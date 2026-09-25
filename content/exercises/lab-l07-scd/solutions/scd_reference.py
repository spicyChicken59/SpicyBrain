"""Reference SCD Type 1 and Type 2 transformations over change events, on local Apache Spark 4.0.4.

This is a *reference* implementation of the semantics the source contract in
DATA.md states. It validates every event with reasons, counts an identical
redelivery once, refuses to guess when two different payloads share one
sequence value, refuses to order an event whose sequence value is invalid,
and only then derives the current table (Type 1) and the history table
(Type 2) with Spark window functions, once with the DataFrame API and once
with Spark SQL so the two can be held to the same literals.

It recomputes both tables from every retained event on each call (a full
recompute). A declarative engine such as an AUTO CDC flow on Databricks
maintains SCD targets incrementally under its own documented rules;
SOLUTIONS.md maps the two and labels that mapping as not executed. Nothing
here runs on Databricks, uses Delta Lake or a declarative pipeline, calls a
network service or writes a table: PySpark 4.0.4 has no pipelines module.
"""
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from pyspark.sql import SparkSession, Window, functions as F, types as T

ROOT = Path(__file__).resolve().parents[1]
MAX_INT = 2147483647
SPARK_CONFIG = {
    "spark.ui.enabled": "false",
    "spark.ui.showConsoleProgress": "false",
    "spark.driver.bindAddress": "127.0.0.1",
    "spark.sql.shuffle.partitions": "2",
    "spark.sql.session.timeZone": "UTC",
}


@dataclass(frozen=True)
class Contract:
    """The explicit source contract: which column identifies the entity, which
    columns order its changes (primary first; later columns break ties), and
    which attribute columns an upsert replaces as a whole."""

    key: str
    sequence: tuple
    attributes: dict  # column -> "text" (non-blank string) or "count" (integer 0..MAX_INT)
    label: str


CINDERLINE = Contract("part_id", ("seq",),
                      {"description": "text", "unit_cost_cents": "count", "supplier_code": "text"}, "cinderline")
MARLOW_COMPOSITE = Contract("customer_id", ("seq", "revision_no"), {"tier": "text", "postcode": "text"},
                            "marlow-composite")
MARLOW_SINGLE = Contract("customer_id", ("seq",), {"tier": "text", "postcode": "text"}, "marlow-single")
SUPPLIERS = Contract("supplier_code", ("snapshot_no",), {"name": "text", "lead_days": "count"}, "suppliers")


class ScdContractError(AssertionError):
    """Raised by the invariant checks; `reason` is a stable code the tests assert on."""

    def __init__(self, reason, key=None, row=None):
        super().__init__(f"{reason}: {key} {row}")
        self.reason, self.key, self.row = reason, key, row


def build_session(app_name="SpicyBrain lab L07", local_dir=None):
    """Local Spark on loopback with the UI off; two shuffle partitions is plenty for tens of rows.

    The Python workers must run the driver's interpreter, so PYSPARK_PYTHON is set
    before the session starts. `local_dir` (a temporary directory the caller owns
    and deletes) receives Spark's scratch files and any warehouse directory."""
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    builder = SparkSession.builder.master("local[2]").appName(app_name)
    for key, value in SPARK_CONFIG.items():
        builder = builder.config(key, value)
    if local_dir is not None:
        builder = (builder.config("spark.local.dir", str(Path(local_dir) / "spark-local"))
                   .config("spark.sql.warehouse.dir", str(Path(local_dir) / "warehouse")))
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def load_events(name):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def nonblank(value):
    return isinstance(value, str) and bool(value.strip())


def positive_int(value):
    return type(value) is int and 0 < value <= MAX_INT  # bool is an int subclass: reject True


def count_int(value):
    return type(value) is int and 0 <= value <= MAX_INT


