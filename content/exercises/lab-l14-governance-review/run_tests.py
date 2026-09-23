#!/usr/bin/env python3
"""Tabletop checks for lab-l14-governance-review (standard library only).

    python3.12 run_tests.py --evidence <path>   # check the reference answers in solutions/ and write evidence JSON
    python3.12 run_tests.py --answers starters  # check your own answers after editing the files in starters/

Execution class: tabletop. solutions/evaluator.py is a small local model of
documented Unity Catalog privilege rules; it evaluates the authored tables in
fixtures/. A locally evaluated policy table is not Unity Catalog enforcement:
nothing here connects to Databricks, runs a GRANT or evaluates a real row filter.
Every expected value in expected/ was written by hand from the rules in DATA.md.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # keep the package free of __pycache__

import argparse
import copy
import json
import platform
import re
import time
import unittest
from datetime import date, datetime, timezone
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "solutions"))
import evaluator  # noqa: E402  (the local evaluator under test)

LAB = "lab-l14-governance-review"
ANSWERS = ROOT / "solutions"
OUTPUTS: dict[str, object] = {}
NOT_EXECUTED = [
    "Unity Catalog GRANT, REVOKE and SHOW GRANTS against a real metastore",
    "Row filter and column mask SQL functions evaluated by Databricks at query time",
    "Attribute-based access control (ABAC) policies and governed tags",
    "Authentication of any principal (OAuth U2M, OAuth M2M, workload identity federation or personal access tokens)",
    "SCIM provisioning and identity-provider group synchronisation",
    "Secret scope ACLs and the secrets utility",
    "Queries on the audit log system table",
]


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def model() -> evaluator.Model:
    return evaluator.Model.load(ROOT)


def plan_tests():
    return read(ROOT / "fixtures" / "plan_matrix.json")["tests"]


def failing_rows(observed: dict, expected: dict) -> list[str]:
    """Matrix rows whose decision or returned rows differ from the key (reasons are informative only)."""
    return sorted(k for k in expected
                  if observed[k]["decision"] != expected[k]["decision"]
                  or observed[k].get("rows") != expected[k].get("rows"))


def answer_mismatches(given: dict, expected: dict) -> list[str]:
    """Human-readable differences between a learner's answers and the key."""
    problems = []
    for key, want in expected.items():
        got = given.get(key)
        if got is None or any(v is None for v in got.values()):
            problems.append(f"{key}: unanswered")
        elif got != want:
            problems.append(f"{key}: expected {canonical(want)}, given {canonical(got)}")
    return problems


