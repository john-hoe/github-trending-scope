#!/usr/bin/env python3
"""Trending Scope 每日更新管线

直连 github.com/trending 抓取榜单（每日/每周/每月 × 全语言+6 种语言），
刷新 data.json（双语数据源 + 多口径榜单）与 data.js（页面运行时加载的包装）。

结构：
- boards[range][lang]：各口径榜单（排名 / stars / 区间新增）
- repos[]：注册表（按 full 去重），保存双语解析、分类、在榜追踪
- archive/YYYY-MM-DD.json：每日·全语言榜快照，在榜追踪的历史依据

规则：
- 已在册的仓库：保留已有 zh/en 深度解析，仅更新动态字段。
- 新出现的仓库：自动生成带 auto 标记的简摘要（取自 GitHub 描述），待人工补充精评。
- 任一预期榜单抓取失败、缺失或解析数量不足时失败退出，绝不发布部分数据。
- 可选 LLM 解析：配置环境变量后，每轮对新上榜及历史 auto 仓库调用 OpenAI 兼容
  接口生成双语深度解析（成功后清除 auto 占位标记，但不等同人工事实核验）；未配置或
  调用失败时保持自动摘要降级。支持并发、退避重试和 GitHub Token 鉴权读取 README；
  每轮最多处理 --llm-limit 个，新上榜及全语言主榜优先。

用法：
    python3 scripts/update.py [--dry-run] [--data PATH] [--html PATH] [--min-repos 10] [--llm-limit 25]
环境：
    无需任何第三方依赖（Python 3.9+ 标准库）。
    LLM_API_KEY / LLM_BASE_URL：OpenAI 兼容接口的密钥与地址（如 https://api.openai.com/v1），
        两者都配置才启用 LLM 精评；未配置则全程保持自动摘要。
    LLM_PROTOCOL：接口协议 openai（默认）或 anthropic（Kimi Code 等 Anthropic
        Messages 兼容服务，base_url 形如 https://api.kimi.com/coding）。
    LLM_MODEL：模型名（默认随协议：gpt-4o-mini / kimi-for-coding）。LLM_LIMIT：每轮最多精评仓库数（默认 25）。
    LLM_CONCURRENCY / LLM_RETRIES / LLM_MAX_TOKENS：并发数、单条失败重试次数与单条最大输出
        token（默认 4 / 3 / 1800）。
    LLM_JSON_MODE=1：为 OpenAI 兼容接口请求 JSON Object 输出。
    LLM_THINKING=enabled|disabled：显式控制支持该参数的 OpenAI 兼容模型的思考模式。
    GITHUB_API_TOKEN / GITHUB_TOKEN：可选，用于提高 README API 额度。
    LLM_README=0：不把 README 摘录放入 prompt 上下文（默认取 README 前 3000 字符）。
"""
import argparse
import glob
import html as html_mod
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError

TRENDING_URL = "https://github.com/trending"
CN_TZ = timezone(timedelta(hours=8), "CST")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
LLM_UA = "Trending-Scope/1.0 (+https://github.com/john-hoe/github-trending-scope)"

RANGES = ["daily", "weekly", "monthly"]
LANGS = [("all", "All languages"), ("python", "Python"), ("typescript", "TypeScript"),
         ("javascript", "JavaScript"), ("rust", "Rust"), ("go", "Go"), ("c++", "C++")]
LANG_NAME = dict(LANGS)
RNG_ZH = {"daily": "日", "weekly": "周", "monthly": "月"}
RNG_EN = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
GAIN_ZH = {"daily": "今日", "weekly": "本周", "monthly": "本月"}
GAIN_EN = {"daily": "today", "weekly": "this week", "monthly": "this month"}

CATS = {
    "agent": {"zh": "Agent 工具链", "en": "Agent Tooling", "color": "#b83d15"},
    "ai":    {"zh": "AI 应用与模型", "en": "AI Apps & Models", "color": "#0e6f63"},
    "infra": {"zh": "平台·数据·应用", "en": "Platforms, Data & Apps", "color": "#8a5c0c"},
    "other": {"zh": "学习 & 游戏", "en": "Learning & Gaming", "color": "#5a7a3a"},
}

REQUIRED_REPO_KEYS = ("slug", "full", "rank", "cat", "lang", "stars", "today", "today_n", "auto", "track", "zh", "en")
REQUIRED_TEXT_KEYS = ("tag", "what", "content", "stack", "hot", "uses")
HIST_DAYS = 14  # sparkline 最多保留的历史点数
EXPECTED_BOARDS = tuple((rng, lang_id) for rng in RANGES for lang_id, _ in LANGS)
FULL_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SLUG_RE = re.compile(r"^[a-z0-9._-]+$")
CJK_RE = re.compile(r"[\u3400-\u9fff]")
PLACEHOLDER_MARKERS = (
    "自动摘要", "人工深度解析待补充", "描述待补充",
    "auto summary", "human deep dive is pending", "description pending",
)


# ---------------------------------------------------------------- 抓取与解析

def board_url(lang_id: str, rng: str) -> str:
    path = "" if lang_id == "all" else "/" + urllib.parse.quote(lang_id, safe="+")
    return f"{TRENDING_URL}{path}?since={rng}"


def fetch_html(url: str, timeout: int = 30, retries: int = 3, backoff: float = 1.0) -> str:
    """抓取页面；瞬时网络错误按指数退避重试，最终错误交给调用方处理。"""
    last_error = None
    for attempt in range(retries):
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001 —— 统一重试网络层瞬时失败
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(backoff * (2 ** attempt))
    raise last_error


