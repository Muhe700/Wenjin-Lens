# -*- coding: utf-8 -*-
"""
tests/test_risk.py
==================
中科院国际预警期刊排查单元测试。
"""
import pytest
from app.services.risk_service import check_cas_warning, load_warning_db


def test_load_warning_db():
    db = load_warning_db()
    assert isinstance(db, dict)
    assert "journals" in db
    assert len(db["journals"]) > 0


def test_check_cas_warning_hit():
    # Cancers 处于 2024 预警名单中
    res = check_cas_warning("Cancers", issn="2072-6694")
    assert res is not None
    assert res["is_warned"] is True
    assert "MDPI" in res.get("publisher", "")


def test_check_cas_warning_clean():
    # 正常期刊不应命中预警
    res = check_cas_warning("中华中医药杂志", issn="1673-1727")
    assert res is None
