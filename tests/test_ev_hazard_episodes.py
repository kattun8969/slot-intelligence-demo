import unittest
from scripts.ev_hazard_episodes import build_episodes
from scripts.ev_joint_outcomes import summarize_model
class HazardTests(unittest.TestCase):
    def test_two_game_ceiling(self):
        rows=build_episodes([.5,1],[dict(probability=1,at_medals=10)],yen_per_game=100,yen_per_medal=20)
        self.assertEqual([r["probability"] for r in rows],[.5,.5])
        self.assertEqual([r["investment_yen"] for r in rows],[100,200])
        r=summarize_model(rows,revision="fixture",assumptions=["independence"],sources=["synthetic"])
        self.assertEqual(r["expected_net_yen"],50)
        self.assertEqual(r["episode_win_probability"],.5)
    def test_no_hits_before_ceiling(self):
        rows=build_episodes([0,0,1],[dict(probability=1,at_medals=10)],yen_per_game=1,yen_per_medal=20)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["investment_yen"],3)
    def test_rejects_missing_ceiling_and_invalid_probability(self):
        for hazards in ([],[.5],[2,1],[float("nan"),1]):
            with self.assertRaises(ValueError):
                build_episodes(hazards,[dict(probability=1,at_medals=1)],yen_per_game=1,yen_per_medal=20)
