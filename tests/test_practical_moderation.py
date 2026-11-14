"""Practical candidate cards, honest EV, and reviewed-only community feed."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/"docs"

class PracticalAndModerationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.detail=(DOCS/"opportunities.html").read_text(encoding="utf-8")
  cls.alts=(DOCS/"alternatives.html").read_text(encoding="utf-8")
  cls.candidates=json.loads((DOCS/"practical-picks.json").read_text(encoding="utf-8"))
  cls.reviewed=json.loads((DOCS/"reviewed-field-reports.json").read_text(encoding="utf-8"))
 def test_realistic_picks_are_not_bogus_rankings(self):
  rows=self.candidates["items"]
  self.assertEqual(self.candidates["schema"],1)
  self.assertTrue({"monkey-reset","monkey-after-at"} <= {x["id"] for x in rows})
  for row in rows:
   self.assertTrue(row["source"].startswith("https://"))
   self.assertIsInstance(row["check"],list)
   self.assertTrue(row["stop"])
   self.assertTrue(row["ev_yen"] is None or isinstance(row["ev_yen"],int))
  self.assertIn("空き台の見つけやすさは未集計",self.detail)
  self.assertGreaterEqual(len(rows),20)
  self.assertGreaterEqual(len({x["machine"] for x in rows}),12)
  self.assertIn("人気順・空き台率のランキングではありません",self.alts)
 def test_checklist_explains_ceiling_and_memo_is_unified(self):
  self.assertIn("打つ前のチェック項目（天井・周期・示唆）",self.detail)
  self.assertIn("通常795G＋α／最大6周期",self.detail)
  self.assertIn('id="session-record"',self.detail)
  self.assertEqual(self.detail.count('summary>台の状態をメモする'),0)
  self.assertIn("実戦記録をつける（台の状態・期待値・結果）",self.detail)
  self.assertIn('id="detail-counter-value"',self.detail)
  self.assertIn('id="save-play"',self.detail)
 def test_moderation_is_reviewed_only(self):
  self.assertEqual(self.reviewed["schema"],1)
  self.assertEqual(self.reviewed["items"],[])
  self.assertIn("reviewed-field-reports.json",self.detail)
  self.assertIn('REVIEWED_REPORTS=data.items.filter',self.detail)
  self.assertIn("一般向けの報告受付は現在休止中",self.detail)
  self.assertNotIn("issues/new?template=field_report.yml",self.detail)
  self.assertFalse((ROOT/".github"/"ISSUE_TEMPLATE"/"field_report.yml").exists())
  self.assertIn('schema:1', (DOCS/"EDITORIAL_MODERATION.md").read_text(encoding="utf-8"))
 def test_alternative_cards_have_machine_detail_links(self):
  self.assertIn("COUNTER_TIPS",self.alts)
  self.assertIn("practical-picks.json",self.alts)
  self.assertIn('狙い目・やめどきを見る',self.alts)
if __name__=="__main__":
 unittest.main()
