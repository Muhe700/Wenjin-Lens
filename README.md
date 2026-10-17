# 选刊助手（xuankan / Wenjin-Lens）

面向学术研究者与高校教师的智能选刊与期刊等级核验工具。输入期刊名称、ISSN / CN 刊号或收录索引关键词，即可一键检索并输出 **9 项核心选刊维度**：

1. **收录索引**：SCIE / SSCI / CSCD / CSSCI / 北大核心 / EI 等权威数据库收录状态
2. **广中医认定级别**：对照《广州中医药大学重要期刊目录（试行）》（广中医校办〔2020〕308号），判定 A类1级~4级、B类（校内限定）及规则升级依据
3. **期刊评分**：最新影响因子（JIF）、中科院分区（基础版/升级版，含大类与小类学科分区）
4. **主编信息**：现任主编、共同主编及编委会依托单位
5. **收稿方向**：办刊宗旨、重点收稿学科、主要常设栏目及篇幅/字数要求
6. **审稿周期**：官方承诺处理时限、同行评议时长与近期作者实际投稿经验
7. **出版方式**：OA（开放获取）/ 订阅模式（非OA）、出版频次与出版周期（半月刊/月刊/双月刊等）
8. **版面费（APC）**：文章处理费标准（币种/金额）、减免政策或无版面费声明
9. **投稿方式与防伪提示**：官方在线投稿系统链接、采编部联系邮箱与山寨/钓鱼网站防伪避坑提示

---

## 运行机制与运行边界说明

选刊助手设计为**“本地离线速查 + Google AI Studio 联网核验”**双模架构，使用者需注意以下运行边界：

* **本地离线模式（Local CLI / EXE）**：
  核心程序仅依赖 Python 标准库即可执行（若安装 `openpyxl` 则可生成带筛选功能的 Excel 追踪表）。离线直接运行 `.py` 或打包后的 `.exe` 时，**仅读取本地已固化的目录文件与已缓存的 `journal_kb.json` 数据**；若查询未核验的新刊，程序会安全输出“待核验”，绝不编造虚假数据。
* **联网核验与刷新模式（AI Studio Grounding）**：
  当查询未曾核验的新刊、或指定 `--refresh` 强制刷新时，程序借助 Google AI Studio 的 Gemini 模型配合 `Grounding with Google Search` 自动联网检索核验最新数据，并回写至本地 `journal_kb.json` 与追踪表。

---

## 版本迭代历程与演进里程碑 (Version Iteration Milestones)

文津·选刊助手（Wenjin-Lens）经历了 **4 次重大架构演进与版本迭代**，从最初的轻量终端脚本逐步成长为企业级、模块化、高内聚的学术决策工作台：

| 版本 | 阶段定位 | 核心技术升级与突破 | 标志性能力 |
|:---:|---|---|---|
| **v1.0** | **单机基准·终端工具** | • 广中医校办〔2020〕308号文官方文件形式化解析<br>• 目录列名与索引升级判定双模仲裁引擎<br>• 纯 Python 标准库零依赖快速交付 | • 终端美观输出 9 项选刊核心指标<br>• 自动幂等维护 12 列标准 Excel 决策追踪表（首行冻结/自动筛选）<br>• 支持刊名、ISSN、CN刊号与索引规则精确及模糊匹配 |
| **v1.5 / v2.0** | **双模驱动·开放生态与 AI** | • 免注册免 Key 深度集成 OpenAlex 与 DOAJ 开放学术 API<br>• 接入 Google AI Studio (Gemini) 进行办刊语义提炼<br>• 建立中科院文献情报中心《国际期刊预警名单》离线排查库<br>• 建立全国中文核心期刊与 CSCD 核心库离线数据库（中医药期刊高被引全量覆盖） | • 杜绝大模型数值幻觉：APC、主页、审稿周期由权威事实源直出<br>• 毫秒级阻断论文工厂、引用操纵与学术治理风险<br>• 支持“本地离线秒查 + 联网深度核验”双模平滑流转 |
| **v2.1** | **工作台化·现代学术 Web 单页** | • 引入 FastAPI 异步微内核驱动本地 Web 服务<br>• 践行 `DESIGN.md` 与 `academic-ui-craft` 学术级 UI 规范<br>• 集成 Element Plus、Chart.js 环形分布图与 Canvas Confetti 微动效 | • 现代化单页学术工作台（选刊检索/多维筛选/台账管理/官方目录全览）<br>• 宣纸温润白与深墨雅夜明暗模式无闪切换<br>• 3 刊横向多维对比矩阵与一键规范化决策简报复制 |
| **v2.2 (当前)** | **工程重塑·全模块化与接口解耦** | • **前端 UI 独立分离**：彻底拆分模板、设计系统与功能逻辑<br>• **标准接口数据传输**：前端封装 `WenjinAPI` 服务层，后端定义 Pydantic DTO 强契约<br>• **领域服务下沉**：抽取 `JournalService` 统一领域门面<br>• **模块化子路由**：FastAPI 解耦为检索、台账、目录独立路由器 | • 前端架构解耦为 `tokens` + `layout` + `components` + `modules` + `services`<br>• 杜绝散落直接 fetch，UI 仅通过接口进行数据传输<br>• CLI 命令行与 Web 端全量共享标准服务门面，消除重复判定逻辑 |