# ---------------------------------------------------------------- evaluator vs hand-authored keys
class EvaluatorTests(unittest.TestCase):
    """The local evaluator reproduces keys written by hand from the rules in DATA.md."""

    def test_twenty_decisions_match_the_key(self):
        m = model()
        key = read(ROOT / "expected" / "decisions.json")["decisions"]
        out = {}
        for r in read(ROOT / "fixtures" / "requests.json")["requests"]:
            out[r["id"]] = m.decide(r["principal"], r["action"], r["securable"])
            with self.subTest(request=r["id"]):
                self.assertEqual(out[r["id"]], key[r["id"]])
        OUTPUTS["decisions"] = out
        self.assertEqual(len(out), 20)

    def test_read_needs_use_catalog_use_schema_and_select(self):
        m = model()
        self.assertEqual(m.decide("maya@cinderline.example", "SELECT", "quality.accepted.inspections"),
                         {"decision": "allow", "reason": "granted"})
        no_schema = copy.deepcopy(m)
        no_schema.grants = [g for g in m.grants if not (g["principal"] == "quality-analysts" and g["privilege"] == "USE SCHEMA")]
        self.assertEqual(no_schema.decide("maya@cinderline.example", "SELECT", "quality.accepted.inspections"),
                         {"decision": "deny", "reason": "missing-use-schema"})
        no_catalog = copy.deepcopy(m)
        no_catalog.grants = [g for g in m.grants if not (g["principal"] == "quality-analysts" and g["privilege"] == "USE CATALOG")]
        self.assertEqual(no_catalog.decide("maya@cinderline.example", "SELECT", "quality.accepted.inspections"),
                         {"decision": "deny", "reason": "missing-use-catalog"})
        no_select = copy.deepcopy(m)
        no_select.grants = [g for g in m.grants if not (g["principal"] == "quality-analysts" and g["privilege"] == "SELECT")]
        self.assertEqual(no_select.decide("maya@cinderline.example", "SELECT", "quality.accepted.inspections"),
                         {"decision": "deny", "reason": "missing-select"})

    def test_schema_level_select_reaches_every_table_in_the_schema(self):
        m = model()
        self.assertEqual(m.decide("ravi@cinderline.example", "SELECT", "quality.accepted.rework_costs")["decision"], "allow")
        self.assertEqual(m.decide("maya@cinderline.example", "SELECT", "quality.accepted.rework_costs"),
                         {"decision": "deny", "reason": "missing-select"})

    def test_nested_group_membership_carries_grants(self):
        m = model()
        self.assertIn("quality-analysts", m.identities("maya@cinderline.example"))
        self.assertNotIn("quality-leads", m.identities("maya@cinderline.example"))
        self.assertEqual(m.identities("sp-nightly-ingest"), {"sp-nightly-ingest", "ingest-jobs"})

    def test_deny_by_default(self):
        m = model()
        self.assertFalse(any("deny" in canonical(g).lower() for g in m.grants), "the grant table holds no deny entries")
        self.assertEqual(m.decide("priya@cinderline.example", "SELECT", "quality.accepted.inspections"),
                         {"decision": "deny", "reason": "unknown-principal"})
        self.assertEqual(m.decide("sp-ci-deploy", "SELECT", "quality.accepted.inspections"),
                         {"decision": "deny", "reason": "missing-use-catalog"})
        self.assertEqual(m.decide("maya@cinderline.example", "SELECT", "quality.accepted.no_such_table"),
                         {"decision": "deny", "reason": "unknown-securable"})

    def test_ownership_covers_the_owned_securable_only(self):
        m = model()
        self.assertEqual(m.decide("lena@cinderline.example", "SELECT", "quality.raw.deliveries"),
                         {"decision": "allow", "reason": "owner"})
        self.assertEqual(m.decide("lena@cinderline.example", "SELECT", "quality.accepted.rework_costs"),
                         {"decision": "deny", "reason": "missing-use-schema"})
        self.assertEqual(m.decide("tess@cinderline.example", "GRANT", "quality.accepted.inspections"),
                         {"decision": "allow", "reason": "owner"})
        self.assertEqual(m.decide("jon@cinderline.example", "GRANT", "quality.accepted.inspections"),
                         {"decision": "deny", "reason": "not-owner"})

    def test_row_filter_and_column_mask_results_match_the_key(self):
        m = model()
        key = read(ROOT / "expected" / "visible.json")["results"]
        out = {}
        for r in read(ROOT / "fixtures" / "row_requests.json")["requests"]:
            out[r["id"]] = m.rows(r["principal"], r["table"])
            with self.subTest(request=r["id"]):
                self.assertEqual(out[r["id"]], key[r["id"]])
        OUTPUTS["visible"] = out

    def test_an_empty_result_is_not_an_error(self):
        result = model().rows("jon@cinderline.example", "quality.accepted.inspections")
        self.assertEqual(result["decision"], "allow")
        self.assertEqual(result["rows"], [])

    def test_a_mask_keeps_the_column_and_replaces_the_value(self):
        m = model()
        stored = read(ROOT / "fixtures" / "tables.json")["quality.accepted.inspections"]
        for row in m.rows("maya@cinderline.example", "quality.accepted.inspections")["rows"]:
            self.assertEqual(set(row), set(stored[0]))
            self.assertEqual(row["inspector_email"], "[masked]")
        leads = m.rows("ravi@cinderline.example", "quality.accepted.inspections")["rows"]
        self.assertEqual(leads, stored)

    def test_the_disclaimer_is_stated(self):
        flat = lambda path: " ".join((ROOT / path).read_text(encoding="utf-8").split())  # ignore Markdown line wraps
        phrase = "a locally evaluated policy table is not Unity Catalog enforcement"
        self.assertIn(phrase, evaluator.DISCLAIMER)
        for path in ("README.md", "SOLUTIONS.md", "run_tests.py"):
            with self.subTest(path=path):
                self.assertIn(phrase, flat(path).replace("A locally", "a locally"))


