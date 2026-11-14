"""Site-wide machine catalog and unverified note roster stay independent of one shop."""
from pathlib import Path
import json
import re
import unittest

DOCS=Path(__file__).resolve().parents[1]/"docs"

class FullMachineCatalogTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.roster=json.loads((DOCS/"note-machine-backlog.json").read_text(encoding="utf-8"))
  cls.home=(DOCS/"index.html").read_text(encoding="utf-8")
  cls.detail=(DOCS/"opportunities.html").read_text(encoding="utf-8")
  cls.shop=json.loads((DOCS/"shop-inventory.json").read_text(encoding="utf-8"))

 def test_full_note_added_as_unverified_research_index(self):
  self.assertEqual(self.roster["schema"],1)
  self.assertEqual(len(self.roster["machines"]),159)
  ids={x["id"] for x in self.roster["machines"]}
  self.assertEqual(len(ids),159)
  self.assertTrue(all(re.fullmatch(r"note-\d{3}",x["id"]) for x in self.roster["machines"]))
  self.assertTrue(all(x["status"]=="research_pending" for x in self.roster["machines"]))
  labels=[x["name"] for x in self.roster["machines"]]
  for required in ("スマスロ ストリートファイター6","スマスロ 鉄拳6","押忍！番長０","スマスロ バイオハザードRE:3"):
   self.assertTrue(any(required.replace(" ","") in n.replace(" ","") for n in labels),msg=required)
  self.assertNotIn("真打吉宗",labels)
  self.assertNotIn("戦国コレクション6",labels)

 def test_all_catalog_search_and_status_disclosure(self):
  self.assertIn('connect-src \'self\'',self.home)
  self.assertIn('const CATALOG_GROUPS=[',self.home)
  self.assertIn('key:"archive"',self.home)
  self.assertIn('catalog-research-fold',self.home)
  self.assertIn('fetch("./note-machine-backlog.json"',self.home)
  self.assertIn('DISCOVERY.push({id:m.id',self.home)
  self.assertIn('fetch("./note-machine-backlog.json"',self.detail)
  self.assertIn('MACHINES.push({id:entry.id',self.detail)
  self.assertIn('tier:9,uncertain:true',self.detail)
  self.assertIn('正確な型式・解析・狙い目・示唆は未調査',self.detail)
  self.assertIn('m.id.startsWith("note-")',self.detail)
  self.assertIn('m.aliases||[]',self.detail)

 def test_shop_snapshot_not_used_as_default_filter(self):
  for page in (self.home,self.detail):
   self.assertNotIn("SHOP_INSTALLED.has(",page)
   self.assertNotIn("STORE_INSTALLED.has(",page)
   self.assertNotIn("楽園大宮店の機種名・略称で探す",page)
  self.assertEqual(self.shop["shop"]["name"],"楽園大宮店")
  self.assertEqual(self.shop["shop"]["observed_date"],"2026-11-12")
  self.assertIn("store",self.shop["shop"]["inventory_source"]) # future optional store filter

if __name__=="__main__":
 unittest.main()
