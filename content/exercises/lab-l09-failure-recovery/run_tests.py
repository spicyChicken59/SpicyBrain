"""lab-l09-failure-recovery test runner (local-executed, Python 3.12 standard library).

    python run_tests.py --evidence <path>     # the reference solution
    python run_tests.py --starter             # your completed starters/pipeline.py

Run from this directory with Python 3.12; nothing needs installing. Offline: no
network, no scheduler service and no Databricks workspace. The pipeline's only
"external effect" is a local channel that appends dictionaries to a Python list;
no message is ever sent. Every expected value is a literal in expected/*.json,
derived by hand as DATA.md explains, or a literal written in this file; no test
compares the pipeline with a value the pipeline computed. Report identities are
checked against an independent digest written in this file. The four shortcuts
in starters/shortcuts.py are asserted to fail for their documented reasons, and
the starter's six gaps are asserted to be marked. Fixture, expected, solution,
starter and produced-output SHA-256 hashes go into the evidence JSON.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import platform
import sys
import time
import unittest

sys.dont_write_bytecode = True  # keep the package free of __pycache__
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

STARTER = "--starter" in sys.argv
P = import_module("starters.pipeline" if STARTER else "solutions.pipeline")
from starters import shortcuts  # noqa: E402

LAB = "lab-l09-failure-recovery"
FIX = ROOT / "fixtures"
TFIX = FIX / "transfer"
EXPECTED = {name: json.loads((ROOT / "expected" / f"{name}.json").read_text(encoding="utf-8"))
            for name in ("reports", "boundaries", "retries", "stale", "backfill", "runbook", "transfer")}
REPORTS = EXPECTED["reports"]
TREPORTS = EXPECTED["transfer"]["reports"]
CONTRACT = json.loads((FIX / "contract.json").read_text(encoding="utf-8"))
TCONTRACT = json.loads((TFIX / "contract.json").read_text(encoding="utf-8"))
BOUNDARIES = ("after_raw_retention", "after_resolution", "before_effect", "after_effect")
OUTPUTS: dict[str, object] = {}


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def independent_digest(content: dict) -> str:
    """Written here, not imported: business date, hyphen, first 12 hex of SHA-256 over canonical JSON."""
    return content["report_date"] + "-" + sha256(canonical(content).encode("utf-8")).hexdigest()[:12]


def landing(date: str) -> Path:
    return FIX / "landing" / f"{date}.json"


def run(pipe, date: str, path: Path | None = None, run_id: str | None = None, faults=None) -> dict:
    return pipe.run(run_id or f"line3-{date}", date, path or landing(date), faults)


def fault(boundary: str, count: int = 1, transient: bool = False):
    return P.Faults({boundary: count}, transient=transient)


def recipients(pipe) -> list[str]:
    return [item["recipient"] for item in pipe.channel.delivered]


def delivered_for(pipe, date: str) -> list[list[str]]:
    return [[item["recipient"], item["report_date"]] for item in pipe.channel.delivered if item["report_date"] == date]


def outbox_counts(pipe) -> dict[str, int]:
    states = [entry["state"] for entry in pipe.store.outbox.values()]
    return {"sent": states.count("sent"), "pending": states.count("pending")}


def executions(pipe, run_id: str) -> dict[str, int]:
    return {task: state["executions"] for task, state in pipe.store.runs[run_id]["tasks"].items()}


def view(pipe, as_of: str) -> dict:
    shown = P.report_view(pipe.store, as_of)
    return {"status": shown["status"], "report_date": shown["report_date"]}


def alerts(pipe) -> list[dict]:
    return [{"run_id": a["run_id"], "task": a["task"], "reason": a["reason"]} for a in pipe.store.alerts]


def boundary_setup(boundary: str, channel=None):
    """2026-03-02 clean, then 2026-03-03 with one non-transient fault at `boundary`."""
    pipe = P.Pipeline(CONTRACT, channel=channel)
    run(pipe, "2026-03-02")
    outcome = run(pipe, "2026-03-03", faults=fault(boundary))
    return pipe, outcome


class ResolutionTests(unittest.TestCase):
    """The business rules the pipeline publishes: one latest valid version per key."""

    def test_each_landing_file_resolves_to_the_hand_derived_report(self):
        pipe = P.Pipeline(CONTRACT)
        for date in ("2026-03-02", "2026-03-03", "2026-03-04"):
            outcome = run(pipe, date)
            self.assertEqual(outcome["status"], "succeeded")
            report = pipe.store.reports[date]
            self.assertEqual(report["content"], REPORTS[date]["content"])
            self.assertEqual(report["report_id"], REPORTS[date]["report_id"])
            self.assertEqual(pipe.store.runs[f"line3-{date}"]["tasks"]["ingest_raw"]["detail"],
                             REPORTS[date]["retention"])
            OUTPUTS[f"report_{date}"] = report["content"]

    def test_report_identity_is_the_independent_digest_of_the_expected_content(self):
        for name, item in {**REPORTS, **TREPORTS}.items():
            if name.startswith("_"):
                continue
            self.assertEqual(independent_digest(item["content"]), item["report_id"], name)
            self.assertEqual(P.report_identity(item["content"]), item["report_id"], name)

    def test_the_same_content_under_another_run_id_has_the_same_identity(self):
        first, second = P.Pipeline(CONTRACT), P.Pipeline(CONTRACT)
        run(first, "2026-03-02")
        second.run("adhoc-rerun-7", "2026-03-02", landing("2026-03-02"))
        self.assertEqual(first.store.reports["2026-03-02"]["report_id"],
                         second.store.reports["2026-03-02"]["report_id"])
        self.assertEqual(second.store.reports["2026-03-02"]["published_by"], "adhoc-rerun-7")

    def test_validation_gives_one_fixed_reason_per_invalid_row(self):
        base = {"event_id": "x", "lot": "L-1", "version": 1, "inspected": 5, "defective": 1}
        cases = [
            ({"lot": ""}, "missing key field lot"),
            ({"version": True}, "version must be a positive integer"),
            ({"version": 0}, "version must be a positive integer"),
            ({"inspected": 2.0}, "inspected must be an integer"),
            ({"inspected": 0}, "inspected must be at least 1"),
            ({"defective": -1}, "defective must be at least 0"),
            ({"defective": 6}, "defective must not exceed inspected"),
            ({}, None),
        ]
        for change, reason in cases:
            self.assertEqual(P.validate(CONTRACT, {**base, **change}), reason, change)


    def test_a_conflict_blocks_only_what_would_be_published(self):
        retained = {"a1": {"event_id": "a1", "lot": "L-1", "version": 1, "inspected": 5, "defective": 1},
                    "a2": {"event_id": "a2", "lot": "L-1", "version": 2, "inspected": 6, "defective": 1}}
        on_old = P.resolve_rows(CONTRACT, retained, [{"event_id": "a1", "reason": "event_conflict"}])
        self.assertEqual(on_old["conflicts"], [])
        self.assertEqual(on_old["rows"], [{"lot": "L-1", "version": 2, "event_id": "a2", "inspected": 6, "defective": 1}])
        on_winner = P.resolve_rows(CONTRACT, retained, [{"event_id": "a2", "reason": "event_conflict"}])
        self.assertEqual(on_winner["conflicts"], [{"event_id": "a2", "reason": "event_conflict"}])


class BoundaryTests(unittest.TestCase):
    """A failure at each named boundary leaves its own evidence; a repair of the same run id completes it."""

    def check_failure(self, boundary: str):
        exp = EXPECTED["boundaries"][boundary]["failed"]
        pipe, outcome = boundary_setup(boundary)
        self.assertEqual(outcome["status"], exp["status"])
        self.assertEqual(outcome["tasks"], exp["tasks"])
        failed = [s for s in pipe.store.runs["line3-2026-03-03"]["tasks"].values() if s["status"] == "failed"]
        self.assertEqual([s["reason"] for s in failed], [exp["reason"]])
        self.assertEqual(pipe.evidence("line3-2026-03-03"), exp["evidence"])
        self.assertEqual(view(pipe, "2026-03-03"), exp["view"])
        self.assertEqual(len(pipe.channel.delivered), exp["deliveries_total"])
        self.assertEqual(len(pipe.store.alerts), exp["alerts"])
        OUTPUTS[f"failed_{boundary}"] = pipe.evidence("line3-2026-03-03")

    def check_repair(self, boundary: str):
        exp = EXPECTED["boundaries"][boundary]["repaired"]
        pipe, _ = boundary_setup(boundary)
        outcome = run(pipe, "2026-03-03")
        self.assertEqual(outcome["status"], exp["status"])
        self.assertEqual(outcome["attempt"], exp["attempt"])
        self.assertEqual(executions(pipe, "line3-2026-03-03"), exp["executions"])
        self.assertEqual(pipe.store.runs["line3-2026-03-03"]["tasks"]["ingest_raw"]["detail"], exp["ingest_detail"])
        self.assertEqual(pipe.store.reports["2026-03-03"]["content"], REPORTS["2026-03-03"]["content"])
        self.assertEqual(pipe.store.reports["2026-03-03"]["report_id"], REPORTS["2026-03-03"]["report_id"])
        self.assertEqual(len(pipe.channel.delivered), exp["deliveries_total"])
        self.assertEqual(delivered_for(pipe, "2026-03-03"), exp["deliveries_for_date"])
        self.assertEqual(pipe.channel.suppressed, exp["suppressed"])
        self.assertEqual(view(pipe, "2026-03-03"), exp["view"])
        OUTPUTS[f"repaired_{boundary}"] = pipe.channel.delivered

    def test_failure_after_raw_retention(self):
        self.check_failure("after_raw_retention")

    def test_repair_after_raw_retention_re_retains_nothing_new(self):
        self.check_repair("after_raw_retention")

    def test_failure_after_resolution(self):
        self.check_failure("after_resolution")

    def test_repair_after_resolution_reuses_the_retained_raw(self):
        self.check_repair("after_resolution")

    def test_failure_before_the_effect_keeps_the_published_report(self):
        self.check_failure("before_effect")

    def test_repair_before_the_effect_sends_each_notification_once(self):
        self.check_repair("before_effect")

    def test_failure_after_the_effect_leaves_one_unacknowledged_delivery(self):
        self.check_failure("after_effect")

    def test_repair_after_the_effect_does_not_send_twice(self):
        self.check_repair("after_effect")

    def test_a_repeated_failure_alerts_once_per_run_task_and_reason(self):
        exp = EXPECTED["boundaries"]["repeated_failure"]
        pipe, _ = boundary_setup("after_resolution")
        second = run(pipe, "2026-03-03", faults=fault("after_resolution"))
        self.assertEqual({"status": second["status"], "attempt": second["attempt"],
                          "resolve_executions": executions(pipe, "line3-2026-03-03")["resolve"],
                          "alerts": len(pipe.store.alerts)}, exp["after_second_failure"])
        third = run(pipe, "2026-03-03")
        self.assertEqual({"status": third["status"], "attempt": third["attempt"],
                          "resolve_executions": executions(pipe, "line3-2026-03-03")["resolve"],
                          "ingest_executions": executions(pipe, "line3-2026-03-03")["ingest_raw"],
                          "alerts": len(pipe.store.alerts)}, exp["after_clean_repair"])

    def test_a_new_run_id_over_the_same_input_changes_nothing_downstream(self):
        exp = EXPECTED["boundaries"]["new_run_id_same_input"]
        pipe = P.Pipeline(CONTRACT)
        run(pipe, "2026-03-02")
        outcome = run(pipe, "2026-03-02", run_id="line3-2026-03-02-rerun")
        tasks = pipe.store.runs["line3-2026-03-02-rerun"]["tasks"]
        self.assertEqual(outcome["status"], exp["status"])
        self.assertEqual(tasks["ingest_raw"]["detail"], exp["ingest_detail"])
        self.assertEqual(tasks["publish_report"]["detail"], exp["publish_detail"])
        self.assertEqual(tasks["notify"]["detail"], exp["notify_detail"])
        self.assertEqual(len(pipe.channel.delivered), exp["deliveries_total"])
        self.assertEqual(len(pipe.store.report_history), exp["history"])

    def test_a_run_id_is_bound_to_its_business_date(self):
        pipe = P.Pipeline(CONTRACT)
        run(pipe, "2026-03-02")
        with self.assertRaises(P.RunIdentityError) as caught:
            pipe.run("line3-2026-03-02", "2026-03-03", landing("2026-03-03"))
        self.assertIn(EXPECTED["boundaries"]["run_identity"]["error_contains"], str(caught.exception))
        self.assertNotIn("2026-03-03", pipe.store.raw)


class RetryTests(unittest.TestCase):
    """A retry policy repeats work; only a key the receiver honours stops a repeated effect."""

    def check(self, name: str, pipe, outcome):
        exp = EXPECTED["retries"][name]
        self.assertEqual(outcome["status"], exp["status"])
        self.assertEqual(outcome["attempt"], exp["attempt"])
        self.assertEqual(executions(pipe, "line3-2026-03-02")["notify"], exp["notify_executions"])
        self.assertEqual(recipients(pipe), exp["deliveries"])
        self.assertEqual(pipe.channel.suppressed, exp["suppressed"])
        self.assertEqual(outbox_counts(pipe), exp["outbox"])
        OUTPUTS[f"retries_{name}"] = pipe.channel.delivered

    def test_the_keyed_outbox_absorbs_a_retry_after_the_effect(self):
        pipe = P.Pipeline(CONTRACT, retries={"notify": 1})
        self.check("keyed_after_effect", pipe, run(pipe, "2026-03-02", faults=fault("after_effect", transient=True)))

    def test_a_naive_retry_without_a_key_duplicates_the_notification(self):
        pipe = P.Pipeline(CONTRACT, retries={"notify": 1}, tasks={"notify": shortcuts.notify_without_key})
        outcome = run(pipe, "2026-03-02", faults=fault("after_effect", transient=True))
        self.check("no_key_after_effect", pipe, outcome)
        first, second = pipe.channel.delivered[0], pipe.channel.delivered[1]
        self.assertEqual((first["recipient"], first["report_id"]), (second["recipient"], second["report_id"]))
        self.assertIsNone(first["key"])  # the reason: nothing identifies the repeat
        self.assertEqual(outcome["tasks"]["notify"], "succeeded")  # and the task is still green

    def test_a_naive_retry_before_the_effect_happens_not_to_duplicate(self):
        pipe = P.Pipeline(CONTRACT, retries={"notify": 1}, tasks={"notify": shortcuts.notify_without_key})
        self.check("no_key_before_effect", pipe, run(pipe, "2026-03-02", faults=fault("before_effect", transient=True)))

    def test_a_fresh_key_per_try_duplicates_and_orphans_intents(self):
        pipe = P.Pipeline(CONTRACT, retries={"notify": 1}, key_fn=shortcuts.fresh_key_per_try)
        self.check("fresh_key_per_try_after_effect", pipe,
                   run(pipe, "2026-03-02", faults=fault("after_effect", transient=True)))
        keys = [item["key"] for item in pipe.channel.delivered if item["recipient"] == "quality-lead"]
        self.assertEqual(len(set(keys)), 2)  # the reason: two keys for one intent

    def test_a_key_is_not_enough_when_the_receiver_ignores_it(self):
        pipe = P.Pipeline(CONTRACT, retries={"notify": 1}, channel=P.LocalChannel(honours_keys=False))
        self.check("receiver_ignores_keys_after_effect", pipe,
                   run(pipe, "2026-03-02", faults=fault("after_effect", transient=True)))
        keys = [item["key"] for item in pipe.channel.delivered if item["recipient"] == "quality-lead"]
        self.assertEqual(len(set(keys)), 1)  # same key, sent twice: the receiver did not deduplicate

    def test_exhausted_retries_fail_the_run_and_a_repair_completes_it(self):
        exp = EXPECTED["retries"]["retries_exhausted"]
        pipe = P.Pipeline(CONTRACT, retries={"notify": 1})
        failed = run(pipe, "2026-03-02", faults=fault("after_effect", count=2, transient=True))
        self.assertEqual({"status": failed["status"], "attempt": failed["attempt"],
                          "notify_executions": executions(pipe, "line3-2026-03-02")["notify"],
                          "deliveries": recipients(pipe), "suppressed": pipe.channel.suppressed,
                          "outbox": outbox_counts(pipe), "alerts": alerts(pipe)}, exp["failed"])
        repaired = run(pipe, "2026-03-02")
        self.assertEqual({"status": repaired["status"], "attempt": repaired["attempt"],
                          "notify_executions": executions(pipe, "line3-2026-03-02")["notify"],
                          "deliveries": recipients(pipe), "suppressed": pipe.channel.suppressed,
                          "outbox": outbox_counts(pipe)}, exp["repaired"])

    def test_a_non_transient_error_is_not_retried(self):
        exp = EXPECTED["retries"]["non_transient_not_retried"]
        pipe = P.Pipeline(CONTRACT, retries={"ingest_raw": 2})
        outcome = run(pipe, "2026-03-04", path=FIX / "stale" / "2026-03-04.json")
        state = pipe.store.runs["line3-2026-03-04"]["tasks"]["ingest_raw"]
        self.assertEqual({"status": outcome["status"], "ingest_executions": state["executions"],
                          "reason": state["reason"]}, {k: exp[k] for k in ("status", "ingest_executions", "reason")})


class StaleInputTests(unittest.TestCase):
    """A green task over a stale input is not correct business data."""

    def setup_two_days(self, **kwargs):
        pipe = P.Pipeline(CONTRACT, **kwargs)
        run(pipe, "2026-03-02")
        run(pipe, "2026-03-03")
        return pipe

    def test_every_task_green_with_a_stale_input_publishes_wrong_business_data(self):
        exp = EXPECTED["stale"]["without_freshness_check"]
        pipe = self.setup_two_days(tasks={"ingest_raw": shortcuts.ingest_without_freshness})
        outcome = run(pipe, "2026-03-04", path=FIX / "stale" / "2026-03-04.json")
        self.assertEqual(outcome["status"], exp["status"])
        self.assertEqual(outcome["tasks"], exp["tasks"])
        published = pipe.store.reports["2026-03-04"]
        self.assertEqual(published["content"], REPORTS[exp["published"]]["content"])
        self.assertEqual(published["report_id"], REPORTS[exp["published"]]["report_id"])
        # The reason: the rows and totals are 2026-03-03's, and the correct 2026-03-04 report differs.
        self.assertEqual(published["content"]["rows"], REPORTS["2026-03-03"]["content"]["rows"])
        self.assertNotEqual(published["content"], REPORTS["2026-03-04"]["content"])
        stale_file = json.loads((FIX / "stale" / "2026-03-04.json").read_text(encoding="utf-8"))
        self.assertEqual(stale_file["business_date"], "2026-03-03")
        self.assertEqual(view(pipe, "2026-03-04"), exp["view"])
        self.assertEqual(len(pipe.channel.delivered), exp["deliveries_total"])
        self.assertEqual(len(pipe.store.alerts), exp["alerts"])
        OUTPUTS["stale_green_report"] = published["content"]

    def test_the_freshness_check_refuses_the_stale_input_and_keeps_the_previous_report_labelled(self):
        exp = EXPECTED["stale"]["with_freshness_check"]
        pipe = self.setup_two_days()
        outcome = run(pipe, "2026-03-04", path=FIX / "stale" / "2026-03-04.json")
        self.assertEqual(outcome["status"], exp["status"])
        self.assertEqual(outcome["tasks"], exp["tasks"])
        self.assertEqual(pipe.store.runs["line3-2026-03-04"]["tasks"]["ingest_raw"]["reason"], exp["reason"])
        self.assertEqual("2026-03-04" in pipe.store.raw and bool(pipe.store.raw["2026-03-04"]),
                         exp["raw_retained_for_date"])
        self.assertNotIn("2026-03-04", pipe.store.reports)
        self.assertEqual(view(pipe, "2026-03-04"), exp["view"])
        self.assertEqual(len(pipe.channel.delivered), exp["deliveries_total"])
        self.assertEqual(alerts(pipe), exp["alerts"])

    def test_a_repair_with_the_fresh_input_publishes_the_correct_report(self):
        exp = EXPECTED["stale"]["repaired_with_fresh_input"]
        pipe = self.setup_two_days()
        run(pipe, "2026-03-04", path=FIX / "stale" / "2026-03-04.json")
        outcome = run(pipe, "2026-03-04")
        self.assertEqual((outcome["status"], outcome["attempt"]), (exp["status"], exp["attempt"]))
        self.assertEqual(executions(pipe, "line3-2026-03-04"), exp["executions"])
        self.assertEqual(pipe.store.reports["2026-03-04"]["content"], REPORTS[exp["published"]]["content"])
        self.assertEqual(view(pipe, "2026-03-04"), exp["view"])
        self.assertEqual(len(pipe.channel.delivered), exp["deliveries_total"])


class BackfillTests(unittest.TestCase):
    """A missed date is backfilled from its own retained input without moving the current report."""

    def setup_gap(self):
        pipe = P.Pipeline(CONTRACT)
        run(pipe, "2026-03-02")
        run(pipe, "2026-03-04")
        return pipe

    def deliveries(self, pipe):
        return [[d["recipient"], d["report_date"], d["backfill"]] for d in pipe.channel.delivered]

    def test_a_backfill_publishes_the_missed_date_and_leaves_the_current_report_alone(self):
        exp = EXPECTED["backfill"]
        pipe = self.setup_gap()
        self.assertEqual(view(pipe, "2026-03-03"), exp["before_backfill"]["view_2026_03_03"])
        self.assertEqual(view(pipe, "2026-03-04"), exp["before_backfill"]["view_2026_03_04"])
        outcome = run(pipe, "2026-03-03")
        self.assertEqual(outcome["status"], exp["backfill"]["status"])
        self.assertEqual(pipe.store.runs["line3-2026-03-03"]["tasks"]["publish_report"]["detail"]["action"],
                         exp["backfill"]["publish_action"])
        self.assertEqual(pipe.store.reports["2026-03-03"]["backfill"], exp["backfill"]["backfill_flag"])
        self.assertEqual(pipe.store.reports["2026-03-03"]["content"], REPORTS["2026-03-03"]["content"])
        self.assertEqual(view(pipe, "2026-03-03"), exp["backfill"]["view_2026_03_03"])
        self.assertEqual(view(pipe, "2026-03-04"), exp["backfill"]["view_2026_03_04"])
        self.assertEqual(self.deliveries(pipe), exp["backfill"]["deliveries"])
        OUTPUTS["backfill_deliveries"] = pipe.channel.delivered

    def test_rerunning_a_succeeded_run_id_changes_nothing(self):
        exp = EXPECTED["backfill"]["rerun_same_run_id"]
        pipe = self.setup_gap()
        run(pipe, "2026-03-03")
        outcome = run(pipe, "2026-03-03")
        self.assertEqual({"status": outcome["status"], "attempt": outcome["attempt"],
                          "deliveries_total": len(pipe.channel.delivered)}, exp)

    def test_a_repair_does_not_reread_input_that_arrived_after_success(self):
        exp = EXPECTED["backfill"]["repair_does_not_reread_new_input"]
        pipe = self.setup_gap()
        run(pipe, "2026-03-03")
        outcome = run(pipe, "2026-03-03", path=FIX / "late" / "2026-03-03-correction.json")
        self.assertEqual(outcome["status"], exp["status"])
        self.assertEqual(sorted(pipe.store.raw["2026-03-03"]), exp["retained_events_for_date"])
        self.assertEqual(pipe.store.reports["2026-03-03"]["report_id"], REPORTS[exp["report"]]["report_id"])

    def test_a_new_run_picks_up_the_correction_and_announces_the_new_report(self):
        exp = EXPECTED["backfill"]["new_run_for_correction"]
        pipe = self.setup_gap()
        run(pipe, "2026-03-03")
        outcome = run(pipe, "2026-03-03", path=FIX / "late" / "2026-03-03-correction.json", run_id=exp["run_id"])
        tasks = pipe.store.runs[exp["run_id"]]["tasks"]
        self.assertEqual(outcome["status"], exp["status"])
        self.assertEqual(tasks["ingest_raw"]["detail"], exp["ingest_detail"])
        self.assertEqual(tasks["publish_report"]["detail"]["action"], exp["publish_action"])
        report = pipe.store.reports["2026-03-03"]
        self.assertEqual((report["content"], report["report_id"]),
                         (REPORTS[exp["report"]]["content"], REPORTS[exp["report"]]["report_id"]))
        self.assertEqual([old["report_id"] for old in pipe.store.report_history],
                         [REPORTS[name]["report_id"] for name in exp["history"]])
        self.assertEqual(report["backfill"], exp["backfill_flag"])
        self.assertEqual(len(pipe.channel.delivered), exp["deliveries_total"])
        self.assertEqual(self.deliveries(pipe)[-2:], exp["new_deliveries"])

    def test_a_conflicting_redelivery_blocks_publication_without_undoing_the_report(self):
        exp = EXPECTED["backfill"]["conflicting_redelivery"]
        pipe = self.setup_gap()
        run(pipe, "2026-03-03")
        run(pipe, "2026-03-03", path=FIX / "late" / "2026-03-03-correction.json", run_id="line3-2026-03-03-late")
        outcome = run(pipe, "2026-03-03", path=FIX / "late" / "2026-03-03-conflict.json", run_id=exp["run_id"])
        tasks = pipe.store.runs[exp["run_id"]]["tasks"]
        self.assertEqual((outcome["status"], outcome["tasks"]), (exp["status"], exp["tasks"]))
        self.assertEqual(tasks["ingest_raw"]["detail"], exp["ingest_detail"])
        self.assertEqual(tasks["resolve"]["detail"], exp["resolve_detail"])
        self.assertEqual(pipe.store.resolved["2026-03-03"]["conflicts"], exp["conflicts"])
        self.assertEqual(tasks["publish_report"]["reason"], exp["publish_reason"])
        shown = P.report_view(pipe.store, "2026-03-03")
        expected_view = exp["view_2026_03_03"]
        self.assertEqual((shown["status"], shown["report_date"], shown["report_id"]),
                         (expected_view["status"], expected_view["report_date"],
                          REPORTS[expected_view["report"]]["report_id"]))
        self.assertEqual(pipe.store.raw["2026-03-03"]["e07"]["defective"], exp["retained_e07_defective"])
        self.assertEqual(len(pipe.channel.delivered), exp["deliveries_total"])
        self.assertEqual(len(pipe.store.alerts), exp["alerts"])


class RunbookTests(unittest.TestCase):
    """diagnose() names each failure state from the evidence it leaves, as RUNBOOK.md's table does."""

    def check(self, name: str, pipe, run_id: str):
        exp = EXPECTED["runbook"][name]
        got = pipe.diagnose(run_id)
        self.assertEqual(got, {key: exp[key] for key in ("failed_task", "boundary", "action", "evidence")}, name)
        OUTPUTS[f"runbook_{name}"] = got

    def test_the_four_boundaries_are_named_from_evidence(self):
        for boundary in BOUNDARIES:
            with self.subTest(boundary=boundary):
                pipe, _ = boundary_setup(boundary)
                self.check(boundary, pipe, "line3-2026-03-03")

    def test_an_effect_cannot_be_placed_when_the_receiver_cannot_answer(self):
        pipe, _ = boundary_setup("after_effect", channel=P.LocalChannel(honours_keys=False))
        self.check("effect_unknown", pipe, "line3-2026-03-03")
        self.assertEqual(len(pipe.channel.delivered), 3)

    def test_stale_input_and_a_refused_gate_are_named_from_the_recorded_reason(self):
        pipe = P.Pipeline(CONTRACT)
        run(pipe, "2026-03-04", path=FIX / "stale" / "2026-03-04.json")
        self.check("stale_input", pipe, "line3-2026-03-04")
        transfer = P.Pipeline(TCONTRACT)
        transfer.run("harbour-2026-03-06", "2026-03-06", TFIX / "landing" / "2026-03-06.json")
        self.check("publication_gate", transfer, "harbour-2026-03-06")

    def test_a_clean_run_needs_no_action(self):
        pipe = P.Pipeline(CONTRACT)
        run(pipe, "2026-03-02")
        self.check("none", pipe, "line3-2026-03-02")


