"""Full CSV->verified mapping->event audit signed counter tests."""
import csv
import io
import unittest
from scripts.ev_hall_csv_import import FIELDS, import_observations_csv
from scripts.ev_counter_normalizer import normalize
from scripts.ev_contract_adapters import observation_to_audit
from scripts.ev_episode_audit import audit_event_stream
from scripts.ev_csv_audit_bridge import process_csv_to_audit

def fixture(counter_type="daily_difference_medals", counter_value="-500",
            counter_label="daily delta", event_order="1", record_id="e1",
            observed_at="2026-11-15T10:00:00+09:00"):
    raw = dict(source_id="synthetic",venue_id="hall",machine_id="machine",
        model_revision="rev",machine_number="101",observed_date="2026-11-15",
        observed_at=observed_at,event_order=event_order,
        counter_label=counter_label,event_label="display",
        counter_value=counter_value,evidence_url="https://example.org/record",
        source_permission="user_owned",
        permission_evidence="https://example.org/permission",
        source_record_id=record_id)
    rule = dict(id="rule1",version=1,source_id="synthetic",venue_id="hall",
        machine_id="machine",model_revision="rev",valid_from="2026-01-01",
        valid_until="2026-12-31",counter_label=counter_label,
        event_label="display",counter_type=counter_type,
        counter_origin="daily_open" if counter_type=="daily_difference_medals" else "last_at_end",
        event_type="display_difference",evidence_url="https://example.org/rule",
        review_status="verified")
    return raw,rule

def csv_rows(*rows):
    out=io.StringIO()
    writer=csv.DictWriter(out,fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()

def run(rows,rules):
    return process_csv_to_audit(csv_rows(*rows),rules=rules,
        intake=import_observations_csv,normalize=normalize,
        to_audit=observation_to_audit,audit=audit_event_stream)

class SignedCSVIntegrationTests(unittest.TestCase):
    def test_negative_daily_difference_reaches_audit(self):
        raw,rule=fixture()
        result=run([raw],[rule])
        self.assertEqual(result["audit_event_count"],1)
        self.assertEqual(result["quarantined_count"],0)
        self.assertEqual(result["audit_groups"][0]["events"][0]["counter_value"],-500)
        self.assertEqual(result["estimate_candidates"],[])
    def test_negative_at_games_quarantined(self):
        raw,rule=fixture(counter_type="at_games",counter_label="AT games")
        result=run([raw],[rule])
        self.assertEqual(result["audit_event_count"],0)
        self.assertEqual(result["quarantined_count"],1)
    def test_unmapped_negative_value_quarantined(self):
        raw,_=fixture()
        result=run([raw],[])
        self.assertEqual(result["audit_event_count"],0)
        self.assertEqual(result["quarantined_count"],1)
    def test_ambiguous_signed_rules_quarantined(self):
        raw,rule=fixture()
        second=dict(rule,id="rule2")
        result=run([raw],[rule,second])
        self.assertEqual(result["audit_event_count"],0)
        self.assertEqual(result["quarantined_count"],1)
    def test_signed_decrease_not_mislabeled_reset(self):
        first,rule=fixture(counter_value="500")
        second,_=fixture(counter_value="-500",event_order="2",
                         record_id="e2",observed_at="2026-11-15T10:05:00+09:00")
        result=run([first,second],[rule])
        self.assertEqual(result["audit_event_count"],2)
        self.assertNotIn("counter_decreased_without_verified_boundary",
                         result["audit_groups"][0]["flags"])
    def test_nonnegative_at_decrease_still_flagged(self):
        first,rule=fixture(counter_type="at_games",counter_label="AT games",
                           counter_value="350")
        second,_=fixture(counter_type="at_games",counter_label="AT games",
                         counter_value="20",event_order="2",record_id="e2",
                         observed_at="2026-11-15T10:05:00+09:00")
        result=run([first,second],[rule])
        self.assertIn("counter_decreased_without_verified_boundary",
                      result["audit_groups"][0]["flags"])

if __name__=="__main__":
    unittest.main()