---

## 工程目录结构（分层设计与 Web 演进架构）

```text
Wenjin-Lens/
├── app/                  # 核心业务逻辑与 Web 服务层（模块化解耦架构）
│   ├── config.py         # 全局配置管理、路径自动解析与代理穿透
│   ├── core/             # 业务规则与底层定义
│   │   ├── constants.py  # 级别字典、规则映射、校本单位期刊清单
│   │   └── rules.py      # 规则判定引擎（单刊多索引合并、从高认定仲裁）
│   ├── models/           # 模块间数据传输契约与接口 DTO 模型
│   │   └── schemas.py    # Pydantic 规范化契约（Search, Track, Catalog, Stats DTO）
│   ├── services/         # 领域业务服务（模块化高内聚设计）
│   │   ├── journal_service.py # 核心领域门面（统一级联检索与AI查证编排）
│   │   ├── catalog_service.py # 官方目录、中文核心库与 CAS JCR 分区库检索
│   │   ├── kb_service.py      # 知识库读写与更新
│   │   ├── risk_service.py    # 中科院国际预警期刊排查
│   │   ├── academic_api.py    # OpenAlex / DOAJ 权威学术数据抓取
│   │   ├── track_service.py   # 选刊追踪台账与带样式 Excel 导出
│   │   ├── ai_verifier.py     # Google Gemini API 联网深度核验服务
│   │   └── display_service.py # 终端 9 项选刊核心维度渲染
│   └── web/              # Web 开放 API 与模块化前端
│       ├── api.py        # FastAPI 主装配器与中间件挂载（含 favicon 路由）
│       ├── routers/      # 模块化独立 API 路由
│       │   ├── search_router.py  # /api/search, /api/refresh
│       │   ├── track_router.py   # /api/track, /api/filter, /api/track/export
│       │   └── catalog_router.py # /api/catalog, /api/stats, /api/health
│       └── static/       # 前端 UI 设计系统（纯净独立分离、零打包免编译）
│           ├── index.html        # 纯净解耦的 HTML 模板与语义视图结构
│           ├── css/              # 学术设计系统（Academic UI Craft）
│           │   ├── tokens.css    # 设计系统变量（宣纸底色、墨青、珊瑚陶土）
│           │   ├── layout.css    # 1140px 学术黄金阅读宽度与响应式网格
│           │   ├── components.css# 9维卡片、A1~B徽章、横向对比矩阵
│           │   └── academic-theme.css # 主题总控聚合入口
│           └── js/               # 前端接口与业务模块
│               ├── services/
│               │   └── api.js    # WenjinAPI: 统一后端 RESTful 接口数据传输层
│               ├── modules/
│               │   ├── theme.js      # 明暗雅墨主题管理
│               │   ├── formatters.js # 学术排版与简报格式化工具
│               │   ├── chart.js      # 目录分布甜甜圈图表封装
│               │   └── comparison.js # 多维横向对比矩阵状态管理
│               └── app.js        # Vue 3 核心应用调度器与视图装配
├── config/               # 配置文件目录
│   ├── config.example.json # 配置模板
│   └── config.json       # 本地私有配置（受 .gitignore 严密保护）
├── data/                 # 数据分层存储目录
│   ├── raw/              # 原始文件（广中医重要期刊目录.docx）
│   ├── catalog/          # 静态基准目录（journal_catalog.json, cas_jcr.db, chinese_core）
│   ├── kb/               # 动态知识库（journal_kb.json）
│   ├── risk/             # 中科院国际预警期刊数据库（cas_warning_journals.json）
│   └── track/            # 选刊追踪台账（journal_track.csv / .xlsx）
├── deploy/               # 生产部署与守护进程模板
│   ├── nginx.conf        # Nginx 反向代理、Gzip 与 SSL 优化配置
│   └── wenjin-lens.service # Linux Systemd 守护进程单元
├── scripts/              # 离线维护与构建脚本（详见 scripts/README.md）
│   ├── build_cas_jcr.py  # 中科院 1~4 区 SQLite 离线数据库构建
│   ├── build_catalog.py  # 从 docx 重建 catalog 的自动化脚本
│   ├── build_chinese_core.py # 中文核心期刊索引构建脚本
│   ├── build_full_chinese_core.py # 全量中文核心与别名大库构建
│   └── build_medline.py  # MEDLINE 核心医学库构建脚本
├── tests/                # 自动化回归测试套件 (Pytest)
│   ├── conftest.py       # 全局测试配置与路径导入
│   ├── test_api.py       # FastAPI RESTful 接口集成测试
│   ├── test_catalog.py   # 目录与中文核心库检索测试
│   ├── test_risk.py      # 中科院国际预警名单比对测试
│   ├── test_rules.py     # 从高认定与规则仲裁引擎测试
│   └── test_track.py     # 决策台账与多维筛选测试
├── Dockerfile            # 生产级多阶段容器化镜像构建规范
├── docker-compose.yml    # 一键容器编排与卷挂载配置
├── .dockerignore         # Docker 镜像构建忽略规约
├── .env.example          # 生产环境变量模板
├── .gitignore            # 严谨的敏感信息与隐私防护规则
├── pytest.ini            # Pytest 测试套件运行配置
├── start_web.bat         # Windows 一键启动脚本
├── start_web.sh          # Linux / macOS 一键启动脚本
├── web_app.py            # Web 服务启动入口（支持 HOST, PORT, WORKERS）
├── xuankan.py            # CLI 命令行入口（面向 JournalService 领域门面）
├── requirements.txt      # 核心生产运行依赖清单
├── requirements-dev.txt  # 开发与自动化测试依赖清单
├── LICENSE               # MIT 开源许可证
├── DESIGN.md             # 学术视觉系统设计规范
├── DEVELOPMENT.md        # 核心技术开发规范与架构说明
├── DEPLOYMENT.md         # 生产环境部署与运维手册
└── README.md             # 用户手册与全量维度说明
```

