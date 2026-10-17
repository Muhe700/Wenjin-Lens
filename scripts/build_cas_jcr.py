# -*- coding: utf-8 -*-
"""
scripts/build_cas_jcr.py
========================
构建中科院 1~4 区国际期刊全量开源历史镜像数据库 (cas_jcr.db)。
数据来源：公开开源学术镜像（ShowJCR / FQBJCR2025 & JCR2025）。
包含：SCIE, SSCI, AHCI, ESCI 共 21,000+ 本期刊。
字段：刊名, ISSN, EISSN, Web of Science子库, 大类, 大类分区(1~4区), Top期刊, JCR影响因子, JCR四分位, 广中医折算级别。
并注入历史版本免责声明：中科院分区服务已于2026-09-30关停。
"""
import csv
import io
import os
import sqlite3
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "catalog", "cas_jcr.db")

FQB_PATH = urllib.parse.quote("中科院分区表及JCR原始数据文件/FQBJCR2025-UTF8.csv")
FQB_URL = f"https://raw.githubusercontent.com/hitfyd/ShowJCR/master/{FQB_PATH}"

JCR_PATH = urllib.parse.quote("中科院分区表及JCR原始数据文件/JCR2025-UTF8.csv")
JCR_URL = f"https://raw.githubusercontent.com/hitfyd/ShowJCR/master/{JCR_PATH}"

DISCLAIMER_TEXT = "本中科院分区数据来源于公开历史开源镜像整理版，其中科院分区在线服务已于2026-09-30关停。仅供选刊参考，实际成果认定请以论文发表当年中国科学院文献情报中心官方最新版本为准。"


def fetch_url(url):
    print(f"正在拉取数据: {url[:80]}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def build():
    # 1. 下载并建立 JCR 影响因子映射
    jcr_raw = fetch_url(JCR_URL)
    jcr_reader = csv.DictReader(io.StringIO(jcr_raw))
    jcr_map = {}
    for r in jcr_reader:
        jname = r.get("Journal", "").strip().upper()
        if jname:
            jcr_map[jname] = {
                "jif": r.get("IF(2025)", "").strip(),
                "jcr_q": r.get("IF Quartile(2025)_1", "").strip(),
            }
        issn = r.get("ISSN", "").strip().replace("-", "").upper()
        if issn:
            jcr_map[issn] = {
                "jif": r.get("IF(2025)", "").strip(),
                "jcr_q": r.get("IF Quartile(2025)_1", "").strip(),
            }
    print(f"JCR 指标库加载完成: {len(jcr_map)} 条映射")

    # 2. 下载并清洗中科院分区表升级版
    fqb_raw = fetch_url(FQB_URL)
    fqb_reader = csv.DictReader(io.StringIO(fqb_raw))

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE cas_journals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_lower TEXT NOT NULL,
        issn TEXT,
        eissn TEXT,
        wos_type TEXT,
        category TEXT,
        zone INTEGER,
        zone_raw TEXT,
        is_top INTEGER,
        jif TEXT,
        jcr_quartile TEXT,
        sub_categories TEXT,
        gzucms_level TEXT,
        disclaimer TEXT
    );
    """)

    cursor.execute("CREATE INDEX idx_cas_name ON cas_journals(name_lower);")
    cursor.execute("CREATE INDEX idx_cas_issn ON cas_journals(issn);")
    cursor.execute("CREATE INDEX idx_cas_eissn ON cas_journals(eissn);")
    cursor.execute("CREATE INDEX idx_cas_zone ON cas_journals(zone);")
    cursor.execute("CREATE INDEX idx_cas_cat ON cas_journals(category);")
    cursor.execute("CREATE INDEX idx_cas_gz_level ON cas_journals(gzucms_level);")

    insert_rows = []
    count = 0
    for r in fqb_reader:
        name = r.get("Journal", "").strip()
        if not name:
            continue
        name_lower = name.lower()
        wos = r.get("Web of Science", "").strip()
        cat = r.get("大类", "").strip()
        raw_zone = r.get("大类分区", "").strip()
        zone_val = None
        if raw_zone:
            z_str = raw_zone.split()[0]
            if z_str.isdigit():
                zone_val = int(z_str)

        is_top = 1 if r.get("Top", "").strip() == "是" else 0
        issn_raw = r.get("ISSN/EISSN", "").strip()
        parts = [x.strip() for x in issn_raw.split("/") if x.strip()]
        issn = parts[0] if len(parts) > 0 else ""
        eissn = parts[1] if len(parts) > 1 else ""

        # 小类汇总
        sub_cats = []
        for i in range(1, 7):
            sub_name = r.get(f"小类{i}", "").strip()
            sub_z = r.get(f"小类{i}分区", "").strip()
            if sub_name:
                sub_cats.append(f"{sub_name}({sub_z})" if sub_z else sub_name)
        sub_cat_str = "；".join(sub_cats)

        # 关联 JCR
        j_metric = jcr_map.get(name.upper()) or jcr_map.get(issn.replace("-", "").upper()) or {}
        jif = j_metric.get("jif", "")
        jcr_q = j_metric.get("jcr_q", "")

        # 广中医折算级别
        gz_level = "不符合/待核验"
        if "AHCI" in wos:
            gz_level = "A2"
        elif zone_val == 1:
            gz_level = "A1"
        elif zone_val == 2:
            gz_level = "A2"
        elif zone_val in (3, 4):
            gz_level = "A3"
        elif "ESCI" in wos:
            gz_level = "B"

        insert_rows.append((
            name,
            name_lower,
            issn,
            eissn,
            wos,
            cat,
            zone_val,
            raw_zone,
            is_top,
            jif,
            jcr_q,
            sub_cat_str,
            gz_level,
            DISCLAIMER_TEXT,
        ))
        count += 1

    cursor.executemany("""
    INSERT INTO cas_journals (
        name, name_lower, issn, eissn, wos_type, category, zone, zone_raw,
        is_top, jif, jcr_quartile, sub_categories, gzucms_level, disclaimer
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, insert_rows)

    conn.commit()
    conn.close()

    db_size = os.path.getsize(DB_PATH) / 1024 / 1024
    print(f"成功构建中科院开源镜像分区数据库！入库记录: {count} 条，文件大小: {db_size:.2f} MB")


if __name__ == "__main__":
    build()
