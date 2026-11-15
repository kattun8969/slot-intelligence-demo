"""Counter normalization regression tests. Synthetic fixtures only."""
import unittest
from scripts.ev_counter_normalizer import normalize, validate_rule, RuleError

def raw(**kw):
    r=dict(source_id="hall-a",venue_id="venue-01",machine_id="ggo",
           model_revision="rev-1",observed_date="2026-11-14",
           counter_label="現在G",event_label="大当り",counter_value=350,
           evidence_url="https://example.org/record")
    r.update(kw)
    return r

def rule(**kw):
    r=dict(id="hall-a-ggo-v1",version=1,source_id="hall-a",
           venue_id="venue-01",machine_id="ggo",model_revision="rev-1",
           valid_from="2026-01-01",valid_until="2026-12-31",
           counter_label="現在G",event_label="大当り",
           counter_type="bonus_games",counter_origin="last_bonus_end",
           event_type="bonus",evidence_url="https://example.org/counter-guide",
           review_status="verified")
    r.update(kw)
    return r

class NormalizationTests(unittest.TestCase):
    def test_unmapped_does_not_guess(self):
        r=normalize(raw(),[])
        self.assertEqual(r.review_status,"unmapped")
        self.assertEqual(r.counter_type,"unknown")
        self.assertEqual(r.state,"unverified")
    def test_verified_rule_keeps_original_and_origin(self):
        r=normalize(raw(),[rule()])
        self.assertEqual(r.review_status,"verified")
        self.assertEqual(r.original_counter_label,"現在G")
        self.assertEqual(r.counter_origin,"last_bonus_end")
        self.assertEqual(r.counter_type,"bonus_games")
        self.assertEqual(r.state,"unverified")
    def test_unreviewed_rule_not_applied(self):
        self.assertEqual(normalize(raw(),[rule(review_status="pending")]).review_status,"unmapped")
    def test_other_venue_and_revision_never_cross_map(self):
        for change in (dict(venue_id="venue-02"),dict(model_revision="rev-2"),
                       dict(source_id="hall-b"),dict(observed_date="2027-01-01")):
            self.assertEqual(normalize(raw(**change),[rule()]).review_status,"unmapped")
    def test_overlapping_rules_quarantined(self):
        r=normalize(raw(),[rule(),rule(id="hall-a-ggo-v2",version=2)])
        self.assertEqual(r.review_status,"ambiguous")
        self.assertEqual(r.counter_type,"unknown")
        self.assertIsNone(r.rule_id)
    def test_claimed_runthrough_is_not_confirmed_state(self):
        r=normalize(raw(event_label="単発"),[rule(event_label="単発",event_type="single_hit_claim")])
        self.assertEqual(r.event_type,"single_hit_claim")
        self.assertEqual(r.state,"unverified")
    def test_invalid_rule_and_raw(self):
        with self.assertRaises(RuleError):
            validate_rule(rule(counter_origin="unknown"))
        with self.assertRaises(RuleError):
            validate_rule(rule(valid_from="2027-01-01"))
        with self.assertRaises(RuleError):
            normalize(raw(counter_value=-1),[])
        with self.assertRaises(RuleError):
            normalize(raw(counter_value=True),[])

if __name__=="__main__":
    unittest.main()