---

## 期刊追踪表（12 列表头定义）

程序每次查询或核验期刊后，均会自动以“期刊名称”为主键执行 upsert（存在则更新、不存在则追加）同步至 `journal_track.csv` 和 `journal_track.xlsx`。Excel 追踪表默认开启首行冻结及 `A1:L 末行` 自动筛选，各列（A~L 列）定义如下：

| 列号 | 表头名称 | 字段说明 | 典型取值 / 示例 |
|:---:|---|---|---|
| **A** | **期刊名称** | 期刊官方中文名或英文全称（唯一主键） | 中华中医药杂志、Scientific Reports |
| **B** | **ISSN / CN** | 国际标准连续出版物号与国内统一刊号 | ISSN 1673-1727 \| CN 11-5334/R |
| **C** | **收录索引** | 权威索引数据库收录情况（分号隔开） | CSCD核心版；北大核心；SCIE 3区 |
| **D** | **广中医认定级别** | 校办〔2020〕308号文件对应级别与升级判定 | A类1级、A类2级、A类3级、A类4级、B类 |
| **E** | **影响因子(JIF)** | 最新发布的 JCR 影响因子或国内权威口径 | 4.9（JIF 2024）、2.588（维普） |
| **F** | **中科院分区** | 最新中科院期刊分区表大类与小类分区 | 中科院1区（中医学）、中科院3区（综合） |
| **G** | **主编信息** | 现任主编姓名及工作单位/编委会机构 | 谷晓红（中华中医药学会编委会） |
| **H** | **收稿方向** | 办刊宗旨、学科范畴、特色栏目及字数规约 | 中医药理论、临床与基础研究、论著限4000字 |
| **I** | **审稿周期** | 官方公布审稿时限与同行实际经验反馈 | 初审约1个月，全流程约4-5个月 |
| **J** | **出版方式与版面费** | OA/非OA、出版频次及 APC 收费标准 | 非OA（免版面费） / OA（APC: $2390） |
| **K** | **投稿方式** | 官方采编系统网址、投稿邮箱与防伪鉴别提示 | 官方采编系统网址（警惕高仿山寨网站） |
| **L** | **核验日期与来源** | 最新一次联网查证日期与证据来源链接数 | 2026-10-15（7 个来源） |

