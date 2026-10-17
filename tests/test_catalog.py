# -*- coding: utf-8 -*-
"""
tests/test_catalog.py
=====================
目录服务、中文核心库与 CAS JCR 分区查询单元测试。
"""
import pytest
from app.services.catalog_service import (
    find_chinese_core,
    get_cas_categories,
    get_cas_journals,
    load_catalog,
    load_chinese_core,
    locate_journal_in_all_indexes,
    search_catalog,
)


def test_load_catalog():
    catalog = load_catalog()
    assert isinstance(catalog, dict)
    assert "journals" in catalog
    assert "categories" in catalog
    assert len(catalog["journals"]) > 0


def test_search_catalog():
    catalog = load_catalog()
    results = search_catalog(catalog, "针灸")
    assert isinstance(results, list)
    assert len(results) > 0
    # 检查返回期刊中含有针灸相关内容
    assert any("针灸" in j.get("name", "") for j in results)


def test_chinese_core():
    core = load_chinese_core()
    assert isinstance(core, list)
    assert len(core) > 0

    # 测试检索已知核心期刊
    j_rec, kb_rec, match_type = find_chinese_core("中国中西医结合杂志")
    assert j_rec is not None
    assert "中国中西医结合杂志" in j_rec.get("name", "")
    assert "核心库" in match_type


def test_locate_journal_in_all_indexes():
    res = locate_journal_in_all_indexes("中华中医药杂志")
    assert res["found"] is True
    assert "matches" in res
    assert len(res["matches"]["gzucms"]) > 0 or len(res["matches"]["cscd"]) > 0


def test_cas_journals_query():
    # 测试中科院数据库分类与期刊查询
    categories = get_cas_categories()
    assert isinstance(categories, list)

    res = get_cas_journals(page=1, page_size=5)
    assert "journals" in res
    assert "total" in res
    assert isinstance(res["journals"], list)
