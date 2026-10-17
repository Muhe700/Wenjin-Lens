# -*- coding: utf-8 -*-
"""
build_catalog.py
================
从《广州中医药大学重要期刊目录（试行）》(广中医校办〔2020〕308号) 的 DOCX
生成机器可读的检索目录文件：
  - journal_catalog.json   结构化检索目录（主数据）
  - journal_catalog.csv    扁平检索目录（便于查阅 / Excel）

用法：
  python3 build_catalog.py <docx路径> [输出目录]
"""
import json
import re
import sys
import csv
import os
from datetime import date

import docx


LEVEL_ORDER = {"A1": 1, "A2": 2, "A3": 3, "A4": 4, "B": 5}

# 索引类条目的规则键（供主程序做“收录索引 → 广中医级别”映射）
# 注意匹配顺序：必须长关键词优先（如“中文社会科学引文索引”同时含
# “社会科学引文索引”和“科学引文索引”子串，需先匹配 CSSCI）。
RULE_KEYWORDS = [
    ("中文社会科学引文索引", "cssci"),
    ("社会科学引文索引", "ssci"),
    ("科学引文索引", "scie"),
    ("中国科学引文数据库", "cscd"),
    ("艺术与人文科学索引", "ahci"),
    ("中文核心期刊要目总览", "pkucore"),
    ("中国人文社会科学核心期刊要览", "chss_core"),
    ("工程索引", "ei"),
    ("社会科学及人文科学会议录索引", "cpci_ssh"),
    ("科学技术会议录索引", "cpci_s"),
    ("科学评论索引", "isr"),
    ("新华文摘", "xhwd"),
    ("人民日报", "rdyb"),
    ("光明日报", "gmrb"),
    ("解放军报", "jfjb"),
    ("经济日报", "jjrb"),
    ("人大复印报刊资料", "rdfy"),
    ("南方日报", "nfyb"),
    ("求是", "qiushi"),
]


def clean(text):
    """去掉单元格内多余空白，保留中文内容。"""
    if text is None:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def parse_issn_cn(text):
    """从单元格文本中提取 ISSN / CN，返回 (issn, cn)。"""
    text = re.sub(r"\s+", "", text or "")
    issn = ""
    m = re.search(r"ISSN[:：]?([0-9]{4}-[0-9]{3}[0-9Xx])", text)
    if m:
        issn = m.group(1).upper()
    cn = ""
    m = re.search(r"CN[:：]?([0-9]{2}-[0-9]{4}/[A-Z0-9]+)", text)
    if m:
        cn = m.group(1)
    return issn, cn


