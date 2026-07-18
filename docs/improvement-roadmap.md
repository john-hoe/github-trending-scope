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
- **保护**：21 个榜单均三次重试并校验完整矩阵、最低条目数、连续排名与重复项；任一榜单异常即失败，不覆盖数据。

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
- **抓取**：update.py 重写为多口径版 —— 每日 / 每周 / 每月 × 7 个语言筛选（All / Python / TypeScript / JavaScript / Rust / Go / C++）共 **21 个榜单**一次抓全（`github.com/trending/<lang>?since=` 原生口径）；现已改为任一榜单失败或不完整即整轮失败，避免发布部分数据。
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

### 7. 紧凑列表视图（本轮完成 · 2026-07-17）
- **视图切换**：工具栏新增「卡片 / 列表」分段选择器（与口径切换同款样式），选择写入 localStorage（`ts-view`）记忆。
- **列表设计**：高密度表格行 —— 排名 / 仓库名 + 在榜徽章 + 一句话摘要 / 语言 / Stars / 区间新增 / 分类 pill；表头新增列跟随当前口径（今日新增 / 本周新增 / 本月新增）；行点击与回车键同样打开弹窗。
- **实现**：筛选 + 排序逻辑抽为 `currentFiltered()` 卡片与列表共用；行入场动画更轻的阶梯延迟（18ms）；窄屏（<960px）自动隐藏语言与分类列；暗色模式全套适配。
- 已验证：列表日榜 / 周榜+Python / 暗色列表 / 列表上打开弹窗 / 切换探测 / 卡片视图回归，全部通过。

### 8. 一键复制分享（本轮完成 · 2026-07-17）
- **弹窗新增「复制 Markdown / Copy Markdown」按钮**（在「打开 GitHub」与「返回列表」之间）：一键复制 `[owner/repo](https://github.com/owner/repo) — 一句话点评`，方便转发到期刊、群聊或 issue。
- **反馈**：复制成功后按钮短暂变为「已复制 ✓ / Copied ✓」（1.6s，青绿色高亮）。
- **兼容**：`navigator.clipboard` 不可用时自动降级为隐藏 textarea + `execCommand("copy")`，file:// 直开与非安全上下文均可用。
- 已验证：中/英/暗色弹窗按钮布局、点击反馈探测（已复制 ✓），全部通过。

### 9. 项目对比（本轮完成 · 2026-07-17）
- **加入对比**：卡片缩略图右上与列表行尾新增圆形「+ / ✓」按钮，最多选 3 个仓库；选满后再点托盘抖动提示。选择状态跨榜单 / 语言 / 视图切换保持。
- **底部托盘**：选中即浮出，显示「已选 n/3」+ 可单独移除的名称胶囊 +「开始对比」（少于 2 个时禁用）+「清空」。
- **对比视图**：复用详情弹窗容器（对比模式加宽至 1080px），11 行并排 —— 排名（含所在榜单口径）/ Stars / 区间新增 / 语言 / 分类 / 在榜 / 定位 / 是做什么的 / 技术栈 / 应用场景 / 为什么火；中英双语全套文案，暗色模式适配。
- **修过一处渲染 bug**：排名行误把整个仓库对象传给文案函数（渲染成 `[object Object]`），截图自查发现后改为传排名数值，重新生成测试页复检通过。
- 已验证：中文 2 列、暗色 3 列、英文 2 列对比视图，托盘交互（添加 / 移除 / 上限抖动），普通详情弹窗回归，全部通过。

### 10. 视觉打磨（本轮完成 · 2026-07-17）
- **衬线 Hero**：大标题改用 Noto Serif（拉丁）+ Noto Serif SC（中文）900 字重（Google Fonts，`display=swap`，加载失败回退系统衬线），行距与字距随衬线重调。
- **区间新增 racing bar**：原「Star 热度 TOP 8（总 stars）」改为「今日 / 本周 / 本月新增 TOP 8」—— 按当前口径的区间新增排序、数值显示 +N，行入场 70ms 阶梯延迟形成竞速感；`activeList()` 合并 `today_n` 供排序。
- 已验证：h1 字体栈 / 标题跟随口径 / 数值探针，中、英、暗三端首屏截图，全部通过。

### 11. LLM 精评自动化（本轮完成 · 2026-07-17）
- **update.py 可选精评**：配置 `LLM_API_KEY` + `LLM_BASE_URL`（OpenAI 兼容接口）后，每轮对新上榜及历史 auto 仓库调用 `/chat/completions` 生成双语六字段解析（tag / what / content / stack / hot / uses）+ 四选一分类；成功会清除 auto 占位标记并保留内容，但不代表人工事实核验，SEO 是否开放索引由独立清单控制。
- **上下文与限速**：prompt 附 README 前 3000 字符摘录（`LLM_README=0` 可关）；每轮上限 `--llm-limit`（默认 25，env `LLM_LIMIT`），新上榜优先，请求间隔 0.4s。
- **降级矩阵**：未配置密钥 / 连接失败 / 返回非 JSON / 字段不完整 → 全部静默保持自动摘要，绝不影响管线主流程；模型名 `LLM_MODEL`（默认 gpt-4o-mini）。
- **Actions**：workflow 注入 `secrets.LLM_API_KEY` / `secrets.LLM_BASE_URL` + `vars.LLM_MODEL`（未配置时展开为空字符串 → 自动降级）。
- 已验证：mock 接口成功路径（3 仓库精评落盘）、坏 JSON 降级、连接失败降级、无密钥降级、精评结果次日 kept 保留，全部通过。

### 12. SEO 抓取与内容质量闭环（本轮完成 · 2026-07-19）
- **根因**：Cloudflare Pages 缺少顶层 `404.html`，导致 robots、sitemap 与随机路径都回退为首页 `200`；289 份仓库详情只存在于 JS 弹窗和 fragment 中，搜索引擎没有独立文档可索引。
- **技术修复**：`scripts/build_site.py` 生成真实 `robots.txt`、70 URL 的 XML sitemap、顶层 404、单跳 redirects、canonical/hreflang、Breadcrumb + CollectionPage/SoftwareSourceCode JSON-LD，并在部署前自检所有 sitemap URL 的文件、canonical、索引状态和唯一元数据。
- **可发现架构**：21 个每日/每周/每月 × 语言榜单视图均生成中英静态页；首页生产包预渲染 14 个卡片和 21 个榜单内链，卡片入口从 button 改为真实链接，同时保留原弹窗交互。
- **质量护栏**：没有把 289 份内容全部推入索引。首期仅将可追溯到自动化扩充前原始数据集、且当前仍在册的 13 个仓库解析纳入 sitemap；其余详情可访问但为 `noindex,follow`。13 项中的过期 Star/“今日”表述已改为非时效描述，动态排名与增量由当日榜单字段渲染。
- **验证**：46 项回归测试覆盖生产构建、70 个唯一 indexable canonical、双语榜单、初始 HTML 正文、JSON-LD 可解析、目录无孤儿链接、非入选详情 noindex、索引页两次点击可达、更新/构建质量门槛一致与内容时效性门槛。

## 🔜 候选方向 / Candidates

当前无排期候选 —— 新方向随每日运营观察补充。（RSS feed 经评估暂不采用。）

## 可选增强 / Optional

- **Cloudflare Pages 同步**：workflow 已包含条件部署；配置 `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` 两个 Secrets 后自动同步 `trending-scope`，未配置时安全跳过。
