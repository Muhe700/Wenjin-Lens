# -*- coding: utf-8 -*-
"""
app.web.routers.track_router
============================
决策台账与多维筛选路由：
提供决策追踪台账读取、复合多维筛选以及标准自适应样式 Excel (.xlsx) 导出下载。
"""
import os
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.config import get_track_xlsx_path
from app.models.schemas import TrackResponseDTO
from app.services.track_service import filter_track_rows, get_filterable_rows, load_track, save_track

router = APIRouter(prefix="/api", tags=["决策台账与智能筛选"])


@router.get("/track", response_model=TrackResponseDTO)
def api_get_track():
    """获取所有已记录的期刊追踪台账。"""
    rows = load_track()
    return {"total": len(rows), "records": rows}


@router.get("/track/export")
def api_export_track():
    """导出并下载带自动筛选样式的 Excel 追踪表。"""
    xlsx_path = get_track_xlsx_path()
    if not os.path.exists(xlsx_path):
        rows = load_track()
        save_track(rows)

    if not os.path.exists(xlsx_path):
        raise HTTPException(status_code=404, detail="追踪表文件尚未生成")

    return FileResponse(
        xlsx_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="选刊追踪表_广州中医药大学.xlsx",
    )


@router.get("/filter", response_model=TrackResponseDTO)
def api_filter(
    expr: str = Query(..., description="筛选表达式，如 level=A类2级,oa=否"),
    scope: str = Query("official", description="筛选范围: official(官方136本目录及核心库) / track(个人已追踪台账) / all(全部)")
):
    """根据多维复合条件筛选期刊数据。"""
    rows = get_filterable_rows(scope=scope)
    filtered = filter_track_rows(rows, expr)
    return {"total": len(filtered), "records": filtered}
