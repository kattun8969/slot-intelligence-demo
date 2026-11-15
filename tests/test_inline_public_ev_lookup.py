"""Inline public EV lookup and independent experimental simulator are both retained."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"docs"
class InlinePublicEvTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.page=(ROOT/"opportunities.html").read_text(encoding="utf-8")
 def test_inline_inputs_and_onpage_memo(self):
  for target in ["quick-ev-condition","quick-ev-games","quick-ev-result","quick-ev-memo","public-ev-reference.json","renderInlinePublicEV(m)","saveInlineEVToMemo"]:
   self.assertIn(target,self.page)
  self.assertIn('$("manual-ev").value=String(data.amount)',self.page)
  self.assertIn('$("played-status").value="not_played"',self.page)
  self.assertIn("線形補間した参考値",self.page)
 def test_experimental_calculator_still_separate(self):
  self.assertTrue((ROOT/"ev-simulator.html").exists())
  self.assertIn('id="ev-simulator-entry"',self.page)
  self.assertIn('href="./ev-simulator.html"',self.page)
 def test_scope_and_no_extrapolation(self):
  self.assertIn('g<p[0][0]||g>p[p.length-1][0]',self.page)
  self.assertIn('["monkey5","tokyoghoul","seiya","ragnador","vivy"]',self.page)
  self.assertIn("この機種の公開期待値表はまだ照合できていません",self.page)
if __name__=="__main__":
 unittest.main()
