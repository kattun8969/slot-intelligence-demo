"""Unresolved distribution boundaries must never masquerade as per-entry metrics."""
import json
from pathlib import Path
import unittest

class ReportedPayoutDistributionTests(unittest.TestCase):
    def test_scope_separation_and_tail_denominator(self):
        data = json.loads((Path(__file__).resolve().parents[1] / 'docs/editorial-machine-traits.json').read_text())
        found = []
        for rec in data['records']:
            for m in rec.get('reported_payout_distributions', []):
                found.append(m)
                with self.subTest(machine=rec['machine_id']):
                    self.assertIs(m['entry_scope_confirmed'], False)
                    self.assertTrue(m['scope'])
                    self.assertTrue(m['period'])
                    self.assertTrue(m['source_url'].startswith('https://'))
                    self.assertTrue(m['verified_on'])
                    self.assertGreater(m['sample_size'], 0)
                    self.assertGreaterEqual(m['mean_medals'], 0)
                    self.assertGreaterEqual(m['median_medals'], 0)
                    self.assertGreaterEqual(m['over_1000_count'], 0)
                    self.assertLessEqual(m['over_1000_count'], m['sample_size'])
                    self.assertAlmostEqual(m['over_1000_rate_pct'], 100*m['over_1000_count']/m['sample_size'], delta=0.01)
                    self.assertNotIn(m, rec.get('payout_per_entry', []))
                    self.assertNotIn(m, rec.get('setting_win_rates', []))
        self.assertTrue(found)

if __name__ == '__main__':
    unittest.main()
