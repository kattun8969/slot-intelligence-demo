import unittest
from scripts.ev_machine_rule_readiness import build_readiness, ReadinessError

def rule(**kw):
    r=dict(id="rule1",version=1,source_id="source",venue_id="venue",
           machine_id="machine",model_revision="rev",valid_from="2026-01-01",
           valid_until="2026-06-30",counter_label="AT interval",
           event_label="AT start",counter_type="at_games",
           counter_origin="last_at_end",event_type="at_start",
           evidence_url="https://example.org/verified",review_status="verified")
    r.update(kw)
    return r

class ReadinessTests(unittest.TestCase):
    def test_empty_registry_does_not_invent_machines(self):
        r=build_readiness({"schema":1,"rules":[]})
        self.assertEqual(r["registered_machines"],0)
        self.assertEqual(r["ev_publication_ready_count"],0)
    def test_verified_mapping_is_not_ev_ready(self):
        r=build_readiness({"schema":1,"rules":[rule()]})
        self.assertTrue(r["machines"][0]["mapping_ready"])
        self.assertFalse(r["machines"][0]["ev_publication_ready"])
        self.assertEqual(r["machines"][0]["usable_counter_types"],["at_games"])
    def test_pending_mapping_not_ready(self):
        r=build_readiness({"schema":1,"rules":[rule(review_status="pending")]})
        self.assertFalse(r["machines"][0]["mapping_ready"])
    def test_conflict_blocks_mapping(self):
        r=build_readiness({"schema":1,"rules":[rule(),rule(id="rule2",version=2)]})
        self.assertFalse(r["machines"][0]["mapping_ready"])
        self.assertEqual(r["machines"][0]["conflicting_rules"],2)
    def test_nonoverlapping_versions_accepted(self):
        r=build_readiness({"schema":1,"rules":[rule(),rule(id="rule2",version=2,valid_from="2026-07-01",valid_until="2026-12-31",counter_type="cz_games",counter_origin="last_cz_end")]})
        self.assertTrue(r["machines"][0]["mapping_ready"])
        self.assertEqual(r["machines"][0]["verified_rules"],2)
    def test_multiple_machines_separate(self):
        r=build_readiness({"schema":1,"rules":[rule(),rule(id="rule2",machine_id="another")]})
        self.assertEqual(r["registered_machines"],2)
    def test_rejected_not_usable(self):
        r=build_readiness({"schema":1,"rules":[rule(review_status="rejected")]})
        self.assertEqual(r["machines"][0]["usable_counter_types"],[])
    def test_expired_rule_not_currently_ready(self):
        r=build_readiness({"schema":1,"rules":[rule()]},as_of="2026-11-15")
        self.assertFalse(r["machines"][0]["mapping_ready"])
        self.assertEqual(r["machines"][0]["effective_verified_rules"],0)
        self.assertEqual(r["as_of"],"2026-11-15")
    def test_effective_rule_ready_on_boundary(self):
        r=build_readiness({"schema":1,"rules":[rule()]},as_of="2026-06-30")
        self.assertTrue(r["machines"][0]["mapping_ready"])
    def test_future_rule_not_currently_ready(self):
        r=build_readiness({"schema":1,"rules":[rule(valid_from="2027-01-01",valid_until="2027-12-31")]},as_of="2026-11-15")
        self.assertFalse(r["machines"][0]["mapping_ready"])
    def test_invalid_as_of_date_rejected(self):
        with self.assertRaises(ReadinessError):
            build_readiness({"schema":1,"rules":[]},as_of="2026-2-01")
    def test_historical_view_explicitly_labeled(self):
        r=build_readiness({"schema":1,"rules":[rule()]})
        self.assertEqual(r["readiness_scope"],"all_historical_rules")
    def test_schema_rejected(self):
        with self.assertRaises(ReadinessError):
            build_readiness({"schema":2,"rules":[]})
    def test_rule_validation_rejected(self):
        with self.assertRaises(ValueError):
            build_readiness({"schema":1,"rules":[rule(counter_type="invented")]})

if __name__=="__main__":
    unittest.main()
