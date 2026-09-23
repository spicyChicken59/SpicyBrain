"""lab-l22-tool-authorization test runner (local-executed, Python 3.12 standard library).

    python run_tests.py --evidence <path>     # the reference solution
    python run_tests.py --starter             # your completed starters/gate.py

Run from this directory with Python 3.12; nothing needs installing. Offline:
no network, no model, no Databricks workspace and no MCP server. Scripted
tool proposals (fixtures/calls.json) stand in for a model, and every effect
is an append to an in-memory list held by a local stub. Every expected value
is a literal in expected/*.json, derived by hand as DATA.md explains, or a
literal written in this file; no test compares the gate with a value the gate
computed. The three shortcuts in starters/shortcuts.py are asserted to fail
for their documented reasons, and the starter's six gaps are asserted to be
marked. Fixture, expected, solution, starter and produced-output SHA-256
hashes go into the evidence JSON.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from functools import cache
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
G = import_module("starters.gate" if STARTER else "solutions.gate")
from starters import shortcuts  # noqa: E402

LAB = "lab-l22-tool-authorization"
FIX = ROOT / "fixtures"
TRANSFER = FIX / "transfer"
EXPECTED = {name: json.loads((ROOT / "expected" / f"{name}.json").read_text(encoding="utf-8"))
            for name in ("decisions", "audit", "effects", "retries", "validation", "transfer")}


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


DOCUMENTS = read(FIX / "documents.json")
CALLS = {item["id"]: item for item in read(FIX / "calls.json")}
TOOLS = {tool["name"]: tool for tool in read(FIX / "tools.json")["exposed"]}
FIELDS = ("decision", "reason", "detail", "effect_id", "approval_id", "attempts")
AUDIT_FIELDS = ("seq", "at", "event", "ref", "actor", "on_behalf_of", "tool", "idempotency_key", "decision",
                "reason", "attempts", "effect_id", "approval_id", "influenced_by")
OUTPUTS: dict[str, object] = {}


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def independent_digest(arguments) -> str:
    """Written here, not imported from the gate: SHA-256 of canonical JSON, first 16 hex characters."""
    return sha256(canonical(arguments).encode("utf-8")).hexdigest()[:16]


def project(outcomes: list[dict]) -> list[dict]:
    return [{field: outcome[field] for field in FIELDS} for outcome in outcomes]


@cache
def main_run():
    result = G.run(FIX)
    OUTPUTS["decisions"] = {ref: project(outs) for ref, outs in result["outcomes"].items()}
    OUTPUTS["audit"] = result["gate"].audit_rows()
    OUTPUTS["effects"] = result["downstream"].effects
    return result


@cache
def transfer_run():
    result = G.run(TRANSFER)
    OUTPUTS["transfer_decisions"] = {ref: project(outs) for ref, outs in result["outcomes"].items()}
    OUTPUTS["transfer_effects"] = result["downstream"].effects
    return result


def outcome(ref: str, index: int = 0) -> dict:
    return main_run()["outcomes"][ref][index]


def effects(name: str) -> list[dict]:
    return main_run()["downstream"].effects[name]


class ValidationTests(unittest.TestCase):
    """Task 1: the schema is enforced in code, with fixed messages."""

    def check(self, names):
        for case in EXPECTED["validation"]:
            if case["case"].split()[0] in names:
                with self.subTest(case=case["case"]):
                    schema = TOOLS[case["tool"]]["input_schema"]
                    self.assertEqual(G.validate(schema, case["arguments"]), case["problems"])

    def test_valid_arguments_have_no_problems(self):
        self.check({"V1"})

    def test_patterns_lengths_and_required_properties(self):
        self.check({"V2", "V3"})

    def test_integers_reject_strings_booleans_and_out_of_range_values(self):
        self.check({"V4", "V5", "V6"})

    def test_authority_bearing_extras_and_non_objects_are_rejected(self):
        self.check({"V7", "V8"})


class DecisionTests(unittest.TestCase):
    """Tasks 2 to 4: each call's decision and reason, in the order the gate checks."""

    def test_every_event_matches_its_literal(self):
        expected = EXPECTED["decisions"]
        self.assertEqual(list(main_run()["outcomes"]), expected["order"])
        for ref in expected["order"]:
            with self.subTest(event=ref):
                self.assertEqual(project(main_run()["outcomes"][ref]), expected["events"][ref])

    def test_allowed_read_returns_the_machines_documents_and_no_effect(self):
        self.assertEqual(outcome("C01")["result"], EXPECTED["decisions"]["read_result_C01"])
        self.assertEqual(main_run()["downstream"].reads, EXPECTED["effects"]["reads"])

    def test_insufficient_scope_names_the_missing_permission(self):
        self.assertEqual(outcome("C05")["actor"], "tech-s1")
        self.assertEqual(outcome("C05")["detail"], "missing drafts:write:north (lacking: user)")
        self.assertFalse(any(d["note"].startswith("Checked the filter") for d in effects("drafts")))

    def test_delegated_permission_is_an_intersection(self):
        grants = read(FIX / "identities.json")["users"]["sup-n1"]["grants"]
        self.assertIn("drafts:close:north", grants)  # the supervisor holds it ...
        self.assertEqual(outcome("C14")["detail"], "missing drafts:close:north (lacking: application)")  # ... the app does not
        self.assertEqual(outcome("C13")["detail"], "missing drafts:close:north (lacking: user, application)")
        self.assertEqual(effects("closures"), [])

    def test_missing_user_credential_never_falls_back_to_the_application(self):
        c15 = outcome("C15")
        self.assertEqual((c15["decision"], c15["reason"], c15["actor"]), ("denied", "unauthenticated", None))
        self.assertEqual(len(main_run()["downstream"].reads), 1)  # only C01 reached the manual store

    def test_malformed_calls_never_reach_a_handler(self):
        for ref in ("C06", "C07", "C10"):
            self.assertEqual((outcome(ref)["decision"], outcome(ref)["attempts"]), ("malformed", 0), ref)
        self.assertFalse(any(d["note"] == "Filter blocked." for d in effects("drafts")))
        self.assertFalse(any(p["quantity"] == 50 or p["part_number"] == "P-9001" for p in effects("purchase_requests")))

    def test_an_unexposed_tool_is_denied_whatever_its_advertised_hints_say(self):
        advertised = {t["name"]: t for t in read(FIX / "tools.json")["advertised"]}
        self.assertTrue(advertised["delete_work_order"]["annotations"]["readOnlyHint"])
        self.assertEqual(outcome("C12")["reason"], "tool_not_exposed")
        gate, _, _ = G.build(FIX)
        for hint in (True, False):
            for item in gate.advertised:
                if item["name"] == "delete_work_order":
                    item["annotations"] = {"readOnlyHint": hint, "destructiveHint": not hint}
            self.assertEqual(gate.handle(dict(CALLS["C12"]))["reason"], "tool_not_exposed")

    def test_approval_holds_every_external_effect_until_a_human_decides(self):
        self.assertEqual((outcome("C08")["effect_id"], outcome("C11")["effect_id"]), (None, None))
        gate, downstream, events = G.build(FIX)
        for item in events["calls"]:
            if not item.get("after_approvals"):
                gate.handle(item)
        self.assertEqual(downstream.effects["purchase_requests"], [])  # nothing before any approval
        self.assertEqual(sorted(gate.approvals), ["A1", "A2"])
        self.assertEqual({a["status"] for a in gate.approvals.values()}, {"pending"})


