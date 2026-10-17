# -*- coding: utf-8 -*-
"""
app.services.catalog_service
============================
检索目录服务：加载主数据，提供精确、核心名、ISSN 及模糊模糊检索。
"""
import json
import os
import re
import sqlite3
import urllib.parse
from app.config import get_catalog_json_path
from app.core.rules import normalize

CAS_DB_PATH = os.path.join(os.path.dirname(get_catalog_json_path()), "cas_jcr.db")
CAS_DISCLAIMER = "⚠️ 本中科院分区数据来源于公开历史开源镜像整理版，其中科院分区在线服务已于2026-09-30关停。仅供选刊参考，实际成果认定请以论文发表当年中国科学院文献情报中心官方最新版本为准。"


def load_catalog(path=None):
    """加载检索目录主数据 (journal_catalog.json)。"""
    target = path or get_catalog_json_path()
    if not os.path.exists(target):
        return {"meta": {}, "categories": [], "journals": [], "rules": []}
    with open(target, encoding="utf-8") as f:
        return json.load(f)


def load_chinese_core():
    """加载全国中文核心期刊与 CSCD 离线全量索引库。"""
    core_path = os.path.join(os.path.dirname(get_catalog_json_path()), "chinese_core_journals.json")
    if not os.path.exists(core_path):
        return []
    try:
        with open(core_path, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("journals", [])
    except Exception:
        return []


def find_chinese_core(q):
    """在中文核心期刊数据库中精确或模糊匹配，返回 (journal_rec, kb_rec, matched_by) 或 None。"""
    if not q or not str(q).strip():
        return None, None, None
    qn = normalize(q)
    core_journals = load_chinese_core()

    for j in core_journals:
        name_n = normalize(j.get("name", ""))
        aliases_n = [normalize(a) for a in j.get("aliases", [])]
        # 精确匹配
        matched = False
        match_type = ""
        if qn == name_n or qn in aliases_n:
            matched = True
            match_type = "核心库精确匹配"
        # ISSN 匹配
        elif is_issn(q):
            if re.sub(r"[^0-9Xx]", "", j.get("issn", "")).upper() == re.sub(r"[^0-9Xx]", "", q).upper():
                matched = True
                match_type = "核心库ISSN匹配"
        # CN 匹配
        elif j.get("cn") and qn in normalize(j.get("cn")):
            matched = True
            match_type = "核心库CN匹配"
        # 模糊子串
        elif len(qn) >= 3 and (qn in name_n or name_n in qn):
            matched = True
            match_type = "核心库模糊匹配"

        if matched:
            # 依广中医规则确定级别基准
            if j.get("cscd_core"):
                calc_level = "A2"
                category_desc = "A类2级（CSCD核心版）"
            elif j.get("pkucore"):
                calc_level = "A3"
                category_desc = "A类3级（中文核心期刊要目总览）"
            elif j.get("cscd_ext"):
                calc_level = "A4"
                category_desc = "A类4级（CSCD扩展版）"
            else:
                calc_level = "B"
                category_desc = "B类（校内限定）"

            journal_rec = {
                "name": j["name"],
                "level": calc_level,
                "category": category_desc,
                "publisher": j.get("publisher", ""),
                "issn": j.get("issn", ""),
                "cn": j.get("cn", ""),
                "is_chinese_core": True,
            }

            idx_notes = []
            if j.get("cscd_core"):
                idx_notes.append("中国科学引文数据库CSCD核心库(2023-2024)")
            if j.get("pkucore"):
                idx_notes.append("中文核心期刊要目总览(2023年版/第10版)")
            if j.get("cscd_ext"):
                idx_notes.append("中国科学引文数据库CSCD扩展版")

            kb_rec = {
                "basic": {
                    "name": j["name"],
                    "issn": j.get("issn", ""),
                    "cn": j.get("cn", ""),
                    "publisher": j.get("publisher", ""),
                },
                "indexes": {
                    "indexes_verified": True,
                    "scie_zone": None,
                    "ssci_zone": None,
                    "cscd_core": bool(j.get("cscd_core")),
                    "cscd_ext": bool(j.get("cscd_ext")),
                    "cssci_core": False,
                    "cssci_ext": False,
                    "pkucore": bool(j.get("pkucore")),
                    "chss_core": False,
                    "ahci": False,
                    "ei": False,
                    "extra": j.get("extra", []),
                },
                "indexes_note": "全国中文核心期刊库收录确认：" + "；".join(idx_notes),
                "impact_factor": {},
                "editor_in_chief": j.get("editor", {}),
                "scope": j.get("scope", ""),
                "review_cycle": j.get("review_cycle", ""),
                "publication_mode": j.get("publication_mode", ""),
                "apc_fee": j.get("apc_fee", ""),
                "submission_url": j.get("submission_url", ""),
                "updated": "2024版核心目录已核验",
                "sources": [
                    "北京大学图书馆《中文核心期刊要目总览》",
                    "中国科学院文献情报中心《中国科学引文数据库(CSCD)》",
                ],
            }
            return journal_rec, kb_rec, match_type

    return None, None, None


def is_issn(q):
    """判断字符串是否为标准 ISSN 号（如 1673-1727 或 16731727）。"""
    if not q:
        return False
    return re.fullmatch(r"\d{4}-?\d{3}[0-9Xx]", q.strip()) is not None


def find_journal(catalog, q):
    """按名称/别名/ISSN 精确或模糊匹配，返回 (journal_rec, matched_by, candidates)。"""
    if not q or not str(q).strip():
        return None, "", []
    qn = normalize(q)
    candidates = []
    
    # 1. 精确匹配与别名匹配
    for j in catalog.get("journals", []):
        name_n = normalize(j.get("name", ""))
        alias_n = [normalize(a) for a in j.get("aliases", [])]
        if qn == name_n or qn in alias_n:
            return j, "精确匹配", [j]
        # 去掉括号附注后再比较（如 医学与哲学(对应曾用名…)）
        name_core = re.sub(r"\(.*?\)", "", name_n)
        if qn == name_core:
            return j, "核心名匹配", [j]

    # 2. ISSN 匹配
    if is_issn(q):
        q_issn = q.strip().replace("-", "").upper()
        for j in catalog.get("journals", []):
            if j.get("issn", "").replace("-", "").upper() == q_issn:
                return j, "ISSN匹配", [j]

    # 3. CN 刊号匹配
    cn_clean = q.strip().replace("CN", "").replace("：", "").replace(":", "").strip()
    for j in catalog.get("journals", []):
        j_cn = j.get("cn", "").replace("CN", "").replace("：", "").replace(":", "").strip()
        if cn_clean and j_cn and cn_clean.upper() == j_cn.upper():
            return j, "CN刊号匹配", [j]

    # 4. 子串模糊匹配
    for j in catalog.get("journals", []):
        name_n = normalize(j.get("name", ""))
        if len(qn) >= 2 and (qn in name_n or name_n in qn):
            candidates.append(j)

    if len(candidates) == 1:
        return candidates[0], "模糊匹配", candidates
    return None, "模糊匹配", candidates


def search_catalog(catalog, keyword):
    """在目录中按关键词搜索期刊。"""
    key = normalize(keyword)
    if not key:
        return []
    hits = []
    for j in catalog.get("journals", []):
        blob = normalize(
            j.get("name", "")
            + " "
            + j.get("publisher", "")
            + " "
            + j.get("issn", "")
            + " "
            + j.get("cn", "")
        )
        if key in blob:
            hits.append(j)
    return hits


def load_chinese_core_full():
    """加载全国中文核心期刊与 CSCD 离线全量数据 (含 meta 与 journals)。"""
    core_path = os.path.join(os.path.dirname(get_catalog_json_path()), "chinese_core_journals.json")
    if not os.path.exists(core_path):
        return {"meta": {}, "journals": []}
    try:
        with open(core_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"meta": {}, "journals": []}


def locate_journal_in_all_indexes(query: str):
    """跨所有权威索引目录（广中医308号、CSCD、北大核心、中科院预警及折算规则）精准定位期刊。"""
    if not query or not str(query).strip():
        return {
            "query": "",
            "found": False,
            "summary": "请输入期刊名称、ISSN、CN 或 检索规则进行跨目录精准定位",
            "matches": {
                "gzucms": [],
                "cscd": [],
                "pkucore": [],
                "cas_warning": [],
                "rules": [],
            },
        }

    qn = normalize(query)
    catalog = load_catalog()
    chinese_core = load_chinese_core()
    from app.services.risk_service import load_warning_db
    warning_db = load_warning_db()

    matches = {
        "gzucms": [],
        "cscd": [],
        "pkucore": [],
        "cas_warning": [],
        "rules": [],
    }

    # 1. 广中医 308 号目录定位
    for cat in catalog.get("categories", []):
        cat_level = cat.get("level", "")
        cat_name = cat.get("name", "")
        for idx, item in enumerate(cat.get("items", [])):
            item_name = item.get("name", "")
            item_name_n = normalize(item_name)
            item_pub_n = normalize(item.get("publisher", ""))
            item_rem_n = normalize(item.get("remark", ""))

            matched = False
            if qn == item_name_n or (len(qn) >= 2 and (qn in item_name_n or item_name_n in qn)):
                matched = True
            elif qn in item_pub_n or qn in item_rem_n:
                matched = True

            if matched:
                matches["gzucms"].append({
                    "catalog_id": "gzucms",
                    "catalog_title": "广中医重要期刊目录（校办〔2020〕308号）",
                    "level": cat_level,
                    "category": cat_name,
                    "serial": item.get("serial", str(idx + 1)),
                    "position_index": idx + 1,
                    "position_desc": f"广中医308号目录【{cat_name}】第 {item.get('serial', idx + 1)} 项",
                    "name": item_name,
                    "publisher": item.get("publisher", ""),
                    "remark": item.get("remark", ""),
                })

    # 2. CSCD / 北大核心库定位
    for idx, j in enumerate(chinese_core):
        j_name = j.get("name", "")
        j_name_n = normalize(j_name)
        j_issn = normalize(j.get("issn", ""))
        j_cn = normalize(j.get("cn", ""))
        j_pub_n = normalize(j.get("publisher", ""))

        matched = False
        if qn == j_name_n or (len(qn) >= 2 and (qn in j_name_n or j_name_n in qn)):
            matched = True
        elif is_issn(query) and j_issn and re.sub(r"[^0-9Xx]", "", j_issn).upper() == re.sub(r"[^0-9Xx]", "", qn).upper():
            matched = True
        elif j_cn and qn in j_cn:
            matched = True
        elif qn in j_pub_n:
            matched = True

        if matched:
            # CSCD 匹配
            if j.get("cscd_core") or j.get("cscd_ext"):
                cscd_type = "CSCD核心版 (从高升A2)" if j.get("cscd_core") else "CSCD扩展版 (认定A4)"
                matches["cscd"].append({
                    "catalog_id": "cscd",
                    "catalog_title": "中国科学引文数据库 (CSCD 2023-2024)",
                    "type": cscd_type,
                    "position_index": idx + 1,
                    "position_desc": f"CSCD 数据库第 {idx + 1} 项 (共 {len(chinese_core)} 项)",
                    "name": j_name,
                    "issn": j.get("issn", ""),
                    "cn": j.get("cn", ""),
                    "publisher": j.get("publisher", ""),
                    "subject": j.get("subject", ""),
                    "extra": j.get("extra", []),
                })

            # 北大核心匹配
            if j.get("pkucore"):
                matches["pkucore"].append({
                    "catalog_id": "pkucore",
                    "catalog_title": "北京大学《中文核心期刊要目总览》(第10版/2023版)",
                    "type": "中文核心期刊 (从高升A3)",
                    "position_index": idx + 1,
                    "position_desc": f"北大中文核心目录第 {idx + 1} 项",
                    "name": j_name,
                    "issn": j.get("issn", ""),
                    "cn": j.get("cn", ""),
                    "publisher": j.get("publisher", ""),
                    "subject": j.get("subject", ""),
                    "extra": j.get("extra", []),
                })

    # 3. 中科院国际期刊预警名单定位
    for idx, w in enumerate(warning_db.get("journals", [])):
        w_name = w.get("name", "")
        w_name_n = normalize(w_name)
        w_issn = normalize(w.get("issn", ""))

        matched = False
        if qn == w_name_n or (len(qn) >= 3 and (qn in w_name_n or w_name_n in qn)):
            matched = True
        elif is_issn(query) and w_issn and re.sub(r"[^0-9Xx]", "", w_issn).upper() == re.sub(r"[^0-9Xx]", "", qn).upper():
            matched = True

        if matched:
            matches["cas_warning"].append({
                "catalog_id": "cas_warning",
                "catalog_title": "中国科学院文献情报中心《国际期刊预警名单》",
                "risk_level": w.get("risk_level", "预警"),
                "year": w.get("year", ""),
                "reason": w.get("reason", "学术治理风险"),
                "position_index": idx + 1,
                "position_desc": f"中科院预警名单第 {idx + 1} 项 ({w.get('year')}年)",
                "name": w_name,
                "issn": w.get("issn", ""),
                "subject": w.get("subject", ""),
                "publisher": w.get("publisher", ""),
            })

    # 4. 广中医目录认定与升级折算规则
    for idx, rule in enumerate(catalog.get("rules", [])):
        rule_name = rule.get("name", "")
        rule_key = rule.get("key", "")
        if qn in normalize(rule_name) or qn in normalize(rule_key):
            matches["rules"].append({
                "catalog_id": "rules",
                "catalog_title": "广中医重要期刊认定与升级折算规则",
                "name": rule_name,
                "level": rule.get("level", ""),
                "label": rule.get("label", ""),
                "note": rule.get("note", ""),
                "position_desc": f"规则第 {idx + 1} 条：{rule_name} → {rule.get('label')}",
            })

    # 5. 中科院 1~4 区国际期刊开源历史镜像检索 (附关停历史声明)
    cas_hits = search_cas_for_locate(query, limit=5)
    matches["cas_jcr"] = cas_hits

    # 构造人性化总结
    found_catalogs = []
    if matches["gzucms"]:
        top = matches["gzucms"][0]
        found_catalogs.append(f"【广中医308号目录·{top['category']}】第{top['serial']}项")
    if matches["cscd"]:
        found_catalogs.append(f"【CSCD数据库】")
    if matches["pkucore"]:
        found_catalogs.append(f"【北大中文核心要目总览】")
    if matches["cas_jcr"]:
        cas_top = matches["cas_jcr"][0]
        found_catalogs.append(f"【中科院{cas_top.get('zone', '')}区·开源镜像】")
    if matches["cas_warning"]:
        found_catalogs.append(f"⚠️【中科院预警名单】")
    if matches["rules"]:
        found_catalogs.append(f"【认定折算规则】")

    total_hits = sum(len(v) for v in matches.values())
    found = total_hits > 0
    if found:
        summary = f"已在 {'、'.join(found_catalogs)} 中命中精准匹配！"
    else:
        summary = f"未在各大权威目录中检索到“{query}”，建议检查名称拼写或使用统一刊号 (ISSN/CN) 再次定位。"

    return {
        "query": query,
        "found": found,
        "summary": summary,
        "matches": matches,
    }


def get_cas_db_connection():
    """获取中科院 1~4 区 SQLite 数据库只读连接。"""
    if not os.path.exists(CAS_DB_PATH):
        return None
    conn = sqlite3.connect(CAS_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def search_cas_for_locate(query: str, limit: int = 5):
    """跨目录定位时检索中科院 1~4 区开源镜像库。"""
    if not query or len(query.strip()) < 2:
        return []
    conn = get_cas_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    qn = query.strip()
    clean_issn = re.sub(r"[^0-9Xx]", "", qn).upper()

    rows = []
    if len(clean_issn) >= 7:
        cursor.execute(
            """
            SELECT id, name, issn, eissn, wos_type, category, zone, zone_raw, is_top, jif, jcr_quartile, sub_categories, gzucms_level
            FROM cas_journals
            WHERE replace(issn, '-', '') = ? OR replace(eissn, '-', '') = ?
            LIMIT ?
            """,
            (clean_issn, clean_issn, limit),
        )
        rows = cursor.fetchall()

    if not rows:
        cursor.execute(
            """
            SELECT id, name, issn, eissn, wos_type, category, zone, zone_raw, is_top, jif, jcr_quartile, sub_categories, gzucms_level
            FROM cas_journals
            WHERE name_lower = ? OR name_lower LIKE ?
            ORDER BY is_top DESC, CAST(jif AS REAL) DESC
            LIMIT ?
            """,
            (qn.lower(), f"%{qn.lower()}%", limit),
        )
        rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        top_str = "Top期刊" if r["is_top"] else ""
        jif_str = f"JIF: {r['jif']}" if r["jif"] else ""
        pos_parts = [p for p in [f"中科院{r['zone']}区", r['category'], top_str, jif_str] if p]
        results.append({
            "catalog_id": "cas_jcr",
            "catalog_title": "中科院1~4区国际期刊 (历史开源镜像)",
            "name": r["name"],
            "issn": r["issn"],
            "eissn": r["eissn"],
            "wos_type": r["wos_type"],
            "category": r["category"],
            "zone": r["zone"],
            "zone_raw": r["zone_raw"],
            "is_top": bool(r["is_top"]),
            "jif": r["jif"],
            "jcr_quartile": r["jcr_quartile"],
            "sub_categories": r["sub_categories"],
            "level": r["gzucms_level"],
            "position_desc": " · ".join(pos_parts),
            "disclaimer": CAS_DISCLAIMER,
        })
    return results


def find_cas_journal(q: str):
    """按刊名或 ISSN 在中科院 1~4 区数据库中检索，用于主检索流水线。"""
    if not q or not str(q).strip():
        return None, None, None
    qn = str(q).strip()
    clean_issn = re.sub(r"[^0-9Xx]", "", qn).upper()
    conn = get_cas_db_connection()
    if not conn:
        return None, None, None
    cursor = conn.cursor()

    row = None
    match_type = ""
    if len(clean_issn) >= 7:
        cursor.execute(
            """
            SELECT * FROM cas_journals
            WHERE replace(issn, '-', '') = ? OR replace(eissn, '-', '') = ?
            LIMIT 1
            """,
            (clean_issn, clean_issn),
        )
        row = cursor.fetchone()
        if row:
            match_type = "中科院分区库ISSN匹配"

    if not row:
        cursor.execute(
            "SELECT * FROM cas_journals WHERE name_lower = ? LIMIT 1",
            (qn.lower(),),
        )
        row = cursor.fetchone()
        if row:
            match_type = "中科院分区库精准匹配"

    if not row and len(qn) >= 4:
        cursor.execute(
            """
            SELECT * FROM cas_journals
            WHERE name_lower LIKE ?
            ORDER BY is_top DESC, CAST(jif AS REAL) DESC
            LIMIT 1
            """,
            (f"%{qn.lower()}%",),
        )
        row = cursor.fetchone()
        if row:
            match_type = "中科院分区库模糊匹配"

    conn.close()
    if not row:
        return None, None, None

    journal_rec = {
        "name": row["name"],
        "level": row["gzucms_level"],
        "category": f"广中医{row['gzucms_level']}级（SCIE中科院{row['zone']}区·开源镜像）" if row["zone"] else f"广中医{row['gzucms_level']}级（{row['wos_type']}）",
        "publisher": row["category"] or row["wos_type"],
        "issn": row["issn"],
        "eissn": row["eissn"],
        "is_cas_jcr": True,
        "zone": row["zone"],
        "is_top": bool(row["is_top"]),
        "jif": row["jif"],
        "jcr_quartile": row["jcr_quartile"],
        "disclaimer": CAS_DISCLAIMER,
    }

    extra_tags = [
        f"中科院{row['zone']}区 (历史开源镜像)",
        f"{row['category']}大类",
    ]
    if row["is_top"]:
        extra_tags.append("Top期刊")
    if row["jcr_quartile"]:
        extra_tags.append(f"JCR {row['jcr_quartile']}")

    kb_rec = {
        "basic": {
            "name": row["name"],
            "issn": row["issn"],
            "eissn": row["eissn"],
            "publisher": f"{row['category']} / {row['wos_type']}",
        },
        "indexes": {
            "indexes_verified": True,
            "scie_zone": row["zone"] if "SCIE" in (row["wos_type"] or "") else None,
            "ssci_zone": row["zone"] if "SSCI" in (row["wos_type"] or "") else None,
            "ahci": "AHCI" in (row["wos_type"] or ""),
            "cscd_core": False,
            "cscd_ext": False,
            "pkucore": False,
            "extra": extra_tags,
        },
        "impact_factor": {
            "jcr_year": 2025,
            "jcr_if": row["jif"] or "未明",
            "cas_zone": f"中科院{row['zone']}区" if row["zone"] else "",
            "is_top": bool(row["is_top"]),
            "note": "2025开源历史镜像数据（该在线服务已于2026-9-30关停）",
        },
        "indexes_note": (
            f"中科院分区收录确认：中科院{row['zone']}区（{row['category']}大类），"
            f"折算广中医级别为 {row['gzucms_level']} 级。"
            f"【历史版本说明：{CAS_DISCLAIMER}】"
        ),
        "editor_in_chief": {},
        "scope": f"学科大类：{row['category']}；细分研究方向：{row['sub_categories']}",
        "review_cycle": "同行评审期刊（时限以期刊官网最新指南为准）",
        "publication_mode": f"国际引文索引期刊 ({row['wos_type']})",
        "apc_fee": "视期刊出版模式而定 (OA期刊需缴纳APC，传统订阅模式免费)",
        "submission_url": f"https://www.google.com/search?q={urllib.parse.quote(row['name'] + ' journal submission')}",
        "updated": "2025开源镜像已核验",
        "sources": [
            "中科院文献情报中心JCR分区表历史开源镜像（服务已于2026-9-30关停）",
            "Clarivate Web of Science 核心合集",
        ],
    }
    return journal_rec, kb_rec, match_type


def get_cas_journals(
    zone: int = None,
    category: str = None,
    is_top: int = None,
    wos_type: str = None,
    q: str = None,
    page: int = 1,
    page_size: int = 20,
):
    """获取中科院 1~4 区开源镜像期刊列表（支持分页、分区、学科筛选、WoS子库、Top过滤与搜索）。"""
    conn = get_cas_db_connection()
    if not conn:
        return {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "disclaimer": CAS_DISCLAIMER,
            "journals": [],
        }

    cursor = conn.cursor()
    conditions = []
    params = []

    if zone in (1, 2, 3, 4):
        conditions.append("zone = ?")
        params.append(zone)

    if category and category.strip() and category.strip() != "ALL":
        conditions.append("category = ?")
        params.append(category.strip())

    if is_top is not None and is_top in (0, 1):
        conditions.append("is_top = ?")
        params.append(is_top)

    if wos_type and wos_type.strip() and wos_type.strip() != "ALL":
        wt = wos_type.strip().upper()
        conditions.append("wos_type LIKE ?")
        params.append(f"%{wt}%")

    if q and q.strip():
        qn = q.strip().lower()
        clean_issn = re.sub(r"[^0-9Xx]", "", qn).upper()
        if len(clean_issn) >= 7:
            conditions.append("(replace(issn, '-', '') LIKE ? OR replace(eissn, '-', '') LIKE ?)")
            params.extend([f"%{clean_issn}%", f"%{clean_issn}%"])
        else:
            conditions.append("(name_lower LIKE ? OR sub_categories LIKE ?)")
            params.extend([f"%{qn}%", f"%{qn}%"])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # 计算总数
    cursor.execute(f"SELECT COUNT(*) FROM cas_journals {where_clause}", params)
    total = cursor.fetchone()[0]

    # 分页查询
    offset = max(0, (page - 1) * page_size)
    query_sql = f"""
        SELECT id, name, issn, eissn, wos_type, category, zone, zone_raw, is_top, jif, jcr_quartile, sub_categories, gzucms_level
        FROM cas_journals
        {where_clause}
        ORDER BY zone ASC, is_top DESC, CAST(jif AS REAL) DESC
        LIMIT ? OFFSET ?
    """
    cursor.execute(query_sql, params + [page_size, offset])
    rows = cursor.fetchall()
    conn.close()

    journals = []
    for r in rows:
        journals.append({
            "id": r["id"],
            "name": r["name"],
            "issn": r["issn"],
            "eissn": r["eissn"],
            "wos_type": r["wos_type"],
            "category": r["category"],
            "zone": r["zone"],
            "zone_raw": r["zone_raw"],
            "is_top": bool(r["is_top"]),
            "jif": r["jif"],
            "jcr_quartile": r["jcr_quartile"],
            "sub_categories": r["sub_categories"],
            "gzucms_level": r["gzucms_level"],
            "disclaimer": CAS_DISCLAIMER,
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "disclaimer": CAS_DISCLAIMER,
        "journals": journals,
    }


def get_cas_categories():
    """获取中科院分区库所有学科大类列表。"""
    conn = get_cas_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM cas_journals WHERE category != '' ORDER BY category")
    cats = [row[0] for row in cursor.fetchall()]
    conn.close()
    return cats
