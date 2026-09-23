"""lab-l06-record-resolution test runner (local-executed, plain Python).

    python run_tests.py --evidence <path>

Runs offline with the standard library only. Every expected value is a literal
in expected/*.json authored by hand (derivations in DATA.md); no test compares
the resolver with a value the resolver computed. The runner hashes every fixture
and expected file and every produced output into the evidence JSON.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
import time
import unittest

sys.dont_write_bytecode = True  # keep the package free of __pycache__
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from solutions.reference import LocalPipeline, guarded_upsert, resolve  # noqa: E402
from solutions.scenarios import business, fixtures, load, observation, pipeline_scenarios, quarantine_view, resolution_scenarios  # noqa: E402
from starters.resolver import flawed_current, naive_gate  # noqa: E402

LAB = "lab-l06-record-resolution"
ORIGINAL = ROOT.parents[0] / "reliable-data" / "solutions" / "reference.py"
ORIGINAL_FIXTURES = {"cinderline-baseline.json": "baseline.json", "cinderline-batches.json": "batches.json",
                     "cinderline-unkeyed.json": "unkeyed-conflict.json"}
CINDERLINE = load("expected/cinderline.json")
NORTHGATE = load("expected/northgate.json")
HASH = load("expected/reference-hash.json")
OUTPUTS = {}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class ReferenceCopyTests(unittest.TestCase):
    def test_reference_copy_hash_equals_recorded_original_hash(self):
        copy = ROOT / "solutions" / "reference.py"
        digest = sha256(copy.read_bytes()).hexdigest()
        self.assertEqual(digest, HASH["sha256"])
        self.assertEqual(copy.stat().st_size, HASH["bytes"])
        OUTPUTS["reference_copy"] = {"sha256": digest, "bytes": copy.stat().st_size, "original_present": ORIGINAL.is_file()}
        if ORIGINAL.is_file():  # Inside the repository: byte equality with the untouched original.
            self.assertEqual(copy.read_bytes(), ORIGINAL.read_bytes())
            self.assertEqual(sha256(ORIGINAL.read_bytes()).hexdigest(), HASH["sha256"])
            for mine, theirs in ORIGINAL_FIXTURES.items():
                self.assertEqual((ROOT / "fixtures" / mine).read_bytes(), (ORIGINAL.parents[1] / "fixtures" / theirs).read_bytes())

    def test_reference_is_pure_python_standard_library(self):
        source = (ROOT / "solutions" / "reference.py").read_text(encoding="utf-8")
        imports = [line.strip() for line in source.splitlines() if line.startswith(("import ", "from "))]
        self.assertEqual(imports, ["from copy import deepcopy", "from hashlib import sha256", "import csv", "import json"])
        self.assertNotIn("pyspark", source)
        OUTPUTS["reference_imports"] = imports


class CinderlineRegressionTests(unittest.TestCase):
    """The preserved regressions, each against the hand-authored literals."""

    @classmethod
    def setUpClass(cls):
        cls.base, cls.batches, cls.unkeyed = fixtures("cinderline")

    def test_baseline_five_rows_resolve_to_a_v2_and_c_v1(self):
        result = resolve(self.base)
        self.assertEqual(result["raw_count"], 5)
        self.assertEqual(business(result), CINDERLINE["baseline"])
        self.assertEqual(quarantine_view(result), CINDERLINE["baseline_quarantine"])
        self.assertEqual(result["conflicts"], [])
        OUTPUTS["cinderline_baseline"] = result

    def test_replay_does_not_change_accepted_totals_or_snapshot(self):
        self.assertEqual(business(resolve(self.base + self.base)), CINDERLINE["baseline"])
        pipe = LocalPipeline()
        pipe.ingest(self.base)
        snapshot = deepcopy(pipe.published)
        pipe.ingest(self.base)
        self.assertEqual(pipe.published, snapshot)
        self.assertEqual({k: observation(pipe)[k] for k in ("status", "raw_count", "local_effect_count")}, CINDERLINE["pipeline"]["replay"])

    def test_older_revision_cannot_replace_newer(self):
        result = resolve(self.base + self.batches["late"])
        self.assertEqual(business(result), CINDERLINE["baseline"])
        self.assertEqual(result["raw_count"], 6)

    def test_a_v3_14_1_produces_22_1_once(self):
        for copies in (1, 2):
            self.assertEqual(business(resolve(self.base + self.batches["correction"] * copies)), CINDERLINE["correction"])
        pipe = LocalPipeline()
        pipe.ingest(self.base)
        pipe.ingest(self.batches["correction"])
        self.assertEqual({k: observation(pipe)[k] for k in ("status", "raw_count", "local_effect_count")}, CINDERLINE["pipeline"]["correction"])
        pipe.ingest(self.batches["correction"])
        self.assertEqual({k: observation(pipe)[k] for k in ("status", "raw_count", "local_effect_count")}, CINDERLINE["pipeline"]["correction_replay"])
        self.assertEqual(pipe.published["totals"], CINDERLINE["correction"]["totals"])
        OUTPUTS["cinderline_correction"] = observation(pipe)

    def test_conflicts_persist_across_batches_and_under_row_order_reversal(self):
        pipe = LocalPipeline()
        pipe.ingest(self.base)
        pipe.ingest(self.batches["version_conflict"])
        self.assertEqual(business(pipe.resolved), CINDERLINE["blocked"])
        self.assertEqual(pipe.resolved["conflicts"], CINDERLINE["conflicts"]["version_conflict"])
        reversed_result = resolve(list(reversed(self.base + self.batches["version_conflict"])))
        self.assertEqual(business(reversed_result), CINDERLINE["blocked"])
        self.assertEqual(reversed_result["conflicts"], CINDERLINE["conflicts"]["version_conflict_reversed"])
        event = resolve(self.base + self.batches["event_conflict"])
        self.assertEqual(business(event), CINDERLINE["blocked"])
        self.assertEqual(event["conflicts"], CINDERLINE["conflicts"]["event_conflict"])
        OUTPUTS["cinderline_conflicts"] = {"version_conflict": pipe.resolved["conflicts"], "reversed": reversed_result["conflicts"], "event_conflict": event["conflicts"]}

    def test_unkeyed_conflict_blocks_publication_and_no_report_on_first_run(self):
        pipe = LocalPipeline()
        pipe.ingest(self.unkeyed)
        self.assertEqual(pipe.resolved["conflicts"], CINDERLINE["conflicts"]["unkeyed_first_run"])
        actual = {"accepted": pipe.resolved["accepted"], "unresolved": pipe.resolved["unresolved"],
                  "publication_allowed": pipe.resolved["publication_allowed"], "status": pipe.status,
                  "published": pipe.published, "local_effect_count": len(pipe.outbox)}
        self.assertEqual(actual, CINDERLINE["pipeline"]["unkeyed_first_run"])
        first = LocalPipeline()
        first.ingest(self.base + self.batches["version_conflict"])
        self.assertEqual({"status": first.status, "published": first.published, "local_effect_count": len(first.outbox)},
                         CINDERLINE["pipeline"]["first_run_conflict"])

    def test_stale_previous_snapshot_retained_on_later_conflict(self):
        pipe = LocalPipeline()
        pipe.ingest(self.base)
        previous, effects = deepcopy(pipe.published), deepcopy(pipe.outbox)
        pipe.ingest([self.unkeyed[0]])
        self.assertTrue(pipe.resolved["publication_allowed"])  # one malformed row alone is not a conflict
        pipe.ingest([self.unkeyed[1]] + self.batches["correction"])
        expected = CINDERLINE["pipeline"]["unkeyed_cross_batch"]
        self.assertEqual(pipe.resolved["accepted"], expected["accepted_candidate"])
        self.assertEqual(pipe.resolved["totals"], expected["candidate_totals"])
        self.assertEqual(pipe.published, previous)
        self.assertEqual(pipe.published["totals"], expected["previous_published_totals"])
        self.assertEqual(pipe.outbox, effects)
        self.assertEqual({"unresolved": pipe.resolved["unresolved"], "publication_allowed": pipe.resolved["publication_allowed"],
                          "status": pipe.status, "local_effect_count": len(pipe.outbox)},
                         {k: expected[k] for k in ("unresolved", "publication_allowed", "status", "local_effect_count")})
        self.assertEqual(pipe.resolved["conflicts"], CINDERLINE["conflicts"]["unkeyed_cross_batch"])
        later = LocalPipeline()
        later.ingest(self.base)
        later.ingest(self.batches["event_conflict"])
        self.assertEqual({k: observation(later)[k] for k in ("status", "raw_count", "local_effect_count")}, CINDERLINE["pipeline"]["event_conflict_after_baseline"])
        self.assertEqual(later.published["totals"], CINDERLINE["baseline"]["totals"])
        OUTPUTS["cinderline_cross_batch"] = observation(pipe)

    def test_invalid_latest_revision_does_not_resurrect_older_row(self):
        pipe = LocalPipeline()
        pipe.ingest(self.base)
        pipe.ingest(self.batches["invalid_latest"])
        self.assertEqual(business(pipe.resolved), CINDERLINE["blocked"])
        self.assertEqual(pipe.resolved["conflicts"], CINDERLINE["conflicts"]["invalid_latest"])
        self.assertEqual({k: observation(pipe)[k] for k in ("status", "raw_count", "local_effect_count")}, CINDERLINE["pipeline"]["invalid_latest_after_baseline"])
        self.assertEqual(pipe.published["totals"], CINDERLINE["baseline"]["totals"])
        self.assertEqual(business(resolve(self.base + self.batches["missing_order"])), CINDERLINE["blocked"])

    def test_failure_after_retained_raw_then_recovery(self):
        pipe = LocalPipeline()
        pipe.ingest(self.base)
        with self.assertRaisesRegex(RuntimeError, "retained_raw"):
            pipe.ingest(self.batches["correction"], fail_after="retained_raw")
        expected = CINDERLINE["pipeline"]["failure_after_retained_raw"]
        self.assertEqual({"raw_count": len(pipe.raw), "status": pipe.status, "local_effect_count": len(pipe.outbox)},
                         {k: expected[k] for k in ("raw_count", "status", "local_effect_count")})
        self.assertEqual(pipe.published["totals"], CINDERLINE["baseline"]["totals"])
        pipe.recover()
        self.assertEqual(pipe.status, expected["recovered_status"])
        self.assertEqual(len(pipe.outbox), expected["recovered_local_effect_count"])
        self.assertEqual(business(pipe.resolved), CINDERLINE["correction"])


class NegativeStarterTests(unittest.TestCase):
    """The deliberately broken starter must fail for the documented reason."""

    @classmethod
    def setUpClass(cls):
        cls.base, cls.batches, cls.unkeyed = fixtures("cinderline")

    def test_flawed_starter_resurrects_the_older_valid_revision(self):
        flawed = flawed_current(self.base + self.batches["invalid_latest"])
        resurrected = [row for row in flawed if row["inspection_id"] == "A"]
        self.assertEqual(resurrected, [{"inspection_id": "A", "version": 2, "inspected_units": 12, "defective_units": 1}],
                         "the starter dropped invalid v3 and reported v2 as current")
        self.assertEqual(resolve(self.base + self.batches["invalid_latest"])["unresolved"], ["A"])
        OUTPUTS["negative_flawed_invalid_latest"] = flawed

    def test_flawed_starter_lets_arrival_order_decide_a_conflict(self):
        rows = self.base + self.batches["version_conflict"]
        forward = [row for row in flawed_current(rows) if row["inspection_id"] == "A"][0]
        backward = [row for row in flawed_current(list(reversed(rows))) if row["inspection_id"] == "A"][0]
        self.assertEqual(forward["inspected_units"], 13, "last arrival won")
        self.assertEqual(backward["inspected_units"], 10, "reversing the input changed the answer")
        self.assertNotEqual(forward, backward)
        self.assertEqual(resolve(rows)["unresolved"], ["A"])
        OUTPUTS["negative_flawed_order"] = {"forward": forward, "reversed": backward}

    def test_naive_gate_publishes_an_unkeyed_conflict(self):
        result = resolve(self.unkeyed)
        self.assertTrue(naive_gate(result), "the gate saw an empty unresolved list and said publish")
        self.assertFalse(result["publication_allowed"])
        self.assertEqual(len(result["conflicts"]), 1)


class NorthgateTransferTests(unittest.TestCase):
    """A second plant and product line under the same contract, independently authored literals."""

    @classmethod
    def setUpClass(cls):
        cls.base, cls.batches, cls.unkeyed = fixtures("northgate")

    def test_baseline_zero_units_duplicate_and_excluded_key(self):
        result = resolve(self.base)
        self.assertEqual(result["raw_count"], 7)
        self.assertEqual(business(result), NORTHGATE["baseline"])
        self.assertEqual(quarantine_view(result), NORTHGATE["baseline_quarantine"])
        self.assertEqual(result["conflicts"], [])
        OUTPUTS["northgate_baseline"] = result

    def test_replay_and_late_older_revision_leave_state_unchanged(self):
        self.assertEqual(business(resolve(self.base + self.base)), NORTHGATE["baseline"])
        self.assertEqual(business(resolve(self.base + self.batches["late"])), NORTHGATE["baseline"])
        pipe = LocalPipeline()
        pipe.ingest(self.base)
        self.assertEqual({k: observation(pipe)[k] for k in ("status", "raw_count", "local_effect_count")}, NORTHGATE["pipeline"]["baseline"])
        snapshot = deepcopy(pipe.published)
        pipe.ingest(self.base)
        self.assertEqual(pipe.published, snapshot)
        self.assertEqual({k: observation(pipe)[k] for k in ("status", "raw_count", "local_effect_count")}, NORTHGATE["pipeline"]["replay"])
        late = LocalPipeline()
        late.ingest(self.base)
        late.ingest(self.batches["late"])
        self.assertEqual(late.published, snapshot)
        self.assertEqual({k: observation(late)[k] for k in ("status", "raw_count", "local_effect_count")}, NORTHGATE["pipeline"]["late"])

    def test_valid_correction_and_its_replay(self):
        for copies in (1, 2):
            self.assertEqual(business(resolve(self.base + self.batches["correction"] * copies)), NORTHGATE["correction"])
        pipe = LocalPipeline()
        pipe.ingest(self.base)
        pipe.ingest(self.batches["correction"])
        self.assertEqual({k: observation(pipe)[k] for k in ("status", "raw_count", "local_effect_count")}, NORTHGATE["pipeline"]["correction"])
        pipe.ingest(self.batches["correction"])
        self.assertEqual({k: observation(pipe)[k] for k in ("status", "raw_count", "local_effect_count")}, NORTHGATE["pipeline"]["correction_replay"])
        self.assertEqual(pipe.published["totals"], NORTHGATE["correction"]["totals"])
        OUTPUTS["northgate_correction"] = observation(pipe)

    def test_same_event_and_key_version_conflicts_with_raw_indices(self):
        event = resolve(self.base + self.batches["event_conflict"])
        self.assertEqual(business(event), NORTHGATE["blocked"])
        self.assertEqual(event["conflicts"], NORTHGATE["conflicts"]["event_conflict"])
        version = resolve(self.base + self.batches["version_conflict"])
        self.assertEqual(business(version), NORTHGATE["blocked"])
        self.assertEqual(version["conflicts"], NORTHGATE["conflicts"]["version_conflict"])
        reversed_result = resolve(list(reversed(self.base + self.batches["version_conflict"])))
        self.assertEqual(business(reversed_result), NORTHGATE["blocked"])
        self.assertEqual(reversed_result["conflicts"], NORTHGATE["conflicts"]["version_conflict_reversed"])
        pipe = LocalPipeline()
        pipe.ingest(self.base)
        pipe.ingest(self.batches["event_conflict"])
        self.assertEqual({k: observation(pipe)[k] for k in ("status", "raw_count", "local_effect_count")}, NORTHGATE["pipeline"]["event_conflict_after_baseline"])
        self.assertEqual(pipe.published["totals"], NORTHGATE["baseline"]["totals"])
        first = LocalPipeline()
        first.ingest(self.base + self.batches["version_conflict"])
        self.assertEqual({"status": first.status, "published": first.published, "local_effect_count": len(first.outbox)},
                         NORTHGATE["pipeline"]["first_run_conflict"])
        OUTPUTS["northgate_conflicts"] = {"event_conflict": event["conflicts"], "version_conflict": version["conflicts"], "reversed": reversed_result["conflicts"]}

    def test_invalid_latest_and_unordered_observation_block_the_key(self):
        for name in ("invalid_latest", "missing_order"):
            result = resolve(self.base + self.batches[name])
            self.assertEqual(business(result), NORTHGATE["blocked"])
            self.assertEqual(result["conflicts"], NORTHGATE["conflicts"][name])
            self.assertEqual(quarantine_view(result)[1:], NORTHGATE["later_quarantine"][name])
        pipe = LocalPipeline()
        pipe.ingest(self.base)
        pipe.ingest(self.batches["invalid_latest"])
        self.assertEqual({k: observation(pipe)[k] for k in ("status", "raw_count", "local_effect_count")}, NORTHGATE["pipeline"]["invalid_latest_after_baseline"])
        self.assertEqual(pipe.published["totals"], NORTHGATE["baseline"]["totals"])
        OUTPUTS["northgate_invalid_latest"] = observation(pipe)

    def test_unkeyed_conflict_first_run_and_cross_batch(self):
        pipe = LocalPipeline()
        pipe.ingest(self.unkeyed)
        self.assertEqual(pipe.resolved["conflicts"], NORTHGATE["conflicts"]["unkeyed_first_run"])
        actual = {"accepted": pipe.resolved["accepted"], "unresolved": pipe.resolved["unresolved"],
                  "publication_allowed": pipe.resolved["publication_allowed"], "status": pipe.status,
                  "published": pipe.published, "local_effect_count": len(pipe.outbox)}
        self.assertEqual(actual, NORTHGATE["pipeline"]["unkeyed_first_run"])
        pipe = LocalPipeline()
        pipe.ingest(self.base)
        previous, effects = deepcopy(pipe.published), deepcopy(pipe.outbox)
        pipe.ingest([self.unkeyed[0]])
        pipe.ingest([self.unkeyed[1]] + self.batches["correction"])
        expected = NORTHGATE["pipeline"]["unkeyed_cross_batch"]
        self.assertEqual(pipe.resolved["accepted"], expected["accepted_candidate"])
        self.assertEqual(pipe.resolved["totals"], expected["candidate_totals"])
        self.assertEqual(pipe.published, previous)
        self.assertEqual(pipe.published["totals"], expected["previous_published_totals"])
        self.assertEqual(pipe.outbox, effects)
        self.assertEqual(pipe.resolved["conflicts"], NORTHGATE["conflicts"]["unkeyed_cross_batch"])
        self.assertEqual({"unresolved": pipe.resolved["unresolved"], "publication_allowed": pipe.resolved["publication_allowed"],
                          "status": pipe.status, "local_effect_count": len(pipe.outbox)},
                         {k: expected[k] for k in ("unresolved", "publication_allowed", "status", "local_effect_count")})
        OUTPUTS["northgate_cross_batch"] = observation(pipe)

    def test_invalid_rows_carry_reasons_and_an_empty_report_is_not_blocked(self):
        result = resolve(self.batches["invalid"])
        self.assertEqual([item["reasons"] for item in result["quarantine"]], NORTHGATE["invalid_reasons"])
        self.assertEqual(business(result), NORTHGATE["invalid_only"])
        pipe = LocalPipeline()
        pipe.ingest(self.batches["invalid"])
        self.assertEqual({k: observation(pipe)[k] for k in ("status", "local_effect_count")}, NORTHGATE["pipeline"]["invalid_only_first_run"])
        self.assertEqual(pipe.published["accepted"], [])
        OUTPUTS["northgate_invalid_only"] = result

    def test_failure_boundaries_and_recovery(self):
        pipe = LocalPipeline()
        pipe.ingest(self.base)
        with self.assertRaisesRegex(RuntimeError, "retained_raw"):
            pipe.ingest(self.batches["correction"], fail_after="retained_raw")
        expected = NORTHGATE["pipeline"]["failure_after_retained_raw"]
        self.assertEqual({"raw_count": len(pipe.raw), "status": pipe.status, "local_effect_count": len(pipe.outbox)},
                         {k: expected[k] for k in ("raw_count", "status", "local_effect_count")})
        self.assertEqual(pipe.published["totals"], NORTHGATE["baseline"]["totals"])
        pipe.recover()
        self.assertEqual(pipe.status, expected["recovered_status"])
        self.assertEqual(len(pipe.outbox), expected["recovered_local_effect_count"])
        self.assertEqual(business(pipe.resolved), NORTHGATE["correction"])
        pipe = LocalPipeline()
        pipe.ingest(self.base)
        with self.assertRaisesRegex(RuntimeError, "published_snapshot"):
            pipe.ingest(self.batches["correction"], fail_after="published_snapshot")
        expected = NORTHGATE["pipeline"]["failure_after_published_snapshot"]
        self.assertEqual({"status": pipe.status, "local_effect_count": len(pipe.outbox)}, {k: expected[k] for k in ("status", "local_effect_count")})
        self.assertEqual(pipe.published["totals"], NORTHGATE["correction"]["totals"])
        pipe.recover()
        pipe.recover()
        self.assertEqual(len(pipe.outbox), expected["recovered_twice_local_effect_count"])
        OUTPUTS["northgate_recovery"] = observation(pipe)

    def test_guarded_upsert_older_replay_absence_and_disagreement(self):
        target = NORTHGATE["baseline"]["accepted"]
        correction = [row for row in NORTHGATE["correction"]["accepted"] if row["inspection_id"] == "VS-2"]
        updated = guarded_upsert(target, correction)
        self.assertEqual(updated, NORTHGATE["correction"]["accepted"])
        self.assertEqual(guarded_upsert(updated, correction), NORTHGATE["correction"]["accepted"])  # replay
        self.assertEqual(guarded_upsert(updated, target), NORTHGATE["correction"]["accepted"])  # older is a no-op
        self.assertEqual(guarded_upsert(updated, []), NORTHGATE["correction"]["accepted"])  # absence is not deletion
        before = deepcopy(updated)
        with self.assertRaisesRegex(ValueError, "equal version"):
            guarded_upsert(updated, [{**correction[0], "inspected_units": 27}])
        self.assertEqual(updated, before)
        OUTPUTS["northgate_upsert"] = updated

    def test_full_scenario_report_matches_literals(self):
        for plant, expected in (("cinderline", CINDERLINE), ("northgate", NORTHGATE)):
            scenarios = resolution_scenarios(plant)
            self.assertEqual(scenarios["baseline"]["business"], expected["baseline"])
            self.assertEqual(scenarios["replay"]["business"], expected["baseline"])
            self.assertEqual(scenarios["late"]["business"], expected["baseline"])
            self.assertEqual(scenarios["correction"]["business"], expected["correction"])
            self.assertEqual(scenarios["correction_replay"]["business"], expected["correction"])
            for name in ("event_conflict", "version_conflict", "version_conflict_reversed", "invalid_latest", "missing_order"):
                self.assertEqual(scenarios[name]["business"], expected["blocked"], name)
                self.assertEqual(scenarios[name]["conflicts"], expected["conflicts"][name], name)
            self.assertEqual(scenarios["unkeyed_first_run"]["conflicts"], expected["conflicts"]["unkeyed_first_run"])
            self.assertFalse(scenarios["unkeyed_first_run"]["business"]["publication_allowed"])
            OUTPUTS[plant + "_scenarios"] = {"resolution": scenarios, "pipeline": pipeline_scenarios(plant)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    suite = unittest.TestSuite()
    for case in (ReferenceCopyTests, CinderlineRegressionTests, NegativeStarterTests, NorthgateTransferTests):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    exit_code = 0 if result.wasSuccessful() else 1
    fixture_hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path.read_bytes()).hexdigest()
                      for directory in ("fixtures", "expected", "solutions", "starters")
                      for path in sorted((ROOT / directory).iterdir()) if path.is_file()}
    output_hashes = {name: sha256(canonical(value).encode("utf-8")).hexdigest() for name, value in sorted(OUTPUTS.items())}
    evidence = {
        "lab": LAB, "executionClass": "local-executed",
        "python": platform.python_version(), "interpreter": sys.executable, "java": "not used", "spark": "not used",
        "packages": {}, "platform": platform.system() + " " + platform.release(),
        "startedAt": started_at.isoformat(), "finishedAt": datetime.now(timezone.utc).isoformat(),
        "durationSeconds": round(time.monotonic() - started, 3),
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "exit": exit_code,
        "referenceSha256": HASH["sha256"], "originalPresent": ORIGINAL.is_file(),
        "fixtureHashes": fixture_hashes, "outputHashes": output_hashes,
        "commands": [f"{Path(sys.executable).name} run_tests.py --evidence <path>"],
        "notes": ("Plain Python: the reference resolver is a byte-for-byte copy of the original Cinderline resolver "
                  "(standard library only, no Spark). Expected values are hand-authored literals in expected/*.json; "
                  "DATA.md states every derivation. No network, no Databricks, no Delta, no notification sent."),
    }
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence[key] for key in ("lab", "python", "tests", "failures", "errors", "skipped", "exit")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
