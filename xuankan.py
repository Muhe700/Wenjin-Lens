# -*- coding: utf-8 -*-
"""
xuankan.py — 文津·选刊助手（广中医重要期刊检索程序）
===================================================
面向学术研究者与高校教师的智能选刊与期刊等级核验命令行工具。
基于模块化架构设计，通过标准化服务接口调度领域引擎。

用法：
  python xuankan.py "中华中医药杂志"        # 查询期刊（9 项输出并自动记录追踪表）
  python xuankan.py "北大核心"              # 查询索引规则对应的广中医级别
  python xuankan.py "1673-1727"             # 按 ISSN 查询
  python xuankan.py "11-5334/R"             # 按 CN 刊号查询
  python xuankan.py --track                 # 查看期刊追踪表（历史记录）
  python xuankan.py --list                  # 列出目录内全部期刊
  python xuankan.py --search "中医"          # 模糊搜索期刊
  python xuankan.py "期刊名" --json          # JSON 输出
  python xuankan.py --refresh "期刊名"       # 联网刷新/查证该期刊（Gemini）
  python xuankan.py --filter "level=A类2级,oa=否" # 多维条件智能选刊
  python xuankan.py --init-kb               # 由目录初始化/重建知识库骨架
"""
import argparse
import json
import sys

from app.core.constants import LEVEL_LABEL
from app.services.catalog_service import load_catalog, search_catalog
from app.services.display_service import format_journal_display, format_rule_display
from app.services.journal_service import JournalService
from app.services.kb_service import init_kb, load_kb
from app.services.track_service import (
    filter_track_rows,
    load_track,
)


def print_filter_results(hits, filter_expr):
    """美观打印筛选命中的期刊列表。"""
    if not hits:
        print(f"未在追踪表中找到符合条件“{filter_expr}”的期刊。")
        print("提示：--filter 筛选基于已沉淀的期刊追踪表（运行 --track 查看已有条目）。可尝试放宽条件或先查询该刊入库。")
        return

    print(f"\n===== 选刊筛选结果：命中 {len(hits)} 本期刊（条件: {filter_expr}）=====")
    print(f"{'序号':>3}  {'期刊名称':<26} {'广中医级别':<14} {'影响因子':<10} {'出版与版面费':<28} {'审稿周期'}")
    print("-" * 105)
    for i, r in enumerate(hits, 1):
        name = r.get("期刊名称", "")
        if len(name) > 22:
            name = name[:20] + ".."
        lvl = r.get("广中医认定级别", "")
        if_val = r.get("影响因子(JIF)", "").split("（")[0]
        pub = r.get("出版方式与版面费", "")
        if len(pub) > 26:
            pub = pub[:24] + ".."
        cycle = r.get("审稿周期", "")
        if len(cycle) > 24:
            cycle = cycle[:22] + ".."
        print(f"{i:>3}. {name:<26} {lvl:<14} {if_val:<10} {pub:<28} {cycle}")
    print("=" * 105)


def main():
    parser = argparse.ArgumentParser(description="文津·选刊助手：广中医重要期刊 9 项选刊核心信息检索")
    parser.add_argument("query", nargs="?", help="期刊名称 / ISSN / 索引关键词")
    parser.add_argument("--list", action="store_true", help="列出目录内全部期刊")
    parser.add_argument("--search", metavar="KEY", help="按关键词模糊搜索期刊")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    parser.add_argument("--init-kb", action="store_true", help="由目录初始化/重建知识库骨架")
    parser.add_argument("--track", action="store_true", help="查看期刊追踪表（查询记录）")
    parser.add_argument("--refresh", action="store_true", help="联网刷新/核验该期刊指标（Gemini AI）")
    parser.add_argument("--api-key", metavar="KEY", help="临时指定 Gemini API Key")
    parser.add_argument("--filter", metavar="COND", help="多维条件筛选期刊，如：level=A类2级,oa=否")
    args = parser.parse_args()

    catalog = load_catalog()
    kb = load_kb()

    if args.filter:
        rows = load_track()
        hits = filter_track_rows(rows, args.filter)
        print_filter_results(hits, args.filter)
        return

    if args.track:
        rows = load_track()
        if not rows:
            print("追踪表为空。查询过的期刊会自动记录到 data/track/journal_track.xlsx。")
            return
        print(f"追踪表共 {len(rows)} 条（存储于 data/track/journal_track.xlsx）：")
        for i, r in enumerate(rows, 1):
            print(
                f"{i:>2}. {r.get('期刊名称','')} | {r.get('广中医认定级别','')} | "
                f"{r.get('收录索引','')[:30]} | {r.get('核验日期与来源') or '未核验'}"
            )
        return

    if args.init_kb:
        _, out_path = init_kb(catalog, kb)
        print(f"知识库已初始化：{out_path}")
        return

    if args.list:
        for cat in catalog.get("categories", []):
            print(f"===== {cat['name']}（{cat['level']}）=====")
            for it in cat.get("items", []):
                print(f"  {it['serial']:>3}  {it['name']}")
        return

    if args.search:
        hits = search_catalog(catalog, args.search)
        print(f"搜索“{args.search}”命中 {len(hits)} 条：")
        for j in hits:
            print(f"  [{j.get('level','')}] {j.get('name','')} | {j.get('publisher', '')} | ISSN {j.get('issn', '')}")
        return

    if not args.query:
        parser.print_help()
        return

    q = args.query

    # 联网查证 / 刷新
    if args.refresh:
        print(f"正在通过免注册开放学术生态 (OpenAlex / DOAJ) 检索《{q}》权威元数据...")
        success, refresh_res = JournalService.refresh(q, args.api_key)
        if success:
            open_meta = refresh_res.get("open_academic") or {}
            if open_meta.get("homepage") or open_meta.get("apc_summary"):
                print(f"✓ OpenAlex/DOAJ 命中：主页={open_meta.get('homepage') or '未列出'}, APC={open_meta.get('apc_summary') or '免费/未收录'}")
            print(f"✓ 学术指标提炼成功并已同步回写知识库（《{refresh_res.get('journal', q)}》）\n")
        else:
            print(f"【查证提示】{refresh_res.get('error', '联网核验未完成')}\n")

    # 执行统一级联检索
    res = JournalService.search(q, auto_track=True)
    res_type = res.get("type")

    if res_type == "journal":
        if args.json:
            out = {
                "name": res["name"],
                "matched_by": res.get("matched_by"),
                "catalog": res.get("catalog"),
                "kb": res.get("kb", {}),
                "gzucm_level": res.get("level_info", {}),
            }
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            print(
                format_journal_display(
                    res["catalog"],
                    res.get("kb"),
                    catalog,
                    res.get("matched_by", "精确匹配"),
                    kb_only=not res.get("in_catalog", True),
                )
            )
        return

    if res_type == "rule":
        if args.json:
            print(
                json.dumps(
                    {"rule": res["name"], "level": res["level"], "label": res["label"]},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(format_rule_display(res["rule_key"], res["level"], res["name"]))
        return

    if res_type == "rule_need_zone":
        print(res.get("message", ""))
        return

    if res_type == "candidates":
        print(res.get("message", "检索到多个候选："))
        for j in res.get("candidates", [])[:10]:
            print(f"  [{j.get('level','')}] {j.get('name','')} | ISSN {j.get('issn', '')}")
        return

    # not_found or other
    print(f"未在目录中找到“{q}”。可用 --search 关键词 模糊搜索，或确认该期刊是否在目录内（--list 查看全部）。")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except Exception:
            pass
        sys.exit(0)