class IdempotencyTests(unittest.TestCase):
    """Task 3: one intent, one key."""

    def test_a_replay_returns_the_first_outcome_without_a_second_effect(self):
        self.assertEqual(outcome("C03")["effect_id"], "D1")
        self.assertEqual([d["id"] for d in effects("drafts") if d["idempotency_key"] == "k-02"], ["D1"])

    def test_the_same_key_with_new_arguments_is_a_conflict(self):
        self.assertEqual(outcome("C04")["reason"], "same_key_different_arguments")
        self.assertEqual(outcome("C19")["reason"], "same_key_different_arguments")
        self.assertFalse(any("2.1 bar" in d["note"] for d in effects("drafts")))
        self.assertEqual([p["quantity"] for p in effects("purchase_requests")], [2])

    def test_keys_are_scoped_to_user_and_tool(self):
        gate, downstream, _ = G.build(FIX)
        first = gate.handle(dict(CALLS["C02"]))
        other = gate.handle({"id": "K1", "session": "s-tech-s1", "tool": "create_maintenance_draft",
                             "arguments": {"machine_id": "C4", "manual_section": "C4-1.2", "note": "Belt tension low."},
                             "idempotency_key": "k-02", "context": []})
        self.assertEqual((first["effect_id"], other["decision"], other["effect_id"]), ("D1", "allowed", "D2"))
        self.assertEqual(len(downstream.effects["drafts"]), 2)

    def test_a_replay_after_execution_returns_the_executed_effect(self):
        c20 = outcome("C20")
        self.assertEqual((c20["decision"], c20["effect_id"], c20["approval_id"]), ("replayed", "PR1", "A1"))
        self.assertEqual(len(effects("purchase_requests")), 1)


