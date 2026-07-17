#!/usr/bin/env python3
"""Trending Scope 每日更新管线

直连 github.com/trending 抓取当日榜单（Repositories · Today · All languages · 未登录口径），
刷新 data.json（双语数据源）与 data.js（页面运行时加载的包装）。

规则：
- 仍在榜的仓库：保留人工撰写的 zh/en 深度解析，仅更新排名 / stars / 今日新增 / 语言。
- 新上榜仓库：自动生成带 auto 标记的简摘要（取自 GitHub 描述），待人工补充精评。
- 解析结果少于 --min-repos 个（页面结构变更）时失败退出，绝不覆盖现有数据。

用法：
    python3 scripts/update.py [--dry-run] [--data PATH] [--min-repos 10]
环境：
    无需任何第三方依赖（Python 3.9+ 标准库）。
"""
import argparse
import glob
import html as html_mod
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

TRENDING_URL = "https://github.com/trending"
CN_TZ = timezone(timedelta(hours=8), "CST")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

CATS = {
    "agent": {"zh": "Agent 工具链", "en": "Agent Tooling", "color": "#cf4a1f"},
    "ai":    {"zh": "AI 应用与模型", "en": "AI Apps & Models", "color": "#0e6f63"},
    "infra": {"zh": "平台·数据·应用", "en": "Platforms, Data & Apps", "color": "#b07a1e"},
    "other": {"zh": "学习 & 游戏", "en": "Learning & Gaming", "color": "#5a7a3a"},
}

REQUIRED_REPO_KEYS = ("slug", "full", "rank", "cat", "lang", "stars", "today", "today_n", "auto", "track", "zh", "en")
REQUIRED_TEXT_KEYS = ("tag", "what", "content", "stack", "hot", "uses")
HIST_DAYS = 14  # sparkline 最多保留的历史点数


# ---------------------------------------------------------------- 抓取与解析

