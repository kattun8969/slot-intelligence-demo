import unittest
from scripts.ev_counter_rule_history import (
    RuleHistoryError, fingerprint, review_registry, pin_observation,
    verify_pinned_snapshot,
)

def rule(**changes):
    r=dict(id="fixture-rule",version=1,source_id="source",venue_id="hall",
           machine_id="machine",model_revision="rev",counter_label="AT interval",
           event_label="AT start",valid_from="2026-01-01",valid_until="2026-06-30",
           counter_type="at_games",counter_origin="last_at_end",
           event_type="at_start",evidence_url="https://example.org/rule",
           review_status="verified")
    r.update(changes)
    return r

def raw():
    return dict(source_id="source",venue_id="hall",machine_id="machine",
                model_revision="rev",counter_label="AT interval",
                event_label="AT start",observed_date="2026-05-01",
                counter_value=350,source_record_id="observation-1")

def normalized():
    return dict(review_status="verified",rule_id="fixture-rule",
                rule_version=1,counter_type="at_games",
                counter_origin="last_at_end",event_type="at_start",
                original_value=350)

class RuleHistoryTests(unittest.TestCase):
    def test_nonoverlap_versioned_rules(self):
        a=rule()
        b=rule(version=2,valid_from="2026-07-01",valid_until="2026-12-31")
        self.assertTrue(review_registry([a,b])["ready"])
    def test_overlapping_verified_versions_flagged(self):
        a=rule()
        b=rule(version=2,valid_from="2026-06-01",valid_until="2026-12-31")
        report=review_registry([a,b])
        self.assertFalse(report["ready"])
        self.assertEqual(len(report["conflicts"]),1)
    def test_same_rule_id_version_rejected(self):
        with self.assertRaises(RuleHistoryError):
            review_registry([rule(),rule()])
    def test_pending_overlap_not_activated(self):
        self.assertTrue(review_registry([rule(),rule(version=2,review_status="pending")])["ready"])
    def test_rule_hash_stable_across_key_order(self):
        r=rule()
        self.assertEqual(fingerprint(r),fingerprint(dict(reversed(list(r.items())))))
    def test_pin_and_verify(self):
        r=rule()
        pin=pin_observation(raw(),normalized(),[r])
        self.assertTrue(verify_pinned_snapshot(pin,r))
        self.assertEqual(pin["rule_version"],1)
    def test_changed_evidence_does_not_verify(self):
        r=rule()
        pin=pin_observation(raw(),normalized(),[r])
        self.assertFalse(verify_pinned_snapshot(pin,rule(evidence_url="https://example.org/changed")))
    def test_changed_semantics_does_not_verify(self):
        r=rule()
        pin=pin_observation(raw(),normalized(),[r])
        self.assertFalse(verify_pinned_snapshot(pin,rule(counter_type="cz_games")))
    def test_pinned_version_missing_fails(self):
        with self.assertRaises(RuleHistoryError):
            pin_observation(raw(),normalized(),[rule(version=2)])
    def test_outside_effective_date_fails(self):
        x=raw()
        x["observed_date"]="2026-07-01"
        with self.assertRaises(RuleHistoryError):
            pin_observation(x,normalized(),[rule()])
    def test_identity_mismatch_fails(self):
        x=raw()
        x["venue_id"]="other-hall"
        with self.assertRaises(RuleHistoryError):
            pin_observation(x,normalized(),[rule()])
    def test_semantics_mismatch_fails(self):
        x=normalized()
        x["counter_origin"]="last_cz_end"
        with self.assertRaises(RuleHistoryError):
            pin_observation(raw(),x,[rule()])
    def test_conflicted_registry_blocks_pin(self):
        with self.assertRaises(RuleHistoryError):
            pin_observation(raw(),normalized(),[rule(),rule(version=2)])
    def test_rejected_rule_cannot_pin(self):
        with self.assertRaises(RuleHistoryError):
            pin_observation(raw(),normalized(),[rule(review_status="rejected")])

if __name__=="__main__":
    unittest.main()