# ---------------------------------------------------------------- the learner's answers
class AnswerTests(unittest.TestCase):
    """Your answers (solutions/ by default, or --answers DIR) against the hand-authored keys."""

    def test_task1_decisions(self):
        given = read(ANSWERS / "decisions.json")["decisions"]
        key = read(ROOT / "expected" / "decisions.json")["decisions"]
        self.assertEqual(answer_mismatches(given, key), [])

    def test_task2_rows_and_values(self):
        given = read(ANSWERS / "visible.json")["results"]
        key = read(ROOT / "expected" / "visible.json")["results"]
        self.assertEqual(answer_mismatches(given, key), [])

    def test_task3_plan_passes_the_matrix(self):
        plan = read(ANSWERS / "plan.json")
        observed = evaluator.matrix(model().apply(plan), plan_tests())
        OUTPUTS["plan_matrix"] = observed
        key = read(ROOT / "expected" / "plan_matrix.json")["results"]
        self.assertEqual(failing_rows(observed, key), [])

    def test_task3_plan_follows_the_review_rules(self):
        self.assertEqual(model().review_violations(read(ANSWERS / "plan.json")), [])

    def test_task4_escalation_packet(self):
        packet = read(ANSWERS / "escalation.json")
        key = read(ROOT / "expected" / "escalation.json")
        m = model()
        for field in key["requiredFields"]:
            self.assertNotIn(packet.get(field), (None, "", [], {}), f"{field} is empty")
        self.assertEqual(packet["securable"], key["securable"])
        observed = m.decide(packet["principal"], packet["action"], packet["securable"])
        self.assertEqual(observed, key["observedDecision"], "the packet must quote the denial the evaluator gives")
        self.assertEqual(packet["observedDecision"], key["observedDecision"])
        self.assertEqual(packet["securableOwner"], key["securableOwner"])
        roles = [packet["requester"], packet["approver"], packet["applier"]]
        self.assertEqual(len(set(roles)), 3, "requester, approver and applier must be three different people")
        self.assertIn(key["securableOwner"], m.identities(packet["approver"]), "the approver belongs to the owning group")
        proposal = packet["proposal"]
        self.assertTrue(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(proposal.get("expires"))), "the proposal needs an expiry date")
        date.fromisoformat(proposal["expires"])
        self.assertEqual(m.review_violations(proposal), [])
        granted = {(g["privilege"], g["securable"]) for g in proposal["grants"]}
        self.assertEqual(granted, {(key["requiredPrivilege"], key["securable"])}, "grant only the privilege the denial names")
        after = m.apply(proposal)
        self.assertEqual(after.decide(packet["principal"], packet["action"], packet["securable"])["decision"],
                         key["decisionAfterProposal"])
        self.assertGreaterEqual(len(packet["negativeTests"]), key["minimumNegativeTests"])
        for t in packet["negativeTests"]:
            with self.subTest(negative=t):
                self.assertEqual(after.decide(t["principal"], t["action"], t["securable"])["decision"], t["expected"])
        OUTPUTS["escalation_after"] = after.decide(packet["principal"], packet["action"], packet["securable"])


# ---------------------------------------------------------------- deliberate failures
class NegativeCaseTests(unittest.TestCase):
    """Deliberately wrong inputs must fail, and for the named reason."""

    def test_wide_plan_fails_its_must_fail_rows_and_the_review_rules(self):
        self._assert_fails_for("wide_plan")

    def test_admin_plan_fails_its_must_fail_rows_and_the_review_rules(self):
        self._assert_fails_for("admin_plan")

    def _assert_fails_for(self, name):
        plan = read(ROOT / "fixtures" / "negative" / f"{name}.json")
        want = read(ROOT / "expected" / "negative.json")[name]
        observed = evaluator.matrix(model().apply(plan), plan_tests())
        OUTPUTS[f"negative_{name}"] = observed
        key = read(ROOT / "expected" / "plan_matrix.json")["results"]
        self.assertEqual(failing_rows(observed, key), want["failingTests"])
        self.assertEqual(model().review_violations(plan), want["ruleViolations"])
        for test_id in ("P1", "P7"):  # the must-succeed rows still pass: only denials expose a wide plan
            self.assertNotIn(test_id, failing_rows(observed, key))

    def test_a_wrong_answer_is_reported_with_both_values(self):
        given = copy.deepcopy(read(ROOT / "solutions" / "decisions.json")["decisions"])
        given["R03"] = {"decision": "allow", "reason": "granted"}
        key = read(ROOT / "expected" / "decisions.json")["decisions"]
        self.assertEqual(answer_mismatches(given, key), [
            'R03: expected {"decision":"deny","reason":"missing-select"}, given {"decision":"allow","reason":"granted"}'])

    def test_a_plan_naming_an_unknown_principal_is_refused(self):
        with self.assertRaisesRegex(evaluator.PlanError, "unknown principal in plan: portal-team"):
            model().apply({"grants": [{"principal": "portal-team", "privilege": "SELECT",
                                       "securable": "quality.shared.supplier_rejections"}]})


