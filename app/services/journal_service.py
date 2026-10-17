# -*- coding: utf-8 -*-
"""
app.services.journal_service
============================
期刊检索、评级判定与数据核验领域服务 (Domain Service & Facade)。
统一封装了多级级联检索引擎、广中医认定规则评估、中科院预警风险扫描及决策台账自动沉淀逻辑，
为 Web API 层与 CLI 终端层提供高内聚、低耦合的标准数据交互接口。
"""
from typing import Any, Dict, Optional, Tuple

from app.config import get_api_key
from app.core.constants import LEVEL_LABEL
from app.core.rules import compute_level, find_rule
from app.services.academic_api import fetch_open_academic_metadata
from app.services.ai_verifier import fetch_journal_from_gemini
from app.services.catalog_service import (
    find_cas_journal,
    find_chinese_core,
    find_journal,
    is_issn,
    load_catalog,
)
from app.services.kb_service import find_in_kb, load_kb, upsert_kb_record
from app.services.risk_service import check_cas_warning
from app.services.track_service import build_track_row, upsert_track


class JournalService:
    """选刊助手核心业务领域服务。"""

    @classmethod
    def search(cls, query: str, auto_track: bool = True) -> Dict[str, Any]:
        """执行统一的多层级联选刊检索流程。
        检索优先级策略：
          1. 广中医校办〔2020〕308号目录精确/别名/刊号匹配
          2. 全国中文核心期刊与 CSCD 全量数据库匹配
          3. 目录外知识库 (KB) 已核验期刊匹配
          4. SCIE/SSCI/中文核心等收录索引定级规则直接匹配
          5. 目录相似期刊模糊候选提示
          6. 未收录引导提示
        """
        q = (query or "").strip()
        if not q:
            return {
                "type": "error",
                "message": "查询关键词不能为空",
            }

        catalog = load_catalog()
        kb = load_kb()

        # 1. 广中医官方目录匹配
        journal_rec, matched_by, candidates = find_journal(catalog, q)
        if journal_rec:
            kb_rec = kb.get("records", {}).get(journal_rec["name"])
            if not kb_rec or not (kb_rec.get("indexes") or {}).get("indexes_verified"):
                _, core_kb, _ = find_chinese_core(journal_rec["name"])
                if core_kb:
                    if not kb_rec:
                        kb_rec = core_kb
                    else:
                        for k, v in core_kb.items():
                            if v and not kb_rec.get(k):
                                kb_rec[k] = v
                        if core_kb.get("indexes"):
                            kb_rec["indexes"] = core_kb["indexes"]
                        if core_kb.get("indexes_note"):
                            kb_rec["indexes_note"] = core_kb["indexes_note"]

            best, reasons, upgraded = compute_level(catalog, journal_rec, kb_rec)
            track_row = build_track_row(journal_rec, kb_rec, catalog, best, kb_only=False)
            if auto_track:
                upsert_track(track_row)
            issn_val = journal_rec.get("issn") or (kb_rec or {}).get("basic", {}).get("issn")
            warning_info = check_cas_warning(journal_rec["name"], issn_val)
            return {
                "type": "journal",
                "name": journal_rec["name"],
                "matched_by": matched_by,
                "in_catalog": True,
                "catalog": journal_rec,
                "kb": kb_rec or {},
                "warning_info": warning_info,
                "level_info": {
                    "level": best,
                    "label": LEVEL_LABEL.get(best, "不符合/待核验"),
                    "reasons": reasons,
                    "upgraded": upgraded,
                },
                "track_row": track_row,
            }

        # 2. 全国中文核心期刊与 CSCD 离线数据库匹配
        core_j, core_kb, core_matched = find_chinese_core(q)
        if core_j:
            existing_kb = kb.get("records", {}).get(core_j["name"]) or {}
            if existing_kb:
                for k, v in existing_kb.items():
                    if k == "indexes" and isinstance(v, dict):
                        for ik, iv in v.items():
                            if iv:
                                core_kb.setdefault("indexes", {})[ik] = iv
                    elif v:
                        core_kb[k] = v
            best, reasons, upgraded = compute_level(catalog, None, core_kb)
            track_row = build_track_row(core_j, core_kb, catalog, best, kb_only=True)
            if auto_track:
                upsert_track(track_row)
            warning_info = check_cas_warning(core_j["name"], core_j.get("issn"))
            return {
                "type": "journal",
                "name": core_j["name"],
                "matched_by": core_matched,
                "in_catalog": False,
                "catalog": core_j,
                "kb": core_kb,
                "warning_info": warning_info,
                "level_info": {
                    "level": best,
                    "label": LEVEL_LABEL.get(best, "不符合/待核验"),
                    "reasons": reasons,
                    "upgraded": upgraded,
                },
                "track_row": track_row,
            }

        # 3. 目录外知识库已核验期刊
        kb_name, kb_matched, kb_rec = find_in_kb(kb, q)
        if kb_rec:
            basic = kb_rec.get("basic") or {}
            synthetic = {
                "name": kb_name,
                "publisher": basic.get("publisher", ""),
                "issn": basic.get("issn", ""),
                "cn": basic.get("cn", ""),
            }
            best, reasons, upgraded = compute_level(catalog, None, kb_rec)
            track_row = build_track_row(synthetic, kb_rec, catalog, best, kb_only=True)
            if auto_track:
                upsert_track(track_row)
            warning_info = check_cas_warning(kb_name, basic.get("issn"))
            return {
                "type": "journal",
                "name": kb_name,
                "matched_by": kb_matched,
                "in_catalog": False,
                "catalog": synthetic,
                "kb": kb_rec,
                "warning_info": warning_info,
                "level_info": {
                    "level": best,
                    "label": LEVEL_LABEL.get(best, "不符合/待核验"),
                    "reasons": reasons,
                    "upgraded": upgraded,
                },
                "track_row": track_row,
            }

        # 4. 索引定级规则直接匹配
        rule_hit = find_rule(catalog, q)
        if rule_hit:
            if rule_hit[0] == "need_zone":
                return {
                    "type": "rule_need_zone",
                    "message": f"“{q}”命中 SCIE/SSCI 分区规则但未给出区号，请补充分区，如：SCIE 1区 / SSCI 2区（1~4区）。",
                }
            zone_num = None
            wos_type = ""
            if "scie" in rule_hit[0] or "ssci" in rule_hit[0]:
                wos_type = "SCIE" if "scie" in rule_hit[0] else "SSCI"
                for z_char in ("1", "2", "3", "4"):
                    if z_char in rule_hit[0]:
                        zone_num = int(z_char)
                        break

            disclaimer = ""
            has_catalog_list = False
            catalog_list_title = ""
            target_tab = ""

            if zone_num:
                has_catalog_list = True
                catalog_list_title = f"{wos_type} 中科院 {zone_num} 区收录期刊全文 (历史开源镜像)"
                disclaimer = "⚠️ 历史版本说明：本中科院分区数据来源于公开历史开源镜像整理版，其中科院分区在线服务已于2026-09-30关停。仅供选刊参考，实际成果认定请以论文发表当年中国科学院文献情报中心官方最新版本为准。"
                target_tab = "cas_zone"
            elif "pku" in rule_hit[0]:
                has_catalog_list = True
                catalog_list_title = "北京大学《中文核心期刊要目总览》收录期刊全文 (2,592本)"
                target_tab = "pkucore"
            elif "cscd" in rule_hit[0]:
                has_catalog_list = True
                catalog_list_title = "CSCD 中国科学引文数据库来源期刊全文 (1,306本)"
                target_tab = "cscd"

            return {
                "type": "rule",
                "rule_key": rule_hit[0],
                "level": rule_hit[1],
                "label": LEVEL_LABEL.get(rule_hit[1]),
                "name": rule_hit[2],
                "zone": zone_num,
                "wos_type": wos_type,
                "target_tab": target_tab,
                "has_catalog_list": has_catalog_list,
                "catalog_list_title": catalog_list_title,
                "disclaimer": disclaimer,
                "note": "SCIE/SSCI 分区按论文发表当年中国科学院文献情报中心分区认定"
                if "scie" in rule_hit[0] or "ssci" in rule_hit[0]
                else "",
            }

        # 4.5. 中科院 1~4 区国际期刊开源历史镜像库匹配
        cas_j, cas_kb, cas_matched = find_cas_journal(q)
        if cas_j:
            existing_kb = kb.get("records", {}).get(cas_j["name"]) or {}
            if existing_kb:
                for k, v in existing_kb.items():
                    if k == "indexes" and isinstance(v, dict):
                        for ik, iv in v.items():
                            if iv:
                                cas_kb.setdefault("indexes", {})[ik] = iv
                    elif v:
                        cas_kb[k] = v
            best, reasons, upgraded = compute_level(catalog, None, cas_kb)
            track_row = build_track_row(cas_j, cas_kb, catalog, best, kb_only=True)
            if auto_track:
                upsert_track(track_row)
            warning_info = check_cas_warning(cas_j["name"], cas_j.get("issn"))
            return {
                "type": "journal",
                "name": cas_j["name"],
                "matched_by": cas_matched,
                "in_catalog": False,
                "catalog": cas_j,
                "kb": cas_kb,
                "warning_info": warning_info,
                "level_info": {
                    "level": best,
                    "label": LEVEL_LABEL.get(best, "不符合/待核验"),
                    "reasons": reasons,
                    "upgraded": upgraded,
                },
                "track_row": track_row,
            }

        # 5. 模糊候选提示
        if candidates:
            return {
                "type": "candidates",
                "message": f"“{q}”匹配到多个候选，请补充更完整名称：",
                "candidates": candidates[:10],
            }

        # 6. 未命中
        return {
            "type": "not_found",
            "message": f"未在目录中找到“{q}”。可用关键词模糊搜索，或在下方尝试联网核验。",
        }

    @classmethod
    def refresh(cls, query: str, explicit_api_key: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """聚合免注册开放学术生态 (OpenAlex/DOAJ) 与 Google Gemini AI 深度提炼办刊指标并回写知识库。
        返回: (success: bool, result_dict: dict)
        """
        q = (query or "").strip()
        if not q:
            return False, {"error": "期刊名称不能为空"}

        # 0. 尝试优先推导本地已知的官方 ISSN 刊号
        local_issn = None
        if is_issn(q):
            local_issn = q
        else:
            cat = load_catalog()
            j_rec, _, _ = find_journal(cat, q)
            if j_rec and j_rec.get("issn"):
                local_issn = j_rec["issn"]
            else:
                cas_rec = find_cas_journal(q)
                if cas_rec and (cas_rec.get("issn") or cas_rec.get("eissn")):
                    local_issn = cas_rec.get("issn") or cas_rec.get("eissn")

        # 1. 抓取 OpenAlex / DOAJ 权威学术元数据（防御性隔离外部网络抖动）
        try:
            academic_meta = fetch_open_academic_metadata(issn=local_issn, journal_name=q)
        except Exception:
            academic_meta = {
                "source": "OpenAcademic",
                "openalex": None,
                "doaj": None,
                "apc_summary": "",
                "homepage": "",
                "review_cycle": "",
                "is_oa": None,
            }

        res_data = {
            "basic": {"name": q, "issn": local_issn or ""},
            "indexes": {"indexes_verified": True},
            "impact_factor": {},
            "editor_in_chief": {},
            "scope": "",
            "review_cycle": academic_meta.get("review_cycle") or "",
            "publication_mode": "开放获取(OA)"
            if academic_meta.get("is_oa")
            else ("传统订阅制" if academic_meta.get("is_oa") is False else ""),
            "apc_fee": academic_meta.get("apc_summary") or "",
            "submission_url": academic_meta.get("homepage") or "",
        }

        # 2. 尝试调用 Gemini 提炼办刊方向、主编及复杂中医药办刊范畴
        api_key = get_api_key(explicit_api_key)
        if api_key:
            gemini_ok, gemini_data = fetch_journal_from_gemini(q, api_key)
            if gemini_ok and isinstance(gemini_data, dict):
                for k, v in gemini_data.items():
                    if v and (not res_data.get(k) or k in ("scope", "editor_in_chief", "impact_factor", "indexes")):
                        res_data[k] = v

        if not res_data.get("submission_url") and not res_data.get("apc_fee") and not api_key:
            return False, {
                "error": "OpenAlex/DOAJ 未检索到该刊且未配置 Gemini API Key，请在 config/config.json 配置 Key 进行深度检索。"
            }

        # 3. 回写持久化至知识库
        kb = load_kb()
        j_name = res_data.get("basic", {}).get("name") or q
        upsert_kb_record(kb, j_name, res_data)

        return True, {
            "status": "success",
            "journal": j_name,
            "data": res_data,
            "open_academic": academic_meta,
        }
