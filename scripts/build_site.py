#!/usr/bin/env python3
"""Build and validate the production-ready static site.

The interactive landing pages remain dependency-free. This builder adds the
server-rendered pages and crawl controls that search engines need without
changing the daily data format.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://trending.cosolution.cc"
GA4_MEASUREMENT_ID = "G-P3808E86C2"
GA4_SCRIPT_URL = f"https://www.googletagmanager.com/gtag/js?id={GA4_MEASUREMENT_ID}"
GA4_CONNECT_SOURCES = (
    "https://*.google-analytics.com https://*.analytics.google.com "
    "https://*.googletagmanager.com"
)
GA4_CSP_REQUIREMENTS = (
    ("script-src", {"https://*.googletagmanager.com"}),
    ("img-src", {"https://*.google-analytics.com", "https://*.googletagmanager.com"}),
    (
        "connect-src",
        {
            "https://*.google-analytics.com",
            "https://*.analytics.google.com",
            "https://*.googletagmanager.com",
        },
    ),
)
BOARD_ORDER = ("daily", "weekly", "monthly")
REPO_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
COPY_FILES = (
    "index.html",
    "index-zh.html",
    "index-en.html",
    "data.json",
    "data.js",
    "favicon.png",
    "og-zh.png",
    "og-en.png",
    "seo.css",
)
LANG_SLUGS = {"c++": "cpp"}

TEXT = {
    "en": {
        "html_lang": "en",
        "locale": "en_US",
        "alternate_locale": "zh_CN",
        "home_path": "/",
        "directory_path": "/repos/",
        "repo_prefix": "/repos/",
        "other": "zh",
        "switch": "中文",
        "site_tag": "GitHub Trending, explained",
        "directory": "Repository analyses",
        "directory_title": "GitHub Trending Repository Analyses | Trending Scope",
        "directory_description": (
            "Browse bilingual, server-rendered analyses of repositories currently represented "
            "across GitHub Trending daily, weekly, monthly, and language charts."
        ),
        "directory_intro": (
            "A deliberately limited, crawlable library from the original editorial dataset. "
            "Each selected page explains what the project does, what is inside, its stack, "
            "use cases, and why it is trending. New pages are not indexed automatically."
        ),
        "updated": "Updated",
        "repos": "repository analyses",
        "boards": "chart views covered",
        "what": "What it does",
        "content": "What's inside",
        "stack": "Tech stack",
        "uses": "Use cases",
        "hot": "Why it's trending",
        "placements": "Current chart placements",
        "period": "Period",
        "filter": "Language filter",
        "rank": "Rank",
        "gain": "Stars gained",
        "stars": "Stars",
        "last_observed_stars": "Stars at last chart appearance",
        "language": "Language",
        "appearances": "Chart appearances",
        "tracking": "On-chart tracking",
        "days": "days tracked",
        "github": "Open repository on GitHub",
        "related": "Related repository analyses",
        "source_note": (
            "Editorial summaries are based on the public repository and the dated GitHub "
            "Trending snapshot. Verify implementation details in the upstream repository."
        ),
        "page_suffix": "Explained | Trending Scope",
        "home": "Trending Scope home",
        "all": "All languages",
        "daily": "Daily",
        "weekly": "Weekly",
        "monthly": "Monthly",
        "not_current": "Not currently represented in the tracked chart views.",
        "not_found": "Page not found",
        "not_found_text": "The requested page does not exist. Browse today's charts or the analysis library.",
        "back_home": "Back to today's GitHub Trending",
    },
    "zh": {
        "html_lang": "zh-CN",
        "locale": "zh_CN",
        "alternate_locale": "en_US",
        "home_path": "/index-zh",
        "directory_path": "/zh/repos/",
        "repo_prefix": "/zh/repos/",
        "other": "en",
        "switch": "EN",
        "site_tag": "读懂 GitHub Trending",
        "directory": "仓库深度解析",
        "directory_title": "GitHub Trending 热门仓库深度解析 | Trending Scope",
        "directory_description": (
            "浏览当前 GitHub Trending 每日、每周、每月及语言榜单中的热门仓库双语解析，"
            "了解项目功能、内容、技术栈、使用场景与走红原因。"
        ),
        "directory_intro": (
            "这里谨慎收录自动化扩充前的初始编辑内容，不会把所有模型生成内容自动放入索引。"
            "每个独立页面都提供项目功能、仓库内容、技术栈、应用场景和热度原因，且无需运行 JavaScript。"
        ),
        "updated": "更新于",
        "repos": "个仓库解析",
        "boards": "个榜单视图",
        "what": "它是做什么的",
        "content": "仓库包含什么",
        "stack": "技术栈",
        "uses": "适用场景",
        "hot": "为什么走红",
        "placements": "当前上榜位置",
        "period": "周期",
        "filter": "语言筛选",
        "rank": "排名",
        "gain": "新增 Star",
        "stars": "Star 数",
        "last_observed_stars": "最后一次上榜时的 Star 数",
        "language": "主要语言",
        "appearances": "上榜视图",
        "tracking": "在榜追踪",
        "days": "天追踪记录",
        "github": "在 GitHub 打开仓库",
        "related": "相关仓库解析",
        "source_note": (
            "编辑解析基于公开仓库信息与带日期的 GitHub Trending 快照；具体实现细节请以上游仓库为准。"
        ),
        "page_suffix": "项目解析 | Trending Scope",
        "home": "Trending Scope 首页",
        "all": "全部语言",
        "daily": "每日",
        "weekly": "每周",
        "monthly": "每月",
        "not_current": "当前追踪的榜单视图中暂无该仓库。",
        "not_found": "页面不存在",
        "not_found_text": "请求的页面不存在，请返回今日榜单或浏览仓库解析目录。",
        "back_home": "返回今日 GitHub Trending",
    },
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def compact(value: object) -> str:
    return " ".join(str(value).split())


def truncate(value: object, limit: int) -> str:
    text = compact(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip(" ,.;:，。；：") + "…"


def repo_parts(full_name: str) -> tuple[str, str]:
    if not REPO_NAME_RE.fullmatch(full_name):
        raise ValueError(f"Unsupported repository name: {full_name!r}")
    owner, name = full_name.split("/", 1)
    return owner.lower(), name.lower()


def repo_path(full_name: str, locale: str) -> str:
    owner, name = repo_parts(full_name)
    return f"{TEXT[locale]['repo_prefix']}{owner}/{name}/"


def repo_url(full_name: str, locale: str) -> str:
    return BASE_URL + repo_path(full_name, locale)


def pair_for_repo(full_name: str) -> tuple[str, str]:
    return repo_url(full_name, "en"), repo_url(full_name, "zh")


def board_path(board: str, language_id: str, locale: str) -> str:
    if board == "daily" and language_id == "all":
        return TEXT[locale]["home_path"]
    language_slug = LANG_SLUGS.get(language_id, language_id)
    prefix = "/zh/trending/" if locale == "zh" else "/trending/"
    return f"{prefix}{board}/{language_slug}/"


def board_pair(board: str, language_id: str) -> tuple[str, str]:
    return BASE_URL + board_path(board, language_id, "en"), BASE_URL + board_path(board, language_id, "zh")


def language_name(data: dict, language_id: str, locale: str) -> str:
    if language_id == "all":
        return TEXT[locale]["all"]
    found = next((row.get("name") for row in data["langs"] if row.get("id") == language_id), None)
    return found or language_id


def validate_data(data: dict) -> None:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(data.get("meta", {}).get("date", ""))):
        raise ValueError("meta.date must use YYYY-MM-DD")
    if not data.get("repos"):
        raise ValueError("No repositories to publish")
    seen: set[str] = set()
    for repo in data["repos"]:
        full_name = str(repo.get("full", ""))
        repo_parts(full_name)
        key = full_name.lower()
        if key in seen:
            raise ValueError(f"Duplicate repository path: {full_name}")
        seen.add(key)
        if repo.get("auto"):
            raise ValueError(f"Unreviewed repository cannot be indexed: {full_name}")
        for locale in ("en", "zh"):
            body = repo.get(locale) or {}
            for field in ("tag", "what", "content", "stack", "hot"):
                minimum = 8 if field == "tag" else 20
                if len(compact(body.get(field, ""))) < minimum:
                    raise ValueError(f"Thin {locale}.{field} for {full_name}")
            uses = body.get("uses")
            if not isinstance(uses, list) or len(uses) < 2 or any(len(compact(item)) < 10 for item in uses):
                raise ValueError(f"Thin {locale}.uses for {full_name}")


def placements_for(data: dict, full_name: str, locale: str) -> list[dict]:
    placements = []
    for board in BOARD_ORDER:
        for lang in data["langs"]:
            lang_id = lang["id"]
            for row in data["boards"].get(board, {}).get(lang_id, []):
                if row.get("full") == full_name:
                    placements.append(
                        {
                            "period": TEXT[locale][board],
                            "filter": language_name(data, lang_id, locale),
                            "rank": row.get("rank", "—"),
                            "gain": row.get("today", "—"),
                        }
                    )
                    break
    return placements


def hreflang_links(en_url: str, zh_url: str) -> str:
    return (
        f'<link rel="alternate" hreflang="en" href="{esc(en_url)}">\n'
        f'<link rel="alternate" hreflang="zh-CN" href="{esc(zh_url)}">\n'
        f'<link rel="alternate" hreflang="x-default" href="{esc(en_url)}">'
    )


def json_ld(payload: object) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'<script type="application/ld+json">{raw}</script>'


def ga4_tag() -> str:
    return f"""<!-- Google tag (gtag.js) -->
