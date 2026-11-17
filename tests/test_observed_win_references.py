"""Keep presumed-setting samples separate from confirmed setting profit rates."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ObservedWinReferences(unittest.TestCase):
    def test_observation_counts_conditions_and_metric_separation(self):
        data = json.loads((ROOT / 'docs/editorial-machine-traits.json').read_text())
        observations = [(r, m) for r in data['records'] for m in r.get('reference_metrics', []) if m.get('metric_kind') == 'observed_positive_day_rate']
        self.assertTrue(observations)
        for rec, m in observations:
            with self.subTest(machine=rec['machine_id']):
                self.assertGreater(m['sample_units'], 0)
                self.assertGreaterEqual(m['positive_units'], 0)
                self.assertLessEqual(m['positive_units'], m['sample_units'])
                self.assertAlmostEqual(m['value'], 100 * m['positive_units'] / m['sample_units'], delta=0.05)
                for field in ['setting_status', 'win_definition', 'period', 'duration', 'exchange', 'source_url', 'source_type', 'verified_on', 'note']:
                    self.assertTrue(m.get(field), field)
                self.assertNotIn(m, rec.get('setting_win_rates', []))
                self.assertNotIn(m, rec.get('payout_per_entry', []))

if __name__ == '__main__':
    unittest.main()
