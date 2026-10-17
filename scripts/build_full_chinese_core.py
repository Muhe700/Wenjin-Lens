# -*- coding: utf-8 -*-
"""
scripts/build_full_chinese_core.py
==================================
拉取并构建全国中文核心学术期刊与 CSCD 来源期刊全量数据库 (chinese_core_journals.json)。
整合两大开源学术源：
1. doublessay/cnki-journal-info (10,860本期刊元数据：ISSN, CN, 主办单位, 复合影响因子, 综合影响因子, 专辑, CNKI链接)
2. ShutterZor/ranking-kit (官方核心库/扩展库精确分级：CSCD核心库/扩展库, 北大核心第10版, CSSCI)
"""
import csv
import io
import json
import os
import re
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "catalog", "chinese_core_journals.json")

CNKI_DATASET_URL = "https://raw.githubusercontent.com/doublessay/cnki-journal-info/main/dataset/2023-11-30.csv"
CSCD_RANK_URL = "https://raw.githubusercontent.com/ShutterZor/ranking-kit/main/show_ranking/data/cscdRankingName.js"
PKU_RANK_URL = "https://raw.githubusercontent.com/ShutterZor/ranking-kit/main/show_ranking/data/pkuRankingName.js"
CSSCI_RANK_URL = "https://raw.githubusercontent.com/ShutterZor/ranking-kit/main/show_ranking/data/cssciRankingName.js"