<script async src="{GA4_SCRIPT_URL}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA4_MEASUREMENT_ID}', {{
    'allow_google_signals': false,
    'allow_ad_personalization_signals': false
  }});
</script>"""


def csp_directives(source: str) -> dict[str, set[str]]:
    match = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)">', source)
    if not match:
        raise ValueError("HTML page is missing its Content-Security-Policy meta tag")
    directives: dict[str, set[str]] = {}
    for raw_directive in match.group(1).split(";"):
        tokens = raw_directive.split()
        if not tokens:
            continue
        name = tokens[0]
        if name in directives:
            raise ValueError(f"Duplicate CSP directive: {name}")
        directives[name] = set(tokens[1:])
    return directives


def prepare_landing_analytics(source: str) -> str:
    match = re.search(r'(<meta http-equiv="Content-Security-Policy" content=")([^"]+)(">)', source)
    if not match:
        raise ValueError("Landing page is missing its Content-Security-Policy meta tag")
    csp = match.group(2)
    replacements = (
        (
            "script-src 'self' 'unsafe-inline'",
            "script-src 'self' 'unsafe-inline' https://*.googletagmanager.com",
        ),
        (
            "img-src 'self' data: https://github.com https://avatars.githubusercontent.com https://opengraph.githubassets.com",
            "img-src 'self' data: https://github.com https://avatars.githubusercontent.com "
            "https://opengraph.githubassets.com https://*.google-analytics.com "
            "https://*.googletagmanager.com",
        ),
        ("connect-src 'none'", f"connect-src {GA4_CONNECT_SOURCES}"),
    )
    for old, new in replacements:
        if csp.count(old) != 1:
            raise ValueError(f"Unexpected landing CSP directive: {old}")
        csp = csp.replace(old, new, 1)
    csp_meta = match.group(1) + csp + match.group(3)
    return source[: match.start()] + csp_meta + "\n" + ga4_tag() + source[match.end() :]


def page_shell(
    *,
    locale: str,
    title: str,
    description: str,
    canonical: str | None,
    alternate_en: str,
    alternate_zh: str,
    body: str,
    structured_data: object,
    robots: str = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1",
) -> str:
    t = TEXT[locale]
    image = f"{BASE_URL}/og-{'zh' if locale == 'zh' else 'en'}.png"
    search_links = ""
    if canonical:
        search_links = f'<link rel="canonical" href="{esc(canonical)}">\n{hreflang_links(alternate_en, alternate_zh)}'
    language_url = (alternate_zh if locale == "en" else alternate_en) if canonical else TEXT[t["other"]]["home_path"]
    og_url = canonical or BASE_URL + t["home_path"]
    if canonical:
        csp = (
            "default-src 'self'; script-src 'self' 'unsafe-inline' https://*.googletagmanager.com; "
            "style-src 'self'; img-src 'self' data: https://*.google-analytics.com "
            "https://*.googletagmanager.com; connect-src "
            f"{GA4_CONNECT_SOURCES}; object-src 'none'; base-uri 'none'; form-action 'none'"
        )
        analytics = ga4_tag()
    else:
        csp = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self'; "
            "img-src 'self' data:; object-src 'none'; base-uri 'none'; form-action 'none'"
        )
        analytics = ""
    return f"""<!doctype html>
