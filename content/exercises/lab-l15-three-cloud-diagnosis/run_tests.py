#!/usr/bin/env python3
"""Tabletop checks for lab-l15-three-cloud-diagnosis (standard library only).

    python3.12 run_tests.py --evidence <path>   # check the reference answers in solutions/ and write evidence JSON
    python3.12 run_tests.py --answers starters  # check your own answers after editing starters/answers.json

Execution class: tabletop. solutions/diagnose.py walks the authored request
paths of three separate fictional cases, one on AWS, one on Azure and one on
Google Cloud, and checks diagnosis answers against keys written by hand in
expected/. A diagram proves nothing is deployed: no name is resolved, no
packet is sent, no policy is read and no AWS, Azure, Google Cloud or
Databricks service is contacted. Every expected value was derived on paper
from the rules in DATA.md.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # keep the package free of __pycache__

import argparse
import copy
import json
import platform
import time
import unittest
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "solutions"))
import diagnose  # noqa: E402  (the local evaluator under test)

LAB = "lab-l15-three-cloud-diagnosis"
ANSWERS = ROOT / "solutions"
OUTPUTS: dict[str, object] = {}
NOT_EXECUTED = [
    "Any AWS, Azure or Google Cloud API call, console read or command-line command (the evidence items name them; none was run)",
    "DNS resolution by Route 53 private hosted zones, Azure Private DNS zones or Cloud DNS private zones",
    "Routing and filtering by VPC route tables, security groups, Azure route tables and NSGs, or Google Cloud VPC firewall rules",
    "Private connectivity: AWS PrivateLink interface endpoints, Azure private endpoints, Google Cloud Private Service Connect endpoints",
    "Serverless network connectivity configurations and their private endpoint rules",
    "Authorization by IAM, S3 bucket policies, KMS key policies, Azure role assignments or Cloud Storage IAM",
    "Unity Catalog privilege checks and Databricks job execution under any run-as principal",
    "Provisioning of any workspace, network, key, bucket, storage account, credential or identity",
]
# Terms that belong to one cloud only (case-sensitive): a case that uses another cloud's words has been relabelled.
EXCLUSIVE_TERMS = {
    "aws": ["PrivateLink", "Route 53", "KMS", "s3://", "instance profile", "arn:aws", "EC2"],
    "azure": ["Entra", "managed identity", "abfss://", "access connector", "Private DNS zone", "NSG", "core.windows.net"],
    "gcp": ["service account", "Cloud NAT", "Private Service Connect", "PSC", "Cloud DNS", "gs://", "gserviceaccount.com", "Compute Engine"],
}


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def cases() -> dict[str, diagnose.Case]:
    return diagnose.load_cases(ROOT)


def key() -> dict:
    return read(ROOT / "expected" / "answers.json")


def walk_summary(result: dict) -> dict:
    return {k: result[k] for k in ("steps", "brokenControl", "classification")}


def problems_for(answers_doc: dict) -> list[str]:
    return diagnose.check_answers(cases(), answers_doc, key())


# ---------------------------------------------------------------- evaluator vs hand-authored keys
class EvaluatorTests(unittest.TestCase):
    """The local evaluator reproduces walks written by hand from the rules in DATA.md."""

    def test_six_walks_match_the_hand_key(self):
        want = read(ROOT / "expected" / "walks.json")["walks"]
        out = {}
        for cloud, case in cases().items():
            for sid in case.symptoms:
                out[sid] = walk_summary(case.walk(sid))
                with self.subTest(symptom=sid):
                    self.assertEqual(out[sid], want[sid])
        OUTPUTS["walks"] = out
        self.assertEqual(sorted(out), sorted(want))

    def test_classification_is_the_layer_of_the_first_failing_control(self):
        for cloud, case in cases().items():
            for control in case.controls.values():
                with self.subTest(control=f"{cloud}/{control['id']}"):
                    self.assertEqual(control["layer"], diagnose.TYPE_LAYER[control["type"]])
            for sid in case.symptoms:
                result = case.walk(sid)
                self.assertEqual(result["classification"], case.controls[result["brokenControl"]]["layer"])
                self.assertEqual(result["steps"][-1], [result["brokenControl"], "fail"])
                self.assertTrue(all(verdict == "pass" for _, verdict in result["steps"][:-1]))

    def test_each_case_has_one_denied_and_one_unreachable_symptom(self):
        for cloud, case in cases().items():
            with self.subTest(cloud=cloud):
                self.assertEqual(sorted(s["kind"] for s in case.symptoms.values()), ["denied", "unreachable"])

    def test_a_timeout_is_never_identity_or_authorization(self):
        for cloud, case in cases().items():
            for sid, symptom in case.symptoms.items():
                family = diagnose.FAMILY[case.walk(sid)["classification"]]
                with self.subTest(symptom=sid):
                    self.assertEqual(family, "network" if symptom["kind"] == "unreachable" else "permission")

    def test_all_four_classifications_are_exercised(self):
        seen = {case.walk(sid)["classification"] for case in cases().values() for sid in case.symptoms}
        self.assertEqual(seen, set(diagnose.LAYERS))

    def test_paths_and_evidence_name_only_their_own_cases_controls(self):
        for cloud, case in cases().items():
            on_paths = {c for ids in case.paths.values() for c in ids}
            with self.subTest(cloud=cloud):
                self.assertEqual(on_paths, set(case.controls), "every path step is a control of the case and every control is on a path")
                self.assertTrue({e["control"] for e in case.evidence.values()} - {None} <= set(case.controls))
                for sid, symptom in case.symptoms.items():
                    self.assertTrue(set(symptom["request"]["segments"]) <= set(case.paths), sid)
                segments = {row["segment"] for row in case.data["requestPath"]} - {None}
                self.assertEqual(segments, set(case.paths), "the request path table shows every walkable segment")

    def test_cloud_side_controls_and_evidence_are_disjoint_across_cases(self):
        loaded = cases()
        shared_controls = {"run-as", "uc-grants"}
        shared_evidence = {"error-record", "job-run-as-setting", "show-grants-output"}
        for cloud, case in loaded.items():
            side = {c["id"] for c in case.controls.values() if c["side"] != "databricks"}
            self.assertEqual({c["id"] for c in case.controls.values() if c["side"] == "databricks"}, shared_controls)
            self.assertTrue(all(case.controls[c]["side"] == cloud for c in side), cloud)
            for other, other_case in loaded.items():
                if other == cloud:
                    continue
                with self.subTest(pair=f"{cloud}/{other}"):
                    self.assertEqual(set(case.controls) & set(other_case.controls), shared_controls)
                    self.assertEqual(set(case.evidence) & set(other_case.evidence), shared_evidence)
                    self.assertEqual(set(case.unknowns) & set(other_case.unknowns), set())

    def test_each_case_uses_only_its_own_clouds_vocabulary(self):
        for cloud in diagnose.CLOUDS:
            text = (ROOT / "fixtures" / f"{cloud}.json").read_text(encoding="utf-8")
            with self.subTest(cloud=cloud):
                self.assertTrue(any(term in text for term in EXCLUSIVE_TERMS[cloud]), "the case speaks its own cloud's terms")
                foreign = [t for other, terms in EXCLUSIVE_TERMS.items() if other != cloud for t in terms if t in text]
                self.assertEqual(foreign, [])

    def test_a_success_on_a_different_identity_proves_nothing(self):
        aws = cases()["aws"]
        legacy = aws.walk_request({"segments": ["storage-classic-legacy"]})
        self.assertEqual(legacy["brokenControl"], None, "the instance profile's role may use the key")
        self.assertEqual(aws.walk("AWS-D")["brokenControl"], "kms-key-policy", "the storage credential's role may not")
        OUTPUTS["aws_legacy_read"] = walk_summary(legacy)

    def test_priority_and_allow_only_filter_semantics(self):
        flow = {"sourceIp": "10.20.1.9", "port": 443}
        ctx = {"ip": "10.20.8.2"}
        rule = lambda name, prio, action, cidr: {"name": name, "priority": prio, "action": action, "cidr": cidr, "ports": "all"}
        lowest_wins = {"semantics": "priority", "direction": "egress",
                       "rules": [rule("allow", 1000, "allow", "10.20.8.0/28"), rule("deny", 900, "deny", "0.0.0.0/0")]}
        self.assertEqual(diagnose.check_filter(lowest_wins, flow, ctx)[0], False)
        tie = {"semantics": "priority", "direction": "egress",
               "rules": [rule("allow", 1000, "allow", "10.20.8.0/28"), rule("deny", 1000, "deny", "10.20.8.0/28")]}
        self.assertEqual(diagnose.check_filter(tie, flow, ctx)[0], False, "at equal priority a deny wins")
        renumbered = {"semantics": "priority", "direction": "egress",
                      "rules": [rule("allow", 800, "allow", "10.20.8.0/28"), rule("deny", 900, "deny", "0.0.0.0/0")]}
        self.assertEqual(diagnose.check_filter(renumbered, flow, ctx)[0], True)
        group = {"semantics": "allow-only", "direction": "ingress", "rules": [{"cidr": "10.20.0.0/24", "ports": [443]}]}
        self.assertEqual(diagnose.check_filter(group, flow, ctx)[0], False, "an allow-only group refuses what it does not list")
        self.assertEqual(diagnose.check_filter(group, {"sourceIp": "10.20.0.5", "port": 443}, ctx)[0], True)

    def test_a_zone_answers_privately_only_to_the_networks_it_serves(self):
        gcp = cases()["gcp"]
        zone = gcp.controls["cloud-dns-private-zone"]["config"]
        ask = {"name": "tunnel.us-east4.gcp.databricks.com", "expect": "private"}
        inside, outside = {}, {}
        self.assertTrue(diagnose.check_dns(zone, {**ask, "sourceNetwork": "cl-vpc-transit"}, inside)[0])
        self.assertEqual(inside["ip"], "10.20.8.2")
        self.assertFalse(diagnose.check_dns(zone, {**ask, "sourceNetwork": "cl-vpc-dbx"}, outside)[0])
        self.assertEqual(outside["answer"], "public")

    def test_error_texts_are_fictional_and_diagrams_are_text(self):
        for cloud, case in cases().items():
            for sid, symptom in case.symptoms.items():
                with self.subTest(symptom=sid):
                    self.assertIs(symptom["observedIsFictional"], True)
        members = [p for p in ROOT.rglob("*") if p.is_file()]
        self.assertEqual([p.name for p in members if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}], [])
        for path in members:
            if path.suffix == ".md":
                with self.subTest(path=path.name):
                    self.assertNotIn("![", path.read_text(encoding="utf-8"))

    def test_the_case_sheet_names_every_control_evidence_item_symptom_and_question(self):
        sheet = (ROOT / "CASES.md").read_text(encoding="utf-8")
        for cloud, case in cases().items():
            for item in list(case.controls) + list(case.evidence) + list(case.symptoms) + case.unknowns:
                with self.subTest(item=f"{cloud}/{item}"):
                    self.assertIn(f"`{item}`" if item not in case.symptoms else f"**{item} ", sheet)

    def test_the_disclaimer_is_stated(self):
        flat = lambda path: " ".join((ROOT / path).read_text(encoding="utf-8").split())  # ignore Markdown line wraps
        phrase = "a diagram proves nothing is deployed"
        self.assertIn(phrase, diagnose.DISCLAIMER.lower())
        for path in ("README.md", "SOLUTIONS.md", "CASES.md", "run_tests.py"):
            with self.subTest(path=path):
                self.assertIn(phrase, flat(path).replace("A diagram", "a diagram"))


# ---------------------------------------------------------------- the learner's answers
class AnswerTests(unittest.TestCase):
    """Your answers (solutions/ by default, or --answers DIR) against the hand-authored keys."""

    def _symptom_problems(self, *topics):
        """Problems about the six symptoms (their lines start with a symptom ID, not cloud/row)."""
        found = problems_for(read(ANSWERS / "answers.json"))
        return [p for p in found if "/" not in p.split(":", 1)[0] and any(f": {t}" in p for t in topics)]

    def test_task1_classifications(self):
        self.assertEqual(self._symptom_problems("classification", "unanswered", "not a symptom"), [])

    def test_task2_broken_controls(self):
        self.assertEqual(self._symptom_problems("brokenControl"), [])

    def test_task3_evidence(self):
        self.assertEqual(self._symptom_problems("evidence", "required evidence"), [])

    def test_task4_open_questions_stay_unknown(self):
        found = problems_for(read(ANSWERS / "answers.json"))
        self.assertEqual([p for p in found if "/" in p.split(":", 1)[0]], [])

    def test_every_cited_control_and_evidence_item_exists_in_its_own_case(self):
        loaded = cases()
        home = {sid: cloud for cloud, case in loaded.items() for sid in case.symptoms}
        answers = read(ANSWERS / "answers.json")["answers"]
        cited = {}
        for sid, given in answers.items():
            case = loaded[home[sid]]
            cited[sid] = {"brokenControl": given.get("brokenControl"), "evidence": given.get("evidence") or []}
            with self.subTest(symptom=sid):  # an unanswered symptom cites nothing; Task 1 reports it
                if cited[sid]["brokenControl"] is not None:
                    self.assertIn(cited[sid]["brokenControl"], case.controls)
                self.assertEqual([e for e in cited[sid]["evidence"] if e not in case.evidence], [])
        OUTPUTS["answers_checked"] = cited


# ---------------------------------------------------------------- deliberate failures
class NegativeCaseTests(unittest.TestCase):
    """Deliberately wrong answer sets must fail, and for the named reasons."""

    def _assert_refused(self, name):
        doc = read(ROOT / "fixtures" / "negative" / f"{name}.json")
        observed = problems_for(doc)
        OUTPUTS[f"negative_{name}"] = observed
        self.assertEqual(observed, read(ROOT / "expected" / "negative.json")[name])
        return observed

    def test_relabelled_answers_are_refused_for_naming_another_clouds_controls(self):
        observed = self._assert_refused("relabelled")
        self.assertFalse(any("classification" in p for p in observed), "the classification was right; the names were not")

    def test_wrong_layer_answers_fail_for_the_named_reasons(self):
        self._assert_refused("wrong_layer")

    def test_evidence_from_a_path_the_request_never_took_is_refused(self):
        self._assert_refused("off_path")

    def test_a_wrong_answer_is_reported_with_both_values(self):
        doc = copy.deepcopy(read(ROOT / "solutions" / "answers.json"))
        doc["answers"]["AWS-D"]["classification"] = "reachability"
        self.assertEqual(problems_for(doc), ["AWS-D: classification expected authorization, given reachability"])

    def test_an_unknown_row_without_a_way_to_settle_it_is_refused(self):
        doc = copy.deepcopy(read(ROOT / "solutions" / "answers.json"))
        doc["unknowns"]["azure"]["azure-ncc-limits"]["wouldSettle"] = " "
        doc["unknowns"]["aws"]["aws-cmk-tier"] = {"status": "supported", "source": {"kind": "test result", "cloud": "aws", "date": "2026-09-01"}}
        self.assertEqual(problems_for(doc), [
            "aws/aws-cmk-tier: status supported, but this lab read no source, so the row stays unknown until verified",
            "azure/azure-ncc-limits: an unknown row must name the source or test that would settle it"])

    def test_a_change_naming_an_unknown_control_is_refused(self):
        with self.assertRaisesRegex(diagnose.ChangeError, "unknown control in change: nsg-host-subnet"):
            cases()["gcp"].apply([{"control": "nsg-host-subnet", "set": {"rules": []}}])


class StarterGapTests(unittest.TestCase):
    """The starters are incomplete on purpose; this test proves the gaps are real."""

    def test_starter_answers_are_unanswered_except_the_worked_examples(self):
        observed = problems_for(read(ROOT / "starters" / "answers.json"))
        self.assertEqual(observed, read(ROOT / "expected" / "negative.json")["starters"])
        self.assertFalse(any(p.startswith("AWS-D") or p.startswith("aws/aws-relay-endpoint-service") for p in observed))


# ---------------------------------------------------------------- altered input
class TransferTests(unittest.TestCase):
    """Changed configurations move the first failing control, and sometimes the classification with it."""

    def test_scenarios_match_the_hand_key(self):
        loaded = cases()
        want = read(ROOT / "expected" / "transfer.json")["scenarios"]
        out = {}
        for scenario in read(ROOT / "fixtures" / "transfer" / "scenarios.json")["scenarios"]:
            result = loaded[scenario["cloud"]].apply(scenario["changes"]).walk(scenario["symptom"])
            out[scenario["id"]] = {"brokenControl": result["brokenControl"], "classification": result["classification"]}
            with self.subTest(scenario=scenario["id"]):
                self.assertEqual(out[scenario["id"]], want[scenario["id"]])
        OUTPUTS["transfer"] = out
        self.assertEqual(sorted(out), sorted(want))

    def test_fixing_one_fault_exposes_the_next(self):
        scenarios = {s["id"]: s for s in read(ROOT / "fixtures" / "transfer" / "scenarios.json")["scenarios"]}
        azure = cases()["azure"]
        chain = [azure.walk("AZ-U")["brokenControl"]] + [
            azure.apply(scenarios[sid]["changes"]).walk("AZ-U")["brokenControl"] for sid in ("T-AZ-1", "T-AZ-2", "T-AZ-3")]
        self.assertEqual(chain, ["private-dns-zone-link", "private-endpoint-connection", "storage-role-assignment", None])
        OUTPUTS["azure_chain"] = chain

    def test_a_timeout_can_become_a_different_layer_after_a_fix(self):
        gcp = cases()["gcp"]
        scenarios = {s["id"]: s for s in read(ROOT / "fixtures" / "transfer" / "scenarios.json")["scenarios"]}
        before = gcp.walk("GCP-U")["classification"]
        after = gcp.apply(scenarios["T-GCP-1"]["changes"]).walk("GCP-U")["classification"]
        self.assertEqual((before, after), ("name-resolution", "reachability"))

    def test_the_base_cases_are_untouched_by_changes(self):
        loaded = cases()
        before = {cloud: canonical(case.data) for cloud, case in loaded.items()}
        for scenario in read(ROOT / "fixtures" / "transfer" / "scenarios.json")["scenarios"]:
            loaded[scenario["cloud"]].apply(scenario["changes"])
        self.assertEqual({cloud: canonical(case.data) for cloud, case in loaded.items()}, before)


def all_files():
    for directory in ("fixtures", "expected", "solutions", "starters"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                yield path
    yield ROOT / "CASES.md"


def main() -> int:
    global ANSWERS
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--evidence", type=Path, help="write evidence JSON to this path")
    parser.add_argument("--answers", default="solutions", help="directory holding answers.json")
    args = parser.parse_args()
    ANSWERS = (ROOT / args.answers).resolve()
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    print(diagnose.DISCLAIMER)
    suites = [EvaluatorTests, AnswerTests, NegativeCaseTests, TransferTests]
    if ANSWERS == (ROOT / "solutions").resolve():
        suites.append(StarterGapTests)
    suite = unittest.TestSuite()
    for case in suites:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if ANSWERS != (ROOT / "solutions").resolve():
        for line in problems_for(read(ANSWERS / "answers.json")):
            print(f"  {line}")
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
        "standardLibrary": ["argparse", "copy", "datetime", "hashlib", "ipaddress", "json", "pathlib", "platform",
                            "re", "time", "unittest"],
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
        "moduleUnderTest": "solutions/diagnose.py (local evaluator of the authored request-path tables)",
        "fixtureHashes": {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p.read_bytes()).hexdigest() for p in all_files()},
        "outputHashes": {name: sha256(canonical(value).encode("utf-8")).hexdigest() for name, value in sorted(OUTPUTS.items())},
        "commands": [" ".join([sys.executable, "run_tests.py"]
                              + (["--answers", args.answers] if args.answers != "solutions" else [])
                              + (["--evidence", "<path>"] if args.evidence else []))],
        "notExecuted": NOT_EXECUTED,
        "notes": ("Tabletop class: the local evaluator walks three authored request-path tables (AWS, Azure, Google "
                  "Cloud) with the standard library, and every expected walk, classification, refusal message and "
                  "transfer result was written by hand from the rules in DATA.md. A diagram proves nothing is "
                  "deployed; no cloud account, Databricks workspace, identity provider or network was used."),
    }
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: evidence[k] for k in ("lab", "executionClass", "python", "tests", "failures", "errors",
                                               "skipped", "exit")}, indent=2))
    print(diagnose.DISCLAIMER)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
