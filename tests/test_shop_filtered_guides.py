"""Verify the shop filter and full-HTML-derived editorial guide coverage."""
from pathlib import Path
import json
import re
import unittest

DOCS=Path(__file__).resolve().parents[1]/"docs"
PAGES=["index.html","opportunities.html","hints.html","hall-compare.html","strategy-cards.html","alternatives.html"]

class ShopFilteredGuidesTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.shop=json.loads((DOCS/"shop-inventory.json").read_text(encoding="utf-8"))
  cls.extras=json.loads((DOCS/"shop-note-extras.json").read_text(encoding="utf-8"))["machines"]
  cls.categories=json.loads((DOCS/"targeting-categories.json").read_text(encoding="utf-8"))["machine_guides"]
  cls.pages={p:(DOCS/p).read_text(encoding="utf-8") for p in PAGES}

 def test_store_scope_and_source_date(self):
  self.assertEqual(self.shop["schema"],1)
  self.assertEqual(self.shop["shop"]["name"],"楽園大宮店")
  self.assertEqual(self.shop["shop"]["observed_date"],"2026-11-12")
  self.assertIn("pekasen.com",self.shop["shop"]["inventory_source"])
  self.assertEqual(len(self.shop["installed"]),37)
  for id,count in self.shop["installed"].items():
   self.assertGreater(count,0,msg=id)
  self.assertEqual(self.shop["installed"]["monkey5"],33)
  self.assertEqual(self.shop["installed"]["tokyoghoul"],62)
  self.assertEqual(self.shop["installed"]["yoshimune"],10)
  for missing in ("sencolle5","uminchu","god"):
   self.assertNotIn(missing,self.shop["installed"])
   self.assertIn(missing,self.shop["excluded"])

 def test_new_full_html_note_guides_match_installed(self):
  self.assertEqual(len(self.extras),17)
  seen={m["id"] for m in self.extras}
  self.assertEqual(len(seen),17)
  self.assertTrue(seen <= set(self.shop["installed"]))
  expanded={g["machine"]:g for g in self.categories}
  for m in self.extras:
   self.assertEqual(expanded[m["id"]]["basis"],"owner_full_html_source")
   self.assertEqual(len(m["points"]),3)
   self.assertIn(m["name"],self.pages["index.html"])
   self.assertIn(m["name"],self.pages["opportunities.html"])
  self.assertEqual(len(expanded),27)

 def test_shop_gate_applies_to_each_visible_selector(self):
  home=self.pages["index.html"]; detail=self.pages["opportunities.html"]
  self.assertIn('STORE_INSTALLED.has(m.id)&&m.group',home)
  self.assertIn('STORE_INSTALLED.has(x.id)',home)
  self.assertIn('SHOP_INSTALLED.has(m.id)',detail)
  self.assertIn('&&SHOP_INSTALLED.has(x.id)',detail)
  self.assertIn('STORESHOP.has(x[0])',self.pages["hints.html"])
  self.assertIn('STORESHOP.has(x[0])',self.pages["hall-compare.html"])
  self.assertIn('STORE_INSTALLED.has(x[0])',self.pages["strategy-cards.html"])
  self.assertIn('STORE_INSTALLED.has(x[0])',self.pages["alternatives.html"])

 def test_original_paid_content_not_copied(self):
  summary=(DOCS/"shop-note-extras.json").read_text(encoding="utf-8")
  self.assertLess(len(summary),16000)
  self.assertNotIn("有料部分です",summary)
  self.assertNotIn("前回AT３連以下",summary)

if __name__=="__main__":
 unittest.main()