class TimeoutTests(unittest.TestCase):
    """Task 5: bounded retry, and a timeout is an unknown outcome."""

    def test_the_retry_schedule_is_bounded_with_exponential_backoff(self):
        for ref in ("C16", "C17", "C18"):
            with self.subTest(event=ref):
                got = outcome(ref)
                OUTPUTS[f"retries_{ref}"] = {"attempts": got["attempts"], "elapsed_ms": got["elapsed_ms"],
                                             "attempt_log": got["attempt_log"]}
                self.assertEqual(OUTPUTS[f"retries_{ref}"], EXPECTED["retries"][ref])

    def test_a_timeout_can_hide_a_committed_effect(self):
        c17 = outcome("C17")
        self.assertEqual((c17["decision"], c17["effect_id"]), ("timed_out", None))
        self.assertEqual([d["id"] for d in effects("drafts") if d["idempotency_key"] == "k-17"], ["D3"])

    def test_the_same_key_resolves_the_unknown_outcome_without_a_duplicate(self):
        self.assertEqual((outcome("C18")["reason"], outcome("C18")["effect_id"]), ("resolved_in_doubt", "D3"))
        self.assertEqual(len(effects("drafts")), 3)

    def test_a_write_without_a_key_gets_exactly_one_attempt(self):
        identities, entities = read(FIX / "identities.json"), read(FIX / "entities.json")
        tools = read(FIX / "tools.json")
        for tool in tools["exposed"]:
            if tool["name"] == "create_maintenance_draft":
                tool["key_required"] = False
        exposed = {t["name"]: t for t in tools["exposed"]}
        downstream = G.Downstream(exposed, {}, {"W1": [{"latency_ms": 3000, "commits": True},
                                                       {"latency_ms": 100, "commits": True}]})
        gate = G.Gate(identities, entities, tools, downstream)
        got = gate.handle({"id": "W1", "session": "s-tech-n1", "tool": "create_maintenance_draft",
                           "arguments": {"machine_id": "M7", "manual_section": "M7-4.2", "note": "No key."},
                           "idempotency_key": None, "context": []})
        self.assertEqual((got["decision"], got["attempts"]), ("timed_out", 1))
        self.assertEqual(len(downstream.effects["drafts"]), 1)  # the single attempt still committed


