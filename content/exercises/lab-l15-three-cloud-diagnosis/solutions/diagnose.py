#!/usr/bin/env python3
"""Local evaluator for lab-l15-three-cloud-diagnosis (standard library only).

    python3.12 solutions/diagnose.py              # every case: its request path as a text table, then each symptom's walk
    python3.12 solutions/diagnose.py --table gcp  # one case's request path table only

Execution class: tabletop. The evaluator walks authored request-path tables
for three fictional deployments of Cinderline Components, one per cloud, and
checks diagnosis answers against keys written by hand. A diagram proves
nothing is deployed: nothing here resolves a name, sends a packet, reads a
policy or contacts AWS, Azure, Google Cloud or Databricks. The rules it
applies are stated in DATA.md, with the places where each real service is
richer than the model.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # keep the package free of __pycache__

import argparse
import copy
import ipaddress
import json
import re
from pathlib import Path

DISCLAIMER = ("Tabletop: this evaluator walks authored request-path tables for three fictional deployments. "
              "A diagram proves nothing is deployed; nothing here contacts AWS, Azure, Google Cloud or Databricks.")
CLOUDS = ("aws", "azure", "gcp")
LAYERS = ("identity", "authorization", "name-resolution", "reachability")
FAMILY = {"identity": "permission", "authorization": "permission",
          "name-resolution": "network", "reachability": "network"}
TYPE_LAYER = {"run-as": "identity", "credential": "identity", "uc-grants": "authorization",
              "allow-list": "authorization", "dns": "name-resolution", "route": "reachability",
              "filter": "reachability", "endpoint-state": "reachability"}
UNKNOWN = "unknown until verified"
SOURCE_KINDS = ("documentation page read", "account team in writing", "test result")
DROPPING_TARGETS = ("blackhole", "None")


class ChangeError(ValueError):
    """A transfer change names a control or a setting the case does not have."""


class CaseError(ValueError):
    """The authored case is malformed (a path step with nothing to read)."""


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _principal(value: str) -> str:
    """'serviceAccount:x@y' and 'x@y' name the same principal."""
    return value.split(":", 1)[1] if value.startswith("serviceAccount:") else value


class Case:
    def __init__(self, data: dict):
        self.data = data
        self.cloud = data["cloud"]
        self.controls = {c["id"]: c for c in data["controls"]}
        self.paths = data["paths"]
        self.symptoms = {s["id"]: s for s in data["symptoms"]}
        self.evidence = {e["id"]: e for e in data["evidence"]}
        self.unknowns = [u["id"] for u in data["unknowns"]]

    @classmethod
    def load(cls, root: Path, cloud: str) -> "Case":
        return cls(read(root / "fixtures" / f"{cloud}.json"))

    # ------------------------------------------------------------------ changes
    def apply(self, changes: list[dict]) -> "Case":
        """Return a copy with each change's settings replaced; the original is untouched."""
        data = copy.deepcopy(self.data)
        by_id = {c["id"]: c for c in data["controls"]}
        for change in changes:
            control = by_id.get(change["control"])
            if control is None:
                raise ChangeError(f"unknown control in change: {change['control']}")
            for key, value in change["set"].items():
                if key not in control["config"]:
                    raise ChangeError(f"{change['control']} has no setting {key}")
                control["config"][key] = copy.deepcopy(value)
        return Case(data)

    # ------------------------------------------------------------------ the walk
    def path_controls(self, request: dict) -> list[str]:
        ordered: list[str] = []
        for segment in request["segments"]:
            for control_id in self.paths[segment]:
                if control_id not in ordered:
                    ordered.append(control_id)
        return ordered

    def walk(self, symptom_id: str) -> dict:
        return self.walk_request(self.symptoms[symptom_id]["request"])

    def walk_request(self, request: dict) -> dict:
        """Check each control on the request's path in order; the first that fails is the broken one."""
        context: dict = {}
        steps, notes = [], []
        for control_id in self.path_controls(request):
            control = self.controls[control_id]
            ok, note = CHECKS[control["type"]](control["config"], request, context)
            steps.append([control_id, "pass" if ok else "fail"])
            notes.append(f"{control_id}: {note}")
            if not ok:
                return {"steps": steps, "brokenControl": control_id,
                        "classification": TYPE_LAYER[control["type"]], "notes": notes}
        return {"steps": steps, "brokenControl": None, "classification": None, "notes": notes}


# ---------------------------------------------------------------------- one check per control type
def check_run_as(cfg, request, context):
    actual = cfg["jobs"].get(request["job"])
    context["principal"] = actual
    if actual == request["designPrincipal"]:
        return True, f"{request['job']} runs as {actual}, as designed"
    return False, f"{request['job']} runs as {actual}; the design names {request['designPrincipal']}"


