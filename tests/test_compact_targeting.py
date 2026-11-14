"""The first-screen targeting overview must be short and traceable."""
from pathlib import Path
import json
import unittest

DOCS=Path(__file__).resolve().parents[1]/"docs"

class CompactTargetingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.html=(DOCS/"opportunities.html").read_text(encoding="utf-8")
  cls.public=json.loads((DOCS/"public-target-lines.json").read_text(encoding="utf-8"))
  cls.sourced=json.loads((DOCS/"source-thresholds.json").read_text(encoding="utf-8"))

 def test_no_duplicate_full_comparison_on_first_screen(self):
  a=self.html
  self.assertIn('<details id="all-source-details"',a)
  self.assertIn('解析サイト別の掲載値をすべて比較',a)
  self.assertIn('className="compact-target"',a)
  self.assertIn('className="compact-other"',a)
  self.assertIn('function bestCompactGroup(lines)',a)
  self.assertIn('function compactRange(group)',a)
  self.assertIn('group.sources.size',a)
  self.assertNotIn('この考察の掲載元noteを見る（詳細・有料部分あり）',a)
  self.assertNotIn('出典の扱い："+entry.source_notice',a)

 def test_missing_numbers_have_clear_date_and_no_invented_values(self):
  a=self.html
  self.assertIn('現在解析情報なし（数値の掲載例は未登録）',a)
  self.assertIn('登録資料の最終照合：2026年11月14日',a)
  self.assertIn('SNS・動画を含む網羅的な調査完了を意味しません',a)
  self.assertIn('||{ceiling:[],zone:[],other:[]}',a)
  self.assertIn('row.display',a)
  self.assertIn('/(天井|以内|到達濃厚)/',a)

 def test_no_mixed_conditions_or_units_for_ranges(self):
  a=self.html
  self.assertIn('const key=[scenario,value.unit,value.exchange].join("|")',a)
  self.assertIn('const scenario=scenarioOf(row)',a)
  self.assertIn('b.sources.size-a.sources.size',a)
  self.assertIn('同じ起点・交換条件での掲載目安に差があります',a)
  self.assertNotIn('function averageTarget',a)

 def test_zone_and_special_sourced_examples(self):
  rows=self.public["items"]
  ids={r["id"] for r in rows}
  for id in ("tokyo-arima-cz100","tokyo-ghoul-eyecatch100",
             "shinuchi-cycle-5","shinuchi-sword-9",
             "monkey-first-cycle222","monkey-short-state495"):
   self.assertIn(id,ids)
  for r in rows:
   self.assertTrue(r["url"].startswith("https://"))
   self.assertTrue(r["warning"])
  self.assertEqual(len(self.sourced["rows"]),63)
  self.assertEqual(len(rows),14)

if __name__=="__main__":
 unittest.main()
