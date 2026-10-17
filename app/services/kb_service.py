# -*- coding: utf-8 -*-
"""
app.services.kb_service
=======================
期刊知识库服务：加载、持久化已核验动态字段，支持目录外期刊的检索与入库。
"""
import datetime
import json
import os
from app.config import get_kb_json_path
from app.core.rules import normalize
from app.services.catalog_service import is_issn


def load_kb(path=None):
    """加载期刊知识库 (journal_kb.json)。"""
    target = path or get_kb_json_path()
    if not os.path.exists(target):
        return {"meta": {}, "records": {}}
    try:
        with open(target, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"meta": {}, "records": {}}


def save_kb(kb, path=None):
    """将知识库写回文件。"""
    target = path or get_kb_json_path()
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)


def find_in_kb(kb, q):
    """在知识库中查找目录外已核验期刊（按名称/别名/ISSN/子串）。"""
    if not q or not str(q).strip():
        return None, None, None
    records = kb.get("records") or {}
    qn = normalize(q)
    # 精确/别名/ISSN
    for name, rec in records.items():
        basic = rec.get("basic") or {}
        if basic.get("in_catalog"):
            continue
        cand_names = [name] + (basic.get("aliases") or [])
        if qn in [normalize(n) for n in cand_names]:
            return name, "知识库记录", rec
        issn = (basic.get("issn") or "").replace("-", "").upper()
        if is_issn(q) and issn == q.strip().replace("-", "").upper():
            return name, "知识库记录(ISSN)", rec
    # 子串模糊
    hits = []
    for name, rec in records.items():
        basic = rec.get("basic") or {}
        if basic.get("in_catalog"):
            continue
        if len(qn) >= 2 and qn in normalize(name):
            hits.append((name, rec))
    if len(hits) == 1:
        return hits[0][0], "知识库记录(模糊)", hits[0][1]
    return None, None, None


def init_kb(catalog, kb=None, path=None):
    """由目录初始化/重建知识库骨架。"""
    kb = kb or load_kb(path)
    records = {}
    for j in catalog.get("journals", []):
        rec = kb.get("records", {}).get(j["name"], {})
        rec.setdefault(
            "indexes",
            {
                "indexes_verified": False,
                "scie_zone": None,
                "ssci_zone": None,
                "cscd_core": False,
                "cscd_ext": False,
                "cssci_core": False,
                "cssci_ext": False,
                "pkucore": False,
                "chss_core": False,
                "ahci": False,
                "ei": False,
                "cpci_s": False,
                "cpci_ssh": False,
                "isr": False,
                "xhwd": False,
                "rdfy": False,
            },
        )
        rec.setdefault("impact_factor", {})
        rec.setdefault("editor_in_chief", {})
        rec.setdefault("scope", "")
        rec.setdefault("review_cycle", "")
        rec.setdefault("publication_mode", "")
        rec.setdefault("apc_fee", "")
        rec.setdefault("submission_url", "")
        rec.setdefault("sources", [])
        records[j["name"]] = rec
    kb["meta"] = {
        "note": "动态字段（收录索引、影响因子、主编、收稿方向、审稿周期、出版方式、版面费、投稿方式）由联网检索核验后补充；缺失时程序输出“待核验”。",
        "updated": datetime.date.today().isoformat(),
    }
    kb["records"] = records
    target = path or get_kb_json_path()
    save_kb(kb, target)
    return kb, target


def upsert_kb_record(kb, journal_name, record_data, path=None):
    """将联网核验获取到的记录合并回知识库。"""
    if "records" not in kb:
        kb["records"] = {}
    if journal_name not in kb["records"]:
        kb["records"][journal_name] = {}
    target = kb["records"][journal_name]
    for k, v in record_data.items():
        if isinstance(v, dict) and isinstance(target.get(k), dict):
            for sub_k, sub_v in v.items():
                if sub_v is not None and sub_v != "" and sub_v is not False:
                    target[k][sub_k] = sub_v
                elif sub_k not in target[k]:
                    target[k][sub_k] = sub_v
        else:
            if v or k not in target:
                target[k] = v
    kb.setdefault("meta", {})["updated"] = datetime.date.today().isoformat()
    save_kb(kb, path or get_kb_json_path())
    return kb
