"""Research EV core tests: no assumptions about individual machine pages."""
import unittest

from scripts.ev_engine_core import InvalidEpisode, summarize_episodes, validate_episode


def sample(i=0):
    return {
        "episode_id": str(i), "machine_id": "demo-machine",
        "model_revision": "revision-A", "venue_id": "test-venue",
        "date": "2026-11-15", "counter_type": "at_games",
        "counter_value": 300, "state": "normal",
        "state_evidence": "observed", "investment_yen": 1000,
        "return_yen": 1800, "exchange_basis": "20-yen-equivalent",
        "play_end_condition": "until_next_AT_end",
        "completed": True, "source_permission": "user_owned",
    }


class EVCoreTests(unittest.TestCase):
    def test_net_from_actual_cash_flows(self):
        self.assertEqual(validate_episode(sample())["net_yen"], 800)

    def test_one_episode_never_claims_confident_ev(self):
        result = summarize_episodes([sample()])[0]
        self.assertEqual(result["sample_size"], 1)
        self.assertFalse(result["sample_threshold_met"])
        self.assertIsNone(result["ci95_low_yen"])
        self.assertEqual(result["publication_status"], "research_only")

    def test_grouping_respects_counter_state_and_exit(self):
        a, b, c = sample(1), sample(2), sample(3)
        b["counter_type"] = "cz_games"
        c["play_end_condition"] = "until_next_CZ"
        self.assertEqual(len(summarize_episodes([a,b,c])), 3)

    def test_rejects_unverified_hidden_state(self):
        a = sample()
        a["state"] = "runthrough_verified"
        a["state_evidence"] = "inferred"
        with self.assertRaises(InvalidEpisode):
            validate_episode(a)

    def test_rejects_censored_observation(self):
        a = sample()
        a["completed"] = False
        with self.assertRaises(InvalidEpisode):
            validate_episode(a)

    def test_rejects_unknown_source(self):
        a = sample()
        a["source_permission"] = "unreviewed_scrape"
        with self.assertRaises(InvalidEpisode):
            validate_episode(a)

    def test_rejects_duplicate_episode(self):
        with self.assertRaises(InvalidEpisode):
            summarize_episodes([sample(1),sample(1)])

    def test_mean_and_interval_not_confused_with_truth(self):
        a,b = sample(1),sample(2)
        b["return_yen"] = 1000
        r = summarize_episodes([a,b],min_samples=2)[0]
        self.assertEqual(r["mean_net_yen"],400)
        self.assertTrue(r["sample_threshold_met"])
        self.assertEqual(r["publication_status"],"research_only")
        self.assertIsNotNone(r["standard_error_yen"])

    def test_invalid_input_and_counter_type(self):
        for value in (-1, float("nan"), True):
            a=sample()
            a["investment_yen"]=value
            with self.assertRaises(InvalidEpisode):
                validate_episode(a)
        a=sample()
        a["counter_type"]="unverified_bonus_count"
        with self.assertRaises(InvalidEpisode):
            validate_episode(a)


if __name__ == "__main__":
    unittest.main()
