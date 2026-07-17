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

### 4. 榜单口径切换（本轮完成 · 2026-07-17）
- **抓取**：update.py 重写为多口径版 —— 每日 / 每周 / 每月 × 7 个语言筛选（All / Python / TypeScript / JavaScript / Rust / Go / C++）共 **21 个榜单**一次抓全（`github.com/trending/<lang>?since=` 原生口径）。单榜失败只告警跳过，主榜（每日·全语言）解析少于 10 个才失败退出。
- **数据结构 schema 2**：`boards.{daily|weekly|monthly}.<lang>` 存各榜排名 / stars / 区间新增；`repos[]` 改为按 `full` 去重的**注册表**（本轮 285 个仓库：17 个人工精评保留 + 268 个自动摘要），双语字段只存一份，`data.json` 433 KB。
- **在榜追踪口径不变**：`track` 仍只从每日·全语言归档计算，语言榜 / 周月榜不干扰连续在榜语义。
- **前端**：
  - 工具栏新增**口径分段选择器**（每日榜 / 每周榜 / 每月榜）+ **语言下拉**；统计四项、分类环形图、TOP8 条形图、分类 chips、卡片网格全部跟随当前口径实时重算。
  - kicker 改为前端模板生成（`每日自动更新 · 日期 · 口径 · 语言 · N 个仓库`），卡片与弹窗的新增 stars 文案跟随口径（今日 / 本周 / 本月）。
  - URL hash 支持 `#board=weekly&lang=python&repo=slug` 深链；旧版 `#repo=xxx` 深链保持兼容（弹窗查找顺序：当前口径 → 每日榜 → 全部榜单）。
- 已用 headless Chrome 验证：日 / 周 / 月榜 × 语言筛选 × 中英双语 × 弹窗深链渲染全部正确。

### 5. OG / Twitter 分享卡片（本轮完成 · 2026-07-17）
- **分享图**：`og-zh.png` / `og-en.png`（1200×630，headless Chrome 直截线上新版首屏：导航 + kicker + 渐变大标题 + 统计条，各约 0.5 MB）。
- **meta**：中英两页 `<head>` 加入 `description`、Open Graph（`og:type/site_name/title/description/url/image(+宽高+alt)/locale`，zh_CN 与 en_US）与 Twitter Card（`summary_large_image` + 标题/描述/图）。
- og:image / og:url 均用生产域名绝对地址（`https://trending.cosolution.cc/` 与 `/index-en`），抓取器不执行 JS 也能拿到完整预览。

### 6. 暗色模式（本轮完成 · 2026-07-17）
- **调色板**：暖纸米的对应面 —— 墨黑底（#16120d）+ 暖橙/青/金提亮版强调色，延续编辑部气质；分类色（agent/ai/infra/other）在暗色下切换为高对比变体并全量重渲染。
- **实现**：全站 CSS 变量换肤（`html[data-theme="dark"]` 覆盖约 40 条硬编码色规则：极光背景、导航、卡片、弹窗、徽章、滚动条等），`color-scheme: dark` 让下拉框/滚动条原生变暗；环形图与 sparkline 的内联 fill/stroke 改为 CSS 变量类。
- **行为**：`<head>` 内联脚本首帧前定主题（无闪烁）；未选择过时跟随 `prefers-color-scheme` 并监听系统切换；导航栏日/月按钮手动切换并写入 localStorage 记忆。
- 已验证：暗色中/英整页、暗色弹窗（标题/徽章/板块对比度）、亮色回归无变化、按钮切换 + 记忆探测全部通过。

## 🔜 候选方向 / Candidates（按价值排序）

### 7. 紧凑列表视图 ⭐ 下一个最值得做
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
