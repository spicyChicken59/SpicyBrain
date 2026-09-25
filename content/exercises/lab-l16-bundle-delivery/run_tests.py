#!/usr/bin/env python3
"""Lab L16 test runner: local checks only, never a workspace.

Execution class P (platform-guide). Everything this runner executes is local:
YAML extraction and parsing, the lab's structure rules, variable resolution,
the package's unit tests and its entry point on a temporary directory. The
Databricks steps (authentication, `databricks bundle validate`, `plan`,
`deploy`, `run`, promotion) are listed in the classification table as NOT RUN
and are never attempted; a guard fails the run if anything tries to open a
network connection or start a process.

Usage, from the lab directory, with Python 3.12 and requirements.txt installed:
  python run_tests.py                          # judge solutions/
  python run_tests.py --evidence evidence.json # also write the evidence record
  python run_tests.py --starter                # judge your work in starters/
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import contextlib  # noqa: E402
import copy  # noqa: E402
import datetime as dt  # noqa: E402
import hashlib  # noqa: E402
import importlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import platform  # noqa: E402
import shutil  # noqa: E402
import socket  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import unittest  # noqa: E402
from decimal import Decimal  # noqa: E402
from pathlib import Path  # noqa: E402
from unittest import mock  # noqa: E402

import yaml  # noqa: E402

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
import bundlecheck  # noqa: E402

LAB_ID = "lab-l16-bundle-delivery"
TARGET = "solutions"
PACKAGE_MODULES = ("cinderline_quality", "test_scrap", "test_params", "test_main")
NOT_EXECUTED = [
    "Authenticate to a Databricks workspace: databricks auth login (OAuth user-to-machine) for a person, "
    "or OAuth machine-to-machine or workload identity federation for the pipeline's service principal",
    "databricks bundle validate --strict for dev, test and prod (authenticated: resolves the current user, "
    "lookups and the CLI's complete schema and target-mode rules)",
    "databricks bundle plan --target test and --target prod",
    "databricks bundle deploy --target dev, test or prod (wheel build, file upload, job creation, deployment state)",
    "databricks bundle run scrap_summary --target test (a job run on Databricks compute)",
    "Integration check of the test run's output in the cinderline_test exports volume",
    "Pull request, CI pipeline and approval on a Git hosting service",
    "Promotion of the reviewed commit to prod and the first scheduled prod run",
    "Wheel build with the pinned tools in requirements-ci.txt",
]


# ------------------------------------------------------------------ helpers
def load_json(relative: str):
    return json.loads((LAB / relative).read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def project_dir(target: str | None = None) -> Path:
    return LAB / (target or TARGET) / "project"


@contextlib.contextmanager
def isolated_package(project: Path):
    """Import the project's package and tests from its own src/ and tests/, then forget them."""
    saved_path = list(sys.path)
    saved = {name: module for name, module in sys.modules.items() if name.split(".")[0] in PACKAGE_MODULES}
    for name in saved:
        del sys.modules[name]
    sys.path[:0] = [str(project / "src"), str(project / "tests")]
    importlib.invalidate_caches()
    try:
        yield
    finally:
        sys.path[:] = saved_path
        for name in [n for n in sys.modules if n.split(".")[0] in PACKAGE_MODULES]:
            del sys.modules[name]
        sys.modules.update(saved)


def run_package_tests(project: Path) -> dict:
    """Run the project's own unittest suite in this process and summarise it by test name."""
    with isolated_package(project):
        loader = unittest.TestLoader()
        suite = loader.discover(str(project / "tests"), pattern="test_*.py", top_level_dir=str(project / "tests"))
        result = unittest.TestResult()
        suite.run(result)
    name = lambda test: test._testMethodName  # noqa: E731
    failures = sorted(name(t) for t, _ in result.failures)
    errors = sorted(name(t) for t, _ in result.errors)
    return {
        "tests": result.testsRun,
        "passed": result.testsRun - len(failures) - len(errors) - len(result.skipped),
        "failures": failures,
        "errors": errors,
        "skipped": len(result.skipped),
    }


