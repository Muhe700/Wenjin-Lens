# -*- coding: utf-8 -*-
"""
app.web.routers.search_router
=============================
期刊检索与 AI 联网核验路由：
提供期刊 9 项选刊核心指标检索、收录定级规则判定、候选词推荐及基于 OpenAlex/DOAJ/Gemini 的深度事实查证。
"""
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Query

from app.models.schemas import RefreshResponseDTO, SearchResponseDTO
from app.services.journal_service import JournalService

router = APIRouter(prefix="/api", tags=["选刊检索与深度核验"])


@router.get("/search", response_model=SearchResponseDTO)
def api_search(
    q: str = Query(..., description="期刊名称、ISSN、CN 或 索引关键词"),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    uid: Optional[str] = Query(None, alias="user_id"),
):
    """核心检索接口：输入期刊名/ISSN/CN/索引规则，返回 9 项选刊核心数据。"""
    query_str = (q or "").strip()
    if not query_str:
        raise HTTPException(status_code=400, detail="查询关键词不能为空")

    effective_uid = uid or user_id
    result = JournalService.search(query_str, auto_track=True, user_id=effective_uid)
    if result.get("type") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "检索失败"))

    return result


@router.post("/refresh", response_model=RefreshResponseDTO)
def api_refresh(q: str = Query(..., description="待联网查证的期刊名称")):
    """聚合 Google Gemini 与 OpenAlex / DOAJ 开放学术生态，联网核验指标并自动回写知识库。"""
    query_str = (q or "").strip()
    if not query_str:
        raise HTTPException(status_code=400, detail="期刊名称不能为空")

    success, res = JournalService.refresh(query_str)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=res.get("error", "联网核验未完成，请检查配置或网络状态"),
        )
    return res