class ApprovalTests(unittest.TestCase):
    """Task 4: a named person approves exact arguments, once."""

    def test_the_requester_cannot_approve_her_own_request(self):
        self.assertEqual(project([outcome("AP1")]), EXPECTED["decisions"]["events"]["AP1"])

    def test_the_approver_needs_the_approve_grant_for_that_plant(self):
        self.assertEqual(outcome("AP2")["detail"], "missing parts:approve:north")

    def test_an_approval_executes_exactly_once(self):
        approved, executed = main_run()["outcomes"]["AP3"]
        self.assertEqual((approved["actor"], executed["actor"], executed["on_behalf_of"]),
                         ("sup-n1", "app-maint-assistant", "tech-n1"))
        self.assertEqual(outcome("AP4")["reason"], "already_decided")
        self.assertEqual(effects("purchase_requests"), EXPECTED["effects"]["purchase_requests"])

    def test_a_rejected_request_never_executes(self):
        self.assertEqual(main_run()["gate"].approvals["A2"]["status"], "rejected")
        self.assertFalse(any(p["part_number"] == "P-9001" for p in effects("purchase_requests")))

    def test_approvals_store_exact_arguments_and_their_origin(self):
        approvals = main_run()["gate"].approvals
        for approval_id, expected in EXPECTED["effects"]["approvals"].items():
            got = approvals[approval_id]
            self.assertEqual({k: got[k] for k in expected}, expected)
            self.assertEqual(got["args_digest"], independent_digest(expected["arguments"]))
        OUTPUTS["approvals"] = {k: {f: v[f] for f in EXPECTED["effects"]["approvals"][k]} for k, v in approvals.items()}


class InjectionTests(unittest.TestCase):
    """Task 2 and the untrusted-content cases: content never decides."""

    def test_decisions_are_identical_without_retrieved_content(self):
        stripped = G.run(FIX, strip_context=True)
        self.assertEqual({r: project(o) for r, o in stripped["outcomes"].items()},
                         {r: project(o) for r, o in main_run()["outcomes"].items()})
        self.assertEqual(stripped["downstream"].effects, main_run()["downstream"].effects)

    def test_content_cannot_supply_identity_or_approval(self):
        self.assertEqual(outcome("C10")["detail"], "unexpected property 'approved_by'")
        self.assertEqual(outcome("C13")["actor"], "tech-n1")
        self.assertEqual((outcome("C11")["decision"], outcome("C11")["effect_id"]), ("approval_required", None))

    def test_the_audit_keeps_the_origin_of_influencing_content(self):
        self.assertEqual(outcome("C12")["influenced_by"], ["DOC-SUP-117", "DOC-WO-88"])
        self.assertEqual(DOCUMENTS["DOC-SUP-117"]["origin"], "supplier catalogue PDF page (external, unreviewed)")
        self.assertEqual(main_run()["gate"].approvals["A2"]["influenced_by"], ["DOC-SUP-117"])

    def test_the_transfer_is_also_decided_without_its_content(self):
        stripped = G.run(TRANSFER, strip_context=True)
        self.assertEqual({r: project(o) for r, o in stripped["outcomes"].items()},
                         {r: project(o) for r, o in transfer_run()["outcomes"].items()})


