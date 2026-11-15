"""Validate sourced editorial machine performance data without inventing win rates."""
from pathlib import Path
import json
import unittest

PATH = Path(__file__).resolve().parents[1] / "docs" / "editorial-machine-traits.json"

class EditorialMachineTraitsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(PATH.read_text(encoding="utf-8"))

    def test_unique_machine_ids(self):
        rows = self.data["records"]
        self.assertEqual(len(rows), len({row["machine_id"] for row in rows}))

    def test_specs_are_sourced(self):
        for row in self.data["records"]:
            for metric in row.get("published_specs", []):
                self.assertTrue(metric["source_url"].startswith("https://"))
                self.assertTrue(metric["verified_on"])
                self.assertTrue(metric["values"])

    def test_win_rates_require_real_samples(self):
        for row in self.data["records"]:
            for rate in row.get("setting_win_rates", []):
                self.assertIn(rate["setting"], ("1", "2", "3", "4", "5", "6"))
                self.assertGreater(rate["sample_size"], 0)
                self.assertTrue(rate["source_url"].startswith("https://"))
                self.assertTrue(rate["win_definition"])
                self.assertTrue(rate["session_duration"])

    def test_payouts_require_clear_denominator(self):
        for row in self.data["records"]:
            for payout in row.get("payout_per_entry", []):
                self.assertGreater(payout["sample_size"], 0)
                self.assertTrue(payout["source_url"].startswith("https://"))
                self.assertIn(payout["unit"], ("AT", "ST", "bonus"))
                self.assertTrue(payout["inclusion_scope"])

    def test_editorial_labels_must_be_approved(self):
        allowed = {label["id"] for label in self.data["editorial_labels"]}
        for row in self.data["records"]:
            self.assertTrue(set(row["editorial_assessment"]["labels"]) <= allowed)
            self.assertTrue(row["editorial_assessment"]["sources"])

if __name__ == "__main__":
    unittest.main()
