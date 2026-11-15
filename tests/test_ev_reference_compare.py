"""Exact-condition comparison tests; synthetic samples only."""
import unittest
from scripts.ev_reference_compare import compare_exact, ComparisonError

def base():
    return dict(machine_id="machine-A",model_revision="rev-A",
                counter_type="at_games",counter_origin="last_at_end",
                counter_value=350,state="normal",exchange_basis="20yen_equal",
                play_end_condition="next_at_end")
def ref(**kw):
    row=dict(base(),provenance="published_reference",ev_yen=1200,
             source_url="https://example.org/ev",checked_at="2026-11-15")
    row.update(kw)
    return row
def obs(**kw):
    row=dict(base(),provenance="observed_episodes",mean_net_yen=900,
             sample_size=100,publication_status="research_only")
    row.update(kw)
    return row

class ComparisonTests(unittest.TestCase):
    def test_exact_comparison(self):
        r=compare_exact([ref()],[obs()])
        self.assertEqual(r["comparison_count"],1)
        self.assertEqual(r["comparisons"][0]["difference_yen"],-300)
        self.assertFalse(r["interpolation_used"])
    def test_counter_origin_and_stop_rules_must_match(self):
        for change in (dict(counter_origin="last_cz_end"),
                       dict(play_end_condition="next_cz_end"),
                       dict(exchange_basis="56medals"),
                       dict(state="after_cz_failure"),
                       dict(model_revision="rev-B"),
                       dict(counter_value=351),
                       dict(counter_type="cz_games")):
            r=compare_exact([ref()],[obs(**change)])
            self.assertEqual(r["comparison_count"],0)
            self.assertEqual(r["unmatched"][0]["reason"],"no_exact_reference")
    def test_no_interpolation_or_duplicate_reference_selection(self):
        r=compare_exact([ref(),ref(source_url="https://example.org/other")],[obs()])
        self.assertEqual(r["unmatched"][0]["reason"],"ambiguous_reference")
    def test_rejects_simulated_observation(self):
        with self.assertRaises(ComparisonError):
            compare_exact([ref()],[obs(provenance="simulated")])
    def test_rejects_publicly_labeled_observation(self):
        with self.assertRaises(ComparisonError):
            compare_exact([ref()],[obs(publication_status="public")])
    def test_missing_reference_source_and_nonfinite(self):
        with self.assertRaises(ComparisonError):
            compare_exact([ref(source_url="")],[obs()])
        with self.assertRaises(ComparisonError):
            compare_exact([ref(ev_yen=float("nan"))],[obs()])
    def test_small_sample_not_hidden(self):
        r=compare_exact([ref()],[obs(sample_size=3)],min_samples=30)
        self.assertFalse(r["comparisons"][0]["sample_threshold_met"])
        self.assertEqual(r["publication_status"],"research_only")

if __name__=="__main__":
    unittest.main()
