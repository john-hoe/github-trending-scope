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

    def test_readme_request_uses_github_token(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"README"
        with mock.patch.dict(UPDATE.os.environ, {"GITHUB_API_TOKEN": "secret-token"}, clear=False), \
             mock.patch.object(UPDATE.urllib.request, "urlopen", return_value=response) as open_mock:
            self.assertEqual(UPDATE.fetch_readme("owner/repo"), "README")
        request = open_mock.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-token")


class LLMReviewTests(unittest.TestCase):
    def test_transient_llm_failure_is_retried(self):
        review = {
            "cat": "infra",
            "tag_zh": "中文定位", "tag_en": "English positioning",
            "what_zh": "中文说明。", "what_en": "English explanation.",
            "content_zh": "仓库内容。", "content_en": "Repository contents.",
            "stack_zh": "技术栈。", "stack_en": "Technology stack.",
            "hot_zh": "热度原因。", "hot_en": "Why it is hot.",
            "uses_zh": ["使用场景"], "uses_en": ["Use case"],
        }
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            "choices": [{"message": {"content": json.dumps(review)}}]
        }).encode()
        cfg = {"protocol": "openai", "base": "https://example.test", "key": "k",
               "model": "m", "readme": False, "retries": 2}
        with mock.patch.object(UPDATE.urllib.request, "urlopen", side_effect=[OSError("temporary"), response]) as open_mock, \
             mock.patch.object(UPDATE.time, "sleep") as sleep_mock:
            result = UPDATE.llm_review("owner/repo", "desc", "Python", 10, 2, 1, "daily", "all", cfg)
        self.assertEqual(result["zh"]["tag"], "中文定位")
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


class PinnedCatalogTests(unittest.TestCase):
    def test_indexed_repo_is_retained_after_leaving_all_live_boards(self):
        old = {
            "owner/repo": {
                "full": "owner/repo", "slug": "repo", "auto": False,
                "zh": {}, "en": {}, "track": {},
            }
        }
        registry, order, slugs = {}, [], {"repo"}
        retained = UPDATE.retain_pinned_repos(
            registry, order, old, ["owner/repo"], slugs
        )
        self.assertEqual(retained, 1)
        self.assertEqual(order, ["owner/repo"])
        self.assertEqual(registry["owner/repo"]["slug"], "repo")

    def test_automatic_placeholder_cannot_be_pinned_for_indexing(self):
        old = {"owner/repo": {"full": "owner/repo", "slug": "repo", "auto": True}}
        with self.assertRaisesRegex(ValueError, "automatic placeholder"):
            UPDATE.retain_pinned_repos({}, [], old, ["owner/repo"], set())


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

    def test_reviewed_gate_rejects_automatic_placeholder(self):
        errors = UPDATE.validate(self.data, 1, 1, True, require_reviewed=True)
        self.assertTrue(any("automated placeholder remains" in e for e in errors), errors)

    def test_reviewed_gate_accepts_complete_review(self):
        self.repo["auto"] = False
        self.repo["zh"] = {
            "tag": "这是完整的中文一句话定位", "what": "这是足够完整的中文项目功能介绍，用于质量门槛测试。",
            "content": "这里说明仓库包含的核心模块、文档与示例结构。",
            "stack": "这里说明主要技术栈、运行环境以及关键依赖。",
            "hot": "这里用不依赖实时数字的方式说明项目受到关注的原因。",
            "uses": ["开发者学习项目内部实现的具体使用场景", "团队评估技术路线与依赖的具体使用场景"],
        }
        self.repo["en"] = {
            "tag": "A complete project positioning line",
            "what": "A complete explanation of what this repository does and who it helps.",
            "content": "A clear description of the modules, documentation, and examples included.",
            "stack": "A clear description of the technology stack and important dependencies.",
            "hot": "A durable explanation of why the project attracts developer attention.",
            "uses": ["Developers learning how the project works internally", "Teams evaluating the architecture and dependencies"],
        }
        self.assertEqual(UPDATE.validate(self.data, 1, 1, True, require_reviewed=True), [])

    def test_reviewed_gate_rejects_structurally_complete_but_thin_copy(self):
        self.repo["auto"] = False
        for locale in ("zh", "en"):
            self.repo[locale] = {
                "tag": "中文短句" if locale == "zh" else "Short tag",
                "what": "中文说明" if locale == "zh" else "Short explanation",
                "content": "中文内容" if locale == "zh" else "Short content",
                "stack": "中文技术" if locale == "zh" else "Short stack",
                "hot": "中文原因" if locale == "zh" else "Short reason",
                "uses": ["中文场景" if locale == "zh" else "Use case"],
            }
        errors = UPDATE.validate(self.data, 1, 1, True, require_reviewed=True)
        self.assertTrue(any("shorter than" in error for error in errors), errors)
        self.assertTrue(any("uses need at least 2" in error for error in errors), errors)

    def test_reviewed_gate_rejects_non_chinese_zh_copy(self):
        self.repo["auto"] = False
        for loc in ("zh", "en"):
            self.repo[loc]["content"] = "content"
            self.repo[loc]["uses"] = ["use case"]
        errors = UPDATE.validate(self.data, 1, 1, True, require_reviewed=True)
        self.assertTrue(any("reviewed tag has no Chinese text" in e for e in errors), errors)
        self.assertTrue(any("reviewed use case has no Chinese text" in e for e in errors), errors)

    def test_reviewed_gate_rejects_disguised_placeholder_copy(self):
        self.repo["auto"] = False
        self.repo["zh"] = {
            "tag": "项目描述待补充", "what": "中文项目介绍", "content": "中文仓库内容",
            "stack": "中文技术栈", "hot": "中文热度原因", "uses": ["中文应用场景"],
        }
        self.repo["en"]["content"] = "content"
        self.repo["en"]["uses"] = ["use case"]
        errors = UPDATE.validate(self.data, 1, 1, True, require_reviewed=True)
        self.assertTrue(any("reviewed placeholder text remains" in e for e in errors), errors)


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