def reasons(event, contract):
    """Every reason, in field order; an event with any reason is quarantined but retained."""
    found = []
    if not nonblank(event.get("event_id")):
        found.append("missing_event_id")
    if not nonblank(event.get(contract.key)):
        found.append(f"missing_{contract.key}")
    if event.get("op") not in ("upsert", "delete"):
        found.append("invalid_op")
    if not all(positive_int(event.get(column)) for column in contract.sequence):
        found.append("invalid_sequence")
    if event.get("op") == "upsert":
        for column, kind in contract.attributes.items():
            value = event.get(column)
            if value is None:
                found.append(f"missing_{column}")
            elif (kind == "text" and not nonblank(value)) or (kind == "count" and not count_int(value)):
                found.append(f"invalid_{column}")
    return found


def payload(event, contract):
    """What a change *says*: the operation and, for an upsert, every attribute. Delivery
    metadata (event id, batch) and the identity/ordering fields are not part of it."""
    if event["op"] == "delete":
        return {"op": "delete"}
    return {"op": "upsert", **{column: event[column] for column in contract.attributes}}


def delivery(event):
    """A delivery is the whole row except the batch it arrived in: a redelivery is identical."""
    return canonical({k: v for k, v in event.items() if k != "batch"})


def resolve(events, contract):
    """Validate, deduplicate and order retained events under the contract.

    Returns a dictionary of evidence: quarantine with reasons, duplicate deliveries,
    redundant evidence, event conflicts, unresolved keys with their reason, excluded
    keys, and the orderable states of the resolved keys. Nothing is guessed: a tie
    the contract cannot break and an event it cannot order both withhold the key.
    """
    quarantine, valid = [], []
    for index, event in enumerate(events):
        found = reasons(event, contract)
        if found:
            quarantine.append([index, found])
        else:
            valid.append((index, event))
    # 1. One event id is one payload. Identical redelivery counts once; a differing payload is a conflict.
    by_event = {}
    for index, event in valid:
        by_event.setdefault(event["event_id"], []).append((index, event))
    duplicates, conflicts, deliveries, conflicted_keys = [], [], [], set()
    for event_id, rows in by_event.items():
        if len({delivery(e) for _, e in rows}) > 1:
            conflicts.append({"event_id": event_id, "raw_indices": [i for i, _ in rows]})
            conflicted_keys.update(e[contract.key] for _, e in rows)
            continue
        if len(rows) > 1:
            duplicates.append({"event_id": event_id, "raw_indices": [i for i, _ in rows]})
        deliveries.append(rows[0])
    # 2. One (key, sequence) is one state. Same payload twice is redundant evidence; different payloads tie.
    groups = {}
    for index, event in deliveries:
        sequence = tuple(event[column] for column in contract.sequence)
        groups.setdefault((event[contract.key], sequence), []).append((index, event))
    states, redundant, unresolved = [], [], {}
    for (key, sequence), rows in sorted(groups.items()):
        distinct = {canonical(payload(e, contract)): payload(e, contract) for _, e in rows}
        if len(distinct) > 1:
            unresolved.setdefault(key, []).append({
                contract.key: key, "reason": "tied_sequence", "sequence": list(sequence),
                "raw_indices": [i for i, _ in rows], "candidates": [distinct[c] for c in sorted(distinct)]})
            continue
        if len(rows) > 1:
            redundant.append({contract.key: key, "sequence": list(sequence),
                              "event_ids": [e["event_id"] for _, e in rows]})
        states.append({contract.key: key, "sequence": list(sequence), **payload(rows[0][1], contract),
                       "event_ids": sorted({e["event_id"] for _, e in rows}), "raw_indices": [i for i, _ in rows]})
    for key in sorted(conflicted_keys):
        unresolved.setdefault(key, []).append({contract.key: key, "reason": "event_conflict",
                                               "raw_indices": [i for c in conflicts for i in c["raw_indices"]
                                                               if events[i][contract.key] == key]})
    # 3. A quarantined event that names a key with valid evidence makes that key unresolved:
    #    the contract cannot say whether the unreadable event was the latest state.
    known = {s[contract.key] for s in states} | set(unresolved)
    quarantined_keys = {}
    for index, found in quarantine:
        key = events[index].get(contract.key)
        if nonblank(key):
            quarantined_keys.setdefault(key, []).append((index, found))
    for key, rows in sorted(quarantined_keys.items()):
        if key in known:
            for index, found in rows:
                unresolved.setdefault(key, []).append({contract.key: key, "reason": found[0], "raw_indices": [index]})
    excluded = sorted(k for k in quarantined_keys if k not in known)
    unresolved_list = [entry for key in sorted(unresolved) for entry in sorted(unresolved[key], key=lambda e: e["reason"])]
    withheld = set(unresolved)
    return {
        "raw_count": len(events),
        # Every arrival counts, quarantined ones included; only an identical redelivery collapses.
        "distinct_deliveries": len({delivery(e) for e in events}),
        "orderable_states": len(states),
        "quarantine": quarantine,
        "duplicate_deliveries": duplicates,
        "redundant_evidence": redundant,
        "event_conflicts": conflicts,
        "unresolved": unresolved_list,
        "excluded": excluded,
        "states": [s for s in states if s[contract.key] not in withheld],
        "withheld_states": [s for s in states if s[contract.key] in withheld],
    }


