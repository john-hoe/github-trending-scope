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

每天 GitHub Trending 的榜单只是一串链接。**Trending Scope** 把它做成一个单文件、零依赖的本地网页：

GitHub Trending is just a list of links. **Trending Scope** turns it into a single-file, zero-dependency local web page:

- **17+ 上榜仓库的深度解析** / Deep dives for every trending repo —— 点击卡片弹出：是做什么的 / 仓库里有什么 / 技术栈 / 应用场景 / 为什么火（What it does · What's inside · Tech stack · Use cases · Why it's hot）
- **中英双语** / Bilingual —— `index.html`（中文）与 `index-en.html`（English）一键切换
- **图表洞察** / Charts —— 分类环形图 + Star 热度 TOP 8 条形图，动画呈现
- **交互** / Interactions —— 分类筛选、实时搜索（防抖）、四种排序（榜单排名 / Stars / 名称）、「今日 +N」新增 star 徽章
- **设计** / Design —— 暖纸编辑部风格配色、极光背景、滚动入场动画、键盘可访问（Enter 打开 / Esc 关闭弹窗）

![English preview](preview-en.png)

## 怎么用 / Usage

无需安装任何东西，直接用浏览器打开：

No build, no dependencies — just open in a browser:

```bash
open index.html      # 中文版
open index-en.html   # English version
```

## 每日自动更新 / Daily auto-update

榜单数据由 **GitHub Actions 每天自动刷新**（北京时间约 08:23，见 `.github/workflows/daily-update.yml`）：

The trending data is refreshed daily by GitHub Actions (~08:23 Beijing time):

- `scripts/update.py` 直连 `github.com/trending` 抓取当日榜单，刷新 `data.json` + `data.js`
- 仍在榜的仓库**保留人工深度解析**，只更新排名与 star 数；新上榜仓库自动生成带 ⚡ 标记的摘要，人工精评随后补充
- Repos that stay on the chart keep their human-written deep dives (only rank/stars update); new entries get an auto summary flagged ⚡ pending a human write-up
- 手动更新 / Manual refresh: `python3 scripts/update.py`（纯标准库，无依赖 / stdlib only）
- 改进方向见 / See `docs/improvement-roadmap.md`

## 数据说明 / Data notes

- 当前数据时间见页脚与 `data.json` 的 `meta.generated_at`，口径为 `github.com/trending`（Repositories · Today · All languages · 未登录）。
- 登录 GitHub 账号或切换语言/时间筛选，看到的榜单可能不同。
- Data timestamp: see the page footer or `meta.generated_at` in `data.json` (Repositories · Today · All languages · logged out). Signed-in users or other filters may see a different list.

## 仓库结构 / Structure

```
├── index.html        # 中文版页面（样式+渲染逻辑，数据来自 data.js）
├── index-en.html     # English page (styles + rendering, data from data.js)
├── data.json         # 双语数据源（canonical dataset, zh + en）
├── data.js           # data.json 的页面加载包装（window.TRENDING_DATA，自动生成）
├── scripts/update.py # 每日抓取更新脚本（stdlib only）
├── .github/workflows/daily-update.yml  # GitHub Actions 每日自动更新
├── docs/improvement-roadmap.md         # 改进路线
├── videos/           # 45s 宣传视频（中文 promo-zh.mp4 / English promo-en.mp4）
├── preview-zh.png    # 中文版整页预览
├── preview-en.png    # English full-page preview
└── LICENSE           # MIT
```

## License

[MIT](LICENSE) © 2026 john-hoe
