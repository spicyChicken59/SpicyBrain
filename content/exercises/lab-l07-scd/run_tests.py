"""Lab L07 runner: SCD Type 1 and Type 2 reference transformations on local Spark 4.0.4.

    python run_tests.py --evidence local-evidence.json

(after creating a virtual environment with requirements.txt installed, as README.md shows)

Offline, one machine, local[2], UI off, two shuffle partitions, Spark's scratch
files in a temporary directory deleted at the end. Every table the reference
produces with the DataFrame API or with Spark SQL is held to the hand-authored
literals in expected/*.json; the deliberately broken cases must fail for the
reason each one names.
"""
import sys

sys.dont_write_bytecode = True  # leave no __pycache__ inside the package

import argparse
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from solutions.scd_reference import (  # noqa: E402
    CINDERLINE, MARLOW_COMPOSITE, MARLOW_SINGLE, SPARK_CONFIG, SUPPLIERS, ScdContractError, build_session,
    check_current_unique, check_intervals, load_events, reasons, resolve, rows, scd_tables, scd_tables_sql,
    snapshot_changes)
from starters.scd_task import append_per_arrival, last_arrival_wins  # noqa: E402

LAB = "lab-l07-scd"
EXECUTION_CLASS = "local-executed"
OUTPUTS = {}
STATE = {}


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def authored(value):
    """Expected literals without the explanatory keys that start with an underscore."""
    if isinstance(value, dict):
        return {k: authored(v) for k, v in value.items() if not k.startswith("_")}
    if isinstance(value, list):
        return [authored(v) for v in value]
    return value


EVENTS = load("fixtures/cinderline-events.json")
MARLOW = load("fixtures/marlow-events.json")
SNAPSHOTS = load("fixtures/supplier-snapshots.json")["snapshots"]
CIN = authored(load("expected/cinderline.json"))       # authored by hand; see DATA.md
MAR = authored(load("expected/marlow.json"))
SNAP = authored(load("expected/snapshots.json"))
EVIDENCE_KEYS = ("raw_count", "distinct_deliveries", "orderable_states", "quarantine", "duplicate_deliveries",
                 "unresolved", "excluded")


def through(events, batch):
    return [e for e in events if e["batch"] <= batch]


def canonical(value):
    return json.dumps(value, sort_keys=True, default=str)


def difference(before, after):
    """Rows in `after` and not in `before`, compared as whole rows, in `after`'s order."""
    seen = {canonical(r) for r in before}
    return [r for r in after if canonical(r) not in seen]


class ScdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        STATE["scratch"] = tempfile.mkdtemp(prefix="lab-l07-")
        cls.spark = build_session("SpicyBrain lab L07 tests", STATE["scratch"])
        OUTPUTS["spark_version"] = cls.spark.version

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
        shutil.rmtree(STATE["scratch"], ignore_errors=True)
        OUTPUTS["temp_dir_removed"] = not Path(STATE["scratch"]).exists()

    # -- helpers -------------------------------------------------------------------

    def tables(self, events, contract, sql=False, view="lab_l07_states"):
        resolution = resolve(events, contract)
        if sql:
            current, history = scd_tables_sql(self.spark, resolution, contract, view)
        else:
            current, history = scd_tables(self.spark, resolution, contract)
        return resolution, rows(current, contract), rows(history, contract)

    def assert_evidence(self, resolution, expected, keys=EVIDENCE_KEYS):
        for key in keys:
            self.assertEqual(resolution[key], expected[key], key)

    def assert_invariants(self, current, history, key):
        check_current_unique(current, key)
        return check_intervals(history, key)

    # -- the contract before any table -----------------------------------------------

    def test_01_validator_names_every_reason(self):
        observed = [reasons(case["event"], CINDERLINE) for case in CIN["validator_cases"]]
        self.assertEqual(observed, [case["reasons"] for case in CIN["validator_cases"]])
        OUTPUTS["validator_cases"] = observed

    def test_02_evidence_over_all_three_batches(self):
        resolution = resolve(EVENTS, CINDERLINE)
        self.assert_evidence(resolution, CIN, EVIDENCE_KEYS + ("redundant_evidence", "event_conflicts"))
        # A quarantined event is still a delivery; only the identical e-05 redelivery collapses.
        self.assertEqual(resolution["raw_count"] - resolution["distinct_deliveries"], 1)
        OUTPUTS["evidence_full"] = {k: v for k, v in resolution.items() if k not in ("states", "withheld_states")}

    # -- Type 1 and Type 2, batch by batch -------------------------------------------------

    def check_stage(self, batch, expected):
        resolution, current, history = self.tables(through(EVENTS, batch), CINDERLINE)
        self.assert_evidence(resolution, expected)
        self.assertEqual(current, expected["current"])
        self.assertEqual(history, expected["history"])
        self.assertEqual(self.assert_invariants(current, history, "part_id"), expected["gaps"])
        return {"current": current, "history": history}

    def test_03_batch_one_opens_one_version_per_part(self):
        OUTPUTS["batch1"] = self.check_stage(1, CIN["stages"]["batch1"])
        self.assertTrue(all(row["is_current"] for row in OUTPUTS["batch1"]["history"]))

    def test_04_batch_two_delete_closes_and_invalid_order_withholds(self):
        OUTPUTS["batch2"] = observed = self.check_stage(2, CIN["stages"]["batch2"])
        # P-200's delete at seq 2 closed its only row and opened none: no current row, no open row.
        self.assertNotIn("P-200", [r["part_id"] for r in observed["current"]])
        self.assertEqual([r["valid_to"] for r in observed["history"] if r["part_id"] == "P-200"], [[2]])
        # P-400's second event says seq "2", a string: the key is withheld from both tables, not coerced.
        self.assertNotIn("P-400", {r["part_id"] for r in observed["current"] + observed["history"]})

    def test_05_all_three_batches_dataframe_api(self):
        _, current, history = self.tables(EVENTS, CINDERLINE)
        self.assertEqual(current, CIN["current"])
        self.assertEqual(history, CIN["history"])
        self.assertEqual(self.assert_invariants(current, history, "part_id"), CIN["gaps"])
        OUTPUTS["batch3"] = {"current": current, "history": history}

    def test_06_spark_sql_reaches_the_same_literals(self):
        _, current, history = self.tables(EVENTS, CINDERLINE, sql=True, view="cinderline_states")
        self.assertEqual(current, CIN["current"])
        self.assertEqual(history, CIN["history"])
        _, current, history = self.tables(MARLOW, MARLOW_COMPOSITE, sql=True, view="marlow_states")
        self.assertEqual(current, MAR["composite"]["current"])
        self.assertEqual(history, MAR["composite"]["history"])
        OUTPUTS["sql_marlow_composite"] = {"current": current, "history": history}

    def test_07_type1_equals_the_open_type2_rows(self):
        scenarios = [(through(EVENTS, b), CINDERLINE) for b in (1, 2, 3)]
        scenarios += [(MARLOW, MARLOW_COMPOSITE), (MARLOW, MARLOW_SINGLE),
                      (snapshot_changes(SNAPSHOTS, SUPPLIERS), SUPPLIERS)]
        checked = 0
        for events, contract in scenarios:
            _, current, history = self.tables(events, contract)
            open_rows = [{contract.key: r[contract.key], "sequence": r["valid_from"],
                          **{c: r[c] for c in contract.attributes}} for r in history if r["is_current"]]
            self.assertEqual(current, open_rows, contract.label)
            checked += len(current)
        OUTPUTS["type1_type2_cross_check_rows"] = checked

    # -- late arrival, replay and a drop-style filter ------------------------------------

    def test_08_late_arrival_rewrites_history_but_not_the_present(self):
        _, current2, history2 = self.tables(through(EVENTS, 2), CINDERLINE)
        _, current3, history3 = self.tables(EVENTS, CINDERLINE)
        changes = CIN["batch3_changes"]
        observed = {"current_removed": difference(current3, current2), "current_added": difference(current2, current3),
                    "history_removed": difference(history3, history2), "history_added": difference(history2, history3)}
        self.assertEqual(observed, changes)
        # The late seq 2 changed nothing current for P-100 ...
        p100 = [r for r in current3 if r["part_id"] == "P-100"]
        self.assertEqual(p100, [r for r in current2 if r["part_id"] == "P-100"])
        # ... but an append-only history could not absorb it: a closed row's valid_to moved from [3] to [2].
        self.assertIn([1], [r["valid_from"] for r in observed["history_removed"] if r["part_id"] == "P-100"])
        OUTPUTS["batch3_changes"] = observed

    def test_09_replaying_batch_three_changes_nothing(self):
        replayed = EVENTS + [e for e in EVENTS if e["batch"] == 3]
        resolution, current, history = self.tables(replayed, CINDERLINE)
        expected = CIN["replay_batch3"]
        self.assertEqual(resolution["raw_count"], expected["raw_count"])
        self.assertEqual(resolution["distinct_deliveries"], expected["distinct_deliveries"])
        self.assertEqual([d["event_id"] for d in resolution["duplicate_deliveries"]], expected["duplicate_event_ids"])
        self.assertEqual(resolution["quarantine"], expected["quarantine"])
        self.assertEqual((current, history), (CIN["current"], CIN["history"]))
        self.assertEqual(resolution["unresolved"], CIN["unresolved"])
        OUTPUTS["replay"] = {"raw_count": resolution["raw_count"], "distinct": resolution["distinct_deliveries"]}

    def test_10_dropping_invalid_rows_publishes_a_stale_row(self):
        kept = [e for e in EVENTS if not reasons(e, CINDERLINE)]
        resolution, current, _ = self.tables(kept, CINDERLINE)
        expected = CIN["drop_filtered"]
        self.assertEqual(len(kept), expected["kept_count"])
        self.assertEqual(resolution["quarantine"], expected["quarantine"])
        self.assertEqual(resolution["excluded"], expected["excluded"])
        self.assertEqual(sorted({u["part_id"] for u in resolution["unresolved"]}), expected["unresolved_keys"])
        self.assertEqual(current, expected["current"])
        # The reference withholds P-400; the drop-style filter publishes its seq 1 row as if it were current.
        self.assertNotIn("P-400", [r["part_id"] for r in CIN["current"]])
        OUTPUTS["drop_filtered_current"] = current

    # -- deliberately wrong approaches and broken tables --------------------------------

    def test_11_negative_last_arrival_wins(self):
        observed = last_arrival_wins(EVENTS)
        self.assertEqual(observed, CIN["negative"]["last_arrival_wins"])
        reference = {r["part_id"]: r for r in CIN["current"]}
        # Wrong for the reason TASKS.md names: arrival order let the late seq 2 overwrite seq 3.
        self.assertEqual(observed["P-100"]["unit_cost_cents"], 1290)
        self.assertEqual(reference["P-100"]["unit_cost_cents"], 1310)
        # And it publishes keys the contract cannot resolve: the P-300 tie and the unorderable P-400.
        self.assertTrue({"P-300", "P-400"} <= set(observed) and not {"P-300", "P-400"} & set(reference))
        OUTPUTS["negative_last_arrival_wins"] = observed

    def test_12_negative_append_per_arrival_breaks_interval_order(self):
        with self.assertRaises(ScdContractError) as raised:
            check_intervals(append_per_arrival(EVENTS), "part_id")
        expected = CIN["negative"]["append_per_arrival"]
        self.assertEqual(raised.exception.reason, expected["reason"])
        self.assertEqual(raised.exception.key, expected["part_id"])
        self.assertEqual((raised.exception.row["valid_from"], raised.exception.row["valid_to"]),
                         (expected["valid_from"], expected["valid_to"]))
        OUTPUTS["negative_append_per_arrival"] = {"reason": raised.exception.reason, "key": raised.exception.key}

    def test_13_invariant_checks_reject_broken_tables(self):
        broken = CIN["broken_tables"]
        current = [dict(r) for r in CIN["current"]]
        duplicate = current + [dict(current[0], unit_cost_cents=1290, sequence=[2])]
        overlap = [dict(r) for r in CIN["history"]]
        overlap[0]["valid_to"] = [3]                      # P-100 [1,3) now overlaps [2,3)
        two_open = [dict(r) for r in CIN["history"]]
        two_open[6]["valid_to"], two_open[6]["is_current"] = None, True   # P-600's first version reopened
        observed = {}
        for name, call in (("duplicate_current", lambda: check_current_unique(duplicate, "part_id")),
                           ("overlap", lambda: check_intervals(overlap, "part_id")),
                           ("two_open_rows", lambda: check_intervals(two_open, "part_id"))):
            with self.assertRaises(ScdContractError) as raised:
                call()
            observed[name] = {"reason": raised.exception.reason, "key": raised.exception.key}
        self.assertEqual(observed, broken)
        # The unbroken tables pass the same checks.
        self.assertEqual(self.assert_invariants(CIN["current"], CIN["history"], "part_id"), CIN["gaps"])
        OUTPUTS["broken_tables"] = observed

    # -- transfer: another domain, a composite sequence, snapshots -----------------------

    def test_14_transfer_composite_sequence_orders_the_revision(self):
        expected = MAR["composite"]
        resolution, current, history = self.tables(MARLOW, MARLOW_COMPOSITE)
        self.assert_evidence(resolution, expected, EVIDENCE_KEYS + ("redundant_evidence",))
        self.assertEqual(current, expected["current"])
        self.assertEqual(history, expected["history"])
        self.assertEqual(self.assert_invariants(current, history, "customer_id"), expected["gaps"])
        OUTPUTS["marlow_composite"] = {"current": current, "history": history}

    def test_15_transfer_single_sequence_leaves_a_tie(self):
        expected = MAR["single"]
        resolution, current, history = self.tables(MARLOW, MARLOW_SINGLE)
        self.assert_evidence(resolution, expected, EVIDENCE_KEYS + ("redundant_evidence",))
        self.assertEqual(current, expected["current"])
        self.assertEqual(history, expected["history"])
        self.assertEqual(self.assert_invariants(current, history, "customer_id"), expected["gaps"])
        # Same events, narrower contract: C-1 goes from three versions to withheld.
        self.assertEqual(resolution["unresolved"][0]["reason"], "tied_sequence")
        OUTPUTS["marlow_single"] = {"unresolved": resolution["unresolved"], "current": current}

    def test_16_snapshot_differences_become_a_change_feed(self):
        expected = SNAP["all_three"]
        changes = snapshot_changes(SNAPSHOTS, SUPPLIERS)
        self.assertEqual(changes, expected["changes"])
        counts = {}
        for change in changes:
            counts.setdefault(str(change["snapshot_no"]), {"upsert": 0, "delete": 0})[change["op"]] += 1
        self.assertEqual(counts, expected["change_counts"])
        resolution, current, history = self.tables(changes, SUPPLIERS)
        self.assertEqual(resolution["orderable_states"], expected["orderable_states"])
        self.assertEqual(current, expected["current"])
        self.assertEqual(history, expected["history"])
        self.assertEqual(self.assert_invariants(current, history, "supplier_code"), expected["gaps"])
        OUTPUTS["snapshots_all_three"] = {"changes": changes, "history": history}

    def test_17_a_skipped_snapshot_hides_a_version(self):
        expected = SNAP["skip_second"]
        kept = [s for s in SNAPSHOTS if s["snapshot_no"] in expected["snapshot_numbers"]]
        changes = snapshot_changes(kept, SUPPLIERS)
        self.assertEqual([c for c in changes if c["snapshot_no"] == 3], expected["changes_at_3"])
        _, _, history = self.tables(changes, SUPPLIERS)
        self.assertEqual(history, expected["history"])
        _, _, full = self.tables(snapshot_changes(SNAPSHOTS, SUPPLIERS), SUPPLIERS)
        invisible = expected["invisible"]
        key = invisible["supplier_code"]
        self.assertEqual(len([r for r in full if r["supplier_code"] == key]), invisible["versions_with_all_three"])
        self.assertEqual(len([r for r in history if r["supplier_code"] == key]), invisible["versions_with_two"])
        self.assertIn(invisible["unseen_lead_days"], [r["lead_days"] for r in full if r["supplier_code"] == key])
        self.assertNotIn(invisible["unseen_lead_days"], [r["lead_days"] for r in history if r["supplier_code"] == key])
        OUTPUTS["snapshots_skip_second"] = {"changes": changes, "history": history}


