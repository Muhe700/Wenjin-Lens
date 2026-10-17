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


def test_user_track_isolation_and_operations(tmp_path, monkeypatch):
    """验证多用户台账隔离、单期刊删减与台账全量清空功能。"""
    from app.services.track_service import clear_track, delete_track_row, upsert_track

    # 设置虚拟隔离测试目录
    monkeypatch.setattr("app.config.TRACK_DATA_DIR", str(tmp_path))

    user_a = "user_test_a"
    user_b = "user_test_b"

    row_a = {"期刊名称": "用户A专属期刊", "广中医认定级别": "A类1级", "ISSN / CN": "ISSN 1111-2222"}
    row_b = {"期刊名称": "用户B专属期刊", "广中医认定级别": "B类", "ISSN / CN": "ISSN 3333-4444"}

    # 1. 验证用户 A 写入，用户 B 互不干扰
    upsert_track(row_a, user_id=user_a)
    assert len(load_track(user_id=user_a)) == 1
    assert load_track(user_id=user_a)[0]["期刊名称"] == "用户A专属期刊"
    assert len(load_track(user_id=user_b)) == 0

    # 2. 验证用户 B 写入自己的期刊
    upsert_track(row_b, user_id=user_b)
    assert len(load_track(user_id=user_b)) == 1
    assert load_track(user_id=user_b)[0]["期刊名称"] == "用户B专属期刊"
    assert len(load_track(user_id=user_a)) == 1

    # 3. 验证台账期刊删除 (删减功能)
    found, remaining = delete_track_row("用户A专属期刊", user_id=user_a)
    assert found is True
    assert remaining == 0
    assert len(load_track(user_id=user_a)) == 0
    # 用户 B 的期刊不受影响
    assert len(load_track(user_id=user_b)) == 1

    # 4. 验证删除不存在的期刊
    not_found, _ = delete_track_row("不存在的期刊", user_id=user_b)
    assert not_found is False

    # 5. 验证台账清空 (Clear 功能)
    clear_track(user_id=user_b)
    assert len(load_track(user_id=user_b)) == 0