---

## 用法指南（Usage）

### 1. 基础查询（本地离线模式）

```bash
# 查询期刊（输出 9 项选刊核心信息，并自动记录/更新到追踪表）
python3 xuankan.py "中华中医药杂志"

# 按 ISSN 查询
python3 xuankan.py "1673-1727"

# 按 CN 刊号查询（适用于仅有 CN 号的国内期刊与党报理论版）
python3 xuankan.py "11-5334/R"

# 查询索引规则对应的广中医级别
python3 xuankan.py "北大核心"
python3 xuankan.py "SCIE 1区"
python3 xuankan.py "CSCD 核心"
python3 xuankan.py "EI"

# 关键词模糊搜索期刊
python3 xuankan.py --search "中医"

# 查看期刊追踪表（历史查询记录）
python3 xuankan.py --track

# 列出目录内全部期刊
python3 xuankan.py --list

# JSON 输出（供程序或前端调用）
python3 xuankan.py "中华中医药杂志" --json

# 由目录重建/初始化知识库骨架
python3 xuankan.py --init-kb
```

### 2. Google AI Studio 联网实时核验（v2.0 双模驱动）

配置 Gemini API Key 后，可直接对未核验期刊进行自动查证，或强制刷新已有数据并回写知识库：

```bash
# 配置 API Key
# Linux / macOS
export GEMINI_API_KEY="your_api_key_here"

# Windows PowerShell
$env:GEMINI_API_KEY="your_api_key_here"

# Windows CMD
set GEMINI_API_KEY=your_api_key_here

# 强制联网刷新最新指标（拉取最新 IF、中科院分区、APC、投稿链接并回写）
python3 xuankan.py "中华中医药杂志" --refresh

# 查询目录外新期刊（自动调用 Google Search Grounding 查证并入库）
python3 xuankan.py "Innovations in Acupuncture and Medicine" --refresh
```

### 3. 逆向智能选刊（v3.0 条件筛选）

支持从已沉淀的 `data/track/journal_track.xlsx` 与知识库中，按照多维复合条件筛选最佳投稿期刊：

```bash
# 筛选 A类2级、非OA（免版面费）、审稿周期在 3 个月内的期刊
python xuankan.py --filter "level=A类2级,oa=否,cycle<3个月"

# 筛选中科院 1 区或 2 区且收稿方向含“针灸”的期刊
python xuankan.py --filter "zone<=2,scope=针灸"
```

### 4. Web 网页端一键启动（Web 浏览器交互）

无需任何复杂的环境配置，直接在项目根目录下执行：

