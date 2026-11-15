"""Event stream auditing tests; all records are synthetic."""
import unittest
from scripts.ev_episode_audit import audit_event_stream, EventStreamError

def event(order=1, **kwargs):
    data = dict(source_id="provider-a", venue_id="hall-1",
                machine_id="machine-1", model_revision="rev-A",
                machine_number="101", observed_at=f"2026-11-15T10:{order:02d}:00+09:00",
                event_order=order, event_type="at_start",
                counter_type="at_games", counter_value=100 + order * 10,
                counter_origin="last_at_end", review_status="verified",
                source_url="https://example.org/data")
    data.update(kwargs)
    return data

class EventStreamAuditTests(unittest.TestCase):
    def test_complete_events_still_not_ev(self):
        a=event(1)
        b=event(2,event_type="at_end")
        group=audit_event_stream([a,b])["groups"][0]
        self.assertFalse(group["ev_ready"])
        self.assertEqual(group["flags"],[])
    def test_unverified_and_claimed_runthrough_are_quarantined(self):
        a=event(1,review_status="unmapped")
        b=event(2,event_type="runthrough_claim")
        group=audit_event_stream([a,b])["groups"][0]
        self.assertIn("unverified_counter_mapping",group["flags"])
        self.assertIn("ambiguous_outcome_label",group["flags"])
        self.assertIn("right_censored_outcome",group["flags"])
    def test_counter_drop_not_assumed_to_be_reset(self):
        a=event(1,counter_value=350)
        b=event(2,counter_value=10,event_type="at_end")
        group=audit_event_stream([a,b])["groups"][0]
        self.assertIn("counter_decreased_without_verified_boundary",group["flags"])
    def test_unsorted_and_duplicate_are_flagged(self):
        a=event(1)
        b=event(2,event_type="at_end")
        group=audit_event_stream([b,a,a])["groups"][0]
        self.assertIn("out_of_order_input",group["flags"])
        self.assertIn("duplicate_event_identity",group["flags"])
    def test_separate_venues_and_models(self):
        a=event(1)
        b=event(2,venue_id="hall-2",event_type="at_end")
        c=event(3,model_revision="rev-B")
        self.assertEqual(audit_event_stream([a,b,c])["group_count"],3)
    def test_naive_timestamp_rejected(self):
        with self.assertRaises(EventStreamError):
            audit_event_stream([event(1,observed_at="2026-11-15T10:00:00")])
    def test_cross_day_and_long_gap(self):
        a=event(1)
        b=event(2,observed_at="2026-11-17T11:00:00+09:00",event_type="at_end")
        group=audit_event_stream([a,b])["groups"][0]
        self.assertIn("long_observation_gap",group["flags"])
        self.assertIn("cross_day_sequence_requires_venue_business_day_rules",group["flags"])
if __name__=="__main__":
    unittest.main()
