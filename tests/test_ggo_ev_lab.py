"""Test isolated GGO experiment and site navigation without paid model copying."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class GGOCalculatorTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.lab=(ROOT/"docs"/"ggo-ev-lab.html").read_text(encoding="utf-8")
  cls.detail=(ROOT/"docs"/"opportunities.html").read_text(encoding="utf-8")
 def test_original_lab_retained_with_multi_machine_navigation(self):
  self.assertTrue((ROOT/"docs"/"ggo-ev-lab.html").exists())
  self.assertIn('id="ev-simulator-entry"',self.detail)
  self.assertIn('href="./ev-simulator.html"',self.detail)
  self.assertIn('"ggo"',self.detail)
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
