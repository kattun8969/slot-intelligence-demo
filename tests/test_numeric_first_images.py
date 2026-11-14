"""Key image and numeric-targeting claims remain sourced and model specific."""
from pathlib import Path
import json
import unittest

DOCS=Path(__file__).resolve().parents[1]/"docs"
class NumericFirstAndImagesTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.home=(DOCS/"index.html").read_text(encoding="utf-8")
  cls.detail=(DOCS/"opportunities.html").read_text(encoding="utf-8")
  cls.data=json.loads((DOCS/"public-target-lines.json").read_text(encoding="utf-8"))
  cls.sources=json.loads((DOCS/"source-thresholds.json").read_text(encoding="utf-8"))
  cls.images=json.loads((DOCS/"machine-image-sources.json").read_text(encoding="utf-8"))

 def test_redundant_home_sections_removed(self):
  self.assertNotIn('<h2>この画面でできること</h2>',self.home)
  self.assertNotIn('<h2>狙い目のある機種を探す</h2>',self.home)
  self.assertNotIn('<h2>本公開までに追加するもの</h2>',self.home)
  self.assertIn('id="catalog-groups"',self.home)
  self.assertIn('id="entry"',self.home)

 def test_model_correct_photo_fallback(self):
  photos={x["path"] for x in self.images["images"]}
  for model in ("monkey5","monhun","juoh","lycoris","tokyoghoul","kabaneri","yoshimune","tensei2","otome5"):
   self.assertIn("machines/"+model+".webp",photos)
  self.assertIn('photo:"https://image.nana-press.com/kaiseki/machine/1160/',self.home)
  self.assertIn('img.src="./assets/machines/"+m.id+".webp"',self.home)
  self.assertIn('img.addEventListener("error"',self.home)

 def test_actual_numbers_and_sources_are_displayed_in_guide(self):
  self.assertEqual(self.data["schema"],1)
  rows=self.data["items"]
  self.assertEqual(len(rows),14)
  self.assertEqual(len(self.sources["rows"]),63)
  for r in rows:
   self.assertTrue(r["url"].startswith("https://"))
   self.assertGreaterEqual(r["value"],0)
   self.assertIn(r["category"],("ceiling","zone","other"))
   self.assertIn(r["unit"],("G","pt","周期"))
   self.assertTrue(r["source"] and r["context"] and r["warning"])
  self.assertIn('populateTargetNumbers(machine,key,title,figures)',self.detail)
  self.assertIn('loadAdditionalLines();',self.detail)
  self.assertIn('const lines=[...FIRST_SOURCE_ROWS,...ADDITIONAL_LINES]',self.detail)
  self.assertIn('targetNumber(row)',self.detail)
  self.assertIn('元資料を開く',self.detail)

 def test_conflicting_sites_are_not_averaged(self):
  monkey={r["id"]:r["value"] for r in self.data["items"] if r["machine"]=="monkey5"}
  self.assertEqual(monkey["monkey5-haienavi-table400"],400)
  self.assertEqual(monkey["monkey5-setting-equal"],500)
  table=next(x for x in self.data["items"] if x["id"]=="monkey5-haienavi-table400")
  self.assertIn("表の一例",table["display"])
  self.assertIn("開始ボーダーではない",table["kind"])
  tokyo={(r["source"],r["label"]):r["value"] for r in self.data["items"] if r["machine"]=="tokyoghoul"}
  self.assertEqual(tokyo[("なな徹","AT間狙い・等価")],550)
  self.assertEqual(tokyo[("スロベース","AT間狙い・等価")],650)

if __name__=="__main__":
 unittest.main()