def fetch_url(url: str, timeout: int = 35) -> str:
    print(f"正在下载数据源: {url[:80]}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def normalize_name(name: str) -> str:
    if not name:
        return ""
    # 去除特殊标点与空格
    return re.sub(r"[\s\.\(\)（）\·\/\-]+", "", name).upper()


def build():
    # 1. 下载权威分级字典
    print(">>> 步骤 1/4: 下载权威期刊分级数据 (CSCD, 北大核心, CSSCI)...")
    cscd_raw = fetch_url(CSCD_RANK_URL)
    pku_raw = fetch_url(PKU_RANK_URL)
    cssci_raw = fetch_url(CSSCI_RANK_URL)

    # 解析 CSCD (区分 核心库 与 扩展库)
    cscd_map = {}
    for name, cscd_type in re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', cscd_raw):
        if name != "中文刊名":
            cscd_map[name.strip()] = cscd_type.strip()
            cscd_map[normalize_name(name)] = cscd_type.strip()
    print(f"CSCD 分级索引建立: {len(cscd_map)} 个映射条目")

    # 解析 北大核心
    pku_set = set()
    for name in re.findall(r'"([^"]+)"\s*:', pku_raw):
        if name != "中文刊名":
            pku_set.add(name.strip())
            pku_set.add(normalize_name(name))
    print(f"北大核心索引建立: {len(pku_set)} 个映射条目")

    # 解析 CSSCI
    cssci_set = set()
    for name, _ in re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', cssci_raw):
        if name != "中文刊名":
            cssci_set.add(name.strip())
            cssci_set.add(normalize_name(name))
    print(f"CSSCI 索引建立: {len(cssci_set)} 个映射条目")

    # 2. 下载 CNKI 全量 10,860 种期刊元数据
    print(">>> 步骤 2/4: 下载并解析 CNKI 全量学术期刊元数据...")
    cnki_raw = fetch_url(CNKI_DATASET_URL, timeout=45)
    reader = csv.DictReader(io.StringIO(cnki_raw))

    # 3. 筛选并聚合中文核心期刊数据库
    print(">>> 步骤 3/4: 聚合中医学、生命科学、工程技术与人文社科核心名册...")
    journals_dict = {}

    for row in reader:
        name = row.get("期刊名称", "").strip()
        if not name:
            continue
        norm = normalize_name(name)
        indexes_info = row.get("收录信息", "")
        indexes_detail = row.get("收录信息详细", "")

        is_pku = (name in pku_set) or (norm in pku_set) or ("北大核心" in indexes_info) or ("北京大学" in indexes_detail)
        is_cscd_core = (cscd_map.get(name) == "核心库") or (cscd_map.get(norm) == "核心库")
        is_cscd_ext = (cscd_map.get(name) == "扩展库") or (cscd_map.get(norm) == "扩展库")
        if not is_cscd_core and not is_cscd_ext and ("CSCD" in indexes_info):
            # CNKI 标记了 CSCD 但字典未分核心/扩展，默认核心库
            is_cscd_core = True

        is_cssci = (name in cssci_set) or (norm in cssci_set) or ("CSSCI" in indexes_info)
        is_tech_core = "统计源" in indexes_info or "科技核心" in indexes_info

        # 仅收录属于上述任一国内核心索引的期刊
        if not (is_pku or is_cscd_core or is_cscd_ext or is_cssci):
            continue

        # 计算广中医校办308号文件折算认定级别
        # CSCD 核心版折算 A2
        # 北大核心 / CSSCI 来源期刊折算 A3
        # CSCD 扩展版折算 A4
        gz_level = "A4"
        if is_cscd_core:
            gz_level = "A2"
        elif is_pku or is_cssci:
            gz_level = "A3"
        elif is_cscd_ext:
            gz_level = "A4"

        # 构造徽章与附加信息
        extra_badges = []
        if is_cscd_core:
            extra_badges.append("CSCD核心库")
        elif is_cscd_ext:
            extra_badges.append("CSCD扩展库")
        if is_pku:
            extra_badges.append("北大核心(第10版/2023版)")
        if is_cssci:
            extra_badges.append("CSSCI来源期刊")
        if is_tech_core:
            extra_badges.append("中国科技核心(CSTPCD)")

        extra_badges.append(f"广中医认定{gz_level}级")

        subject = row.get("专辑名称", "").strip() or "综合科学"
        sub_subject = row.get("专题名称", "").strip()

        rec = {
            "name": name,
            "issn": row.get("ISSN", "").strip(),
            "cn": row.get("CN", "").strip(),
            "publisher": row.get("主办单位", "").strip(),
            "subject": subject,
            "sub_subject": sub_subject,
            "period": row.get("出版周期", "").strip(),
            "city": row.get("出版地", "").strip(),
            "cscd_core": is_cscd_core,
            "cscd_ext": is_cscd_ext,
            "pkucore": is_pku,
            "cssci": is_cssci,
            "cstpcd": is_tech_core,
            "gzucms_level": gz_level,
            "composite_if": row.get("复合影响因子", "").strip(),
            "comprehensive_if": row.get("综合影响因子", "").strip(),
            "extra": extra_badges,
            "submission_url": row.get("url", "").strip(),
            "doc_count": row.get("出版文献量", "").strip(),
            "cite_count": row.get("总被引次数", "").strip(),
        }
        journals_dict[name] = rec

    # 4. 补充 ranking-kit 中有但 CNKI 数据表中刊名略有差异的纯核心期刊
    for name, cscd_type in cscd_map.items():
        if len(name) < 2 or name.isupper():
            continue
        if name not in journals_dict and normalize_name(name) not in [normalize_name(k) for k in journals_dict.keys()]:
            is_core = cscd_type == "核心库"
            gz_level = "A2" if is_core else "A4"
            journals_dict[name] = {
                "name": name,
                "issn": "",
                "cn": "",
                "publisher": "中国科学引文数据库来源机构",
                "subject": "自然科学与工程技术",
                "sub_subject": "",
                "period": "",
                "city": "",
                "cscd_core": is_core,
                "cscd_ext": not is_core,
                "pkucore": (name in pku_set),
                "cssci": (name in cssci_set),
                "cstpcd": False,
                "gzucms_level": gz_level,
                "composite_if": "",
                "comprehensive_if": "",
                "extra": [f"CSCD{cscd_type}", f"广中医认定{gz_level}级"],
                "submission_url": "",
                "doc_count": "",
                "cite_count": "",
            }

    # 补充北大核心
    for name in pku_set:
        if len(name) < 2 or name.isupper():
            continue
        if name not in journals_dict and normalize_name(name) not in [normalize_name(k) for k in journals_dict.keys()]:
            journals_dict[name] = {
                "name": name,
                "issn": "",
                "cn": "",
                "publisher": "北大中文核心来源机构",
                "subject": "综合科学",
                "sub_subject": "",
                "period": "",
                "city": "",
                "cscd_core": False,
                "cscd_ext": False,
                "pkucore": True,
                "cssci": (name in cssci_set),
                "cstpcd": False,
                "gzucms_level": "A3",
                "composite_if": "",
                "comprehensive_if": "",
                "extra": ["北大核心(第10版)", "广中医认定A3级"],
                "submission_url": "",
                "doc_count": "",
                "cite_count": "",
            }

    # 排序：优先按广中医认定级别 (A2 > A3 > A4)，再按刊名
    level_order = {"A1": 1, "A2": 2, "A3": 3, "A4": 4, "B": 5}
    final_list = list(journals_dict.values())
    final_list.sort(key=lambda x: (level_order.get(x["gzucms_level"], 9), x["name"]))

    # 统计数据
    total_count = len(final_list)
    pku_count = sum(1 for j in final_list if j["pkucore"])
    cscd_core_count = sum(1 for j in final_list if j["cscd_core"])
    cscd_ext_count = sum(1 for j in final_list if j["cscd_ext"])
    cssci_count = sum(1 for j in final_list if j["cssci"])

    output_data = {
        "meta": {
            "title": "全国权威中文核心期刊与引文数据库全景全量合集",
            "version": "2024全量版",
            "pku_version": "北京大学《中文核心期刊要目总览》(第10版/2023-2024最新版)",
            "cscd_version": "中国科学院文献情报中心《中国科学引文数据库》(CSCD 2023-2024年度)",
            "cssci_version": "南京大学中国社会科学研究评价中心《CSSCI来源期刊》(2023-2024)",
            "total_journals": total_count,
            "pku_core_count": pku_count,
            "cscd_core_count": cscd_core_count,
            "cscd_ext_count": cscd_ext_count,
            "cssci_count": cssci_count,
            "acknowledgement_rule": "依据广州中医药大学校办〔2020〕308号文：CSCD核心版折算A2级，北大核心/CSSCI折算A3级，CSCD扩展版折算A4级。",
        },
        "journals": final_list,
    }

    print(f">>> 步骤 4/4: 保存输出至 {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    file_size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print(f"✅ 全量国内核心学术期刊库构建成功！")
    print(f"📊 总入库核心期刊: {total_count} 本")
    print(f"   - 北大中文核心要目总览: {pku_count} 本")
    print(f"   - CSCD 核心库: {cscd_core_count} 本 (折算A2级)")
    print(f"   - CSCD 扩展库: {cscd_ext_count} 本 (折算A4级)")
    print(f"   - CSSCI 南大核心: {cssci_count} 本 (折算A3级)")
    print(f"   - 生成文件大小: {file_size_mb:.2f} MB")


if __name__ == "__main__":
    build()
