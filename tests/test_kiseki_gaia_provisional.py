"""Regressions for the provisional user-supplied Kiseki field hypotheses."""
import json
from pathlib import Path
import unittest
DOCS=Path(__file__).resolve().parents[1]/"docs"
class KisekiGaiaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((DOCS/"practical-picks.json").read_text(encoding="utf-8"))
        cls.page=(DOCS/"opportunities.html").read_text(encoding="utf-8")
    def test_four_distinct_conditional_play_options(self):
        rows=[x for x in self.data["items"] if x["machine"]=="kiseki"]
        self.assertEqual({x["id"] for x in rows},{"kiseki-reset","kiseki-red7","kiseki-cut","kiseki-single"})
        self.assertTrue(all(x["ev_yen"] is None for x in rows))
        self.assertTrue(all("暫定" in x["confidence"] for x in rows))
        self.assertTrue(all("確認" in " ".join(x["check"]) for x in rows))
    def test_published_sample_is_a_nonverified_observation(self):
        for token in ["32,123G","41.73G","107.368％","535.16","独立した検証","保証しません"]:
            self.assertIn(token,self.page)
        self.assertIn("appendKisekiGaiaNotes(root)",self.page)
        self.assertIn('machine.id==="kiseki"',self.page)
    def test_no_made_up_source_url(self):
        self.assertIn('if(row.source&&/^https:',self.page)
        self.assertIn("暫定考察（独立検証前）",self.page)
if __name__=="__main__":
    unittest.main()