<html lang="{t['html_lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}">
{analytics}
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="{esc(robots)}">
{search_links}
<link rel="icon" type="image/png" sizes="512x512" href="/favicon.png">
<link rel="stylesheet" href="/seo.css">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Trending Scope">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(og_url)}">
<meta property="og:image" content="{image}">
<meta property="og:locale" content="{t['locale']}">
<meta property="og:locale:alternate" content="{t['alternate_locale']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{image}">
{json_ld(structured_data)}
</head>
<body>
<header class="topbar"><a class="brand" href="{t['home_path']}">⌥ <span>Trending Scope</span></a><span class="tagline">{t['site_tag']}</span><nav><a href="{t['directory_path']}">{t['directory']}</a><a hreflang="{TEXT[t['other']]['html_lang']}" href="{language_url}">{t['switch']}</a></nav></header>
{body}
</body>
</html>
"""


def breadcrumb_schema(locale: str, canonical: str, name: str) -> dict:
    t = TEXT[locale]
    return {
        "@type": "BreadcrumbList",
        "@id": canonical + "#breadcrumb",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": t["home"], "item": BASE_URL + t["home_path"]},
            {"@type": "ListItem", "position": 2, "name": t["directory"], "item": BASE_URL + t["directory_path"]},
            {"@type": "ListItem", "position": 3, "name": name, "item": canonical},
        ],
    }


def detail_page(data: dict, repo: dict, locale: str, indexed_repos: list[dict], indexable: bool) -> str:
    t = TEXT[locale]
    localized = repo[locale]
    en_url, zh_url = pair_for_repo(repo["full"])
    canonical = en_url if locale == "en" else zh_url
    title = truncate(f"{repo['full']} — {t['page_suffix']}", 68)
    description = truncate(localized["what"], 158)
    placements = placements_for(data, repo["full"], locale)
    category = data["cats"].get(repo.get("cat"), {}).get(locale, repo.get("cat", ""))
    related = [row for row in indexed_repos if row["full"] != repo["full"] and row.get("cat") == repo.get("cat")]
    related.sort(key=lambda row: row["full"].lower())
    related = related[:6]
    placement_rows = "".join(
        f"<tr><td>{esc(row['period'])}</td><td>{esc(row['filter'])}</td><td>#{esc(row['rank'])}</td><td>{esc(row['gain'])}</td></tr>"
        for row in placements
    )
    use_items = "".join(f"<li>{esc(item)}</li>" for item in localized["uses"])
    related_items = "".join(
        f'<li><a href="{repo_path(row["full"], locale)}">{esc(row["full"])}</a><span>{esc(row[locale]["tag"])}</span></li>'
        for row in related
    )
    track = repo.get("track") or {}
    stars_label = t["stars"] if placements else t["last_observed_stars"]
    if not placement_rows:
        placement_rows = f'<tr><td colspan="4">{t["not_current"]}</td></tr>'
    body = f"""
