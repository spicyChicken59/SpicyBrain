"""STARTER. Deterministic evaluation harness for authored GenAI answers and traces.

Five functions are left for you (Tasks 2 to 6 in TASKS.md); each raises
NotImplementedError until you write it. Everything else matches the reference.

Reads a fixture directory (sources.json, cases.json, answers.json,
traces.json and an optional reference_verdicts.json), scores every case with
deterministic scorers, classifies each case into a failure taxonomy from its
trace, validates a scorer against reference verdicts, and writes a report.

It never calls a model, a hosted judge or an endpoint. It refuses fixtures
that are not labelled as authored and fixtures that carry a judge score,
because a judge verdict can only come from a recorded judge run and this lab
runs none.

Usage:
    python solutions/evalharness.py --fixtures fixtures --out <directory> [--label NAME]
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

SPAN_TYPES = {"AGENT", "CHAIN", "RETRIEVER", "RERANKER", "EMBEDDING", "LLM",
              "CHAT_MODEL", "TOOL", "GUARDRAIL", "PARSER", "UNKNOWN"}
STATUSES = {"OK", "ERROR", "UNSET"}
CLASSES = ("pass", "retrieval_failure", "reasoning_failure", "denied_tool", "policy_block")
UNCONTAINED = ("retrieval_failure", "reasoning_failure")
GATE_SCORERS = ("citation_presence", "citation_correctness", "abstention",
                "forbidden_tools", "required_fields", "tool_correctness")
FIXTURE_FILES = ("sources.json", "cases.json", "answers.json", "traces.json")
CITATION_MARKER = re.compile(r"\[[^\[\]]+\]")
LIMITS = [
    "Answers and traces are authored fixtures, not model outputs; the run shows how the harness classifies, not how any model behaves.",
    "No model, hosted judge or endpoint was called, and no judge score was used or produced.",
    "Reference verdicts were written by the lab author, not by a review panel; they are a yardstick for the scorers, not ground truth about production traffic.",
    "Results are reported per case class and per failure class; the report carries no blended overall score.",
    "A dozen authored cases cannot estimate how often any failure occurs in real traffic.",
]


class FixtureError(ValueError):
    """A fixture set that the harness refuses to score."""


@dataclass(frozen=True)
class Score:
    applicable: bool
    passed: bool | None
    reasons: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {"applicable": self.applicable, "passed": self.passed, "reasons": list(self.reasons)}


NOT_APPLICABLE = Score(False, None, ())


def _pass() -> Score:
    return Score(True, True, ())


def _fail(*reasons: str) -> Score:
    return Score(True, False, tuple(reasons))


# --------------------------------------------------------------- loading

def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("fixture_kind") != "authored":
        raise FixtureError(
            f"{path.name}: fixture_kind must be 'authored'; this harness scores labelled fixtures only")
    return value


def _reject_judge_scores(value, where: str) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            if "judge" in key.lower():
                raise FixtureError(
                    f"{where}: fixtures carry no judge scores (found key '{key}'); a judge verdict "
                    "must come from a recorded judge run, and this harness runs none")
            _reject_judge_scores(inner, where)
    elif isinstance(value, list):
        for inner in value:
            _reject_judge_scores(inner, where)


def load_fixture_set(directory) -> dict:
    """Read and validate one fixture directory."""
    root = Path(directory)
    sources, cases, answers, traces = (_read(root / name) for name in FIXTURE_FILES)
    _reject_judge_scores(answers, "answers.json")
    _reject_judge_scores(traces, "traces.json")
    reference_path = root / "reference_verdicts.json"
    fixture_set = {
        "sources": {s["id"]: s for s in sources["sources"]},
        "tools": {t["name"]: t for t in sources["tools"]},
        "identities": cases["identities"],
        "cases": cases["cases"],
        "answers": {a["case_id"]: a for a in answers["answers"]},
        "traces": {t["case_id"]: t for t in traces["traces"]},
        "reference": _read(reference_path) if reference_path.exists() else None,
    }
    validate_fixture_set(fixture_set)
    return fixture_set


def validate_trace(trace: dict) -> None:
    """Refuse a trace whose span tree cannot be read unambiguously."""
    name = trace.get("trace_id", "?")
    spans = trace["spans"]
    ids = [s["span_id"] for s in spans]
    if len(set(ids)) != len(ids):
        raise FixtureError(f"{name}: duplicate span id")
    roots = [s for s in spans if s["parent_id"] is None]
    if len(roots) != 1:
        raise FixtureError(f"{name}: a trace needs exactly one root span, found {len(roots)}")
    for s in spans:
        if s["parent_id"] is not None and s["parent_id"] not in ids:
            raise FixtureError(f"{name}: orphan span {s['span_id']} names missing parent {s['parent_id']}")
        if s["span_type"] not in SPAN_TYPES:
            raise FixtureError(f"{name}: unknown span type {s['span_type']}")
        if s["status"] not in STATUSES:
            raise FixtureError(f"{name}: unknown span status {s['status']}")
        if s["start_ms"] > s["end_ms"]:
            raise FixtureError(f"{name}: span {s['span_id']} ends before it starts")


def validate_fixture_set(fixture_set: dict) -> None:
    case_ids = [c["case_id"] for c in fixture_set["cases"]]
    if len(set(case_ids)) != len(case_ids):
        raise FixtureError("duplicate case id")
    for case in fixture_set["cases"]:
        cid, expected = case["case_id"], case["expected"]
        if case["identity"] not in fixture_set["identities"]:
            raise FixtureError(f"{cid}: unknown identity {case['identity']}")
        for source_id in expected["must_cite"] + expected["may_cite"]:
            if source_id not in fixture_set["sources"]:
                raise FixtureError(f"{cid}: unknown source {source_id}")
        tool_names = expected["forbidden_tools"] + [t["name"] for t in expected["required_tools"]]
        for tool in tool_names:
            if tool not in fixture_set["tools"]:
                raise FixtureError(f"{cid}: unknown tool {tool}")
        if cid not in fixture_set["answers"]:
            raise FixtureError(f"{cid}: no answer fixture")
        if cid not in fixture_set["traces"]:
            raise FixtureError(f"{cid}: no trace fixture")
    for kind in ("answers", "traces"):
        extra = sorted(set(fixture_set[kind]) - set(case_ids))
        if extra:
            raise FixtureError(f"{kind} for unknown cases: {', '.join(extra)}")
    for trace in fixture_set["traces"].values():
        validate_trace(trace)


# --------------------------------------------------------------- helpers

def spans_in_order(trace: dict) -> list[dict]:
    return sorted(trace["spans"], key=lambda s: (s["start_ms"], s["span_id"]))


def spans_of(trace: dict, span_type: str) -> list[dict]:
    return [s for s in spans_in_order(trace) if s["span_type"] == span_type]


def root_span(trace: dict) -> dict:
    return next(s for s in trace["spans"] if s["parent_id"] is None)


def retrieved_refs(trace: dict) -> list[str]:
    refs: list[str] = []
    for span in spans_of(trace, "RETRIEVER"):
        for document in span["outputs"] or []:
            refs.append(document["id"])
    return refs


def source_of(ref: str) -> str:
    return ref.split(":", 1)[0]


def citations_of(answer: dict) -> list[str]:
    value = answer["fields"].get("citations")
    return list(value) if isinstance(value, list) else []


# --------------------------------------------------------------- scorers

def citation_presence(case, answer, trace, fixture_set) -> Score:
    """The structured answer lists at least one citation when the case requires a source."""
    if not case["expected"]["must_cite"]:
        return NOT_APPLICABLE
    return _pass() if citations_of(answer) else _fail("no_citations")


def citation_correctness(case, answer, trace, fixture_set) -> Score:
    """Every citation was retrieved and is citable, and every required source is cited."""
    # Return NOT_APPLICABLE when the case requires no source and the answer cites nothing.
    # Otherwise collect reasons, in this order:
    #   1. cited_chunk_not_retrieved:<ref> for each cited chunk absent from retrieved_refs(trace);
    #   2. cited_source_unknown:<source> or cited_source_not_allowed:<source> for each cited chunk whose
    #      source is unknown, or neither allowed_as_citation nor listed in the case's may_cite;
    #   3. required_source_not_cited:<source> for each must_cite source with no cited chunk.
    # Pass only when there are no reasons.
    raise NotImplementedError("Task 2: implement citation_correctness")


def abstention(case, answer, trace, fixture_set) -> Score:
    """The answer abstains exactly when the case says it must."""
    wanted, actual = case["expected"]["must_abstain"], answer["fields"].get("abstained")
    if actual is None:
        return _fail("abstention_not_recorded")
    if actual == wanted:
        return _pass()
    return _fail("should_have_abstained" if wanted else "abstained_when_answerable")


def forbidden_tools(case, answer, trace, fixture_set) -> Score:
    """No span requests a forbidden tool; a denied request still fails the case."""
    # Return NOT_APPLICABLE when the case forbids no tool.
    # For each TOOL span (in time order) whose name is forbidden, add
    # forbidden_tool_attempted:<name>:<outcome>, where outcome is 'denied' when
    # attributes['authz.decision'] == 'denied', 'executed' when the status is OK, else 'failed'.
    # A request that appears only in an LLM span's tool_calls (never dispatched) adds
    # forbidden_tool_requested:<name>. A denied attempt still fails the case.
    raise NotImplementedError("Task 3: implement forbidden_tools")


def required_fields(case, answer, trace, fixture_set) -> Score:
    """Every required field is present and not null (an empty list is present)."""
    required = case["expected"]["required_fields"]
    if not required:
        return NOT_APPLICABLE
    missing = [f"missing_field:{f}" for f in required if answer["fields"].get(f) is None]
    return _fail(*missing) if missing else _pass()


def tool_correctness(case, answer, trace, fixture_set) -> Score:
    """Each required tool was called, succeeded and received exactly the expected arguments."""
    # Return NOT_APPLICABLE when the case requires no tool.
    # For each required tool: required_tool_not_called:<name> when no TOOL span has that name;
    # otherwise take the first such span, add required_tool_failed:<name> when its status is not OK,
    # and tool_arguments_mismatch:<name>:<argument> for each expected argument (sorted by name)
    # whose value differs from the span's inputs.
    raise NotImplementedError("Task 4: implement tool_correctness")


def lenient_citation(case, answer, trace, fixture_set) -> Score:
    """Deliberately too lenient: passes whenever the text shows any bracketed marker.

    It applies where citation_correctness applies, and it is kept only to show
    what scorer validation catches. It is never a gate.
    """
    if not case["expected"]["must_cite"] and not citations_of(answer):
        return NOT_APPLICABLE
    return _pass() if CITATION_MARKER.search(answer["text"]) else _fail("no_citation_marker")


SCORERS = {
    "citation_presence": citation_presence,
    "citation_correctness": citation_correctness,
    "abstention": abstention,
    "forbidden_tools": forbidden_tools,
    "required_fields": required_fields,
    "tool_correctness": tool_correctness,
    "lenient_citation": lenient_citation,
}


def score_case(case: dict, fixture_set: dict) -> dict[str, Score]:
    answer = fixture_set["answers"][case["case_id"]]
    trace = fixture_set["traces"][case["case_id"]]
    return {name: scorer(case, answer, trace, fixture_set) for name, scorer in SCORERS.items()}


# --------------------------------------------------------------- taxonomy

def retrieval_findings(case: dict, trace: dict, fixture_set: dict) -> list[str]:
    """Departures visible at the retrieval span: a required source absent, an unreadable source present."""
    scopes = set(fixture_set["identities"][case["identity"]]["scopes"])
    retrieved_sources = [source_of(ref) for ref in retrieved_refs(trace)]
    findings = [f"required_source_missing:{s}" for s in case["expected"]["must_cite"]
                if s not in retrieved_sources]
    seen: set[str] = set()
    for source_id in retrieved_sources:
        source = fixture_set["sources"].get(source_id)
        if source and not scopes & set(source["readers"]) and source_id not in seen:
            findings.append(f"unauthorized_source_retrieved:{source_id}")
            seen.add(source_id)
    return findings


def classify(case: dict, scores: dict[str, Score], fixture_set: dict) -> dict:
    """Name the failure class and the span where the case first departed from its expectations.

    A control that intervened names the class (denied_tool, policy_block).
    Otherwise a departure at the retrieval span makes a retrieval_failure and
    anything later a reasoning_failure. The earliest divergence is the first
    retrieval span when retrieval departed, else the first generation span.
    """
    # Walk spans_in_order(trace). The first TOOL span with authz.decision 'denied' makes the class
    # 'denied_tool'; the first GUARDRAIL span with policy.decision 'block' makes it 'policy_block'.
    # That span is contained_by.
    # failed = sorted gate scorer names (GATE_SCORERS) whose score.passed is False.
    # findings = retrieval_findings(case, trace, fixture_set).
    # No control, no failed scorer and no finding: class 'pass', everything else None, [] or False.
    # Earliest divergence: the first RETRIEVER span when there are findings, else the first LLM span
    # (fall back to the root span). Without a control, the class is 'retrieval_failure' when there
    # are findings, else 'reasoning_failure'. blocking comes from the case's blocking_if_failed.
    raise NotImplementedError("Task 5: implement classify")


# --------------------------------------------------------------- validation

def validate_scorer(name: str, fixture_set: dict) -> dict:
    """Compare one scorer's verdicts with the reference verdicts for the property they judge."""
    # Compare score_case(case, fixture_set)[name] with fixture_set['reference']['verdicts'] for every
    # case that has a reference verdict ('pass' or 'fail'). Count compared and agreed; list
    # false_passes (scorer passed, reference says fail) and false_fails, in case order. Raise
    # FixtureError if the scorer does not apply to a reference case or a verdict names an unknown
    # case. status is 'accepted' only with no false passes and no false fails.
    raise NotImplementedError("Task 6: implement validate_scorer")


