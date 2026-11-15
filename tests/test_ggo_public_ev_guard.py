"""Verify GGO public EV samples are not mixed across different SJ outcomes."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]/"docs"
class GgoPublicEVTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((ROOT/"public-ev-reference.json").read_text(encoding="utf-8"))
  cls.page=(ROOT/"public-ev-lookup.html").read_text(encoding="utf-8")
 def test_ggo_has_five_distinct_scenarios(self):
  rows=[x for x in self.data["scenarios"] if x["machine"]=="ggo"]
  self.assertEqual(len(rows),5)
  self.assertEqual(len({x["id"] for x in rows}),5)
  self.assertTrue(all(x["counter_origin"]=="data_counter" for x in rows))
  self.assertTrue(all(x["through_range"] and len(x["through_range"])==2 for x in rows))
  self.assertTrue(all("SJ" in x["label"] for x in rows))
  self.assertTrue(all(x["exit"] and x["price"]=="20円等価" for x in rows))
  self.assertTrue(all(len(x["points"])>=5 for x in rows))
 def test_no_confused_counter_or_missing_input(self):
  self.assertIn('id="counter-confirm"',self.page)
  self.assertIn('if(!$("counter-confirm").checked)',self.page)
  self.assertIn('raw===""?NaN:Number(raw)',self.page)
  self.assertIn("データカウンターG",self.page)
  self.assertIn('value="ggo"',self.page)
  self.assertIn('["monkey5","tokyoghoul","seiya","ragnador","vivy","ggo"].includes(id)',self.page)
if __name__=="__main__":
 unittest.main()