<main class="page-wrap">
  <nav class="breadcrumbs" aria-label="Breadcrumb"><a href="{t['home_path']}">{t['home']}</a><span>›</span><a href="{t['directory_path']}">{t['directory']}</a><span>›</span><span aria-current="page">{esc(repo['full'])}</span></nav>
  <article class="analysis">
    <p class="eyebrow">GitHub Trending · {esc(category)} · {t['updated']} <time datetime="{esc(data['meta']['date'])}">{esc(data['meta']['date'])}</time></p>
    <h1>{esc(repo['full'])}</h1>
    <p class="lead">{esc(localized['tag'])}</p>
    <dl class="metrics">
      <div><dt>{stars_label}</dt><dd>★ {esc(repo.get('stars', '—'))}k</dd></div>
      <div><dt>{t['language']}</dt><dd>{esc(repo.get('lang') or '—')}</dd></div>
      <div><dt>{t['appearances']}</dt><dd>{len(placements)}</dd></div>
      <div><dt>{t['tracking']}</dt><dd>{esc(track.get('days', 0))} {t['days']}</dd></div>
    </dl>
    <section><h2>{t['what']}</h2><p>{esc(localized['what'])}</p></section>
    <section><h2>{t['content']}</h2><p>{esc(localized['content'])}</p></section>
    <section><h2>{t['stack']}</h2><p>{esc(localized['stack'])}</p></section>
    <section><h2>{t['uses']}</h2><ul>{use_items}</ul></section>
    <section><h2>{t['hot']}</h2><p>{esc(localized['hot'])}</p></section>
    <section><h2>{t['placements']}</h2><div class="table-scroll"><table><thead><tr><th>{t['period']}</th><th>{t['filter']}</th><th>{t['rank']}</th><th>{t['gain']}</th></tr></thead><tbody>{placement_rows}</tbody></table></div></section>
    <p class="source-note">{t['source_note']}</p>
    <p><a class="primary-link" href="https://github.com/{esc(repo['full'])}" rel="noopener noreferrer">{t['github']} ↗</a></p>
  </article>
  <aside class="related"><h2>{t['related']}</h2><ul>{related_items}</ul></aside>
</main>
<footer class="site-footer">Trending Scope · {t['updated']} {esc(data['meta']['date'])} · <a href="{t['directory_path']}">{t['directory']}</a></footer>
"""
    software = {
        "@type": "SoftwareSourceCode",
        "@id": canonical + "#software",
        "name": repo["full"],
        "description": compact(localized["what"]),
        "codeRepository": f"https://github.com/{repo['full']}",
        "url": f"https://github.com/{repo['full']}",
    }
    if repo.get("lang"):
        software["programmingLanguage"] = repo["lang"]
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": title,
                "description": description,
                "dateModified": data["meta"]["date"],
                "inLanguage": t["html_lang"],
                "isPartOf": {"@id": BASE_URL + "/#website"},
                "mainEntity": {"@id": canonical + "#software"},
                "breadcrumb": {"@id": canonical + "#breadcrumb"},
            },
            software,
            breadcrumb_schema(locale, canonical, repo["full"]),
        ],
    }
    return page_shell(
        locale=locale,
        title=title,
        description=description,
        canonical=canonical,
        alternate_en=en_url,
        alternate_zh=zh_url,
        body=body,
        structured_data=structured,
        robots=(
            "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"
            if indexable
            else "noindex,follow"
        ),
    )


def directory_page(data: dict, locale: str, indexed_repos: list[dict]) -> str:
    t = TEXT[locale]
    canonical = BASE_URL + t["directory_path"]
    en_url = BASE_URL + TEXT["en"]["directory_path"]
    zh_url = BASE_URL + TEXT["zh"]["directory_path"]
    groups: dict[str, list[dict]] = defaultdict(list)
    for repo in sorted(indexed_repos, key=lambda row: row["full"].lower()):
        groups[repo.get("cat", "other")].append(repo)
    group_html = []
    for category_id, category in data["cats"].items():
        rows = groups.get(category_id, [])
        cards = "".join(
            f"""<article class="directory-card"><h3><a href="{repo_path(repo['full'], locale)}">{esc(repo['full'])}</a></h3><p>{esc(repo[locale]['tag'])}</p><div>{esc(repo.get('lang') or '—')} · ★ {esc(repo.get('stars', '—'))}k</div></article>"""
            for repo in rows
        )
        group_html.append(
            f'<section class="directory-group"><h2>{esc(category[locale])} <span>{len(rows)}</span></h2>'
            f'<div class="directory-grid">{cards}</div></section>'
        )
    board_count = len(BOARD_ORDER) * len(data["langs"])
    body = f"""
