"""Synthetic contract adapter tests."""
import unittest
from scripts.ev_contract_adapters import AdapterError, observation_to_audit, estimate_to_comparison

def raw():
    return dict(source_id="source-A",venue_id="hall-A",machine_id="machine-A",
                model_revision="rev-A",machine_number="101",
                observed_date="2026-11-15",observed_at="2026-11-15T10:00:00+09:00",
                event_order=1,counter_value=350,
                evidence_url="https://example.org/observation")
def norm():
    return dict(source_id="source-A",venue_id="hall-A",machine_id="machine-A",
                model_revision="rev-A",observed_date="2026-11-15",
                review_status="verified",original_value=350,
                counter_type="at_games",counter_origin="last_at_end",
                event_type="at_start",evidence_url="https://example.org/rules")
def estimate():
    return dict(machine_id="machine-A",model_revision="rev-A",counter_type="at_games",
                counter_value=350,state="normal",exchange_basis="20yen",
                play_end_condition="next_at_end",sample_size=40,
                mean_net_yen=1000,state_evidence="observed",
                publication_status="research_only")

class ContractTests(unittest.TestCase):
    def test_normalizer_to_audit_preserves_observation_source(self):
        converted=observation_to_audit(raw(),norm())
        self.assertEqual(converted["source_url"],"https://example.org/observation")
        self.assertEqual(converted["counter_origin"],"last_at_end")
        self.assertEqual(converted["machine_number"],"101")
    def test_missing_time_or_identity_rejected(self):
        with self.assertRaises(AdapterError):
            observation_to_audit({k:v for k,v in raw().items() if k!="observed_at"},norm())
        with self.assertRaises(AdapterError):
            observation_to_audit(raw(),dict(norm(),venue_id="other"))
    def test_unmapped_rejected(self):
        with self.assertRaises(AdapterError):
            observation_to_audit(raw(),dict(norm(),review_status="unmapped"))
    def test_observation_date_must_match(self):
        with self.assertRaises(AdapterError):
            observation_to_audit(dict(raw(),observed_at="2026-11-16T10:00:00+09:00"),norm())
    def test_estimate_bridge(self):
        converted=estimate_to_comparison(estimate(),counter_origin="last_at_end",
                                         origin_evidence_url="https://example.org/rules")
        self.assertEqual(converted["provenance"],"observed_episodes")
        self.assertEqual(converted["counter_origin"],"last_at_end")
    def test_estimate_inferred_state_rejected(self):
        with self.assertRaises(AdapterError):
            estimate_to_comparison(dict(estimate(),state_evidence="inferred"),
                                   counter_origin="last_at_end",
                                   origin_evidence_url="https://example.org/rules")
    def test_estimate_without_origin_rejected(self):
        with self.assertRaises(AdapterError):
            estimate_to_comparison(estimate(),counter_origin="unknown",
                                   origin_evidence_url="https://example.org/rules")
if __name__=="__main__":
    unittest.main()
