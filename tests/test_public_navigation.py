"""Public-site regression for full-card navigation and sourced field research."""
from pathlib import Path
import json
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]/"docs"

class PublicNavigationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.home=(ROOT/"index.html").read_text(encoding="utf-8")
  cls.detail=(ROOT/"opportunities.html").read_text(encoding="utf-8")
  cls.reports=json.loads((ROOT/"field-reports.json").read_text(encoding="utf-8"))

 def test_every_card_has_full_hit_target_and_clear_detail_button(self):
  for marker in (
   'entry.className="tile-hit"',
   'entry.href="./opportunities.html#machine="+encodeURIComponent(m.id)',
   'entry.setAttribute("aria-label",m.name+"の機種詳細・狙い方を開く")',
   '["機種詳細","./opportunities.html#machine="]',
   '.machine-tile .tile-links a{position:relative;z-index:2}',
   '.machine-tile .tile-hit{position:absolute;inset:0;z-index:1',
  ):
   self.assertIn(marker,self.home)
  self.assertIn('function selected(){return MACHINES.find(x=>x.id===location.hash.replace("#machine=",""))||null}',self.detail)

 def test_unverified_sources_are_separate_from_strategy(self):
  self.assertEqual(self.reports["schema"],2)
  items=self.reports["items"]
  self.assertGreaterEqual(len(items),9)
  self.assertEqual(len({x["id"] for x in items}),len(items))
  for record in items:
   self.assertTrue(record["url"].startswith("https://"))
   self.assertGreaterEqual(len(record["highlights"]),2)
   self.assertTrue(all(isinstance(x,str) and x for x in record["highlights"]))
   for field in ("machine","title","published_at","source","caution","kind","summary","headline","why_watch","verification","source_scope"):
    self.assertTrue(record[field])
  self.assertTrue({"monkey5","tokyoghoul","yoshimune","juoh","world","otome5"}<=set(x["machine"] for x in items))
  self.assertIn('FIELD_REPORTS=data.items.filter',self.detail)
  self.assertIn('FIELD_SCOPE_LABELS={',self.detail)
  self.assertIn('typeof x.verification==="string"',self.detail)
  self.assertIn('どんな人に役立つ？',self.detail)
  self.assertIn('item.source_scope==="channel_index"',self.detail)
  self.assertIn('if(data.schema!==2',self.detail)
  self.assertIn('for(const point of item.highlights',self.detail)
  self.assertIn('"未検証の点："+item.caution',self.detail)
  self.assertLess(self.detail.index('id="field-report-items"'),self.detail.index('id="detail-counter-value"'))

if __name__=="__main__":
 unittest.main()
