"""Research pipeline contracts; no public-site or real hall data."""
import unittest
from scripts.ev_research_pipeline import PipelineError, run_pipeline

def source(i=1):
    return dict(machine_number="101",observed_at=f"2026-11-15T10:{i:02d}:00+09:00",
                event_order=i)

def normalizer(row):
    return dict(source_id="source-a",venue_id="hall-a",machine_id="machine-a",
                model_revision="rev-A",machine_number=row["machine_number"],
                observed_at=row["observed_at"],event_order=row["event_order"],
                original_value=350,counter_type="at_games",
                counter_origin="last_at_end",event_type="at_start",
                evidence_url="https://example.org",review_status="verified")

def auditor(rows):
    return {"group_count":1,"groups":[{"event_count":len(rows),"ev_ready":False,
                                        "flags":["right_censored_outcome"]}]}

class ResearchPipelineTests(unittest.TestCase):
    def test_events_never_generate_ev(self):
        result=run_pipeline([source()],normalize=normalizer,audit=auditor)
        self.assertEqual(result.source_count,1)
        self.assertEqual(result.normalized_count,1)
        self.assertEqual(result.blocked_group_count,1)
        self.assertEqual(result.estimate_candidates,())
        self.assertEqual(result.as_dict()["publication_status"],"research_only")
    def test_unmapped_data_quarantined(self):
        def unverified(row):
            return dict(normalizer(row),review_status="unmapped")
        result=run_pipeline([source()],normalize=unverified,audit=auditor)
        self.assertEqual(result.normalized_count,0)
        self.assertEqual(len(result.rejected_observations),1)
        self.assertEqual(result.audit_group_count,0)
    def test_bad_observation_isolated(self):
        def fail(row):
            raise ValueError("invalid venue mapping")
        result=run_pipeline([source()],normalize=fail,audit=auditor)
        self.assertEqual(result.rejected_observations[0]["reason"],"invalid venue mapping")
    def test_episode_estimator_is_separate(self):
        def summarize(episodes):
            self.assertEqual(episodes,[{"episode_id":"independent"}])
            return [{"publication_status":"research_only","sample_size":1}]
        result=run_pipeline([],normalize=normalizer,audit=auditor,
                            episodes=[{"episode_id":"independent"}],summarize=summarize)
        self.assertEqual(result.estimate_candidates[0]["sample_size"],1)
    def test_public_estimate_rejected(self):
        with self.assertRaises(PipelineError):
            run_pipeline([],normalize=normalizer,audit=auditor,
                         episodes=[{"episode_id":"a"}],
                         summarize=lambda _: [{"publication_status":"public"}])
    def test_no_estimator_rejected(self):
        with self.assertRaises(PipelineError):
            run_pipeline([],normalize=normalizer,audit=auditor,
                         episodes=[{"episode_id":"a"}])
if __name__=="__main__":
    unittest.main()