class TransferTests(unittest.TestCase):
    """The same recovery rules on another contract: a composite key and three recipients."""

    exp = EXPECTED["transfer"]

    def first_day(self, **kwargs):
        pipe = P.Pipeline(TCONTRACT, **kwargs)
        pipe.run("harbour-2026-03-05", "2026-03-05", TFIX / "landing" / "2026-03-05.json",
                 P.Faults({"after_resolution": 1}))
        return pipe

    def correct(self, pipe):
        pipe.run("harbour-2026-03-05", "2026-03-05", TFIX / "landing" / "2026-03-05.json")
        return pipe.run("harbour-2026-03-05-c1", "2026-03-05", TFIX / "correction" / "2026-03-05.json")

    def test_a_first_day_failure_leaves_nothing_to_show(self):
        exp = self.exp["failed_after_resolution"]
        pipe = self.first_day()
        record = pipe.store.runs[exp["run_id"]]
        self.assertEqual(record["status"], exp["status"])
        self.assertEqual({t: s["status"] for t, s in record["tasks"].items()}, exp["tasks"])
        self.assertEqual(view(pipe, "2026-03-05"), exp["view"])
        self.assertEqual(pipe.evidence(exp["run_id"]), exp["evidence"])

    def test_the_repair_publishes_both_docks_for_one_trailer(self):
        exp = self.exp["repaired"]
        pipe = self.first_day()
        outcome = pipe.run("harbour-2026-03-05", "2026-03-05", TFIX / "landing" / "2026-03-05.json")
        self.assertEqual((outcome["status"], outcome["attempt"]), (exp["status"], exp["attempt"]))
        self.assertEqual(executions(pipe, "harbour-2026-03-05"), exp["executions"])
        report = pipe.store.reports["2026-03-05"]
        self.assertEqual(report["content"], TREPORTS["2026-03-05"]["content"])
        self.assertEqual(report["report_id"], TREPORTS["2026-03-05"]["report_id"])
        self.assertEqual(pipe.store.runs["harbour-2026-03-05"]["tasks"]["ingest_raw"]["detail"],
                         TREPORTS["2026-03-05"]["retention"])
        self.assertEqual([[r["dock"], r["trailer"]] for r in report["content"]["rows"] if r["trailer"] == "T-88"],
                         [["D1", "T-88"], ["D2", "T-88"]])
        self.assertEqual(delivered_for(pipe, "2026-03-05"), exp["deliveries"])
        OUTPUTS["transfer_report"] = report["content"]

    def test_a_corrected_report_gets_a_new_identity_and_its_own_notifications(self):
        exp = self.exp["correction_run"]
        pipe = self.first_day()
        outcome = self.correct(pipe)
        self.assertEqual(outcome["status"], exp["status"])
        self.assertEqual(pipe.store.runs[exp["run_id"]]["tasks"]["publish_report"]["detail"]["action"],
                         exp["publish_action"])
        report = pipe.store.reports["2026-03-05"]
        self.assertEqual(report["content"], TREPORTS["2026-03-05-corrected"]["content"])
        self.assertEqual(report["report_id"], TREPORTS["2026-03-05-corrected"]["report_id"])
        self.assertEqual(len(pipe.store.report_history), exp["history"])
        self.assertEqual(pipe.store.report_history[0]["report_id"], TREPORTS["2026-03-05"]["report_id"])
        self.assertEqual(len(pipe.channel.delivered), exp["deliveries_total"])
        new = pipe.channel.delivered[-3:]
        self.assertEqual([[d["recipient"], d["report_date"]] for d in new], exp["new_deliveries"])
        self.assertEqual({d["report_id"] for d in new}, {TREPORTS["2026-03-05-corrected"]["report_id"]})
        OUTPUTS["transfer_corrected"] = report["content"]

    def test_a_key_without_the_report_identity_hides_the_correction(self):
        exp = self.exp["coarse_key_after_correction"]
        pipe = self.first_day(key_fn=shortcuts.coarse_key)
        self.correct(pipe)
        entries = list(pipe.store.outbox.values())
        self.assertEqual(len(pipe.channel.delivered), exp["deliveries_total"])
        self.assertEqual(len(entries), exp["outbox_entries"])
        self.assertEqual(all(e["state"] == "sent" for e in entries), exp["outbox_all_sent"])
        # The reason: every entry still names the replaced report, while readers now see the corrected one.
        self.assertEqual({e["report_id"] for e in entries} == {TREPORTS["2026-03-05"]["report_id"]},
                         exp["outbox_report_is_the_replaced_one"])
        self.assertEqual(pipe.store.reports["2026-03-05"]["report_id"], TREPORTS["2026-03-05-corrected"]["report_id"])

    def test_a_conflict_blocks_the_new_day_and_labels_the_previous_report_stale(self):
        exp = self.exp["conflict_day"]
        pipe = self.first_day()
        self.correct(pipe)
        outcome = pipe.run(exp["run_id"], "2026-03-06", TFIX / "landing" / "2026-03-06.json")
        self.assertEqual((outcome["status"], outcome["tasks"]), (exp["status"], exp["tasks"]))
        self.assertEqual(pipe.store.runs[exp["run_id"]]["tasks"]["publish_report"]["reason"], exp["publish_reason"])
        self.assertEqual(pipe.store.resolved["2026-03-06"]["conflicts"], exp["conflicts"])
        self.assertNotIn("2026-03-06", pipe.store.reports)
        shown = P.report_view(pipe.store, "2026-03-06")
        self.assertEqual((shown["status"], shown["report_date"], shown["report_id"]),
                         (exp["view"]["status"], exp["view"]["report_date"],
                          TREPORTS[exp["view"]["report"]]["report_id"]))
        self.assertEqual(len(pipe.channel.delivered), exp["deliveries_total"])
        self.assertEqual(alerts(pipe), exp["alerts"])
        OUTPUTS["transfer_alerts"] = pipe.store.alerts


    def test_a_superseding_version_clears_the_conflict_in_a_new_run(self):
        exp = self.exp["conflict_superseded"]
        pipe = self.first_day()
        self.correct(pipe)
        pipe.run("harbour-2026-03-06", "2026-03-06", TFIX / "landing" / "2026-03-06.json")
        repair = pipe.run("harbour-2026-03-06", "2026-03-06", TFIX / "landing" / "2026-03-06.json")
        self.assertEqual({"status": repair["status"],
                          "publish_reason": pipe.store.runs["harbour-2026-03-06"]["tasks"]["publish_report"]["reason"],
                          "deliveries_total": len(pipe.channel.delivered)}, exp["same_run_id_repair"])
        outcome = pipe.run(exp["run_id"], "2026-03-06", TFIX / "correction" / "2026-03-06.json")
        tasks = pipe.store.runs[exp["run_id"]]["tasks"]
        self.assertEqual(outcome["status"], exp["status"])
        self.assertEqual(tasks["ingest_raw"]["detail"], TREPORTS["2026-03-06-corrected"]["retention"])
        self.assertEqual(tasks["resolve"]["detail"], exp["resolve_detail"])
        self.assertEqual(tasks["publish_report"]["detail"]["action"], exp["publish_action"])
        report = pipe.store.reports["2026-03-06"]
        self.assertEqual((report["content"], report["report_id"]),
                         (TREPORTS["2026-03-06-corrected"]["content"], TREPORTS["2026-03-06-corrected"]["report_id"]))
        self.assertEqual(view(pipe, "2026-03-06"), exp["view"])
        self.assertEqual(len(pipe.channel.delivered), exp["deliveries_total"])


