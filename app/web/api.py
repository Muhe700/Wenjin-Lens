# -*- coding: utf-8 -*-
"""
app.web.api
===========
FastAPI Web API 核心服务入口：
采用模块化路由器架构，聚合选刊检索、台账决策、目录统计及静态前端资源。
各模块之间通过标准 RESTful 接口与 Pydantic 契约规范传输数据。
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from fastapi.responses import FileResponse, Response

from app.web.routers import catalog_router, search_router, track_router

app = FastAPI(
    title="文津·选刊助手 API (Wenjin-Lens)",
    description="面向高校教师与学术研究者的智能选刊与期刊等级核验 API 服务（模块化微内核架构）",
    version="2.2.0",
)

# 允许跨域请求，保障前后端彻底解耦与独立部署
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载各领域模块化路由器
app.include_router(search_router)
app.include_router(track_router)
app.include_router(catalog_router)

# 挂载静态 Web 资源目录
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# 挂载 favicon.ico 响应，防止浏览器 404
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    fav_path = os.path.join(static_dir, "favicon.ico")
    if os.path.exists(fav_path):
        return FileResponse(fav_path)
    logo_path = os.path.join(static_dir, "images", "logo.jpg")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/jpeg")
    return Response(status_code=204)

if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