def file_hashes(directory, suffixes=(".json", ".csv", ".py", ".md", ".txt")):
    return {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path.read_bytes()).hexdigest()
            for path in sorted((ROOT / directory).rglob("*")) if path.is_file() and path.suffix in suffixes}


def java_version():
    home = os.environ.get("JAVA_HOME")
    java = str(Path(home) / "bin" / ("java.exe" if os.name == "nt" else "java")) if home else "java"
    try:
        text = subprocess.run([java, "-version"], capture_output=True, text=True).stderr
    except OSError as error:
        return "unavailable: %s" % error
    match = re.search(r'version "([^"]+)"', text)
    return match.group(1) if match else text.strip()


def pipelines_check():
    """What this interpreter's PySpark offers for declarative pipelines (booleans only, no paths)."""
    import pyspark
    return {
        "pyspark.pipelines importable": importlib.util.find_spec("pyspark.pipelines") is not None,
        "spark-pipelines launcher in pyspark/bin": (Path(pyspark.__file__).parent / "bin" / "spark-pipelines").exists(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--evidence", type=Path, help="write evidence JSON to this path")
    parser.add_argument("--outputs", type=Path, help="also write every collected output to this JSON path")
    args = parser.parse_args()
    import py4j
    import pyspark
    started = datetime.now(timezone.utc)
    clock = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ScdTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finished = datetime.now(timezone.utc)
    exit_code = 0 if result.wasSuccessful() and result.testsRun > 0 and not result.skipped else 1
    OUTPUTS["pipelines_check"] = pipelines_check()
    evidence = {
        "lab": LAB, "executionClass": EXECUTION_CLASS, "runtime": "spark",
        "interpreter": sys.executable,
        "python": platform.python_version(), "java": java_version(),
        "packages": {"pyspark": pyspark.__version__, "py4j": py4j.__version__},
        "spark": OUTPUTS.get("spark_version", "not started"),
        "master": "local[2]",
        "sparkConfig": dict(SPARK_CONFIG, **{"spark.local.dir": "a runner-created temporary directory, deleted after the run",
                                             "spark.sql.warehouse.dir": "inside the same temporary directory; no table is written"}),
        "platform": "%s %s (%s)" % (platform.system(), platform.release(), platform.machine()),
        "startedAt": started.isoformat(), "finishedAt": finished.isoformat(),
        "durationSeconds": round(time.monotonic() - clock, 3),
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "exit": exit_code,
        "fixtureHashes": dict(file_hashes("fixtures"), **file_hashes("expected")),
        "solutionHashes": dict(file_hashes("solutions"), **file_hashes("starters"),
                               **{"run_tests.py": sha256((ROOT / "run_tests.py").read_bytes()).hexdigest()}),
        "outputHashes": {name: sha256(canonical(value).encode("utf-8")).hexdigest()
                         for name, value in sorted(OUTPUTS.items())},
        "observations": {
            "pipelinesCheck": OUTPUTS.get("pipelines_check"),
            "batch3Changes": OUTPUTS.get("batch3_changes"),
            "negativeAppendPerArrival": OUTPUTS.get("negative_append_per_arrival"),
            "brokenTables": OUTPUTS.get("broken_tables"),
            "tempDirRemoved": OUTPUTS.get("temp_dir_removed"),
        },
        "commands": [" ".join([sys.executable] + sys.argv)],
        "notes": ("Local Apache Spark %s on one machine (local[2], UI off, 2 shuffle partitions, UTC); no Databricks, "
                  "Delta Lake, declarative pipeline, network call or external effect. The SCD tables are computed by "
                  "Spark window functions (DataFrame API and Spark SQL) from events validated, deduplicated and "
                  "ordered in plain Python under the source contract in DATA.md; expected literals are authored by "
                  "hand there. The AUTO CDC adaptation in SOLUTIONS.md was not executed. outputHashes are SHA-256 of "
                  "the canonical JSON of each collected output." % OUTPUTS.get("spark_version", "?")),
    }
    if args.outputs:
        args.outputs.parent.mkdir(parents=True, exist_ok=True)
        args.outputs.write_text(json.dumps(OUTPUTS, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence[key] for key in ("lab", "python", "java", "spark", "tests", "failures",
                                                     "errors", "skipped", "exit")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
