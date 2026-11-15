import unittest
from scripts.ev_rule_change_impact import compare_rule_registries

def rule(**changes):
    r=dict(id="rule1",version=1,source_id="src",venue_id="hall",
           machine_id="machine",model_revision="rev",counter_label="AT",
           event_label="start",valid_from="2026-01-01",valid_until="2026-06-30",
           counter_type="at_games",counter_origin="last_at_end",
           event_type="at_start",evidence_url="https://example.org/rule",
           review_status="verified")
    r.update(changes)
    return r

def registry(*rules):
    return {"schema":1,"rules":list(rules)}

class RuleImpactTests(unittest.TestCase):
    def test_no_change(self):
        r=compare_rule_registries(registry(rule()),registry(rule()))
        self.assertFalse(r["requires_manual_review"])
        self.assertTrue(r["safe_to_reprocess_historical_data"])
    def test_future_version_added_requires_review_but_no_historical_block(self):
        r=compare_rule_registries(registry(rule()),registry(rule(),rule(version=2,valid_from="2026-07-01",valid_until="2026-12-31")))
        self.assertTrue(r["requires_manual_review"])
        self.assertFalse(r["historical_reinterpretation_blocked"])
    def test_changed_counter_origin_blocks(self):
        r=compare_rule_registries(registry(rule()),registry(rule(counter_origin="last_cz_end")))
        self.assertTrue(r["historical_reinterpretation_blocked"])
        self.assertEqual(r["changed"][0]["rule_id"],"rule1")
    def test_changed_evidence_blocks(self):
        r=compare_rule_registries(registry(rule()),registry(rule(evidence_url="https://example.org/other")))
        self.assertTrue(r["historical_reinterpretation_blocked"])
    def test_removed_version_blocks(self):
        r=compare_rule_registries(registry(rule()),registry())
        self.assertTrue(r["historical_reinterpretation_blocked"])
    def test_overlapping_new_version_blocks(self):
        r=compare_rule_registries(registry(rule()),registry(rule(),rule(version=2,valid_from="2026-06-01",valid_until="2026-12-31")))
        self.assertTrue(r["historical_reinterpretation_blocked"])
    def test_addition_in_other_machine_is_review_only(self):
        r=compare_rule_registries(registry(rule()),registry(rule(),rule(id="other",machine_id="other-machine")))
        self.assertFalse(r["historical_reinterpretation_blocked"])
    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError):
            compare_rule_registries(registry(),registry(rule(),rule()))
    def test_bad_registry_rejected(self):
        with self.assertRaises(ValueError):
            compare_rule_registries({"schema":2,"rules":[]},registry())
    def test_changed_review_status_blocks(self):
        r=compare_rule_registries(registry(rule()),registry(rule(review_status="pending")))
        self.assertTrue(r["historical_reinterpretation_blocked"])

if __name__=="__main__":
    unittest.main()