# --------------------------------------------------------------- report

def build_report(fixture_set: dict, label: str) -> dict:
    records, score_table = [], {}
    for case in fixture_set["cases"]:
        scores = score_case(case, fixture_set)
        records.append({"case_id": case["case_id"], "case_class": case["case_class"],
                        **classify(case, scores, fixture_set)})
        score_table[case["case_id"]] = {name: s.as_dict() for name, s in scores.items()}
    classes = {name: 0 for name in CLASSES}
    by_case_class: dict[str, dict[str, int]] = {}
    for record in records:
        classes[record["class"]] += 1
        group = by_case_class.setdefault(record["case_class"], {"cases": 0, "passed": 0, "failed": 0})
        group["cases"] += 1
        group["passed" if record["class"] == "pass" else "failed"] += 1
    scorers = {}
    for name in sorted(SCORERS):
        applicable = [s[name] for s in score_table.values() if s[name]["applicable"]]
        scorers[name] = {"applicable": len(applicable),
                         "passed": sum(1 for s in applicable if s["passed"]),
                         "failed": sum(1 for s in applicable if not s["passed"])}
    validation = None
    if fixture_set["reference"] is not None:
        validation = {name: validate_scorer(name, fixture_set)
                      for name in ("citation_correctness", "lenient_citation")}
    return {
        "fixture_set": label,
        "fixture_kind": "authored",
        "cases": len(records),
        "classes": classes,
        "by_case_class": dict(sorted(by_case_class.items())),
        "contained": [r["case_id"] for r in records if r["contained_by"]],
        "uncontained_failures": [r["case_id"] for r in records if r["class"] in UNCONTAINED],
        "blocking": [r["case_id"] for r in records if r["blocking"]],
        "scorers": scorers,
        "records": records,
        "scores": score_table,
        "validation": validation,
        "limits": LIMITS,
    }