class StarterGapTests(unittest.TestCase):
    """The starters are incomplete on purpose; these tests prove the gaps are real."""

    def test_starter_decisions_are_unanswered_except_the_worked_example(self):
        given = read(ROOT / "starters" / "decisions.json")["decisions"]
        key = read(ROOT / "expected" / "decisions.json")["decisions"]
        problems = answer_mismatches(given, key)
        self.assertEqual(len(problems), 19)
        self.assertTrue(all(p.endswith("unanswered") for p in problems))
        self.assertNotIn("R01: unanswered", problems)

    def test_starter_plan_fails_the_must_succeed_rows(self):
        observed = evaluator.matrix(model().apply(read(ROOT / "starters" / "plan.json")), plan_tests())
        key = read(ROOT / "expected" / "plan_matrix.json")["results"]
        self.assertEqual(failing_rows(observed, key), ["P1", "P7"])

    def test_starter_escalation_packet_is_empty(self):
        packet = read(ROOT / "starters" / "escalation.json")
        empty = [f for f in read(ROOT / "expected" / "escalation.json")["requiredFields"] if packet.get(f) in (None, "", [], {})]
        self.assertEqual(empty, ["requester", "observedDecision", "securableOwner", "approver", "applier",
                                 "negativeTests", "justification"])


# ---------------------------------------------------------------- altered input
class TransferTests(unittest.TestCase):
    """A membership move and a new filter clause change access with no grant edited."""

    def test_membership_move_and_new_filter_clause(self):
        m = model()
        changed = m.apply(read(ROOT / "fixtures" / "transfer" / "changes.json"))
        self.assertEqual(canonical(changed.grants), canonical(m.grants), "no grant was edited")
        requests = read(ROOT / "fixtures" / "transfer" / "requests.json")
        key = read(ROOT / "expected" / "transfer.json")
        out = {}
        for r in requests["decisions"]:
            out[r["id"]] = changed.decide(r["principal"], r["action"], r["securable"])
            with self.subTest(request=r["id"]):
                self.assertEqual(out[r["id"]], key["decisions"][r["id"]])
        for r in requests["rows"]:
            out[r["id"]] = changed.rows(r["principal"], r["table"])
            with self.subTest(request=r["id"]):
                self.assertEqual(out[r["id"]], key["rows"][r["id"]])
        OUTPUTS["transfer"] = out
        self.assertEqual(m.decide("maya@cinderline.example", "SELECT", "quality.accepted.inspections")["decision"], "allow",
                         "the original model is untouched")


def all_files():
    for directory in ("fixtures", "expected", "solutions", "starters"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                yield path


def main() -> int:
    global ANSWERS
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--evidence", type=Path, help="write evidence JSON to this path")
    parser.add_argument("--answers", default="solutions", help="directory holding decisions, visible, plan and escalation JSON")
    args = parser.parse_args()
    ANSWERS = (ROOT / args.answers).resolve()
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    print(evaluator.DISCLAIMER)
    cases = [EvaluatorTests, AnswerTests, NegativeCaseTests, TransferTests]
    if ANSWERS == (ROOT / "solutions").resolve():
        cases.append(StarterGapTests)
    suite = unittest.TestSuite()
    for case in cases:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    exit_code = 0 if result.wasSuccessful() else 1
    evidence = {
        "lab": LAB,
        "executionClass": "tabletop",
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "interpreter": sys.executable,
        "inVirtualEnvironment": sys.prefix != sys.base_prefix,
        "java": "not used",
        "spark": "not used",
        "packages": {},
        "standardLibrary": ["argparse", "copy", "datetime", "hashlib", "json", "pathlib", "platform", "re",
                            "time", "unittest"],
        "platform": platform.system() + " " + platform.release(),
        "startedAt": started_at.isoformat(),
        "finishedAt": datetime.now(timezone.utc).isoformat(),
        "durationSeconds": round(time.monotonic() - started, 3),
        "tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "exit": exit_code,
        "answersChecked": str(ANSWERS.relative_to(ROOT)) if ANSWERS.is_relative_to(ROOT) else "outside the package",
        "moduleUnderTest": "solutions/evaluator.py (local evaluator of the authored policy table)",
        "fixtureHashes": {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p.read_bytes()).hexdigest() for p in all_files()},
        "outputHashes": {name: sha256(canonical(value).encode("utf-8")).hexdigest() for name, value in sorted(OUTPUTS.items())},
        "commands": [" ".join([sys.executable, "run_tests.py"]
                              + (["--answers", args.answers] if args.answers != "solutions" else [])
                              + (["--evidence", "<path>"] if args.evidence else []))],
        "notExecuted": NOT_EXECUTED,
        "notes": ("Tabletop class: the local evaluator checks an authored principal, securable, grant and policy "
                  "table with the standard library, and every expected decision, row set and plan result was "
                  "written by hand from the rules in DATA.md. A locally evaluated policy table is not Unity Catalog "
                  "enforcement; no Databricks workspace, identity provider or network was used."),
    }
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: evidence[k] for k in ("lab", "executionClass", "python", "tests", "failures", "errors",
                                               "skipped", "exit")}, indent=2))
    print(evaluator.DISCLAIMER)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
