import json
import re
import subprocess
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree

from scripts import build_site


ROOT = Path(__file__).resolve().parents[1]
GA4_MEASUREMENT_ID = "G-8GNR8S1LRW"
GA4_SCRIPT_URL = f"https://www.googletagmanager.com/gtag/js?id={GA4_MEASUREMENT_ID}"


class DataIntegrityTests(unittest.TestCase):
    def test_favicon_is_square_512_png(self):
        raw = (ROOT / "favicon.png").read_bytes()
        self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", raw[16:24]), (512, 512))

    def test_data_js_matches_canonical_json(self):
        data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
        js = (ROOT / "data.js").read_text(encoding="utf-8")
        prefix = "/* Auto-generated from data.json — do not edit by hand. */\nwindow.TRENDING_DATA = "
        self.assertTrue(js.startswith(prefix))
        self.assertEqual(json.loads(js[len(prefix):]), data)

    def test_current_archive_exists_and_matches_daily_board(self):
        data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
        archive_path = ROOT / "archive" / f"{data['meta']['date']}.json"
        self.assertTrue(archive_path.is_file(), archive_path)
        archived = json.loads(archive_path.read_text(encoding="utf-8"))
        self.assertEqual(
            [row["full"] for row in archived["repos"]],
            [row["full"] for row in data["boards"]["daily"]["all"]],
        )

    def test_indexed_editorial_notes_avoid_volatile_rank_and_star_claims(self):
        data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
        indexed = set(json.loads((ROOT / "seo-index.json").read_text(encoding="utf-8"))["repos"])
        volatile = re.compile(
            r"(?:\d+(?:\.\d+)?k[- ]?star|\+\d|stars? today|today|yesterday|recently|"
            r"今日|昨天|近期|本周|本月|上线半年|\d+\s*万\s*star)",
            re.IGNORECASE,
        )
        for repo in data["repos"]:
            if repo["full"] not in indexed:
                continue
            for locale in ("en", "zh"):
                with self.subTest(repo=repo["full"], locale=locale):
                    self.assertIsNone(volatile.search(repo[locale]["hot"]))


class AutomationContractTests(unittest.TestCase):
    def setUp(self):
        self.workflow = (ROOT / ".github" / "workflows" / "daily-update.yml").read_text(encoding="utf-8")

    def test_workflow_serializes_updates_and_tracks_archives(self):
        self.assertRegex(self.workflow, r"(?m)^concurrency:")
        self.assertIn("git add data.json data.js archive/", self.workflow)
        self.assertIn("scripts/build_site.py --output dist", self.workflow)
        self.assertNotIn("cp index.html index-zh.html index-en.html", self.workflow)
        self.assertIn("pages deploy dist", self.workflow)
        self.assertNotIn("pages deploy . ", self.workflow)

    def test_workflow_runs_tests_before_update(self):
        test_at = self.workflow.find("unittest discover")
        update_at = self.workflow.find("scripts/update.py")
        self.assertGreaterEqual(test_at, 0)
        self.assertGreater(update_at, test_at)

    def test_workflow_retests_refreshed_data_before_build(self):
        test_positions = [match.start() for match in re.finditer("unittest discover", self.workflow)]
        update_at = self.workflow.find("scripts/update.py")
        build_at = self.workflow.find("scripts/build_site.py --output dist")
        self.assertEqual(len(test_positions), 2)
        self.assertLess(test_positions[0], update_at)
        self.assertLess(update_at, test_positions[1])
        self.assertLess(test_positions[1], build_at)

    def test_workflow_authenticates_review_context_and_retries(self):
        self.assertIn("GITHUB_API_TOKEN: ${{ github.token }}", self.workflow)
        self.assertIn('LLM_CONCURRENCY: "4"', self.workflow)
        self.assertIn('LLM_RETRIES: "3"', self.workflow)
        self.assertIn('LLM_MAX_TOKENS: "1800"', self.workflow)
        self.assertIn("LLM_JSON_MODE: ${{ vars.LLM_JSON_MODE }}", self.workflow)
        self.assertIn("LLM_THINKING: ${{ vars.LLM_THINKING }}", self.workflow)

    def test_workflow_blocks_placeholder_content_from_production(self):
        self.assertIn("scripts/update.py --require-reviewed", self.workflow)
        self.assertIn("vars.LLM_LIMIT || '400'", self.workflow)

    def test_workflow_can_deploy_static_changes_without_refreshing_data(self):
        self.assertRegex(self.workflow, r"(?m)^\s{6}deploy_only:")
        self.assertIn('type: boolean', self.workflow)
        self.assertEqual(self.workflow.count('if: ${{ inputs.deploy_only != true }}'), 3)
        self.assertIn("scripts/build_site.py --output dist", self.workflow)

    def test_production_build_runs_before_data_commit(self):
        build_at = self.workflow.find("scripts/build_site.py --output dist")
        commit_at = self.workflow.find("git add data.json data.js archive/")
        self.assertGreaterEqual(build_at, 0)
        self.assertGreater(commit_at, build_at)

    def test_third_party_actions_are_pinned_to_commits(self):
        uses = re.findall(r"(?m)^\s*-?\s*uses:\s*[^@\s]+@([^\s#]+)", self.workflow)
        self.assertTrue(uses)
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in uses), uses)


