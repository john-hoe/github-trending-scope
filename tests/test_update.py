import copy
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("trending_update", ROOT / "scripts" / "update.py")
UPDATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UPDATE)


def archive(day, repos):
    return {
        "date": day,
        "repos": [
            {"full": full, "rank": rank, "stars": stars, "today_n": 1}
            for full, rank, stars in repos
        ],
    }


class ClassificationTests(unittest.TestCase):
    def test_short_ml_keyword_does_not_match_html(self):
        self.assertEqual(UPDATE.classify("owner/html-tool", "An HTML parser"), "infra")

    def test_standalone_ml_keyword_matches_ai(self):
        self.assertEqual(UPDATE.classify("owner/tool", "Fast ML inference"), "ai")

    def test_agent_keyword_has_priority(self):
        self.assertEqual(UPDATE.classify("owner/tool", "Agent for LLM workflows"), "agent")

    def test_plural_agent_keyword_matches(self):
        self.assertEqual(UPDATE.classify("owner/tool", "Runtime for autonomous agents"), "agent")


class ParsingTests(unittest.TestCase):
    def test_article_class_order_does_not_break_parser(self):
        page = '''
        <article data-x="1" class="Box-row color-bg-default">
          <h2><a href="/owner/repo">owner / repo</a></h2>
          <p class="col-9 color-fg-muted">A useful &amp; safe tool</p>
          <span itemprop="programmingLanguage">Python</span>
          <a href="/owner/repo/stargazers">1,234</a>
          <span>56 stars today</span>
        </article>'''
        self.assertEqual(
            UPDATE.parse_trending(page),
            [{"full": "owner/repo", "desc": "A useful & safe tool", "lang": "Python", "stars_n": 1234, "today_n": 56}],
        )

    def test_non_repository_href_is_ignored(self):
        page = '<article class="Box-row"><h2><a href="/owner/repo/issues">bad</a></h2></article>'
        self.assertEqual(UPDATE.parse_trending(page), [])


class FetchTests(unittest.TestCase):
    def test_fetch_retries_transient_failure(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"ok"
        with mock.patch.object(UPDATE.urllib.request, "urlopen", side_effect=[OSError("temporary"), response]) as open_mock, \
             mock.patch.object(UPDATE.time, "sleep") as sleep_mock:
            self.assertEqual(UPDATE.fetch_html("https://example.test", retries=2), "ok")
        self.assertEqual(open_mock.call_count, 2)
        sleep_mock.assert_called_once()


class ArchiveTests(unittest.TestCase):
    def test_corrupt_archive_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "2026-07-18.json").write_text("{broken", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unreadable archive"):
                UPDATE.load_archives(directory)

    def test_archive_date_must_match_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "2026-07-18.json").write_text(
                json.dumps({"date": "2026-07-17", "repos": []}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "malformed archive"):
                UPDATE.load_archives(directory)


class TrackingTests(unittest.TestCase):
    def test_missing_calendar_day_breaks_streak(self):
        archives = [
            archive("2026-07-16", [("owner/repo", 2, 1.0)]),
            archive("2026-07-18", [("owner/repo", 1, 1.2)]),
        ]
        track = UPDATE.compute_track(archives, "owner/repo", "2026-07-18")
        self.assertEqual(track["days"], 1)
        self.assertFalse(track["is_back"])

    def test_consecutive_calendar_days_count(self):
        archives = [
            archive("2026-07-17", [("owner/repo", 2, 1.0)]),
            archive("2026-07-18", [("owner/repo", 1, 1.2)]),
        ]
        self.assertEqual(UPDATE.compute_track(archives, "owner/repo", "2026-07-18")["days"], 2)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.repo = {
            "slug": "repo", "full": "owner/repo", "rank": 1, "cat": "infra",
            "lang": "Python", "stars": 1.2, "today": "+12", "today_n": 12,
            "auto": True,
            "track": {"days": 1, "first": "2026-07-18", "is_new": False, "is_back": False, "hist": []},
            "zh": {"tag": "t", "what": "w", "content": "", "stack": "s", "hot": "h", "uses": []},
            "en": {"tag": "t", "what": "w", "content": "", "stack": "s", "hot": "h", "uses": []},
        }
        entry = {"full": "owner/repo", "rank": 1, "stars": 1.2, "today": "+12", "today_n": 12}
        boards = {rng: {lid: [copy.deepcopy(entry)] for lid, _ in UPDATE.LANGS} for rng in UPDATE.RANGES}
        self.data = {
            "schema": 2,
            "meta": {"date": "2026-07-18", "generated_at": "now", "source": "github.com/trending",
                     "headline_zh": "h", "headline_en": "h", "sub_zh": "s", "sub_en": "s"},
            "cats": copy.deepcopy(UPDATE.CATS),
            "langs": [{"id": lid, "name": name} for lid, name in UPDATE.LANGS],
            "boards": boards,
            "repos": [self.repo],
        }

    def test_complete_board_matrix_passes(self):
        self.assertEqual(UPDATE.validate(self.data, 1, 1, True), [])

    def test_missing_board_is_rejected(self):
        del self.data["boards"]["weekly"]["rust"]
        errors = UPDATE.validate(self.data, 1, 1, True)
        self.assertTrue(any("missing board weekly/rust" in e for e in errors), errors)

    def test_duplicate_and_non_sequential_ranks_are_rejected(self):
        bad = copy.deepcopy(self.data["boards"]["daily"]["all"][0])
        bad["rank"] = 3
        self.data["boards"]["daily"]["all"].append(bad)
        errors = UPDATE.validate(self.data, 1, 1, True)
        self.assertTrue(any("duplicate repo" in e for e in errors), errors)
        self.assertTrue(any("ranks are not sequential" in e for e in errors), errors)


class MetadataTests(unittest.TestCase):
    def test_dynamic_metadata_is_refreshed_and_legacy_kickers_removed(self):
        rows = [{"full": "owner/repo", "cat": "infra", "today": "+12", "today_n": 12}]
        meta = UPDATE.build_meta(
            {"kicker_zh": "stale", "kicker_en": "stale", "sub_zh": "stale"},
            False,
            datetime(2026, 7, 18, 8, 23, tzinfo=UPDATE.CN_TZ),
            rows,
        )
        self.assertNotIn("kicker_zh", meta)
        self.assertNotIn("kicker_en", meta)
        self.assertIn("1 个上榜仓库", meta["sub_zh"])


if __name__ == "__main__":
    unittest.main()
