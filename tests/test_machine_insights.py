"""Check Otome 5 1-cycle and Kabaneri setting insights remain source-scoped."""
from pathlib import Path
import json
import unittest

DOCS=Path(__file__).resolve().parents[1]/"docs"

class InsightTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.html=(DOCS/"opportunities.html").read_text(encoding="utf-8")
  cls.insights=json.loads((DOCS/"machine-insights.json").read_text(encoding="utf-8"))
  cls.picks=json.loads((DOCS/"practical-picks.json").read_text(encoding="utf-8"))
 def test_1cycle_ending_conditions_and_stop(self):
  o=next(x for x in self.insights["machines"] if x["machine"]=="otome5")
  self.assertIn("1周期目",o["title"])
  self.assertTrue(any(x["label"]=="ノブナガ（デフォルト）" and x["ev_yen"]<0 for x in o["conditions"]))
  self.assertTrue(any(x["label"]=="マサムネ＆ヒデヨシ" and x["ev_yen"]>0 for x in o["conditions"]))
  item=next(x for x in self.picks["items"] if x["id"]=="otome5-after-at-first-cycle")
  self.assertIn("百花繚乱チャンス5G",item["condition"])
  self.assertIn("1周期目",item["stop"])
  self.assertIn("192件",item["ev_basis"])
 def test_setting_clues_not_confused_with_ev(self):
  k=next(x for x in self.insights["machines"] if x["machine"]=="kabaneri")
  self.assertTrue(any("ボイス" in x["label"] for x in k["conditions"]))
  self.assertTrue(any("駿城" in x["label"] for x in k["conditions"]))
  self.assertTrue(any("ST終了画面" in x["label"] for x in k["conditions"]))
  self.assertTrue(all(x["ev_yen"] is None for x in k["conditions"]))
  self.assertIn("断定しない",k["note"])
 def test_sources_and_renderer(self):
  self.assertEqual(self.insights["schema"],1)
  for machine in self.insights["machines"]:
   for row in machine["conditions"]:
    self.assertTrue(row["url"].startswith("https://"))
    self.assertTrue(row["basis"])
  for marker in ["machine-insights.json","renderMachineInsights(m)","根拠・前提を見る","期待収支の掲載例："]:
   self.assertIn(marker,self.html)
if __name__=="__main__":
 unittest.main()
