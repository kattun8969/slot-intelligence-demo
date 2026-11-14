"""A cycle limit is not automatically a start threshold; nominal RTP is not yen profit."""
from pathlib import Path
import json
import unittest
DOCS=Path(__file__).resolve().parents[1]/"docs"

class ActionableLinesTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.lines={x["id"]:x for x in json.loads((DOCS/"public-target-lines.json").read_text(encoding="utf-8"))["items"]}
  cls.html=(DOCS/"opportunities.html").read_text(encoding="utf-8")

 def test_yoshimune_5th_cycle_only_starts_at_0g_within_5th_cycle(self):
  a=self.lines["shinuchi-cycle-5"]
  self.assertTrue(a["actionable"])
  self.assertEqual(a["value"],0)
  self.assertEqual(a["unit"],"周期内G")
  self.assertIn("5周期目",a["startBasis"])
  self.assertIn("AT後0G",a["context"])
  self.assertIn("通常A",a["warning"])

 def test_monkey_first_cycle_is_0g_after_at_not_start_at_222pt(self):
  a=self.lines["monkey-first-cycle222"]
  b=self.lines["monkey1-222-cycle-limit"]
  self.assertTrue(a["actionable"])
  self.assertEqual(a["value"],0)
  self.assertEqual(a["unit"],"G")
  self.assertIn("AT終了後 0G",a["display"])
  self.assertFalse(b["actionable"])
  self.assertEqual(b["value"],222)
  self.assertIn("開始ラインではない",b["kind"])
  self.assertIn("actionable===false",self.html)
  self.assertIn("r.actionable===true",self.html)

 def test_expectation_math_explained_as_example_not_guarantee(self):
  a=self.html
  for text in ("機械割105％","総投入10,000円","＋500円","総投入100,000円","＋5,000円",
               "期待収益（円）","現金投資は別","期待値がプラスでも負ける"):
   self.assertIn(text,a)
  self.assertIn("<details class=\"profit-explainer\">",a)

 def test_unverified_social_numbers_not_fabricated(self):
  self.assertIn("出典不明のSNS情報も調査対象",self.html)
  for row in self.lines.values():
   self.assertTrue(row["source"])
   self.assertTrue(row["url"].startswith("https://"))
   self.assertIn(row["category"],("ceiling","zone","other"))

if __name__=="__main__":
 unittest.main()