<main class="page-wrap directory-page">
  <nav class="breadcrumbs" aria-label="Breadcrumb"><a href="{t['home_path']}">{t['home']}</a><span>›</span><span aria-current="page">{t['directory']}</span></nav>
  <header class="directory-hero"><p class="eyebrow">GitHub Trending · {t['updated']} <time datetime="{esc(data['meta']['date'])}">{esc(data['meta']['date'])}</time></p><h1>{t['directory']}</h1><p>{t['directory_intro']}</p><div class="directory-stats"><strong>{len(indexed_repos)}</strong> {t['repos']} · <strong>{board_count}</strong> {t['boards']}</div></header>
  {''.join(group_html)}
</main>
<footer class="site-footer">Trending Scope · {t['updated']} {esc(data['meta']['date'])}</footer>
"""
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": t["directory_title"],
                "description": t["directory_description"],
                "dateModified": data["meta"]["date"],
                "inLanguage": t["html_lang"],
                "isPartOf": {"@id": BASE_URL + "/#website"},
                "breadcrumb": {"@id": canonical + "#breadcrumb"},
            },
            {
                "@type": "BreadcrumbList",
                "@id": canonical + "#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": t["home"], "item": BASE_URL + t["home_path"]},
                    {"@type": "ListItem", "position": 2, "name": t["directory"], "item": canonical},
                ],
            },
        ],
    }
    return page_shell(
        locale=locale,
        title=t["directory_title"],
        description=t["directory_description"],
        canonical=canonical,
        alternate_en=en_url,
        alternate_zh=zh_url,
        body=body,
        structured_data=structured,
    )


def board_page(data: dict, board: str, language_id: str, locale: str, indexed_names: set[str]) -> str:
    t = TEXT[locale]
    rows = data["boards"][board][language_id]
    registry = {repo["full"]: repo for repo in data["repos"]}
    language = language_name(data, language_id, locale)
    period = t[board]
    en_url, zh_url = board_pair(board, language_id)
    canonical = en_url if locale == "en" else zh_url
    if locale == "en":
        title = truncate(f"GitHub Trending {language} {period} — {len(rows)} Repos | Trending Scope", 68)
        description = truncate(
            f"Explore the {period.lower()} GitHub Trending {language} chart for {data['meta']['date']}: "
            f"{len(rows)} repositories with ranks, star gains, and concise project explanations.",
            158,
        )
        intro = (
            f"A server-rendered snapshot of the {period.lower()} {language} chart, captured logged out "
            f"from github.com/trending on {data['meta']['date']}."
        )
    else:
        title = truncate(f"GitHub Trending {language}{period}榜：{len(rows)} 个热门仓库 | Trending Scope", 68)
        description = truncate(
            f"查看 {data['meta']['date']} 的 GitHub Trending {language}{period}榜：{len(rows)} 个仓库的排名、"
            "新增 Star 和项目简介，服务端直接输出，无需 JavaScript。",
            158,
        )
        intro = f"这是 {data['meta']['date']} 未登录状态下抓取的 GitHub Trending {language}{period}榜服务端快照。"
    nav_links = []
    for candidate in data["langs"]:
        candidate_id = candidate["id"]
        nav_links.append(
            f'<a href="{board_path(board, candidate_id, locale)}">{esc(language_name(data, candidate_id, locale))}</a>'
        )
    for candidate_board in BOARD_ORDER:
        nav_links.append(
            f'<a href="{board_path(candidate_board, language_id, locale)}">{esc(t[candidate_board])}</a>'
        )
    list_rows = []
    item_list = []
    for row in rows:
        repo = registry[row["full"]]
        is_indexed = repo["full"] in indexed_names
        href = repo_path(repo["full"], locale) if is_indexed else f"https://github.com/{repo['full']}"
        rel = "" if is_indexed else ' rel="noopener noreferrer"'
        category = data["cats"].get(row.get("cat") or repo.get("cat"), {}).get(locale, "")
        list_rows.append(
            f"""<article class="board-row"><div class="board-rank">#{esc(row['rank'])}</div><div class="board-main"><h2><a href="{esc(href)}"{rel}>{esc(repo['full'])}</a></h2><p>{esc(repo[locale]['tag'])}</p></div><div class="board-meta">★ {esc(row.get('stars', '—'))}k<br>{esc(row.get('today', '—'))} · {esc(category)}</div></article>"""
        )
        item_list.append(
            {
                "@type": "ListItem",
                "position": row["rank"],
                "name": repo["full"],
                "url": BASE_URL + href if href.startswith("/") else href,
            }
        )
    body = f"""
<main class="page-wrap board-page">
  <nav class="breadcrumbs" aria-label="Breadcrumb"><a href="{t['home_path']}">{t['home']}</a><span>›</span><span aria-current="page">{esc(period)} · {esc(language)}</span></nav>
  <header class="board-hero"><p class="eyebrow">GitHub Trending · {t['updated']} <time datetime="{esc(data['meta']['date'])}">{esc(data['meta']['date'])}</time></p><h1>GitHub Trending · {esc(period)} · {esc(language)}</h1><p>{esc(intro)}</p><nav class="board-nav" aria-label="Chart views">{''.join(nav_links)}</nav></header>
  <section class="board-list" aria-label="{esc(title)}">{''.join(list_rows)}</section>
</main>
<footer class="site-footer">Trending Scope · {t['updated']} {esc(data['meta']['date'])} · <a href="{t['directory_path']}">{t['directory']}</a></footer>
"""
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": title,
                "description": description,
                "dateModified": data["meta"]["date"],
                "inLanguage": t["html_lang"],
                "isPartOf": {"@id": BASE_URL + "/#website"},
                "mainEntity": {"@id": canonical + "#itemlist"},
                "breadcrumb": {"@id": canonical + "#breadcrumb"},
            },
            {"@type": "ItemList", "@id": canonical + "#itemlist", "numberOfItems": len(rows), "itemListElement": item_list},
            {
                "@type": "BreadcrumbList",
                "@id": canonical + "#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": t["home"], "item": BASE_URL + t["home_path"]},
                    {"@type": "ListItem", "position": 2, "name": f"{period} · {language}", "item": canonical},
                ],
            },
        ],
    }
    return page_shell(
        locale=locale,
        title=title,
        description=description,
        canonical=canonical,
        alternate_en=en_url,
        alternate_zh=zh_url,
        body=body,
        structured_data=structured,
    )


