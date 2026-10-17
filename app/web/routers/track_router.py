# -*- coding: utf-8 -*-
"""
app.web.routers.track_router
============================
决策台账与多维筛选路由：
提供决策追踪台账读取、期刊删除与清空、复合多维筛选以及多用户隔离的自适应样式 Excel (.xlsx) 导出下载。
"""
import os
from typing import Optional
from urllib.parse import quote
from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import FileResponse

from app.config import get_track_xlsx_path
from app.models.schemas import TrackActionResponseDTO, TrackResponseDTO
from app.services.journal_service import JournalService
from app.services.track_service import (
    clear_track,
    delete_track_row,
    filter_track_rows,
    get_filterable_rows,
    load_track,
    save_track,
)

router = APIRouter(prefix="/api", tags=["决策台账与智能筛选"])


@router.get("/track", response_model=TrackResponseDTO)
def api_get_track(
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    uid: Optional[str] = Query(None, alias="user_id"),
):
    """获取指定用户的选刊决策台账（多用户隔离）。"""
    effective_uid = uid or user_id
    rows = load_track(user_id=effective_uid)
    return {"total": len(rows), "records": rows}


@router.delete("/track", response_model=TrackActionResponseDTO)
def api_delete_track_row(
    name: str = Query(..., description="待从台账中移出的期刊名称"),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    uid: Optional[str] = Query(None, alias="user_id"),
):
    """从用户选刊决策台账中删除指定期刊。"""
    journal_name = (name or "").strip()
    if not journal_name:
        raise HTTPException(status_code=400, detail="期刊名称不能为空")

    effective_uid = uid or user_id
    found, remaining = delete_track_row(journal_name, user_id=effective_uid)
    if not found:
        raise HTTPException(status_code=404, detail=f"台账中未找到期刊《{journal_name}》")

    return {
        "status": "success",
        "message": f"已成功从选刊台账中移出《{journal_name}》",
        "remaining": remaining,
    }


@router.delete("/track/clear", response_model=TrackActionResponseDTO)
def api_clear_track(
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    uid: Optional[str] = Query(None, alias="user_id"),
):
    """清空当前用户的选刊决策台账。"""
    effective_uid = uid or user_id
    clear_track(user_id=effective_uid)
    return {
        "status": "success",
        "message": "当前用户的选刊决策台账已清空",
        "remaining": 0,
    }


@router.post("/track", response_model=TrackActionResponseDTO)
def api_add_to_track(
    name: str = Query(..., description="待收录至台账的期刊名称"),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    uid: Optional[str] = Query(None, alias="user_id"),
):
    """手动将某期刊加入当前用户的选刊台账。"""
    journal_name = (name or "").strip()
    if not journal_name:
        raise HTTPException(status_code=400, detail="期刊名称不能为空")

    effective_uid = uid or user_id
    res = JournalService.search(journal_name, auto_track=True, user_id=effective_uid)
    if res.get("type") == "error":
        raise HTTPException(status_code=400, detail=res.get("message", "加入台账失败"))

    rows = load_track(user_id=effective_uid)
    return {
        "status": "success",
        "message": f"已成功将《{journal_name}》收录至选刊台账",
        "remaining": len(rows),
    }


@router.get("/track/export")
def api_export_track(
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    uid: Optional[str] = Query(None, alias="user_id"),
):
    """导出并下载当前用户带自适应筛选样式的 Excel 追踪台账。"""
    effective_uid = uid or user_id
    xlsx_path = get_track_xlsx_path(user_id=effective_uid)
    if not os.path.exists(xlsx_path):
        rows = load_track(user_id=effective_uid)
        save_track(rows, user_id=effective_uid)

    if not os.path.exists(xlsx_path):
        raise HTTPException(status_code=404, detail="追踪表文件尚未生成")

    download_name = (
        f"选刊决策台账_{effective_uid}.xlsx"
        if effective_uid and effective_uid != "default"
        else "选刊追踪表_广州中医药大学.xlsx"
    )

    encoded_filename = quote(download_name)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
    }

    return FileResponse(
        xlsx_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=download_name,
        headers=headers,
    )


@router.get("/filter", response_model=TrackResponseDTO)
def api_filter(
    expr: str = Query(..., description="筛选表达式，如 level=A类2级,oa=否"),
    scope: str = Query("official", description="筛选范围: official(官方136本目录及核心库) / track(个人已追踪台账) / all(全部)"),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    uid: Optional[str] = Query(None, alias="user_id"),
):
    """根据多维复合条件筛选期刊数据（支持个人专属台账范围）。"""
    effective_uid = uid or user_id
    rows = get_filterable_rows(scope=scope, user_id=effective_uid)
    filtered = filter_track_rows(rows, expr)
    return {"total": len(filtered), "records": filtered}