def summarize_file(project: Path, fixture: str, threshold: str) -> dict:
    records = load_json(fixture)
    with isolated_package(project):
        scrap = importlib.import_module("cinderline_quality.scrap")
        rows, rejected = scrap.summarize_scrap(records, Decimal(threshold))
    return {"alert_threshold": threshold, "rows": rows, "rejected": rejected}


def run_entry_point(project: Path, arguments: list[str]) -> dict:
    """Run main() on a temporary directory standing in for the volume root; return the summary."""
    parsed = [a for a in arguments]
    catalog = parsed[parsed.index("--catalog") + 1]
    schema = parsed[parsed.index("--schema") + 1]
    with tempfile.TemporaryDirectory(prefix="lab-l16-volume-") as root:
        folder = Path(root, catalog, schema, "exports")
        folder.mkdir(parents=True)
        shutil.copyfile(LAB / "fixtures" / "inspections.json", folder / "inspections.json")
        with isolated_package(project):
            main = importlib.import_module("cinderline_quality.main")
            code = main.main([*arguments, "--volume-root", root])
        summary = json.loads((folder / "scrap_summary.json").read_text(encoding="utf-8"))
    return {"exit": code, "summary": summary}


def refused_arguments(project: Path, arguments: list[str]) -> str:
    with isolated_package(project):
        params = importlib.import_module("cinderline_quality.params")
        try:
            params.parse_params(arguments)
        except ValueError as error:
            return str(error)
    return ""


def apply_mutation(docs: dict, mutation: dict) -> dict:
    changed = copy.deepcopy(docs)
    node = changed[mutation["file"]]
    *parents, last = mutation["path"]
    for key in parents:
        node = node[key]
    if mutation["op"] == "set":
        node[last] = copy.deepcopy(mutation["value"])
    elif mutation["op"] == "delete":
        del node[last]
    elif mutation["op"] == "append":
        node[last].append(copy.deepcopy(mutation["value"]))
    else:
        raise ValueError(f"unknown mutation op {mutation['op']}")
    return changed


def pairs(findings) -> list[list[str]]:
    return [[f.rule, f.where] for f in findings]


class NetworkGuard:
    """Refuse and record any socket connection, name lookup or process start."""

    def __init__(self):
        self.attempts: list[str] = []
        self._patches = []

    def _refuse(self, what):
        def refused(*args, **kwargs):
            self.attempts.append(what)
            raise RuntimeError(f"{what} refused: this lab never contacts a workspace")
        return refused

    def __enter__(self):
        self._patches = [
            mock.patch.object(socket.socket, "connect", self._refuse("socket.connect")),
            mock.patch.object(socket.socket, "connect_ex", self._refuse("socket.connect_ex")),
            mock.patch.object(socket, "create_connection", self._refuse("socket.create_connection")),
            mock.patch.object(socket, "getaddrinfo", self._refuse("socket.getaddrinfo")),
            mock.patch.object(subprocess, "Popen", self._refuse("subprocess.Popen")),
            mock.patch.object(os, "system", self._refuse("os.system")),
        ]
        for patch in self._patches:
            patch.start()
        return self

    def __exit__(self, *exc):
        for patch in reversed(self._patches):
            patch.stop()
        return False


def local_steps(project: Path) -> dict:
    """Run every local step once and return what each produced."""
    blocks = bundlecheck.extract_blocks((project / "BUNDLE.md").read_text(encoding="utf-8"))
    docs, syntax = bundlecheck.parse_blocks(blocks)
    findings = bundlecheck.check(docs, project) if not syntax else []
    resolved = bundlecheck.resolve(docs) if not syntax and "targets" in docs.get("databricks.yml", {}) else {}
    package = run_package_tests(project)
    entry = None
    test_args = (resolved.get("test") or {}).get("task_parameters", {}).get("scrap_summary.summarize")
    if test_args and package["failures"] == [] and package["errors"] == []:
        entry = run_entry_point(project, test_args)
    return {
        "blocks": sorted(blocks),
        "syntax": [[f.rule, f.where, f.message] for f in syntax],
        "findings": pairs(findings),
        "resolved": resolved,
        "package": package,
        "entry_point": entry,
    }


