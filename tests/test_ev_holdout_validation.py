"""Synthetic temporal holdout tests."""
import unittest
from scripts.ev_holdout_validation import validate_holdout, ValidationError

def episode(i=0, day="2026-11-01", **kw):
    row = dict(machine_id="machine-A",model_revision="rev-A",
               counter_type="at_games",counter_origin="last_at_end",
               counter_value=350,state="normal",exchange_basis="20yen",
               play_end_condition="until_at_end",venue_id="venue-1",
               episode_id=str(i),date=day,investment_yen=1000,
               return_yen=1500,completed=True,source_permission="user_owned")
    row.update(kw)
    return row

class HoldoutTests(unittest.TestCase):
    def test_strict_time_split(self):
        rows=[episode(i) for i in range(3)]
        rows += [episode(i+3,day="2026-11-15",return_yen=1000) for i in range(3)]
        report=validate_holdout(rows,split_date="2026-11-15",min_train=3,min_test=3)["groups"][0]
        self.assertEqual(report["train_mean_yen"],500)
        self.assertEqual(report["test_mean_yen"],0)
        self.assertEqual(report["holdout_difference_yen"],-500)
        self.assertTrue(report["minimum_samples_met"])
        self.assertEqual(report["validation_status"],"research_only")
    def test_conditions_never_mix(self):
        rows=[episode(1),episode(2,counter_origin="last_cz_end")]
        self.assertEqual(validate_holdout(rows,split_date="2026-11-15")["group_count"],2)
    def test_small_sample_is_not_verified(self):
        result=validate_holdout([episode(1)],split_date="2026-11-15")["groups"][0]
        self.assertEqual(result["validation_status"],"insufficient_samples")
        self.assertIsNone(result["test_mean_yen"])
    def test_rejects_duplicate_and_incomplete(self):
        with self.assertRaises(ValidationError):
            validate_holdout([episode(1),episode(1)],split_date="2026-11-15")
        with self.assertRaises(ValidationError):
            validate_holdout([episode(1,completed=False)],split_date="2026-11-15")
    def test_rejects_unapproved_source(self):
        with self.assertRaises(ValidationError):
            validate_holdout([episode(1,source_permission="scraped_without_review")],split_date="2026-11-15")
    def test_rejects_nonfinite_amount(self):
        with self.assertRaises(ValidationError):
            validate_holdout([episode(1,return_yen=float("nan"))],split_date="2026-11-15")
    def test_boundary_is_test_not_train(self):
        result=validate_holdout([episode(1,day="2026-11-15")],split_date="2026-11-15")["groups"][0]
        self.assertEqual(result["train_n"],0)
        self.assertEqual(result["test_n"],1)

if __name__ == "__main__":
    unittest.main()
