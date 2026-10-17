# 文津·选刊助手 (Wenjin-Lens) 数据构建脚本说明（scripts/）

本目录包含用于离线构建、同步与清洗学术目录数据库的 ETL 工具脚本。所有产物均已编译打包至 `data/` 目录，日常运行系统**无需**重复执行这些脚本；仅在需要更新底层索引大库时按需使用。

---

## 脚本清单与功能索引

| 脚本文件 | 产物目标路径 | 数据源与功能说明 | 运行依赖 |
| :--- | :--- | :--- | :--- |
| `build_catalog.py` | `data/catalog/journal_catalog.json`<br>`data/catalog/journal_catalog.csv` | 解析学校官方《广州中医药大学重要期刊目录（试行）》DOCX 文档，提取 136 本 B 类期刊及定级规则 | `python-docx` |
| `build_cas_jcr.py` | `data/catalog/cas_jcr.db` | 从开源学术镜像拉取 JCR 2025 与中科院分区表，构建包含 21,000+ 期刊的 SQLite 离线数据库 | 标准库 (`sqlite3`, `urllib`) |
| `build_chinese_core.py` | `data/catalog/chinese_core_journals.json` | 提取全国中文核心期刊与 CSCD 核心版精选库（中医药学与生物医学） | 标准库 |
| `build_full_chinese_core.py` | `data/catalog/chinese_core_journals.json` | 全量构建全国中文核心期刊与 CSCD 离线大库（含多别名映射与综合学科） | 标准库 |
| `build_medline.py` | `data/catalog/medline_journals.json` | 从美国国家医学图书馆 (NLM) 官方公开 FTP 服务器拉取并解析 MEDLINE 官方期刊库 | 标准库 (`urllib`) |

---

## 使用指南

### 1. 重新解析广中医 308 号文件
```bash
python scripts/build_catalog.py data/raw/广中医重要期刊目录.docx data/catalog
```

### 2. 更新中科院 1~4 区 SQLite 离线数据库
```bash
python scripts/build_cas_jcr.py
```

### 3. 重建全国中文核心库与别名映射
```bash
python scripts/build_full_chinese_core.py
```

### 4. 同步 MEDLINE 官方核心库
```bash
python scripts/build_medline.py
```