def _strip_tags(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", fragment)
    return re.sub(r"\s+", " ", html_mod.unescape(text)).strip()


def _to_int(s: str) -> int:
    return int(s.replace(",", "").strip())


def parse_trending(page: str) -> list:
    """解析 trending 页面，返回 [{full, desc, lang, stars_n, today_n}, ...]（按榜单顺序）。"""
    chunks = re.split(r'<article\b[^>]*\bclass="[^"]*\bBox-row\b[^"]*"[^>]*>', page)[1:]
    repos = []
    for ch in chunks:
        m = re.search(r"<h2[^>]*>.*?href=\"/([^\"]+)\"", ch, re.S)
        if not m:
            continue
        full = m.group(1).strip()
        if not FULL_NAME_RE.fullmatch(full):
            continue
        desc_m = re.search(r'<p class="col-9[^"]*">(.*?)</p>', ch, re.S)
        desc = _strip_tags(desc_m.group(1)) if desc_m else ""
        lang_m = re.search(r'itemprop="programmingLanguage">\s*([^<]+)<', ch)
        lang = lang_m.group(1).strip() if lang_m else None
        stars_m = re.search(r"/stargazers\"[^>]*>(.*?)</a>", ch, re.S)
        stars_n = _to_int(_strip_tags(stars_m.group(1))) if stars_m else 0
        today_m = re.search(r"([\d,]+)\s*stars\s+(today|this\s+week|this\s+month)", ch)
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
         "machine learning", "deep learning", "ai", "genai", "openai", "vllm", "ml",
         "tokenizer", "embedding")


def _contains_keyword(text: str, keyword: str) -> bool:
    """按字母数字边界匹配，避免 `ml` 将 `html` 误判为 AI。"""
    plural = r"(?:s|es)?" if keyword.isalpha() else ""
    pattern = rf"(?<![a-z0-9]){re.escape(keyword)}{plural}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def classify(full: str, desc: str) -> str:
    text = (full + " " + desc).lower()
    if any(_contains_keyword(text, k) for k in AGENT_KW):
        return "agent"
    if any(_contains_keyword(text, k) for k in OTHER_KW):
        return "other"
    if any(_contains_keyword(text, k) for k in AI_KW):
        return "ai"
    return "infra"


def make_slug(full: str, taken: set) -> str:
    owner, name = full.split("/", 1)
    slug = name.lower()
    if slug in taken:
        slug = re.sub(r"[^a-z0-9]+", "-", f"{owner}-{name}".lower()).strip("-")
    taken.add(slug)
    return slug


