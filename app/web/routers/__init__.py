# -*- coding: utf-8 -*-
"""
app.web.routers
===============
FastAPI 路由模块包：按功能领域将 API 分解为检索核验、台账管理和目录统计三大独立子路由。
"""
from app.web.routers.catalog_router import router as catalog_router
from app.web.routers.search_router import router as search_router
from app.web.routers.track_router import router as track_router

__all__ = ["search_router", "track_router", "catalog_router"]