def classification_rows(steps: dict) -> list[dict]:
    rows = [dict(row) for row in load_json("expected/classification.json")]
    package = steps["package"]
    needs = [f"{t} {n}" for t, r in steps["resolved"].items() for n in r["needs_workspace"]]
    local_evidence = {
        "local-syntax": f"{len(steps['blocks'])} blocks parsed ({', '.join(steps['blocks'])}); "
                        f"{len(steps['syntax'])} syntax findings",
        "local-structure": f"{len(steps['findings'])} findings on the configuration under test; "
                           f"{len(bundlecheck.RULES) - 1} structure rules",
        "local-resolve": f"{len(steps['resolved'])} targets resolved; left for the workspace: "
                         + (", ".join(needs) if needs else "nothing"),
        "unit-tests": f"{package['tests']} tests: {package['passed']} passed, {len(package['failures'])} failed, "
                      f"{len(package['errors'])} errors, {package['skipped']} skipped",
        "entry-point": (
            f"exit {steps['entry_point']['exit']}; {len(steps['entry_point']['summary']['rows'])} rows and "
            f"{len(steps['entry_point']['summary']['rejected'])} rejected records in a temporary scrap_summary.json"
            if steps["entry_point"] else "not reached: the package tests did not all pass"
        ),
    }
    for row in rows:
        if row["status"] == "EXECUTED":
            row["evidence"] = local_evidence[row["id"]]
            if row["id"] == "entry-point" and not steps["entry_point"]:
                row["status"] = "NOT REACHED"
        else:
            row["evidence"] = "not attempted: needs an authenticated Databricks workspace"
    return rows


def print_table(rows: list[dict]) -> None:
    print("\nLab L16 classification: what ran here and what did not")
    print(f"{'#':>2}  {'step':<16} {'class':<33} {'status':<11} evidence")
    for row in rows:
        print(f"{row['step']:>2}  {row['id']:<16} {row['class']:<33} {row['status']:<11} {row['evidence']}")
        print(f"{'':>2}  {'':<16} {row['check']}")


