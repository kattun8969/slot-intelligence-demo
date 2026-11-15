"""CSV intake tests with entirely synthetic hall observations."""
import csv
import io
import unittest
from scripts.ev_hall_csv_import import FIELDS, import_observations_csv, IntakeError

def sample(**updates):
    row = dict(
        source_id="fixture-source", venue_id="fixture-hall",
        machine_id="fixture-machine", model_revision="fixture-rev",
        machine_number="101", observed_date="2026-11-15",
        observed_at="2026-11-15T10:00:00+09:00",
        event_order="1", counter_label="AT interval",
        event_label="AT start", counter_value="350",
        evidence_url="https://example.org/observation",
        source_permission="user_owned",
        permission_evidence="https://example.org/permission",
        source_record_id="event-1",
    )
    row.update(updates)
    return row

def csv_text(rows):
    f = io.StringIO()
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return f.getvalue()

class IntakeTests(unittest.TestCase):
    def test_valid_row_keeps_source_and_types(self):
        report=import_observations_csv(csv_text([sample()]))
        self.assertEqual(report["accepted_count"],1)
        self.assertEqual(report["accepted"][0]["counter_value"],350)
        self.assertEqual(report["accepted"][0]["source_record_id"],"event-1")
        self.assertEqual(report["publication_status"],"research_only")
    def test_bad_row_quarantined_without_dropping_valid(self):
        report=import_observations_csv(csv_text([
            sample(), sample(source_record_id="event-2",source_permission="unlicensed")
        ]))
        self.assertEqual(report["accepted_count"],1)
        self.assertEqual(report["quarantined_count"],1)
        self.assertEqual(report["quarantine"][0]["csv_line"],3)
    def test_duplicate_record_quarantined(self):
        report=import_observations_csv(csv_text([sample(),sample()]))
        self.assertEqual(report["quarantined_count"],1)
        self.assertEqual(report["quarantine"][0]["reason"],"duplicate_source_record")
    def test_rejects_timezone_missing(self):
        report=import_observations_csv(csv_text([sample(observed_at="2026-11-15T10:00:00")]))
        self.assertEqual(report["quarantine"][0]["reason"],"timestamp_missing_timezone")
    def test_rejects_date_mismatch(self):
        report=import_observations_csv(csv_text([sample(observed_date="2026-11-14")]))
        self.assertEqual(report["quarantine"][0]["reason"],"observation_calendar_date_mismatch")
    def test_rejects_unverifiable_permission(self):
        report=import_observations_csv(csv_text([sample(permission_evidence="")]))
        self.assertEqual(report["accepted_count"],0)
    def test_signed_value_provisional_until_mapping(self):
        report=import_observations_csv(csv_text([sample(counter_value="-5")]))
        self.assertEqual(report["accepted_count"],1)
        self.assertEqual(report["accepted"][0]["counter_value"],-5)
    def test_rejects_missing_headers(self):
        with self.assertRaises(IntakeError):
            import_observations_csv("source_id,venue_id\na,b\n")
    def test_enforces_row_limit(self):
        with self.assertRaises(IntakeError):
            import_observations_csv(csv_text([sample(),sample(source_record_id="2")]),max_rows=1)
    def test_rejects_duplicate_headers(self):
        with self.assertRaises(IntakeError):
            import_observations_csv("source_id,source_id\na,b\n")

if __name__=="__main__":
    unittest.main()