class FrontendAccessibilityContractTests(unittest.TestCase):
    @staticmethod
    def contrast(foreground, background):
        def luminance(value):
            channels = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            channels = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
            return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]
        high, low = sorted((luminance(foreground), luminance(background)), reverse=True)
        return (high + 0.05) / (low + 0.05)

    def test_starry_theme_assets_exist_and_text_colors_meet_wcag_aa(self):
        for name in ("scope.css", "scope.js", "assets/milkyway.jpg", "favicon.png"):
            self.assertTrue((ROOT / name).is_file(), name)
        css = (ROOT / "scope.css").read_text(encoding="utf-8")
        for skin, colors in (("zh", ("#f1ece0", "#a9a69f", "#d4b472")), ("en", ("#eef0f5", "#9ca3b5", "#e9b872"))):
            self.assertIn(f'[data-skin="{skin}"]', css)
            for color in colors:
                with self.subTest(skin=skin, color=color):
                    self.assertIn(color, css)
                    self.assertGreaterEqual(self.contrast(color, "#02030a"), 4.5)

    def test_videos_manifest_points_at_existing_posters_and_data(self):
        path = ROOT / "videos.json"
        if not path.is_file():
            self.skipTest("no videos yet")
        videos = json.loads(path.read_text(encoding="utf-8"))
        data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
        known = {repo["full"] for repo in data["repos"]}
        for edition in videos["editions"]:
            for locale in ("zh", "en"):
                top = edition["top10"][locale]
                self.assertTrue((ROOT / top["poster"]).is_file(), top["poster"])
                self.assertGreater(len(top["chapters"]), 2)
            for full, entry in edition["repos"].items():
                self.assertIn(full, known)
                for locale in ("zh", "en"):
                    self.assertTrue((ROOT / entry[locale]["poster"]).is_file(), entry[locale]["poster"])


class SEOProductionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp_dir.name) / "dist"
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_site.py"), "--output", str(cls.output)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        cls.report = json.loads(completed.stdout)
        cls.sitemap_text = (cls.output / "sitemap.xml").read_text(encoding="utf-8")
        tree = ElementTree.fromstring(cls.sitemap_text)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        cls.urls = [node.text for node in tree.findall("sm:url/sm:loc", ns)]

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    @classmethod
    def file_for_url(cls, url):
        path = urlsplit(url).path
        if path == "/":
            return cls.output / "index.html"
        if path == "/index-zh":
            return cls.output / "index-zh.html"
        return cls.output / path.lstrip("/") / "index.html"

    @staticmethod
    def video_names():
        path = ROOT / "videos.json"
        if not path.is_file():
            return set()
        videos = json.loads(path.read_text(encoding="utf-8"))
        return {full for ed in videos.get("editions", []) for full in (ed.get("repos") or {})}

    def test_crawl_contract_and_sitemap_scope(self):
        robots = (self.output / "robots.txt").read_text(encoding="utf-8")
        self.assertEqual(robots.count("Sitemap:"), 2)  # 主 sitemap + 视频 sitemap
        self.assertIn("https://trending.cosolution.cc/sitemap.xml", robots)
        self.assertTrue((self.output / "404.html").is_file())
        self.assertIn('name="robots" content="noindex,follow"', (self.output / "404.html").read_text())
        self.assertNotIn('rel="canonical"', (self.output / "404.html").read_text())
        self.assertNotIn('rel="alternate"', (self.output / "404.html").read_text())
        self.assertIn("/index-en / 301", (self.output / "_redirects").read_text())
        manifest = json.loads((ROOT / "seo-index.json").read_text(encoding="utf-8"))
        extra = self.video_names() - set(manifest["repos"])
        expected = 70 + 2 * len(extra)  # every repo with its own video also gets an indexable bilingual page
        self.assertEqual(len(self.urls), expected)
        self.assertEqual(len(self.urls), len(set(self.urls)))
        self.assertEqual(self.report["urls"], expected)

    def test_every_sitemap_url_is_a_unique_indexable_canonical(self):
        titles = set()
        descriptions = set()
        for url in self.urls:
            with self.subTest(url=url):
                source = self.file_for_url(url).read_text(encoding="utf-8")
                self.assertIn(f'<link rel="canonical" href="{url}">', source)
                self.assertNotIn("noindex", source.lower())
                title = re.search(r"<title>(.*?)</title>", source, re.S).group(1)
                description = re.search(r'<meta name="description" content="([^"]+)">', source).group(1)
                self.assertNotIn(title, titles)
                self.assertNotIn(description, descriptions)
                titles.add(title)
                descriptions.add(description)
                scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', source, re.S)
                self.assertTrue(scripts)
                for script in scripts:
                    json.loads(script.replace("<\\/", "</"))

    def test_landing_pages_are_server_rendered_and_link_all_chart_views(self):
        data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
        daily_names = [row["full"] for row in data["boards"]["daily"]["all"]]
        indexed_names = set(json.loads(
            (ROOT / "seo-index.json").read_text(encoding="utf-8")
        )["repos"]) | self.video_names()
        for name, locale in (("index.html", "en"), ("index-zh.html", "zh")):
            source = (self.output / name).read_text(encoding="utf-8")
            cards = re.search(r'<ol class="cards">(.*?)</ol>', source, re.S).group(1)
            self.assertEqual(cards.count('class="scard"'), 10)
            rows = re.search(r'<ol class="rows">(.*?)</ol>', source, re.S).group(1)
            self.assertEqual(rows.count("<li>"), len(daily_names) - 10)
            for index, full in enumerate(daily_names):
                href = build_site.repo_path(full, locale) if (index < 10 or full in indexed_names) \
                    else f"https://github.com/{full}"
                self.assertIn(f'href="{href}"', cards if index < 10 else rows)
            self.assertEqual(source.count('class="chips"'), 1)
            nav = re.search(r'<nav class="chips".*?</nav>', source, re.S).group(0)
            self.assertEqual(nav.count("<a "), 21)
            self.assertEqual(source.count('data-skin="%s"' % locale), 1)
        english = (self.output / "index.html").read_text(encoding="utf-8")
        chinese = (self.output / "index-zh.html").read_text(encoding="utf-8")
        self.assertIn('class="lang" hreflang="zh-CN" href="/index-zh">中文</a>', english)
        self.assertIn('class="lang" hreflang="en" href="/">English</a>', chinese)
        for source in (english, chinese):
            self.assertIn("cosolutions-Affiliate", source)
            self.assertIn('"@type":"VideoObject"', source)
        # 联系方式出现在首页和每个内页的页脚
        pages = [self.output / "index.html", self.output / "index-zh.html",
                 self.output / "repos" / "index.html", self.output / "trending" / "weekly" / "python" / "index.html"]
        for page in pages:
            source = page.read_text(encoding="utf-8")
            self.assertIn('href="https://t.me/johnjohor"', source, page)
            self.assertIn('href="mailto:john@cosolution.cc"', source, page)
        self.assertEqual(english.count('id="contact"'), 1)
        # 视频不提供下载入口
        self.assertIn('controlslist="nodownload noremoteplayback"', english)
        self.assertIn("disablepictureinpicture", english)
        # 长视频有 1080p / 720p 两档切换
        for source in (english, chinese):
            self.assertEqual(source.count('data-q="hd"'), 1)
            self.assertIn("-720.mp4", source)

    def test_video_sitemap_matches_pages(self):
        source = (self.output / "sitemap-video.xml").read_text(encoding="utf-8")
        self.assertIn("http://www.google.com/schemas/sitemap-video/1.1", source)
        # 首页 2 个长视频 + 10 个仓库 × 中英 20 个短视频
        self.assertEqual(source.count("<video:video>"), 22)
        for tag in ("thumbnail_loc", "title", "description", "content_loc", "duration", "publication_date"):
            self.assertEqual(source.count(f"<video:{tag}>"), 22, tag)
        locs = re.findall(r"<url>\s*<loc>(.*?)</loc>", source)
        self.assertEqual(len(locs), 22)
        self.assertIn(build_site.BASE_URL + "/", locs)
        self.assertIn(build_site.BASE_URL + "/index-zh", locs)
        self.assertTrue(all(url in self.urls for url in locs if url.count("/") > 3))
        self.assertIn(f"Sitemap: {build_site.BASE_URL}/sitemap-video.xml", (self.output / "robots.txt").read_text(encoding="utf-8"))

    def test_all_board_views_exist_bilingually(self):
        board_urls = [url for url in self.urls if "/trending/" in url]
        self.assertEqual(len(board_urls), 40)
        sample = self.output / "trending" / "weekly" / "python" / "index.html"
        source = sample.read_text(encoding="utf-8")
        self.assertIn("GitHub Trending · Weekly · Python", source)
        self.assertIn('class="board-row"', source)
        self.assertNotIn('<script src="data.js"', source)

    def test_ga4_tracks_each_real_content_page_once_without_redirect_or_404_noise(self):
        html_paths = sorted(self.output.rglob("*.html"))
        excluded = {self.output / "404.html", self.output / "index-en.html"}
        tracked = []
        for path in html_paths:
            source = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(self.output)):
                if path in excluded:
                    self.assertNotIn(GA4_MEASUREMENT_ID, source)
                    self.assertNotIn("googletagmanager.com/gtag/js", source)
                    continue
                tracked.append(path)
                self.assertEqual(source.count(GA4_SCRIPT_URL), 1)
                self.assertEqual(source.count(f"gtag('config', '{GA4_MEASUREMENT_ID}'"), 1)
                self.assertEqual(source.count(GA4_MEASUREMENT_ID), 2)
                self.assertNotIn("gtag('event', 'page_view'", source)
                self.assertIn("'allow_google_signals': false", source)
                self.assertIn("'allow_ad_personalization_signals': false", source)
                directives = build_site.csp_directives(source)
                for directive, required_sources in build_site.GA4_CSP_REQUIREMENTS:
                    self.assertEqual(required_sources - directives.get(directive, set()), set())
        self.assertEqual(len(tracked), self.report["html_pages"] - 2)
        self.assertGreater(len(tracked), self.report["urls"])

    def test_ga4_validator_rejects_csp_domains_hidden_in_body_text(self):
        path = self.output / "index.html"
        original = path.read_text(encoding="utf-8")
        match = re.search(r'(<meta http-equiv="Content-Security-Policy" content=")([^"]+)(">)', original)
        self.assertIsNotNone(match)
        broken_csp = match.group(2)
        for marker in (
            "https://*.googletagmanager.com",
            "https://*.google-analytics.com",
            "https://*.analytics.google.com",
        ):
            broken_csp = broken_csp.replace(marker, "https://blocked.invalid")
        decoy = "<!-- https://*.googletagmanager.com https://*.google-analytics.com https://*.analytics.google.com -->"
        modified = original[: match.start(2)] + broken_csp + original[match.end(2) :] + decoy
        path.write_text(modified, encoding="utf-8")
        try:
            with self.assertRaisesRegex(ValueError, "GA4 CSP"):
                build_site.validate_output(self.output, self.urls)
        finally:
            path.write_text(original, encoding="utf-8")

    def test_ga4_exists_only_in_production_output(self):
        source = (ROOT / "index-en.html").read_text(encoding="utf-8")
        self.assertNotIn(GA4_MEASUREMENT_ID, source)
        self.assertNotIn("googletagmanager.com/gtag/js", source)
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "build_site.py"), "--output", str(Path(tmp) / "dist"), "--preview"],
                cwd=ROOT, check=True, capture_output=True, text=True,
            )
            for page in (Path(tmp) / "dist").rglob("*.html"):
                self.assertNotIn(GA4_MEASUREMENT_ID, page.read_text(encoding="utf-8"), page.name)

    def test_only_original_editorial_subset_is_indexed(self):
        manifest = json.loads((ROOT / "seo-index.json").read_text(encoding="utf-8"))
        data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
        indexed_names = set(manifest["repos"]) | self.video_names()
        self.assertEqual(len(manifest["repos"]), 13)
        indexed = "https://trending.cosolution.cc/repos/codecrafters-io/build-your-own-x/"
        self.assertIn(indexed, self.urls)
        selected_source = self.file_for_url(indexed).read_text(encoding="utf-8")
        self.assertIn("What it does", selected_source)
        unselected_names = sorted(repo["full"] for repo in data["repos"] if repo["full"] not in indexed_names)
        self.assertTrue(unselected_names)
        for full_name in unselected_names:
            for locale in ("en", "zh"):
                with self.subTest(repo=full_name, locale=locale):
                    detail_path = build_site.repo_path(full_name, locale)
                    unselected = self.output / detail_path.strip("/") / "index.html"
                    self.assertTrue(unselected.is_file(), unselected)
                    source = unselected.read_text(encoding="utf-8")
                    self.assertIn('name="robots" content="noindex,follow"', source)
                    self.assertNotIn(detail_path, self.sitemap_text)

    def test_directory_links_every_indexed_detail(self):
        manifest = json.loads((ROOT / "seo-index.json").read_text(encoding="utf-8"))
        english = (self.output / "repos" / "index.html").read_text(encoding="utf-8").lower()
        chinese = (self.output / "zh" / "repos" / "index.html").read_text(encoding="utf-8").lower()
        for full_name in manifest["repos"]:
            path = full_name.lower() + "/"
            self.assertIn(f'href="/repos/{path}"', english)
            self.assertIn(f'href="/zh/repos/{path}"', chinese)

    def test_sitemap_pages_are_reachable_within_two_clicks_per_locale(self):
        sitemap_urls = set(self.urls)

        def links_from(url):
            source = self.file_for_url(url).read_text(encoding="utf-8")
            return {
                urljoin(url, href)
                for href in re.findall(r'<a\b[^>]*\bhref="([^"]+)"', source)
                if not href.startswith(("#", "mailto:"))
            } & sitemap_urls

        for root, locale_urls in (
            ("https://trending.cosolution.cc/", {u for u in sitemap_urls if "/zh/" not in u and not u.endswith("/index-zh")}),
            ("https://trending.cosolution.cc/index-zh", {u for u in sitemap_urls if "/zh/" in u or u.endswith("/index-zh")}),
        ):
            reached = {root}
            frontier = {root}
            for _ in range(2):
                frontier = set().union(*(links_from(url) for url in frontier)) - reached
                reached.update(frontier)
            self.assertEqual(locale_urls - reached, set())


if __name__ == "__main__":
    unittest.main()
