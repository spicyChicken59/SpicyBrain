<!-- section:dbxfe-record-resolution-start -->

[Identity and ordering](#/lesson/dbxfe-m04-l02) defines immutable event payloads, inspection keys and replacement revisions. [DataFrames](#/lesson/dbxfe-dataframes) explains typed row validation. This lesson connects row-level checks with reconciliation across records and batches.

<!-- section:dbxfe-record-resolution-stages -->

Retained raw evidence records what arrived, including repeats and invalid input. Row quarantine carries explicit reasons and input references. Current accepted state contains at most one unambiguous valid replacement per inspection. Publication status says whether those results may be called a current report. These are separate outputs; a clean-looking accepted table does not mean the raw input was fully valid or the report is safe to publish.

First preserve the raw batch. Validate required nonempty IDs, positive integer version and integer nonnegative quantities with defective <= inspected. Record every reason rather than coercing missing units to zero. Check immutable event IDs and key/version payload agreement against the retained history. Only then identify the highest observed ordered revision for each key. Validate that current revision before acceptance: filtering invalid rows before selecting latest would silently resurrect an older valid state.

Two exclusions have different consequences under our explicit policy. B's only known revision is invalid and no valid B has ever been published; the baseline permits an accepted-only report with B disclosed as excluded. But A previously had valid state and now has invalid v3: A's current state is unresolved. Do not publish C-only totals as a new current report. Block publication and label the last verified A/C snapshot stale/previous. Unresolved identity conflicts also block publication, even when found in historical evidence. These conservative choices are original fiction, not required Databricks behavior.

Keep **global provenance conflicts** distinct from **unresolved inspection keys**. A conflicting event ID may have no usable inspection ID: missing, null, empty and whitespace-only inspection IDs are invalid under this contract. The conflict still exists even though there is no real key to put in the unresolved-key list. Never invent a key to fill that gap. Publication requires both no unresolved keys **and** no unresolved conflict evidence; an empty key list alone proves neither trustworthy provenance nor safe publication. A quarantined row without a conflicting identity is a different case, so the baseline's disclosed exclusion of B still applies.

<!-- section:dbxfe-record-resolution-worked -->

For the five-row baseline: raw=5, distinct deliveries=4, quarantined distinct rows=1, structurally valid revision rows=3, accepted current rows=2. The three valid revisions are A v1, A v2 and C v1; only two are current. A v1 is superseded, not rejected. B's negative inspected quantity remains traceable.

| Case added after baseline | Accepted candidate | Unresolved | Publish status |
|---|---|---|---|
| identical replay | A v2, C v1 | none | Current, exclusions disclosed |
| A v3 14/1 | A v3, C v1 | none | Current, totals 22/1 |
| A v3 null/1 | C v1 only | A | Block new report; old snapshot stale |
| A v2 13/1 with new event ID | C v1 only | A | Block: equal-revision conflict |

The internal candidate C-only aggregate is 8/0. It is diagnostic output, not an authorized current metric. Showing it without publication status would mislead the learner. Across repeated ingestion, raw_count can increase while accepted business state, totals and the publication identity stay unchanged.

### A conflict without an identifiable inspection

Two retained rows have event_id="unkeyed", inspection_id=null, version=1 and defective_units=0. One says inspected_units=2; the other says 3. Both are quarantined for missing inspection identity, and the nonempty event ID also has contradictory payloads. Conflicts is nonempty while unresolved inspection keys is empty. On a first run, publication must be blocked: status is blocked_no_snapshot, there is no published report and no simulated notification.

Now start with the verified baseline report of **20 inspected / 1 defective**, ingest the first unkeyed row, then ingest the second together with valid A v3=14/1. The accepted candidate can contain A v3 and C, totaling **22/1**, because neither valid inspection has an attributable conflict. Nevertheless, the retained event contradiction blocks publication globally. Keep the published **20/1** snapshot labeled **stale/previous** and leave its simulated effects unchanged. Neither reversing the two malformed deliveries nor replaying them establishes which payload is trustworthy.

<!-- section:dbxfe-record-resolution-task -->

A flawed resolver does three operations: discard invalid rows; sort by arrival; keep the last row per inspection. Explain its output and failure for A v2=12/1 followed by A v3=null/1, and for two disagreeing A v3 payloads delivered in separate batches. Specify an ordered replacement algorithm and a test whose expected answer is not computed by that algorithm.

Then review a publication gate that checks only whether the unresolved-key list is empty. Apply it to the unkeyed conflict above, first with no previous report and then with the baseline plus A v3 correction. Predict the required publication flag, published snapshot, status and simulated-effect count in both cases. Explain why the candidate's 22/1 total is not permission to publish it.

<!-- section:dbxfe-record-resolution-solution -->

The flawed implementation discards invalid v3 and resurrects v2 as current. It also makes a conflicting revision depend on which batch happened to arrive last. A correct algorithm retains all evidence, validates with reasons, detects event/key-version conflicts over retained history, identifies the greatest observed revision before filtering invalid values, and accepts only unambiguous valid current keys. Publication is blocked when current/provenance uncertainty remains.

For the invalid-latest test, explicitly expect accepted candidate [{inspection_id:C, version:1, inspected_units:8, defective_units:0}], unresolved=[A], publication_allowed=false. Assert the prior published 20/1 snapshot is marked stale, not current. For the cross-batch conflict, expect both payloads to remain in raw, a key_version conflict for A, unresolved A and no new report. Reversing the arrival order must not change those business outcomes. A rejected row's location may differ; that operational detail is not claimed invariant.

For the unkeyed first run, expect nonempty conflict evidence, an empty unresolved-key list, publication_allowed=false, status=blocked_no_snapshot, published=None and zero simulated effects. For the baseline/correction run, expect the diagnostic accepted candidate A v3 plus C and totals 22/1, but publication_allowed=false, status=stale_previous, the exact prior published 20/1 snapshot and the same one-entry outbox. The gate must inspect conflicts as well as unresolved keys. Retain both malformed payloads and their reasons; filtering them away, inventing an inspection ID, or choosing a delivery by arrival would hide the provenance problem rather than resolve it.

The complete reference implementation is included in the source-resolution section below and in the download. It uses dictionaries to group evidence, canonical JSON to compare payload values, and sets to collect blocked keys. setdefault creates a group if absent; sorted stabilizes diagnostic output; deepcopy prevents later caller mutation from altering retained evidence. The code recomputes all retained history, intentionally favoring inspectability over streaming scalability.

In the optional source, a list comprehension such as [row for row in rows if condition] builds a list by looping and filtering; a dictionary comprehension builds key/value entries similarly. A tuple (key, revision) is an immutable compound dictionary key. A set stores unique values; add inserts one and update adds several. sorted returns a new ordered list without changing the input. max selects the greatest numeric revision within one key. The expression [0] selects the first element only after the code has proved the surviving equal-revision payloads agree; it is not the conflict-resolution rule.

<!-- section:dbxfe-record-resolution-limits -->

An expectation such as "inspected_units >= 0" can evaluate a row and retain/drop/fail it according to configuration. It does not itself establish immutable event identity or reconcile cross-batch revisions. Aggregate coverage checks and conflict adjudication need additional logic. A zero-error task is not proof that all source records arrived, and an accepted-only metric must disclose exclusions.

<!-- section:dbxfe-record-resolution-links -->

[Version-aware updates](#/lesson/dbxfe-versioned-updates) consumes resolved source state. [Orchestration and recovery](#/lesson/dbxfe-m04-l03) carries publication status across failures. Sources support product quality-rule behavior and language mechanics; the actual resolution policy is authored fiction.

<!-- section:dbxfe-record-resolution-reference-code -->

This is the complete imported reference source, not pseudocode. It uses a stricter signed 32-bit nonnegative integer quantity policy than the introductory LongType expression demo. It preserves raw payloads and reasons. The download adds independent fixtures/tests; this code does not execute inside the reader.

~~~python
"""Original fictional teaching policy, deliberately recomputing retained history.

This is neither a streaming engine nor a database CDC connector. No network
calls, real notifications, Delta commands, or Databricks services are used.
"""
from copy import deepcopy
from hashlib import sha256
import csv
import json

FIELDS = ("event_id", "inspection_id", "version", "inspected_units", "defective_units")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def positive_int(value):
    # bool is a Python int subclass: reject True instead of treating it as v1.
    return type(value) is int and 0 < value <= 2147483647


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def reasons(row):
    errors = []
    for key in ("event_id", "inspection_id"):
        if not nonempty(row.get(key)):
            errors.append("missing_" + key)
    if not positive_int(row.get("version")):
        errors.append("invalid_version")
    for key in ("inspected_units", "defective_units"):
        value = row.get(key)
        if value is None:
            errors.append("missing_" + key)
        elif type(value) is not int or not 0 <= value <= 2147483647:
            errors.append("invalid_" + key)
    inspected, defective = row.get("inspected_units"), row.get("defective_units")
    if type(inspected) is int and type(defective) is int and defective > inspected:
        errors.append("defective_exceeds_inspected")
    return errors


def resolve(history):
    """Return evidence, row-quality failures, reconciled state, and coverage.

    Revision numbers order one inspection, not different inspections. Delivery
    IDs identify immutable payloads; arrival position is never the tie-breaker.
    Exact repeats are audit evidence, not another business inspection.
    """
    rows = [deepcopy(row) for row in history]
    by_event, by_revision, by_key = {}, {}, {}
    quarantine = []
    for index, row in enumerate(rows):
        errors = reasons(row)
        if errors:
            quarantine.append({"raw_index": index, "row": row, "reasons": errors})
        event, key, revision = row.get("event_id"), row.get("inspection_id"), row.get("version")
        payload = {field: row.get(field) for field in FIELDS}
        if nonempty(event):
            by_event.setdefault(event, {}).setdefault(canonical(payload), []).append(index)
        if nonempty(key):
            by_key.setdefault(key, []).append((index, row, errors))
            if positive_int(revision):
                quantities = {field: row.get(field) for field in ("inspected_units", "defective_units")}
                by_revision.setdefault((key, revision), {}).setdefault(canonical(quantities), []).append(index)

    conflicts, blocked = [], set()
    for event, payloads in sorted(by_event.items()):
        if len(payloads) > 1:
            indices = sorted(index for group in payloads.values() for index in group)
            conflicts.append({"kind": "event_id", "identity": event, "raw_indices": indices})
            blocked.update(rows[index]["inspection_id"] for index in indices
                           if nonempty(rows[index].get("inspection_id")))
    for (key, revision), payloads in sorted(by_revision.items()):
        if len(payloads) > 1:
            conflicts.append({"kind": "key_version", "identity": [key, revision],
                              "raw_indices": sorted(index for group in payloads.values() for index in group)})
            blocked.add(key)

    accepted, excluded = [], []
    for key, evidence in sorted(by_key.items()):
        valid = [row for _, row, errors in evidence if not errors]
        ordered = [row for _, row, _ in evidence if positive_int(row.get("version"))]
        if not valid:
            # Baseline B never had any valid state. Its exclusion is disclosed.
            if key not in blocked:
                excluded.append(key)
            continue
        if any(not positive_int(row.get("version")) for _, row, _ in evidence):
            blocked.add(key)  # Cannot prove the current version of a known key.
        highest = max(row["version"] for row in ordered)
        latest = [(row, errors) for _, row, errors in evidence if row.get("version") == highest]
        if any(errors for _, errors in latest):
            blocked.add(key)  # Do not filter out invalid v3 then resurrect v2.
        if key in blocked:
            continue
        # Uniqueness was proved above. All remaining equal-version quantities agree.
        selected = latest[0][0]
        accepted.append({field: selected[field] for field in FIELDS[1:]})

    total = sum(row["inspected_units"] for row in accepted)
    defective = sum(row["defective_units"] for row in accepted)
    return {
        "raw_count": len(rows), "raw": rows, "accepted": accepted,
        "quarantine": quarantine, "conflicts": conflicts, "excluded_keys": excluded,
        # Provenance can conflict even when no usable inspection key is known.
        "unresolved": sorted(blocked), "publication_allowed": not conflicts and not blocked,
        "totals": {"inspected_units": total, "defective_units": defective,
                   "defect_rate": defective / total if total else None},
        "coverage": "Accepted inspections only; quarantined/excluded inputs are not complete source coverage.",
    }


def guarded_upsert(target, source):
    """Local target-update model after source resolution, not SQL MERGE execution.

    Input rows have business fields only, one row per inspection. Unknown
    absence is not deletion. Validate ambiguity before touching the target.
    A caller must separately enforce the resolver's publication_allowed gate.
    """
    state = {row["inspection_id"]: deepcopy(row) for row in target}
    if len(state) != len(target):
        raise ValueError("target is not unique at inspection grain")
    keys = [row["inspection_id"] for row in source]
    if len(set(keys)) != len(keys):
        raise ValueError("ambiguous source matches; resolve before update")
    for incoming in source:
        key = incoming["inspection_id"]
        current = state.get(key)
        if current is None or incoming["version"] > current["version"]:
            state[key] = deepcopy(incoming)
        elif incoming["version"] == current["version"] and incoming != current:
            raise ValueError("equal version disagrees with target")
        # Equal-and-identical or older source is a no-op, not an increment.
    return [state[key] for key in sorted(state)]


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


def parse_bridge(path):
    """CSV text is parsed explicitly; no truthiness shortcut turns missing into zero."""
    accepted, rejected = [], []
    with open(path, encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            text = row.get("units")
            try:
                if text is None or text.strip() == "":
                    raise ValueError("missing units")
                try:
                    units = int(text)
                except ValueError:
                    raise ValueError("malformed integer") from None
                if units < 0:
                    raise ValueError("negative units")
                accepted.append({"record_id": row["record_id"], "units": units})
            except ValueError as error:
                rejected.append({"record_id": row["record_id"], "reason": str(error)})
    return {"accepted": accepted, "rejected": rejected}
~~~

<!-- section:dbxfe-record-resolution-spark-code -->

The functions below consume typed synthetic input using the shown IntegerType schema; raw JSON validation precedes that boundary. SQL and PySpark both preserve intermediate reasoning and compute current revision before removing invalid current rows. Expected baseline intermediates are 5 raw, 4 distinct, 1 invalid, 3 valid revisions and 2 accepted current rows.

Both interfaces expose event-conflict and revision-conflict evidence, unresolved keys, and a one-row publication decision with their counts. That decision checks global conflicts even when no usable inspection key can be associated with them. Missing/null/blank inspection IDs do not form revision-conflict identities or unresolved-key entries, while their conflicting nonempty event ID remains evidence. A consumer must inspect the publication decision; counting zero rows in unresolved is insufficient. These Spark outputs are transformations and diagnostics, not published reports. The separate Python LocalPipeline consumes its resolver's gate and models retaining the last verified snapshot and local effects.

In the optional code, nonempty_sql builds the shared SQL predicate used by both interfaces. Its RLIKE pattern asks whether a string contains a non-whitespace character, including the whitespace cases recognized by the Python reference; a spaces-only trim would miss tabs and some other blank inputs. This validates identity without replacing it. Each aggregate count yields one row. crossJoin combines those one-row counts into one decision row, and publication_allowed is true only when event_conflict_count, revision_conflict_count and unresolved_key_count are all zero. Candidate totals remain a separate relation.

~~~python
"""Complete local Spark 4.0.4 transformations. No Delta dependency or cloud use.

This layer accepts explicitly typed source rows. reference.py validates raw
JSON types before this boundary; try_cast is taught separately in the runner.
"""
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

SCHEMA = StructType([
    StructField("event_id", StringType(), True),
    StructField("inspection_id", StringType(), True),
    StructField("version", IntegerType(), True),
    StructField("inspected_units", IntegerType(), True),
    StructField("defective_units", IntegerType(), True),
])
BUSINESS = ["inspection_id", "version", "inspected_units", "defective_units"]


def nonempty_sql(column):
    # Match Python str.strip's blank-key policy, including tabs and Unicode
    # whitespace. SQL's ordinary trim removes spaces only. This is authored policy.
    return f"{column} IS NOT NULL AND {column} RLIKE r'(?U)[^\\s\\x1c-\\x1f]'"


VALID_SQL = f"""({nonempty_sql('event_id')})
 AND ({nonempty_sql('inspection_id')})
 AND version IS NOT NULL AND version > 0
 AND inspected_units IS NOT NULL AND inspected_units >= 0
 AND defective_units IS NOT NULL AND defective_units >= 0
 AND defective_units <= inspected_units"""


def pyspark_transform(raw):
    # 1. Remove identical deliveries only; never pick arbitrary conflicting rows.
    distinct = raw.distinct()
    # 2. A predicate is a Column expression evaluated by Spark, not a Python bool.
    checked = distinct.withColumn("valid", F.coalesce(F.expr(VALID_SQL), F.lit(False)))
    quarantine = checked.filter(~F.col("valid"))
    valid = checked.filter(F.col("valid"))
    # 3. Detect conflicting identities before selecting the latest version.
    event_conflicts = (distinct.groupBy("event_id")
                       .agg(F.countDistinct(F.struct(*BUSINESS)).alias("payloads"))
                       .filter(f"({nonempty_sql('event_id')}) AND payloads > 1"))
    revision_conflicts = (distinct.filter(f"version > 0 AND ({nonempty_sql('inspection_id')})")
                          .groupBy("inspection_id", "version")
                          .agg(F.countDistinct(F.struct("inspected_units", "defective_units")).alias("payloads"))
                          .filter("payloads > 1"))
    event_keys = distinct.join(event_conflicts, "event_id").select("inspection_id")
    # 4. Latest is computed before filtering invalid quantities: no resurrection.
    latest = (distinct.filter("version > 0").groupBy("inspection_id")
              .agg(F.max("version").alias("version")))
    current = checked.join(latest, ["inspection_id", "version"])
    known_valid = valid.select("inspection_id").distinct()
    invalid_current = current.filter(~F.col("valid")).select("inspection_id").join(known_valid, "inspection_id")
    unordered_known = (distinct.filter("version IS NULL OR version <= 0")
                       .select("inspection_id").join(known_valid, "inspection_id"))
    unresolved = (event_keys.union(revision_conflicts.select("inspection_id")).union(invalid_current).union(unordered_known)
                  .filter(nonempty_sql("inspection_id")).distinct())
    # 5. Reject ambiguity, then project one canonical current inspection row.
    accepted = (current.filter(F.col("valid")).join(unresolved, "inspection_id", "left_anti")
                .select(*BUSINESS).distinct())
    # 6. Weighted ratio: total defective / total inspected, never mean(row ratios).
    totals = (accepted.agg(F.sum("inspected_units").alias("inspected_units"),
                          F.sum("defective_units").alias("defective_units"))
              .withColumn("defect_rate", F.when(F.col("inspected_units") > 0,
                         F.col("defective_units").cast("double") / F.col("inspected_units"))))
    # Expose a decision relation separately from candidate rows. Empty unresolved
    # keys do not clear global provenance conflicts. This does not publish a report.
    publication = (event_conflicts.agg(F.count("*").alias("event_conflict_count"))
                   .crossJoin(revision_conflicts.agg(F.count("*").alias("revision_conflict_count")))
                   .crossJoin(unresolved.agg(F.count("*").alias("unresolved_key_count")))
                   .withColumn("publication_allowed", (F.col("event_conflict_count") == 0)
                               & (F.col("revision_conflict_count") == 0) & (F.col("unresolved_key_count") == 0)))
    return {"distinct": distinct, "quarantine": quarantine, "valid": valid,
            "accepted": accepted, "unresolved": unresolved, "totals": totals,
            "event_conflicts": event_conflicts, "revision_conflicts": revision_conflicts,
            "publication": publication}


SQL_STAGES = f"""
WITH distinct_input AS (SELECT DISTINCT * FROM raw_inspections),
checked AS (SELECT *, coalesce(({VALID_SQL}), false) AS valid FROM distinct_input),
valid_keys AS (SELECT DISTINCT inspection_id FROM checked WHERE valid),
event_conflicts AS (
 SELECT event_id, count(DISTINCT struct(inspection_id, version, inspected_units, defective_units)) AS payloads
 FROM distinct_input WHERE {nonempty_sql('event_id')} GROUP BY event_id
 HAVING count(DISTINCT struct(inspection_id, version, inspected_units, defective_units)) > 1),
revision_conflicts AS (
 SELECT inspection_id, version, count(DISTINCT struct(inspected_units, defective_units)) AS payloads
 FROM distinct_input WHERE version > 0 AND ({nonempty_sql('inspection_id')}) GROUP BY inspection_id, version
 HAVING count(DISTINCT struct(inspected_units, defective_units)) > 1),
latest AS (SELECT inspection_id, max(version) AS version FROM distinct_input
 WHERE version > 0 GROUP BY inspection_id),
current_rows AS (SELECT c.* FROM checked c JOIN latest l
 ON c.inspection_id = l.inspection_id AND c.version = l.version),
unresolved_evidence AS (
 SELECT d.inspection_id FROM distinct_input d JOIN event_conflicts e USING (event_id)
 UNION SELECT inspection_id FROM revision_conflicts
 UNION SELECT c.inspection_id FROM current_rows c JOIN valid_keys v USING (inspection_id) WHERE NOT c.valid
 UNION SELECT d.inspection_id FROM distinct_input d JOIN valid_keys v USING (inspection_id)
 WHERE d.version IS NULL OR d.version <= 0),
unresolved AS (SELECT DISTINCT inspection_id FROM unresolved_evidence WHERE {nonempty_sql('inspection_id')}),
accepted AS (
 SELECT DISTINCT c.inspection_id, c.version, c.inspected_units, c.defective_units
 FROM current_rows c LEFT ANTI JOIN unresolved u ON c.inspection_id = u.inspection_id
 WHERE c.valid)
"""


def sql_transform(raw, spark):
    raw.createOrReplaceTempView("raw_inspections")
    accepted = spark.sql(SQL_STAGES + "SELECT * FROM accepted")
    totals = spark.sql(SQL_STAGES + """
      SELECT sum(inspected_units) AS inspected_units,
             sum(defective_units) AS defective_units,
             CASE WHEN sum(inspected_units) > 0
                  THEN CAST(sum(defective_units) AS DOUBLE) / sum(inspected_units)
             END AS defect_rate FROM accepted""")
    publication = spark.sql(SQL_STAGES + """,
      decision_counts AS (
        SELECT (SELECT count(*) FROM event_conflicts) AS event_conflict_count,
               (SELECT count(*) FROM revision_conflicts) AS revision_conflict_count,
               (SELECT count(*) FROM unresolved) AS unresolved_key_count)
      SELECT *, event_conflict_count = 0 AND revision_conflict_count = 0
                AND unresolved_key_count = 0 AS publication_allowed FROM decision_counts""")
    return {"accepted": accepted, "totals": totals,
            "unresolved": spark.sql(SQL_STAGES + "SELECT * FROM unresolved"),
            "event_conflicts": spark.sql(SQL_STAGES + "SELECT * FROM event_conflicts"),
            "revision_conflicts": spark.sql(SQL_STAGES + "SELECT * FROM revision_conflicts"),
            "publication": publication}


def join_experiment(spark, accepted):
    # Cinderline tags are one-to-many. Two tags for A multiply A's 12/1 facts.
    tags = spark.createDataFrame([("A", "urgent"), ("A", "sampled"), ("C", "routine")],
                                 "inspection_id string, tag string")
    flawed = accepted.join(tags, "inspection_id")
    # A semijoin means 'inspection has any tag', preserving inspection grain.
    corrected = accepted.join(tags.select("inspection_id").distinct(), "inspection_id", "left_semi")
    return flawed, corrected
~~~

<!-- section:dbxfe-record-resolution-foundation-sources -->

Primary documentation was read on 19 September 2026. Open Sources below for exact publishers, cloud/runtime context and limitations. Official mechanisms, original professional guidance and fictional records are distinct. These examples do not establish a Databricks execution, production performance, configured permissions or complete source coverage. The optional downloadable bundle provides setup, input files, independent expected outputs, starter tasks and complete solutions. Its execution.json records the actual local run, pinned versions and fixture/program hashes. The initial milestone's 30-test run did not cover the unkeyed-conflict regressions added in this material correction. This fix enforces the existing original exercise policy; it is not a newly verified Databricks requirement. No Delta or Databricks execution is claimed, and the reader itself does not execute code.

<!-- section:dbxfe-record-resolution-revisit -->

Try the explained checks, then review the linked cards. A reveal, visit or optional bridge skip does not record a pass or mastery. Mark completion only when you choose; assessment and review evidence remain separate.
