"""PDF-inspired, non-reproduced machine-guide integration checks."""
from pathlib import Path
import json
import re
import unittest

DOCS=Path(__file__).resolve().parents[1]/"docs"
NEW={"godeva2","garo","ragnador","vivy","uminchu"}
PDF_LIST={"seiya","ggo","godeva2","garo","ragnador","vivy","uminchu","mahoako","juoh","sunbreak"}


class PDFGuideTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.home=(DOCS/"index.html").read_text(encoding="utf-8")
  cls.detail=(DOCS/"opportunities.html").read_text(encoding="utf-8")
  cls.hints=(DOCS/"hints.html").read_text(encoding="utf-8")
  cls.hall=(DOCS/"hall-compare.html").read_text(encoding="utf-8")
  cls.guides=json.loads((DOCS/"targeting-categories.json").read_text(encoding="utf-8"))

 def test_pdf_table_of_contents_is_covered(self):
  self.assertEqual(self.guides["schema"],1)
  records={x["machine"]:x for x in self.guides["machine_guides"]}
  self.assertTrue(PDF_LIST <= set(records))
  for m in NEW:
   for page in (self.home,self.detail,self.hints,self.hall):
    self.assertIn('"'+m+'"',page)
  self.assertIn('"ラグナドール"',self.home)
  self.assertIn('"Lウミンチュ"',self.home)

 def test_three_source_bounded_categories(self):
  for r in self.guides["machine_guides"]:
   for category in ("ceiling","zone","other"):
    self.assertIsInstance(r[category],list)
    self.assertTrue(r[category])
   self.assertTrue(r["source_notice"])
   self.assertIn(r["basis"],{"pdf_summary","toc_only","toc_plus_external","owner_full_html_source"})
  records={x["machine"]:x for x in self.guides["machine_guides"]}
  self.assertEqual(records["vivy"]["basis"],"owner_full_html_source")
  self.assertEqual(records["uminchu"]["basis"],"toc_plus_external")
  self.assertEqual(records["godeva2"]["basis"],"owner_full_html_source")
  self.assertNotIn("PDF原本の全内容",self.guides["description"])

 def test_machine_page_leads_with_targeting_before_numbers_and_notes(self):
  self.assertLess(self.detail.index('id="targeting-categories"'),self.detail.index('id="strategy-source-summary"'))
  self.assertLess(self.detail.index('id="category-guide-content"'),self.detail.index('id="detail-counter-value"'))
  for part in ('天井狙い','ゾーン狙い','特殊狙い','showTargetingCategories(m);','loadTargetingCategories();','targeting-categories.json'):
   self.assertIn(part,self.detail)
  self.assertIn('sourceComparison.textContent=isNew?',self.detail)
  self.assertIn('linkBase=title==="狙い目"&&newGuide',self.home)

if __name__=="__main__":
 unittest.main()
