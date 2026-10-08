"""Starry-sky pages for Trending Scope: logo, home page and daily Top-10 video helpers.

Everything here is pure string building so the daily build stays dependency-free.
`build_site.py` passes its own helpers in through ``Ctx`` to avoid a circular import.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import date as _date
from typing import Callable

BRAND = "cosolutions-Affiliate"
PRODUCT = {"en": "Trending Scope", "zh": "星榜 Trending Scope"}
RANK_ZH = "一二三四五六七八九十"
GREEK = "αβγδεζηθικ"
# Ten star positions in the 640x640 chart, and the lines between them (same shape as the approved style board).
STARS = [(330, 120), (440, 190), (400, 300), (500, 360), (330, 380), (210, 330), (120, 250), (210, 170), (300, 250), (170, 420)]
LINES = [(0, 1), (1, 2), (2, 3), (2, 4), (4, 5), (5, 6), (6, 7), (7, 0), (7, 8), (8, 2), (5, 9), (4, 9)]
MANSIONS = "角亢氐房心尾箕斗牛女虚危室壁奎娄胃昴毕觜参井鬼柳星张翼轸"

HOME = {
    "en": {
        "title": "GitHub Trending Today: Top 10 Repos Explained in Video | cosolutions-Affiliate",
        "description": "The ten hottest open-source projects on GitHub today, explained one by one in plain English: a countdown video, a short video and a write-up for each repo, updated daily.",
        "kicker": "TONIGHT’S SKY",
        "h1": "Ten stars.<br><em>Ten stories.</em>",
        "lead": "The ten hottest open-source projects on GitHub today, <b>explained one by one</b>. No code. Just what each of them is actually good for.",
        "watch": "Watch tonight’s ten",
        "all": "All trending",
        "nav": [("#tonight", "Tonight"), ("#stories", "Ten stories"), ("#more", "All repos")],
        "tonight": "Tonight’s countdown",
        "tonight_sub": "Number ten to number one, one practical scenario each.",
        "stories": "Ten stories",
        "stories_sub": "Each has its own short video and write-up.",
        "more": "Beyond the top ten",
        "more_sub": "The rest of today’s daily chart, and every other chart view.",
        "boards": "Chart views",
        "chapters": "Chapters",
        "chart_label": "Star chart of today’s ten trending repositories",
        "edition": "Edition",
        "no_video": "Tonight’s video isn’t ready yet.",
        "last_edition": "Latest edition",
        "credit": "MILKY WAY PANORAMA · ESO / S. BRUNIER · CC BY 4.0",
        "footer": "Data updated",
        "directory": "Repository analyses",
        "daily": "Daily",
        "weekly": "Weekly",
        "monthly": "Monthly",
        "alt_label": "中文",
        "ring": "DAILY SKY CHART · {date} · TEN BRIGHTEST · ",
        "star": "★",
        "video_name": "GitHub Trending Top 10 — {date}",
        "video_desc": "A countdown of the ten hottest GitHub repositories on {date}, with a practical scenario for each.",
        "play": "Play",
    },
    "zh": {
        "title": "GitHub 今日热榜 Top 10 视频解说：十个热门开源项目 | cosolutions-Affiliate",
        "description": "每天十个最热的 GitHub 开源项目，用大白话一个一个讲清楚：倒数长视频、每个项目一条短视频和图文解析，每日更新。",
        "kicker": "今夜星象",
        "h1": "十星当空<br><em>今日 GitHub 热榜</em>",
        "lead": "每天十个最热的开源项目，<b>一个一个讲清楚</b>。不念代码，用大白话，说说它们到底能拿来干什么。",
        "watch": "观看今夜十星",
        "all": "全部热榜",
        "nav": [("#tonight", "今夜星象"), ("#stories", "十星故事"), ("#more", "全部热榜")],
        "tonight": "今夜十星倒数",
        "tonight_sub": "从第十名倒数到第一名，每个项目讲一个实用场景。",
        "stories": "十星故事",
        "stories_sub": "每个项目都有自己的短视频和图文解析。",
        "more": "十名之后",
        "more_sub": "今日日榜的其余项目，以及所有榜单视图。",
        "boards": "榜单视图",
        "chapters": "章节",
        "chart_label": "今日 GitHub 热榜前十名星图",
        "edition": "期数",
        "no_video": "今夜的视频还没有做好。",
        "last_edition": "最近一期",
        "credit": "银河全景 · ESO / S. BRUNIER · CC BY 4.0",
        "footer": "数据更新于",
        "directory": "仓库解析",
        "daily": "每日",
        "weekly": "每周",
        "monthly": "每月",
        "alt_label": "English",
        "ring": "",
        "star": "★",
        "video_name": "GitHub 热榜 Top 10 · {date}",
        "video_desc": "{date} GitHub 最热的十个开源仓库倒数解说，每个项目讲一个实用场景。",
        "play": "播放",
    },
}


@dataclass
class Ctx:
    """Helpers owned by build_site.py, injected to avoid a circular import."""

    esc: Callable[[object], str]
    repo_path: Callable[[str, str], str]
    board_path: Callable[[str, str, str], str]
    language_name: Callable[[dict, str, str], str]
    json_ld: Callable[[object], str]
    compact: Callable[[object], str]
    base_url: str


def logo_svg(size: int = 30) -> str:
    """A ring with a small star on it: 'co-' orbit. Hairlines only, no glow."""
    return (
        f'<svg class="mark" width="{size}" height="{size}" viewBox="0 0 32 32" aria-hidden="true" focusable="false">'
        '<circle cx="16" cy="16" r="13.5" fill="none" stroke="currentColor" stroke-opacity=".85" stroke-width="1.2"/>'
        '<circle cx="16" cy="16" r="7" fill="none" stroke="currentColor" stroke-opacity=".4" stroke-width="1" stroke-dasharray="1.5 3"/>'
        '<path d="M16 8.2l1.6 5 5.2.1-4.2 3.1 1.6 5-4.2-3.1-4.2 3.1 1.6-5-4.2-3.1 5.2-.1z" fill="currentColor"/></svg>'
    )


def brand_link(locale: str, href: str) -> str:
    return f'<a class="brand" href="{href}" aria-label="{BRAND} · Trending Scope">{logo_svg()}<span>{BRAND}</span><small>Trending Scope</small></a>'


def fmt_date(iso: str, locale: str) -> str:
    d = _date.fromisoformat(iso)
    if locale == "zh":
        return f"{d.year}年{d.month}月{d.day}日"
    return d.strftime("%d %b %Y").upper()


def iso_duration(seconds: float) -> str:
    s = int(round(seconds))
    return f"PT{s // 60}M{s % 60}S"


def mmss(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 60}:{s % 60:02d}"


# ---------------------------------------------------------------- videos manifest
def latest_edition(videos: dict | None) -> dict | None:
    eds = (videos or {}).get("editions") or []
    return max(eds, key=lambda e: e["date"]) if eds else None


def repo_video(videos: dict | None, full: str) -> tuple[dict, dict] | None:
    """Newest edition that contains a short video for `full` -> (edition, repo entry)."""
    for ed in sorted((videos or {}).get("editions") or [], key=lambda e: e["date"], reverse=True):
        if full in (ed.get("repos") or {}):
            return ed, ed["repos"][full]
    return None


def video_urls(videos: dict, entry: dict, base: str) -> dict:
    return {
        "video": f"{base}/{entry['video']}",
        "vtt": f"{base}/{entry['vtt']}" if entry.get("vtt") else "",
        "poster": "/" + entry["poster"],
    }


def player_html(c: Ctx, videos: dict, entry: dict, locale: str, base: str, vid: str, label: str, caption: str = "") -> str:
    u = video_urls(videos, entry, base)
    track = f'<track kind="subtitles" srclang="{"zh-CN" if locale == "zh" else "en"}" label="{"中文" if locale == "zh" else "English"}" src="{c.esc(u["vtt"])}" default>' if u["vtt"] else ""
    cap = f"<figcaption>{c.esc(caption)}</figcaption>" if caption else ""
    return (
        f'<figure class="vid"><video id="{vid}" controls preload="none" playsinline crossorigin="anonymous" poster="{c.esc(u["poster"])}" aria-label="{c.esc(label)}">'
        f'<source src="{c.esc(u["video"])}" type="video/mp4">{track}</video>{cap}</figure>'
    )


def video_object(c: Ctx, entry: dict, base: str, name: str, desc: str, upload: str, locale: str, page_url: str) -> dict:
    return {
        "@type": "VideoObject",
        "name": name,
        "description": desc,
        "thumbnailUrl": c.base_url + "/" + entry["poster"],
        "uploadDate": upload,
        "duration": iso_duration(entry["duration"]),
        "contentUrl": f"{base}/{entry['video']}",
        "inLanguage": "zh-CN" if locale == "zh" else "en",
        "isFamilyFriendly": True,
        "mainEntityOfPage": page_url,
    }


# ---------------------------------------------------------------- star chart
def star_chart(c: Ctx, locale: str, rows: list[dict], hrefs: list[str], iso: str) -> str:
    t = HOME[locale]
    zh = locale == "zh"
    parts = ['<g class="spin">']
    parts.append('<circle cx="320" cy="320" r="300" fill="none" stroke="#f1ece0" stroke-opacity=".45"/>')
    parts.append('<circle cx="320" cy="320" r="272" fill="none" stroke="#f1ece0" stroke-opacity=".3"/>')
    parts.append('<circle cx="320" cy="320" r="150" fill="none" stroke="#f1ece0" stroke-opacity=".16" stroke-dasharray="2 8"/>')
    import math

    for i in range(0, 360, 5):
        a = math.radians(i)
        r1 = 266 if i % 15 else 258
        parts.append(
            f'<line x1="{320 + math.cos(a) * r1:.1f}" y1="{320 + math.sin(a) * r1:.1f}" x2="{320 + math.cos(a) * 272:.1f}" y2="{320 + math.sin(a) * 272:.1f}" stroke="#f1ece0" stroke-opacity=".4"/>'
        )
    if zh:
        for i, ch in enumerate(MANSIONS):
            a = i / 28 * 2 * math.pi - math.pi / 2
            x, y = 320 + math.cos(a) * 286, 320 + math.sin(a) * 286
            parts.append(
                f'<text x="{x:.1f}" y="{y:.1f}" fill="#d4b472" fill-opacity=".85" font-family="Kaiti SC,STKaiti,KaiTi,serif" font-size="16" text-anchor="middle" dominant-baseline="middle" transform="rotate({i / 28 * 360:.1f} {x:.1f} {y:.1f})">{ch}</text>'
            )
    else:
        ring = (t["ring"].format(date=iso)) * 2
        parts.append('<defs><path id="rp" d="M320 320 m-287 0 a287 287 0 1 1 574 0 a287 287 0 1 1 -574 0"/></defs>')
        parts.append(f'<text fill="#e9b872" fill-opacity=".8" font-family="SF Mono,Menlo,monospace" font-size="12" letter-spacing="7"><textPath href="#rp">{html.escape(ring)}</textPath></text>')
    parts.append("</g>")
    parts.append('<line x1="20" y1="320" x2="620" y2="320" stroke="#f1ece0" stroke-opacity=".1"/><line x1="320" y1="20" x2="320" y2="620" stroke="#f1ece0" stroke-opacity=".1"/>')
    for a, b in LINES:
        parts.append(f'<line x1="{STARS[a][0]}" y1="{STARS[a][1]}" x2="{STARS[b][0]}" y2="{STARS[b][1]}" stroke="#f1ece0" stroke-opacity=".5"/>')
    for i, ((x, y), row) in enumerate(zip(STARS, rows)):
        r = 7 - i * 0.45
        glyph = RANK_ZH[i] if zh else GREEK[i]
        left = x > 380
        nx, anchor = (x - 14, "end") if left else (x + 14, "start")
        label = f"No. {row['rank']} {row['full']}"
        parts.append(
            f'<a href="{c.esc(hrefs[i])}" aria-label="{c.esc(label)}"><circle class="hit" cx="{x}" cy="{y}" r="22"/>'
            + (f'<circle cx="{x}" cy="{y}" r="19" fill="none" stroke="#d4b472" stroke-width="1.2"/>' if i == 0 else "")
            + f'<circle class="star" cx="{x}" cy="{y}" r="{r:.2f}"/>'
            + f'<text class="lbl" x="{nx}" y="{y - 10}" text-anchor="{anchor}" font-family="{"Kaiti SC,STKaiti,KaiTi,serif" if zh else "Didot,Georgia,serif"}" font-size="{18 if zh else 20}" font-style="{"normal" if zh else "italic"}">{glyph}</text>'
            + f'<text class="name" x="{nx}" y="{y + 16}" text-anchor="{anchor}">{c.esc(row["full"])}</text></a>'
        )
    return (
        f'<svg class="chart" viewBox="0 0 640 640" role="group" aria-label="{c.esc(t["chart_label"])}">' + "".join(parts) + "</svg>"
    )


# ---------------------------------------------------------------- home body
def home_body(c: Ctx, data: dict, locale: str, indexed: set[str], videos: dict | None, base: str, other_href: str) -> tuple[str, list[dict]]:
    """Returns (<body> markup without the sky/GA wrapper, extra JSON-LD nodes)."""
    t = HOME[locale]
    iso = data["meta"]["date"]
    registry = {r["full"]: r for r in data["repos"]}
    rows = data["boards"]["daily"]["all"]
    top, rest = rows[:10], rows[10:]
    ed = latest_edition(videos)
    fresh = bool(ed and ed["date"] == iso)
    nodes: list[dict] = []

    def card_href(full: str) -> str:
        return c.repo_path(full, locale)

    # --- hero
    hrefs = [card_href(r["full"]) for r in top]
    nav_links = "".join(f'<a href="{h}">{c.esc(n)}</a>' for h, n in t["nav"])
    nav = (
        f'<header class="nav">{brand_link(locale, "/" if locale == "en" else "/index-zh")}'
        f'<nav aria-label="Main">{nav_links}<a class="lang" hreflang="{"zh-CN" if locale == "en" else "en"}" href="{other_href}">{t["alt_label"]}</a></nav></header>'
    )
    hero = (
        f'<section class="hero" id="top"><div class="copy"><p class="kicker"><i></i>{fmt_date(iso, locale)} · {t["kicker"]}</p>'
        f'<h1>{t["h1"]}</h1><p class="lead">{t["lead"]}</p>'
        f'<div class="cta"><a class="btn solid" href="#tonight"><span class="tri"></span>{t["watch"]}</a><a class="btn line" href="#more">{t["all"]}</a></div></div>'
        f"{star_chart(c, locale, top, hrefs, iso)}</section>"
    )

    # --- long video
    if ed and (ed.get("top10") or {}).get(locale):
        e = ed["top10"][locale]
        name = t["video_name"].format(date=fmt_date(ed["date"], locale))
        cap = f'{t["edition"]} {fmt_date(ed["date"], locale)}' + ("" if fresh else f' · {t["last_edition"]}')
        chap = "".join(
            f'<li><button type="button" data-t="{ch["t"]:.2f}"><span class="n">{"NO. %02d" % ch["rank"] if ch.get("rank") else "—"}</span>'
            f'<span class="nm">{c.esc(ch["title"])}</span><span class="t">{mmss(ch["t"])}</span></button></li>'
            for ch in e.get("chapters", [])
        )
        player = (
            f'<div class="player">{player_html(c, videos, e, locale, base, "long-video", name, cap)}'
            f'<h3 class="sr-only">{t["chapters"]}</h3><ol class="chapters" id="chapters">{chap}</ol></div>'
        )
        nodes.append(video_object(c, e, base, name, t["video_desc"].format(date=fmt_date(ed["date"], locale)), ed["date"], locale, c.base_url + ("/" if locale == "en" else "/index-zh")))
    else:
        player = f'<div class="pending">{t["no_video"]}</div>'
    tonight = (
        f'<section class="sec wide" id="tonight"><div class="sec-head"><span class="no">NO. 10 → 01</span><h2>{t["tonight"]}</h2><p>{t["tonight_sub"]}</p></div>{player}</section>'
    )

    # --- ten cards
    cards = []
    for i, row in enumerate(top):
        repo = registry[row["full"]]
        loc = repo[locale]
        vid = repo_video(videos, row["full"]) if fresh else None
        still = ""
        dur = ""
        if vid and vid[1].get(locale):
            ve = vid[1][locale]
            still = f'<img src="/{c.esc(ve["poster"])}" alt="" loading="lazy" width="640" height="360"><span class="tri"></span>'
            dur = f'<span class="dur">{mmss(ve["duration"])}</span>'
        else:
            still = '<span class="tri"></span>' if False else ""
        cards.append(
            f'<li class="scard" id="r{row["rank"]}"><a class="hit" href="{c.esc(card_href(row["full"]))}">{c.esc(row["full"])}</a>'
            f'<div class="still"><span class="rk">NO. {row["rank"]:02d}</span>{still}{dur}</div>'
            f'<div class="info"><h3>{c.esc(row["full"])}</h3><p>{c.esc(loc["tag"])}</p>'
            f'<div class="meta"><span>{c.esc(repo.get("lang") or "—")}</span><span>{t["star"]} {c.esc(row.get("stars", "—"))}k</span><span>{c.esc(row.get("today", "—"))}</span></div></div></li>'
        )
    stories = f'<section class="sec" id="stories"><div class="sec-head"><span class="no">TOP 10</span><h2>{t["stories"]}</h2><p>{t["stories_sub"]}</p></div><ol class="cards">{"".join(cards)}</ol></section>'

    # --- ranks 11+ and chart views
    items = []
    for row in rest:
        repo = registry[row["full"]]
        href = card_href(row["full"]) if row["full"] in indexed else f'https://github.com/{row["full"]}'
        ext = "" if row["full"] in indexed else ' rel="noopener noreferrer"'
        items.append(
            f'<li><span class="r">#{row["rank"]}</span><div><a href="{c.esc(href)}"{ext}>{c.esc(row["full"])}</a><small>{c.esc(repo[locale]["tag"])}</small></div>'
            f'<span class="m">{c.esc(repo.get("lang") or "—")} · {t["star"]} {c.esc(row.get("stars", "—"))}k · {c.esc(row.get("today", "—"))}</span></li>'
        )
    chips = []
    for board in ("daily", "weekly", "monthly"):
        links = "".join(
            f'<a href="{c.board_path(board, lg["id"], locale)}">{t[board]} · {c.esc(c.language_name(data, lg["id"], locale))}</a>'
            for lg in data["langs"]
            if not (board == "daily" and lg["id"] == "all")
        )
        chips.append(links)
    more = (
        f'<section class="sec" id="more"><div class="sec-head"><span class="no">11+</span><h2>{t["more"]}</h2><p>{t["more_sub"]}</p></div>'
        f'<ol class="rows">{"".join(items)}</ol>'
        f'<nav class="chips" aria-label="{t["boards"]}"><b>{t["boards"]}</b>{"".join(chips)}<a href="{"/repos/" if locale == "en" else "/zh/repos/"}">{t["directory"]}</a></nav></section>'
    )
    footer = (
        f'<div class="credit">{t["credit"]}</div>'
        f'<footer class="site-footer">{BRAND} · Trending Scope · {t["footer"]} {c.esc(data["meta"]["generated_at"])}</footer>'
    )
    return nav + f'<main id="main">{hero}{tonight}{stories}{more}</main>' + footer, nodes