def prerender_landing(source: str, data: dict, locale: str, indexed_names: set[str]) -> str:
    source = prepare_landing_analytics(source)
    source_switch, production_switch = {
        "en": (
            '<a href="index-zh.html" class="lang">中文</a>',
            '<a href="/index-zh" class="lang">中文</a>',
        ),
        "zh": (
            '<a href="index.html" class="lang">EN</a>',
            '<a href="/" class="lang">EN</a>',
        ),
    }[locale]
    if source.count(source_switch) != 1:
        raise ValueError(f"Expected exactly one {locale} locale switch")
    source = source.replace(source_switch, production_switch, 1)
    source = source.replace(
        "const SEO_INDEXED = new Set([]);",
        "const SEO_INDEXED = new Set(" + json.dumps(sorted(indexed_names), ensure_ascii=False) + ");",
        1,
    )
    rows = data["boards"]["daily"]["all"]
    registry = {repo["full"]: repo for repo in data["repos"]}
    cards = []
    item_list = []
    for row in rows:
        repo = registry[row["full"]]
        is_indexed = repo["full"] in indexed_names
        href = repo_path(repo["full"], locale) if is_indexed else f"https://github.com/{repo['full']}"
        cards.append(
            f"""<article class="card show" data-slug="{esc(repo['slug'].lower())}"><a class="openhit" href="{esc(href)}" data-open="{esc(repo['slug'].lower())}" aria-label="{esc(repo['full'])}"><span class="sr-only">{esc(repo['full'])}</span></a><div class="body"><h4><span class="rank">#{esc(row['rank'])}</span> {esc(repo['full'])} <span class="arrow">→</span></h4><p class="tag">{esc(repo[locale]['tag'])}</p><div class="meta"><span>{esc(repo.get('lang') or '—')}</span><span class="stars">★ {esc(row.get('stars', '—'))}k</span><span class="today">{esc(row.get('today', '—'))}</span></div></div></article>"""
        )
        item_list.append(
            {
                "@type": "ListItem",
                "position": row["rank"],
                "name": repo["full"],
                "url": BASE_URL + href if href.startswith("/") else href,
            }
        )
    source = source.replace('<main class="grid" id="grid"></main>', f'<main class="grid" id="grid">{"".join(cards)}</main>')
    t = TEXT[locale]
    canonical = BASE_URL + t["home_path"]
    page_type = "WebSite" if locale == "en" else "WebPage"
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": page_type,
                "@id": canonical + "#website",
                "url": canonical,
                "name": "Trending Scope",
                "description": compact(data["meta"].get(f"sub_{locale}", "")),
                "dateModified": data["meta"]["date"],
                "inLanguage": t["html_lang"],
            },
            {"@type": "ItemList", "@id": canonical + "#itemlist", "numberOfItems": len(rows), "itemListElement": item_list},
        ],
    }
    source = source.replace("</head>", json_ld(structured) + "\n</head>", 1)
    board_links = []
    for board in BOARD_ORDER:
        for lang in data["langs"]:
            board_links.append(
                f'<a href="{board_path(board, lang["id"], locale)}">{esc(t[board])} · {esc(language_name(data, lang["id"], locale))}</a>'
            )
    label = "Chart views" if locale == "en" else "榜单视图"
    nav = f'<nav class="seo-board-links" aria-label="{label}"><strong>{label}</strong>{"".join(board_links)}</nav>'
    source = source.replace("</footer>", nav + "\n</footer>", 1)
    return source