def fetch_html(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def _strip_tags(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", fragment)
    return re.sub(r"\s+", " ", html_mod.unescape(text)).strip()


def _to_int(s: str) -> int:
    return int(s.replace(",", "").strip())


def parse_trending(page: str) -> list:
    """解析 trending 页面，返回 [{full, desc, lang, stars_n, today_n}, ...]（按榜单顺序）。"""
    chunks = page.split('<article class="Box-row">')[1:]
    repos = []
    for ch in chunks:
        m = re.search(r"<h2[^>]*>.*?href=\"/([^\"]+)\"", ch, re.S)
        if not m:
            continue
        full = m.group(1).strip()
        if "/" not in full:
            continue
        desc_m = re.search(r'<p class="col-9[^"]*">(.*?)</p>', ch, re.S)
        desc = _strip_tags(desc_m.group(1)) if desc_m else ""
        lang_m = re.search(r'itemprop="programmingLanguage">\s*([^<]+)<', ch)
        lang = lang_m.group(1).strip() if lang_m else None
        stars_m = re.search(r"/stargazers\"[^>]*>(.*?)</a>", ch, re.S)
        stars_n = _to_int(_strip_tags(stars_m.group(1))) if stars_m else 0
        today_m = re.search(r"([\d,]+)\s*stars\s+today", ch)
        today_n = _to_int(today_m.group(1)) if today_m else 0
        repos.append({"full": full, "desc": desc, "lang": lang,
                      "stars_n": stars_n, "today_n": today_n})
    return repos


# ---------------------------------------------------------------- 格式化与分类

def fmt_stars_k(n: int) -> float:
    return round(n / 1000.0, 1)


def fmt_today(n: int) -> str:
    return f"+{n / 1000.0:.1f}k" if n >= 1000 else f"+{n}"


AGENT_KW = ("agent", "mcp", "claude", "codex", "copilot", "cursor", "skill", "openai codex", "agentic")
OTHER_KW = ("game", "cheat", "mod menu", "gta", "learn", "course", "tutorial", "curriculum",
            "interview", "roadmap", "book", "awesome", "self-taught", "education")
AI_KW = ("llm", "gpt", "model", "diffusion", "rag", "neural", "transformer", "inference",
         "machine learning", "deep learning", " ai", "ai ", "ml", "tokenizer", "embedding")


def classify(full: str, desc: str) -> str:
    text = (full + " " + desc).lower()
    if any(k in text for k in AGENT_KW):
        return "agent"
    if any(k in text for k in OTHER_KW):
        return "other"
    if any(k in text for k in AI_KW):
        return "ai"
    return "infra"


def make_slug(full: str, taken: set) -> str:
    owner, name = full.split("/", 1)
    slug = name.lower()
    if slug in taken:
        slug = re.sub(r"[^a-z0-9]+", "-", f"{owner}-{name}".lower()).strip("-")
    taken.add(slug)
    return slug


# ---------------------------------------------------------------- 自动摘要

def auto_entry(full: str, rank: int, desc: str, lang, stars_n: int, today_n: int, slug: str) -> dict:
    cat = classify(full, desc)
    today = fmt_today(today_n)
    stars = fmt_stars_k(stars_n)
    if desc:
        what_zh = f"{desc}（自动摘要，人工深度解析待补充。）"
        what_en = f"{desc} (Auto summary — a human deep dive is pending.)"
        tag_zh, tag_en = desc, desc
    else:
        tag_zh = "GitHub 热榜项目（描述待补充）"
        tag_en = "Trending repo (description pending)"
        what_zh = "该项目今日登上 GitHub Trending 日榜，暂无官方描述，人工深度解析待补充。"
        what_en = "This project is on today's GitHub Trending. No description available yet — a human deep dive is pending."
    stack_zh = f"主语言 {lang}。" if lang else ""
    stack_en = f"Primarily {lang}." if lang else ""
    hot_zh = f"今日新增 {today} stars，位列 GitHub Trending 日榜第 {rank} 名。"
    hot_en = f"{today} stars today, ranked #{rank} on today's GitHub Trending."
    return {
        "slug": slug, "full": full, "rank": rank, "cat": cat, "lang": lang,
        "stars": stars, "today": today, "today_n": today_n, "auto": True,
        "zh": {"tag": tag_zh, "what": what_zh, "content": "", "stack": stack_zh, "hot": hot_zh, "uses": []},
        "en": {"tag": tag_en, "what": what_en, "content": "", "stack": stack_en, "hot": hot_en, "uses": []},
    }


# ---------------------------------------------------------------- 每日归档 & 在榜追踪

def snapshot(date: str, stamp: str, repos: list) -> dict:
    """当日榜单快照（写入 archive/<date>.json）。"""
    return {
        "date": date,
        "generated_at": stamp,
        "repos": [{"full": r["full"], "rank": r["rank"], "stars": r["stars"],
                   "today_n": r["today_n"], "slug": r["slug"], "cat": r["cat"],
                   "lang": r["lang"]} for r in repos],
    }


def load_archives(archive_dir: str) -> list:
    """读取全部历史快照，按日期升序。"""
    out = []
    for p in sorted(glob.glob(os.path.join(archive_dir, "????-??-??.json"))):
        try:
            with open(p, encoding="utf-8") as f:
                a = json.load(f)
            if a.get("date") and isinstance(a.get("repos"), list):
                out.append(a)
        except (OSError, json.JSONDecodeError):
            print(f"[update] WARN: skipping unreadable archive {p}", file=sys.stderr)
    out.sort(key=lambda a: a["date"])
    return out


def compute_track(archives: list, full: str, today_str: str) -> dict:
    """从归档计算单个仓库的在榜追踪信息。

    days:     截至今日的连续在榜天数
    first:    首次上榜日期
    is_new:   今日首次上榜
    is_back:  曾在榜、昨日不在、今日回榜
    hist:     最近 HIST_DAYS 个在榜日 [{d, s, r}]（sparkline 数据）
    """
    points = []
    for a in archives:
        hit = next((r for r in a["repos"] if r["full"] == full), None)
        if hit:
            points.append({"d": a["date"], "s": hit["stars"], "r": hit["rank"]})
    hist = points[-HIST_DAYS:]
    days = 0
    for a in reversed(archives):
        if any(r["full"] == full for r in a["repos"]):
            days += 1
        else:
            break
    first = points[0]["d"] if points else today_str
    # 归档只有 1 天（追踪刚启动）时不判 NEW——无法区分「首次上榜」与「追踪刚开始」
    is_new = len(points) == 1 and points[0]["d"] == today_str and len(archives) >= 2
    is_back = (not is_new and len(points) >= 1 and points[-1]["d"] == today_str
               and len(archives) >= 2
               and not any(r["full"] == full for r in archives[-2]["repos"]))
    return {"days": days, "first": first, "is_new": is_new, "is_back": is_back, "hist": hist}


# ---------------------------------------------------------------- 元信息

def build_meta(prev_meta: dict, list_changed: bool, now: datetime, repos: list) -> dict:
    date = now.strftime("%Y-%m-%d")
    stamp = now.strftime("%Y-%m-%d %H:%M (CST)")
    n = len(repos)
    meta = dict(prev_meta or {})
    meta.update({
        "date": date,
        "generated_at": stamp,
        "source": "github.com/trending",
        "criteria": "Repositories · Today · All languages · logged out",
        "kicker_zh": f"每日自动更新 · {date} · 每日榜 · 全语言 · {n} 个仓库",
        "kicker_en": f"Auto-updated · {date} · Daily · All languages · {n} repos",
        "footer_zh": f"Trending Scope · 数据更新于 {stamp}，由自动化管线直连 github.com 抓取",
        "footer_en": f"Trending Scope · Data updated {stamp} by the automated pipeline, fetched directly from github.com",
    })
    if list_changed or not meta.get("headline_zh"):
        counts = {}
        for r in repos:
            counts[r["cat"]] = counts.get(r["cat"], 0) + 1
        cat_zh = "、".join(f"{CATS[c]['zh']} {k} 个" for c, k in counts.items())
        cat_en = ", ".join(f"{k} {CATS[c]['en']}" for c, k in counts.items())
        top3 = sorted(repos, key=lambda r: -r["today_n"])[:3]
        top3_zh = "、".join(f"{r['full']}（{r['today']}）" for r in top3)
        top3_en = ", ".join(f"{r['full']} ({r['today']})" for r in top3)
        meta["headline_zh"] = "今日热榜全景速递"
        meta["headline_en"] = "Your daily trending digest"
        meta["sub_zh"] = (f"{n} 个上榜仓库：{cat_zh}。今日新增 Star 前三：{top3_zh}。"
                          f"点击任意卡片查看深度解析。")
        meta["sub_en"] = (f"{n} trending repos: {cat_en}. Biggest star gainers today: {top3_en}. "
                          f"Click any card for a deep dive.")
    return meta


# ---------------------------------------------------------------- 校验

def validate(data: dict) -> list:
    errors = []
    if not isinstance(data.get("repos"), list) or not data["repos"]:
        errors.append("repos is empty")
        return errors
    slugs = set()
    for r in data["repos"]:
        for k in REQUIRED_REPO_KEYS:
            if k not in r:
                errors.append(f"{r.get('full','?')}: missing key {k}")
        if r.get("cat") not in CATS:
            errors.append(f"{r.get('full','?')}: bad cat {r.get('cat')}")
        if r.get("slug") in slugs:
            errors.append(f"{r.get('full','?')}: duplicate slug {r.get('slug')}")
        slugs.add(r.get("slug"))
        tr = r.get("track", {})
        if not isinstance(tr.get("hist"), list) or not isinstance(tr.get("days"), int):
            errors.append(f"{r.get('full','?')}: bad track")
        for loc in ("zh", "en"):
            blk = r.get(loc, {})
            for k in REQUIRED_TEXT_KEYS:
                if k not in blk:
                    errors.append(f"{r.get('full','?')}/{loc}: missing {k}")
            if not isinstance(blk.get("uses"), list):
                errors.append(f"{r.get('full','?')}/{loc}: uses not a list")
    return errors


# ---------------------------------------------------------------- 主流程

def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh Trending Scope data.json from github.com/trending")
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--data", default=os.path.join(here, "..", "data.json"), help="data.json 路径")
    ap.add_argument("--url", default=TRENDING_URL, help="trending 页面 URL")
    ap.add_argument("--min-repos", type=int, default=10, help="解析少于该数量视为页面结构变更，失败退出")
    ap.add_argument("--html", help="从本地 HTML 文件解析（离线测试用），跳过网络抓取")
    ap.add_argument("--dry-run", action="store_true", help="只打印将要发生的变化，不写文件")
    args = ap.parse_args()

    data_path = os.path.abspath(args.data)
    if args.html:
        print(f"[update] parsing local page {args.html} ...")
        with open(args.html, encoding="utf-8") as f:
            page = f.read()
    else:
        print(f"[update] fetching {args.url} ...")
        page = fetch_html(args.url)
    fetched = parse_trending(page)
    print(f"[update] parsed {len(fetched)} repos from trending page")
    if len(fetched) < args.min_repos:
        print(f"[update] ERROR: only {len(fetched)} repos parsed (< {args.min_repos}). "
              f"Trending page markup may have changed; existing data left untouched.", file=sys.stderr)
        return 1

    prev = {}
    prev_meta = {}
    if os.path.exists(data_path):
        with open(data_path, encoding="utf-8") as f:
            old = json.load(f)
        prev = {r["full"]: r for r in old.get("repos", [])}
        prev_meta = old.get("meta", {})

    taken_slugs = set()
    repos, kept, new, auto_kept = [], 0, 0, 0
    for i, fr in enumerate(fetched, 1):
        full = fr["full"]
        old = prev.get(full)
        if old and not old.get("auto"):
            # 仍在榜 + 已有人工精评：保留 zh/en 文本与分类，仅刷新动态字段
            slug = old["slug"]
            taken_slugs.add(slug)
            entry = dict(old)
            entry.update({
                "rank": i,
                "stars": fmt_stars_k(fr["stars_n"]),
                "today": fmt_today(fr["today_n"]),
                "today_n": fr["today_n"],
                "lang": fr["lang"] or old.get("lang"),
            })
            kept += 1
        elif old and old.get("auto"):
            # 仍在榜但此前是自动摘要：刷新自动文本
            slug = old["slug"]
            taken_slugs.add(slug)
            entry = auto_entry(full, i, fr["desc"], fr["lang"], fr["stars_n"], fr["today_n"], slug)
            auto_kept += 1
        else:
            slug = make_slug(full, taken_slugs)
            entry = auto_entry(full, i, fr["desc"], fr["lang"], fr["stars_n"], fr["today_n"], slug)
            new += 1
        repos.append(entry)

    old_fulls = set(prev)
    new_fulls = {r["full"] for r in repos}
    dropped = sorted(old_fulls - new_fulls)
    list_changed = old_fulls != new_fulls

    now = datetime.now(CN_TZ)
    today_str = now.strftime("%Y-%m-%d")
    stamp = now.strftime("%Y-%m-%d %H:%M (CST)")

    # 每日归档：今日快照与历史合并（同日期覆盖），据此计算每个仓库的在榜追踪
    archive_dir = os.path.join(os.path.dirname(data_path), "archive")
    archives = [a for a in load_archives(archive_dir) if a["date"] != today_str]
    today_snap = snapshot(today_str, stamp, repos)
    archives.append(today_snap)
    for r in repos:
        r["track"] = compute_track(archives, r["full"], today_str)

    data = {
        "schema": 1,
        "meta": build_meta(prev_meta, list_changed, now, repos),
        "cats": CATS,
        "repos": repos,
    }

    errors = validate(data)
    if errors:
        print("[update] ERROR: validation failed:", file=sys.stderr)
        for e in errors:
            print("  -", e, file=sys.stderr)
        return 1

    print(f"[update] kept {kept} curated, refreshed {auto_kept} auto, new {new}, dropped {len(dropped)}")
    if dropped:
        print("[update] dropped:", ", ".join(dropped))
    n_new = sum(1 for r in repos if r["track"]["is_new"])
    n_back = sum(1 for r in repos if r["track"]["is_back"])
    longest = max(repos, key=lambda r: r["track"]["days"])
    print(f"[update] tracking: {n_new} first-time, {n_back} returning, "
          f"longest streak {longest['track']['days']}d ({longest['full']})")
    print(f"[update] headline_zh: {data['meta']['headline_zh']}")
    print(f"[update] sub_zh: {data['meta']['sub_zh'][:80]}...")

    if args.dry_run:
        print("[update] dry-run: no files written")
        return 0

    os.makedirs(archive_dir, exist_ok=True)
    arch_path = os.path.join(archive_dir, today_str + ".json")
    with open(arch_path + ".tmp", "w", encoding="utf-8") as f:
        f.write(json.dumps(today_snap, ensure_ascii=False, indent=2) + "\n")
    os.replace(arch_path + ".tmp", arch_path)

    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    tmp = data_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(payload)
    os.replace(tmp, data_path)
    js_path = os.path.join(os.path.dirname(data_path), "data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("/* Auto-generated from data.json — do not edit by hand. */\n")
        f.write("window.TRENDING_DATA = " + payload)
    print(f"[update] wrote {data_path} and {js_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