def check_uc_grants(cfg, request, context):
    principal = context.get("principal")
    if principal is None:
        raise CaseError("uc-grants needs a run-as step before it")
    identities = {principal} | {g for g, members in cfg["groups"].items() if principal in members}
    catalog, schema, _ = request["table"].split(".")
    needed = [("USE CATALOG", catalog), ("USE SCHEMA", f"{catalog}.{schema}"), ("SELECT", request["table"])]
    held = {(g["privilege"], g["securable"]) for g in cfg["grants"] if g["principal"] in identities}
    for privilege, securable in needed:
        if (privilege, securable) not in held:
            return False, f"{principal} lacks {privilege} on {securable}"
    return True, f"{principal} holds USE CATALOG, USE SCHEMA and SELECT"


def check_credential(cfg, request, context):
    context["storageIdentity"] = cfg["identity"]
    return True, f"storage requests act as {cfg['identity']}"


def check_allow_list(cfg, request, context):
    identity = context.get("storageIdentity")
    if identity is None:
        raise CaseError("an allow-list needs a credential step before it")
    need = cfg["requires"]
    for entry in cfg["entries"]:
        if (_principal(entry["principal"]) == identity and entry["resource"] == need["resource"]
                and set(entry["grants"]) & set(need["anyOf"])):
            return True, f"{identity} holds {sorted(set(entry['grants']) & set(need['anyOf']))[0]} on {need['resource']}"
    return False, f"no entry gives {identity} any of {', '.join(need['anyOf'])} on {need['resource']}"


def check_dns(cfg, request, context):
    record = cfg["records"].get(request["name"])
    if request["sourceNetwork"] in cfg["networks"] and record:
        context.update(ip=record["ip"], via=record["via"], answer="private")
    else:
        context.update(ip=None, via="public", answer="public")
    if context["answer"] == request["expect"]:
        return True, f"{request['name']} answers {context['ip']} ({context['via']}) in {request['sourceNetwork']}"
    return False, (f"{request['name']} answers publicly in {request['sourceNetwork']}; "
                   f"the zone answers privately only in {', '.join(cfg['networks']) or 'no network'}")


def check_route(cfg, request, context):
    if request["sourceSubnet"] not in cfg["subnets"]:
        raise CaseError(f"the route table is not associated with {request['sourceSubnet']}")
    address = ipaddress.ip_address(context["ip"])
    matches = [r for r in cfg["routes"] if address in ipaddress.ip_network(r["destination"])]
    if not matches:
        return False, f"no route covers {address}"
    best = max(matches, key=lambda r: ipaddress.ip_network(r["destination"]).prefixlen)
    if best["target"] in DROPPING_TARGETS:
        return False, f"{best['destination']} drops traffic to {address}"
    return True, f"{address} leaves by {best['destination']} to {best['target']}"


def check_filter(cfg, request, context):
    address = ipaddress.ip_address(request["sourceIp"] if cfg["direction"] == "ingress" else context["ip"])
    port = request["port"]
    matches = [r for r in cfg["rules"]
               if address in ipaddress.ip_network(r["cidr"]) and (r["ports"] == "all" or port in r["ports"])]
    if cfg["semantics"] == "allow-only":
        if matches:
            return True, f"a rule admits {address} on {port}"
        return False, f"no rule admits {address} on {port}; a security group allows only what it lists"
    if not matches:
        return False, f"no rule matches {address} on {port}"
    decider = min(matches, key=lambda r: (r["priority"], 0 if r["action"] == "deny" else 1))
    verdict = decider["action"] == "allow"
    return verdict, f"{decider['name']} at priority {decider['priority']} decides: {decider['action']}"


def check_endpoint_state(cfg, request, context):
    if cfg["state"] in cfg["healthy"]:
        return True, f"state {cfg['state']}"
    return False, f"state {cfg['state']}; only {', '.join(cfg['healthy'])} carries traffic"


CHECKS = {"run-as": check_run_as, "uc-grants": check_uc_grants, "credential": check_credential,
          "allow-list": check_allow_list, "dns": check_dns, "route": check_route,
          "filter": check_filter, "endpoint-state": check_endpoint_state}


# ---------------------------------------------------------------------- answers
def load_cases(root: Path) -> dict[str, Case]:
    return {cloud: Case.load(root, cloud) for cloud in CLOUDS}


def _owners(cases: dict[str, Case], item: str, kind: str, besides: str) -> str:
    table = {"control": lambda c: c.controls, "evidence": lambda c: c.evidence, "unknown": lambda c: c.unknowns}[kind]
    owners = [cloud for cloud, case in cases.items() if cloud != besides and item in table(case)]
    return f" (it belongs to: {', '.join(owners)})" if owners else " (no case has it)"


