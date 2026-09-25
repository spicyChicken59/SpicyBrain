"""Starter for Lab L22: the policy gate with six marked gaps (GAP 1 to GAP 6).

Everything that is not a gap already works: loading fixtures, the Downstream
stub, the event clock, the order of checks in Gate.handle and the approval
flow in Gate.decide_approval. Fill each gap so that
`python run_tests.py --starter` passes. The rules and message formats are in
TASKS.md. Standard library only; nothing here calls a model or a network.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

CLOCK_START = datetime(2026, 9, 21, 8, 0, tzinfo=timezone.utc)
DEFAULT_LATENCY_MS = 100
DECISIONS = ("allowed", "denied", "malformed", "conflict", "replayed",
             "approval_required", "timed_out", "approved", "rejected")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(arguments) -> str:
    """First 16 hex characters of the SHA-256 of the canonical JSON arguments."""
    return hashlib.sha256(canonical(arguments).encode("utf-8")).hexdigest()[:16]


def validate(schema: dict, arguments) -> list[str]:
    """Return the schema violations of `arguments` in a fixed order; [] means valid.

    Supported keywords: type (object, string, integer), required,
    additionalProperties false, maxLength, pattern, minimum, maximum, enum.
    Order: missing required properties (schema order), unexpected properties
    (alphabetical), then per-property problems (alphabetical by property).
    """
    # GAP 1: check the arguments against the tool's JSON Schema subset.
    # Return [] when valid, otherwise the problems in this order: missing required properties
    # (schema order), unexpected properties when additionalProperties is false (alphabetical), then
    # per-property problems (alphabetical). Message formats are listed in TASKS.md, task 1.
    raise NotImplementedError("GAP 1: check the arguments against the tool's JSON Schema subset")


class Downstream:
    """Local stand-ins for the target systems. An effect is a list append.

    `conditions` scripts the network per event reference (a call id or an
    approval action id): each attempt consumes one step with a latency and a
    `commits` flag saying whether the request reached the store. A late reply
    can therefore follow a committed effect, which is what makes a timeout an
    unknown outcome. The store remembers effects by (collection, user, key),
    so a repeated key from the same user returns the existing effect instead
    of creating another, and two users' identical key strings never collide.
    """

    def __init__(self, tools: dict, index: dict, conditions: dict):
        self.tools = tools
        self.index = index
        self.conditions = {ref: list(steps) for ref, steps in conditions.items()}
        self.effects = {tool["effect_collection"]: [] for tool in tools.values() if tool.get("effect_collection")}
        self.by_key: dict[tuple[str, str, str], str] = {}
        self.reads: list[dict] = []

    def _step(self, ref: str) -> dict:
        steps = self.conditions.get(ref)
        return steps.pop(0) if steps else {"latency_ms": DEFAULT_LATENCY_MS, "commits": True}

    def perform(self, tool: dict, arguments: dict, key, on_behalf_of: str, extra: dict, ref: str):
        """One attempt. Returns (latency_ms, result); the effect may exist even if the reply is late."""
        step = self._step(ref)
        collection = tool.get("effect_collection")
        if collection is None:
            entity = arguments[tool["entity_arg"]]
            self.reads.append({"tool": tool["name"], "entity": entity, "on_behalf_of": on_behalf_of})
            return step["latency_ms"], {"documents": sorted(self.index.get(entity, []))}
        slot = (collection, on_behalf_of, key)
        if key is not None and slot in self.by_key:
            return step["latency_ms"], {"effect_id": self.by_key[slot]}
        if not step.get("commits", True):
            return step["latency_ms"], {"effect_id": None}
        effect_id = f"{tool['effect_prefix']}{len(self.effects[collection]) + 1}"
        record = {"id": effect_id}
        record.update({field: arguments[field] for field in tool["effect_fields"]})
        record.update({"requested_by": on_behalf_of, **extra, "idempotency_key": key})
        self.effects[collection].append(record)
        if key is not None:
            self.by_key[slot] = effect_id
        return step["latency_ms"], {"effect_id": effect_id}


class Gate:
    """Application-side policy gate between proposed tool calls and their handlers."""

    def __init__(self, identities: dict, entities: dict, tools: dict, downstream: Downstream):
        self.application = identities["application"]
        self.users = identities["users"]
        self.sessions = identities["sessions"]
        self.scope_of = entities["scope_of"]
        self.tools = {tool["name"]: tool for tool in tools["exposed"]}
        self.advertised = tools.get("advertised", [])  # discovery only; never consulted for a decision
        self.downstream = downstream
        self.keys: dict[tuple, dict] = {}
        self.approvals: dict[str, dict] = {}
        self._audit: list[dict] = []
        self._events = 0

    # --- identity -------------------------------------------------------
    def _user(self, session_id):
        """The authenticated user of a session, or None. Never taken from arguments or content."""
        session = self.sessions.get(session_id) if session_id else None
        if not session or not session.get("valid"):
            return None
        return session["user"]

    def _tick(self) -> str:
        at = CLOCK_START + timedelta(minutes=self._events)
        self._events += 1
        return at.strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- audit ------------------------------------------------------------
    def _record(self, at, base, decision, reason, detail="", *, effect_id=None, approval_id=None,
                attempts=0, extra=None) -> dict:
        """Append one audit row (refusals included) and return it with any non-audited extras."""
        # GAP 6: append one audit row and return the outcome.
        # Build the row with every field listed in TASKS.md, task 6, append a copy to self._audit and
        # return a copy that also carries `extra`. Record refusals exactly as carefully as successes.
        raise NotImplementedError("GAP 6: append one audit row and return the outcome")

    def audit_rows(self) -> list[dict]:
        """Copies of the append-only audit; there is no method that edits or deletes a row."""
        return [dict(row, influenced_by=list(row["influenced_by"])) for row in self._audit]

    # --- checks -------------------------------------------------------------
    def _authorize(self, user: str, tool: dict, scope: str):
        """Delegated permission is an intersection: the user's grant AND the application's scope."""
        # GAP 2: compute the required permission and who lacks it.
        # Required permission = f"{tool['permission']}:{scope}". Return (permission, lacking) where
        # lacking lists 'user' if the user's grants miss it, then 'application' if the application's
        # delegated_scopes miss tool['permission']. Delegation is an intersection, never a union.
        raise NotImplementedError("GAP 2: compute the required permission and who lacks it")

    def _key_status(self, slot, args_digest: str) -> str:
        """'new', 'conflict', 'replay' or 'resolve' for an idempotency slot (user, tool, key)."""
        # GAP 3: classify an idempotency slot.
        # No slot or unseen slot -> 'new'; stored digest differs -> 'conflict'; stored state
        # 'in_doubt' -> 'resolve'; any other stored state -> 'replay'.
        raise NotImplementedError("GAP 3: classify an idempotency slot")

    def _needs_approval(self, tool: dict, arguments: dict) -> bool:
        """'always', 'never' or {'above': {'field': ..., 'value': ...}} from the tool's policy."""
        # GAP 4: decide whether the tool's policy holds this call for a human.
        # 'always' -> True, 'never' -> False, {'above': {'field': f, 'value': v}} -> arguments[f] > v.
        raise NotImplementedError("GAP 4: decide whether the tool's policy holds this call for a human")

    def _execute(self, tool: dict, arguments: dict, key, on_behalf_of: str, extra: dict, ref: str) -> dict:
        """Bounded retry with exponential backoff; every attempt carries the same key.

        A write without a key gets one attempt only, because repeating it could
        repeat the effect. Timeouts are the only retried failure in this lab.
        """
        # GAP 5: bounded retry with exponential backoff and the same key on every attempt.
        # Call self.downstream.perform(...) up to tool['max_attempts'] times (once for a write without a
        # key). A reply later than tool['timeout_ms'] is a timeout: count timeout_ms, wait
        # backoff_ms * 2 ** (attempt - 1) unless it was the last attempt. Return the dict described in
        # TASKS.md, task 5 (status, attempts, elapsed_ms, log, result).
        raise NotImplementedError("GAP 5: bounded retry with exponential backoff and the same key on every attempt")

    # --- tool calls -----------------------------------------------------------
    def handle(self, call: dict) -> dict:
        at = self._tick()
        user = self._user(call.get("session"))
        name = call["tool"]
        arguments = call.get("arguments", {})
        key = call.get("idempotency_key")
        base = {"event": "call", "ref": call["id"], "actor": user, "on_behalf_of": user, "tool": name,
                "args_digest": digest(arguments), "idempotency_key": key,
                "influenced_by": sorted(call.get("context", []))}
        if user is None:
            return self._record(at, base, "denied", "unauthenticated",
                                "no valid session; the application's identity is not used as a fallback")
        tool = self.tools.get(name)
        if tool is None:
            return self._record(at, base, "denied", "tool_not_exposed",
                                f"'{name}' is not in the application's exposed tools")
        problems = validate(tool["input_schema"], arguments)
        if tool.get("key_required") and not key:
            problems.append("missing idempotency key")
        if problems:
            return self._record(at, base, "malformed", "schema_violation", "; ".join(problems))
        entity = arguments[tool["entity_arg"]]
        scope = self.scope_of.get(entity)
        if scope is None:
            return self._record(at, base, "malformed", "unknown_entity", f"unknown {tool['entity_arg']} '{entity}'")
        permission, lacking = self._authorize(user, tool, scope)
        if lacking:
            return self._record(at, base, "denied", "insufficient_scope",
                                f"missing {permission} (lacking: {', '.join(lacking)})")
        slot = (user, name, key) if key is not None else None
        status = self._key_status(slot, base["args_digest"])
        if status == "conflict":
            return self._record(at, base, "conflict", "same_key_different_arguments",
                                f"key {key} already used with different arguments")
        if status == "replay":
            stored = self.keys[slot]
            return self._record(at, base, "replayed", "same_key_same_arguments",
                                f"stored outcome: {stored['state']}", effect_id=stored.get("effect_id"),
                                approval_id=stored.get("approval_id"))
        resolving = status == "resolve"
        if not resolving and self._needs_approval(tool, arguments):
            approval_id = f"A{len(self.approvals) + 1}"
            self.approvals[approval_id] = {
                "id": approval_id, "tool": name, "arguments": dict(arguments), "args_digest": base["args_digest"],
                "requester": user, "scope": scope, "idempotency_key": key, "status": "pending",
                "approver": None, "effect_id": None, "influenced_by": list(base["influenced_by"])}
            self.keys[slot] = {"digest": base["args_digest"], "state": "pending_approval", "approval_id": approval_id}
            return self._record(at, base, "approval_required", "held_for_approval",
                                f"{name} needs {tool['approve_permission']}:{scope} from someone other than the requester",
                                approval_id=approval_id)
        run = self._execute(tool, arguments, key, user, {}, call["id"])
        extra = {"elapsed_ms": run["elapsed_ms"], "attempt_log": run["log"], "result": run["result"]}
        if run["status"] == "timed_out":
            if slot is not None:
                self.keys[slot] = {"digest": base["args_digest"], "state": "in_doubt"}
            return self._record(at, base, "timed_out", "outcome_unknown",
                                f"no reply within {tool['timeout_ms']} ms after {run['attempts']} attempts; "
                                "safe to retry with the same key", attempts=run["attempts"], extra=extra)
        effect_id = run["result"].get("effect_id")
        if slot is not None:
            self.keys[slot] = {"digest": base["args_digest"], "state": "completed", "effect_id": effect_id}
        if resolving:
            reason, detail = "resolved_in_doubt", "the target already held the effect for this key"
        elif run["attempts"] > 1:
            reason, detail = "ok_after_retry", f"succeeded on attempt {run['attempts']} of {tool['max_attempts']}"
        else:
            reason, detail = "ok", ""
        return self._record(at, base, "allowed", reason, detail, effect_id=effect_id,
                            attempts=run["attempts"], extra=extra)

    # --- human approval --------------------------------------------------------
    def _approver_problem(self, approver: str, record: dict, tool: dict):
        """None when `approver` may decide `record`; otherwise (reason, detail). Self-approval is checked first."""
        # GAP 4: refuse self-approval and approvers without the approve grant.
        # Self-approval first: ('self_approval', ...). Then the approver needs
        # f"{tool['approve_permission']}:{record['scope']}": ('approver_lacks_permission', 'missing ...').
        # Return None when the approver may decide.
        raise NotImplementedError("GAP 4: refuse self-approval and approvers without the approve grant")

    def decide_approval(self, action: dict) -> list[dict]:
        """A human decision taken outside the model, in its own authenticated session."""
        at = self._tick()
        approver = self._user(action.get("session"))
        record = self.approvals.get(action["approval_id"])
        base = {"event": "approval", "ref": action["id"], "actor": approver,
                "on_behalf_of": record["requester"] if record else None,
                "tool": record["tool"] if record else None,
                "args_digest": record["args_digest"] if record else None,
                "idempotency_key": record["idempotency_key"] if record else None,
                "influenced_by": record["influenced_by"] if record else []}
        approval_id = action["approval_id"]
        if approver is None:
            return [self._record(at, base, "denied", "unauthenticated", "no valid session", approval_id=approval_id)]
        if record is None:
            return [self._record(at, base, "denied", "unknown_approval", f"no approval {approval_id}")]
        if record["status"] != "pending":
            return [self._record(at, base, "replayed", "already_decided", f"approval is {record['status']}",
                                 approval_id=approval_id, effect_id=record["effect_id"])]
        tool = self.tools[record["tool"]]
        problem = self._approver_problem(approver, record, tool)
        if problem:
            return [self._record(at, base, "denied", problem[0], problem[1], approval_id=approval_id)]
        slot = (record["requester"], record["tool"], record["idempotency_key"])
        record["approver"] = approver
        if action["decision"] == "reject":
            record["status"] = "rejected"
            self.keys[slot] = {"digest": record["args_digest"], "state": "rejected", "approval_id": approval_id}
            return [self._record(at, base, "rejected", "rejected_by_approver", f"rejected by {approver}",
                                 approval_id=approval_id)]
        record["status"] = "approved"
        rows = [self._record(at, base, "approved", "approved_by_approver", f"approved by {approver}",
                             approval_id=approval_id)]
        run = self._execute(tool, record["arguments"], record["idempotency_key"], record["requester"],
                            {"approved_by": approver}, action["id"])
        execution = dict(base, event="execution", actor=self.application["id"])
        extra = {"elapsed_ms": run["elapsed_ms"], "attempt_log": run["log"], "result": run["result"]}
        if run["status"] == "timed_out":
            record["status"] = "in_doubt"
            self.keys[slot] = {"digest": record["args_digest"], "state": "in_doubt", "approval_id": approval_id}
            rows.append(self._record(at, execution, "timed_out", "outcome_unknown",
                                     "approved execution did not reply; safe to retry with the same key",
                                     approval_id=approval_id, attempts=run["attempts"], extra=extra))
            return rows
        record["status"] = "executed"
        record["effect_id"] = run["result"]["effect_id"]
        self.keys[slot] = {"digest": record["args_digest"], "state": "completed",
                           "effect_id": record["effect_id"], "approval_id": approval_id}
        rows.append(self._record(at, execution, "allowed", "executed_after_approval", f"approved by {approver}",
                                 effect_id=record["effect_id"], approval_id=approval_id,
                                 attempts=run["attempts"], extra=extra))
        return rows


