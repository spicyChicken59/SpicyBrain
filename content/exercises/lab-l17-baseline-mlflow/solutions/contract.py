"""The versioned model contract, its checks and the promotion decision for lab L17.

The contract says what the model must accept (input schema), what it returns (output), what it must
achieve on a time-based test period (thresholds) and what evidence a run must carry before its
metrics are even read. decide() applies the evidence gate first, then the thresholds: a run whose
metrics are better is still rejected when its record cannot support a rerun or records a leak.
Promotion means one thing here: the registered model version receives the alias "candidate" and
tags naming the contract and the decision. Nothing is deployed.
"""
import json
from pathlib import Path

import mlflow
from mlflow import MlflowClient
from mlflow.models import get_model_info

from solutions.data import FEATURES, LABEL, OVENS, load_dictionary
from solutions.experiment import training_digest

CONTRACT = {
    "contract_version": "1.0.0",
    "model_name": "cinderline-oven-fault",
    "prediction": {"moment": "09:00 each day, per oven", "horizon_hours": 24,
                   "action": "add the oven to today's inspection round, which holds 2 of the 8 ovens"},
    "input_schema": [{"name": name, "type": "double"} for name in FEATURES],
    "output": {"name": LABEL, "type": "long", "values": [0, 1]},
    "thresholds": {"recall_min": 0.75, "precision_min": 0.2, "warnings_per_day_max": 2.0},
    "evidence": {"split": "time", "post_event_features": "none", "seed_recorded": True,
                 "dataset_digest_recorded": True, "signature_required": True},
    "baselines": {"never_warn": "recall 0", "temperature_rule": "warn when temp_max_c >= 220.0"},
    "fleet_ovens": OVENS,
}
POST_EVENT_ROLES = {"post_event", "label"}
ALIAS = "candidate"


def write_contract(path, contract=CONTRACT):
    Path(path).write_text(json.dumps(contract, indent=1) + "\n", encoding="utf-8")
    return contract