def _schema(contract):
    fields = [T.StructField(contract.key, T.StringType(), False)]
    fields += [T.StructField(column, T.LongType(), False) for column in contract.sequence]
    fields.append(T.StructField("op", T.StringType(), False))
    for column, kind in contract.attributes.items():
        fields.append(T.StructField(column, T.StringType() if kind == "text" else T.LongType(), True))
    return T.StructType(fields)


def states_frame(spark, resolution, contract):
    """The resolved states as a typed DataFrame: one row per (key, sequence), deletes included."""
    rows = []
    for state in resolution["states"]:
        rows.append((state[contract.key], *state["sequence"], state["op"],
                     *[state.get(column) for column in contract.attributes]))
    return spark.createDataFrame(rows, _schema(contract))


def scd_tables(spark, resolution, contract):
    """Type 1 (current rows) and Type 2 (validity intervals) from the resolved states.

    Type 2: order each key by the sequence columns; `valid_to` is the next state's
    sequence (a delete closes the previous row without opening one); an open row is
    current. Type 1 is derived independently with row_number so the two can be
    cross-checked.
    """
    df = states_frame(spark, resolution, contract)
    sequence = F.struct(*[F.col(column) for column in contract.sequence])
    ascending = Window.partitionBy(contract.key).orderBy(*[F.col(c).asc() for c in contract.sequence])
    descending = Window.partitionBy(contract.key).orderBy(*[F.col(c).desc() for c in contract.sequence])
    history = (df.withColumn("valid_from", sequence)
                 .withColumn("valid_to", F.lead(sequence).over(ascending))
                 .filter(F.col("op") == "upsert")
                 .withColumn("is_current", F.col("valid_to").isNull())
                 .select(contract.key, "valid_from", "valid_to", "is_current", *contract.attributes))
    current = (df.withColumn("rn", F.row_number().over(descending))
                 .filter((F.col("rn") == 1) & (F.col("op") == "upsert"))
                 .withColumn("sequence", sequence)
                 .select(contract.key, "sequence", *contract.attributes))
    return current, history