def not_found_page() -> str:
    t = TEXT["en"]
    body = f"""<main class="not-found"><p class="error-code">404</p><h1>{t['not_found']}</h1><p>{t['not_found_text']}</p><p>页面不存在。请返回今日榜单或仓库解析目录。</p><div><a class="primary-link" href="/">{t['back_home']}</a><a href="/repos/">{t['directory']}</a><a href="/index-zh">中文</a></div></main>"""
    return page_shell(
        locale="en",
        title="404 — Page not found | Trending Scope",
        description=t["not_found_text"],
        canonical=None,
        alternate_en=BASE_URL + "/",
        alternate_zh=BASE_URL + "/index-zh",
        body=body,
        structured_data={"@context": "https://schema.org", "@type": "WebPage", "name": t["not_found"]},
        robots="noindex,follow",
    )


def sitemap_xml(data: dict, indexed_repos: list[dict]) -> tuple[str, list[str]]:
    pairs = []
    for board in BOARD_ORDER:
        for language in data["langs"]:
            pairs.append((*board_pair(board, language["id"]), data["meta"]["date"]))
    pairs.append((BASE_URL + "/repos/", BASE_URL + "/zh/repos/", data["meta"]["date"]))
    for repo in sorted(indexed_repos, key=lambda row: row["full"].lower()):
        history = (repo.get("track") or {}).get("hist") or []
        lastmod = history[-1].get("d") if history else data["meta"]["date"]
        pairs.append((*pair_for_repo(repo["full"]), lastmod))
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    urls = []
    for en_url, zh_url, lastmod in pairs:
        for loc, locale in ((en_url, "en"), (zh_url, "zh-CN")):
            urls.append(loc)
            lines.extend(
                [
                    "  <url>",
                    f"    <loc>{esc(loc)}</loc>",
                    f"    <lastmod>{esc(lastmod)}</lastmod>",
                    f'    <xhtml:link rel="alternate" hreflang="en" href="{esc(en_url)}"/>',
                    f'    <xhtml:link rel="alternate" hreflang="zh-CN" href="{esc(zh_url)}"/>',
                    f'    <xhtml:link rel="alternate" hreflang="x-default" href="{esc(en_url)}"/>',
                    "  </url>",
                ]
            )
    lines.append("</urlset>")
    return "\n".join(lines) + "\n", urls


def output_file_for_url(output: Path, url: str) -> Path:
    path = urlsplit(url).path
    if path == "/":
        return output / "index.html"
    if path == "/index-zh":
        return output / "index-zh.html"
    if path.endswith("/"):
        return output / path.lstrip("/") / "index.html"
    return output / path.lstrip("/")