def load_contract(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _columns(spec):
    """A signature side as a list of {name, type} dicts, whether given as JSON text or as a list."""
    columns = json.loads(spec) if isinstance(spec, str) else spec
    return [{"name": c.get("name"), "type": c.get("type")} for c in columns or []]


def check_signature(contract, signature):
    """Compare a signature (as signature.to_dict()) with the contract: inputs by name and type, then the output.

    Names are compared as sets, so a reordered frame is not drift; MLflow itself matches columns by
    name. An extra input is drift here even though MLflow's own enforcement ignores it with a warning.
    """
    if signature is None:
        return {"ok": False, "reasons": ["signature_missing"]}
    actual = {c["name"]: c["type"] for c in _columns(signature.get("inputs"))}
    expected = {c["name"]: c["type"] for c in contract["input_schema"]}
    reasons = [f"missing_input:{n}" for n in sorted(set(expected) - set(actual))]
    reasons += [f"unexpected_input:{n}" for n in sorted(set(actual) - set(expected))]
    reasons += [f"type_mismatch:{n}:{expected[n]}->{actual[n]}" for n in sorted(set(expected) & set(actual))
                if expected[n] != actual[n]]
    outputs = _columns(signature.get("outputs"))
    wanted = contract["output"]
    if len(outputs) != 1 or outputs[0]["name"] != wanted["name"] or outputs[0]["type"] != wanted["type"]:
        found = ",".join(f"{o['name']}:{o['type']}" for o in outputs) or "none"
        reasons.append(f"output_mismatch:{found}")
    return {"ok": not reasons, "reasons": reasons}


def logged_signature(run_id):
    """The signature of the model a run logged, as a dict, or None when the model has none."""
    run = mlflow.get_run(run_id)
    if not (run.outputs and run.outputs.model_outputs):
        return None
    info = get_model_info(f"models:/{run.outputs.model_outputs[0].model_id}")
    return info.signature.to_dict() if info.signature else None


def evidence_report(contract, run_id):
    """Does the run's record carry what the contract demands? Reads params, inputs and the model only."""
    run = mlflow.get_run(run_id)
    params = run.data.params
    reasons = []
    if params.get("split") != contract["evidence"]["split"]:
        reasons.append("split_not_time_based")
    if "seed" not in params:
        reasons.append("seed_not_recorded")
    if training_digest(run_id) is None:
        reasons.append("dataset_digest_missing")
    roles = {c["name"]: c["role"] for c in load_dictionary()["columns"]}
    features = params["features"].split(",") if params.get("features") else []
    if not features:
        reasons.append("features_not_recorded")
    reasons.extend(f"post_event_feature:{f}" for f in features if roles.get(f) in POST_EVENT_ROLES)
    if run.outputs and run.outputs.model_outputs:
        reasons.extend(check_signature(contract, logged_signature(run_id))["reasons"])
    else:
        reasons.append("model_missing")
    return {"run_id": run_id, "ok": not reasons, "reasons": sorted(reasons)}


def threshold_report(contract, metrics):
    """Compare the recorded metrics with the contract's thresholds; an absent precision counts as zero."""
    t = contract["thresholds"]
    reasons = []
    if metrics.get("recall", 0.0) < t["recall_min"]:
        reasons.append("recall_below_min")
    if metrics.get("precision", 0.0) < t["precision_min"]:
        reasons.append("precision_below_min")
    if metrics.get("warnings_per_day", 0.0) > t["warnings_per_day_max"]:
        reasons.append("warnings_above_cap")
    return {"ok": not reasons, "reasons": sorted(reasons)}


def decide(contract, run_id):
    """Evidence first, thresholds second. Metrics are not read until the record has passed."""
    run = mlflow.get_run(run_id)
    evidence = evidence_report(contract, run_id)
    if not evidence["ok"]:
        return {"run_id": run_id, "run_name": run.info.run_name, "decision": "reject", "gate": "evidence",
                "reasons": evidence["reasons"], "metrics": dict(run.data.metrics)}
    thresholds = threshold_report(contract, run.data.metrics)
    decision = "promote-candidate" if thresholds["ok"] else "reject"
    return {"run_id": run_id, "run_name": run.info.run_name, "decision": decision, "gate": "thresholds",
            "reasons": thresholds["reasons"], "metrics": dict(run.data.metrics)}


def promote(contract, decision, model_uri, alias=ALIAS):
    """Register the decided run's model and move the alias to the new version.

    Refuses a run that was not decided promote-candidate. The version is immutable; the alias is a
    mutable pointer that a later decision can move (or move back); nothing is deployed.
    """
    if decision["decision"] != "promote-candidate":
        raise ValueError(f"run {decision['run_name']} was decided {decision['decision']}; nothing to register")
    client = MlflowClient()
    version = mlflow.register_model(model_uri, contract["model_name"])
    client.set_model_version_tag(contract["model_name"], version.version, "contract_version",
                                 contract["contract_version"])
    client.set_model_version_tag(contract["model_name"], version.version, "decided_from_run", decision["run_id"])
    client.set_registered_model_alias(contract["model_name"], alias, version.version)
    return {"name": contract["model_name"], "version": int(version.version), "alias": alias,
            "uri": f"models:/{contract['model_name']}@{alias}"}


LIMITATIONS = [
    "18 faults in the test period (days 85 to 120): differences of a few faults between runs are within noise.",
    "Synthetic data from a seeded generator; nothing here describes real ovens.",
    "Every oven appears in both training and test; behaviour on an oven absent from training is untested.",
    "The evidence gate reads what each run declares; it does not re-derive the split or the features from the rows.",
    "Offline metrics say nothing about serving latency, feature availability in production or monitoring cost.",
    "A logged run records which data was used; it does not certify data quality.",
]


def write_decision(path, contract, decisions, baselines, promotions, limitations=LIMITATIONS):
    """The promotion decision file: the contract version, the baselines, every decision and its reasons,
    what was promoted, and the limits of the evidence."""
    document = {"contract_version": contract["contract_version"], "model_name": contract["model_name"],
                "thresholds": contract["thresholds"], "baselines": baselines,
                "decisions": [{k: d[k] for k in ("run_name", "run_id", "decision", "gate", "reasons")}
                              for d in decisions],
                "promoted": promotions, "limitations": list(limitations),
                "note": "promote-candidate registers the run's model and moves the registry alias 'candidate' to "
                        "that version; nothing is deployed, and a logged run does not certify data quality."}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")
    return document
