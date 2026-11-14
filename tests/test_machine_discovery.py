"""Validate public slot-machine metadata scraping and safe auto-publication."""
import json
from pathlib import Path
import unittest
from scripts.collect_machine_updates import (
    LIST_URL, build, normalize_url, parse_catalog, parse_updates,
)

DOCS = Path(__file__).resolve().parents[1] / "docs"


class MachineDiscoveryTests(unittest.TestCase):
    def test_catalog_extracts_only_machine_detail_links(self):
        html = """
        <html><body>
          <a href="/machines/list_machine/slot.html">一覧</a>
          <a href="/machines/7463"><img alt="スマート沖スロ ハイハイシオサイRe">
          メーカー名：パイオニア</a>
          <a href="https://pachiseven.jp/machines/7493">ゴジラ対エヴァンゲリオン2
          メーカー名：ビスティ</a>
          <a href="/machines/7490">牙狼 闇を照らす者 メーカー名：サンセイ</a>
          <a href="/machines/7463">重複</a>
          <a href="http://evil.com/machines/9999">偽の別サイト</a>
          <a href="javascript:alert(1)">不正</a>
          <script><a href="/machines/6666">script内</a></script>
        </body></html>"""
        rows = parse_catalog(html)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["id"], "7463")
        self.assertEqual(rows[0]["maker"], "パイオニア")
        self.assertTrue(all(x["url"].startswith("https://pachiseven.jp/machines/") for x in rows))
        self.assertEqual(rows[1]["name"], "ゴジラ対エヴァンゲリオン2")

    def test_fail_closed_on_empty_or_wrong_page(self):
        with self.assertRaises(ValueError):
            parse_catalog('<a href="/machines/7412">台1</a>')
        self.assertIsNone(normalize_url("https://other-site.example/machines/7493"))
        self.assertIsNone(normalize_url("javascript:alert(1)"))

    def test_update_labels_date_and_deduplication(self):
        markup = """
        <a href="/machines/7463">2026.11.13　「天井機能」を更新</a>
        <a href="/machines/7463">2026.11.13　「天井機能」を更新</a>
        <a href="/machines/7493">2026.11.11　「設定差」を更新</a>
        <a href="/machines/7490">2026.19.44 異常な日付</a>
        <a href="/machines/7463">導入日：2026.11.16 スマスロXYZ メーカー名：A</a>"""
        rows = parse_updates(markup)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["date"], "2026-11-13")
        self.assertEqual(rows[0]["headline"], "「天井機能」を更新")

    def test_incremental_merge_preserves_first_seen(self):
        old = {
            "machines": [
                {"id": "7463", "name": "旧名称", "maker": "X",
                 "url": "https://pachiseven.jp/machines/7463", "first_seen": "2026-11-14"}
            ],
            "updates": [
                {"date": "2026-11-10", "headline": "以前の解析更新",
                 "url": "https://pachiseven.jp/machines/7463"}
            ]
        }
        catalog = [
            {"id": "7463", "name": "正式名称", "maker": "Y", "url": "https://pachiseven.jp/machines/7463"},
            {"id": "7493", "name": "ゴジエヴァ2", "maker": "ビスティ", "url": "https://pachiseven.jp/machines/7493"}
        ]
        updates = [{"date": "2026-11-13", "headline": "スペック更新", "url": "https://pachiseven.jp/machines/7493"}]
        result = build(old, catalog, updates, "2026-11-15")
        self.assertEqual(result["machines"][0]["first_seen"], "2026-11-14")
        self.assertEqual(result["machines"][1]["first_seen"], "2026-11-15")
        self.assertEqual(len(result["updates"]), 2)
        self.assertNotIn("ev_yen", str(result))
        self.assertEqual(build(result, catalog, updates, "2026-11-16"), result)

    def test_public_page_is_not_auto_betting_advice(self):
        page = (DOCS / "auto-machine-updates.html").read_text(encoding="utf-8")
        snapshot = json.loads((DOCS / "auto-machine-discovery.json").read_text(encoding="utf-8"))
        self.assertIn("期待値", page)
        self.assertIn("新台・解析更新", page)
        self.assertIn('fetch("./auto-machine-discovery.json"', page)
        self.assertIn('hostname==="pachiseven.jp"', page)
        self.assertTrue(snapshot["machines"])
        self.assertTrue(all("ev" not in row for row in snapshot["machines"]))

    def test_metadata_push_redeploys_to_pages(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "auto-machine-discovery.yml").read_text(encoding="utf-8")
        self.assertIn("actions/deploy-pages@v4", workflow)
        self.assertIn("steps.commit.outputs.changed == 'true'", workflow)
        self.assertIn("permissions:\n  contents: write\n  pages: write\n  id-token: write", workflow)


if __name__ == "__main__":
    unittest.main()
