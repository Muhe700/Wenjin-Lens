# -*- coding: utf-8 -*-
"""
app.services
============
业务逻辑服务层：统一选刊领域服务、官方目录检索、知识库读写、选刊追踪表及 Gemini AI 联网核验。
"""
from app.services.journal_service import JournalService

__all__ = ["JournalService"]
