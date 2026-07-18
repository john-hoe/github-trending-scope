# GitHub Trending Scope

> 把 github.com/trending 变成一页可看、可搜、可交互的双语全景报告
> Turn github.com/trending into an interactive bilingual one-page report.

## 宣传视频 / Promo Video · 45s

| 🇨🇳 中文宣传片 | 🇺🇸 English Promo |
| --- | --- |
| <video src="https://john-hoe.github.io/github-trending-scope/videos/promo-zh.mp4" poster="preview-zh.png" controls muted playsinline width="100%"></video> | <video src="https://john-hoe.github.io/github-trending-scope/videos/promo-en.mp4" poster="preview-en.png" controls muted playsinline width="100%"></video> |

无法内嵌播放？/ Can't play inline? 直接下载 / Download：[中文宣传片](videos/promo-zh.mp4) · [English Promo](videos/promo-en.mp4)

![中文预览](preview-zh.png)

## 这是什么 / What is this

每天 GitHub Trending 的榜单只是一串链接。**Trending Scope** 把它做成中英双语静态页面与一份共享数据、零构建依赖的本地网站：

GitHub Trending is just a list of links. **Trending Scope** turns it into two static pages backed by one shared dataset, with no build dependencies:

- **上榜仓库解析** / Trending repo explainers —— 初始编辑内容与模型生成的双语解析并存；点击卡片查看功能 / 内容 / 技术栈 / 场景 / 热度原因。模型生成并不等同人工核验，只有 `seo-index.json` 明确列出的内容才进入搜索索引
- **中英双语** / Bilingual —— `index.html`（English，默认）与 `index-zh.html`（中文）一键切换；旧 `index-en.html` 链接自动跳转到默认英文页
- **可抓取 SEO 页面** / Crawlable SEO pages —— 21 个榜单视图 × 双语均有独立静态 URL、服务端正文、自 canonical、互惠 hreflang 与 JSON-LD；原始编辑集中的仓库解析才进入 sitemap，自动扩充内容默认 `noindex`
- **图表洞察** / Charts —— 分类环形图 + 区间新增 TOP 8 竞速条形图（跟随每日/每周/每月口径，animated racing bars of gainers）
- **交互** / Interactions —— 分类筛选、实时搜索（防抖）、四种排序（榜单排名 / Stars / 名称）、「今日 +N」新增 star 徽章、卡片 / 紧凑列表双视图（cards or compact list view）、项目对比（选 2~3 个仓库并排比较 / side-by-side compare for up to 3 repos）
- **设计** / Design —— 衬线大标题（Noto Serif / Noto Serif SC）+ 暖纸编辑部风格配色 + 墨黑暗色模式、极光背景、尊重 reduced-motion；支持 Tab、Enter / Space 打开、Esc 关闭及弹窗焦点管理

![English preview](preview-en.png)

## 怎么用 / Usage

无需安装任何东西，直接用浏览器打开：

No build, no dependencies — just open in a browser:

```bash
open index.html      # English version (default)
open index-zh.html   # 中文版
```

## 每日自动更新 / Daily auto-update

榜单数据由 **GitHub Actions 每天自动刷新**（北京时间约 08:23，见 `.github/workflows/daily-update.yml`）：

The trending data is refreshed daily by GitHub Actions (~08:23 Beijing time):

- `scripts/update.py` 直连 `github.com/trending` 抓取榜单，刷新 `data.json` + `data.js`，并把当日快照归档到 `archive/YYYY-MM-DD.json`
- 全部 21 个榜单均采用三次网络重试并做完整性校验；任一榜单缺失或条目异常时整轮失败，不发布部分数据
- **多口径榜单**：每日 / 每周 / 每月 × 7 个语言筛选（All / Python / TypeScript / JavaScript / Rust / Go / C++）共 21 个榜单一次抓全，页面工具栏可切换口径与语言，支持 `#board=weekly&lang=python` 深链
- Daily / Weekly / Monthly × 7 language filters (21 boards total) — switchable in the toolbar, with `#board=…&lang=…` deep links
- 仍在榜的仓库保留已有解析，只更新排名与 star 数；新上榜仓库先生成带 ⚡ 标记的摘要；配置 LLM（见下）后可生成完整双语解析，但这只代表通过字段完整性门槛，不代表人工事实核验
- **在榜追踪**：卡片显示「首次上榜 / 回榜 / 在榜 N 天」徽章，弹窗含 star 增长 sparkline（自 2026-07-17 起逐日积累）
- Repos that stay on the chart keep their existing write-ups while rank/stars update; new entries get an auto summary flagged ⚡ until a complete write-up is generated or reviewed. On-chart tracking badges and a star-history sparkline build up from the daily archives
- **可选 LLM 精评** / Optional LLM write-ups —— 仓库 Secrets 配置 `LLM_API_KEY` + `LLM_BASE_URL`（OpenAI 兼容接口；Kimi Code 网关 `https://agent-gw.kimi.com/coding` 亦可，Variables 设 `LLM_PROTOCOL=anthropic`），Variables 可选 `LLM_MODEL`；每轮为新上榜及历史 ⚡ 仓库生成双语深度解析（每轮上限 `LLM_LIMIT`，默认 25，新上榜优先），失败或未配置自动保持摘要降级
- 手动更新 / Manual refresh: `python3 scripts/update.py`（纯标准库，无依赖 / stdlib only）
- 生产构建 / Production build: `python3 scripts/build_site.py --output dist`（生成并校验 robots、sitemap、404、榜单页与仓库页）
- 回归测试 / Regression tests: `python3 -m unittest discover -s tests -v`
- 配置 `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` 后，同一 workflow 会同步部署生产域名对应的 Cloudflare Pages 项目；未配置时仅更新 GitHub Pages
- 改进方向见 / See `docs/improvement-roadmap.md`

## 数据说明 / Data notes

- 当前数据时间见页脚与 `data.json` 的 `meta.generated_at`，抓取口径为 `github.com/trending`（Repositories · 每日/每周/每月 × 语言筛选 · 未登录），页面默认展示每日·全语言榜。
- 登录 GitHub 账号或切换语言/时间筛选，看到的榜单可能不同。
- Data timestamp: see the page footer or `meta.generated_at` in `data.json` (Repositories · Today · All languages · logged out). Signed-in users or other filters may see a different list.

## 仓库结构 / Structure

```
├── index.html        # English page, default entry (styles + rendering from data.js)
├── index-zh.html     # 中文版页面（样式+渲染逻辑，数据来自 data.js）
├── index-en.html     # 旧英文入口兼容跳转 / legacy English redirect
├── data.json         # 双语数据源（canonical dataset, zh + en）
├── data.js           # data.json 的页面加载包装（window.TRENDING_DATA，自动生成）
├── seo-index.json    # 谨慎开放索引的原始编辑内容清单
├── favicon.png       # 站点图标（512×512）
├── archive/          # 每日榜单快照（YYYY-MM-DD.json，在榜追踪的历史依据）
├── scripts/update.py # 每日抓取更新脚本（stdlib only）
├── scripts/build_site.py # 静态 SEO 构建器 + 生产输出自检
├── seo.css           # 榜单目录与仓库详情页样式
├── .github/workflows/daily-update.yml  # GitHub Actions 每日自动更新
├── docs/improvement-roadmap.md         # 改进路线
├── videos/           # 45s 宣传视频（中文 promo-zh.mp4 / English promo-en.mp4）
├── preview-zh.png    # 中文版整页预览
├── preview-en.png    # English full-page preview
└── LICENSE           # MIT
```

## License

[MIT](LICENSE) © 2026 john-hoe
