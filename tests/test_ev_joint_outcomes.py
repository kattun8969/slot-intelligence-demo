"""Synthetic fixtures only: no machine predictions."""
import unittest
from scripts.ev_joint_outcomes import summarize_model

class JointOutcomeTests(unittest.TestCase):
    def run_model(self, rows):
        return summarize_model(rows, revision="test-v1", assumptions=["synthetic"], sources=["fixture"])
    def rows(self):
        return [
            dict(probability=.75, investment_yen=1000, return_yen=0, at_medals=0),
            dict(probability=.25, investment_yen=1000, return_yen=8000, at_medals=400)]
    def test_positive_ev_can_have_low_win_probability(self):
        r=self.run_model(self.rows())
        self.assertEqual(r["expected_net_yen"],1000)
        self.assertEqual(r["episode_win_probability"],.25)
        self.assertEqual(r["at_mean_medals"],100)
        self.assertEqual(r["at_median_medals"],0)
    def test_ties_are_not_wins_and_threshold_is_inclusive(self):
        r=self.run_model([dict(probability=1,investment_yen=20000,return_yen=20000,at_medals=1000)])
        self.assertEqual(r["episode_win_probability"],0)
        self.assertEqual(r["at_over_1000_probability"],1)
    def test_invalid_inputs_rejected(self):
        for value in (True, -1, float("nan"), float("inf")):
            for field in ("probability","investment_yen","return_yen","at_medals"):
                rows=self.rows()
                rows[0][field]=value
                with self.subTest(field=field,value=value),self.assertRaises(ValueError):
                    self.run_model(rows)
        with self.assertRaises(ValueError):
            self.run_model(self.rows()[:1])
    def test_metadata_and_order_invariance(self):
        a=self.run_model(self.rows())
        self.assertEqual(a,self.run_model(list(reversed(self.rows()))))
        self.assertEqual(a["evidence_kind"],"editorial_prediction")
        self.assertEqual(a["model_revision"],"test-v1")
        with self.assertRaises(ValueError):
            summarize_model(self.rows(),revision="",assumptions=["test"],sources=["fixture"])
