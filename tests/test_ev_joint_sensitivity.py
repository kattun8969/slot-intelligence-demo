import unittest
from scripts.ev_joint_sensitivity import compare_scenarios

class SensitivityTests(unittest.TestCase):
    def scope(self):
        return dict(machine_id="synthetic",setting="unknown",counter="at_games",
                    start_condition="0G",end_condition="one AT",exchange="20yen equal")
    def scenario(self,name,payout):
        return dict(name=name,revision="fixture-v1",assumptions=["synthetic"],
                    sources=["fixture"],outcomes=[dict(probability=1,investment_yen=100,
                    return_yen=payout,at_medals=payout/20)])
    def test_ranges_and_scope(self):
        r=compare_scenarios([self.scenario("low",0),self.scenario("high",200)],scope=self.scope())
        self.assertEqual(r["ranges"]["expected_net_yen"],dict(low=-100,high=100))
        self.assertEqual(r["scope"]["setting"],"unknown")
        self.assertEqual(r["range_kind"],"assumption_sensitivity_not_confidence_interval")
    def test_invalid_scope_and_duplicate_name(self):
        with self.assertRaises(ValueError):
            compare_scenarios([self.scenario("one",0)],scope={})
        with self.assertRaises(ValueError):
            compare_scenarios([self.scenario("one",0),self.scenario("one",200)],scope=self.scope())
