"""Validate the research hypothesis, not its real-world predictive accuracy."""
import json
from pathlib import Path
import unittest

class MonkeyCalibrationTests(unittest.TestCase):
    def test_published_aggregate_constraints(self):
        d=json.loads((Path(__file__).resolve().parents[1]/"data/ev/monkey5-payout-calibration.json").read_text())
        rows=d["support"]
        self.assertAlmostEqual(sum(r["probability"] for r in rows),1)
        self.assertTrue(all(r["probability"]>=0 and r["at_medals"]>=0 for r in rows))
        target=d["observed_constraints"]
        self.assertAlmostEqual(sum(r["probability"]*r["at_medals"] for r in rows),target["mean_medals"])
        cumulative=0
        for r in sorted(rows,key=lambda r:r["at_medals"]):
            cumulative+=r["probability"]
            if cumulative>=.5:
                self.assertEqual(r["at_medals"],target["median_medals"])
                break
        for threshold in (1000,2000,3000):
            self.assertAlmostEqual(sum(r["probability"] for r in rows if r["at_medals"]>=threshold),
                                   target[f"over_{threshold}_probability"])
        self.assertEqual(d["status"],"research_only")
        self.assertTrue(d["assumptions"])
        self.assertTrue(d["unidentified"])
        self.assertNotIn("expected_net_yen",d)
        self.assertNotIn("setting_win_rates",d)
