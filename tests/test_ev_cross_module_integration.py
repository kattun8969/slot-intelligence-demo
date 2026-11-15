"""Cross-module integration with synthetic evidence; no real hall or EV values."""
import unittest
from scripts.ev_counter_normalizer import normalize
from scripts.ev_contract_adapters import observation_to_audit, estimate_to_comparison
from scripts.ev_episode_audit import audit_event_stream
from scripts.ev_engine_core import summarize_episodes
from scripts.ev_reference_compare import compare_exact
from scripts.ev_holdout_validation import validate_holdout
from scripts.ev_research_pipeline import run_pipeline
from scripts.ev_hall_csv_import import import_observations_csv, FIELDS
from scripts.ev_csv_audit_bridge import process_csv_to_audit
import csv
import io

def rule():
    return {
        "id":"fixture-rule","version":1,"source_id":"fixture-source",
        "venue_id":"fixture-hall","machine_id":"fixture-machine",
        "model_revision":"fixture-rev","valid_from":"2026-01-01",
        "valid_until":"2026-12-31","counter_label":"AT interval",
        "event_label":"AT start","counter_type":"at_games",
        "counter_origin":"last_at_end","event_type":"at_start",
        "evidence_url":"https://example.org/rule","review_status":"verified"
    }

def raw():
    return {
        "source_id":"fixture-source","venue_id":"fixture-hall",
        "machine_id":"fixture-machine","model_revision":"fixture-rev",
        "observed_date":"2026-11-15","counter_label":"AT interval",
        "event_label":"AT start","counter_value":350,
        "evidence_url":"https://example.org/observation",
        "machine_number":"101","observed_at":"2026-11-15T10:00:00+09:00",
        "event_order":1
    }

def episode(i, day, return_yen=1400):
    return {
        "episode_id":str(i),"machine_id":"fixture-machine",
        "model_revision":"fixture-rev","venue_id":"fixture-hall",
        "date":day,"counter_type":"at_games","counter_origin":"last_at_end","counter_value":350,
        "state":"normal","state_evidence":"observed",
        "investment_yen":1000,"return_yen":return_yen,
        "exchange_basis":"20yen_equal",
        "play_end_condition":"next_at_end","completed":True,
        "source_permission":"user_owned"
    }

class EndToEndEVTests(unittest.TestCase):
    def test_real_normalizer_adapter_auditor_pipeline_no_ev(self):
        source=raw()
        normal=normalize(source,[rule()]).to_dict()
        audit_input=observation_to_audit(source,normal)
        audited=audit_event_stream([audit_input])
        self.assertEqual(audited["group_count"],1)
        self.assertFalse(audited["groups"][0]["ev_ready"])
        self.assertIn("right_censored_outcome",audited["groups"][0]["flags"])
        def normalizer(item):
            n=normalize(item,[rule()]).to_dict()
            # The pipeline contract requires evidence fields from raw records.
            a=observation_to_audit(item,n)
            return dict(n,machine_number=a["machine_number"],
                        observed_at=a["observed_at"],event_order=a["event_order"],
                        evidence_url=a["source_url"])
        result=run_pipeline([source],normalize=normalizer,audit=audit_event_stream)
        self.assertEqual(result.normalized_count,1)
        self.assertEqual(result.blocked_group_count,1)
        self.assertEqual(result.estimate_candidates,())

    def test_csv_through_real_normalization_and_audit(self):
        row = dict(raw())
        row.update(event_order="1",counter_value="350",
                   source_permission="user_owned",
                   permission_evidence="https://example.org/permission",
                   source_record_id="record-1")
        out = io.StringIO()
        writer = csv.DictWriter(out,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(row)
        result = process_csv_to_audit(
            out.getvalue(),rules=[rule()],
            intake=import_observations_csv,
            normalize=normalize,
            to_audit=observation_to_audit,
            audit=audit_event_stream)
        self.assertEqual(result["csv_accepted_count"],1)
        self.assertEqual(result["audit_event_count"],1)
        self.assertEqual(result["quarantined_count"],0)
        self.assertEqual(result["audit_group_count"],1)
        self.assertEqual(result["estimate_candidates"],[])

    def test_unmapped_counter_never_produces_estimate(self):
        item=dict(raw(),counter_label="unknown label")
        def normalizer(r):
            return normalize(r,[rule()]).to_dict()
        result=run_pipeline([item],normalize=normalizer,audit=audit_event_stream)
        self.assertEqual(result.normalized_count,0)
        self.assertEqual(len(result.rejected_observations),1)
        self.assertEqual(result.estimate_candidates,())

    def test_actual_episode_estimate_to_comparison_and_holdout(self):
        records=[episode(i,"2026-11-01") for i in range(3)]
        records += [episode(i+3,"2026-11-15",return_yen=1200) for i in range(3)]
        summary=summarize_episodes(records,min_samples=2)
        self.assertEqual(len(summary),1)
        self.assertEqual(summary[0]["sample_size"],6)
        self.assertEqual(summary[0]["mean_net_yen"],300)
        observed=estimate_to_comparison(summary[0],counter_origin="last_at_end",
                                        origin_evidence_url="https://example.org/rule")
        reference={
            "machine_id":"fixture-machine","model_revision":"fixture-rev",
            "counter_type":"at_games","counter_origin":"last_at_end",
            "counter_value":350,"state":"normal","exchange_basis":"20yen_equal",
            "play_end_condition":"next_at_end","provenance":"published_reference",
            "ev_yen":500,"source_url":"https://example.org/reference",
            "checked_at":"2026-11-15"
        }
        compared=compare_exact([reference],[observed],min_samples=2)
        self.assertEqual(compared["comparisons"][0]["difference_yen"],-200)
        holdout=validate_holdout(records,split_date="2026-11-15",
                                 min_train=3,min_test=3)
        self.assertEqual(holdout["groups"][0]["train_mean_yen"],400)
        self.assertEqual(holdout["groups"][0]["test_mean_yen"],200)
        self.assertEqual(holdout["groups"][0]["holdout_difference_yen"],-200)
        self.assertEqual(holdout["publication_status"],"research_only")

if __name__=="__main__":
    unittest.main()
