"""Offline safety tests for WordPress news draft staging."""
import importlib.util
import json
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

    def test_rejects_http_source(self):
        self.article["source_url"] = "http://example.org/press"
        with self.assertRaises(ValueError):
            wp.read_article(self.write())

    def test_rejects_bad_slug(self):
        self.article["slug"] = "not-a-news-slug"
        with self.assertRaises(ValueError):
            wp.read_article(self.write())

    def test_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            wp.read_article("../../secrets.json")


if __name__ == "__main__":
    unittest.main()
