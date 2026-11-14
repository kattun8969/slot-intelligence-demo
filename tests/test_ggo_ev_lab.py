"""Test isolated GGO experiment and site navigation without paid model copying."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class GGOCalculatorTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.lab=(ROOT/"docs"/"ggo-ev-lab.html").read_text(encoding="utf-8")
  cls.detail=(ROOT/"docs"/"opportunities.html").read_text(encoding="utf-8")
 def test_link_only_on_ggo(self):
  self.assertIn('id="ggo-lab-entry"',self.detail)
  self.assertIn('m.id!=="ggo"',self.detail)
  self.assertIn('href="./ggo-ev-lab.html"',self.detail)
 def test_not_a_real_betting_ev_calculator(self):
  self.assertIn('独自の検証用モデル',self.lab)
  self.assertIn('実機の期待値ではありません',self.lab)
  self.assertIn('id="ack"',self.lab)
  self.assertIn('if(!$("ack").checked)',self.lab)
  self.assertIn('goal==="at"?win*reward*exchange+(1-win)*next:0',self.lab)
 def test_status_uses_owned_model_inputs(self):
  for term in ('AT後のスルー回数','現在のボーナス間G数','50枚で回るG数','貸出単価','交換単価','感度テスト'):
   self.assertIn(term,self.lab)
if __name__=="__main__":
 unittest.main()