```bash
# 启动本地 Web 服务（默认监听 127.0.0.1:8000）
python web_app.py

# 启动后在浏览器打开：
# 网页界面: http://127.0.0.1:8000
# 交互式 API 文档 (Swagger): http://127.0.0.1:8000/docs
```

网页端集成：
* **智能选刊检索**：可视化 9 项核心指标卡片、中英文期刊名/ISSN/CN 快速检索
* **多维条件选刊**：按级别、OA/非OA、审稿周期即时筛选
* **选刊台账与下载**：实时查看历史查询记录，支持一键下载 Excel 选刊表
* **官方目录全览**：134 种收录期刊及各级规则结构化浏览


---

## Google AI Studio 部署与配置

本助手可直接接入 Google AI Studio，利用 Gemini 2.5 / 1.5 配合 Google 搜索接地实现全自动期刊核验：

1. **挂载静态基准上下文（System Instruction）**：
   * 将 `journal_catalog.json` 作为 System Instruction 或 Context Cache 载入。
   * 注入广中医校办〔2020〕308号文认定规则，确保模型在级别裁定时零幻觉、严格对齐官方条款。
2. **启用实时搜索接地（Grounding with Google Search）**：
   * 在 AI Studio 界面开启 `Tools` -> `Google Search`。
   * 触发查证任务时，模型自动穿透查询 Web of Science、中科院文献情报中心、万方/知网、LetPub 及期刊官方主页，提取主编、审稿周期、APC 与官方投稿域名。
3. **启用结构化输出（Structured Outputs）**：
   * 将下文的 JSON Schema 设为 Response Schema，确保返回的数据可以直接无损反序列化并合并入 `journal_kb.json`。

---

## 知识库数据字典（JSON Schema 规范）

