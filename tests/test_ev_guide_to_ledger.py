"""Verify source-scoped EV guide and memo navigation."""
from pathlib import Path
import unittest

HTML=(Path(__file__).resolve().parents[1]/"docs"/"opportunities.html").read_text(encoding="utf-8")

class EvGuideToLedgerTest(unittest.TestCase):
 def test_profit_explainers_appear_with_ledger_not_targeting(self):
  self.assertLess(HTML.index('id="ledger-panel"'),HTML.index('class="profit-worksheet"'))
  self.assertLess(HTML.index('class="profit-worksheet"'),HTML.index('id="ledger-rows"'))
  self.assertIn('class="profit-explainer"',HTML)
 def test_guide_contains_scoped_known_value_and_unknown_cases(self):
  self.assertIn('0G〜・1周期目まで',HTML)
  self.assertIn('50G〜・1周期目まで',HTML)
  self.assertIn('value:1227',HTML)
  self.assertIn('value:null',HTML)
  self.assertIn('推奨開始ラインと断定したものではなく',HTML)
  self.assertIn('出典："+row.source',HTML)
 def test_memo_button_prefills_provenance_not_guessed_amount(self):
  self.assertIn('const form=$("play-note").closest("details")',HTML)
  self.assertIn('if(form)form.open=true',HTML)
  self.assertIn('row.value===null?"":String(row.value)',HTML)
  self.assertIn('btn.addEventListener("click",()=>openEstimateMemo(row))',HTML)
  self.assertIn('appendEstimateGuide(machine,sectionKey,top)',HTML)
 def test_no_ev_guessed_for_all_machines(self):
  self.assertIn('期待値（円）は調査中',HTML)
  self.assertIn('50G開始時点の金額は未登録',HTML)

if __name__=="__main__":
 unittest.main()