def build(fixture_dir) -> tuple[Gate, Downstream, dict]:
    """Load one fixture set and return a fresh gate, its downstream stub and the scripted events."""
    base = Path(fixture_dir)
    identities = load(base / "identities.json")
    entities = load(base / "entities.json")
    tools = load(base / "tools.json")
    documents = load(base / "documents.json")
    index: dict[str, list[str]] = {}
    for doc_id, doc in documents.items():
        index.setdefault(doc["entity"], []).append(doc_id)
    downstream = Downstream({tool["name"]: tool for tool in tools["exposed"]}, index, load(base / "conditions.json"))
    gate = Gate(identities, entities, tools, downstream)
    events = {"calls": load(base / "calls.json"), "approvals": load(base / "approvals.json")}
    return gate, downstream, events


def run(fixture_dir, strip_context: bool = False, gate_factory=None) -> dict:
    """Replay a fixture set: every call in order, then approval actions, then the calls marked `after`."""
    gate, downstream, events = build(fixture_dir) if gate_factory is None else gate_factory(fixture_dir)
    outcomes: dict[str, list[dict]] = {}

    def call(item):
        item = dict(item, context=[]) if strip_context else item
        outcomes[item["id"]] = [gate.handle(item)]

    for item in events["calls"]:
        if not item.get("after_approvals"):
            call(item)
    for action in events["approvals"]:
        outcomes[action["id"]] = gate.decide_approval(action)
    for item in events["calls"]:
        if item.get("after_approvals"):
            call(item)
    return {"gate": gate, "downstream": downstream, "outcomes": outcomes}
