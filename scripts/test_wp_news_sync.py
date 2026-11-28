"""Offline safety tests for WordPress news draft staging."""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parent / "wp_news_sync.py"
spec = importlib.util.spec_from_file_location("wp_news_sync", MODULE_PATH)
wp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wp)


class NewsDraftValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.queue = self.root / "wordpress-queue" / "news"
        self.queue.mkdir(parents=True)
        self._original_root, self._original_queue = wp.ROOT, wp.QUEUE
        wp.ROOT, wp.QUEUE = self.root, self.queue

        def restore():
            wp.ROOT, wp.QUEUE = self._original_root, self._original_queue
        self.addCleanup(restore)
        self.article = {
            "slug": "news-test-story-20261126",
            "title": "テスト記事",
            "content_html": "<p>独自記事</p>",
            "source_url": "https://example.org/press",
            "source_checked_at": "2026-11-26",
            "announced_on": "2026-11-24",
            "editor_reviewed": True,
        }

    def write(self, name="test.json"):
        path = self.queue / name
        path.write_text(json.dumps(self.article, ensure_ascii=False), encoding="utf-8")
        return str(path.relative_to(self.root))

    def test_accepts_editor_reviewed_article(self):
        self.assertEqual(wp.read_article(self.write())["slug"], "news-test-story-20261126")

    def test_rejects_unreviewed_article(self):
        self.article["editor_reviewed"] = False
        with self.assertRaises(ValueError):
            wp.read_article(self.write())

    def test_rejects_script(self):
        self.article["content_html"] = "<script>alert(1)</script>"
        with self.assertRaises(ValueError):
            wp.read_article(self.write())

    def test_rejects_event_handler_html(self):
        self.article["content_html"] = '<p onclick="alert(1)">本文</p>'
        with self.assertRaises(ValueError):
            wp.read_article(self.write())

    def test_rejects_javascript_link(self):
        self.article["content_html"] = '<a href="javascript:alert(1)">本文</a>'
        with self.assertRaises(ValueError):
            wp.read_article(self.write())

    def test_rejects_invalid_calendar_date(self):
        self.article["announced_on"] = "2026-02-30"
        with self.assertRaises(ValueError):
            wp.read_article(self.write())

    def test_rejects_http_source(self):
        self.article["source_url"] = "http://example.org/press"
        with self.assertRaises(ValueError):
            wp.read_article(self.write())

    def test_rejects_bad_slug(self):
        self.article["slug"] = "not-a-news-slug"
        with self.assertRaises(ValueError):
            wp.read_article(self.write())

    def test_duplicate_slug_never_posts(self):
        filename = self.write()
        with patch.object(wp, "verify_front_page_not_duplicate", return_value=True), \
                patch.object(wp, "verify_manual_news_not_duplicate", return_value=True), \
                patch.object(sys, "argv", ["wp_news_sync.py", "--file", filename]), \
                patch.dict(os.environ, {"WP_BASE_URL": "https://kajiplus.info",
                                        "WP_USERNAME": "test", "WP_APP_PASSWORD": "fake"}), \
                patch.object(wp, "request", side_effect=[
                    (200, {"id": 1}), (200, [{"id": 100, "status": "publish"}])
                ]) as mock_request:
            wp.main()
        self.assertEqual(mock_request.call_count, 2)
        self.assertFalse(any(call.kwargs.get("method") == "POST" or
                             (len(call.args) >= 4 and call.args[3] == "POST")
                             for call in mock_request.call_args_list))

    def test_creates_draft_only_and_verifies_it(self):
        filename = self.write()
        with patch.object(wp, "verify_front_page_not_duplicate", return_value=True), \
                patch.object(wp, "verify_manual_news_not_duplicate", return_value=True), \
                patch.object(sys, "argv", ["wp_news_sync.py", "--file", filename]), \
                patch.dict(os.environ, {"WP_BASE_URL": "https://kajiplus.info",
                                        "WP_USERNAME": "test", "WP_APP_PASSWORD": "fake"}), \
                patch.object(wp, "request", side_effect=[
                    (200, {"id": 1}), (200, []),
                    (201, {"id": 100, "status": "draft"}),
                    (200, {"id": 100, "status": "draft", "slug": self.article["slug"]}),
                ]) as mock_request:
            wp.main()
        self.assertEqual(mock_request.call_count, 4)
        post_call = mock_request.call_args_list[2]
        self.assertEqual(post_call.args[3], "POST")
        self.assertEqual(post_call.args[4]["status"], "draft")

    def test_non_draft_response_is_not_accepted(self):
        filename = self.write()
        with patch.object(wp, "verify_front_page_not_duplicate", return_value=True), \
                patch.object(wp, "verify_manual_news_not_duplicate", return_value=True), \
                patch.object(sys, "argv", ["wp_news_sync.py", "--file", filename]), \
                patch.dict(os.environ, {"WP_BASE_URL": "https://kajiplus.info",
                                        "WP_USERNAME": "test", "WP_APP_PASSWORD": "fake"}), \
                patch.object(wp, "request", side_effect=[
                    (200, {"id": 1}), (200, []),
                    (201, {"id": 100, "status": "publish"}),
                ]):
            with self.assertRaises(RuntimeError):
                wp.main()

    def test_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            wp.read_article("../../secrets.json")



    def test_manual_news_duplicate_slug_prevents_staging(self):
        with patch.object(wp, "request", return_value=(200, [{"id": 7}])) as mocked:
            self.assertFalse(wp.verify_manual_news_not_duplicate("https://kajiplus.info", "fake", self.article))
        self.assertIn("minna_news_edit?", mocked.call_args.args[2])
        self.assertIn("status=any", mocked.call_args.args[2])

    def test_manual_news_duplicate_title_prevents_staging(self):
        with patch.object(wp, "request", side_effect=[(200, []), (200, [{"title": {"raw": self.article["title"]}}])]):
            self.assertFalse(wp.verify_manual_news_not_duplicate("https://kajiplus.info", "fake", self.article))

    def test_manual_news_unavailable_fails_closed(self):
        with patch.object(wp, "request", return_value=(200, {"code": "rest_forbidden"})):
            with self.assertRaises(RuntimeError):
                wp.verify_manual_news_not_duplicate("https://kajiplus.info", "fake", self.article)

    def test_main_never_posts_when_manual_news_has_match(self):
        filename = self.write()
        with patch.object(wp, "verify_front_page_not_duplicate", return_value=True), \
                patch.object(sys, "argv", ["wp_news_sync.py", "--file", filename]), \
                patch.dict(os.environ, {"WP_BASE_URL": "https://kajiplus.info", "WP_USERNAME": "test", "WP_APP_PASSWORD": "fake"}), \
                patch.object(wp, "request", side_effect=[(200, {"id": 1}), (200, []), (200, [{"id": 7}])]) as mocked:
            wp.main()
        self.assertEqual(mocked.call_count, 3)
        self.assertTrue(all(len(call.args) == 3 for call in mocked.call_args_list))

    def test_front_page_duplicate_slug_prevents_staging(self):
        story = dict(self.article)
        with patch.object(wp, "request", side_effect=[
                (200, {"show_on_front": "page", "page_on_front": 12}),
                (200, {"content": {"raw": '<section id="news-test-story-20261126">Published</section>'}}),
                ]):
            self.assertFalse(wp.verify_front_page_not_duplicate("https://kajiplus.info", "fake", story))

    def test_front_page_unavailable_fails_closed(self):
        with patch.object(wp, "request", return_value=(200, {"show_on_front": "posts"})):
            with self.assertRaises(RuntimeError):
                wp.verify_front_page_not_duplicate("https://kajiplus.info", "fake", self.article)

    def test_front_page_clean_allows_draft_staging(self):
        with patch.object(wp, "request", side_effect=[
                (200, {"show_on_front": "page", "page_on_front": 12}),
                (200, {"content": {"raw": '<p>Other existing news</p>'}}),
                ]):
            self.assertTrue(wp.verify_front_page_not_duplicate("https://kajiplus.info", "fake", self.article))

if __name__ == "__main__":
    unittest.main()
