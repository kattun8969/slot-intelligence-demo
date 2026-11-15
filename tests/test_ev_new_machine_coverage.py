import unittest
from datetime import date
from scripts.ev_new_machine_coverage import coverage, valid_scenario

def scenario(**kwargs):
    s={"id":"v1","machine":"vivy","label":"通常AT間","counter":"at","state":"normal",
       "exit":"AT後","price":"20円等価","source_name":"source",
       "url":"https://example.org/reference","checked_at":"2026-11-15",
       "preconditions":["通常"],"points":[[100,-100],[200,300]]}
    s.update(kwargs)
    return s

class CoverageTests(unittest.TestCase):
    def test_valid_reference(self):
        self.assertTrue(valid_scenario(scenario()))
    def test_missing_end_condition(self):
        self.assertFalse(valid_scenario(scenario(exit="")))
    def test_bad_points(self):
        self.assertFalse(valid_scenario(scenario(points=[[200,1],[100,2]])))
    def test_non_https(self):
        self.assertFalse(valid_scenario(scenario(url="http://example.org")))
    def test_no_scenario_is_not_published(self):
        r=coverage({"machines":[{"id":"7489","name":"Vivy","url":"https://example.org","first_seen":"2026-11-15"}]},
                   {"scenarios":[scenario()]},as_of=date(2026,11,15))
        self.assertTrue(r["machines"][0]["reference_rows_available"])
        self.assertFalse(r["machines"][0]["machine_page_table_verified"])
        self.assertEqual(r["live_machine_tables_verified_count"],0)
    def test_unknown_machine_needs_research(self):
        r=coverage({"machines":[{"id":"9999","name":"Other","url":"https://example.org","first_seen":"2026-11-15"}]},
                   {"scenarios":[scenario()]},as_of=date(2026,11,15))
        self.assertTrue(r["machines"][0]["needs_source_research"])
    def test_24h_warning(self):
        r=coverage({"machines":[{"id":"7489","name":"Vivy","url":"https://example.org","first_seen":"2026-11-13"}]},
                   {"scenarios":[scenario()]},as_of=date(2026,11,15))
        self.assertTrue(r["machines"][0]["target_24h_exceeded"])
    def test_duplicate_catalog_id(self):
        row={"id":"7489","name":"Vivy","url":"https://example.org","first_seen":"2026-11-15"}
        with self.assertRaises(ValueError):
            coverage({"machines":[row,row]},{"scenarios":[]},as_of=date(2026,11,15))

if __name__=="__main__":
    unittest.main()