`journal_kb.json` 单条记录的标准数据结构定义如下，可直接用于 Google AI Studio 的 Structured Outputs 格式约束：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "JournalKBRecord",
  "description": "期刊知识库单条记录标准结构定义",
  "type": "object",
  "properties": {
    "basic": {
      "type": "object",
      "properties": {
        "name": { "type": "string", "description": "期刊全称" },
        "issn": { "type": "string", "description": "国际标准连续出版物号" },
        "cn": { "type": "string", "description": "国内统一连续出版物号" },
        "publisher": { "type": "string", "description": "主办单位或出版机构" }
      },
      "required": ["name"]
    },
    "indexes": {
      "type": "object",
      "properties": {
        "indexes_verified": { "type": "boolean", "description": "是否已核验证实" },
        "scie_zone": { "type": ["integer", "null"], "description": "中科院SCIE分区(1-4)" },
        "ssci_zone": { "type": ["integer", "null"], "description": "中科院SSCI分区(1-4)" },
        "cscd_core": { "type": "boolean", "description": "CSCD核心版收录" },
        "cscd_ext": { "type": "boolean", "description": "CSCD扩展版收录" },
        "cssci_core": { "type": "boolean", "description": "CSSCI核心版收录" },
        "cssci_ext": { "type": "boolean", "description": "CSSCI扩展版收录" },
        "pkucore": { "type": "boolean", "description": "北大核心收录" },
        "chss_core": { "type": "boolean", "description": "中国人文社科核心要览收录" },
        "ahci": { "type": "boolean", "description": "A&HCI收录" },
        "ei": { "type": "boolean", "description": "EI Compendex核心版期刊收录" },
        "cpci_s": { "type": "boolean", "description": "CPCI-S收录" },
        "cpci_ssh": { "type": "boolean", "description": "CPCI-SSH收录" },
        "isr": { "type": "boolean", "description": "ISR收录" },
        "xhwd": { "type": "boolean", "description": "新华文摘全文转载" },
        "rdfy": { "type": "boolean", "description": "人大复印全文转载" },
        "extra": { "type": "array", "items": { "type": "string" }, "description": "其他数据库收录(如PubMed/Scopus/CA)" }
      },
      "required": ["indexes_verified"]
    },
    "impact_factor": {
      "type": "object",
      "properties": {
        "jcr_year": { "type": "integer", "description": "影响因子年份" },
        "jcr_if": { "type": "string", "description": "最新影响因子数值及说明" },
        "cas_zone": { "type": "string", "description": "中科院分区详细信息(含大类与小类学科)" },
        "note": { "type": "string", "description": "多统计口径说明(如维普/知网/科睿唯安)" }
      }
    },
    "editor_in_chief": {
      "type": "object",
      "properties": {
        "name": { "type": "string", "description": "主编姓名" },
        "affiliation": { "type": "string", "description": "主编单位或依托机构" },
        "note": { "type": "string", "description": "名誉主编或编委会补充说明" }
      }
    },
    "scope": { "type": "string", "description": "收稿学科范围、办刊方向、重点栏目与篇幅字数要求" },
    "review_cycle": { "type": "string", "description": "官方承诺审稿时限与同行实际审稿录用周期经验" },
    "publication_mode": { "type": "string", "description": "出版方式(OA开放获取/传统订阅非OA)、出版周期(半月刊/月刊/双月刊)" },
    "apc_fee": { "type": "string", "description": "版面费说明(如免版面费，或具体APC币种金额与减免政策)" },
    "submission_url": { "type": "string", "description": "官方在线投稿平台链接或官方投稿信箱，含防钓鱼山寨辨识提示" },
    "sources": { "type": "array", "items": { "type": "string" }, "description": "联网核验采纳的官方或权威数据源URL列表" },
    "indexes_note": { "type": "string", "description": "索引综合核验证据与历史变更说明" },
    "updated": { "type": "string", "description": "最新核验日期(YYYY-MM-DD)" }
  },
  "required": ["indexes", "impact_factor", "scope", "review_cycle", "publication_mode", "apc_fee", "submission_url", "updated"]
}
```

### 单条记录示例

```json
{
  "basic": {
    "name": "中华中医药杂志",
    "issn": "1673-1727",
    "cn": "11-5334/R",
    "publisher": "中华中医药学会"
  },
  "indexes": {
    "indexes_verified": true,
    "scie_zone": null,
    "ssci_zone": null,
    "cscd_core": true,
    "cscd_ext": false,
    "cssci_core": false,
    "cssci_ext": false,
    "pkucore": true,
    "chss_core": false,
    "ahci": false,
    "ei": false,
    "cpci_s": false,
    "cpci_ssh": false,
    "isr": false,
    "xhwd": false,
    "rdfy": false,
    "extra": ["中国科技核心(CSTPCD)", "卓越期刊/T1级期刊", "CA", "WPRIM"]
  },
  "impact_factor": {
    "jcr_year": 2024,
    "jcr_if": "2.588（维普2024年影响因子口径）",
    "cas_zone": "中科院分区1区（中医学领域，以论文发表当年官方版本为准）",
    "note": "非SCIE收录，无JCR IF；维普2024 IF 2.588；知网综合IF约1.9"
  },
  "editor_in_chief": {
    "name": "谷晓红",
    "affiliation": "中华中医药学会《中华中医药杂志》编委会",
    "note": "名誉主编：王琦"
  },
  "scope": "中医药理论、临床与基础研究、中药药理、针灸推拿等。论著限4000字，综述限5000字。",
  "review_cycle": "官方双盲同行评审。作者经验参考：初审约1个月，录用周期4-5个月，排期约12个月。",
  "publication_mode": "非OA（传统订阅制）；月刊",
  "apc_fee": "收取常规版面费（根据排版页数核算，不收高额APC）",
  "submission_url": "http://www.zhzyyzz.com（请认准官方域名，防范山寨投稿中介）",
  "sources": [
    "http://www.zhzyyzz.com/CN/news/news117.shtml",
    "https://sns.wanfangdata.com.cn/perio/zgyyxb/"
  ],
  "indexes_note": "北大核心(2023版)、CSCD核心库(2025-2026)、中国科技核心；曾用名《中国医药学报》",
  "updated": "2026-10-15"
}
```

---

## 广中医认定规则（依据广中医校办〔2020〕308号官方原文校准）

严格对照《广州中医药大学重要期刊目录（试行）》（广中医校办〔2020〕308号）官方文件原文细则校准：

- **A类1级**：
  * 《科学通报》（中英文版）、《中国社会科学》（中英文版）
  * 《求是》（**1500字左右**理论文章）
  * SCIE 中科院 1 区、SSCI 1 区
- **A类2级**：
  * CSCD 核心版、CSSCI 核心版、A&HCI
  * SCIE 2 区、SSCI 2 区
  * 《新华文摘》全文转载
- **A类3级**：
  * 《中文核心期刊要目总览》（北大核心）、《中国人文社会科学核心期刊要览》、CSSCI 扩展版
  * SCIE 3 区、SSCI 3 区
  * 《人民日报》/《光明日报》理论版全文转载
  * 《解放军报》（**1500字以上**理论文章）
- **A类4级**：
  * CSCD 扩展版、SCIE 4 区、SSCI 4 区
  * **EI Compendex（工程索引核心版）期刊**（注：仅认定核心版期刊，不认定 EI 会议论文）
  * CPCI-SSH、CPCI-S、ISR
  * 《经济日报》（**1500字以上**理论文章）
  * 人大复印报刊资料全文转载（3000字以上，**不含“文摘”系列、“报刊资料索引”系列及中心原发刊**）
  * 《南方日报》理论版
- **B类（校内限定期刊）**：
  * 《广州中医药大学重要期刊目录（试行）》列名的 134 种中医药及相关领域期刊

### 关键认定备注（官方原则）

1. **就高认定原则（备注1）**：目录所列刊物如进入更高级别，则按高级别期刊认定（例如：目录内的 B 类期刊若被 CSCD 核心版收录，升级认定为 **A类2级**）。
2. **发表当年有效与兜底原则（备注2/3）**：SCIE/SSCI 分区按中科院分区（大类小类均予认定），以论文正式发表当年版本为准；SSCI 在 2020-12-31 前按科睿唯安执行。**若因特殊原因未提供分区，以可查年限中最近年份分区为准**。
3. **本单位期刊限额（备注4）**：本单位期刊《新中医》、《广州中医药大学学报》、《中医肿瘤学杂志》每人每次职称申报**仅可用 1 篇**作为有效业绩。
4. **用途限定（备注5）**：本目录规则仅用于广州中医药大学专业技术资格（职称）评审。

---

## 快速启动与分享部署

### 方式一：Web 网页端一键启动（推荐）
- **Windows 用户**：直接双击根目录下的 `start_web.bat`，系统将自动检查依赖并开启 Web 服务。
- **Linux / macOS 用户**：运行 `./start_web.sh`。
- **命令行启动**：
  ```bash
  pip install -r requirements.txt
  python web_app.py --host 127.0.0.1 --port 8000
  ```
  启动后访问：
  * 本地交互界面：`http://127.0.0.1:8000`
  * 交互式 OpenAPI 文档：`http://127.0.0.1:8000/docs`

### 方式二：Docker 容器化部署
一键编排并挂载持久化台账数据：
```bash
docker compose up -d --build
```

### 方式三：终端 CLI 命令行直接使用
在终端执行快速查询（零 Web 依赖）：
```bash
python xuankan.py "中华中医药杂志"
```

### 方式四：自动化测试与回归核验
系统提供覆盖规则判定、目录服务、风险预警与 RESTful API 的完整测试套件：
```bash
pytest tests -v
```

---

## 生产部署与运维指南

有关在 Ubuntu/CentOS 服务器配置 Systemd 守护进程、Nginx 反向代理、SSL 证书以及持久化容灾备份，请参阅专门的生产运维手册：
👉 **[DEPLOYMENT.md](DEPLOYMENT.md)**

---

## 开发者与维护指南

有关系统架构演进模型、统一领域门面、Google AI Studio 提示词工程及代码迭代规范，请参阅专门的开发指南：
👉 **[DEVELOPMENT.md](DEVELOPMENT.md)**
👉 **[DESIGN.md](DESIGN.md)** (学术视觉设计系统规范)
👉 **[scripts/README.md](scripts/README.md)** (数据流水线 ETL 脚本说明)


