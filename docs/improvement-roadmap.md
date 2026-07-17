# Trending Scope 改进路线 / Improvement Roadmap

> 记录站点后续完善的方向与优先级。已完成项打勾并附实现说明。
> Ideas for improving the site, ordered by value. Checked items link to their implementation.

## ✅ 已落地 / Shipped

### 1. 每日自动更新管线（本轮完成 · 2026-07-17）
- **问题**：站点数据是 2026-07-17 凌晨的一次性快照，第二天就过期。
- **方案**：
  - `scripts/update.py` —— 直连 `github.com/trending` 抓取当日榜单（Repositories · Today · All languages · 未登录口径），解析排名 / 描述 / 语言 / 总 stars / 今日新增。
  - 已在榜仓库**保留人工撰写的深度解析**，只更新排名与 star 数；新上榜仓库自动生成带 `⚡ 自动摘要` 标记的条目（取自 GitHub 描述），待人工补充精评。
  - `.github/workflows/daily-update.yml` —— GitHub Actions 每天 **00:23 UTC（北京时间 08:23）** 自动运行，数据有变化才提交，推送后 GitHub Pages 自动重新发布。也可在 Actions 页手动触发（workflow_dispatch）。
- **保护**：解析结果少于 10 个仓库（页面结构变更）时脚本直接失败退出，不会用坏数据覆盖 `data.json`。

### 2. 数据与页面分离（本轮完成 · 2026-07-17）
- **问题**：数据硬编码在两个 HTML 文件里，中英两份各自维护，改数据必须动页面。
- **方案**：
  - 单一数据源 `data.json`（双语 schema：每个仓库 `zh` / `en` 两个文本块，含分类名、hero 文案、统计口径）。
  - `data.js` 为 `data.json` 的包装（`window.TRENDING_DATA = {...}`），页面通过 `<script src>` 加载 —— **双击本地打开（file://）依然可用**，无需起服务器。
  - `index.html` / `index-en.html` 变成纯展示壳：样式 + 渲染逻辑 + 各自语言的 UI 文案，运行时按语言取用数据。
  - Hero 标题 / 副文案 / 数据核验时间 / 仓库总数等全部来自 `data.json` meta，统计数字（合计 stars、Agent 占比、语言数）由前端实时计算。

### 3. 历史档案 + 在榜追踪（本轮完成 · 2026-07-17）
- **归档**：update.py 每次运行把当日榜单快照写入 `archive/YYYY-MM-DD.json`（日期、排名、stars、今日新增），Git 提交形成连续历史。
- **追踪计算**：从归档为每个仓库计算 `track` 字段 —— 连续在榜天数 `days`、首次出现 `first`、今日首次上榜 `is_new`、回榜 `is_back`、最近 14 个在榜日的 star 历史 `hist`。
- **前端**：卡片显示「首次上榜 / 回榜 / 在榜 N 天」徽章；弹窗新增「在榜追踪 / ON-CHART TRACKING」板块，含 star 增长 sparkline（SVG 折线 + 端点日期标注）。
- **首日保护**：归档只有 1 天时无法区分「首次上榜」与「追踪刚启动」，不判 NEW，弹窗显示「在榜追踪今日启动」。
- 已用合成三日数据验证：连续 3 天、回榜、首次上榜三种状态计算与渲染全部正确。
- 日历式历史榜单回看（按日期切换查看往日榜单）留待后续，归档数据已具备。

## 🔜 候选方向 / Candidates（按价值排序）

### 4. 榜单口径切换 ⭐ 下一个最值得做
- Today / This week / This month、按编程语言过滤（github.com/trending 原生支持 `?since=` 与语言路径）。
- update.py 增加参数化抓取，前端加口径切换器。

### 5. OG / Twitter 分享卡片（低成本高回报）
- `<head>` 增加 `og:title` / `og:description` / `og:image`（用 `preview-zh.png` / `preview-en.png`）/ `twitter:card`，社媒分享带预览图。

### 6. 暗色模式
- 暖纸米的对应面：墨黑底 + 暖橙点缀，延续编辑部气质；`prefers-color-scheme` + 手动切换。

### 7. 紧凑列表视图
- 卡片之外加高密度表格视图（排名 / 仓库 / 语言 / stars / 今日新增），扫榜更快。

### 8. 一键复制分享
- 弹窗内「复制 Markdown」按钮：`[owner/repo](url) — 一句话点评`，方便转发到 issue / 群聊 / 周刊。

### 9. 项目对比
- 选 2-3 个项目并排比较 stars / 定位 / 技术栈 / 应用场景。

### 10. RSS feed
- 管线顺带生成 `feed.xml`，老派用户可订阅每日榜。

### 11. 视觉打磨
- Hero 引入衬线大标题（如 Noto Serif SC）强化「每日编辑部」气质；今日新增 stars 做横向 racing bar，突出榜单脉搏。

## 可选增强 / Optional

- **LLM 精评自动化**：update.py 预留了人工精评字段（`what/content/stack/hot/uses`）。如需新上榜仓库自动生成双语深度解析，可在仓库 Secrets 配置 LLM API（如 `LLM_API_KEY` + `LLM_BASE_URL`），脚本检测到后调用 OpenAI 兼容接口补全，未配置则保持「自动摘要」降级。
- **Cloudflare Pages 同步**：生产域名 trending.cosolution.cc 目前经 wrangler 手动部署。如需 Actions 自动部署，配置 `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` 两个 Secrets 后在 workflow 里加一步 `cloudflare/wrangler-action`。
