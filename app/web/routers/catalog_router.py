# -*- coding: utf-8 -*-
"""
app.web.routers.catalog_router
==============================
官方目录与统计指标路由：
提供官方期刊分级目录全景数据、系统全量运行资产统计及健康探针。
"""
from typing import Optional
from fastapi import APIRouter, Header, Query

from app.models.schemas import (
    AllIndexesResponseDTO,
    CasJournalsResponseDTO,
    CatalogResponseDTO,
    LocateResponseDTO,
    StatsResponseDTO,
)
from app.services.catalog_service import (
    get_cas_categories,
    get_cas_journals,
    load_catalog,
    load_chinese_core,
    load_chinese_core_full,
    locate_journal_in_all_indexes,
)
from app.services.kb_service import load_kb
from app.services.risk_service import load_warning_db
from app.services.track_service import load_track

router = APIRouter(prefix="/api", tags=["官方目录与系统统计"])


@router.get("/health")
def health_check():
    """服务健康检查接口。"""
    return {"status": "ok", "app": "Wenjin-Lens", "version": "2.2.0"}


@router.get("/catalog", response_model=CatalogResponseDTO)
def api_get_catalog():
    """获取完整的官方目录及分级期刊清单。"""
    catalog = load_catalog()
    return {
        "meta": catalog.get("meta", {}),
        "categories": catalog.get("categories", []),
        "total_journals": len(catalog.get("journals", [])),
        "journals": catalog.get("journals", []),
        "rules": catalog.get("rules", []),
    }


@router.get("/indexes/all", response_model=AllIndexesResponseDTO)
def api_get_all_indexes():
    """获取全量权威索引目录全景聚合数据（广中医308号、CSCD、北大核心、中科院预警）。"""
    catalog = load_catalog()
    chinese_core = load_chinese_core_full()
    warning_db = load_warning_db()
    return {
        "gzucms": catalog,
        "chinese_core": chinese_core,
        "cas_warning": warning_db,
    }


@router.get("/indexes/locate", response_model=LocateResponseDTO)
def api_locate_journal(q: str = ""):
    """跨所有权威索引目录（广中医308号、CSCD、北大核心、中科院预警及折算规则）精准定位期刊。"""
    return locate_journal_in_all_indexes(q)


@router.get("/indexes/cas/journals", response_model=CasJournalsResponseDTO)
def api_get_cas_journals(
    zone: Optional[int] = Query(None, description="中科院分区号 (1, 2, 3, 4)"),
    category: Optional[str] = Query(None, description="学科大类 (如：医学, 生物学, 综合性期刊)"),
    is_top: Optional[int] = Query(None, description="是否Top期刊 (1 或 0)"),
    wos_type: Optional[str] = Query(None, description="WoS数据库类型 (SCIE, SSCI, AHCI, ESCI)"),
    q: Optional[str] = Query(None, description="刊名或 ISSN 模糊搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):
    """获取中科院 1~4 区国际期刊全量开源历史镜像清单 (支持分页与多维筛选)。"""
    return get_cas_journals(
        zone=zone,
        category=category,
        is_top=is_top,
        wos_type=wos_type,
        q=q,
        page=page,
        page_size=page_size,
    )


@router.get("/indexes/cas/categories")
def api_get_cas_categories():
    """获取中科院分区库中涵盖的所有学科大类列表。"""
    return {"categories": get_cas_categories()}


@router.get("/stats", response_model=StatsResponseDTO)
def api_get_stats(
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    uid: Optional[str] = Query(None, alias="user_id"),
):
    """获取当前系统运行统计（目录数、知识库数、追踪数、核心库数、预警库数）。"""
    effective_uid = uid or user_id
    catalog = load_catalog()
    kb = load_kb()
    track = load_track(user_id=effective_uid)
    chinese_core = load_chinese_core()
    warning_db = load_warning_db()

    verified_cnt = sum(
        1 for r in kb.get("records", {}).values() if (r.get("indexes") or {}).get("indexes_verified")
    )
    return {
        "catalog_journals": len(catalog.get("journals", [])),
        "catalog_rules": len(catalog.get("rules", [])),
        "chinese_core_count": len(chinese_core),
        "cas_warning_count": len(warning_db.get("journals", [])),
        "kb_records": len(kb.get("records", {})),
        "kb_verified": verified_cnt,
        "track_records": len(track),
    }