def scd_tables_sql(spark, resolution, contract, view="lab_l07_states"):
    """The same two tables written in Spark SQL: LEAD for Type 2, ROW_NUMBER for Type 1."""
    states_frame(spark, resolution, contract).createOrReplaceTempView(view)
    key, attributes = contract.key, ", ".join(contract.attributes)
    struct = "named_struct(" + ", ".join(f"'{c}', {c}" for c in contract.sequence) + ")"
    ascending = ", ".join(contract.sequence)
    descending = ", ".join(f"{c} DESC" for c in contract.sequence)
    history = spark.sql(f"""
        SELECT {key}, valid_from, valid_to, valid_to IS NULL AS is_current, {attributes}
        FROM (
          SELECT *, {struct} AS valid_from,
                 LEAD({struct}) OVER (PARTITION BY {key} ORDER BY {ascending}) AS valid_to
          FROM {view}
        ) AS ordered
        WHERE op = 'upsert'""")
    current = spark.sql(f"""
        SELECT {key}, {struct} AS sequence, {attributes}
        FROM (
          SELECT *, ROW_NUMBER() OVER (PARTITION BY {key} ORDER BY {descending}) AS rn
          FROM {view}
        ) AS ranked
        WHERE rn = 1 AND op = 'upsert'""")
    return current, history


def _plain(value):
    if value is None:
        return None
    if hasattr(value, "asDict"):
        return [_plain(v) for v in value]
    return value


def rows(df, contract):
    """Collected rows as plain dictionaries, sequence structs as lists, sorted by key then position."""
    out = [{k: _plain(v) for k, v in r.asDict().items()} for r in df.collect()]
    order = "valid_from" if "valid_from" in df.columns else "sequence"
    return sorted(out, key=lambda r: (r[contract.key], r[order]))


def current_rows(spark, events, contract):
    current, _ = scd_tables(spark, resolve(events, contract), contract)
    return rows(current, contract)


def history_rows(spark, events, contract):
    _, history = scd_tables(spark, resolve(events, contract), contract)
    return rows(history, contract)


def check_current_unique(current, key):
    """Type 1 invariant: one row per key."""
    seen = set()
    for row in current:
        if row[key] in seen:
            raise ScdContractError("duplicate_current_key", row[key], row)
        seen.add(row[key])


def check_intervals(history, key):
    """Type 2 invariants per key: every closed interval ends after it starts, at most one
    open row and it is the last, no overlap. Returns the gaps (a delete leaves one)."""
    gaps, by_key = [], {}
    for row in history:
        by_key.setdefault(row[key], []).append(row)
    for k in sorted(by_key):
        ordered = sorted(by_key[k], key=lambda r: r["valid_from"])
        for row in ordered:
            if row["valid_to"] is not None and row["valid_to"] <= row["valid_from"]:
                raise ScdContractError("interval_order", k, row)
        if sum(1 for r in ordered if r["valid_to"] is None) > 1:
            raise ScdContractError("open_rows_per_key", k)
        for previous, following in zip(ordered, ordered[1:]):
            if previous["valid_to"] is None:
                raise ScdContractError("open_row_not_last", k, previous)
            if following["valid_from"] < previous["valid_to"]:
                raise ScdContractError("overlap", k, following)
            if following["valid_from"] > previous["valid_to"]:
                gaps.append({key: k, "from": previous["valid_to"], "to": following["valid_from"]})
    return gaps


def snapshot_changes(snapshots, contract):
    """Derive a change feed from consecutive full snapshots: a row that appears or differs is an
    upsert at that snapshot's number; a key that disappears is a delete. Unchanged rows emit
    nothing. A change that happens and reverts between two snapshots is invisible."""
    changes, previous = [], {}
    for snapshot in sorted(snapshots, key=lambda s: s["snapshot_no"]):
        number = snapshot["snapshot_no"]
        current = {row[contract.key]: {c: row[c] for c in contract.attributes} for row in snapshot["rows"]}
        for key in sorted(set(previous) | set(current)):
            if key not in current:
                changes.append({"event_id": f"snap-{number}-{key}", "batch": number, contract.key: key,
                                contract.sequence[0]: number, "op": "delete",
                                **{c: None for c in contract.attributes}})
            elif current[key] != previous.get(key):
                changes.append({"event_id": f"snap-{number}-{key}", "batch": number, contract.key: key,
                                contract.sequence[0]: number, "op": "upsert", **current[key]})
        previous = current
    return changes
