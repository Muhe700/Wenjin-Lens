# -*- coding: utf-8 -*-
"""
scripts/build_medline.py
========================
构建 NLM / PubMed 官方 MEDLINE 核心医学期刊库 (medline_journals.json)。
数据源：美国国家医学图书馆 (NLM) 官方公开 FTP 服务器。
"""
import json
import os
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "catalog", "medline_journals.json")
URL = "https://ftp.ncbi.nih.gov/pubmed/J_Medline.txt"


def build():
    print("正在从 NLM 官方 FTP 下载 J_Medline.txt...")
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8", errors="ignore")

    blocks = text.split("--------------------------------------------------------")
    journals = []
    for b in blocks:
        lines = b.strip().split("\n")
        item = {}
        for line in lines:
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip()
                if k == "JournalTitle":
                    item["name"] = v
                elif k == "MedAbbr":
                    item["abbr"] = v
                elif k == "ISSN (Print)":
                    item["issn"] = v
                elif k == "ISSN (Online)":
                    item["eissn"] = v
                elif k == "NlmId":
                    item["nlm_id"] = v
        if item.get("name"):
            journals.append(item)

    print(f"解析完成，收录 MEDLINE 官方核心期刊: {len(journals)} 种")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"total": len(journals), "journals": journals}, f, ensure_ascii=False, indent=2)

    size = os.path.getsize(OUTPUT_PATH) / 1024 / 1024
    print(f"写入文件成功: {OUTPUT_PATH} ({size:.2f} MB)")


if __name__ == "__main__":
    build()
