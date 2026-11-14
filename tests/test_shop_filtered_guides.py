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
  self.assertEqual(len(expanded),38)
  self.assertEqual(len(set(expanded)),38)
  self.assertEqual(set(self.shop["installed"]) - set(expanded),set())
  self.assertEqual(set(expanded) - set(self.shop["installed"]),{"uminchu"})
  for machine_id in self.shop["installed"]:
   entry=expanded[machine_id]
   self.assertTrue(entry["ceiling"] and entry["zone"] and entry["other"],msg=machine_id)

 def test_shop_snapshot_is_reference_only_not_a_global_gate(self):
  for p in PAGES:
   page=self.pages[p]
   for banned in ("STORE_INSTALLED.has(","STORESHOP.has(","SHOP_INSTALLED.has("):
    self.assertNotIn(banned,page,msg=p)
  home=self.pages["index.html"]
  detail=self.pages["opportunities.html"]
  self.assertIn('function loadNoteMachineBacklog()',home)
  self.assertIn('function loadNoteMachineBacklog()',detail)
  self.assertIn('note-machine-backlog.json',home)
  self.assertIn('note-machine-backlog.json',detail)
  self.assertNotIn('楽園大宮店の機種名・略称で探す',home)
  self.assertNotIn('楽園大宮店での掲載台数',detail)

 def test_original_paid_content_not_copied(self):
  summary=(DOCS/"shop-note-extras.json").read_text(encoding="utf-8")
  self.assertLess(len(summary),16000)
  self.assertNotIn("有料部分です",summary)
  self.assertNotIn("前回AT３連以下",summary)

if __name__=="__main__":
 unittest.main()
