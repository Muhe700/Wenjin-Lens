# -*- coding: utf-8 -*-
"""
app.services.risk_service
=========================
学术风险排查服务：自动对照中国科学院文献情报中心《国际期刊预警名单》。
支持按期刊全称、别名或 ISSN 毫秒级离线比对，提示论文工厂、引用操纵与学术治理风险。
"""
import json
import os
import re
from app.config import DATA_DIR
from app.core.rules import normalize

WARNING_DB_PATH = os.path.join(DATA_DIR, "risk", "cas_warning_journals.json")


def load_warning_db():
    """加载中科院预警期刊离线数据库。"""
    if not os.path.exists(WARNING_DB_PATH):
        return {"meta": {}, "journals": []}
    try:
        with open(WARNING_DB_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"meta": {}, "journals": []}


def check_cas_warning(journal_name, issn=None):
    """核验某期刊是否在中科院国际期刊预警名单中。
    返回: dict(is_warned=True, ...) 或 None
    """
    db = load_warning_db()
    journals = db.get("journals", [])
    if not journals:
        return None

    # 1. 优先按 ISSN 比对
    cand_issns = []
    if issn:
        clean = re.sub(r"[^0-9Xx]", "", str(issn)).upper()
        if clean:
            cand_issns.append(clean)

    # 2. 从名称中尝试提取 ISSN
    name_clean = normalize(journal_name)
    m = re.search(r"(\d{4}-?\d{3}[0-9Xx])", journal_name or "")
    if m:
        cand_issns.append(re.sub(r"[^0-9Xx]", "", m.group(1)).upper())

    for j in journals:
        j_issn = re.sub(r"[^0-9Xx]", "", j.get("issn", "")).upper()
        if j_issn and j_issn in cand_issns:
            return {
                "is_warned": True,
                "name": j["name"],
                "issn": j["issn"],
                "year": j.get("year", ""),
                "risk_level": j.get("risk_level", "预警"),
                "reason": j.get("reason", "学术治理风险"),
                "publisher": j.get("publisher", ""),
                "warning_text": f"【中科院预警期刊({j.get('year')}年)】预警原因：{j.get('reason')}",
            }

    # 3. 按期刊英文全称比对
    for j in journals:
        target_n = normalize(j["name"])
        if name_clean == target_n or (len(name_clean) >= 4 and name_clean == target_n):
            return {
                "is_warned": True,
                "name": j["name"],
                "issn": j["issn"],
                "year": j.get("year", ""),
                "risk_level": j.get("risk_level", "预警"),
                "reason": j.get("reason", "学术治理风险"),
                "publisher": j.get("publisher", ""),
                "warning_text": f"【中科院预警期刊({j.get('year')}年)】预警原因：{j.get('reason')}",
            }

    return None
