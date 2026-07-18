import json
import re
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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


class AutomationContractTests(unittest.TestCase):
    def setUp(self):
        self.workflow = (ROOT / ".github" / "workflows" / "daily-update.yml").read_text(encoding="utf-8")

    def test_workflow_serializes_updates_and_tracks_archives(self):
        self.assertRegex(self.workflow, r"(?m)^concurrency:")
        self.assertIn("git add data.json data.js archive/", self.workflow)
        self.assertIn("pages deploy dist", self.workflow)
        self.assertNotIn("pages deploy . ", self.workflow)

    def test_workflow_runs_tests_before_update(self):
        test_at = self.workflow.find("unittest discover")
        update_at = self.workflow.find("scripts/update.py")
        self.assertGreaterEqual(test_at, 0)
        self.assertGreater(update_at, test_at)

    def test_workflow_authenticates_review_context_and_retries(self):
        self.assertIn("GITHUB_API_TOKEN: ${{ github.token }}", self.workflow)
        self.assertIn('LLM_CONCURRENCY: "4"', self.workflow)
        self.assertIn('LLM_RETRIES: "3"', self.workflow)

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

    def test_both_locales_include_keyboard_and_modal_contracts(self):
        for name in ("index.html", "index-en.html"):
            with self.subTest(name=name):
                text = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn('aria-hidden="true"', text)
                self.assertIn('e.key===" "', text)
                self.assertIn('aria-pressed=', text)
                self.assertIn('prefers-reduced-motion:reduce', text)
                self.assertIn(':focus-visible', text)
                self.assertIn('class="openhit"', text)
                self.assertNotIn('role="button"', text)
                self.assertNotIn('minmax(350px,1fr)', text)
                self.assertIn('repo=([A-Za-z0-9._-]+)', text)
                self.assertIn("object-src 'none'", text)
                self.assertIn('rel="canonical"', text)
                self.assertEqual(text.count('rel="alternate"'), 3)

    def test_light_theme_small_text_colors_meet_wcag_aa(self):
        for color in ("#6f6452", "#776c5b", "#b83d15", "#0e6f63", "#8a5c0c", "#805900"):
            with self.subTest(color=color):
                self.assertGreaterEqual(self.contrast(color, "#fffdf8"), 4.5)

    def test_dark_theme_small_text_colors_meet_wcag_aa(self):
        for color in ("#b3a78e", "#9b907b", "#e45c2d", "#2ba892", "#d09a2e", "#8aa851", "#e0a42c"):
            with self.subTest(color=color):
                self.assertGreaterEqual(self.contrast(color, "#221c15"), 4.5)


if __name__ == "__main__":
    unittest.main()
