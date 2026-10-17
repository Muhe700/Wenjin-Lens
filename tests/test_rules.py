# -*- coding: utf-8 -*-
"""
tests/test_rules.py
===================
选刊规则判定与从高认定引擎单元测试。
"""
import pytest
from app.core.rules import compute_level, find_rule, normalize


def test_normalize():
    assert normalize("  中华中医药杂志  ") == "中华中医药杂志"
    assert normalize("Journal of TCM (English)") == "journaloftcm(english)"
    assert normalize("1673-1727") == "1673-1727"
    assert normalize("《中草药》") == "中草药"
    assert normalize("") == ""


def test_compute_level_catalog_b():
    # 308 目录内的 B 类期刊
    catalog = {"rules": []}
    journal_rec = {"name": "广州中医药大学学报", "level": "B", "category": "重要期刊B类"}
    kb_rec = None
    level, reasons, upgraded = compute_level(catalog, journal_rec, kb_rec)
    assert level == "B"
    assert upgraded is False


def test_compute_level_cscd_core_a2():
    # CSCD 核心版折算 A类2级，同时命中北大核心 (A3)
    catalog = {
        "rules": [
            {"key": "cscd_core", "name": "CSCD核心库", "level": "A2"},
            {"key": "pkucore", "name": "中文核心期刊", "level": "A3"},
        ]
    }
    journal_rec = {"name": "中华中医药杂志", "level": "B", "category": "重要期刊B类"}
    kb_rec = {
        "indexes": {
            "indexes_verified": True,
            "cscd_core": True,
            "pkucore": True,
        }
    }
    # 根据从高认定原则，目录B类升级为 A2
    level, reasons, upgraded = compute_level(catalog, journal_rec, kb_rec)
    assert level == "A2"
    assert upgraded is True


def test_compute_level_pkucore_a3():
    # 纯北大核心折算 A类3级
    catalog = {
        "rules": [
            {"key": "pkucore", "name": "中文核心期刊", "level": "A3"},
        ]
    }
    journal_rec = None
    kb_rec = {
        "indexes": {
            "indexes_verified": True,
            "cscd_core": False,
            "pkucore": True,
        }
    }
    level, reasons, upgraded = compute_level(catalog, journal_rec, kb_rec)
    assert level == "A3"
    assert upgraded is False


def test_find_rule():
    catalog = {
        "rules": [
            {"key": "pkucore", "name": "中文核心期刊要目总览", "level": "A3"},
            {"key": "cscd_core", "name": "中国科学引文数据库核心库", "level": "A2"},
        ]
    }
    res = find_rule(catalog, "北大核心")
    assert res is not None
    key, level, name = res
    assert level == "A3"
    assert key == "pkucore"

    res_none = find_rule(catalog, "一个完全不存在的非索引长文本名称测试")
    assert res_none is None
