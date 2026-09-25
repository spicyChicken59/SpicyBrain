"""Lab L21 test runner: deterministic evaluation, traces and a failure taxonomy.

    python run_tests.py --evidence <path>     # test the reference solution, write evidence
    python run_tests.py                       # test the reference solution
    python run_tests.py --starter             # test your copy in starters/ (gaps fail)

Every expected value comes from expected/*.json, which were typed by hand
from the case design in DATA.md; nothing in expected/ is produced by the code
under test. The runner uses the Python standard library only, calls no model,
judge or endpoint, and writes its temporary outputs to a directory that it
deletes before exiting. The evidence JSON records versions, counts, SHA-256
hashes of every fixture and produced output, and the command that ran.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import unittest  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from hashlib import sha256  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
TRANSFER = FIXTURES / "transfer"
EXPECTED = ROOT / "expected"
OUTPUTS: dict[str, str] = {}
H = None  # the module under test, set in main()


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"lab21_{path.parent.name}_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve annotations through sys.modules
    spec.loader.exec_module(module)
    return module


def expected(name: str) -> dict:
    return json.loads((EXPECTED / name).read_text(encoding="utf-8"))


def copy_fixtures(source: Path, target: Path) -> Path:
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("transfer"))
    return target


def edit_json(path: Path, change) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    change(value)
    path.write_text(json.dumps(value, indent=1), encoding="utf-8")


def fixture_case(fixture_set: dict, case_id: str) -> dict:
    return next(c for c in fixture_set["cases"] if c["case_id"] == case_id)


def record_for(report: dict, case_id: str) -> dict:
    return next(r for r in report["records"] if r["case_id"] == case_id)


class Base(unittest.TestCase):
    """Fixtures load once; reports are built on first use, so a starter gap
    fails the tests that need it and leaves the others running."""
    _reports: dict[str, dict] = {}

    @classmethod
    def setUpClass(cls):
        cls.main = H.load_fixture_set(FIXTURES)
        cls.transfer = H.load_fixture_set(TRANSFER)

    @property
    def report(self) -> dict:
        if "main" not in Base._reports:
            Base._reports["main"] = H.build_report(self.main, "cinderline-pilot")
        return Base._reports["main"]

    @property
    def transfer_report(self) -> dict:
        if "transfer" not in Base._reports:
            Base._reports["transfer"] = H.build_report(self.transfer, "harbourline-transfer")
        return Base._reports["transfer"]

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lab21-")
        self.addCleanup(self.tmp.cleanup)

    def altered(self, change_traces=None, change_answers=None) -> dict:
        target = copy_fixtures(FIXTURES, Path(self.tmp.name) / "fixtures")
        if change_traces:
            edit_json(target / "traces.json", change_traces)
        if change_answers:
            edit_json(target / "answers.json", change_answers)
        return H.load_fixture_set(target)


class FixtureContract(Base):
    def test_every_fixture_file_is_labelled_authored(self):
        for path in sorted(FIXTURES.rglob("*.json")):
            with self.subTest(path=path.name):
                self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["fixture_kind"], "authored")

    def test_unlabelled_fixture_is_refused(self):
        target = copy_fixtures(FIXTURES, Path(self.tmp.name) / "fixtures")
        edit_json(target / "answers.json", lambda v: v.pop("fixture_kind"))
        with self.assertRaisesRegex(H.FixtureError, "fixture_kind must be 'authored'"):
            H.load_fixture_set(target)

    def test_a_judge_score_in_a_fixture_is_refused(self):
        target = copy_fixtures(FIXTURES, Path(self.tmp.name) / "fixtures")
        edit_json(target / "answers.json", lambda v: v["answers"][0].update({"judge_score": 0.9}))
        with self.assertRaisesRegex(H.FixtureError, "fixtures carry no judge scores .*judge_score"):
            H.load_fixture_set(target)

    def test_orphan_span_is_refused(self):
        target = copy_fixtures(FIXTURES, Path(self.tmp.name) / "fixtures")

        def orphan(v):
            v["traces"][0]["spans"][2]["parent_id"] = "c01-missing"
        edit_json(target / "traces.json", orphan)
        with self.assertRaisesRegex(H.FixtureError, "orphan span c01-generate names missing parent c01-missing"):
            H.load_fixture_set(target)

    def test_unknown_source_in_a_case_is_refused(self):
        target = copy_fixtures(FIXTURES, Path(self.tmp.name) / "fixtures")
        edit_json(target / "cases.json", lambda v: v["cases"][0]["expected"]["must_cite"].append("M7-R9"))
        with self.assertRaisesRegex(H.FixtureError, "c01-torque: unknown source M7-R9"):
            H.load_fixture_set(target)


class Scorers(Base):
    """Each scorer is called on its own, so one finished task turns its own tests green."""

    def score(self, name: str, case_id: str) -> dict:
        case = fixture_case(self.main, case_id)
        answer, trace = self.main["answers"][case_id], self.main["traces"][case_id]
        return H.SCORERS[name](case, answer, trace, self.main).as_dict()

    def check_literal(self, name: str):
        want = expected("scores.json")["scores"]
        self.assertEqual(sorted(want), sorted(c["case_id"] for c in self.main["cases"]))
        for case_id, scorers in want.items():
            with self.subTest(case=case_id, scorer=name):
                self.assertEqual(self.score(name, case_id), scorers[name])

    def test_citation_presence_matches_the_authored_literal(self):
        self.check_literal("citation_presence")

    def test_citation_correctness_matches_the_authored_literal(self):
        self.check_literal("citation_correctness")

    def test_abstention_matches_the_authored_literal(self):
        self.check_literal("abstention")

    def test_forbidden_tools_matches_the_authored_literal(self):
        self.check_literal("forbidden_tools")

    def test_required_fields_matches_the_authored_literal(self):
        self.check_literal("required_fields")

    def test_tool_correctness_matches_the_authored_literal(self):
        self.check_literal("tool_correctness")

    def test_lenient_citation_matches_the_authored_literal(self):
        self.check_literal("lenient_citation")

    def test_presence_is_not_correctness(self):
        for case_id in ("c02-lube", "c03-guard"):
            with self.subTest(case=case_id):
                self.assertTrue(self.score("citation_presence", case_id)["passed"])
                self.assertFalse(self.score("citation_correctness", case_id)["passed"])

    def test_attempted_forbidden_tool_fails_even_when_denied(self):
        score = self.score("forbidden_tools", "c08-injection")
        self.assertEqual(score["reasons"], ["forbidden_tool_attempted:create_work_order:denied"])
        self.assertFalse(score["passed"])

    def test_tool_arguments_are_compared_exactly(self):
        self.assertTrue(self.score("tool_correctness", "c09-stock")["passed"])
        self.assertEqual(self.score("tool_correctness", "c10-stock-wrong")["reasons"],
                         ["tool_arguments_mismatch:lookup_part_stock:part_id"])

    def test_a_missing_field_is_named(self):
        self.assertEqual(self.score("required_fields", "c11-nofields")["reasons"], ["missing_field:citations"])

    def test_report_scores_match_the_authored_literal(self):
        self.assertEqual(self.report["scores"], expected("scores.json")["scores"])


class Taxonomy(Base):
    def test_taxonomy_matches_the_authored_literal(self):
        want = expected("taxonomy.json")["cases"]
        self.assertEqual([r["case_id"] for r in self.report["records"]], list(want))
        for case_id, literal in want.items():
            with self.subTest(case=case_id):
                got = {k: v for k, v in record_for(self.report, case_id).items()
                       if k not in ("case_id", "case_class")}
                self.assertEqual(got, literal)

    def test_report_counts_match_the_authored_literal(self):
        want = expected("report_counts.json")
        for key in ("classes", "by_case_class", "contained", "uncontained_failures", "blocking", "scorers"):
            with self.subTest(key=key):
                self.assertEqual(self.report[key], want[key])
        self.assertEqual(sum(self.report["classes"].values()), self.report["cases"])

    def test_policy_block_is_not_a_pass_even_when_the_final_answer_scores_clean(self):
        scores = self.report["scores"]["c07-bypass"]
        applicable = {n: s for n, s in scores.items() if s["applicable"] and n in H.GATE_SCORERS}
        self.assertTrue(applicable and all(s["passed"] for s in applicable.values()))
        record = record_for(self.report, "c07-bypass")
        self.assertEqual((record["class"], record["earliest_divergence"], record["contained_by"]),
                         ("policy_block", "c07-generate", "c07-guardrail"))

    def test_adversarial_source_instruction_is_flagged_when_the_tool_is_denied(self):
        trace = self.main["traces"]["c08-injection"]
        self.assertIn("NOTE-114:c01", H.retrieved_refs(trace))
        record = record_for(self.report, "c08-injection")
        self.assertEqual((record["class"], record["contained_by"], record["blocking"]),
                         ("denied_tool", "c08-tool-1", True))

    def test_adversarial_source_quoted_as_content_passes(self):
        self.assertIn("NOTE-114:c01", H.retrieved_refs(self.main["traces"]["c12-note"]))
        self.assertEqual(record_for(self.report, "c12-note")["class"], "pass")

    def test_earliest_divergence_moves_when_retrieval_is_repaired(self):
        def add_current_revision(v):
            trace = next(t for t in v["traces"] if t["case_id"] == "c02-lube")
            trace["spans"][1]["outputs"].append(
                {"id": "M7-R3:c33", "page_content": "Slide lubrication: every 24 operating hours with EP2 grease.",
                 "metadata": {"doc_uri": "M7-R3", "chunk_id": "c33"}})
        fixture_set = self.altered(change_traces=add_current_revision)
        case = fixture_case(fixture_set, "c02-lube")
        scores = H.score_case(case, fixture_set)
        self.assertEqual(scores["citation_correctness"].reasons,
                         ("cited_source_not_allowed:M7-R2", "required_source_not_cited:M7-R3"))
        record = H.classify(case, scores, fixture_set)
        self.assertEqual((record["class"], record["earliest_divergence"], record["retrieval_findings"]),
                         ("reasoning_failure", "c02-generate", []))
        OUTPUTS["altered_c02_record"] = json.dumps(record, sort_keys=True)

    def test_denied_versus_executed_forbidden_tool(self):
        def let_it_run(v):
            trace = next(t for t in v["traces"] if t["case_id"] == "c08-injection")
            tool = next(s for s in trace["spans"] if s["span_id"] == "c08-tool-1")
            tool.update({"status": "OK", "outputs": {"work_order": "WO-0001"}})
            tool["attributes"] = {"authz.decision": "allowed"}
        fixture_set = self.altered(change_traces=let_it_run)
        case = fixture_case(fixture_set, "c08-injection")
        scores = H.score_case(case, fixture_set)
        self.assertEqual(scores["forbidden_tools"].reasons, ("forbidden_tool_attempted:create_work_order:executed",))
        record = H.classify(case, scores, fixture_set)
        self.assertEqual((record["class"], record["contained_by"], record["blocking"]),
                         ("reasoning_failure", None, True))
        OUTPUTS["altered_c08_record"] = json.dumps(record, sort_keys=True)


class Validation(Base):
    def test_validation_matches_the_authored_literal(self):
        want = expected("validation.json")
        for name in ("citation_correctness", "lenient_citation"):
            with self.subTest(scorer=name):
                self.assertEqual(self.report["validation"][name], want[name])

    def test_strict_citation_scorer_is_accepted(self):
        result = H.validate_scorer("citation_correctness", self.main)
        self.assertEqual((result["agreed"], result["compared"], result["status"]), (7, 7, "accepted"))

    def test_lenient_scorer_is_rejected_for_the_asserted_reason(self):
        result = H.validate_scorer("lenient_citation", self.main)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["false_passes"], ["c02-lube", "c03-guard", "c04-precharge"])
        self.assertEqual(result["false_fails"], [])
        for case_id in result["false_passes"]:
            with self.subTest(case=case_id):
                case = fixture_case(self.main, case_id)
                answer = self.main["answers"][case_id]
                scores = H.score_case(case, self.main)
                # The marker the lenient scorer looks for is present...
                self.assertRegex(answer["text"], r"\[[^\[\]]+\]")
                self.assertTrue(scores["lenient_citation"].passed)
                # ...but every citation defect sits in what the marker does not show:
                # which chunk was retrieved, which source may be cited, which source was required.
                self.assertTrue(scores["citation_correctness"].reasons)
                for reason in scores["citation_correctness"].reasons:
                    self.assertRegex(reason, r"^(cited_chunk_not_retrieved|cited_source_not_allowed|"
                                             r"required_source_not_cited):")


class Transfer(Base):
    def test_transfer_taxonomy_matches_the_authored_literal(self):
        want = expected("transfer_taxonomy.json")
        for case_id, literal in want["cases"].items():
            with self.subTest(case=case_id):
                got = {k: v for k, v in record_for(self.transfer_report, case_id).items()
                       if k not in ("case_id", "case_class")}
                self.assertEqual(got, literal)
        self.assertEqual(self.transfer_report["classes"], want["classes"])
        self.assertEqual(self.transfer_report["blocking"], want["blocking"])

    def test_executed_forbidden_tool_is_uncontained(self):
        want = expected("transfer_taxonomy.json")["forbidden_tool_reasons"]["t04-release"]
        self.assertEqual(self.transfer_report["scores"]["t04-release"]["forbidden_tools"]["reasons"], want)
        self.assertIsNone(record_for(self.transfer_report, "t04-release")["contained_by"])
        self.assertIn("t04-release", self.transfer_report["uncontained_failures"])

    def test_policy_block_traced_back_to_retrieval(self):
        record = record_for(self.transfer_report, "t05-client")
        self.assertEqual((record["class"], record["earliest_divergence"], record["contained_by"]),
                         ("policy_block", "t05-retrieve", "t05-guardrail"))
        self.assertEqual(record["retrieval_findings"], ["unauthorized_source_retrieved:CLIENT-88"])


class Report(Base):
    def test_cli_writes_identical_reports_on_two_runs(self):
        produced = []
        for run in ("first", "second"):
            out = Path(self.tmp.name) / run
            completed = subprocess.run(
                [sys.executable, "-B", str(Path(H.__file__).resolve().relative_to(ROOT)),
                 "--fixtures", "fixtures", "--out", str(out), "--label", "cinderline-pilot"],
                cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("12 cases: pass 5, retrieval_failure 1, reasoning_failure 4", completed.stdout)
            produced.append(((out / "report.json").read_bytes(), (out / "report.md").read_bytes()))
        self.assertEqual(produced[0], produced[1])
        self.assertEqual(json.loads(produced[0][0]), json.loads(H.report_json(self.report)))
        OUTPUTS["cli_report_json"] = produced[0][0].decode("utf-8")
        OUTPUTS["cli_report_md"] = produced[0][1].decode("utf-8")

    def test_report_states_its_limits_and_carries_no_blended_score(self):
        text = " ".join(self.report["limits"])
        self.assertIn("authored fixtures, not model outputs", text)
        self.assertIn("no judge score was used or produced", text)
        numeric = [k for k, v in self.report.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
        self.assertEqual(numeric, ["cases"])

    def test_starter_leaves_each_gap_open(self):
        starter = load_module(ROOT / "starters" / "evalharness.py")
        fixture_set = starter.load_fixture_set(FIXTURES)
        case = fixture_case(fixture_set, "c02-lube")
        answer, trace = fixture_set["answers"]["c02-lube"], fixture_set["traces"]["c02-lube"]
        self.assertTrue(starter.citation_presence(case, answer, trace, fixture_set).passed)
        gaps = {"citation_correctness": "Task 2", "forbidden_tools": "Task 3", "tool_correctness": "Task 4"}
        for name, task in gaps.items():
            with self.subTest(gap=name):
                with self.assertRaisesRegex(NotImplementedError, task):
                    getattr(starter, name)(case, answer, trace, fixture_set)
        with self.assertRaisesRegex(NotImplementedError, "Task 5"):
            starter.classify(case, {}, fixture_set)
        with self.assertRaisesRegex(NotImplementedError, "Task 6"):
            starter.validate_scorer("lenient_citation", fixture_set)


def hashes(paths) -> dict[str, str]:
    return {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def main() -> int:
    global H
    parser = argparse.ArgumentParser(description="Lab L21 tests")
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--starter", action="store_true", help="test starters/evalharness.py instead")
    args = parser.parse_args()
    if args.starter and args.evidence:
        parser.error("evidence records the reference solution only; drop --evidence when using --starter")
    target = ROOT / ("starters" if args.starter else "solutions") / "evalharness.py"
    H = load_module(target)
    started = datetime.now(timezone.utc)
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finished = datetime.now(timezone.utc)
    code = 0 if result.wasSuccessful() and not result.skipped else 1
    if args.evidence:
        main_set, transfer_set = H.load_fixture_set(FIXTURES), H.load_fixture_set(TRANSFER)
        OUTPUTS["report_main_json"] = H.report_json(H.build_report(main_set, "cinderline-pilot"))
        OUTPUTS["report_main_md"] = H.render_markdown(H.build_report(main_set, "cinderline-pilot"))
        OUTPUTS["report_transfer_json"] = H.report_json(H.build_report(transfer_set, "harbourline-transfer"))
        evidence = {
            "lab": "lab-l21-evaluation-traces",
            "executionClass": "local-executed",
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "interpreter": sys.executable,
            "inVirtualEnvironment": sys.prefix != sys.base_prefix,
            "java": "not used",
            "spark": "not used",
            "packages": {},
            "standardLibrary": ["argparse", "dataclasses", "datetime", "hashlib", "importlib",
                                "json", "pathlib", "platform", "re", "shutil", "subprocess",
                                "tempfile", "unittest"],
            "platform": platform.system() + " " + platform.release(),
            "startedAt": started.isoformat(),
            "finishedAt": finished.isoformat(),
            "durationSeconds": round((finished - started).total_seconds(), 3),
            "tests": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "exit": code,
            "moduleUnderTest": "solutions/evalharness.py",
            "fixtureHashes": hashes([p for d in ("fixtures", "expected", "solutions", "starters")
                                     for p in (ROOT / d).rglob("*") if p.is_file()]
                                    + [ROOT / "run_tests.py"]),
            "outputHashes": {name: sha256(value.encode("utf-8")).hexdigest()
                             for name, value in sorted(OUTPUTS.items())},
            "commands": [f"{sys.executable} run_tests.py --evidence <path>"],
            "subprocessCommands": [
                "python3.12 -B solutions/evalharness.py --fixtures fixtures --out <temporary directory> --label cinderline-pilot (run twice)"],
            "notes": ("Plain CPython standard library, no packages, no network, no model, judge or endpoint. "
                      "Answers and traces are authored fixtures labelled as such; the loader refuses unlabelled "
                      "fixtures and any fixture carrying a judge score. Expected values are hand-typed literals "
                      "in expected/*.json derived in DATA.md. Temporary outputs are written under the system "
                      "temporary directory and deleted before exit."),
        }
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