def check_answers(cases: dict[str, Case], answers_doc: dict, key: dict) -> list[str]:
    """Every difference between an answer set and the key, as readable lines; [] means all correct."""
    problems: list[str] = []
    answers = answers_doc.get("answers", {})
    home = {sid: cloud for cloud, case in cases.items() for sid in case.symptoms}
    for sid in sorted(set(answers) - set(key["symptoms"])):
        problems.append(f"{sid}: not a symptom of any case")
    for sid in sorted(key["symptoms"]):
        want, given = key["symptoms"][sid], answers.get(sid)
        if not given or given.get("classification") is None or given.get("brokenControl") is None or not given.get("evidence"):
            problems.append(f"{sid}: unanswered")
            continue
        case = cases[home[sid]]
        request = case.symptoms[sid]["request"]
        on_path = case.path_controls(request)
        segments = ", ".join(request["segments"])
        cls = given["classification"]
        if cls not in LAYERS:
            problems.append(f"{sid}: classification {cls} is not one of {', '.join(LAYERS)}")
        elif cls != want["classification"]:
            problems.append(f"{sid}: classification expected {want['classification']}, given {cls}")
        broken = given["brokenControl"]
        if broken not in case.controls:
            problems.append(f"{sid}: brokenControl {broken} is not a control of the {case.cloud} case"
                            + _owners(cases, broken, "control", case.cloud))
        elif broken not in on_path:
            problems.append(f"{sid}: brokenControl {broken} is not on the request path of {sid} ({segments})")
        if broken != want["brokenControl"]:
            problems.append(f"{sid}: brokenControl expected {want['brokenControl']}, given {broken}")
        needs = FAMILY[want["classification"]]
        seen = set()
        for item in given["evidence"]:
            if item in seen:
                continue
            seen.add(item)
            if item not in case.evidence:
                problems.append(f"{sid}: evidence {item} is not evidence of the {case.cloud} case"
                                + _owners(cases, item, "evidence", case.cloud))
                continue
            control_id = case.evidence[item]["control"]
            if control_id is None:
                continue
            if control_id not in on_path:
                problems.append(f"{sid}: evidence {item} is not on the request path of {sid} ({segments})")
                continue
            family = FAMILY[case.controls[control_id]["layer"]]
            if family != needs:
                problems.append(f"{sid}: evidence {item} is {family} evidence, but a {want['classification']} "
                                f"symptom needs {needs} evidence")
        missing = sorted(set(want["requiredEvidence"]) - seen)
        if missing:
            problems.append(f"{sid}: required evidence missing: {', '.join(missing)}")
    given_unknowns = answers_doc.get("unknowns", {})
    for cloud in CLOUDS:
        rows = given_unknowns.get(cloud, {})
        for row in sorted(set(rows) - set(key["unknowns"][cloud])):
            problems.append(f"{cloud}/{row}: not an open question of the {cloud} case"
                            + _owners(cases, row, "unknown", cloud))
        for row in key["unknowns"][cloud]:
            problems.extend(_unknown_problems(cloud, row, rows.get(row)))
    return problems


def _unknown_problems(cloud: str, row: str, given) -> list[str]:
    where = f"{cloud}/{row}"
    if not given or not given.get("status"):
        return [f"{where}: unanswered"]
    status = given["status"]
    if status == UNKNOWN:
        if not str(given.get("wouldSettle", "")).strip():
            return [f"{where}: an unknown row must name the source or test that would settle it"]
        return []
    source = given.get("source")
    if not source:
        return [f"{where}: status {status} needs a dated source about {cloud}"]
    if source.get("cloud") != cloud:
        return [f"{where}: a source about {source.get('cloud')} never settles a {cloud} row"]
    if source.get("kind") not in SOURCE_KINDS:
        return [f"{where}: a source of kind '{source.get('kind')}' never settles a row"]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(source.get("date", ""))):
        return [f"{where}: a source without a date never settles a row"]
    return [f"{where}: status {status}, but this lab read no source, so the row stays {UNKNOWN}"]


# ---------------------------------------------------------------------- text tables
def render_table(case: Case) -> str:
    """The case's request path as a Markdown text table: every hop, its identity and its controls in order."""
    lines = [f"{case.data['title']}", "",
             "| Path | Hop | Identity | Controls in order (layer) |", "|---|---|---|---|"]
    for row in case.data["requestPath"]:
        if row["segment"] is None:
            controls = "not examined in this case"
        else:
            controls = "; ".join(f"{c} ({case.controls[c]['layer']})" for c in case.paths[row["segment"]])
        lines.append(f"| {row['path']} | {row['hop']} | {row['identity']} | {controls} |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--table", choices=CLOUDS, help="print one case's request path table only")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    cases = load_cases(root)
    print(DISCLAIMER)
    for cloud in ([args.table] if args.table else CLOUDS):
        case = cases[cloud]
        print()
        print(render_table(case))
        if args.table:
            continue
        for sid in case.symptoms:
            result = case.walk(sid)
            print(f"\n{sid} ({case.symptoms[sid]['kind']}): broken control {result['brokenControl']}, "
                  f"classification {result['classification']}")
            for note in result["notes"]:
                print(f"  {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