class StarterTests(unittest.TestCase):
    """The starter's six gaps are marked and raise until they are filled."""

    def test_the_starter_marks_six_gaps(self):
        source = (ROOT / "starters" / "pipeline.py").read_text(encoding="utf-8")
        for number in range(1, 7):
            self.assertEqual(source.count(f'raise NotImplementedError("GAP {number}:'), 1, number)
        self.assertEqual(source.count("raise NotImplementedError"), 6)
        self.assertNotIn("NotImplementedError", (ROOT / "solutions" / "pipeline.py").read_text(encoding="utf-8"))

    def test_the_unfilled_starter_stops_at_its_first_gap(self):
        starter = import_module("starters.pipeline")
        pipe = starter.Pipeline(CONTRACT)
        with self.assertRaises(NotImplementedError) as caught:
            pipe.run("line3-2026-03-02", "2026-03-02", landing("2026-03-02"))
        self.assertTrue(str(caught.exception).startswith("GAP 1"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--starter", action="store_true",
                        help="test your completed starters/pipeline.py instead of the reference solution")
    args = parser.parse_args()
    if args.starter and args.evidence:
        parser.error("evidence records the reference solution only; drop --evidence when using --starter")
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    suite = unittest.TestSuite()
    cases = [ResolutionTests, BoundaryTests, RetryTests, StaleInputTests, BackfillTests, RunbookTests, TransferTests]
    if not args.starter:  # the gap checks only make sense on the untouched starter
        cases.append(StarterTests)
    for case in cases:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    exit_code = 0 if result.wasSuccessful() else 1

    def hashes(directory: str) -> dict[str, str]:
        return {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path.read_bytes()).hexdigest()
                for path in sorted((ROOT / directory).rglob("*")) if path.is_file()}

    evidence = {
        "lab": LAB, "executionClass": "local-executed",
        "python": platform.python_version(), "implementation": platform.python_implementation(),
        "interpreter": sys.executable, "inVirtualEnvironment": sys.prefix != sys.base_prefix,
        "packages": {},
        "standardLibrary": ["argparse", "datetime", "hashlib", "importlib", "json", "pathlib", "platform",
                            "sys", "time", "unittest"],
        "java": "not used", "spark": "not used", "platform": platform.system() + " " + platform.release(),
        "startedAt": started_at.isoformat(), "finishedAt": datetime.now(timezone.utc).isoformat(),
        "durationSeconds": round(time.monotonic() - started, 3),
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "exit": exit_code,
        "moduleUnderTest": P.__name__,
        "fixtureHashes": hashes("fixtures"), "expectedHashes": hashes("expected"),
        "solutionHashes": {**hashes("solutions"), **hashes("starters"),
                           "run_tests.py": sha256((ROOT / "run_tests.py").read_bytes()).hexdigest()},
        "outputHashes": {name: sha256(canonical(value).encode("utf-8")).hexdigest()
                         for name, value in sorted(OUTPUTS.items())},
        "commands": [f"{Path(sys.executable).name} run_tests.py --evidence <path>"],
        "notes": ("Plain CPython standard library on one machine: no packages, no network, no scheduler "
                  "service and no Databricks workspace. A local runner executes four tasks (ingest_raw, "
                  "resolve, publish_report, notify) with a per-run-id ledger; failures are injected at four "
                  "named boundaries and recovery re-runs the same run id, reusing succeeded tasks. The only "
                  "external effect is a local channel that appends to a Python list; no message is sent. "
                  "Expected values are hand-derived literals in expected/*.json (derivations in DATA.md); "
                  "report identities are also checked against a digest written independently in run_tests.py. "
                  "The no-key, no-freshness, fresh-key-per-try and coarse-key shortcuts in starters/ are "
                  "asserted to fail for their documented reasons; the starter's six gaps are asserted to be "
                  "marked. Cinderline Components and Harbourline, their lots, docks, trailers and recipients "
                  "are fictional."),
    }
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence[key] for key in ("lab", "python", "tests", "failures", "errors", "skipped", "exit")},
                     indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
