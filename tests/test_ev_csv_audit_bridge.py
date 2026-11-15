"""Isolated bridge contract tests with synthetic records."""
import unittest
from scripts.ev_csv_audit_bridge import process_csv_to_audit, BridgeError

def imported(_):
    return {"accepted_count": 2, "accepted": [
        {"source_record_id":"1", "counter_value": 10},
        {"source_record_id":"2", "counter_value": 20},
    ], "quarantine":[]}
def normal(raw, rules):
    if raw["counter_value"] == 20:
        raise ValueError("unmapped")
    return {"review_status":"verified", "counter_value":raw["counter_value"]}
def convert(raw, n):
    return {"source_record_id":raw["source_record_id"],"ev_ready":False}
def audit(rows):
    return {"groups":[{"ev_ready":False,"events":rows}]}

class CSVBridgeTests(unittest.TestCase):
    def test_quarantines_unmapped_without_aborting(self):
        r=process_csv_to_audit("synthetic",rules=[],intake=imported,
                               normalize=normal,to_audit=convert,audit=audit)
        self.assertEqual(r["audit_event_count"],1)
        self.assertEqual(r["quarantined_count"],1)
        self.assertEqual(r["estimate_candidates"],[])
        self.assertEqual(r["publication_status"],"research_only")
    def test_no_audit_when_all_quarantined(self):
        r=process_csv_to_audit("synthetic",rules=[],intake=imported,
                               normalize=lambda *_: (_ for _ in ()).throw(ValueError("no mapping")),
                               to_audit=convert,audit=audit)
        self.assertEqual(r["audit_group_count"],0)
        self.assertEqual(r["quarantined_count"],2)
    def test_never_accepts_ev_ready_from_hall_events(self):
        with self.assertRaises(BridgeError):
            process_csv_to_audit("synthetic",rules=[],intake=imported,
                                 normalize=lambda raw,rules: {"ok":True},
                                 to_audit=convert,
                                 audit=lambda rows: {"groups":[{"ev_ready":True}]})
    def test_rejects_invalid_audit_contract(self):
        with self.assertRaises(BridgeError):
            process_csv_to_audit("synthetic",rules=[],intake=imported,
                                 normalize=lambda raw,rules: {"ok":True},
                                 to_audit=convert,audit=lambda rows: {"groups":None})

if __name__=="__main__":
    unittest.main()
