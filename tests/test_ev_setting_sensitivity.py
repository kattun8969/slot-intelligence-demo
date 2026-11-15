import unittest
from scripts.ev_counter_rule_history import fingerprint
from scripts.ev_setting_sensitivity import analyze_setting_sensitivity, SensitivityError
from scripts.ev_engine_core import InvalidEpisode

def episode(i, setting=1, ret=2000, **kw):
    rule=dict(id="r",version=1,source_id="owned",venue_id="hall",machine_id="m",
        model_revision="v",counter_label="AT",event_label="start",
        valid_from="2026-01-01",valid_until="2026-12-31",
        counter_type="at_games",counter_origin="last_at_end",event_type="at_start",
        evidence_url="https://example.org/rule",review_status="verified")
    row=dict(episode_id=str(i),source_id="owned",machine_id="m",model_revision="v",
        venue_id="hall",date="2026-11-15",counter_type="at_games",
        counter_origin="last_at_end",counter_value=300,state="normal",
        state_evidence="observed",investment_yen=1000,return_yen=ret,
        exchange_basis="20yen",play_end_condition="after_at",completed=True,
        source_permission="user_owned",source_url="https://example.org/episode",
        permission_evidence="https://example.org/permission",
        origin_evidence_url="https://example.org/rule",rule_snapshot=rule,
        rule_pin=dict(rule_id="r",rule_version=1,source_id="owned",
                      rule_fingerprint_sha256=fingerprint(rule)),
        verified_setting=setting,setting_evidence_status="verified")
    row.update(kw)
    return row

class SettingSensitivityTests(unittest.TestCase):
    def test_weighted_scenario(self):
        rows=[episode(1,1,2000),episode(2,1,2000),episode(3,6,5000),episode(4,6,5000)]
        r=analyze_setting_sensitivity(rows,{"equal":{"1":.5,"6":.5}},min_per_setting=2)
        self.assertEqual(r["scenarios"][0]["weighted_observed_mean_yen"],2500)
        self.assertFalse(r["strategy_ev_verified"])
    def test_missing_setting_not_extrapolated(self):
        r=analyze_setting_sensitivity([episode(1),episode(2)],{"s":{"1":.5,"6":.5}},min_per_setting=2)
        self.assertIsNone(r["scenarios"][0]["weighted_observed_mean_yen"])
        self.assertEqual(r["scenarios"][0]["missing_settings"],["6"])
    def test_insufficient_setting_not_extrapolated(self):
        r=analyze_setting_sensitivity([episode(1)],{"s":{"1":1}},min_per_setting=2)
        self.assertFalse(r["scenarios"][0]["scenario_calculable"])
    def test_invalid_weight_sum(self):
        with self.assertRaises(SensitivityError):
            analyze_setting_sensitivity([],{"s":{"1":.7}})
    def test_bool_weight_rejected(self):
        with self.assertRaises(SensitivityError):
            analyze_setting_sensitivity([],{"s":{"1":True}})
    def test_unknown_setting_rejected(self):
        with self.assertRaises(SensitivityError):
            analyze_setting_sensitivity([episode(1,setting=0)],{"s":{"1":1}})
    def test_inferred_setting_rejected(self):
        with self.assertRaises(SensitivityError):
            analyze_setting_sensitivity([episode(1,setting_evidence_status="inferred")],{"s":{"1":1}})
    def test_mixed_conditions_rejected(self):
        with self.assertRaises(SensitivityError):
            analyze_setting_sensitivity([episode(1),episode(2,counter_value=400)],{"s":{"1":1}})
    def test_duplicate_rejected(self):
        with self.assertRaises(InvalidEpisode):
            analyze_setting_sensitivity([episode(1),episode(1)],{"s":{"1":1}})
    def test_invalid_minimum_rejected(self):
        with self.assertRaises(SensitivityError):
            analyze_setting_sensitivity([],{"s":{"1":1}},min_per_setting=True)
    def test_simulated_episode_rejected(self):
        with self.assertRaises(InvalidEpisode):
            analyze_setting_sensitivity([episode(1,state_evidence="simulated")],{"s":{"1":1}})
    def test_no_rows_not_calculable(self):
        r=analyze_setting_sensitivity([],{"s":{"1":1}})
        self.assertIsNone(r["scenarios"][0]["weighted_observed_mean_yen"])

if __name__=="__main__":
    unittest.main()
