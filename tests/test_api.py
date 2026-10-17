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


def test_api_refresh_endpoint(monkeypatch):
    """验证 /api/refresh 接口能够成功处理期刊核验（包含中科院期刊与普通期刊分支）。"""
    from app.services.journal_service import JournalService

    def mock_fetch_open_academic(issn=None, journal_name=None):
        return {
            "source": "OpenAcademic",
            "openalex": {"id": "W123", "display_name": journal_name, "issn": [issn] if issn else []},
            "doaj": None,
            "apc_summary": "官方APC: 免费",
            "homepage": "https://acsjournals.onlinelibrary.wiley.com/journal/15424863",
            "review_cycle": "12周",
            "is_oa": True,
        }

    monkeypatch.setattr("app.services.journal_service.fetch_open_academic_metadata", mock_fetch_open_academic)
    monkeypatch.setattr("app.services.journal_service.fetch_journal_from_gemini", lambda *a, **k: (False, "mocked in test"))

    # 针对 CAS 期刊测试 refresh
    resp = client.post("/api/refresh?q=CA-A CANCER JOURNAL FOR CLINICIANS")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "data" in data


def test_api_multi_user_track_and_delete_endpoints(tmp_path, monkeypatch):
    """验证 API 层的多用户台账隔离、单期刊删除与清空功能。"""
    monkeypatch.setattr("app.config.TRACK_DATA_DIR", str(tmp_path))

    headers_a = {"X-User-ID": "test_prof_zhang"}
    headers_b = {"X-User-ID": "test_prof_li"}

    # 1. 验证用户 张老师 通过搜索自动入库
    resp_search = client.get("/api/search?q=中草药", headers=headers_a)
    assert resp_search.status_code == 200

    # 检查用户 张老师 的台账中有且仅有 1 篇
    resp_track_a = client.get("/api/track", headers=headers_a)
    assert resp_track_a.status_code == 200
    assert resp_track_a.json()["total"] == 1
    assert resp_track_a.json()["records"][0]["期刊名称"] == "中草药"

    # 检查用户 李老师 的台账为空
    resp_track_b = client.get("/api/track", headers=headers_b)
    assert resp_track_b.status_code == 200
    assert resp_track_b.json()["total"] == 0

    # 2. 验证用户 李老师 手动 POST 添加期刊
    resp_add = client.post("/api/track?name=中国中药杂志", headers=headers_b)
    assert resp_add.status_code == 200
    assert resp_add.json()["status"] == "success"
    assert client.get("/api/track", headers=headers_b).json()["total"] == 1

    # 3. 验证删除期刊接口 DELETE /api/track?name=...
    resp_del = client.delete("/api/track?name=中草药", headers=headers_a)
    assert resp_del.status_code == 200
    assert resp_del.json()["status"] == "success"
    assert resp_del.json()["remaining"] == 0
    assert client.get("/api/track", headers=headers_a).json()["total"] == 0
    # 李老师的台账不受任何影响
    assert client.get("/api/track", headers=headers_b).json()["total"] == 1

    # 4. 验证清空台账接口 DELETE /api/track/clear
    resp_clear = client.delete("/api/track/clear", headers=headers_b)
    assert resp_clear.status_code == 200
    assert resp_clear.json()["status"] == "success"
    assert client.get("/api/track", headers=headers_b).json()["total"] == 0

    # 5. 验证导出台账
    resp_export = client.get("/api/track/export", headers=headers_a)
    assert resp_export.status_code == 200


def test_api_refresh_failure_handling(monkeypatch):
    """验证当 AI 接口报错且开放学术库未找到时，系统拒绝虚假成功，返回 400 且不写入知识库空白记录。"""
    from unittest.mock import patch
    from app.services.kb_service import load_kb

    bogus_name = "完全虚构测试刊名_999xyz"

    def mock_fetch_gemini(journal_name, api_key=None, proxy=None):
        return False, "Google API 异常 (HTTP 429: Quota exceeded)"

    def mock_fetch_open_academic(issn=None, journal_name=None):
        return {
            "source": "OpenAcademic",
            "openalex": None,
            "doaj": None,
            "apc_summary": "",
            "homepage": "",
            "review_cycle": "",
            "is_oa": None,
        }

    monkeypatch.setattr("app.services.journal_service.fetch_journal_from_gemini", mock_fetch_gemini)
    monkeypatch.setattr("app.services.journal_service.fetch_open_academic_metadata", mock_fetch_open_academic)

    resp = client.post(f"/api/refresh?q={bogus_name}")
    # 必须返回 400，绝不允许返回 200 虚假成功！
    assert resp.status_code == 400
    err_detail = resp.json().get("detail", "")
    assert "深度联网查证未完成" in err_detail or "Quota exceeded" in err_detail or "未检索到" in err_detail

    # 验证知识库中绝对没有被污染写入该期刊的空白壳
    kb = load_kb()
    assert bogus_name not in kb.get("records", {})




