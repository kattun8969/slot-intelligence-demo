"""Guardrails for simplified public EV lookups and independent hall-data research."""
from pathlib import Path
import csv
import json
import tempfile
import unittest

from scripts.audit_hall_counter_csv import parse_csv

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/"docs"


class PublicEvLookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((DOCS/"public-ev-reference.json").read_text(encoding="utf-8"))
        cls.page=(DOCS/"public-ev-lookup.html").read_text(encoding="utf-8")
        cls.machines=(DOCS/"opportunities.html").read_text(encoding="utf-8")
    def test_conditions_and_points(self):
        rows=self.data["scenarios"]
        self.assertEqual({x["machine"] for x in rows},{"monkey5","tokyoghoul","seiya","ragnador","vivy"})
        self.assertEqual(len(rows),9)
        for x in rows:
            self.assertTrue(x["url"].startswith("https://"))
            self.assertTrue(x["exit"] and x["preconditions"] and x["price"])
            self.assertTrue(all(x["points"][i][0]<x["points"][i+1][0] for i in range(len(x["points"])-1)))
            self.assertTrue(all(isinstance(p[1],int) for p in x["points"]))
        self.assertTrue(any(x["counter"]=="at" for x in rows))
        self.assertTrue(any(x["counter"]=="cz" for x in rows))
    def test_no_standalone_guessing(self):
        for text in ["掲載範囲外","線形補間","前提","期待値集計にメモする","sessionStorage.setItem"]:
            self.assertIn(text,self.page)
        self.assertIn("function calculate(s,g)",self.page)
        self.assertIn("g<p[0][0]||g>p[p.length-1][0]",self.page)
        self.assertIn("公開期待値の簡易チェック",self.machines)
        self.assertIn('href="./ev-simulator.html"',self.page)
        self.assertIn('m.id',self.machines)
    def test_backlog_enriched_without_fake_ev(self):
        practical=json.loads((DOCS/"practical-picks.json").read_text(encoding="utf-8"))
        picks=[x for x in practical["items"] if x["machine"] in {"ragnador","vivy"}]
        self.assertGreaterEqual(len(picks),3)
        self.assertTrue(all(x["ev_yen"] is None and x["source"].startswith("https://") for x in picks))


class CounterAuditorTests(unittest.TestCase):
    fields=["venue_id","machine_model","model_revision","data_date","machine_number",
            "counter_label","counter_value","counter_unit","event_label",
            "event_order","source_url","collection_method","observation_confidence",
            "rules_verified"]
    def csv(self, rows):
        d=tempfile.TemporaryDirectory()
        path=Path(d.name)/"events.csv"
        with path.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=self.fields)
            w.writeheader()
            for x in rows:w.writerow(x)
        return d,path
    def basic_row(self):
        return dict(zip(self.fields,["venue-1","GGO","6.5号機","2026-11-14","01",
                                     "ボーナス間","250","G","AT","1","https://example.com/a",
                                     "permitted_csv","observed","yes"]))
    def test_accepted_observation_does_not_prove_ev(self):
        d,p=self.csv([self.basic_row()])
        try:
            valid,hold=parse_csv(p)
            self.assertEqual(len(valid),1)
            self.assertFalse(hold)
            self.assertEqual(valid[0]["event_type"],"AT")
            self.assertNotIn("expected_value",valid[0])
        finally:d.cleanup()
    def test_run_through_and_unknown_counters_are_held(self):
        a=self.basic_row()
        a["event_label"]="駆け抜け"
        b=self.basic_row()
        b["event_label"]="CZ終了？"
        b["rules_verified"]="no"
        d,p=self.csv([a,b])
        try:
            valid,hold=parse_csv(p)
            self.assertEqual(len(valid),0)
            self.assertEqual(len(hold),2)
            self.assertIn("claimed state needs independent outcome verification",hold[0]["reasons"])
            self.assertIn("counter rules unverified",hold[1]["reasons"])
        finally:d.cleanup()
    def test_unknown_unit_rejected(self):
        a=self.basic_row()
        a["counter_unit"]="Gかpt"
        d,p=self.csv([a])
        try:
            ok,hold=parse_csv(p)
            self.assertEqual(len(ok),0)
            self.assertIn("unsupported unit",hold[0]["reasons"])
        finally:d.cleanup()

if __name__=="__main__":
    unittest.main()
