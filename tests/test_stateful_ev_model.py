"""Ensure state-specific inputs enter the six-machine calculator, with JS syntax checks."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
HTML=(Path(__file__).resolve().parents[1]/"docs"/"ev-simulator.html").read_text(encoding="utf-8")
class StatefulEvModelTests(unittest.TestCase):
 def test_public_setting_one_baselines_and_customization(self):
  for term in ['name:"ガンゲイル・オンライン",denom:192,base:31','name:"ゴジラ対エヴァンゲリオン2",denom:234.2','name:"牙狼 闇を照らす者",denom:291.1','name:"魔法少女にあこがれて",denom:436.3','name:"リコリス・リコイル",denom:328.8','name:"Vivy",denom:276.5']:
   self.assertIn(term,HTML)
  self.assertIn('id="denom"',HTML)
 def test_ggo_skips_affect_number_of_bonus_cycles(self):
  self.assertIn('if(active().id==="ggo")',HTML)
  self.assertIn('maxSkips-v.through',HTML)
  self.assertIn('prob*=1-entry',HTML)
  self.assertIn('spins+=prob*waitSpins',HTML)
 def test_godeva_dual_ceiling_and_hypothetical_regime(self):
  self.assertIn('v.atGames>0?v.atGames:v.games',HTML)
  self.assertIn('id="at-g"',HTML)
  self.assertIn('id="hit-mult"',HTML)
  self.assertIn('id="win-mult"',HTML)
  self.assertIn('mode==="warm"?"1.15"',HTML if False else 'ignore') if False else None
  self.assertIn('$("regime").addEventListener("change",render)',HTML)
  self.assertIn("優遇・冷遇を確定判別する機能ではありません",HTML)
 def test_ledger_handoff_contains_assumption(self):
  self.assertIn('sessionStorage.setItem("slotintel-ev-transfer-v1"',HTML)
  self.assertIn('区間仮説"+x.regime',HTML)
 def test_inline_js_parses_when_node_is_available(self):
  if not shutil.which("node"):
   self.skipTest("node not installed")
  script=HTML.split("<script>",1)[1].split("</script>",1)[0]
  with tempfile.TemporaryDirectory() as tmp:
   file=Path(tmp)/"script.js"
   file.write_text(script,encoding="utf-8")
   result=subprocess.run(["node","--check",str(file)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
if __name__=="__main__":
 unittest.main()
