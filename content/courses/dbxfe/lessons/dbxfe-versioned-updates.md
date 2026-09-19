<!-- section:dbxfe-versioned-updates-start -->

[Delta snapshots](#/lesson/dbxfe-m03-l02) provides the table boundary. [Record resolution](#/lesson/dbxfe-record-resolution) provides retained evidence, unique current keys and a publication decision. Do not replace that reconciliation with a MERGE statement. The local executable reference uses Python and Spark without Delta; the Delta SQL below is illustrative and unexecuted.

<!-- section:dbxfe-versioned-updates-guard -->

An upsert updates an existing target key or inserts a missing key. It is a mechanism for applying a chosen source relation, not a rule for deciding which conflicting source row is authoritative. Prepare at most one unambiguous row per target business key. Compare source and target revisions: a strictly newer valid replacement may update, an identical equal revision is a no-op, and an older revision must not overwrite newer state. Equal revision with different quantities is a conflict, never a blind overwrite.

Before applying a batch, reconciliation must also consider prior evidence and target state. A late same-event conflict is detectable only if immutable identity evidence has been retained. The tutorial's reference resolves all retained history; the separate target example below deliberately assumes that validation has succeeded. If publication_allowed is false, do not call the target update or publish a new report. A target can contain last verified data while explicitly being stale.

<!-- section:dbxfe-versioned-updates-worked -->

~~~python
from copy import deepcopy

def apply_resolved(target, source):
    next_target = deepcopy(target)
    seen = set()
    for row in source:
        key = row["inspection_id"]
        if key in seen:
            raise ValueError("source must be unique per inspection")
        seen.add(key)
        old = next_target.get(key)
        if old is None or row["version"] > old["version"]:
            next_target[key] = deepcopy(row)
        elif row["version"] == old["version"]:
            if (row["inspected_units"], row["defective_units"]) != (
                    old["inspected_units"], old["defective_units"]):
                raise ValueError("equal-version conflict")
        # An older revision is retained upstream but does not replace target.
    return next_target

target = {"A": {"inspection_id":"A", "version":2,
                 "inspected_units":12, "defective_units":1},
          "C": {"inspection_id":"C", "version":1,
                 "inspected_units":8, "defective_units":0}}
correction = [{"inspection_id":"A", "version":3,
               "inspected_units":14, "defective_units":1}]
updated = apply_resolved(target, correction)
assert updated["A"] == correction[0]
assert updated["C"] == target["C"]
assert apply_resolved(updated, correction) == updated
assert apply_resolved(updated, [target["A"]]) == updated
assert target["A"]["version"] == 2
~~~

Deep-copying produces a candidate instead of partially mutating the caller's target before a later conflict throws. Returning a dictionary is not a durable database transaction. All source rows must already have passed the quantity/identity policy. The complete retained-history resolver from the previous lesson prepares that source and blocks ambiguous publication.

<!-- section:dbxfe-versioned-updates-delta-example -->

Target: a Unity Catalog Delta table on Databricks Runtime 16.4 LTS, with an existing separately validated resolved_source temporary view and an authorized execution identity. This syntax has been reviewed against current MERGE documentation; no Databricks or Delta execution is claimed. Recheck the actual engine/runtime, table features, grants and workspace constraints before an authorized run.

~~~sql
MERGE INTO quality.accepted.inspections AS t
USING resolved_source AS s
ON t.inspection_id = s.inspection_id
WHEN MATCHED AND s.version > t.version THEN UPDATE SET
  t.version = s.version,
  t.inspected_units = s.inspected_units,
  t.defective_units = s.defective_units
WHEN NOT MATCHED THEN INSERT
  (inspection_id, version, inspected_units, defective_units)
VALUES (s.inspection_id, s.version, s.inspected_units, s.defective_units);
~~~

The source must contain one resolved row per inspection. Equal-version conflicts must be checked before this statement; its equal-version no-op alone would hide a contradiction. There is deliberately no WHEN NOT MATCHED BY SOURCE DELETE: an incremental batch listing only A says nothing about deleting C. The source contract here has no deletion operation.

Databricks documentation distinguishes duplicate matching in Runtime 16.0+ from 15.4 LTS and earlier: the newer behavior considers matched-clause conditions as well as ON conditions, while the older behavior considers ON for duplicate matching. Do not depend on that distinction to choose an arbitrary source winner. Resolve ambiguity before MERGE in either case.

<!-- section:dbxfe-versioned-updates-task -->

Starting from A v2 12/1 and C v1 8/0, apply only A v3 14/1, replay it, then receive A v1 10/1. Predict every target and total. Finally introduce A v3 15/1 from a new event and explain why "no update occurred" is not a sufficient success result. State what must happen to the previous published report.

<!-- section:dbxfe-versioned-updates-solution -->

After the correction, target A v3 plus C v1 totals 22/1. Replay leaves those rows/totals unchanged. The older A v1 does not replace v3; C remains because batch absence is not a delete. A second payload for A v3 conflicts with retained evidence, even though the SQL guard would perform no newer-version update. Detect it upstream, preserve both payloads, withhold a new current report and mark the previous snapshot stale. Neither choosing last arrival nor treating a no-op SQL statement as a clean bill of health is acceptable.

<!-- section:dbxfe-versioned-updates-replay-reference -->

Identify immutable inputs and business keys. Verify source ordering and compare payloads for equal identities. Resolve before updating. Guard against older overwrites. Record exact expected rows, types and coverage. Keep raw/rejected evidence separate from published state. Test replay plus one late correction and one cross-batch conflict. Treat any notification as a separate effect with its own idempotency key and acknowledgment policy.

<!-- section:dbxfe-versioned-updates-limits -->

Transactions do not establish source completeness, conflict adjudication or exactly-once notifications. This toy keeps full history in memory and is not a recommended large-scale CDC architecture. The illustrated Delta table name is fictional; no actual permissions, networking or table protocol compatibility have been exercised.

<!-- section:dbxfe-versioned-updates-links -->

[Orchestration, failure and reconciliation](#/lesson/dbxfe-m04-l03) tests the boundary after raw retention and after publication. [Record resolution](#/lesson/dbxfe-record-resolution) remains the canonical source-policy explanation rather than a duplicated rule set.

<!-- section:dbxfe-versioned-updates-foundation-sources -->

Primary documentation was read on 19 September 2026. Open Sources below for exact publishers, cloud/runtime context and limitations. Official mechanisms, original professional guidance and fictional records are distinct. These examples do not establish a Databricks execution, production performance, configured permissions or complete source coverage. The optional downloadable bundle provides setup, input files, independent expected outputs, starter tasks and complete solutions. The local acceptance run passed 30 tests with no failures or skips using Python 3.12.14, Apache Spark 4.0.4 and Java 17.0.20.1+1, including the complete displayed Python/SQL examples and changed input cases. The bundle includes exact fixture/output hashes and execution evidence. These results do not include Delta or Databricks execution; the reader itself does not execute code.

<!-- section:dbxfe-versioned-updates-revisit -->

Try the explained checks, then review the linked cards. A reveal, visit or optional bridge skip does not record a pass or mastery. Mark completion only when you choose; assessment and review evidence remain separate.
