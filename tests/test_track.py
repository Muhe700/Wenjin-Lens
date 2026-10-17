# -*- coding: utf-8 -*-
"""
tests/test_track.py
===================
选刊决策台账装配与多维条件筛选单元测试。
"""
import pytest
from app.services.track_service import (
    build_track_row,
    filter_track_rows,
    get_filterable_rows,
    load_track,
)


def test_build_track_row():
    journal_rec = {
        "name": "测试期刊",
        "issn": "1234-5678",
        "cn": "11-0000/R",
    }
    kb_rec = {
        "basic": {"name": "测试期刊", "issn": "1234-5678", "cn": "11-0000/R"},
        "indexes": {"indexes_verified": True},
        "impact_factor": {"jcr_if": "3.5", "cas_zone": "中科院2区"},
        "publication_mode": "订阅模式（非OA）",
        "apc_fee": "免版面费",
        "sources": ["https://example.com"],
    }
    catalog = {"journals": [], "rules": []}

    row = build_track_row(journal_rec, kb_rec, catalog, best_level="A2")
    assert row["期刊名称"] == "测试期刊"
    assert "ISSN 1234-5678" in row["ISSN / CN"]
    assert "CN 11-0000/R" in row["ISSN / CN"]
    assert row["广中医认定级别"] == "A类2级"
    assert "免版面费" in row["出版方式与版面费"]


def test_filter_track_rows():
    sample_rows = [
        {
            "期刊名称": "期刊甲",
            "广中医认定级别": "A类2级",
            "出版方式与版面费": "订阅模式；免版面费",
            "中科院分区": "中科院2区",
        },
        {
            "期刊名称": "期刊乙",
            "广中医认定级别": "B类",
            "出版方式与版面费": "开放获取(OA)；版面费: 2500 USD",
            "中科院分区": "",
        },
    ]

    # 按级别筛选
    hits = filter_track_rows(sample_rows, "level=A类2级")
    assert len(hits) == 1
    assert hits[0]["期刊名称"] == "期刊甲"

    # 按 OA 模式筛选
    hits_no_oa = filter_track_rows(sample_rows, "oa=否")
    assert len(hits_no_oa) == 1
    assert hits_no_oa[0]["期刊名称"] == "期刊甲"


def test_get_filterable_rows():
    rows = get_filterable_rows(scope="official")
    assert isinstance(rows, list)
    assert len(rows) > 0
    assert any("期刊名称" in r for r in rows)
