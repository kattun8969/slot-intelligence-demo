"""Source-backed hint cards must retain machine identity and provenance."""
import json
from pathlib import Path
import unittest
from urllib.parse import urlparse

class HintReferenceIntegrityTests(unittest.TestCase):
    def test_cards_keep_unique_identity_and_traceable_source(self):
        path = Path(__file__).resolve().parents[1] / 'docs/machine-hint-references.json'
        rows = json.loads(path.read_text(encoding='utf-8'))['guides']
        self.assertTrue(rows)
        keys = [(r['machine'], r['title']) for r in rows]
        self.assertEqual(len(keys), len(set(keys)))
        for r in rows:
            with self.subTest(machine=r['machine'], title=r['title']):
                for key in ['machine', 'title', 'meaning', 'url', 'asof']:
                    self.assertTrue(isinstance(r.get(key), str) and r[key].strip(), key)
                url = urlparse(r['url'])
                self.assertEqual(url.scheme, 'https')
                self.assertTrue(url.netloc)
                if r.get('placement') == 'target':
                    self.assertTrue(r.get('evidence_kind'))
                if r.get('cached'):
                    self.assertTrue(r['cached'].startswith('./assets/hints/'))
                    self.assertNotIn('..', r['cached'].split('/'))

if __name__ == '__main__':
    unittest.main()
