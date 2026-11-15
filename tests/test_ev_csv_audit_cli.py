import csv
import io
import unittest
from scripts.ev_csv_audit_cli import inspect_csv
from scripts.ev_hall_csv_import import FIELDS

def fixture(value="350"):
    return dict(source_id="user_csv",venue_id="hall1",machine_id="machine1",
        model_revision="rev1",machine_number="101",
        observed_date="2026-11-15",observed_at="2026-11-15T10:00:00+09:00",
        event_order="1",counter_label="AT games",event_label="AT start",
        counter_value=value,evidence_url="https://example.org/record",
        source_permission="user_owned",
        permission_evidence="https://example.org/permission",
        source_record_id="event1")

def csv_text(row):
    out=io.StringIO()
    writer=csv.DictWriter(out,fieldnames=FIELDS)
    writer.writeheader()
    writer.writerow(row)
    return out.getvalue()

def rule():
    return dict(id="rule1",version=1,source_id="user_csv",venue_id="hall1",
        machine_id="machine1",model_revision="rev1",valid_from="2026-01-01",
        valid_until="2026-12-31",counter_label="AT games",
        event_label="AT start",counter_type="at_games",
        counter_origin="last_at_end",event_type="at_start",
        evidence_url="https://example.org/rule",review_status="verified")

class OfflineAuditCLITests(unittest.TestCase):
    def test_empty_rule_registry_quarantines(self):
        r=inspect_csv(csv_text(fixture()),[])
        self.assertEqual(r["audit_event_count"],0)
        self.assertEqual(r["quarantined_count"],1)
        self.assertEqual(r["estimate_candidates"],[])
    def test_verified_rule_pins_and_audits(self):
        r=inspect_csv(csv_text(fixture()),[rule()])
        self.assertEqual(r["audit_event_count"],1)
        self.assertEqual(r["quarantined_count"],0)
        self.assertEqual(r["pinned_rule_snapshots"][0]["rule_version"],1)
        self.assertEqual(r["publication_status"],"research_only")
    def test_negative_at_games_quarantined(self):
        r=inspect_csv(csv_text(fixture("-5")),[rule()])
        self.assertEqual(r["audit_event_count"],0)
        self.assertEqual(r["quarantined_count"],1)
    def test_unverified_rule_quarantined(self):
        r=inspect_csv(csv_text(fixture()),[dict(rule(),review_status="pending")])
        self.assertEqual(r["audit_event_count"],0)
        self.assertEqual(r["quarantined_count"],1)
    def test_duplicate_rules_quarantined(self):
        a=rule()
        b=dict(a,id="rule2",version=2)
        r=inspect_csv(csv_text(fixture()),[a,b])
        self.assertEqual(r["audit_event_count"],0)
        self.assertEqual(r["quarantined_count"],1)
    def test_no_ev_even_when_event_accepted(self):
        r=inspect_csv(csv_text(fixture()),[rule()])
        self.assertEqual(r["estimate_candidates"],[])

if __name__=="__main__":
    unittest.main()