def load_pinned_repo_names(data_path: str) -> list:
    """Load the explicit SEO catalog next to data.json, if present."""
    path = os.path.join(os.path.dirname(data_path), "seo-index.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        manifest = json.load(f)
    names = manifest.get("repos", [])
    if not isinstance(names, list) or len(names) != len(set(names)):
        raise ValueError("seo-index.json repos must be a unique list")
    if any(not isinstance(name, str) or not FULL_NAME_RE.fullmatch(name) for name in names):
        raise ValueError("seo-index.json contains an invalid repository name")
    return names


def retain_pinned_repos(registry: dict, order: list, previous: dict, pinned_names: list, taken_slugs: set) -> int:
    """Keep explicitly indexed editorial pages stable after they leave all live charts."""
    retained = 0
    for full in pinned_names:
        if full in registry:
            continue
        old = previous.get(full)
        if not old:
            raise ValueError(f"indexed repository is missing from both current and previous data: {full}")
        if old.get("auto"):
            raise ValueError(f"indexed repository is still an automatic placeholder: {full}")
        slug = old.get("slug")
        if (not isinstance(slug, str)
                or any(entry.get("slug") == slug for entry in registry.values())):
            raise ValueError(f"indexed repository has an invalid or duplicate slug: {full}")
        registry[full] = dict(old)
        order.append(full)
        taken_slugs.add(slug)
        retained += 1
    return retained


# ---------------------------------------------------------------- 自动摘要

def auto_entry(full: str, rank: int, desc: str, lang, stars_n: int, today_n: int, slug: str,
               rng: str = "daily", lang_id: str = "all") -> dict:
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
        what_zh = "该项目今日登上 GitHub Trending 榜单，暂无官方描述，人工深度解析待补充。"
        what_en = "This project is on GitHub Trending. No description available yet — a human deep dive is pending."
    stack_zh = f"主语言 {lang}。" if lang else ""
    stack_en = f"Primarily {lang}." if lang else ""
    if lang_id == "all":
        hot_zh = f"{GAIN_ZH[rng]}新增 {today} stars，位列 GitHub Trending {RNG_ZH[rng]}榜第 {rank} 名。"
        hot_en = f"{today} stars {GAIN_EN[rng]}, ranked #{rank} on the {RNG_EN[rng]} GitHub Trending chart."
    else:
        hot_zh = f"{GAIN_ZH[rng]}新增 {today} stars，位列 GitHub Trending {RNG_ZH[rng]}榜（{LANG_NAME.get(lang_id, lang_id)}）第 {rank} 名。"
        hot_en = f"{today} stars {GAIN_EN[rng]}, ranked #{rank} on the {RNG_EN[rng]} {LANG_NAME.get(lang_id, lang_id)} chart."
    return {
        "slug": slug, "full": full, "rank": rank, "cat": cat, "lang": lang,
        "stars": stars, "today": today, "today_n": today_n, "auto": True,
        "zh": {"tag": tag_zh, "what": what_zh, "content": "", "stack": stack_zh, "hot": hot_zh, "uses": []},
        "en": {"tag": tag_en, "what": what_en, "content": "", "stack": stack_en, "hot": hot_en, "uses": []},
    }


# ---------------------------------------------------------------- LLM 精评（可选）

LLM_PROMPT = """你是「Trending Scope」的编辑，为 GitHub 热榜仓库撰写双语深度解析。
根据下面的仓库信息，只输出一个 JSON 对象（不要输出 JSON 以外的任何文字）：
{{
  "cat": "agent | ai | infra | other 四选一（agent=AI 代理与工具链, ai=模型与 AI 应用, infra=平台/数据/基础设施/应用, other=学习/游戏等）",
  "tag_zh": "一句话定位，≤40字", "tag_en": "one-line positioning, ≤80 chars",
  "what_zh": "是做什么的，2~3句", "what_en": "what it does, 2-3 sentences",
  "content_zh": "仓库里有什么（目录/组成/形态），1~2句", "content_en": "what's inside, 1-2 sentences",
  "stack_zh": "技术栈与依赖，1~2句", "stack_en": "tech stack, 1-2 sentences",
  "hot_zh": "为什么火，1~2句，结合 star 数据", "hot_en": "why it's hot, 1-2 sentences, tie to the star numbers",
  "uses_zh": ["适用人群/场景 —— 一句话说明", "……共2~4条"],
  "uses_en": ["audience/scenario — one line each", "……2-4 items"]
}}
仓库：{full}
描述：{desc}
主语言：{lang}
Stars：{stars_n}（{gain_zh}新增 {today_n}，GitHub Trending {board_desc}第 {rank} 名）
{readme_block}"""


def llm_config(args) -> "dict | None":
    """LLM_API_KEY + LLM_BASE_URL 都配置才返回配置，否则 None（全程自动摘要）。"""
    key = os.environ.get("LLM_API_KEY", "").strip()
    base = os.environ.get("LLM_BASE_URL", "").strip().rstrip("/")
    if not key or not base:
        return None
    protocol = (os.environ.get("LLM_PROTOCOL") or "openai").strip().lower() or "openai"
    if protocol not in ("openai", "anthropic"):
        print(f"[llm] WARN: unknown LLM_PROTOCOL {protocol!r}, falling back to openai")
        protocol = "openai"
    default_model = "kimi-for-coding" if protocol == "anthropic" else "gpt-4o-mini"
    thinking = os.environ.get("LLM_THINKING", "").strip().lower()
    if thinking not in ("", "enabled", "disabled"):
        print(f"[llm] WARN: unknown LLM_THINKING {thinking!r}, omitting parameter")
        thinking = ""
    return {
        "key": key, "base": base, "protocol": protocol,
        "model": os.environ.get("LLM_MODEL", "").strip() or default_model,
        "limit": args.llm_limit,
        "concurrency": args.llm_concurrency,
        "retries": args.llm_retries,
        "max_tokens": max(256, int(os.environ.get("LLM_MAX_TOKENS") or "1800")),
        "json_mode": os.environ.get("LLM_JSON_MODE", "").strip().lower() in ("1", "true", "yes"),
        "thinking": thinking,
        "readme": os.environ.get("LLM_README", "1").strip() != "0",
    }


def fetch_readme(full: str, timeout: int = 15) -> str:
    """取 README 纯文本前 ~3000 字符作为 prompt 上下文；任何失败静默返回 ""。"""
    try:
        headers = {"User-Agent": UA, "Accept": "application/vnd.github.raw"}
        github_token = (os.environ.get("GITHUB_API_TOKEN") or os.environ.get("GITHUB_TOKEN") or "").strip()
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"
        req = urllib.request.Request(
            f"https://api.github.com/repos/{full}/readme",
            headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", "replace")
        return re.sub(r"\s+", " ", text).strip()[:3000]
    except Exception:  # noqa: BLE001 —— README 只是上下文，缺失不阻塞
        return ""


def llm_review(full: str, desc: str, lang, stars_n: int, today_n: int,
               rank: int, rng: str, lang_id: str, cfg: dict) -> "dict | None":
    """调 OpenAI 兼容接口生成双语精评；任何一步失败返回 None（调用方降级自动摘要）。"""
    readme = fetch_readme(full) if cfg["readme"] else ""
    board_desc = f"{RNG_ZH[rng]}榜" if lang_id == "all" \
        else f"{RNG_ZH[rng]}榜（{LANG_NAME.get(lang_id, lang_id)}）"
    prompt = LLM_PROMPT.format(
        full=full, desc=desc or "（无描述）", lang=lang or "未知",
        stars_n=stars_n, gain_zh=GAIN_ZH[rng], today_n=today_n,
        board_desc=board_desc, rank=rank,
        readme_block=f"README 摘录：{readme}" if readme else "")
    if cfg.get("protocol") == "anthropic":
        body = json.dumps({
            "model": cfg["model"], "max_tokens": cfg.get("max_tokens", 1800),
            "system": "You are a meticulous bilingual editor. Reply with JSON only.",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
        }).encode("utf-8")
        req = urllib.request.Request(
            cfg["base"] + "/v1/messages", data=body, method="POST",
            headers={"User-Agent": LLM_UA, "Content-Type": "application/json",
                     "x-api-key": cfg["key"], "anthropic-version": "2023-06-01"})
    else:
        request_body = {
            "model": cfg["model"],
            "max_tokens": cfg.get("max_tokens", 1800),
            "messages": [
                {"role": "system", "content": "You are a meticulous bilingual editor. Reply with JSON only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
        if cfg.get("json_mode"):
            request_body["response_format"] = {"type": "json_object"}
        if cfg.get("thinking") in ("enabled", "disabled"):
            request_body["thinking"] = {"type": cfg["thinking"]}
        body = json.dumps(request_body).encode("utf-8")
        req = urllib.request.Request(
            cfg["base"] + "/chat/completions", data=body, method="POST",
            headers={"User-Agent": LLM_UA, "Content-Type": "application/json",
                     "Authorization": f"Bearer {cfg['key']}"})
    text = ""
    retries = max(1, int(cfg.get("retries", 3)))
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.loads(resp.read().decode("utf-8", "replace"))
            if cfg.get("protocol") == "anthropic":
                text = "".join(b.get("text", "") for b in payload.get("content", [])
                               if b.get("type") == "text")
            else:
                text = payload["choices"][0]["message"]["content"]
            break
        except HTTPError as e:
            detail = f"HTTP {e.code}"
            try:
                payload = json.loads(e.read(4096).decode("utf-8", "replace"))
                error = payload.get("error", {}) if isinstance(payload, dict) else {}
                message = error.get("message") if isinstance(error, dict) else error
                if isinstance(message, str) and message.strip():
                    detail += ": " + re.sub(r"\s+", " ", message).strip()[:300]
            except (OSError, UnicodeError, json.JSONDecodeError):
                pass
            retryable = e.code in (408, 409, 425, 429) or 500 <= e.code < 600
            if not retryable or attempt + 1 == retries:
                print(f"[llm] {full}: request failed after {attempt + 1} attempt(s): {detail}")
                return None
            time.sleep(1.5 * (2 ** attempt))
        except Exception as e:  # noqa: BLE001 —— 瞬时网络/网关错误重试，最终才降级
            if attempt + 1 == retries:
                print(f"[llm] {full}: request failed after {retries} attempts: {e}")
                return None
            time.sleep(1.5 * (2 ** attempt))
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        print(f"[llm] {full}: no JSON object in reply")
        return None
    try:
        obj = json.loads(m.group(0))
    except Exception as e:
        print(f"[llm] {full}: unparseable JSON: {e}")
        return None
    zh, en, ok = {}, {}, True
    for loc, blk in (("zh", zh), ("en", en)):
        for k in ("tag", "what", "content", "stack", "hot"):
            v = obj.get(f"{k}_{loc}")
            if not isinstance(v, str) or not v.strip():
                ok = False
                break
            blk[k] = v.strip()
        uses = obj.get(f"uses_{loc}")
        if not isinstance(uses, list) or not [u for u in uses if isinstance(u, str) and u.strip()]:
            ok = False
        blk["uses"] = [u.strip() for u in uses if isinstance(u, str) and u.strip()][:6] \
            if isinstance(uses, list) else []
    if not ok:
        print(f"[llm] {full}: incomplete fields, falling back to auto summary")
        return None
    cat = obj.get("cat") if obj.get("cat") in CATS else classify(full, desc)
    return {"cat": cat, "zh": zh, "en": en}


def polish_with_llm(registry: dict, order: list, new_fulls: set,
                    info: dict, pres_map: dict, cfg: dict) -> int:
    """对 auto 仓库逐个调用 LLM 精评：新上榜优先，每轮最多 cfg['limit'] 个。"""
    cands = [f for f in order if registry[f].get("auto")]
    order_index = {full: i for i, full in enumerate(order)}
    cands.sort(key=lambda f: (
        f not in new_fulls,
        pres_map[f][1] != "all",
        RANGES.index(pres_map[f][0]),
        pres_map[f][2]["rank"],
        order_index[f],
    ))
    targets = cands[: cfg["limit"]]
    done = 0

    def review_one(full: str):
        rng_p, lid_p, e_p = pres_map[full]
        fr = info[full]
        res = llm_review(full, fr["desc"], fr["lang"], fr["stars_n"], fr["today_n"],
                         e_p["rank"], rng_p, lid_p, cfg)
        return full, res

    if not targets:
        return 0

    # 先用一个真实候选做健康检查，避免密钥/额度/模型错误时并发轰炸整个候选集。
    first_full, first_res = review_one(targets[0])
    if not first_res:
        print(f"[llm] provider preflight failed; skipped {len(targets) - 1} remaining repos")
        return 0
    first_entry = registry[first_full]
    first_entry["cat"], first_entry["zh"], first_entry["en"] = \
        first_res["cat"], first_res["zh"], first_res["en"]
    first_entry["auto"] = False
    done = 1
    print(f"[llm] polished {first_full}")

    remaining = targets[1:]
    workers = min(max(1, int(cfg.get("concurrency", 4))), len(remaining) or 1)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(review_one, full) for full in remaining]
        for future in as_completed(futures):
            full, res = future.result()
            if not res:
                continue
            entry = registry[full]
            entry["cat"], entry["zh"], entry["en"] = res["cat"], res["zh"], res["en"]
            entry["auto"] = False
            done += 1
            print(f"[llm] polished {full}")
    return done


# ---------------------------------------------------------------- 每日归档 & 在榜追踪

def snapshot(date: str, stamp: str, board_entries: list, registry: dict) -> dict:
    """当日（每日·全语言榜）快照，写入 archive/<date>.json。"""
    return {
        "date": date,
        "generated_at": stamp,
        "repos": [{"full": e["full"], "rank": e["rank"], "stars": e["stars"],
                   "today_n": e["today_n"],
                   "slug": registry[e["full"]]["slug"], "cat": registry[e["full"]]["cat"],
                   "lang": registry[e["full"]]["lang"]} for e in board_entries],
    }


def load_archives(archive_dir: str) -> list:
    """读取全部历史快照，按日期升序；损坏历史会阻止发布错误追踪数据。"""
    out = []
    for p in sorted(glob.glob(os.path.join(archive_dir, "????-??-??.json"))):
        try:
            with open(p, encoding="utf-8") as f:
                a = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"unreadable archive {p}: {exc}") from exc
        expected_date = os.path.basename(p)[:-5]
        try:
            datetime.strptime(expected_date, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"invalid archive filename date: {p}") from exc
        if a.get("date") != expected_date or not isinstance(a.get("repos"), list):
            raise ValueError(f"malformed archive {p}: date must match filename and repos must be a list")
        out.append(a)
    out.sort(key=lambda a: a["date"])
    return out


def compute_track(archives: list, full: str, today_str: str) -> dict:
    """从归档（每日·全语言榜）计算单个仓库的在榜追踪信息。

    days:     截至今日的连续在榜天数
    first:    首次上榜日期
    is_new:   今日首次上榜（归档 ≥2 天才判定，首日无法区分「新上榜」与「追踪刚启动」）
    is_back:  曾在榜、昨日不在、今日回榜
    hist:     最近 HIST_DAYS 个在榜日 [{d, s, r}]（sparkline 数据）
    """
    ordered = sorted(archives, key=lambda a: a["date"])
    points = []
    hits_by_date = {}
    for a in ordered:
        hit = next((r for r in a["repos"] if r["full"] == full), None)
        if hit:
            point = {"d": a["date"], "s": hit["stars"], "r": hit["rank"]}
            points.append(point)
            hits_by_date[a["date"]] = point
    hist = points[-HIST_DAYS:]
    days = 0
    expected = datetime.strptime(today_str, "%Y-%m-%d").date()
    while expected.isoformat() in hits_by_date:
        days += 1
        expected -= timedelta(days=1)
    first = points[0]["d"] if points else today_str
    is_new = len(points) == 1 and points[0]["d"] == today_str and len(ordered) >= 2
    yesterday = (datetime.strptime(today_str, "%Y-%m-%d").date() - timedelta(days=1)).isoformat()
    has_yesterday_archive = any(a["date"] == yesterday for a in ordered)
    is_back = (not is_new and len(points) >= 1 and points[-1]["d"] == today_str
               and has_yesterday_archive and yesterday not in hits_by_date)
    return {"days": days, "first": first, "is_new": is_new, "is_back": is_back, "hist": hist}


# ---------------------------------------------------------------- 元信息

def build_meta(prev_meta: dict, list_changed: bool, now: datetime, daily_entries: list) -> dict:
    date = now.strftime("%Y-%m-%d")
    stamp = now.strftime("%Y-%m-%d %H:%M (CST)")
    n = len(daily_entries)
    meta = dict(prev_meta or {})
    meta.pop("kicker_zh", None)
    meta.pop("kicker_en", None)
    meta.update({
        "date": date,
        "generated_at": stamp,
        "source": "github.com/trending",
        "criteria": "Repositories · Today/Week/Month · All languages · logged out",
        "footer_zh": f"Trending Scope · 数据更新于 {stamp}，由自动化管线直连 github.com 抓取",
        "footer_en": f"Trending Scope · Data updated {stamp} by the automated pipeline, fetched directly from github.com",
    })
    counts = {}
    for e in daily_entries:
        counts[e["cat"]] = counts.get(e["cat"], 0) + 1
    cat_zh = "、".join(f"{CATS[c]['zh']} {k} 个" for c, k in counts.items())
    cat_en = ", ".join(f"{k} {CATS[c]['en']}" for c, k in counts.items())
    top3 = sorted(daily_entries, key=lambda e: -e["today_n"])[:3]
    top3_zh = "、".join(f"{e['full']}（{e['today']}）" for e in top3)
    top3_en = ", ".join(f"{e['full']} ({e['today']})" for e in top3)
    meta["headline_zh"] = "今日热榜全景速递"
    meta["headline_en"] = "Your daily trending digest"
    meta["sub_zh"] = (f"{n} 个上榜仓库：{cat_zh}。今日新增 Star 前三：{top3_zh}。"
                      f"点击任意卡片查看深度解析。")
    meta["sub_en"] = (f"{n} trending repos: {cat_en}. Biggest star gainers today: {top3_en}. "
                      f"Click any card for a deep dive.")
    return meta


# ---------------------------------------------------------------- 校验

def validate(data: dict, min_repos: int, min_board_repos: int = 1,
             require_all_boards: bool = True, require_reviewed: bool = False) -> list:
    errors = []
    if data.get("schema") != 2:
        errors.append(f"unsupported schema {data.get('schema')}")
    meta = data.get("meta", {})
    for key in ("date", "generated_at", "source", "headline_zh", "headline_en", "sub_zh", "sub_en"):
        if not meta.get(key):
            errors.append(f"meta missing {key}")
    if meta.get("date"):
        try:
            datetime.strptime(meta["date"], "%Y-%m-%d")
        except (TypeError, ValueError):
            errors.append(f"meta has invalid date {meta.get('date')}")
    if set(data.get("cats", {})) != set(CATS):
        errors.append("category definitions do not match expected categories")
    lang_ids = [item.get("id") for item in data.get("langs", []) if isinstance(item, dict)]
    if require_all_boards and lang_ids != [lid for lid, _ in LANGS]:
        errors.append("language definitions do not match expected languages")
    boards = data.get("boards", {})
    daily = boards.get("daily", {}).get("all", [])
    if len(daily) < min_repos:
        errors.append(f"daily/all board has only {len(daily)} entries (< {min_repos})")
    if require_all_boards:
        for rng, lid in EXPECTED_BOARDS:
            if lid not in boards.get(rng, {}):
                errors.append(f"missing board {rng}/{lid}")

    repos = data.get("repos", [])
    fulls = [r.get("full") for r in repos if isinstance(r, dict)]
    registry = set(fulls)
    if len(fulls) != len(registry):
        errors.append("registry contains duplicate full names")
    for rng, langs in boards.items():
        if rng not in RANGES or not isinstance(langs, dict):
            errors.append(f"unexpected or invalid range {rng}")
            continue
        for lid, entries in langs.items():
            board_name = f"{rng}/{lid}"
            if lid not in dict(LANGS):
                errors.append(f"unexpected language board {board_name}")
            if not isinstance(entries, list):
                errors.append(f"board {board_name}: entries is not a list")
                continue
            required_count = min_repos if board_name == "daily/all" else min_board_repos
            if len(entries) < required_count:
                errors.append(f"board {board_name} has only {len(entries)} entries (< {required_count})")
            ranks = [e.get("rank") for e in entries if isinstance(e, dict)]
            if ranks != list(range(1, len(entries) + 1)):
                errors.append(f"board {board_name}: ranks are not sequential")
            board_fulls = [e.get("full") for e in entries if isinstance(e, dict)]
            if len(board_fulls) != len(set(board_fulls)):
                errors.append(f"board {board_name}: duplicate repo")
            for e in entries:
                if not isinstance(e, dict):
                    errors.append(f"board {board_name}: entry is not an object")
                    continue
                full = e.get("full")
                if full not in registry:
                    errors.append(f"board {board_name}: {full} not in registry")
                if not isinstance(e.get("stars"), (int, float)) or e.get("stars", -1) < 0:
                    errors.append(f"board {board_name}: {full} has invalid stars")
                if not isinstance(e.get("today_n"), int) or e.get("today_n", -1) < 0:
                    errors.append(f"board {board_name}: {full} has invalid today_n")
    if not repos:
        errors.append("repos is empty")
        return errors
    slugs = set()
    for r in repos:
        if not isinstance(r, dict):
            errors.append("registry entry is not an object")
            continue
        for k in REQUIRED_REPO_KEYS:
            if k not in r:
                errors.append(f"{r.get('full','?')}: missing key {k}")
        if r.get("cat") not in CATS:
            errors.append(f"{r.get('full','?')}: bad cat {r.get('cat')}")
        if not isinstance(r.get("full"), str) or not FULL_NAME_RE.fullmatch(r["full"]):
            errors.append(f"{r.get('full','?')}: invalid GitHub full name")
        if not isinstance(r.get("slug"), str) or not SLUG_RE.fullmatch(r["slug"]):
            errors.append(f"{r.get('full','?')}: invalid slug {r.get('slug')}")
        if require_reviewed and r.get("auto"):
            errors.append(f"{r.get('full','?')}: automated placeholder remains")
        if r.get("slug") in slugs:
            errors.append(f"{r.get('full','?')}: duplicate slug {r.get('slug')}")
        slugs.add(r.get("slug"))
        if not isinstance(r.get("stars"), (int, float)) or r.get("stars", -1) < 0:
            errors.append(f"{r.get('full','?')}: bad stars")
        if not isinstance(r.get("today_n"), int) or r.get("today_n", -1) < 0:
            errors.append(f"{r.get('full','?')}: bad today_n")
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
            if not r.get("auto"):
                for k in REQUIRED_TEXT_KEYS[:-1]:
                    if not isinstance(blk.get(k), str) or not blk[k].strip():
                        errors.append(f"{r.get('full','?')}/{loc}: reviewed {k} is empty")
                if not isinstance(blk.get("uses"), list) or not [u for u in blk["uses"] if isinstance(u, str) and u.strip()]:
                    errors.append(f"{r.get('full','?')}/{loc}: reviewed uses is empty")
                reviewed_text = " ".join(
                    [str(blk.get(k, "")) for k in REQUIRED_TEXT_KEYS[:-1]]
                    + [str(u) for u in blk.get("uses", [])]
                ).lower()
                if any(marker in reviewed_text for marker in PLACEHOLDER_MARKERS):
                    errors.append(f"{r.get('full','?')}/{loc}: reviewed placeholder text remains")
                if require_reviewed:
                    for k in REQUIRED_TEXT_KEYS[:-1]:
                        minimum = 8 if k == "tag" else 20
                        value = blk.get(k)
                        if not isinstance(value, str) or len(" ".join(value.split())) < minimum:
                            errors.append(
                                f"{r.get('full','?')}/{loc}: reviewed {k} is shorter than {minimum} characters"
                            )
                    uses = blk.get("uses")
                    if (not isinstance(uses, list) or len(uses) < 2
                            or any(not isinstance(use, str) or len(" ".join(use.split())) < 10 for use in uses)):
                        errors.append(
                            f"{r.get('full','?')}/{loc}: reviewed uses need at least 2 items of 10 characters"
                        )
                if loc == "zh":
                    for k in REQUIRED_TEXT_KEYS[:-1]:
                        value = blk.get(k)
                        if isinstance(value, str) and value.strip() and not CJK_RE.search(value):
                            errors.append(f"{r.get('full','?')}/zh: reviewed {k} has no Chinese text")
                    for use in blk.get("uses", []):
                        if isinstance(use, str) and use.strip() and not CJK_RE.search(use):
                            errors.append(f"{r.get('full','?')}/zh: reviewed use case has no Chinese text")
    return errors


# ---------------------------------------------------------------- 主流程

def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh Trending Scope data.json from github.com/trending")
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--data", default=os.path.join(here, "..", "data.json"), help="data.json 路径")
    ap.add_argument("--min-repos", type=int, default=10, help="主榜解析少于该数量视为页面结构变更，失败退出")
    ap.add_argument("--min-board-repos", type=int, default=5,
                    help="任一非主榜解析少于该数量视为部分数据，失败退出（默认 5）")
    ap.add_argument("--html", help="从本地 HTML 文件解析主榜（离线测试用），跳过网络抓取")
    ap.add_argument("--dry-run", action="store_true", help="只打印将要发生的变化，不写文件")
    ap.add_argument("--llm-limit", type=int, default=int(os.environ.get("LLM_LIMIT") or "25"),
                    help="每轮最多 LLM 精评的仓库数（默认 25，可用 env LLM_LIMIT 覆盖）")
    ap.add_argument("--llm-concurrency", type=int, default=int(os.environ.get("LLM_CONCURRENCY") or "4"),
                    help="LLM 精评并发数（默认 4，可用 env LLM_CONCURRENCY 覆盖）")
    ap.add_argument("--llm-retries", type=int, default=int(os.environ.get("LLM_RETRIES") or "3"),
                    help="单个 LLM 精评失败重试次数（默认 3，可用 env LLM_RETRIES 覆盖）")
    ap.add_argument("--require-reviewed", action="store_true",
                    help="存在任何自动占位摘要时失败退出，不发布不完整深度解析")
    args = ap.parse_args()

    if (args.min_repos < 1 or args.min_board_repos < 1 or args.llm_limit < 0
            or args.llm_concurrency < 1 or args.llm_retries < 1):
        ap.error("repo minimums/concurrency/retries must be >= 1; --llm-limit must be >= 0")

    data_path = os.path.abspath(args.data)

    # ---------------- 抓取全部榜单 ----------------
    boards = {rng: {} for rng in RANGES}
    info = {}     # full -> {desc, lang, stars_n, today_n}（首次出现时的原始值）
    order = []    # full 首次出现顺序（daily/all → weekly/all → monthly/all → 语言榜）
    fetched_boards = 0
    for rng in RANGES:
        for lang_id, _lang_name in LANGS:
            if args.html:
                if not (rng == "daily" and lang_id == "all"):
                    continue
                print(f"[update] parsing local page {args.html} ...")
                with open(args.html, encoding="utf-8") as f:
                    page = f.read()
            else:
                url = board_url(lang_id, rng)
                try:
                    page = fetch_html(url)
                    fetched_boards += 1
                    time.sleep(0.3)
                except Exception as e:  # noqa: BLE001 —— 记录失败，最终校验阻止部分数据发布
                    print(f"[update] ERROR: {rng}/{lang_id} fetch failed after retries: {e}", file=sys.stderr)
                    continue
            lst = parse_trending(page)
            if rng == "daily" and lang_id == "all" and len(lst) < args.min_repos:
                print(f"[update] ERROR: only {len(lst)} repos parsed on daily/all (< {args.min_repos}). "
                      f"Trending page markup may have changed; existing data left untouched.", file=sys.stderr)
                return 1
            required_count = args.min_repos if (rng == "daily" and lang_id == "all") else args.min_board_repos
            if len(lst) < required_count:
                print(f"[update] ERROR: {rng}/{lang_id} parsed {len(lst)} repos (< {required_count})",
                      file=sys.stderr)
                continue
            boards[rng][lang_id] = [{
                "full": r["full"], "rank": i + 1,
                "stars": fmt_stars_k(r["stars_n"]),
                "today": fmt_today(r["today_n"]), "today_n": r["today_n"],
            } for i, r in enumerate(lst)]
            for r in lst:
                if r["full"] not in info:
                    info[r["full"]] = r
                    order.append(r["full"])
    if not args.html:
        print(f"[update] fetched {fetched_boards} boards; registry candidates: {len(order)} repos")

    daily_board = boards["daily"].get("all", [])
    daily_fulls = {e["full"] for e in daily_board}

    # ---------------- 读取旧数据 ----------------
    prev, prev_meta, prev_daily_fulls = {}, {}, set()
    if os.path.exists(data_path):
        with open(data_path, encoding="utf-8") as f:
            old = json.load(f)
        prev = {r["full"]: r for r in old.get("repos", [])}
        prev_meta = old.get("meta", {})
        old_daily = old.get("boards", {}).get("daily", {}).get("all")
        if old_daily:
            prev_daily_fulls = {e["full"] for e in old_daily}
        else:  # v1 数据：repos 即日榜
            prev_daily_fulls = set(prev)

    try:
        pinned_names = load_pinned_repo_names(data_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[update] ERROR: invalid SEO index: {exc}", file=sys.stderr)
        return 1

    # ---------------- 注册表构建 ----------------
    taken_slugs = {
        prev[full]["slug"] for full in pinned_names
        if full in prev and isinstance(prev[full].get("slug"), str)
    }
    registry = {}   # full -> entry
    pres_map = {}   # full -> (rng, lang_id, board_entry)：auto 仓库的代表性榜单
    new_fulls = set()
    kept, new, auto_kept = 0, 0, 0
    for full in order:
        old = prev.get(full)
        fr = info[full]
        if old and not old.get("auto"):
            slug = old["slug"]
            taken_slugs.add(slug)
            entry = dict(old)
            entry.update({
                "lang": fr["lang"] or old.get("lang"),
                "stars": fmt_stars_k(fr["stars_n"]),
                "today": fmt_today(fr["today_n"]),
                "today_n": fr["today_n"],
            })
            if full in daily_fulls:
                entry["rank"] = next(e["rank"] for e in daily_board if e["full"] == full)
            kept += 1
        else:
            slug = old["slug"] if old else make_slug(full, taken_slugs)
            if old:
                taken_slugs.add(slug)
            # 找到该仓库最具代表性的榜单（daily/all → weekly/all → monthly/all → 语言榜）
            pres = None
            for rng in RANGES:
                e = next((x for x in boards[rng].get("all", []) if x["full"] == full), None)
                if e:
                    pres = (rng, "all", e)
                    break
            if not pres:
                for rng in RANGES:
                    for lang_id, _ in LANGS[1:]:
                        e = next((x for x in boards[rng].get(lang_id, []) if x["full"] == full), None)
                        if e:
                            pres = (rng, lang_id, e)
                            break
                    if pres:
                        break
            rng_p, lid_p, e_p = pres
            pres_map[full] = (rng_p, lid_p, e_p)
            entry = auto_entry(full, e_p["rank"], fr["desc"], fr["lang"],
                               fr["stars_n"], fr["today_n"], slug, rng=rng_p, lang_id=lid_p)
            if old:
                auto_kept += 1
            else:
                new += 1
                new_fulls.add(full)
        registry[full] = entry

    try:
        pinned_retained = retain_pinned_repos(registry, order, prev, pinned_names, taken_slugs)
    except ValueError as exc:
        print(f"[update] ERROR: cannot retain SEO catalog: {exc}", file=sys.stderr)
        return 1

    # ---------------- 可选：LLM 精评 ----------------
    llm_cfg = llm_config(args)
    if llm_cfg:
        n_llm = polish_with_llm(registry, order, new_fulls, info, pres_map, llm_cfg)
        print(f"[update] LLM polished {n_llm} repos (model {llm_cfg['model']}, limit {llm_cfg['limit']})")

    dropped = sorted(set(prev) - set(order))
    list_changed = prev_daily_fulls != daily_fulls

    # ---------------- 归档 & 在榜追踪 ----------------
    now = datetime.now(CN_TZ)
    today_str = now.strftime("%Y-%m-%d")
    stamp = now.strftime("%Y-%m-%d %H:%M (CST)")

    archive_dir = os.path.join(os.path.dirname(data_path), "archive")
    try:
        archives = [a for a in load_archives(archive_dir) if a["date"] != today_str]
    except ValueError as exc:
        print(f"[update] ERROR: {exc}; existing data left untouched.", file=sys.stderr)
        return 1
    today_snap = snapshot(today_str, stamp, daily_board, registry)
    archives.append(today_snap)
    for full, entry in registry.items():
        entry["track"] = compute_track(archives, full, today_str)

    repos = [registry[full] for full in order]

    # 主榜条目补上分类（build_meta 统计用）
    for e in daily_board:
        e["cat"] = registry[e["full"]]["cat"]

    langs_out = [{"id": lid, "name": lname} for lid, lname in LANGS
                 if lid == "all" or any(lid in boards[rng] for rng in RANGES)]
    data = {
        "schema": 2,
        "meta": build_meta(prev_meta, list_changed, now, daily_board),
        "cats": CATS,
        "langs": langs_out,
        "boards": boards,
        "repos": repos,
    }

    errors = validate(data, args.min_repos, args.min_board_repos,
                      require_all_boards=not bool(args.html), require_reviewed=args.require_reviewed)
    if errors:
        print("[update] ERROR: validation failed:", file=sys.stderr)
        for e in errors:
            print("  -", e, file=sys.stderr)
        return 1

    n_boards = sum(len(v) for v in boards.values())
    print(f"[update] registry {len(repos)} repos (kept {kept} existing, retained {pinned_retained} indexed, "
          f"refreshed {auto_kept} auto, new {new}, dropped {len(dropped)}), boards: {n_boards}")
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
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    js_path = os.path.join(os.path.dirname(data_path), "data.js")
    outputs = {
        arch_path: json.dumps(today_snap, ensure_ascii=False, indent=2) + "\n",
        data_path: payload,
        js_path: "/* Auto-generated from data.json — do not edit by hand. */\nwindow.TRENDING_DATA = " + payload,
    }
    try:
        for path, content in outputs.items():
            with open(path + ".tmp", "w", encoding="utf-8") as f:
                f.write(content)
        for path in outputs:
            os.replace(path + ".tmp", path)
    finally:
        for path in outputs:
            try:
                os.unlink(path + ".tmp")
            except FileNotFoundError:
                pass
    print(f"[update] wrote {data_path} ({len(payload)//1024} KB) and {js_path}")
    print(f"[update] wrote archive {arch_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