class AuditTests(unittest.TestCase):
    """Task 6: every decision is a row, refusals included."""

    def test_audit_rows_match_the_literals(self):
        rows = main_run()["gate"].audit_rows()
        self.assertEqual([{f: row[f] for f in AUDIT_FIELDS} for row in rows], EXPECTED["audit"]["rows"])

    def test_every_decision_is_audited_including_refusals(self):
        rows = main_run()["gate"].audit_rows()
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["decision"]] = counts.get(row["decision"], 0) + 1
        self.assertEqual(counts, EXPECTED["audit"]["decision_counts"])
        self.assertEqual([row["seq"] for row in rows], list(range(1, 27)))
        self.assertEqual({row["executing_identity"] for row in rows}, {EXPECTED["audit"]["executing_identity"]})

    def test_the_audit_holds_digests_not_note_text(self):
        gate = main_run()["gate"]
        notes = [item["arguments"]["note"] for item in CALLS.values() if "note" in item["arguments"]]
        for row in gate.audit_rows():
            text = canonical(row)
            self.assertFalse(any(note in text for note in notes), row["ref"])
            if row["event"] == "call":
                self.assertEqual(row["args_digest"], independent_digest(CALLS[row["ref"]]["arguments"]), row["ref"])
            else:
                self.assertEqual(row["args_digest"], independent_digest(gate.approvals[row["approval_id"]]["arguments"]))

    def test_audit_rows_are_append_only_copies(self):
        gate = main_run()["gate"]
        first = gate.audit_rows()
        first[0]["decision"] = "edited"
        first[0]["influenced_by"].append("DOC-FAKE")
        self.assertEqual(gate.audit_rows()[0]["decision"], "allowed")
        self.assertEqual(gate.audit_rows()[0]["influenced_by"], [])
        self.assertFalse([name for name in dir(gate) if name.startswith(("delete", "update", "edit"))])


class EffectsTests(unittest.TestCase):
    """All effects are local list appends; the final state is a literal."""

    def test_final_effects_match_the_literals(self):
        for name in ("drafts", "closures", "purchase_requests"):
            with self.subTest(collection=name):
                self.assertEqual(effects(name), EXPECTED["effects"][name])


class TransferTests(unittest.TestCase):
    """Altered input: a clinic supply assistant with a threshold approval policy."""

    def test_transfer_decisions_match_the_literals(self):
        expected = EXPECTED["transfer"]
        self.assertEqual(list(transfer_run()["outcomes"]), expected["order"])
        for ref in expected["order"]:
            with self.subTest(event=ref):
                self.assertEqual(project(transfer_run()["outcomes"][ref]), expected["events"][ref])

    def test_transfer_effects_and_audit_counts(self):
        result = transfer_run()
        self.assertEqual(result["downstream"].effects, EXPECTED["transfer"]["effects"])
        rows = result["gate"].audit_rows()
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["decision"]] = counts.get(row["decision"], 0) + 1
        self.assertEqual((len(rows), counts), (EXPECTED["transfer"]["audit_rows"], EXPECTED["transfer"]["decision_counts"]))


class ShortcutTests(unittest.TestCase):
    """The three shortcuts fail for their documented reasons."""

    def test_trusting_retrieved_text_lets_a_document_order_parts(self):
        bad = G.run(FIX, gate_factory=lambda d: self._build(d, shortcuts.content_trusting(G, DOCUMENTS)))
        orders = bad["downstream"].effects["purchase_requests"]
        self.assertIn(("P-9001", 20), [(p["part_number"], p["quantity"]) for p in orders])
        self.assertEqual(bad["outcomes"]["C13"][0]["actor"], "sup-n1")  # identity taken from a comment field
        clean = G.run(FIX, strip_context=True,
                      gate_factory=lambda d: self._build(d, shortcuts.content_trusting(G, DOCUMENTS)))
        self.assertNotEqual(project(bad["outcomes"]["C11"]), project(clean["outcomes"]["C11"]))

    def test_a_fresh_key_per_attempt_duplicates_a_draft(self):
        bad = G.run(FIX, gate_factory=lambda d: self._build(d, shortcuts.fresh_key_per_attempt(G)))
        same_intent = [d for d in bad["downstream"].effects["drafts"] if d["manual_section"] == "M12-2.1"]
        self.assertEqual(len(same_intent), 2)
        self.assertEqual(len([d for d in effects("drafts") if d["manual_section"] == "M12-2.1"]), 1)

    def test_falling_back_to_the_application_serves_a_request_without_its_user(self):
        bad = G.run(FIX, gate_factory=lambda d: self._build(d, shortcuts.application_fallback(G)))
        self.assertEqual(bad["outcomes"]["C15"][0]["decision"], "allowed")
        self.assertEqual(bad["outcomes"]["C15"][0]["actor"], "app-maint-assistant")
        self.assertEqual(outcome("C15")["decision"], "denied")

    @staticmethod
    def _build(fixture_dir, gate_class):
        gate, downstream, events = G.build(fixture_dir)
        replacement = gate_class({"application": gate.application, "users": gate.users, "sessions": gate.sessions},
                                 {"scope_of": gate.scope_of},
                                 {"exposed": list(gate.tools.values()), "advertised": gate.advertised}, downstream)
        return replacement, downstream, events


