"""Integrated rule pinning through CSV, verified normalization and audit."""
import unittest
from scripts.ev_hall_csv_import import import_observations_csv
from scripts.ev_counter_normalizer import normalize
from scripts.ev_contract_adapters import observation_to_audit
from scripts.ev_episode_audit import audit_event_stream
from scripts.ev_csv_audit_bridge import process_csv_to_audit
from scripts.ev_counter_rule_history import pin_observation, verify_pinned_snapshot
from test_ev_signed_csv_integration import fixture, csv_rows

class PinnedIntegrationTests(unittest.TestCase):
    def test_verified_signed_event_pins_exact_rule(self):
        raw, rule = fixture()
        result = process_csv_to_audit(
            csv_rows(raw), rules=[rule], intake=import_observations_csv,
            normalize=normalize, to_audit=observation_to_audit,
            audit=audit_event_stream, pin_rule=pin_observation)
        self.assertEqual(result["audit_event_count"], 1)
        self.assertEqual(len(result["pinned_rule_snapshots"]), 1)
        pin = result["pinned_rule_snapshots"][0]
        self.assertTrue(verify_pinned_snapshot(pin, rule))
        self.assertEqual(pin["counter_origin"], "daily_open")
    def test_modified_rule_snapshot_fails_revalidation(self):
        raw, rule = fixture()
        result = process_csv_to_audit(
            csv_rows(raw), rules=[rule], intake=import_observations_csv,
            normalize=normalize, to_audit=observation_to_audit,
            audit=audit_event_stream, pin_rule=pin_observation)
        pin = result["pinned_rule_snapshots"][0]
        self.assertFalse(verify_pinned_snapshot(pin, dict(rule, evidence_url="https://example.org/changed")))
    def test_rule_conflict_quarantines_event(self):
        raw, rule = fixture()
        other = dict(rule, id="overlap", version=2)
        result = process_csv_to_audit(
            csv_rows(raw), rules=[rule, other], intake=import_observations_csv,
            normalize=normalize, to_audit=observation_to_audit,
            audit=audit_event_stream, pin_rule=pin_observation)
        self.assertEqual(result["audit_event_count"], 0)
        self.assertEqual(result["quarantined_count"], 1)
        self.assertEqual(result["pinned_rule_snapshots"], [])

if __name__ == "__main__":
    unittest.main()
