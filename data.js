/* Auto-generated from data.json — do not edit by hand. */
window.TRENDING_DATA = {
  "schema": 1,
  "meta": {
    "date": "2026-07-17",
    "generated_at": "2026-07-17 14:05 (CST)",
    "source": "github.com/trending",
    "criteria": "Repositories · Today · All languages · logged out",
    "kicker_zh": "每日自动更新 · 2026-07-17 · 每日榜 · 全语言 · 17 个仓库",
    "kicker_en": "Auto-updated · 2026-07-17 · Daily · All languages · 17 repos",
    "headline_zh": "Agent Skills 技能包集体屠榜",
    "headline_en": "Agent Skills packs storm the chart",
    "sub_zh": "17 个上榜仓库中 7 个属于 Agent 工具链，其中 5 个是「给 AI 装技能」的 Skills 包 —— 从反 AI 味设计（hallmark）到知识图谱上下文（graphify）。老牌神仓 build-your-own-x（526k stars）与 OSSU 自学路线依然稳居榜上。点击任意卡片查看深度解析。",
    "sub_en": "7 of the 17 trending repos are agent tooling — and 5 of those are \"give your AI a skill\" packs, from anti-slop design (hallmark) to knowledge-graph context (graphify). Evergreen giants build-your-own-x (526k stars) and OSSU hold their ground. Click any card for a deep dive.",
    "footer_zh": "Trending Scope · 数据更新于 2026-07-17 14:05 (CST)，由自动化管线直连 github.com 抓取",
    "footer_en": "Trending Scope · Data updated 2026-07-17 14:05 (CST) by the automated pipeline, fetched directly from github.com"
  },
  "cats": {
    "agent": {
      "zh": "Agent 工具链",
      "en": "Agent Tooling",
      "color": "#cf4a1f"
    },
    "ai": {
      "zh": "AI 应用与模型",
      "en": "AI Apps & Models",
      "color": "#0e6f63"
    },
    "infra": {
      "zh": "平台·数据·应用",
      "en": "Platforms, Data & Apps",
      "color": "#b07a1e"
    },
    "other": {
      "zh": "学习 & 游戏",
      "en": "Learning & Gaming",
      "color": "#5a7a3a"
    }
  },
  "repos": [
    {
      "slug": "ossie",
      "full": "apache/ossie",
      "rank": 1,
      "cat": "infra",
      "lang": "Python",
      "stars": 1.0,
      "today": "+60",
      "today_n": 60,
      "auto": false,
      "zh": {
        "tag": "Apache 孵化的语义交换标准，让 BI/AI 工具说同一种指标语言",
        "what": "行业级开放规范（原名 Open Semantic Interchange / OSI，现为 Apache 孵化项目），目标是标准化语义元数据在数据分析、AI 与 BI 平台之间的交换：用一套 JSON/YAML 规范统一定义 KPI、指标和业务逻辑，解决「同一个指标在不同工具里定义不一致」的老大难，让 AI agent 基于一致的业务语义输出可靠结果。",
        "content": "以规范文档为主：core-spec/（spec.md、spec.yaml、osi-schema.json）、converters/（与 dbt、GoodData、Polaris、Salesforce 等格式互转的参考实现）、examples/（含完整 TPC-DS 示例模型）、validation/（schema 校验工具）。",
        "stack": "主语言 Python，规范本体是 JSON Schema + YAML，Apache-2.0，走 Apache 基金会孵化流程。",
        "hot": "「AI agent 要消费企业数据语义」带火了语义层标准化；项目刚转入 Apache 孵化、今天仍在高频提交，处于规范成型的关键曝光期。",
        "uses": [
          "数据团队 —— 统一各 BI 工具里的指标定义，告别「同指标不同口径」",
          "AI 应用开发者 —— 让 agent 基于一致的语义层查询企业数据，减少幻觉",
          "平台厂商 —— 用参考转换器接入 dbt / Salesforce 等生态"
        ]
      },
      "en": {
        "tag": "Apache-incubated semantic interchange spec — one metric language for BI & AI",
        "what": "An industry-wide open specification (formerly Open Semantic Interchange / OSI, now an Apache incubator project) standardizing how semantic metadata is exchanged across analytics, AI and BI platforms. One JSON/YAML spec defines KPIs, metrics and business logic consistently — ending the classic 'same metric, different definition in every tool' problem, so AI agents can reason over consistent business semantics.",
        "content": "Mostly spec documents: core-spec/ (spec.md, spec.yaml, osi-schema.json), converters/ (reference converters for dbt, GoodData, Polaris, Salesforce formats), examples/ (including a full TPC-DS sample model) and validation/ (schema tooling).",
        "stack": "Python as the main language; the spec itself is JSON Schema + YAML; Apache-2.0, going through the Apache incubation process.",
        "hot": "'AI agents consuming enterprise data semantics' made the semantic layer a hot topic; the project just moved into Apache incubation and is committing at high frequency — peak visibility during spec formation.",
        "uses": [
          "Data teams — unify metric definitions across BI tools, ending 'same metric, different numbers'",
          "AI app builders — let agents query enterprise data over a consistent semantic layer, cutting hallucinations",
          "Platform vendors — plug into the dbt / Salesforce ecosystems with the reference converters"
        ]
      }
    },
    {
      "slug": "hallmark",
      "full": "Nutlope/hallmark",
      "rank": 2,
      "cat": "agent",
      "lang": "CSS",
      "stars": 11.2,
      "today": "+3.4k",
      "today_n": 3372,
      "auto": false,
      "zh": {
        "tag": "专治「AI 味」网页的设计 skill，让 AI 生成的 UI 不像模板货",
        "what": "Together AI 出品的设计 skill 包：装进 Claude Code、Cursor 或 Codex 后，AI 生成网页 UI 时会从 20 套主题里选宏观结构，并跑 57 项「anti-slop」检查加自我批判，拒绝 LLM 默认那套千篇一律的渐变卡片风。提供生成、hallmark audit（给现有代码打分）、hallmark redesign（换结构重写）、hallmark study（从截图/URL 提取设计 DNA）四个动词。",
        "content": "核心是 skills/hallmark/ 下的 SKILL.md + references/ 规则文件；docs/ 有 recipes 和示例，site/ 是官网及大量自包含 HTML+CSS 示例页（语言占比因此显示为 CSS）。",
        "stack": "Markdown 规则 + 参考文档的 skill 包（符合 Agent Skills 规范），示例为纯 HTML/CSS，MIT，无运行时依赖，一行 npx skills add nutlope/hallmark 安装。",
        "hot": "今日 +3.2k，病毒式传播 ——「AI 生成的网站都长一个样」是当下普遍痛点，「反 AI slop」定位精准踩中情绪，还有在线 demo 可直接体验。",
        "uses": [
          "独立开发者 / 小团队 —— 没有设计师，也能让 AI 生成不撞脸的官网和落地页",
          "设计师 —— 用 hallmark study 从优秀网站提取设计 DNA 做参考",
          "前端工程师 —— 用 audit 给存量项目打分，找出「AI 味」重灾区"
        ]
      },
      "en": {
        "tag": "The anti-'AI-slop' design skill — AI-built UIs that don't look like templates",
        "what": "A design skill pack from Together AI: once installed in Claude Code, Cursor or Codex, your agent picks a macro-structure from 20 themes when generating web UIs, then runs 57 'anti-slop' checks plus self-critique — rejecting the default LLM look of identical gradient cards. Four verbs: generate, hallmark audit (score existing code), hallmark redesign (rewrite with a new structure), hallmark study (extract design DNA from a screenshot or URL).",
        "content": "The core is SKILL.md plus rule files under skills/hallmark/ and references/; docs/ holds recipes and examples; site/ contains the homepage and many self-contained HTML+CSS example pages (which is why the language stat reads CSS).",
        "stack": "A Markdown-rules skill pack (Agent Skills compliant) with pure HTML/CSS examples; MIT, zero runtime dependencies; install via npx skills add nutlope/hallmark.",
        "hot": "+3.2k stars today and going viral — 'AI-generated websites all look the same' is a universal pain point, the anti-slop positioning hits it precisely, and the live demo makes trying it frictionless.",
        "uses": [
          "Indie devs & small teams — generate distinctive sites and landing pages without a designer",
          "Designers — extract design DNA from great sites with hallmark study",
          "Frontend engineers — audit existing projects to find the worst 'AI-slop' offenders"
        ]
      }
    },
    {
      "slug": "opencut",
      "full": "OpenCut-app/OpenCut",
      "rank": 3,
      "cat": "infra",
      "lang": "TypeScript",
      "stars": 74.3,
      "today": "+3.5k",
      "today_n": 3537,
      "auto": false,
      "zh": {
        "tag": "开源版 CapCut（剪映），免费跨平台视频编辑器",
        "what": "免费开源视频编辑器，对标 CapCut，目标覆盖 Web、桌面和移动端。项目正在从零重写：Editor API、插件优先架构、Rust 核心（一套代码跑桌面/移动/浏览器）、供 AI agent 调用的 MCP server、无头批量渲染模式和编辑器内置脚本页。旧版代码已迁至 opencut-classic 继续维护。",
        "content": "monorepo：apps/web、apps/desktop、apps/api 三个应用，根目录 Cargo.toml（Rust 核心）；用 moonrepo + proto 管理工具链，moon run web:dev 即可起本地开发。",
        "stack": "TypeScript（Web 前端）+ Rust 核心，Bun 包管理，MIT；重写期间暂不接受外部代码贡献。",
        "hot": "今日 +3.3k，今日榜热度头部 ——「开源剪映平替」需求巨大（存量 73.8k stars），Rust 重写 +「让 AI 剪视频」的 MCP 叙事又推了一波。",
        "uses": [
          "自媒体创作者 —— 免费替代剪映专业版，无水印跨平台剪片",
          "开发者 / 自动化团队 —— 通过 MCP server 让 AI agent 批量剪视频",
          "企业 —— 基于 Editor API 和插件架构搭建内部视频流水线"
        ]
      },
      "en": {
        "tag": "The open-source CapCut alternative — free, cross-platform video editing",
        "what": "A free, open-source video editor rivaling CapCut, targeting web, desktop and mobile. The project is being rewritten from scratch: an Editor API, plugin-first architecture, a Rust core (one codebase for desktop/mobile/browser), an MCP server so AI agents can edit video, a headless mode for automated batch rendering, and built-in editor scripting. Legacy code lives on in opencut-classic.",
        "content": "A monorepo: apps/web, apps/desktop and apps/api, with a root Cargo.toml for the Rust core; toolchain managed by moonrepo + proto — `moon run web:dev` starts local dev.",
        "stack": "TypeScript (web frontend) + Rust core, Bun for packages, MIT; external code contributions are paused during the rewrite.",
        "hot": "+3.3k today, the hottest riser on the list — 'open-source CapCut' is a massive latent demand (73.8k stars banked), and the Rust rewrite plus 'let AI edit your video' MCP narrative pushed it further.",
        "uses": [
          "Content creators — a free, watermark-free CapCut Pro alternative across platforms",
          "Dev & automation teams — batch-edit video via AI agents over the MCP server",
          "Companies — build internal video pipelines on the Editor API and plugin architecture"
        ]
      }
    },
    {
      "slug": "posthog",
      "full": "PostHog/posthog",
      "rank": 4,
      "cat": "infra",
      "lang": "Python",
      "stars": 35.9,
      "today": "+77",
      "today_n": 77,
      "auto": false,
      "zh": {
        "tag": "开源一体化产品数据平台：分析、回放、实验、LLM 观测全包",
        "what": "知名开源产品数据平台：产品分析、Web 分析、session 回放、feature flag、A/B 实验、错误追踪、日志、问卷、数据仓库、CDP、LLM 可观测性全部集成在一个系统。最新定位「构建自驱动产品（self-driving products）」：把错误、rage click 等产品信号自动转成分析报告和 PR 供你 review 合并，可从 Slack、Web、桌面端或 MCP 操作，支持 Docker 自托管。",
        "content": "超大型 monorepo：posthog/（Django 后端）、frontend/、products/（各产品线）、rust/、services/、ee/（企业版，单独授权），大量 docker-compose 部署文件与全平台 SDK。",
        "stack": "Python/Django + TypeScript/React + Rust 服务，底层 ClickHouse；MIT（ee/ 目录除外）。",
        "hot": "35.8k 的成熟项目仍每日活跃提交；近期把整条产品线重定位为面向 AI agent 的「self-driving」叙事，稳稳吃到 AI 生态流量。",
        "uses": [
          "产品团队 —— 一个平台替代 GA + 回放 + 实验工具的组合订阅",
          "注重数据合规的公司 —— 自托管部署，用户数据不出机房",
          "AI 产品团队 —— 用 LLM 可观测性追踪自家 agent 的成本与质量"
        ]
      },
      "en": {
        "tag": "The open-source all-in-one product data platform",
        "what": "The well-known open-source product data platform: product analytics, web analytics, session replay, feature flags, A/B experiments, error tracking, logs, surveys, a data warehouse, CDP pipelines and LLM observability in one system. Its latest positioning is 'self-driving products': product signals like errors and rage clicks are automatically turned into analysis reports and PRs for you to review and merge — operable from Slack, web, desktop or MCP, and self-hostable via Docker.",
        "content": "A huge monorepo: posthog/ (Django backend), frontend/, products/ (each product line), rust/, services/, ee/ (enterprise code, separately licensed), lots of docker-compose files and SDKs for every platform.",
        "stack": "Python/Django + TypeScript/React + Rust services over ClickHouse; MIT (except ee/).",
        "hot": "A mature 35.8k-star project still committing daily; it recently repositioned its whole product line around an agent-facing 'self-driving' narrative and is riding the AI ecosystem wave.",
        "uses": [
          "Product teams — replace the GA + replay + experimentation stack with one platform",
          "Compliance-sensitive companies — self-host so user data never leaves your infra",
          "AI product teams — track your agents' cost and quality with LLM observability"
        ]
      }
    },
    {
      "slug": "openinterpreter",
      "full": "openinterpreter/openinterpreter",
      "rank": 5,
      "cat": "agent",
      "lang": "Rust",
      "stars": 66.1,
      "today": "+661",
      "today_n": 661,
      "auto": false,
      "zh": {
        "tag": "终端里的编程 agent，专为便宜小模型优化",
        "what": "跑在终端里的 AI 编程助手（OpenAI Codex 的 fork），核心思路「换 harness 不换模型」：内置 claude-code、kimi-cli、qwen-code、deepseek-tui 等多种 agent 运行框架，让低成本开源模型也打出好表现。自带 QA 技能，可驱动真实浏览器或原生 App 做界面测试，支持 macOS/Linux/Windows 原生沙箱执行。",
        "content": "完整 Rust 工程：终端 TUI、文档站（openinterpreter.com/docs）、安装脚本；配置与会话存本地 ~/.openinterpreter，支持 /model 切模型、/harness 切框架、MCP、hooks、AGENTS.md。",
        "stack": "Rust（2023 年创建的老牌项目，刚从 Python 重写），Apache-2.0；支持 ACP 协议接入编辑器，可接多家模型 provider。",
        "hot": "老树开新花：刚完成 Rust 重写并转型「低成本模型的 harness」，今天仍在提交，踩中「便宜模型 + 编程 agent」风口。",
        "uses": [
          "预算有限的开发者 —— 用 DeepSeek / Qwen 等便宜模型跑编程 agent，成本降一个量级",
          "多工具用户 —— 一套终端切换 claude-code、kimi-cli 等不同框架",
          "QA 团队 —— 让 agent 驱动真实浏览器做界面自动化测试"
        ]
      },
      "en": {
        "tag": "A coding agent in your terminal, tuned for low-cost models",
        "what": "An AI coding assistant in your terminal (a fork of OpenAI Codex) built on the idea of 'swap the harness, not the model': it bundles multiple agent runtimes — claude-code, kimi-cli, qwen-code, deepseek-tui — so cheap open models still perform well. It ships a QA skill that drives real browsers or native apps for UI testing, with native sandboxing on macOS/Linux/Windows.",
        "content": "A full Rust project: the terminal TUI, a docs site (openinterpreter.com/docs) and install scripts; config and sessions live in ~/.openinterpreter, with /model to switch models, /harness to switch runtimes, plus MCP, hooks and AGENTS.md support.",
        "stack": "Rust (a 2023 veteran, freshly rewritten from Python), Apache-2.0; supports ACP (Agent Client Protocol) for editors and multiple model providers.",
        "hot": "An old tree blooming again: the Rust rewrite and its new role as 'a harness for low-cost models' — still committing today — landed right on the 'cheap models + coding agents' wave.",
        "uses": [
          "Budget-conscious devs — run coding agents on cheap models like DeepSeek / Qwen, an order of magnitude cheaper",
          "Multi-tool users — swap between claude-code, kimi-cli and other harnesses in one terminal",
          "QA teams — let agents drive real browsers for UI automation testing"
        ]
      }
    },
    {
      "slug": "bonsai-demo",
      "full": "PrismML-Eng/Bonsai-demo",
      "rank": 6,
      "cat": "ai",
      "lang": "Shell",
      "stars": 1.6,
      "today": "+196",
      "today_n": 196,
      "auto": false,
      "zh": {
        "tag": "1-bit/三值超压缩大模型 Bonsai 的本地运行 demo",
        "what": "PrismML 的 Bonsai 系列语言模型官方演示仓库，主打极致量化：1-bit 版每权重约 1.125 bit，27B 模型能塞进现代 iPhone；三值（Ternary）版约 1.7 bit，是质量更高的默认选项。最新 27B 是视觉语言模型，支持看图、tool calling、MCP、256k+ 长上下文和推理努力度调节。",
        "content": "纯 Shell 脚本工程：setup.sh / setup.ps1 一键装依赖下模型，scripts/ 放运行和下载脚本，另有三份白皮书 PDF、AGENTS.md（写给 AI agent 看的配置指南）、VISION/TOOLS 等专题文档与社区 benchmark。",
        "stack": "Shell + llama.cpp 服务端，模型托管在 HuggingFace；支持 Mac Metal、CUDA/Vulkan/ROCm 和纯 CPU，Apache-2.0。",
        "hot": "昨天刚发布家族最大、首个视觉语言模型 Bonsai 27B ——「27B 模型跑在 iPhone 上」的噱头加上开箱即用脚本，传播力极强。",
        "uses": [
          "手机 / 边缘设备开发者 —— 在 iPhone 上离线跑 27B 视觉语言模型",
          "隐私敏感场景 —— 医疗、法律等数据不出本地的本地 AI 助手",
          "硬件玩家 —— 在树莓派等低功耗设备上体验大模型"
        ]
      },
      "en": {
        "tag": "Local-run demo of Bonsai, the 1-bit / ternary ultra-compressed LLMs",
        "what": "The official demo repo for PrismML's Bonsai model family, built around extreme quantization: the 1-bit version uses ~1.125 bits per weight so a 27B model fits a modern iPhone; the ternary version (~1.7 bits) is the higher-quality default. The newest 27B is a vision-language model with image input, tool calling, MCP, 256k+ context and adjustable reasoning effort.",
        "content": "A pure Shell project: setup.sh / setup.ps1 one-liners install dependencies and pull models, scripts/ holds run/download scripts, plus three whitepaper PDFs, an AGENTS.md (a config guide written for AI agents), topical docs (VISION/TOOLS/…) and community benchmarks.",
        "stack": "Shell + a llama.cpp server, models hosted on HuggingFace; runs on Mac Metal, CUDA/Vulkan/ROCm or plain CPU; Apache-2.0.",
        "hot": "The family's biggest model — its first vision-language release, Bonsai 27B — dropped yesterday; 'a 27B model running on an iPhone' plus batteries-included scripts travels far.",
        "uses": [
          "Mobile / edge developers — run a 27B vision-language model offline on an iPhone",
          "Privacy-sensitive settings — local AI assistants for medical or legal data that can't leave the device",
          "Hardware tinkerers — run LLMs on low-power boards like a Raspberry Pi"
        ]
      }
    },
    {
      "slug": "exercises-dataset",
      "full": "hasaneyldrm/exercises-dataset",
      "rank": 7,
      "cat": "infra",
      "lang": "HTML",
      "stars": 15.2,
      "today": "+710",
      "today_n": 710,
      "auto": false,
      "zh": {
        "tag": "1324 个健身动作数据集，带动图和 10 国语言说明",
        "what": "开箱即用的健身动作数据集：1324 个动作，每个配动画 GIF、180×180 缩略图、目标肌群/器械/分类等结构化字段，以及 10 种语言（含中文）的分步动作说明。定位「健身应用的数据层」—— 作者是 LogPress 健身打卡 App 的开发者，这个库就是他 App 背后的数据，适合做健身 App、动作推荐 ML 项目或教学演示。",
        "content": "data/exercises.json（结构化数据）+ videos/（1324 个 GIF）+ images/（缩略图），外加 index.html 交互式浏览器和 setup.html 开发者接入指南。",
        "stack": "纯数据仓库：JSON + GIF + 静态 HTML，无运行时依赖。注意：代码 MIT，GIF 媒体版权归 Gym visual 所有，商用需留意。",
        "hot": "健身类数据集稀缺，带版权清晰的动图和多语言说明的更少 —— 做健身 App / AI 教练的开发者拿去就能用。",
        "uses": [
          "健身 App 开发者 —— 直接拿 1324 个动作数据做产品，省去数月内容制作",
          "AI 教练 / 推荐系统开发者 —— 用结构化字段训练动作推荐模型",
          "教学演示 —— 数据集 + 可视化页面拿来就能讲课"
        ]
      },
      "en": {
        "tag": "1,324-exercise fitness dataset with animated GIFs in 10 languages",
        "what": "A ready-to-use fitness exercise dataset: 1,324 exercises, each with an animated GIF, a 180×180 thumbnail, structured fields (target muscles / equipment / category) and step-by-step instructions in 10 languages including Chinese. Positioned as 'the data layer for fitness apps' — the author built the LogPress workout-tracking app on top of it. Great for fitness apps, exercise-recommendation ML projects or teaching demos.",
        "content": "data/exercises.json (structured data) + videos/ (1,324 GIFs) + images/ (thumbnails), plus an interactive index.html browser and a setup.html developer onboarding guide.",
        "stack": "A pure data repo: JSON + GIFs + static HTML, no runtime. Note: code is MIT, but the GIF media is copyrighted by Gym visual — check before commercial use.",
        "hot": "Fitness datasets are scarce, and ones with clean animated GIFs and multilingual instructions are scarcer — developers building fitness apps or AI coaches can use it as-is.",
        "uses": [
          "Fitness app developers — ship faster with 1,324 ready-made exercises, skipping months of content production",
          "AI coach / recommendation builders — train exercise recommenders on the structured fields",
          "Educators — the dataset plus its visual browser is demo-ready"
        ]
      }
    },
    {
      "slug": "awesome-llm-apps",
      "full": "Shubhamsaboo/awesome-llm-apps",
      "rank": 8,
      "cat": "ai",
      "lang": "Python",
      "stars": 123.1,
      "today": "+923",
      "today_n": 923,
      "auto": false,
      "zh": {
        "tag": "100+ 个能直接跑起来的 AI Agent 和 RAG 应用合集",
        "what": "超大号 LLM 应用模板库：收录 100 多个亲手构建并端到端测试过的 AI agent、agent skill 和 RAG 应用，全部 Apache-2.0 可商用。兼容 Claude、Gemini、GPT、DeepSeek、Llama、Qwen 等主流模型，克隆下来装依赖就能跑，口号「clone, customize, ship」。",
        "content": "按难度和形态分目录：agent_skills/（npx 一键装技能）、starter_ai_agents/（单文件入门）、advanced_ai_agents/（多智能体团队）、voice_ai_agents/、always_on_agents/、RAG 教程等；每个模板配 README 和依赖清单，场景覆盖旅行规划、金融分析、播客生成、房屋装修等。",
        "stack": "Python 为主，常见 Streamlit 前端 + 各家模型 SDK，部分用 CrewAI/AG2 等多智能体框架。",
        "hot": "122.7k 的存量巨无霸还在涨：最近押注 agent skills 新形态、每周更新模板，配 Unwind AI 教程引流，LLM 应用层常青树。",
        "uses": [
          "AI 入门开发者 —— 克隆单文件模板，一天跑通第一个 LLM 应用",
          "创业团队 —— 基于成熟模板二开（旅行规划 / 金融分析 / 播客生成）快速验证 idea",
          "企业技术选型 —— 横向对比 CrewAI / AG2 等框架的真实代码"
        ]
      },
      "en": {
        "tag": "100+ AI Agent & RAG apps you can actually run",
        "what": "A giant library of LLM app templates: 100+ hand-built, end-to-end-tested AI agents, agent skills and RAG apps, all Apache-2.0 (commercial use OK). Works with Claude, Gemini, GPT, DeepSeek, Llama, Qwen and more — clone, install deps, run. The motto: 'clone, customize, ship'.",
        "content": "Organized by difficulty and form: agent_skills/ (one-line npx installs), starter_ai_agents/ (single-file starters), advanced_ai_agents/ (multi-agent teams), voice_ai_agents/, always_on_agents/, RAG tutorials and more; each template ships a README and requirements, covering travel planning, financial analysis, podcast generation, home renovation…",
        "stack": "Mostly Python, usually a Streamlit frontend over OpenAI/Gemini/Anthropic SDKs, some CrewAI/AG2 multi-agent frameworks.",
        "hot": "A 122.7k-star giant that keeps growing: it recently bet on the agent-skills form factor, ships new templates weekly, and funnels readers from the Unwind AI tutorials.",
        "uses": [
          "AI beginners — clone a single-file template and ship your first LLM app in a day",
          "Startup teams — fork mature templates (travel planning, finance analysis, podcast generation) to validate ideas fast",
          "Enterprise evaluators — compare CrewAI / AG2 and other frameworks on real code"
        ]
      }
    },
    {
      "slug": "lobehub",
      "full": "lobehub/lobehub",
      "rank": 9,
      "cat": "agent",
      "lang": "TypeScript",
      "stars": 80.3,
      "today": "+71",
      "today_n": 71,
      "auto": false,
      "zh": {
        "tag": "你的「AI 团队总管」：把一堆 agent 组织起来 7×24 干活",
        "what": "定位「Chief Agent Operator」：把多个 AI agent 当工作单元统一招聘、调度和汇报。核心功能包括 Agent Builder（描述需求即可自动配置出可用 agent）、Agent Groups（多 agent 并行协作）、Pages/Schedule/Project/Workspace 协作面板，以及白盒可编辑的 Personal Memory；支持接入任意模型和模态，号称 10000+ skills 和 MCP 插件生态。",
        "content": "可自部署的 Web 应用（Vercel/Docker/Zeabur/Sealos 一键部署），仓库含完整中英文档、Changelog、插件体系和本地开发指南；默认分支 canary，今天仍在高频 push。",
        "stack": "TypeScript + Next.js 系 Web 应用，Docker 自托管，插件走 MCP 协议；许可证为自定义（非标准）。",
        "hot": "80.1k 老牌项目的稳定热度：最近押注「多 agent 调度 + IM Gateway」叙事，持续曝光。",
        "uses": [
          "一人公司 / 自由职业者 —— 组建 7×24 自动干活的 agent 团队处理重复工作",
          "运营团队 —— 定时调度 agent 做日报、巡检、内容分发",
          "进阶玩家 —— 用 Personal Memory 和 10000+ skills 定制专属助手"
        ]
      },
      "en": {
        "tag": "Your 'Chief Agent Operator' — an AI team working 7×24",
        "what": "Positioned as a 'Chief Agent Operator': hire, schedule and hear reports from multiple AI agents as work units. Key features: Agent Builder (describe the need, get a configured agent), Agent Groups (parallel multi-agent collaboration), Pages/Schedule/Project/Workspace panels, and a white-box editable Personal Memory; any model and modality, with a claimed 10,000+ skills and MCP plugin ecosystem.",
        "content": "A self-deployable web app (one-click Vercel/Docker/Zeabur/Sealos), with full bilingual docs, a changelog, the plugin system and local dev guides; default branch canary, still pushing frequently today.",
        "stack": "TypeScript + Next.js, self-hosted via Docker, plugins over MCP; custom (non-standard) license.",
        "hot": "Steady heat for an 80.1k veteran: it's now betting on the 'multi-agent scheduling + IM Gateway' narrative and stays in the spotlight.",
        "uses": [
          "Solo founders & freelancers — run a 7×24 agent team for repetitive work",
          "Ops teams — schedule agents for daily reports, patrols and content distribution",
          "Power users — craft custom assistants with Personal Memory and 10,000+ skills"
        ]
      }
    },
    {
      "slug": "yimmenuv2",
      "full": "YimMenu/YimMenuV2",
      "rank": 10,
      "cat": "other",
      "lang": "C++",
      "stars": 1.5,
      "today": "+128",
      "today_n": 128,
      "auto": false,
      "zh": {
        "tag": "GTA 5 增强版的开源作弊菜单 DLL",
        "what": "《GTA 5: Enhanced》的实验性修改菜单（mod menu）：编译成 DLL 后用 Xenos 等注入器在游戏主菜单注入，按 INSERT 或 Ctrl+\\ 呼出菜单。建议配合 FSL 把存档数据重定向到本地磁盘以保号，且需要关闭 BattlEye 反作弊（目前没有 BE 绕过，公共战局会被心跳检测踢出）。",
        "content": "C++ 源码 + 一份简短 README，讲清使用步骤（FSL → 下载 nightly release → 注入器 → 关 BattlEye → 注入）和常见问题修复（掉线、存档消失、游戏起不来）。",
        "stack": "C++，DLL 注入式单机/联机修改器，依赖外部注入器和 FSL，GPL-2.0；默认分支 enhanced。",
        "hot": "GTA5 增强版 mod 圈刚需工具，YimMenu 系在这类开源菜单里口碑最老，7 月 12 日仍在更新。",
        "uses": [
          "GTA5 单机玩家 —— 刷车刷钱体验全部游戏内容",
          "mod 开发者 —— 基于源码学习或二次开发游戏菜单",
          "离线娱乐 —— 关 BattlEye 后在私人战局整活"
        ]
      },
      "en": {
        "tag": "The open-source mod menu DLL for GTA 5: Enhanced",
        "what": "An experimental mod menu for GTA 5: Enhanced: compile to a DLL, inject at the main menu with an injector like Xenos, then press INSERT or Ctrl+\\ to open. Pairing with FSL (redirecting save data to local disk) is recommended to protect your account, and BattlEye anti-cheat must be disabled (there's no BE bypass — public sessions will kick you via heartbeat checks).",
        "content": "C++ source plus a short README covering the workflow (FSL → nightly release → injector → disable BattlEye → inject) and fixes for common issues (disconnects, missing saves, game won't launch).",
        "stack": "C++, a DLL-injection single/multiplayer mod menu relying on external injectors and FSL; GPL-2.0; default branch enhanced.",
        "hot": "A must-have in the GTA5 Enhanced modding scene — the YimMenu line is the most established of these open menus, still updated on July 12.",
        "uses": [
          "GTA5 single-player fans — unlock vehicles and cash to experience all content",
          "mod developers — learn from or fork the source for custom game menus",
          "Offline fun — mess around in private sessions with BattlEye off"
        ]
      }
    },
    {
      "slug": "deeptutor",
      "full": "HKUDS/DeepTutor",
      "rank": 11,
      "cat": "ai",
      "lang": "Python",
      "stars": 27.0,
      "today": "+656",
      "today_n": 656,
      "auto": false,
      "zh": {
        "tag": "港大出品的 AI 私人家教：个性化终身学习工作区",
        "what": "香港大学 HKUDS 实验室的「agent 原生」学习平台：聊天辅导、刷题测验、深度研究、可视化、解题、Mastery Path 掌握度练习跑在同一套 agent 循环上。支持多引擎 RAG 知识库（LlamaIndex、PageIndex、GraphRAG、LightRAG，可挂 Obsidian 库），可从任意对话呼叫 Claude Code / Codex 等子 agent；带三层可检查记忆（L1 trace / L2 摘要 / L3 综合）和 Memory Graph 溯源。",
        "content": "完整 Web 应用（Python 后端 + Next.js 16 前端），附 11 种语言 README、Docker 部署、CLI/agent-native 接口、EduHub 社区 skills 生态；发版极勤。",
        "stack": "Python 3.11+ + Next.js 16，RAG 多引擎 + MCP 工具 + FAISS 向量库，Apache-2.0；2025 年 12 月底创建，有 arXiv 论文背书。",
        "hot": "上线半年多冲到 26.8k ——「AI 教育 + agent 原生」双热点，高校实验室背书 + 极密发版节奏，社区运营齐全。",
        "uses": [
          "学生 / 自学者 —— 把教材和论文喂进去，得到 24 小时私人家教",
          "考研 / 考证党 —— 用刷题测验 + 掌握度路径系统备考",
          "知识管理玩家 —— 直接挂 Obsidian 库做 RAG 问答"
        ]
      },
      "en": {
        "tag": "An AI personal tutor from HKU: a lifelong, personalized learning workspace",
        "what": "An 'agent-native' learning platform from HKU's HKUDS lab: chat tutoring, quizzes, deep research, visualization, problem solving and Mastery-Path practice all run on one agent loop. It supports multi-engine RAG knowledge bases (LlamaIndex, PageIndex, GraphRAG, LightRAG — even your Obsidian vault), lets you call Claude Code / Codex sub-agents from any conversation, and ships three-layer inspectable memory (L1 trace / L2 summary / L3 synthesis) with a Memory Graph for provenance.",
        "content": "A full web app (Python backend + Next.js 16 frontend) with READMEs in 11 languages, Docker deployment, CLI/agent-native interfaces and the EduHub community skills ecosystem; releases ship very frequently.",
        "stack": "Python 3.11+ + Next.js 16, multi-engine RAG + MCP tools + FAISS; Apache-2.0; created late December 2025 with an arXiv paper behind it.",
        "hot": "26.8k stars in just over half a year — riding both 'AI education' and 'agent-native' trends, with a university lab's credibility and a relentless release cadence.",
        "uses": [
          "Students & self-learners — feed in textbooks and papers, get a 24/7 personal tutor",
          "Exam candidates — prepare systematically with quizzes and the mastery path",
          "PKM enthusiasts — plug your Obsidian vault straight in for RAG Q&A"
        ]
      }
    },
    {
      "slug": "skills",
      "full": "mattpocock/skills",
      "rank": 12,
      "cat": "agent",
      "lang": "Shell",
      "stars": 174.6,
      "today": "+2.1k",
      "today_n": 2060,
      "auto": false,
      "zh": {
        "tag": "TypeScript 网红 Matt Pocock 自用的 Claude 技能包",
        "what": "Matt Pocock（Total TypeScript 作者）把自己 .claude 目录里日常用的 agent skills 原样开源，主打「真工程，不是 vibe coding」。每个 skill 解决一个具体失败模式：/grill-me、/grill-with-docs 让 agent 先反问对齐需求，/tdd 强制红绿重构，/diagnosing-bugs 调试循环，还有 /triage、/to-spec、/to-tickets、/code-review 等。设计哲学是小、可组合、模型无关 —— 把控制权留给人。",
        "content": "skills/ 目录下的 Markdown skill 文件（engineering / productivity / misc，engineering 下 18 个 skill）+ ADR 文档和安装脚本；两种装法：npx skills add 拷进项目随便改，或 Claude Code 插件市场订阅式安装，兼容 Agent-Skills 标准的 harness。",
        "stack": "Markdown skills + Shell 安装脚本，MIT；走 Claude Code 插件市场和 skills.sh 生态。",
        "hot": "2026 年 2 月才建仓库，5 个多月冲到 173.9k —— 作者本人流量 +「skills 取代重型流程框架」的叙事，踩中 skills 生态爆发风口。",
        "uses": [
          "Claude Code 用户 —— 一行命令装进项目，立刻获得 TDD / 调试 / 需求澄清工作流",
          "团队 Lead —— 把 skill 拷进仓库，统一全组的 AI 协作方式",
          "方法论学习者 —— 读 ADR 学「怎么写好一个 skill」"
        ]
      },
      "en": {
        "tag": "TypeScript celebrity Matt Pocock's own Claude skill pack",
        "what": "Matt Pocock (author of Total TypeScript) open-sourced the agent skills he actually uses from his .claude directory — 'real engineering, not vibe coding'. Each skill fixes one concrete failure mode: /grill-me and /grill-with-docs make the agent interrogate requirements first, /tdd enforces red-green-refactor, /diagnosing-bugs runs a debug loop, plus /triage, /to-spec, /to-tickets, /code-review and more. The philosophy: small, composable, model-agnostic — control stays with the human.",
        "content": "Markdown skill files under skills/ (engineering / productivity / misc — 18 in engineering alone) plus ADR docs and install scripts; install via npx skills add (copy into your project, edit freely) or as a Claude Code plugin subscription; works with any Agent-Skills-compliant harness.",
        "stack": "Markdown skills + Shell installers, MIT; distributed via the Claude Code plugin marketplace and the skills.sh ecosystem.",
        "hot": "Created February 2026 and already at 173.9k stars — the author's reach plus the 'skills replace heavy process frameworks' narrative, right on the skills-ecosystem explosion.",
        "uses": [
          "Claude Code users — one command adds TDD / debugging / requirements-clarification workflows",
          "Team leads — commit skills into the repo to standardize how the team works with AI",
          "Methodology learners — read the ADRs to learn how to write a good skill"
        ]
      }
    },
    {
      "slug": "copilot-sdk",
      "full": "github/copilot-sdk",
      "rank": 13,
      "cat": "agent",
      "lang": "Java",
      "stars": 9.7,
      "today": "+13",
      "today_n": 13,
      "auto": false,
      "zh": {
        "tag": "把 GitHub Copilot 智能体嵌进你自己应用的官方 SDK",
        "what": "GitHub 官方出的多语言 SDK：在自己的应用或服务里直接调用 Copilot Agent 的能力。它暴露的是 Copilot CLI 背后同一套经过生产验证的 agent 运行时 —— 你不用自己搭编排层，定义好 agent 行为，规划、工具调用、文件编辑都交给 Copilot 处理。",
        "content": "单仓库 6 套 SDK，按目录分：nodejs/、python/、go/、dotnet/、java/、rust/，另有 docs/、test/ 和 cookbook 示例；各语言经 npm / PyPI / NuGet / Maven Central / crates.io 分发。",
        "stack": "多语言 monorepo（TS/Python/Go/.NET/Java/Rust 六个 SDK），MIT；2026 年 1 月创建，推送非常活跃。",
        "hot": "「Copilot agent 能力开放给第三方应用」的定位自带关注度，GitHub 官方背书。",
        "uses": [
          "SaaS 厂商 —— 在产品里内嵌 Copilot 级 AI 助手（IDE、低代码平台等）",
          "企业内部工具 —— 快速给内部系统加 agent 能力，不用自研编排",
          "多语言团队 —— JS / Python / Go / .NET / Java / Rust 任选"
        ]
      },
      "en": {
        "tag": "GitHub's official SDK for embedding the Copilot agent in your own apps",
        "what": "GitHub's official multi-language SDK: call the Copilot Agent's capabilities directly from your own apps and services. It exposes the same production-proven agent runtime behind the Copilot CLI — no need to build your own orchestration layer: define the agent's behavior and let Copilot handle planning, tool calls and file edits.",
        "content": "Six SDKs in one repo, by directory: nodejs/, python/, go/, dotnet/, java/, rust/, plus docs/, test/ and cookbook examples; distributed via npm / PyPI / NuGet / Maven Central / crates.io.",
        "stack": "A multi-language monorepo (TS/Python/Go/.NET/Java/Rust), MIT; created January 2026, committing very actively.",
        "hot": "'Copilot agent capabilities opened to third-party apps' draws attention by itself — with GitHub's official stamp on it.",
        "uses": [
          "SaaS vendors — embed Copilot-grade AI assistance into products (IDEs, low-code platforms)",
          "Internal tooling — add agent capabilities to internal systems without building orchestration",
          "Polyglot teams — pick from JS / Python / Go / .NET / Java / Rust"
        ]
      }
    },
    {
      "slug": "ui-skills",
      "full": "ibelick/ui-skills",
      "rank": 14,
      "cat": "agent",
      "lang": "TypeScript",
      "stars": 4.4,
      "today": "+178",
      "today_n": 178,
      "auto": false,
      "zh": {
        "tag": "给设计工程师准备的一套 UI 类 Agent Skills",
        "what": "知名设计工程师 ibelick 出品的 UI 技能包集合：让 AI 编码 agent 按任务自动走对应的 UI 技能流程，跑一行 npx ui-skills start 就能把 agent 路由到合适的技能集。",
        "content": "skills/ 目录下 6 个技能：baseline-ui、improve-ui、fixing-accessibility、fixing-metadata、fixing-motion-performance、ui-skills-root；另有 bin/（CLI 入口）和配套网站（Astro + Cloudflare Workers）。",
        "stack": "TypeScript，CLI 走 npx 分发，MIT；2026 年 1 月创建，官网 ui-skills.com。",
        "hot": "作者本身就是设计工程师圈的知名人物，「给 AI agent 装设计品味技能」这个方向正当红。",
        "uses": [
          "前端开发者 —— 让 agent 按设计规范生成和改进 UI，告别「能跑但丑」",
          "设计工程师 —— 把无障碍、metadata、动效性能检查自动化",
          "独立开发者 —— 一人兼顾开发和设计时的品味兜底"
        ]
      },
      "en": {
        "tag": "A set of UI Agent Skills for design engineers",
        "what": "A UI skill-pack collection from well-known design engineer ibelick: routes your AI coding agent through the right UI skill workflow per task — run npx ui-skills start and the agent picks the appropriate skill set.",
        "content": "Six skills under skills/: baseline-ui, improve-ui, fixing-accessibility, fixing-metadata, fixing-motion-performance and ui-skills-root; plus bin/ (the CLI entry) and the companion site (Astro on Cloudflare Workers).",
        "stack": "TypeScript, CLI distributed via npx, MIT; created January 2026, site at ui-skills.com.",
        "hot": "The author is a known figure in the design-engineer scene, and 'installing design taste into AI agents' is a hot direction right now.",
        "uses": [
          "Frontend developers — let agents generate and improve UI to design standards, no more 'works but ugly'",
          "Design engineers — automate accessibility, metadata and motion-performance checks",
          "Indie hackers — a taste safety net when you cover both dev and design"
        ]
      }
    },
    {
      "slug": "graphify",
      "full": "Graphify-Labs/graphify",
      "rank": 15,
      "cat": "agent",
      "lang": "Python",
      "stars": 89.4,
      "today": "+1.1k",
      "today_n": 1107,
      "auto": false,
      "zh": {
        "tag": "把整个项目文件夹变成可查询知识图谱的 AI 技能",
        "what": "给 Claude Code、Codex、OpenCode、Cursor、Gemini CLI 等 AI 编码助手用的 skill：输入 /graphify，它就把整个项目（代码、SQL schema、文档、PDF、图片、视频）映射成一张可查询的知识图谱，代替 grep 翻文件。代码解析走 tree-sitter AST —— 确定性、不用 LLM、完全本地；文档类内容才走模型做语义处理。不是向量索引，是真图谱，每条边标注 EXTRACTED（直接读到）还是 INFERRED（推断出来）。",
        "content": "以 CLI 形式分发（PyPI 包 graphifyy，uv tool install 或 pipx 安装），仓库含 docs/（30 多种语言 README 翻译）和交互式 graph.html 可视化产物；默认分支 v8，迭代很快。",
        "stack": "Python + tree-sitter 代码解析，产出力导向 HTML 图；挂到各家 CLI 助手上当 skill 用。",
        "hot": "README 挂着 YC S26 徽章 ——「知识图谱代替向量检索给 AI 助手供上下文」正踩在 RAG 焦虑点上，88.7k 总量说明已出圈。",
        "uses": [
          "接手中大型老项目的开发者 —— 一条命令生成知识图谱，快速搞清代码结构",
          "AI 重度用户 —— 给 agent 换图谱上下文，替代检索不准的向量 RAG",
          "技术文档团队 —— 把文档 / PDF / 图纸一起纳入可查询图谱"
        ]
      },
      "en": {
        "tag": "An AI skill that turns a whole project folder into a queryable knowledge graph",
        "what": "A skill for Claude Code, Codex, OpenCode, Cursor, Gemini CLI and more: type /graphify and your entire project — code, SQL schemas, docs, PDFs, images, videos — is mapped into a queryable knowledge graph, replacing grep-and-scroll. Code parsing uses tree-sitter AST: deterministic, no LLM, fully local; only document content goes through a model. Not a vector index — a real graph, with every edge labeled EXTRACTED (read directly) or INFERRED.",
        "content": "Distributed as a CLI (PyPI package graphifyy, install via uv tool install or pipx); the repo holds docs/ (README translations in 30+ languages) and interactive graph.html visualizations; default branch v8, iterating fast.",
        "stack": "Python + tree-sitter, outputting force-directed HTML graphs; hooks into each CLI assistant as a skill.",
        "hot": "Sports a YC S26 badge — 'knowledge graphs instead of vector search for agent context' lands right on the RAG anxiety, and 88.7k total stars say it's broken out.",
        "uses": [
          "Developers inheriting large legacy projects — one command maps the codebase into a knowledge graph",
          "Heavy AI users — swap vector RAG for graph context that retrieves the right thing",
          "Docs teams — fold docs, PDFs and diagrams into one queryable graph"
        ]
      }
    },
    {
      "slug": "build-your-own-x",
      "full": "codecrafters-io/build-your-own-x",
      "rank": 16,
      "cat": "other",
      "lang": "Markdown",
      "stars": 526.5,
      "today": "+435",
      "today_n": 435,
      "auto": false,
      "zh": {
        "tag": "教你从零重写各种技术的教程大合集",
        "what": "CodeCrafters 维护的著名教程索引仓库，理念是费曼那句「我不能创造的东西，我就不理解」。收录大量「从零重写某技术」的 step-by-step 教程链接，覆盖数据库、操作系统、Git、Docker、编程语言、神经网络、Web 浏览器等约 30 个类别。",
        "content": "主体是一个巨大的 README 列表，按「Build your own X」分类组织，每条标注所用编程语言和链接（如用 Python 写 LLM、用 C++ 写光线追踪）；无代码本体。",
        "stack": "纯 Markdown 文档；收录的教程本身横跨 C/C++/Python/Go/Rust 等各种语言。",
        "hot": "52.6 万 star 的神仓、GitHub 全站 star 最多的仓库之一 —— AI 时代「亲手造一遍理解原理」反而更有市场，常青树稳定进账。",
        "uses": [
          "在校生 / 转行者 —— 按「造一遍」路线真正理解数据库、操作系统原理",
          "资深工程师 —— 面试前用手写 Git / Docker 项目补底层功底",
          "技术布道者 —— 按分类找写作和分享素材"
        ]
      },
      "en": {
        "tag": "The giant collection of 'rebuild your favorite tech from scratch' tutorials",
        "what": "CodeCrafters' famous tutorial index, founded on Feynman's 'What I cannot create, I do not understand'. It collects step-by-step 'build your own X' tutorial links across ~30 categories: databases, operating systems, Git, Docker, programming languages, neural networks, web browsers and more.",
        "content": "Essentially one huge README list organized by 'Build your own X' categories, each entry tagged with its language and link (e.g. write an LLM in Python, a raytracer in C++); no code of its own.",
        "stack": "Pure Markdown; the tutorials themselves span C/C++/Python/Go/Rust and more.",
        "hot": "A 526.1k-star legend — one of the most-starred repos on all of GitHub; in the AI era, 'build it once to understand it' is more valuable than ever.",
        "uses": [
          "Students & career switchers — truly understand databases and OS internals by building them",
          "Senior engineers — shore up fundamentals before interviews by hand-rolling Git / Docker",
          "Tech writers — find writing and talk material by category"
        ]
      }
    },
    {
      "slug": "computer-science",
      "full": "ossu/computer-science",
      "rank": 17,
      "cat": "other",
      "lang": "HTML",
      "stars": 206.7,
      "today": "+107",
      "today_n": 107,
      "auto": false,
      "zh": {
        "tag": "用免费网课自学完整个 CS 本科的路线",
        "what": "Open Source Society University 的计算机科学课程体系：用免费的在线材料（多来自哈佛、MIT、普林斯顿等名校课程）拼出一套完整的 CS 本科教育。课程按 CS 2013 本科课程标准挑选，分 Intro CS、Core CS、Advanced CS 和毕业项目四个阶段，每周 20 小时约 2 年可完成，材料基本全免费。",
        "content": "README 即完整课程大纲和学习路径，另有 extras/（补充课程和书单）、CURRICULAR_GUIDELINES.md，配套网站 cs.ossu.dev 和进度估算电子表格。",
        "stack": "文档仓库（HTML/Markdown），内容聚合自 Coursera、edX 等平台的公开课。",
        "hot": "206.4k stars 的自学 CS 领域标杆 ——「免费系统自学」的需求长盛不衰，稳定涨星。",
        "uses": [
          "转码自学者 —— 零成本获得体系化 CS 本科教育路线",
          "在职补基础 —— 每周 20 小时，约两年补完核心课程",
          "培训班学员 —— 用作课外补充和毕业项目参考"
        ]
      },
      "en": {
        "tag": "A complete CS undergrad education from free online courses",
        "what": "The Open Source Society University's computer-science curriculum: a full CS undergrad education assembled from free online materials (largely Harvard, MIT and Princeton courses). Courses are chosen per the CS 2013 curricular standard across four stages — Intro CS, Core CS, Advanced CS and a final project; at ~20 hours a week it takes about 2 years, and the materials are almost entirely free.",
        "content": "The README is the complete syllabus and learning path; extras/ holds additional courses and reading lists, plus CURRICULAR_GUIDELINES.md, the cs.ossu.dev site and a progress-estimating spreadsheet.",
        "stack": "A documentation repo (HTML/Markdown) aggregating courses from Coursera, edX and similar platforms.",
        "hot": "The 206.4k-star benchmark for self-taught CS — demand for 'a free, systematic way to learn' never fades.",
        "uses": [
          "Self-taught switchers — a structured CS undergrad path at zero cost",
          "Working professionals — finish the core courses in ~2 years at 20 hrs/week",
          "Bootcamp students — use it as a supplement and final-project reference"
        ]
      }
    }
  ]
}