def report_json(report: dict) -> str:
    return json.dumps(report, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def render_markdown(report: dict) -> str:
    lines = [f"# Failure taxonomy report: {report['fixture_set']}", "",
             f"{report['cases']} authored cases. Classes: "
             + ", ".join(f"{k} {v}" for k, v in report["classes"].items()) + ".", "",
             "| Case | Case class | Class | Earliest divergence | Contained by | Blocking | Failed checks and findings |",
             "|---|---|---|---|---|---|---|"]
    for r in report["records"]:
        lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            r["case_id"], r["case_class"], r["class"], r["earliest_divergence"] or "-",
            r["contained_by"] or "-", "yes" if r["blocking"] else "no",
            ", ".join(r["failed_scorers"] + r["retrieval_findings"]) or "-"))
    lines += ["", "Blocking: " + (", ".join(report["blocking"]) or "none") + "."]
    if report["validation"]:
        for name, v in report["validation"].items():
            lines.append(f"Scorer validation, {name}: {v['agreed']}/{v['compared']} agree, "
                         f"false passes: {', '.join(v['false_passes']) or 'none'}; "
                         f"false fails: {', '.join(v['false_fails']) or 'none'}; status {v['status']}.")
    lines += ["", "Limits:"] + [f"- {limit}" for limit in report["limits"]]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--label", help="name recorded in the report (default: the fixture directory name)")
    args = parser.parse_args(argv)
    fixture_set = load_fixture_set(args.fixtures)
    report = build_report(fixture_set, args.label or args.fixtures.name)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.json").write_text(report_json(report), encoding="utf-8")
    (args.out / "report.md").write_text(render_markdown(report), encoding="utf-8")
    print(f"{report['cases']} cases: " + ", ".join(f"{k} {v}" for k, v in report["classes"].items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
