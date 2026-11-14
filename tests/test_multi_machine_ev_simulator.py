"""Six-machine experimental calculator: integration and safety guardrails."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]/"docs"
class CalculatorTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.lab=(ROOT/"ev-simulator.html").read_text(encoding="utf-8")
  cls.site=(ROOT/"opportunities.html").read_text(encoding="utf-8")
 def test_six_machine_configs(self):
  for code in ["ggo","godeva2","garo","mahoako","lycoris","vivy"]:
   self.assertIn('id:"'+code+'"',self.lab)
   self.assertIn('"'+code+'"',self.site)
  self.assertIn("ボーナス間",self.lab)
  self.assertIn("CZ間",self.lab)
 def test_not_actual_ev(self):
  self.assertIn("実機の期待値",self.lab)
  self.assertIn('id="accept"',self.lab)
  self.assertIn('if(!$("accept").checked)',self.lab)
  self.assertIn("当選確率",self.lab)
  self.assertIn("仮の平均払出",self.lab)
 def test_trial_handoff_not_auto_save(self):
  self.assertIn("sessionStorage.setItem",self.lab)
  self.assertIn("slotintel-ev-transfer-v1",self.site)
  self.assertIn('$("played-status").value="not_played"',self.site)
  self.assertIn('$("manual-ev").value=String(row.ev)',self.site)
  self.assertIn('record.open=true',self.site)
  self.assertIn('href="./ev-simulator.html"',self.site)
 def test_bounded_inputs(self):
  for token in ["v.games<0","v.denom<1","v.base<=0","v.owned>100","v.win<0"]:
   self.assertIn(token,self.lab)
if __name__=="__main__":
 unittest.main()
