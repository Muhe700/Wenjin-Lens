# -*- coding: utf-8 -*-
"""
app.core.rules
==============
广中医重要期刊认定规则引擎与多索引收录计算模块。
实现核心特性：
  1. 多索引收录解析（同一期刊支持同时命中 CSCD、北大核心、SCIE、EI 等多个索引）
  2. 广中医“从高认定”仲裁（根据目录备注1：本表中所列刊物如进入更高级别，则按高级别期刊认定）
"""
import re
from app.core.constants import (
    LEVEL_ORDER,
    LEVEL_LABEL,
    KB_INDEX_TO_RULE,
    RULE_QUERY_ALIASES,
)


def normalize(s):
    """归一化：去空白、书名号、引号等装饰字符，转小写。"""
    if not s:
        return ""
    s = str(s).strip().lower()
    s = s.replace("《", "").replace("》", "").replace("「", "").replace("」", "")
    s = re.sub(r"\s+", "", s)
    s = s.replace("（", "(").replace("）", ")")
    return s


def is_rule_query(q):
    """判定输入是否为“索引规则查询”：
    含中文（如“北大核心”“SCIE 1区”），或为短英文索引词（如 SCIE/SSCI/EI/ISR）。
    纯英文长名称（如期刊英文名含 science/scie 子串）不做规则查询，避免误判。"""
    q_str = str(q).strip()
    has_cjk = any("\u4e00" <= ch <= "\u9fff" for ch in q_str)
    if has_cjk:
        return True
    return len(normalize(q_str)) <= 8


def find_rule(catalog, q):
    """索引规则查询：返回 (rule_key, level, rule_name) 或 (need_zone, None, None) 或 None。"""
    if not is_rule_query(q):
        return None
    qn = normalize(q)
    rules_by_key = {r["key"]: r for r in catalog.get("rules", [])}
    zone_missing = False
    for key, aliases in RULE_QUERY_ALIASES.items():
        for a in aliases:
            if normalize(a) in qn:
                # 分区类规则需要具体区号
                if key in ("scie_zone", "ssci_zone"):
                    zone = None
                    m = re.search(r"([1-4])区", qn)
                    if m:
                        zone = m.group(1)
                    else:
                        for zh, num in (("一", "1"), ("二", "2"), ("三", "3"), ("四", "4")):
                            if f"{zh}区" in qn:
                                zone = num
                                break
                    if not zone:
                        zone_missing = True
                        continue
                    fkey = f"{key}{zone}"
                else:
                    fkey = key
                r = rules_by_key.get(fkey)
                if r:
                    return (fkey, r["level"], r["name"])
    # 直接输入规则全名
    for r in catalog.get("rules", []):
        if normalize(r["name"]) == qn or normalize(r["name"]) in qn:
            return (r["key"], r["level"], r["name"])
    if zone_missing:
        return ("need_zone", None, None)
    return None


def kb_rule_hits(kb_rec):
    """由知识库索引字段得出命中的 (rule_key) 列表。"""
    hits = []
    if not kb_rec:
        return hits
    indexes = kb_rec.get("indexes") or {}
    for field, tmpl in KB_INDEX_TO_RULE:
        val = indexes.get(field)
        if not val:
            continue
        if field in ("scie_zone", "ssci_zone"):
            if str(val) in ("1", "2", "3", "4"):
                hits.append(tmpl.format(zone=val))
        else:
            hits.append(tmpl)
    return hits


def compute_level(catalog, journal_rec, kb_rec):
    """计算广中医认定级别，返回 (best_level, reasons, upgraded)。
    同时支持单刊多索引收录，并依广中医备注1“从高认定”。"""
    rules_by_key = {r["key"]: r for r in catalog.get("rules", [])}
    levels = []
    reasons = []
    if journal_rec:
        lv = journal_rec["level"]
        levels.append(lv)
        reasons.append(f"目录列名：{journal_rec.get('category','')}（{journal_rec.get('name','')}）")
    for key in kb_rule_hits(kb_rec):
        r = rules_by_key.get(key)
        if r:
            levels.append(r["level"])
            reasons.append(f"索引命中：{r['name']} → {r['level']}")
    if not levels:
        return None, reasons, False
    best = min(levels, key=lambda x: LEVEL_ORDER.get(x, 99))
    # “进入更高级别，按高级别认定”：索引规则级别高于目录直接列名级别
    catalog_level = journal_rec["level"] if journal_rec else None
    upgraded = (
        catalog_level is not None
        and LEVEL_ORDER.get(best, 99) < LEVEL_ORDER.get(catalog_level, 99)
        and any(reason.startswith("索引命中") for reason in reasons)
    )
    return best, reasons, upgraded


def index_summary(kb_rec):
    """把知识库索引字段汇总成一行文本（用分号串联所有命中索引）。"""
    idx = (kb_rec or {}).get("indexes") or {}
    parts = []
    if idx.get("scie_zone"):
        parts.append(f"SCIE(中科院{idx['scie_zone']}区)")
    if idx.get("ssci_zone"):
        parts.append(f"SSCI(中科院{idx['ssci_zone']}区)")
    for field, label in (
        ("cscd_core", "CSCD核心版"),
        ("cscd_ext", "CSCD扩展版"),
        ("cssci_core", "CSSCI核心版"),
        ("cssci_ext", "CSSCI扩展版"),
        ("pkucore", "北大核心"),
        ("chss_core", "人文社科核心要览"),
        ("ahci", "A&HCI"),
        ("ei", "EI"),
        ("cpci_s", "CPCI-S"),
        ("cpci_ssh", "CPCI-SSH"),
        ("isr", "ISR"),
        ("xhwd", "新华文摘转载"),
        ("rdfy", "人大复印转载"),
    ):
        if idx.get(field):
            parts.append(label)
    if idx.get("extra"):
        parts.extend(idx["extra"])
    if not parts:
        if kb_rec and idx.get("indexes_verified"):
            return "未命中主流索引"
        return "待核验"
    return "；".join(parts)