def validate_output(output: Path, expected_urls: list[str]) -> dict:
    required = ("robots.txt", "sitemap.xml", "404.html", "_redirects", "_headers", "index.html", "index-zh.html")
    missing = [name for name in required if not (output / name).is_file()]
    if missing:
        raise ValueError(f"Missing production files: {missing}")
    tree = ElementTree.parse(output / "sitemap.xml")
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    actual_urls = [node.text for node in tree.findall("sm:url/sm:loc", namespace)]
    if actual_urls != expected_urls or len(actual_urls) != len(set(actual_urls)):
        raise ValueError("Sitemap URLs are missing, duplicated, or out of order")
    titles: set[str] = set()
    descriptions: set[str] = set()
    for url in actual_urls:
        path = output_file_for_url(output, url)
        if not path.is_file():
            raise ValueError(f"Sitemap URL has no output file: {url}")
        source = path.read_text(encoding="utf-8")
        canonical = re.search(r'<link rel="canonical" href="([^"]+)">', source)
        if not canonical or canonical.group(1) != url:
            raise ValueError(f"Canonical mismatch for {url}")
        if "noindex" in source.lower():
            raise ValueError(f"Indexable page contains noindex: {url}")
        title = re.search(r"<title>(.*?)</title>", source, re.S)
        description = re.search(r'<meta name="description" content="([^"]+)">', source)
        if not title or not description:
            raise ValueError(f"Missing title or description: {url}")
        title_text = html.unescape(title.group(1))
        description_text = html.unescape(description.group(1))
        if title_text in titles or description_text in descriptions:
            raise ValueError(f"Duplicate title or description: {url}")
        titles.add(title_text)
        descriptions.add(description_text)
        for marker in ('rel="alternate" hreflang="en"', 'rel="alternate" hreflang="zh-CN"', 'application/ld+json'):
            if marker not in source:
                raise ValueError(f"Missing {marker} on {url}")
    if f"Sitemap: {BASE_URL}/sitemap.xml" not in (output / "robots.txt").read_text(encoding="utf-8"):
        raise ValueError("robots.txt does not advertise the sitemap")
    html_paths = sorted(output.rglob("*.html"))
    untracked = {output / "404.html", output / "index-en.html"}
    for path in html_paths:
        source = path.read_text(encoding="utf-8")
        if path in untracked:
            if GA4_MEASUREMENT_ID in source or "googletagmanager.com/gtag/js" in source:
                raise ValueError(f"Excluded page unexpectedly contains GA4: {path.relative_to(output)}")
            continue
        if source.count(GA4_SCRIPT_URL) != 1:
            raise ValueError(f"GA4 loader must appear once: {path.relative_to(output)}")
        if source.count(f"gtag('config', '{GA4_MEASUREMENT_ID}'") != 1:
            raise ValueError(f"GA4 config must appear once: {path.relative_to(output)}")
        if source.count(GA4_MEASUREMENT_ID) != 2:
            raise ValueError(f"GA4 measurement ID count is invalid: {path.relative_to(output)}")
        directives = csp_directives(source)
        for directive, required_sources in GA4_CSP_REQUIREMENTS:
            missing_sources = required_sources - directives.get(directive, set())
            if missing_sources:
                raise ValueError(
                    f"GA4 CSP {directive} is missing {sorted(missing_sources)}: {path.relative_to(output)}"
                )
        if "'allow_google_signals': false" not in source or "'allow_ad_personalization_signals': false" not in source:
            raise ValueError(f"GA4 privacy controls are missing: {path.relative_to(output)}")
    return {"urls": len(actual_urls), "html_pages": len(html_paths), "titles": len(titles)}


def build(output: Path) -> dict:
    output = output.resolve()
    if output == ROOT.resolve() or output in ROOT.resolve().parents:
        raise ValueError(f"Refusing unsafe output path: {output}")
    data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
    validate_data(data)
    manifest = json.loads((ROOT / "seo-index.json").read_text(encoding="utf-8"))
    indexed_names = set(manifest.get("repos", []))
    registry = {repo["full"]: repo for repo in data["repos"]}
    missing_indexed = sorted(indexed_names - registry.keys())
    if missing_indexed:
        raise ValueError(f"SEO index references repositories missing from data.json: {missing_indexed}")
    indexed_repos = [registry[name] for name in manifest["repos"]]
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for name in COPY_FILES:
        if name in ("index.html", "index-zh.html"):
            locale = "zh" if name == "index-zh.html" else "en"
            source = (ROOT / name).read_text(encoding="utf-8")
            (output / name).write_text(prerender_landing(source, data, locale, indexed_names), encoding="utf-8")
        else:
            shutil.copy2(ROOT / name, output / name)
    for directory in ("archive", "videos"):
        if (ROOT / directory).is_dir():
            shutil.copytree(ROOT / directory, output / directory)
    (output / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8"
    )
    (output / "404.html").write_text(not_found_page(), encoding="utf-8")
    (output / "_redirects").write_text(
        "/index.html / 301\n/index-en / 301\n/index-en.html / 301\n/index-zh.html /index-zh 301\n",
        encoding="utf-8",
    )
    (output / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n\n"
        "/archive/*\n  X-Robots-Tag: noindex, nofollow\n\n"
        "/data.json\n  X-Robots-Tag: noindex, nofollow\n\n"
        "/videos/*\n  X-Robots-Tag: noindex, nofollow\n",
        encoding="utf-8",
    )
    for locale in ("en", "zh"):
        directory = output / TEXT[locale]["directory_path"].strip("/")
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.html").write_text(directory_page(data, locale, indexed_repos), encoding="utf-8")
        for repo in data["repos"]:
            target = output / repo_path(repo["full"], locale).strip("/")
            target.mkdir(parents=True, exist_ok=True)
            (target / "index.html").write_text(
                detail_page(data, repo, locale, indexed_repos, repo["full"] in indexed_names), encoding="utf-8"
            )
        for board in BOARD_ORDER:
            for language in data["langs"]:
                language_id = language["id"]
                if board == "daily" and language_id == "all":
                    continue
                target = output / board_path(board, language_id, locale).strip("/")
                target.mkdir(parents=True, exist_ok=True)
                (target / "index.html").write_text(
                    board_page(data, board, language_id, locale, indexed_names), encoding="utf-8"
                )
    sitemap, urls = sitemap_xml(data, indexed_repos)
    (output / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    return validate_output(output, urls)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