class StarterTests(unittest.TestCase):
    """The starter's six gaps are marked and raise until they are filled."""

    def test_the_starter_marks_six_gaps(self):
        source = (ROOT / "starters" / "gate.py").read_text(encoding="utf-8")
        for number in range(1, 7):
            self.assertIn(f'raise NotImplementedError("GAP {number}:', source)
        self.assertEqual(source.count('raise NotImplementedError("GAP'), 7)  # GAP 4 covers two functions
        self.assertNotIn("NotImplementedError", (ROOT / "solutions" / "gate.py").read_text(encoding="utf-8"))

    def test_the_unfilled_starter_stops_at_its_first_gap(self):
        starter = import_module("starters.gate")
        gate, _, _ = starter.build(FIX)
        with self.assertRaises(NotImplementedError) as caught:
            gate.handle(dict(CALLS["C01"]))
        self.assertTrue(str(caught.exception).startswith("GAP 1"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--starter", action="store_true",
                        help="test your completed starters/gate.py instead of the reference solution")
    args = parser.parse_args()
    if args.starter and args.evidence:
        parser.error("evidence records the reference solution only; drop --evidence when using --starter")
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    suite = unittest.TestSuite()
    cases = [ValidationTests, DecisionTests, IdempotencyTests, TimeoutTests, ApprovalTests, InjectionTests,
             AuditTests, EffectsTests, TransferTests, ShortcutTests]
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
        "standardLibrary": ["argparse", "datetime", "functools", "hashlib", "importlib", "json",
                            "pathlib", "platform", "re", "sys", "time", "unittest"],
        "java": "not used", "spark": "not used", "platform": platform.system() + " " + platform.release(),
        "startedAt": started_at.isoformat(), "finishedAt": datetime.now(timezone.utc).isoformat(),
        "durationSeconds": round(time.monotonic() - started, 3),
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "exit": exit_code,
        "moduleUnderTest": G.__name__,
        "fixtureHashes": hashes("fixtures"), "expectedHashes": hashes("expected"),
        "solutionHashes": {**hashes("solutions"), **hashes("starters"),
                           "run_tests.py": sha256((ROOT / "run_tests.py").read_bytes()).hexdigest()},
        "outputHashes": {name: sha256(canonical(value).encode("utf-8")).hexdigest()
                         for name, value in sorted(OUTPUTS.items())},
        "commands": [f"{Path(sys.executable).name} run_tests.py --evidence <path>"],
        "notes": ("Plain CPython standard library on one machine: no packages, no network, no model call, no "
                  "Databricks workspace and no MCP server. Scripted tool proposals stand in for a model; the "
                  "policy gate decides from the authenticated session, the exposed tools, the schema, the user's "
                  "grants intersected with the application's delegated scopes, idempotency keys and approval "
                  "policy, and never from retrieved content. Timeouts are simulated by scripted latencies on an "
                  "event clock, not by waiting. Every effect is an append to an in-memory list. Expected values "
                  "are hand-derived literals in expected/*.json (derivations in DATA.md). The content-trusting, "
                  "fresh-key and application-fallback shortcuts in starters/ are asserted to fail for their "
                  "documented reasons; the starter's six gaps are asserted to be marked. Cinderline, the clinic, "
                  "their people, machines, parts and documents are fictional."),
    }
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence[key] for key in ("lab", "python", "tests", "failures", "errors", "skipped", "exit")},
                     indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
