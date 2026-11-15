import unittest
from scripts.ev_counter_rule_history import fingerprint
from scripts.ev_engine_core import InvalidEpisode
from scripts.ev_observed_episode_provenance import validate_observed_episode, summarize_observed_episodes

def episode(**changes):
    rule=dict(id="rule1",version=1,source_id="owned",venue_id="hall1",
        machine_id="machine1",model_revision="rev1",counter_label="AT",
        event_label="start",valid_from="2026-01-01",valid_until="2026-12-31",
        counter_type="at_games",counter_origin="last_at_end",
        event_type="at_start",evidence_url="https://example.org/rule",
        review_status="verified")
    row=dict(episode_id="ep1",machine_id="machine1",model_revision="rev1",
        venue_id="hall1",date="2026-11-15",counter_type="at_games",
        counter_origin="last_at_end",counter_value=300,state="normal",
        state_evidence="observed",investment_yen=10000,return_yen=13000,
        exchange_basis="20yen_56medals",play_end_condition="after_at",
        completed=True,source_permission="user_owned",source_id="owned",
        source_url="https://example.org/episode",
        permission_evidence="https://example.org/permission",
        origin_evidence_url="https://example.org/rule",
        rule_snapshot=rule,
        rule_pin=dict(rule_id="rule1",rule_version=1,
                      source_id="owned",rule_fingerprint_sha256=fingerprint(rule)))
    row.update(changes)
    return row

class ObservedProvenanceTests(unittest.TestCase):
    def test_complete_observed_episode_accepted(self):
        self.assertEqual(validate_observed_episode(episode())["net_yen"],3000)
    def test_inferred_state_refused(self):
        with self.assertRaises(InvalidEpisode):
            validate_observed_episode(episode(state_evidence="inferred"))
    def test_simulated_state_refused(self):
        with self.assertRaises(InvalidEpisode):
            validate_observed_episode(episode(state_evidence="simulated"))
    def test_unknown_counter_origin_refused(self):
        with self.assertRaises(InvalidEpisode):
            validate_observed_episode(episode(counter_origin="unknown"))
    def test_missing_source_evidence_refused(self):
        with self.assertRaises(InvalidEpisode):
            validate_observed_episode(episode(source_url=""))
    def test_tampered_rule_snapshot_refused(self):
        r=episode()
        r["rule_snapshot"]=dict(r["rule_snapshot"],counter_origin="last_cz_end")
        with self.assertRaises(InvalidEpisode):
            validate_observed_episode(r)
    def test_mismatched_machine_refused(self):
        with self.assertRaises(InvalidEpisode):
            validate_observed_episode(episode(machine_id="machine2"))
    def test_expired_rule_refused(self):
        with self.assertRaises(InvalidEpisode):
            validate_observed_episode(episode(date="2027-01-01"))
    def test_public_hall_record_cannot_prove_player_payout(self):
        with self.assertRaises(InvalidEpisode):
            validate_observed_episode(episode(source_permission="manual_public_record"))
    def test_different_origins_never_pooled(self):
        r1=episode()
        r2=episode(episode_id="ep2",counter_origin="last_cz_end")
        rule2=dict(r2["rule_snapshot"],id="rule2",counter_origin="last_cz_end")
        r2["rule_snapshot"]=rule2
        r2["rule_pin"]=dict(rule_id="rule2",rule_version=1,
            source_id="owned",rule_fingerprint_sha256=fingerprint(rule2))
        summary=summarize_observed_episodes([r1,r2],min_samples=2)
        self.assertEqual(len(summary),2)
        self.assertTrue(all(not x["sample_threshold_met"] for x in summary))
    def test_duplicate_episode_rejected(self):
        with self.assertRaises(InvalidEpisode):
            summarize_observed_episodes([episode(),episode()])
    def test_mean_remains_research_only(self):
        summary=summarize_observed_episodes([episode(),episode(episode_id="ep2",return_yen=9000)],min_samples=2)
        self.assertEqual(summary[0]["mean_net_yen"],1000)
        self.assertEqual(summary[0]["publication_status"],"research_only")
        self.assertTrue(summary[0]["sample_threshold_met"])
    def test_incomplete_episode_refused(self):
        with self.assertRaises(InvalidEpisode):
            validate_observed_episode(episode(completed=False))
    def test_bool_min_samples_refused(self):
        with self.assertRaises(ValueError):
            summarize_observed_episodes([],min_samples=True)

if __name__=="__main__":
    unittest.main()
