<!-- section:dbxfe-m04-l03-foundation-start -->

[Version-aware updates](#/lesson/dbxfe-versioned-updates) prevents older overwrites. [Record resolution](#/lesson/dbxfe-record-resolution) makes uncertainty and exclusions explicit. A scheduler cannot repair wrong logic in either step. This package uses an in-memory local simulation and sends no real notifications.

<!-- section:dbxfe-m04-l03-foundation-mechanism -->

Our dependency chain is retained_raw → resolved_state → published_snapshot → local_effect. Raw retention preserves what arrived. Resolution produces accepted/rejected/conflicting evidence and a publish decision. Publication associates a named snapshot with rows, totals and coverage. The external-effect boundary models a notification keyed by that snapshot. A successful earlier boundary does not establish a later one.

Before ingesting new evidence, a previous report is labeled stale until the new resolution/publication decision is known. If conflict blocks publication, retain the previous verified snapshot but keep its stale label. If publication succeeds and the local notification step fails, the data snapshot may be current while its notification is pending. Reporting data status and effect status separately avoids turning one failure into an inaccurate description of all state.

Lakeflow Jobs coordinates tasks, dependencies, triggers and monitoring. Spark Declarative Pipelines expresses data transformations/dependencies; Databricks Lakeflow adds a managed platform context beyond the open-source project. Pipeline expectations apply configured row-quality actions such as retain, drop or fail. Cross-record reconciliation, publication coverage and recipient idempotency remain authored responsibilities. None of our local calls is a Jobs run or a cloud pipeline execution.

<!-- section:dbxfe-m04-l03-foundation-example -->

The complete LocalPipeline class appears below with the resolver. This short driver can run from the exercise directory with its supplied files:
~~~python
import json
from solutions.reference import LocalPipeline

with open("fixtures/baseline.json", encoding="utf-8") as handle:
    baseline = json.load(handle)
with open("fixtures/batches.json", encoding="utf-8") as handle:
    correction = json.load(handle)["correction"]
pipeline = LocalPipeline()
pipeline.ingest(baseline)
old_id = pipeline.published["snapshot_id"]
try:
    pipeline.ingest(correction, fail_after="retained_raw")
except RuntimeError:
    pass  # Expected injected failure only, not a general error suppression policy.
assert pipeline.status == "stale_previous"
assert pipeline.published["totals"]["inspected_units"] == 20
pipeline.recover()
assert pipeline.published["totals"]["inspected_units"] == 22
assert pipeline.published["totals"]["defective_units"] == 1
assert pipeline.published["snapshot_id"] != old_id
pipeline.recover()
assert len(pipeline.outbox) == 2  # One local effect per distinct published snapshot.
~~~

The failure occurs after the correction is retained but before resolution. The previous 20/1 snapshot exists, explicitly stale. Recovery recomputes from retained history and publishes A v3 plus C, totaling 22/1. Repeating recovery yields the same business snapshot and does not add a duplicate local effect. Raw delivery count is not the invariant; accepted rows, totals and business snapshot identity are.

<!-- section:dbxfe-m04-l03-foundation-task -->

Start a fresh pipeline with the baseline, then ingest the correction with failure after published_snapshot. Predict the report status, totals and number of local outbox entries immediately after failure and after recover. Then ingest an invalid A v4 with a null required quantity. Predict which existing snapshot may be displayed and its label. Compare recovered business rows to an independently specified clean-run output.

<!-- section:dbxfe-m04-l03-foundation-solution -->

After the publication-boundary failure, the new 22/1 report is current with baseline B excluded, but its notification has not been recorded. The outbox still contains only the baseline snapshot entry. recover recomputes the same 22/1 snapshot and adds its one missing local effect, resulting in two entries. It does not need to count the correction again.

After invalid A v4, A is unresolved; the candidate accepted relation contains C only, but publication is blocked. The prior 22/1 snapshot can remain visible only as stale/previous, with the known unresolved key and exclusion disclosure. It is not a current C-only report. For a clean run compare literal accepted rows A v3 14/1 and C v1 8/0 plus totals 22/1, rather than asking the recovery function to generate its own expected answer.

The hash-derived snapshot ID keys a local dictionary acting as a recipient model. canonical serializes the same business snapshot with a stable key order; encode converts its text to bytes; sha256 computes a digest and hexdigest represents it as text. A digest identifies these modeled payloads, not their business truth. setdefault adds a dictionary entry only if that snapshot key is absent. It does not provide durable delivery or exactly-once behavior to a real service. A production design needs durable state/outbox transitions, recipient idempotency support, acknowledgments and an explicit retry/reconciliation policy. No real notification is sent here.

<!-- section:dbxfe-m04-l03-transfer-task -->

An order can have several lines. The supplied transfer fixture includes O7/L1 revision 1 with quantity 2 at 300 cents each, O7/L2 revision 1 with quantity 1 at 500 cents, O7/L1 revision 2 with quantity 3 at 300 cents, O7/L2 revision 2 explicitly cancelled, and O8/L1 revision 1 with quantity 2 at 200 cents. Test an older late revision and replay after processing these five rows. Use (order_id, line_id) as the business key. Cancellation is an explicit replacement state with operation="cancel" and quantity=0, not disappearance from a batch. Predict the current line states, the active order totals and total revenue in integer cents. Explain why resolving only by order_id loses legitimate lines and why deleting unseen lines is wrong.

<!-- section:dbxfe-m04-l03-transfer-solution -->

O7/L2 remains in current state as a cancelled line; O7/L1 is active at 3 × 300 = 900 cents; O8/L1 is active at 2 × 200 = 400 cents. There are three current lines including one cancellation, two active lines, O7=900 cents, O8=400 cents and total active revenue=1300 cents. Replaying the cancellation leaves those outputs unchanged. An older revision cannot reinstate the cancelled line. Keeping a tombstone preserves the fact that this key was explicitly cancelled.

Resolve by the composite line key, validate and order revisions, detect equal-identity conflicts, then aggregate only current noncancelled lines by order. Integer cents avoid teaching an imprecise floating-point money sum. The model solution in the bundle follows those steps with independent expected results. In its optional source, grouped uses tuple keys to keep order lines distinct; sets identify distinct serialized payloads per revision. After checking that the current set has exactly one value, next(iter(latest)) retrieves that unique value. This use does not choose between conflicting values: those raise an error before retrieval. This task transfers the distinction between source state, business identity and reporting population; it is not just changing inspection column names. The full local transfer source is also included below for workspace-independent reading.

<!-- section:dbxfe-m04-l03-foundation-runbook -->

Preserve the failing input, error and named completed boundary. Identify the last verified snapshot and label whether it is current. Inspect rejects, conflicts and unresolved keys before retry. Recompute/apply using the agreed revision policy. Compare exact rows, quantities and coverage to the expected case. Reconcile any external effect with its own identity and acknowledgment. Record what ran locally and what remains a proposed cloud configuration.

<!-- section:dbxfe-m04-l03-foundation-limits -->

The simulation retains history only for the life of its Python object. It deliberately models boundaries and failure injection, not durable restart after a process crash. Its exercises prove bounded local logic, not cloud availability, permission, performance or an exactly-once service contract. A real operating procedure requires owners and durable evidence. The original recovery/application material is preserved below.

<!-- section:dbxfe-m04-l03-foundation-links -->

[Existing proof-of-value charter](#/lesson/dbxfe-m10-l02) provides a field-practice application. [Migration and reconciliation](#/lesson/dbxfe-m08-l03) offers introductory broader context. This path develops reliable-data foundations; it is neither the complete Databricks curriculum nor official onboarding or an employer readiness score.

<!-- section:dbxfe-m04-l03-pipeline-code -->

Use this class in the same reference.py file as the complete resolver in the record-resolution lesson. Its imports are deepcopy, sha256 and the shared canonical/resolve functions. The downloadable source contains them together. No notification leaves this process.

~~~python
class LocalPipeline:
    """In-memory dependency/failure simulation, not durable orchestration.

    Boundaries: retained_raw -> resolved_state -> published_snapshot -> local_effect.
    A production design needs actual durable transactions/outbox storage and a
    recipient's idempotency agreement. A Python dictionary is not that guarantee.
    """
    def __init__(self):
        self.raw = []
        self.resolved = None
        self.published = None
        self.status = "not_published"
        self.outbox = {}

    def ingest(self, batch, fail_after=None):
        self.raw.extend(deepcopy(batch))
        self.status = "stale_previous" if self.published else "not_published"
        if fail_after == "retained_raw":
            raise RuntimeError("Injected failure after retained_raw")
        return self.recover(fail_after)

    def recover(self, fail_after=None):
        self.resolved = resolve(self.raw)
        if fail_after == "resolved_state":
            raise RuntimeError("Injected failure after resolved_state")
        if not self.resolved["publication_allowed"]:
            self.status = "stale_previous" if self.published else "blocked_no_snapshot"
            return self.resolved
        snapshot = {field: deepcopy(self.resolved[field]) for field in
                    ("accepted", "totals", "excluded_keys", "coverage")}
        snapshot_id = sha256(canonical(snapshot).encode()).hexdigest()
        self.published = {"snapshot_id": snapshot_id, **snapshot}
        self.status = "current_with_exclusions" if snapshot["excluded_keys"] else "current"
        if fail_after == "published_snapshot":
            raise RuntimeError("Injected failure after published_snapshot")
        # setdefault models a receiver keyed by snapshot ID; it sends nothing.
        self.outbox.setdefault(snapshot_id, {"kind": "local_notification", "snapshot_id": snapshot_id})
        return self.resolved
~~~

<!-- section:dbxfe-m04-l03-transfer-code -->

This deliberately different contract uses a composite key, integer cents and explicit cancellation. Current same-revision disagreement raises an error. The small exercise does not assert the full Cinderline immutable-event policy for orders.

~~~python
"""Different contract: composite order-line keys, cents, explicit cancellation."""
import json


def reconcile_orders(events):
    grouped = {}
    for event in events:
        key = (event["order_id"], event["line_id"])
        for field in ("revision", "quantity", "unit_cents"):
            if type(event[field]) is not int or event[field] < (1 if field == "revision" else 0):
                raise ValueError("invalid " + field)
        if event["operation"] not in ("upsert", "cancel"):
            raise ValueError("unknown operation")
        if event["operation"] == "cancel" and event["quantity"] != 0:
            raise ValueError("cancellation must carry zero quantity")
        grouped.setdefault(key, {}).setdefault(event["revision"], set()).add(
            json.dumps(event, sort_keys=True))
    current = []
    for revisions in grouped.values():
        latest = revisions[max(revisions)]
        if len(latest) != 1:
            raise ValueError("ambiguous current line")
        current.append(json.loads(next(iter(latest))))
    totals, cancelled = {}, []
    for row in current:
        if row["operation"] == "cancel":
            cancelled.append([row["order_id"], row["line_id"]])
        else:
            totals[row["order_id"]] = totals.get(row["order_id"], 0) + row["quantity"] * row["unit_cents"]
    return {"order_cents": dict(sorted(totals.items())), "total_cents": sum(totals.values()),
            "current_line_count": len(current), "active_line_count": len(current) - len(cancelled),
            "cancelled_keys": sorted(cancelled)}
~~~

<!-- section:dbxfe-m04-l03-foundation-sources -->

Primary documentation was read on 19 September 2026. Open Sources below for exact publishers, cloud/runtime context and limitations. Official mechanisms, original professional guidance and fictional records are distinct. These examples do not establish a Databricks execution, production performance, configured permissions or complete source coverage. The optional downloadable bundle provides setup, input files, independent expected outputs, starter tasks and complete solutions. The local acceptance run passed 30 tests with no failures or skips using Python 3.12.14, Apache Spark 4.0.4 and Java 17.0.20.1+1, including the complete displayed Python/SQL examples and changed input cases. The bundle includes exact fixture/output hashes and execution evidence. These results do not include Delta or Databricks execution; the reader itself does not execute code.

<!-- section:why -->

A job succeeded yesterday but fails today after writing part of its output. The customer asks whether pressing Retry is safe. Answer by tracing state changes and side effects.

<!-- section:understand -->

An operation is **idempotent** when repeating it has the same intended effect as applying it once. A retry policy says when to try again; it does not make the underlying work idempotent. For each task identify inputs, output state, commit boundary, and effects outside the data transaction.

Orchestration coordinates task dependencies and execution. Lakeflow Jobs supplies jobs, tasks, triggers, and run monitoring. Declarative pipelines describe data transformations and dependencies in SQL or Python. These responsibilities complement each other; neither removes the need for an operating plan.

Quality handling should distinguish valid data, rejected data, and unknown data. Pipeline expectations can evaluate record-level Boolean rules with actions such as retaining, dropping, or failing invalid records. Cinderline still needs a place to inspect quarantined data and a named owner to decide how to correct it. Silently dropping every surprising row makes a clean-looking report at the cost of hidden incompleteness.

<!-- section:see -->

**Fictional failure walkthrough.** Task 1 stores the raw batch; task 2 applies accepted inspection revisions; task 3 publishes a report; task 4 sends a notification. The process fails after task 3 but before the notification acknowledgement.

| Boundary | Question before retry |
|---|---|
| Raw write | Can the same batch ID be recognized? |
| Transformation | Does replay preserve the accepted inspection state? |
| Report publication | Is the published version identifiable? |
| Notification | Can a repeated request send duplicate messages? |

A successful data transaction does not answer the last question. Track the external effect or design a safe repeat policy.

<!-- section:deeper -->

An expectation is not a general cross-table reconciliation engine. Use explicit tests for aggregate counts, totals, referential relationships, and business exceptions that exceed a row-level expression. Define alert thresholds, owner, investigation evidence, replay procedure, and escalation. A recoverability test should introduce a known failure, then compare actual output after retry with the expected state; a green task icon alone is insufficient.

<!-- section:customer -->

For the operating team: “We will test a retry after a partial failure and compare the final data to the expected result. We also need an owner for quarantined records and a safe policy for notifications, because repeating a job must not silently double-count or duplicate external actions.”

<!-- section:try -->

A hypothetical batch has 100 records, of which 4 fail a required quantity rule. The report must disclose incomplete coverage. Choose a handling plan, an owner, and a replay test. Explain why “drop the 4 and mark success” is incomplete.

<!-- section:revisit -->

A defensible plan retains the raw 100, publishes only the 96 valid records if the agreed policy permits it, exposes the 4-record gap, and assigns the quality lead to investigate. If the report requires complete coverage, withhold publication or fail the update under the agreed rule. After correction, replay using stable keys and compare counts and totals to an explicit expected result.

The correct choice depends on the reporting contract. In either case, losing the rejected records or hiding the missing population prevents diagnosis and misleads the reader.
