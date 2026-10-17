# -*- coding: utf-8 -*-
"""
tests/test_api.py
=================
FastAPI 核心 RESTful API 接口与 DTO 契约集成测试。
"""
import pytest
from fastapi.testclient import TestClient
from app.web.api import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "Wenjin-Lens"


def test_api_favicon():
    response = client.get("/favicon.ico")
    assert response.status_code in (200, 204)


def test_api_catalog():
    response = client.get("/api/catalog")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "journals" in data
    assert data["total_journals"] > 0


def test_api_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "catalog_journals" in data
    assert "kb_records" in data
    assert "track_records" in data


def test_api_search_success():
    response = client.get("/api/search?q=中国中西医结合杂志")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "journal"
    assert data["name"] == "中国中西医结合杂志"
    assert "level_info" in data
    assert "track_row" in data


def test_api_search_empty():
    response = client.get("/api/search?q=")
    assert response.status_code == 400


def test_api_track():
    response = client.get("/api/track")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "records" in data


def test_api_filter():
    response = client.get("/api/filter?expr=level=B类&scope=official")
    assert response.status_code == 200
    data = response.json()
    assert "records" in data
    assert data["total"] > 0


def test_api_cas_categories():
    response = client.get("/api/indexes/cas/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert len(data["categories"]) > 0


def test_api_search_chinese_core_journal():
    """验证检索全国中文核心期刊（如中草药、中国中药杂志）返回 200，且 level_info 不触发校验异常。"""
    for q in ("中草药", "中国中药杂志"):
        resp = client.get(f"/api/search?q={q}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "journal"
        assert "level_info" in data
        assert data["level_info"]["level"] in ("A1", "A2", "A3", "A4", "B", None)


def test_api_search_unrated_journal_with_none_level(tmp_path, monkeypatch):
    """验证当期刊未定级 (level is None) 时，FastAPI ResponseValidationError 不会发生，返回 200 OK。"""
    from app.models.schemas import LevelInfoDTO, SearchResponseDTO
    dto = LevelInfoDTO(level=None, label="不符合/待核验", reasons=[], upgraded=False)
    assert dto.level is None
    assert dto.label == "不符合/待核验"

    # 模拟知识库中有一本非目录非核心未定级期刊
    from app.services.kb_service import load_kb, upsert_kb_record
    kb = load_kb()
    test_journal = "测试未定级非核心学报"
    upsert_kb_record(kb, test_journal, {
        "basic": {"name": test_journal, "in_catalog": False},
        "indexes": {"indexes_verified": True},
        "scope": "中西医结合实验研究"
    })
    try:
        resp = client.get(f"/api/search?q={test_journal}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "journal"
        assert data["level_info"]["level"] is None
        assert data["level_info"]["label"] == "不符合/待核验"
    finally:
        # 清理测试数据
        kb = load_kb()
        if test_journal in kb.get("records", {}):
            del kb["records"][test_journal]
            from app.services.kb_service import save_kb
            save_kb(kb)


def test_academic_api_resilience(monkeypatch):
    """验证当 OpenAlex 返回的 issn 为 None、空列表或缺失时，fetch_open_academic_metadata 健壮容错不崩溃。"""
    from app.services.academic_api import fetch_open_academic_metadata

    def mock_fetch_openalex(issn, journal_name):
        return {
            "success": True,
            "data": {
                "source": "OpenAlex",
                "display_name": "Mock Journal",
                "publisher": "Mock University",
                "homepage_url": "https://example.com",
                "is_oa": True,
                "is_in_doaj": False,
                "apc_usd": 1500,
                "apc_prices": [],
                "cited_by_count": 10,
                "works_count": 100,
                "h_index": 2,
                "issn": None,  # 模拟造成 NoneType subscriptable 的核心场景
                "type": "journal",
            },
        }

    monkeypatch.setattr("app.services.academic_api.fetch_openalex_journal", mock_fetch_openalex)
    meta = fetch_open_academic_metadata(journal_name="Mock Journal")
    assert meta["openalex"] is not None
    assert meta["openalex"]["issn"] is None
    assert meta["apc_summary"] == "官方APC: $1500"
    assert meta["homepage"] == "https://example.com"
    assert meta["is_oa"] is True


