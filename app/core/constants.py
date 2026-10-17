# -*- coding: utf-8 -*-
"""
app.core.constants
==================
选刊核心业务常量、级别权重映射及索引别名字典。
"""

LEVEL_ORDER = {
    "A1": 1,
    "A2": 2,
    "A3": 3,
    "A4": 4,
    "B": 5,
}

LEVEL_LABEL = {
    "A1": "A类1级",
    "A2": "A类2级",
    "A3": "A类3级",
    "A4": "A类4级",
    "B": "B类（校内限定期刊）",
}

# 广中医校本单位期刊（目录备注4：每人每次申报限用1篇有效业绩）
OWN_JOURNALS = {
    "新中医",
    "广州中医药大学学报",
    "中医肿瘤学杂志",
}

# 知识库索引字段 → 规则键映射（用于“收录索引 → 广中医级别”）
KB_INDEX_TO_RULE = [
    ("scie_zone", "scie_zone{zone}"),
    ("ssci_zone", "ssci_zone{zone}"),
    ("cscd_core", "cscd_core"),
    ("cscd_ext", "cscd_ext"),
    ("cssci_core", "cssci_core"),
    ("cssci_ext", "cssci_ext"),
    ("pkucore", "pkucore"),
    ("chss_core", "chss_core"),
    ("ahci", "ahci"),
    ("ei", "ei"),
    ("cpci_s", "cpci_s"),
    ("cpci_ssh", "cpci_ssh"),
    ("isr", "isr"),
    ("xhwd", "xhwd"),
    ("rdfy", "rdfy"),
]

# 索引规则查询的别名（供直接输入“北大核心”“SCIE 1区”等使用）
# 注意：ssci_zone 必须排在 scie_zone 之前（“社会科学引文索引”含“科学引文索引”子串）
RULE_QUERY_ALIASES = {
    "ssci_zone": ["ssci", "社会科学引文索引"],
    "scie_zone": ["scie", "科学引文索引"],
    "pkucore": ["北大核心", "中文核心", "中文核心期刊要目总览", "要目总览"],
    "chss_core": ["人文社科核心", "中国人文社会科学核心期刊要览"],
    "cscd_core": ["cscd核心", "中国科学引文数据库核心"],
    "cscd_ext": ["cscd扩展", "中国科学引文数据库扩展"],
    "cssci_core": ["cssci核心", "中文社会科学引文索引核心"],
    "cssci_ext": ["cssci扩展", "中文社会科学引文索引扩展"],
    "ahci": ["ahci", "艺术与人文"],
    "ei": ["ei", "工程索引"],
    "cpci_s": ["cpci", "istp", "科学技术会议录"],
    "cpci_ssh": ["isshp", "社会科学及人文科学会议录"],
    "isr": ["isr", "科学评论索引"],
    "xhwd": ["新华文摘"],
    "rdfy": ["人大复印"],
    "qiushi": ["求是"],
    "rdyb": ["人民日报理论"],
    "gmrb": ["光明日报理论"],
    "jfjb": ["解放军报"],
    "jjrb": ["经济日报理论"],
    "nfyb": ["南方日报理论"],
}

# 期刊追踪表（12 列表头定义：A ~ L 列）
TRACK_HEADERS = [
    "期刊名称",              # A: 官方全称（唯一主键）
    "ISSN / CN",            # B: 刊号（如 ISSN 1673-1727 | CN 11-5334/R）
    "收录索引",              # C: CSCD/北大核心/SCIE等
    "广中医认定级别",        # D: A类1级~4级 / B类 / 不符合
    "影响因子(JIF)",         # E: 影响因子数值及口径说明
    "中科院分区",            # F: 中科院大类及小类学科分区
    "主编信息",              # G: 主编姓名及机构
    "收稿方向",              # H: 办刊宗旨、重点栏目与篇幅要求
    "审稿周期",              # I: 官方承诺时限与作者经验
    "出版方式与版面费",      # J: OA/订阅、出版周期、APC收费标准
    "投稿方式",              # K: 官方采编网址与防伪避坑提示
    "核验日期与来源",        # L: 核验日期 + 来源链接数
]