def build_rule_key(name, remark, level):
    """为索引/规则类条目生成规则键（如 scie_1、cscd_core）。"""
    text = name + " " + (remark or "")
    for kw, base in RULE_KEYWORDS:
        if kw in text:
            if base in ("scie", "ssci"):
                zone = re.search(r"([1-4])区", text)
                if zone:
                    return f"{base}_zone{zone.group(1)}"
            if base == "cscd":
                return "cscd_core" if "核心" in text else "cscd_ext"
            if base == "cssci":
                return "cssci_core" if "核心" in text else "cssci_ext"
            return base
    return None


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_src = os.path.join(base, "data", "raw", "广中医重要期刊目录.docx")
    default_out = os.path.join(base, "data", "catalog")

    if len(sys.argv) >= 2:
        src = sys.argv[1]
    else:
        src = default_src

    if len(sys.argv) >= 3:
        out_dir = sys.argv[2]
    else:
        out_dir = default_out

    if not os.path.exists(src):
        print(f"错误: 原始文档未找到: {src}")
        print("用法: python scripts/build_catalog.py [docx路径] [输出目录]")
        sys.exit(1)

    d = docx.Document(src)
    t = d.tables[0]

    meta = {
        "document": "广州中医药大学重要期刊目录（试行）",
        "document_no": "广中医校办〔2020〕308号",
        "issued_by": "广州中医药大学",
        "issued_date": "2020-12-08",
        "scope": "本期刊目录仅作为职称评审使用",
        "generated_from": os.path.basename(src),
        "generated_at": date.today().isoformat(),
        "notes": [
            "1.本表中所列刊物如进入更高级别，则按高级别期刊认定。",
            "2.SCIE收录期刊分区是指中国科学院文献情报中心期刊分区（大类小类均予认定），以论文正式发表当年版本为准。若因特殊原因未提供分区，以可查年限中最近年份分区情况为准。",
            "3.根据SSCI收录期刊分区情况，2020年12月31日前发表论文分区按科睿唯安执行，2021年1月1日起发表文章分区按中国科学院文献情报中心期刊分区（大类小类均予认定）执行。期刊分区情况以论文发表当年版本为准。",
            "4.发表在本单位期刊《新中医》、《广州中医药大学学报》、《中医肿瘤学杂志》的论文，每人每次职称申报时仅可使用1篇作为有效业绩。",
            "5.本期刊目录仅作为职称评审使用。",
        ],
    }

    categories = []   # 分段：{level, name, items:[...]}
    journals = []     # 扁平化：具体期刊
    rules = []        # 扁平化：索引/规则类条目

    current = None
    notes_text = ""
    for row in t.rows:
        cells = [c.text for c in row.cells]
        c0 = clean(cells[0])
        # 类别头行（合并单元格：四列内容相同）
        if c0 in ("A类1级", "A类2级", "A类3级", "A类4级", "B类（校内限定期刊）"):
            level = {"A类1级": "A1", "A类2级": "A2", "A类3级": "A3", "A类4级": "A4",
                     "B类（校内限定期刊）": "B"}[c0]
            current = {"level": level, "name": c0, "items": []}
            categories.append(current)
            continue
        # 表头行
        if c0 == "序号":
            continue
        # 备注行
        if c0.startswith("注："):
            notes_text = "\n".join(clean(x) for x in cells if clean(x))
            continue
        if current is None:
            continue

        serial = c0
        name = clean(cells[1])
        publisher = clean(cells[2])
        remark = clean(cells[3]) if len(cells) > 3 else ""
        if not name:
            continue

        item = {
            "serial": serial,
            "name": name,
            "publisher": publisher,
            "remark": remark,
        }
        current["items"].append(item)

        if current["level"] == "B":
            # B类：主办单位/出版单位 + 刊号列
            issn, cn = parse_issn_cn(remark)
            # 名称可能含换行的补充信息（如 医学与哲学（对应曾用名人文社会医学版））
            aliases = []
            m = re.search(r"[（(]([^）)]*曾用名[^）)]*)[）)]", name)
            if m:
                aliases.append(m.group(1))
            record = {
                "name": name,
                "aliases": aliases,
                "type": "journal",
                "level": current["level"],
                "category": current["name"],
                "publisher": publisher,
                "issn": issn,
                "cn": cn,
                "remark": remark,
                "source": "B类（校内限定期刊）",
            }
            journals.append(record)
        else:
            issn, cn = parse_issn_cn(remark)
            rule_key = build_rule_key(name, remark, current["level"])
            if rule_key:
                rules.append({
                    "key": rule_key,
                    "name": name,
                    "level": current["level"],
                    "category": current["name"],
                    "publisher": publisher,
                    "desc": remark,
                })
            else:
                # A类中列出的具体期刊（如 科学通报、中国社会科学、求是）
                journals.append({
                    "name": name,
                    "aliases": [],
                    "type": "journal",
                    "level": current["level"],
                    "category": current["name"],
                    "publisher": publisher,
                    "issn": issn,
                    "cn": cn,
                    "remark": remark,
                    "source": f"{current['name']} 直接列名",
                })

    catalog = {
        "meta": meta,
        "categories": categories,
        "journals": journals,
        "rules": rules,
    }

    json_path = os.path.join(out_dir, "journal_catalog.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    csv_path = os.path.join(out_dir, "journal_catalog.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["类别", "级别", "序号", "期刊名称/索引", "主办单位/出版单位", "ISSN", "CN", "条目类型"])
        for cat in categories:
            for it in cat["items"]:
                issn, cn = parse_issn_cn(it.get("remark", ""))
                w.writerow([cat["name"], cat["level"], it["serial"], it["name"],
                            it["publisher"], issn, cn,
                            "规则/索引" if cat["level"] != "B" else "期刊"])

    # 统计输出
    print(f"检索目录已生成：")
    print(f"  JSON: {json_path}")
    print(f"  CSV : {csv_path}")
    print(f"  类别：{[(c['level'], len(c['items'])) for c in categories]}")
    print(f"  具体期刊数（含A类列名期刊）：{len(journals)}")
    print(f"  索引/规则条目数：{len(rules)}")
    print(f"  备注：{notes_text[:80]}...")


if __name__ == "__main__":
    main()
