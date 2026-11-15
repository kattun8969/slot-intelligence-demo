import unittest
from scripts.ev_counter_rule_history import fingerprint
from scripts.ev_selection_bias_audit import audit_sampling, SamplingAuditError
from scripts.ev_engine_core import InvalidEpisode

def episode(n):
    rule=dict(id="rule1",version=1,source_id="owned",venue_id="hall",
        machine_id="machine",model_revision="rev",counter_label="AT",
        event_label="start",valid_from="2026-01-01",valid_until="2026-12-31",
        counter_type="at_games",counter_origin="last_at_end",event_type="at_start",
        evidence_url="https://example.org/rule",review_status="verified")
    return dict(episode_id=str(n),source_id="owned",machine_id="machine",
        model_revision="rev",venue_id="hall",date="2026-11-15",
        counter_type="at_games",counter_origin="last_at_end",counter_value=300,
        state="normal",state_evidence="observed",investment_yen=1000,
        return_yen=2000,exchange_basis="20yen_56medals",play_end_condition="after_at",
        completed=True,source_permission="user_owned",
        source_url="https://example.org/episode",
        permission_evidence="https://example.org/permission",
        origin_evidence_url="https://example.org/rule",rule_snapshot=rule,
        rule_pin=dict(rule_id="rule1",rule_version=1,source_id="owned",
            rule_fingerprint_sha256=fingerprint(rule)))

def manifest(**kw):
    m=dict(capture_method="consecutive_all_eligible",eligible_episode_count=2,
        setting_distribution_status="verified",capture_protocol_predeclared=True,
        all_outcomes_reported=True)
    m.update(kw)
    return m

class SamplingAuditTests(unittest.TestCase):
    def test_complete_capture_is_not_strategy_ev(self):
        r=audit_sampling([episode(1),episode(2)],manifest(),min_samples=2)
        self.assertTrue(r["basic_sampling_checks_passed"])
        self.assertFalse(r["strategy_ev_verified"])
    def test_selected_winners_flagged(self):
        r=audit_sampling([episode(1),episode(2)],manifest(capture_method="selected_winners"),min_samples=2)
        self.assertIn("selection_prone_capture_method",r["sampling_warnings"])
    def test_voluntary_submission_flagged(self):
        r=audit_sampling([episode(1),episode(2)],manifest(capture_method="voluntary_submission"),min_samples=2)
        self.assertFalse(r["basic_sampling_checks_passed"])
    def test_missing_episodes_flagged(self):
        r=audit_sampling([episode(1)],manifest(),min_samples=2)
        self.assertIn("unobserved_eligible_episodes",r["sampling_warnings"])
    def test_unknown_setting_distribution_flagged(self):
        r=audit_sampling([episode(1),episode(2)],manifest(setting_distribution_status="unknown"),min_samples=2)
        self.assertIn("setting_distribution_unverified",r["sampling_warnings"])
    def test_unregistered_protocol_flagged(self):
        r=audit_sampling([episode(1),episode(2)],manifest(capture_protocol_predeclared=False),min_samples=2)
        self.assertIn("capture_protocol_not_predeclared",r["sampling_warnings"])
    def test_missing_outcomes_flagged(self):
        r=audit_sampling([episode(1),episode(2)],manifest(all_outcomes_reported=False),min_samples=2)
        self.assertIn("outcome_reporting_not_complete",r["sampling_warnings"])
    def test_excess_records_rejected(self):
        with self.assertRaises(SamplingAuditError):
            audit_sampling([episode(1),episode(2)],manifest(eligible_episode_count=1),min_samples=2)
    def test_duplicate_records_rejected(self):
        with self.assertRaises(InvalidEpisode):
            audit_sampling([episode(1),episode(1)],manifest(),min_samples=2)
    def test_simulation_rejected(self):
        r=episode(1)
        r["state_evidence"]="simulated"
        with self.assertRaises(InvalidEpisode):
            audit_sampling([r],manifest(),min_samples=2)
    def test_empty_manifest_flagged(self):
        r=audit_sampling([],manifest(eligible_episode_count=0),min_samples=2)
        self.assertIn("empty_eligible_population",r["sampling_warnings"])
    def test_bool_eligible_count_rejected(self):
        with self.assertRaises(SamplingAuditError):
            audit_sampling([],manifest(eligible_episode_count=True))
    def test_missing_protocol_flag_rejected(self):
        m=manifest()
        del m["capture_protocol_predeclared"]
        with self.assertRaises(SamplingAuditError):
            audit_sampling([],m)
    def test_min_samples_bool_rejected(self):
        with self.assertRaises(SamplingAuditError):
            audit_sampling([],manifest(),min_samples=True)

if __name__=="__main__":
    unittest.main()