# -------------------------------------------------------------------- tests
class BundleDeliveryLab(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.project = project_dir()
        cls.bundle_md = cls.project / "BUNDLE.md"
        cls.blocks = bundlecheck.extract_blocks(cls.bundle_md.read_text(encoding="utf-8"))
        cls.docs, cls.syntax = bundlecheck.parse_blocks(cls.blocks)

    def test_01_blocks_are_extracted_and_parse_as_mappings(self):
        self.assertEqual(sorted(self.blocks), ["databricks.yml", "resources/scrap_job.yml"])
        self.assertEqual(self.syntax, [])
        self.assertEqual(
            set(self.docs["databricks.yml"]),
            {"bundle", "include", "artifacts", "variables", "targets"},
        )
        self.assertEqual(list(self.docs["resources/scrap_job.yml"]["resources"]["jobs"]), ["scrap_summary"])

    def test_02_reviewed_configuration_passes_every_local_rule(self):
        findings = bundlecheck.check(self.docs, self.project)
        self.assertEqual(pairs(findings), load_json("expected/bundle_findings.json")["reviewed"],
                         "\n".join(f"{f.rule} {f.where}: {f.message}" for f in findings))

    def test_03_resolved_targets_match_the_hand_derivation(self):
        self.assertEqual(bundlecheck.resolve(self.docs), load_json("expected/resolved_targets.json"))

    def test_04_package_unit_tests_pass(self):
        self.assertEqual(run_package_tests(self.project) | {"skipped": 0},
                         load_json("expected/package_unit_results.json") | {"skipped": 0})

    def test_05_fixture_summary_matches_expected(self):
        threshold = bundlecheck.resolve(self.docs)["prod"]["variables"]["alert_threshold"]
        self.assertEqual(summarize_file(self.project, "fixtures/inspections.json", threshold),
                         load_json("expected/scrap_summary.json"))

    def test_06_transfer_input_matches_expected(self):
        self.assertEqual(summarize_file(self.project, "fixtures/inspections_transfer.json", "0.0400"),
                         load_json("expected/scrap_transfer.json"))

    def test_07_entry_point_runs_with_the_test_targets_parameters(self):
        expected = load_json("expected/entry_point_summary.json")
        resolved = bundlecheck.resolve(self.docs)
        arguments = resolved[expected["target"]]["task_parameters"]["scrap_summary.summarize"]
        self.assertEqual(arguments, expected["arguments"])
        run = run_entry_point(self.project, arguments)
        self.assertEqual(run["exit"], 0)
        self.assertEqual(run["summary"], expected["summary"])
        # dev's schema still holds ${workspace.current_user.short_name}: only the workspace can resolve it.
        dev_arguments = resolved["dev"]["task_parameters"]["scrap_summary.summarize"]
        self.assertEqual(refused_arguments(self.project, dev_arguments), expected["dev_arguments_refused_because"])

    def test_08_each_mutation_fails_for_its_documented_reason(self):
        mutations = load_json("fixtures/bundle_mutations.json")
        expected = load_json("expected/bundle_findings.json")["mutations"]
        self.assertEqual([m["id"] for m in mutations], sorted(expected))
        for mutation in mutations:
            with self.subTest(mutation=mutation["id"], summary=mutation["summary"]):
                findings = bundlecheck.check(apply_mutation(self.docs, mutation), self.project)
                self.assertEqual(pairs(findings), expected[mutation["id"]],
                                 "\n".join(f"{f.rule} {f.where}: {f.message}" for f in findings))

    def test_09_syntax_errors_name_the_file_and_line(self):
        _, findings = bundlecheck.load_markdown(LAB / "fixtures" / "broken_blocks.md")
        self.assertEqual([[f.rule, f.where, f.message] for f in findings], load_json("expected/syntax_findings.json"))

    def test_10_a_block_without_a_file_marker_is_refused(self):
        text = "Intro\n\n```yaml\nbundle:\n  name: cinderline_scrap\n```\n"
        with self.assertRaisesRegex(bundlecheck.BlockError, r"line 3 does not start with '# file: <path>'"):
            bundlecheck.extract_blocks(text)
        with self.assertRaisesRegex(bundlecheck.BlockError, "no yaml block names databricks.yml"):
            bundlecheck.extract_blocks("```yaml\n# file: resources/x.yml\nresources: {}\n```\n")

    def test_11_materialized_project_round_trips(self):
        with tempfile.TemporaryDirectory(prefix="lab-l16-project-") as tmp:
            destination = Path(tmp, "cinderline-scrap")
            written = bundlecheck.materialize(self.bundle_md, destination)
            self.assertEqual(written, ["databricks.yml", "resources/scrap_job.yml"])
            files = sorted(p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file())
            self.assertIn("src/cinderline_quality/scrap.py", files)
            self.assertIn("pyproject.toml", files)
            self.assertNotIn("BUNDLE.md", files)
            docs, syntax = bundlecheck.load_files(destination)
            self.assertEqual(syntax, [])
            self.assertEqual(docs, self.docs)
            self.assertEqual(bundlecheck.check(docs, destination), [])
            self.assertEqual(run_package_tests(destination)["passed"], 14)

    def test_12_starter_bundle_shows_the_documented_gaps(self):
        starter = project_dir("starters")
        docs, syntax = bundlecheck.load_markdown(starter / "BUNDLE.md")
        self.assertEqual(syntax, [])
        self.assertEqual(pairs(bundlecheck.check(docs, starter)), load_json("expected/starter_findings.json"))

    def test_13_starter_package_fails_for_the_documented_reasons(self):
        result = run_package_tests(project_dir("starters"))
        result.pop("skipped")
        self.assertEqual(result, load_json("expected/starter_unit_results.json"))

    def test_14_no_network_and_no_process_during_local_steps(self):
        with NetworkGuard() as guard:
            steps = local_steps(self.project)
        self.assertEqual(guard.attempts, [])
        self.assertIsNotNone(steps["entry_point"])

    def test_15_requirements_are_exact_pins(self):
        lines = [line.split("#", 1)[0].strip() for line in (LAB / "requirements.txt").read_text().splitlines()]
        pins = [line for line in lines if line]
        self.assertEqual(pins, ["pyyaml==6.0.3"])
        self.assertEqual(yaml.__version__, "6.0.3")
        ci = [line.split("#", 1)[0].strip() for line in (self.project / "requirements-ci.txt").read_text().splitlines()]
        for line in filter(None, ci):
            self.assertRegex(line, bundlecheck.PINNED)

    def test_16_classification_table_separates_local_from_not_run(self):
        with NetworkGuard() as guard:
            rows = classification_rows(local_steps(self.project))
        self.assertEqual(guard.attempts, [])
        static = [{k: r[k] for k in ("step", "id", "class", "status", "check")} for r in rows]
        self.assertEqual(static, load_json("expected/classification.json"))
        executed = {r["id"] for r in rows if r["status"] == "EXECUTED"}
        self.assertEqual(executed, {"local-syntax", "local-structure", "local-resolve", "unit-tests", "entry-point"})
        platform_classes = {"authentication", "authenticated validation", "deployment preview", "deployment",
                            "job run (execution)", "integration test", "promotion"}
        for row in rows:
            if row["class"] in platform_classes:
                self.assertEqual(row["status"], "NOT RUN", row["id"])


STARTER_EXCLUDED = {"test_12_starter_bundle_shows_the_documented_gaps",
                    "test_13_starter_package_fails_for_the_documented_reasons"}


# ------------------------------------------------------------------- runner
def evidence_record(result, started, finished, exit_code, command) -> dict:
    project = project_dir()
    steps = local_steps(project)
    rows = classification_rows(steps)
    fixture_hashes = {p.relative_to(LAB).as_posix(): sha256_file(p) for p in sorted((LAB / "fixtures").iterdir())}
    expected_hashes = {p.relative_to(LAB).as_posix(): sha256_file(p) for p in sorted((LAB / "expected").iterdir())}
    solution_files = [LAB / "bundlecheck.py", LAB / "run_tests.py"]
    solution_files += sorted(p for p in project.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    solution_hashes = {p.relative_to(LAB).as_posix(): sha256_file(p) for p in solution_files}
    docs, _ = bundlecheck.load_markdown(project / "BUNDLE.md")
    mutations = load_json("fixtures/bundle_mutations.json")
    starter = project_dir("starters")
    starter_docs, _ = bundlecheck.load_markdown(starter / "BUNDLE.md")
    threshold = steps["resolved"]["prod"]["variables"]["alert_threshold"]
    outputs = {
        "parsed_configuration": docs,
        "reviewed_findings": steps["findings"],
        "resolved_targets": steps["resolved"],
        "mutation_findings": {m["id"]: pairs(bundlecheck.check(apply_mutation(docs, m), project)) for m in mutations},
        "syntax_findings": [[f.rule, f.where, f.message] for f in bundlecheck.load_markdown(LAB / "fixtures" / "broken_blocks.md")[1]],
        "package_unit_results": steps["package"],
        "scrap_summary": summarize_file(project, "fixtures/inspections.json", threshold),
        "scrap_transfer": summarize_file(project, "fixtures/inspections_transfer.json", "0.0400"),
        "entry_point_summary": steps["entry_point"],
        "starter_findings": pairs(bundlecheck.check(starter_docs, starter)),
        "starter_unit_results": run_package_tests(starter),
        "classification": rows,
    }
    return {
        "lab": LAB_ID,
        "executionClass": "platform-guide",
        "runtime": "ml",
        "executed": (
            "local Python with PyYAML on one machine: YAML block extraction and parsing, the lab's structure "
            "rules, variable resolution, the package's unittest suite and its entry point on a temporary "
            "directory; no Databricks workspace, CLI, SDK, network connection or subprocess"
        ),
        "target": TARGET,
        "python": platform.python_version(),
        "interpreter": sys.executable,
        "packages": {"pyyaml": yaml.__version__},
        "platform": platform.platform(),
        "startedAt": started.isoformat(),
        "finishedAt": finished.isoformat(),
        "durationSeconds": round((finished - started).total_seconds(), 3),
        "tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "exit": exit_code,
        "fixtureHashes": fixture_hashes,
        "expectedHashes": expected_hashes,
        "solutionHashes": solution_hashes,
        "outputHashes": {name: digest(value) for name, value in sorted(outputs.items())},
        "packageUnitTests": steps["package"],
        "classification": rows,
        "networkGuard": "socket connect, name lookup, subprocess and os.system were patched to refuse and record; "
                        "tests 14 and 16 assert zero attempts",
        "commands": [command],
        "notExecuted": NOT_EXECUTED,
        "notes": (
            "Class P (platform-guide). The Declarative Automation Bundle configuration (formerly Databricks Asset "
            "Bundles) travels as fenced YAML blocks in BUNDLE.md because the download may not contain .yml files. "
            "Local rules D1-D11 restate behaviour read in the Databricks CLI v1.17.0 source; H1-H10 are this lab's "
            "house review policy. Expected results were written by hand before the code ran (DATA.md). Nothing was "
            "validated, deployed or run on Databricks."
        ),
    }


def main(argv: list[str]) -> int:
    global TARGET
    parser = argparse.ArgumentParser(description="Lab L16 local checks")
    parser.add_argument("--evidence", type=Path, help="write the evidence JSON here")
    parser.add_argument("--starter", action="store_true", help="judge starters/ instead of solutions/")
    args = parser.parse_args(argv)
    if args.starter:
        TARGET = "starters"
    started = dt.datetime.now(dt.timezone.utc)
    loader = unittest.TestLoader()
    names = [n for n in loader.getTestCaseNames(BundleDeliveryLab)
             if not (args.starter and n in STARTER_EXCLUDED)]
    suite = unittest.TestSuite(BundleDeliveryLab(n) for n in names)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    exit_code = 0 if result.wasSuccessful() and not result.skipped else 1
    try:
        with NetworkGuard() as guard:
            rows = classification_rows(local_steps(project_dir()))
        if guard.attempts:
            exit_code = 1
        print_table(rows)
    except Exception as error:  # the table is a report; a broken starter may not produce one
        print(f"\nclassification table not produced: {error}")
    finished = dt.datetime.now(dt.timezone.utc)
    if args.evidence:
        if args.starter:
            print("evidence is written only for solutions/; rerun without --starter")
        else:
            # The recorded command names the interpreter generically and the evidence path as a
            # placeholder, so the evidence carries no machine-specific path.
            command = "python run_tests.py " + " ".join(
                "<path>" if arg == str(args.evidence) else arg for arg in argv
            )
            record = evidence_record(result, started, finished, exit_code, command)
            args.evidence.parent.mkdir(parents=True, exist_ok=True)
            args.evidence.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"\nevidence written: {args.evidence}")
    for cache in LAB.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    print(f"\n{result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors, "
          f"{len(result.skipped)} skipped; exit {exit_code}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
