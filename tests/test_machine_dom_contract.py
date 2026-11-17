"""Guard the required DOM shared by every public machine page."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class MachinePage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.machine = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "body":
            self.machine = attrs.get("data-machine")

class MachineDomContractTests(unittest.TestCase):
    def test_all_dedicated_pages_support_shared_renderer(self):
        source = (ROOT / "docs/machine-detail.js").read_text()
        required = set(re.findall(r"\$\('([^']+)'\)", source))
        self.assertIn("targets", required)
        self.assertIn("performance", required)
        pages = list((ROOT / "docs/machines").glob("*.html"))
        self.assertGreaterEqual(len(pages), 18)
        for path in pages:
            with self.subTest(machine=path.stem):
                page = MachinePage()
                page.feed(path.read_text())
                self.assertEqual(page.machine, path.stem)
                self.assertFalse(required - set(page.ids), f"Missing renderer IDs: {sorted(required - set(page.ids))}")
                self.assertFalse([key for key, n in Counter(page.ids).items() if n > 1], "Duplicate DOM IDs")
