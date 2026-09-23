"""Lab L24 reference solution: a tested target transformation and its reconciliation.

Runs on local Apache Spark 4.0.4 (PySpark) on one machine. The legacy T-SQL
procedure and the SSIS-style package outline in ``legacy/`` are read as text
only: no SQL Server, SSIS or SQL Server Agent is installed, started or
contacted. Target tables are in-memory lists of rows standing in for platform
tables; nothing is written to Delta, a metastore or a workspace.

Five semantic choices decide whether a translation behaves like the legacy
procedure. ``TARGET`` makes each choice the way the legacy code behaves;
``NAIVE`` is the line-by-line translation that compiles, runs and differs.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

ROOT = Path(__file__).resolve().parent.parent
SESSION_TIME_ZONE = "UTC"  # the platform-side default this lab assumes; set explicitly
UNASSIGNED = "UNASSIGNED"


def fixture(name: str):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


CONTEXT = fixture("run_context.json")
SERVER_TIME_ZONE = CONTEXT["server_time_zone"]
CUTOFF_HOURS = CONTEXT["business_day_cutoff_hours"]


@dataclass(frozen=True)
class Rules:
    """One semantic decision per field; the defaults reproduce the legacy procedure."""

    key_rule: str = "collation"  # collation (upper + rtrim) | binary | trim
    join_rule: str = "on"  # plant predicate in ON | moved to WHERE
    day_rule: str = "server_local"  # server_local | session | plant_local
    division: str = "integer"  # integer (T-SQL INT / INT) | fractional
    amount_type: str = "decimal"  # decimal(12,2) | double


TARGET = Rules()
NAIVE = Rules(key_rule="binary", join_rule="where", day_rule="session", division="fractional", amount_type="double")
FLIPS = {
    "binary_keys": replace(TARGET, key_rule="binary"),
    "where_filter": replace(TARGET, join_rule="where"),
    "session_day": replace(TARGET, day_rule="session"),
    "fractional_division": replace(TARGET, division="fractional"),
    "double_amounts": replace(TARGET, amount_type="double"),
}

DETAIL_COLUMNS = [
    "inspection_id",
    "plant_code",
    "business_day",
    "shift_code",
    "inspector_code",
    "units_inspected",
    "units_defective",
    "rework_cost",
]
REPORT_COLUMNS = [
    "plant_code",
    "business_day",
    "shift_code",
    "inspections",
    "units_inspected",
    "units_defective",
    "rework_cost",
    "defect_pct",
]
DETAIL_FIELDS = ["business_day", "shift_code", "inspector_code", "units_inspected", "units_defective", "rework_cost"]
REPORT_FIELDS = ["inspections", "units_inspected", "units_defective", "rework_cost", "defect_pct"]
TOTAL_FIELDS = ["units_inspected", "units_defective", "rework_cost"]
NUMERIC = {"inspection_id", "units_inspected", "units_defective", "rework_cost", "inspections", "defect_pct"}
# Types the legacy tables declare, as families the target must stay inside.
DECLARED = {
    "detail.inspection_id": "integral",
    "detail.plant_code": "string",
    "detail.business_day": "date",
    "detail.shift_code": "string",
    "detail.inspector_code": "string",
    "detail.units_inspected": "integral",
    "detail.units_defective": "integral",
    "detail.rework_cost": "decimal(*,2)",
    "report.plant_code": "string",
    "report.business_day": "date",
    "report.shift_code": "string",
    "report.inspections": "integral",
    "report.units_inspected": "integral",
    "report.units_defective": "integral",
    "report.rework_cost": "decimal(*,2)",
    "report.defect_pct": "integral",
}
INSPECTION_DDL = (
    "inspection_id INT, plant_code STRING, lot_id STRING, inspector_code STRING, inspected_at STRING, "
    "units_inspected INT, units_defective INT, rework_cost STRING, updated_at STRING"
)
INSPECTION_FIELDS = [part.split()[0] for part in INSPECTION_DDL.split(", ")]


class InjectedFailure(RuntimeError):
    """Raised on purpose between two writes to test the retry path."""


# ---------------------------------------------------------------- session


def build_session(time_zone: str = SESSION_TIME_ZONE) -> SparkSession:
    """A small local session: two threads, no web UI, two shuffle partitions."""
    os.environ["PYSPARK_PYTHON"] = sys.executable
    scratch = tempfile.mkdtemp(prefix="lab-l24-")
    spark = (
        SparkSession.builder.master("local[2]")
        .appName("lab-l24-migration-reconciliation")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.sql.session.timeZone", time_zone)
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.local.dir", scratch)
        .config("spark.sql.warehouse.dir", str(Path(scratch) / "warehouse"))
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    spark.conf.set("lab.scratch", scratch)
    return spark


def stop_session(spark: SparkSession) -> None:
    scratch = spark.conf.get("lab.scratch", None)
    spark.stop()
    if scratch:
        shutil.rmtree(scratch, ignore_errors=True)


# ---------------------------------------------------------------- canonical values


def canon(value):
    """One string form per value so that both paths are compared on equal terms."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="milliseconds")
    if isinstance(value, date):
        return value.isoformat()
    return value


def canon_row(row: dict) -> dict:
    return {key: canon(value) for key, value in row.items()}


def same(field: str, old, new) -> bool:
    if old is None or new is None:
        return old is None and new is None  # the stated null rule: NULL equals NULL
    if field in NUMERIC:
        return Decimal(old) == Decimal(new)
    return old == new


def detail_key(row):
    return int(row["inspection_id"])


def report_key(row):
    return (row["plant_code"], row["business_day"], row["shift_code"])


def rows_of(df: DataFrame, columns, key) -> list[dict]:
    return sorted((canon_row(r.asDict()) for r in df.select(*columns).collect()), key=key)


def types_of(df: DataFrame, table: str) -> dict:
    return {f"{table}.{f.name}": f.dataType.simpleString() for f in df.schema.fields}


# ---------------------------------------------------------------- target transformation


def source_frame(spark: SparkSession, rows: list[dict]) -> DataFrame:
    return spark.createDataFrame([tuple(r[c] for c in INSPECTION_FIELDS) for r in rows], INSPECTION_DDL)


def inspectors_frame(spark: SparkSession) -> DataFrame:
    rows = fixture("inspectors.json")
    return spark.createDataFrame(
        [(r["plant_code"], r["inspector_code"], r["shift_code"]) for r in rows],
        "plant_code STRING, inspector_code STRING, shift_code STRING",
    )


def plant_zone(plant_code: str) -> str:
    return next(p["plant_time_zone"] for p in fixture("plants.json") if p["plant_code"] == plant_code)


def land(raw: DataFrame, rules: Rules = TARGET) -> DataFrame:
    """Type the exported text explicitly: DATETIME text as TIMESTAMP_NTZ, money as DECIMAL(12,2)."""
    amount = "decimal(12,2)" if rules.amount_type == "decimal" else "double"
    return raw.select(
        "inspection_id",
        "plant_code",
        "lot_id",
        "inspector_code",
        "inspected_at",
        F.col("inspected_at").cast("timestamp_ntz").alias("inspected_local"),
        F.col("updated_at").cast("timestamp_ntz").alias("updated_local"),
        "units_inspected",
        "units_defective",
        F.col("rework_cost").cast(amount).alias("rework_cost"),
    )


def business_day(rules: Rules, plant_code: str):
    """CAST(DATEADD(HOUR, -6, inspected_at) AS DATE), made explicit about its clock."""
    back = F.expr(f"INTERVAL {CUTOFF_HOURS} HOURS")
    local = F.col("inspected_local")
    if rules.day_rule == "server_local":  # wall-clock arithmetic on the server's local time
        return F.to_date(local - back)
    if rules.day_rule == "plant_local":  # the intended rule: 06:00 in the plant's own zone
        return F.to_date(F.convert_timezone(F.lit(SERVER_TIME_ZONE), F.lit(plant_zone(plant_code)), local) - back)
    if rules.day_rule == "session":  # an instant, rendered in whatever the session zone is
        instant = F.to_timestamp(
            F.concat(F.col("inspected_at"), F.lit(" " + SERVER_TIME_ZONE)), "yyyy-MM-dd HH:mm:ss.SSS VV"
        )
        return F.to_date(instant - back)
    raise ValueError(rules.day_rule)


def normalize(column, key_rule: str):
    if key_rule == "collation":  # case-insensitive, trailing spaces ignored, leading spaces kept
        return F.upper(F.rtrim(column))
    if key_rule == "trim":
        return F.upper(F.trim(column))
    if key_rule == "binary":
        return column
    raise ValueError(key_rule)


def assign_shift(rows: DataFrame, inspectors: DataFrame, plant_code: str, rules: Rules) -> DataFrame:
    i, s = rows.alias("i"), inspectors.alias("s")
    same_code = normalize(F.col("i.inspector_code"), rules.key_rule) == normalize(F.col("s.inspector_code"), rules.key_rule)
    same_plant = F.col("s.plant_code") == F.lit(plant_code)
    if rules.join_rule == "on":
        joined = i.join(s, same_code & same_plant, "left")
    elif rules.join_rule == "where":
        joined = i.join(s, same_code, "left").where(same_plant)  # NULL = 'P1' is not true: unmatched rows vanish
    else:
        raise ValueError(rules.join_rule)
    return joined.select("i.*", F.coalesce(F.col("s.shift_code"), F.lit(UNASSIGNED)).alias("shift_code"))


def aggregate(detail: DataFrame, rules: Rules) -> DataFrame:
    grouped = detail.groupBy("plant_code", "business_day", "shift_code").agg(
        F.count(F.lit(1)).alias("inspections"),
        F.sum("units_inspected").alias("units_inspected"),
        F.sum("units_defective").alias("units_defective"),
        F.sum("rework_cost").alias("rework_cost"),
    )
    if rules.division == "integer":
        pct = F.expr("(units_defective * 100) div units_inspected")  # T-SQL INT / INT truncates
    elif rules.division == "fractional":
        pct = F.col("units_defective") * 100 / F.col("units_inspected")  # Spark '/' is fractional
    else:
        raise ValueError(rules.division)
    return grouped.withColumn("defect_pct", pct).select(*REPORT_COLUMNS)


def build(spark: SparkSession, source_rows, plant_code: str, rules: Rules = TARGET, as_of: str | None = None, days=None):
    """The decomposed procedure: land, select the basis, derive the day, assign the shift, aggregate."""
    silver = land(source_frame(spark, source_rows), rules).where(F.col("plant_code") == plant_code)
    if as_of is not None:
        silver = silver.where(F.col("updated_local") <= F.lit(as_of).cast("timestamp_ntz"))
    silver = silver.withColumn("business_day", business_day(rules, plant_code))
    if days is not None:
        silver = silver.where(F.col("business_day").isin([date.fromisoformat(d) for d in days]))
    detail = assign_shift(silver, inspectors_frame(spark), plant_code, rules).select(*DETAIL_COLUMNS)
    return detail, aggregate(detail, rules)


def outputs(spark, source_rows, plant_code, rules=TARGET, as_of=None) -> dict:
    detail, report = build(spark, source_rows, plant_code, rules, as_of)
    return {
        "detail": rows_of(detail, DETAIL_COLUMNS, detail_key),
        "report": rows_of(report, REPORT_COLUMNS, report_key),
        "types": {**types_of(detail, "detail"), **types_of(report, "report")},
    }


def legacy_outputs(detail_fixture: str, report_fixture: str) -> dict:
    return {
        "detail": sorted((canon_row(r) for r in fixture(detail_fixture)), key=detail_key),
        "report": sorted((canon_row(r) for r in fixture(report_fixture)), key=report_key),
        "types": None,  # the legacy side declares its types; see DECLARED
    }


# ---------------------------------------------------------------- reconciliation


def type_ok(expected: str, actual: str) -> bool:
    if expected == "integral":
        return actual in {"tinyint", "smallint", "int", "bigint"}
    if expected == "decimal(*,2)":
        return re.fullmatch(r"decimal\(\d+,2\)", actual) is not None
    return actual == expected


def keyed(old_rows, new_rows, key, fields):
    old = {key(r): r for r in old_rows}
    new = {key(r): r for r in new_rows}
    only_old = sorted(k for k in old if k not in new)
    only_new = sorted(k for k in new if k not in old)
    changed = []
    for k in sorted(k for k in old if k in new):
        for f in fields:
            if not same(f, old[k][f], new[k][f]):
                changed.append([k, f, old[k][f], new[k][f]])
    return only_old, only_new, changed


def day_totals(report_rows) -> dict:
    totals: dict = {}
    for r in report_rows:
        bucket = totals.setdefault((r["plant_code"], r["business_day"]), {f: Decimal(0) for f in TOTAL_FIELDS})
        for f in TOTAL_FIELDS:
            bucket[f] += Decimal(r[f])
    return totals


def null_counts(rows, table, columns) -> dict:
    return {f"{table}.{c}": sum(1 for r in rows if r[c] is None) for c in columns}


def reconcile(old: dict, new: dict) -> dict:
    """Compare two paths on one basis: counts, keys, totals, nulls and declared types."""
    d_only_old, d_only_new, d_changed = keyed(old["detail"], new["detail"], detail_key, DETAIL_FIELDS)
    r_missing, r_extra, r_changed = keyed(old["report"], new["report"], report_key, REPORT_FIELDS)
    old_totals, new_totals = day_totals(old["report"]), day_totals(new["report"])
    totals = []
    for key in sorted(set(old_totals) | set(new_totals)):
        for f in TOTAL_FIELDS:
            a = old_totals.get(key, {}).get(f, Decimal(0))
            b = new_totals.get(key, {}).get(f, Decimal(0))
            if a != b:
                totals.append([key[0], key[1], f, str(a), str(b)])
    old_nulls = {**null_counts(old["detail"], "detail", DETAIL_COLUMNS), **null_counts(old["report"], "report", REPORT_COLUMNS)}
    new_nulls = {**null_counts(new["detail"], "detail", DETAIL_COLUMNS), **null_counts(new["report"], "report", REPORT_COLUMNS)}
    nulls = [[c, old_nulls[c], new_nulls[c]] for c in sorted(old_nulls) if old_nulls[c] != new_nulls[c]]
    types = []
    if new.get("types"):
        types = [[c, DECLARED[c], new["types"][c]] for c in sorted(DECLARED) if not type_ok(DECLARED[c], new["types"][c])]
    row_counts = {
        "detail": [len(old["detail"]), len(new["detail"])],
        "report": [len(old["report"]), len(new["report"])],
    }
    checks = {
        "row_counts": "pass" if all(a == b for a, b in row_counts.values()) else "fail",
        "detail_keys": "pass" if not (d_only_old or d_only_new or d_changed) else "fail",
        "report_keys": "pass" if not (r_missing or r_extra or r_changed) else "fail",
        "totals": "pass" if not totals else "fail",
        "nulls": "pass" if not nulls else "fail",
        "types": "pass" if not types else "fail",
    }
    return {
        "verdict": "pass" if all(v == "pass" for v in checks.values()) else "fail",
        "checks": checks,
        "row_counts": row_counts,
        "detail": {"only_old": d_only_old, "only_new": d_only_new, "changed": d_changed},
        "report": {
            "missing": [list(k) for k in r_missing],
            "extra": [list(k) for k in r_extra],
            "changed": [[*k, f, a, b] for k, f, a, b in r_changed],
        },
        "totals": totals,
        "nulls": nulls,
        "types": types,
    }


def spark_key_membership(spark: SparkSession, old_rows, new_rows, keys) -> dict:
    """The same key comparison as a null-safe full outer join, the form that scales."""
    schema = ", ".join(f"{k} STRING" for k in keys)
    old = spark.createDataFrame([tuple(r[k] for k in keys) for r in old_rows], schema).withColumn("in_old", F.lit(True))
    new = spark.createDataFrame([tuple(r[k] for k in keys) for r in new_rows], schema).withColumn("in_new", F.lit(True))
    condition = None
    for k in keys:
        term = old[k].eqNullSafe(new[k])
        condition = term if condition is None else condition & term
    joined = old.join(new, condition, "full_outer")
    counts = joined.select(
        F.sum(F.when(F.col("in_new").isNull(), 1).otherwise(0)).alias("only_old"),
        F.sum(F.when(F.col("in_old").isNull(), 1).otherwise(0)).alias("only_new"),
        F.sum(F.when(F.col("in_old") & F.col("in_new"), 1).otherwise(0)).alias("both"),
    ).first()
    return {"only_old": int(counts.only_old), "only_new": int(counts.only_new), "both": int(counts.both)}


# ---------------------------------------------------------------- register of expected differences


def aggregate_rows(detail_rows) -> list[dict]:
    """Plain-Python aggregation with the legacy rules, used to re-derive a report from detail."""
    groups: dict = {}
    for r in detail_rows:
        g = groups.setdefault(report_key(r), {"inspections": 0, "units_inspected": 0, "units_defective": 0, "rework_cost": Decimal("0.00")})
        g["inspections"] += 1
        g["units_inspected"] += int(r["units_inspected"])
        g["units_defective"] += int(r["units_defective"])
        g["rework_cost"] += Decimal(r["rework_cost"])
    out = []
    for (plant, day, shift), g in sorted(groups.items()):
        out.append(
            canon_row(
                {
                    "plant_code": plant,
                    "business_day": day,
                    "shift_code": shift,
                    **g,
                    "defect_pct": g["units_defective"] * 100 // g["units_inspected"],
                }
            )
        )
    return out


def plant_local_hour(source_row: dict) -> int:
    from zoneinfo import ZoneInfo

    local = datetime.fromisoformat(source_row["inspected_at"]).replace(tzinfo=ZoneInfo(SERVER_TIME_ZONE))
    return local.astimezone(ZoneInfo(plant_zone(source_row["plant_code"]))).hour


def explain(result: dict, old: dict, new: dict, source_rows, register: dict) -> dict:
    """Accept differences only when a registered, owned rule predicts every one of them."""
    by_id = {r["inspection_id"]: r for r in source_rows}
    entry = next(e for e in register["entries"] if e["rule"] == "plant_local_business_day")
    explained, unexplained = [], []
    moves = {}
    for inspection_id, field, before, after in result["detail"]["changed"]:
        predicted = (
            field == entry["expected_change"]["field"]
            and entry["owner"]
            and plant_local_hour(by_id[inspection_id]) == CUTOFF_HOURS - 1
            and date.fromisoformat(after) == date.fromisoformat(before) + timedelta(days=entry["expected_change"]["days"])
        )
        if predicted:
            explained.append([entry["id"], inspection_id])
            moves[inspection_id] = after
        else:
            unexplained.append([inspection_id, field, before, after])
    for inspection_id in result["detail"]["only_old"] + result["detail"]["only_new"]:
        unexplained.append([inspection_id, "membership", None, None])
    adjusted = [dict(r, business_day=moves.get(int(r["inspection_id"]), r["business_day"])) for r in old["detail"]]
    residue = reconcile({"detail": adjusted, "report": aggregate_rows(adjusted)}, {"detail": new["detail"], "report": new["report"]})
    residue_keys = residue["report"]["missing"] + residue["report"]["extra"] + residue["report"]["changed"]
    return {
        "verdict": "explained" if not unexplained and not residue_keys else "fail",
        "explained": explained,
        "unexplained": unexplained,
        "report_residue": residue_keys,
    }


# ---------------------------------------------------------------- incremental state


def affected_days(spark, source_rows, plant_code, since, until, select_by="change", rules=TARGET) -> list[list[str]]:
    """Business days touched in the half-open window (since, until]."""
    silver = land(source_frame(spark, source_rows), rules).where(F.col("plant_code") == plant_code)
    moment = "updated_local" if select_by == "change" else "inspected_local"
    changed = silver.where(
        (F.col(moment) > F.lit(since).cast("timestamp_ntz"))
        & (F.col("updated_local") <= F.lit(until).cast("timestamp_ntz"))
    ).withColumn("business_day", business_day(rules, plant_code))
    return sorted([r.plant_code, r.business_day.isoformat()] for r in changed.select("plant_code", "business_day").distinct().collect())


def run_window(spark, state, source_rows, plant_code, since, until, select_by="change", fail_after_detail=False, rules=TARGET):
    """Replace every affected day in detail, then report, then advance the watermark last."""
    days = affected_days(spark, source_rows, plant_code, since, until, select_by, rules)
    if days:
        detail, report = build(spark, source_rows, plant_code, rules, as_of=until, days=[d for _, d in days])
        touched = {tuple(d) for d in days}
        keep = lambda r: (r["plant_code"], r["business_day"]) not in touched  # noqa: E731
        state["detail"] = sorted([r for r in state["detail"] if keep(r)] + rows_of(detail, DETAIL_COLUMNS, detail_key), key=detail_key)
        if fail_after_detail:
            raise InjectedFailure("stopped after the detail write; report and watermark untouched")
        state["report"] = sorted([r for r in state["report"] if keep(r)] + rows_of(report, REPORT_COLUMNS, report_key), key=report_key)
    state["watermark"] = until
    return days


def legacy_state_before() -> dict:
    before = fixture("legacy_state_before_p1.json")
    return {
        "watermark": before["watermark"],
        "detail": sorted((canon_row(r) for r in before["detail"]), key=detail_key),
        "report": sorted((canon_row(r) for r in before["report"]), key=report_key),
    }


def consistent(state: dict) -> bool:
    """Is the report exactly the aggregate of the detail it claims to summarize?"""
    derived = aggregate_rows(state["detail"])
    return reconcile({"detail": state["detail"], "report": derived}, {"detail": state["detail"], "report": state["report"]})["verdict"] == "pass"


# ---------------------------------------------------------------- inventory and orchestration (text only)


def strip_comments(sql: str) -> str:
    return re.sub(r"--[^\n]*", "", sql)


def scan_tsql(sql: str) -> dict:
    """A dependency and semantics inventory read from procedure text; nothing is executed."""
    code = strip_comments(sql)
    name = r"[A-Za-z_]\w*\.[A-Za-z_]\w*"
    reads = set(re.findall(rf"\b(?:FROM|JOIN)\s+({name})", code))
    deletes = [table for _, table in re.findall(rf"\bDELETE\s+(\w+)\s+FROM\s+({name})\s+AS\s+\1\b", code)]
    inserts = re.findall(rf"\bINSERT\s+INTO\s+({name})", code)
    merges = re.findall(rf"\bMERGE\s+({name})", code)
    updates = re.findall(rf"\bUPDATE\s+({name})", code)
    writes = set(deletes + inserts + merges + updates)
    tx = re.search(r"\bBEGIN\s+TRANSACTION\b(.*?)\bCOMMIT\s+TRANSACTION\b", code, re.S)
    inside = []
    if tx:
        body = tx.group(1)
        inside = sorted(
            {f"DELETE {t}" for t in re.findall(rf"\bDELETE\s+\w+\s+FROM\s+({name})", body)}
            | {f"INSERT {t}" for t in re.findall(rf"\bINSERT\s+INTO\s+({name})", body)}
            | {f"MERGE {t}" for t in re.findall(rf"\bMERGE\s+({name})", body)}
            | {f"UPDATE {t}" for t in re.findall(rf"\bUPDATE\s+({name})", body)}
        )
    on_predicates = []
    for clause in re.findall(r"\bLEFT\s+JOIN\s+\S+\s+AS\s+\w+\s+ON\s+(.*?)\s+(?=WHERE|LEFT|JOIN|;)", code, re.S):
        on_predicates += [" ".join(p.split()) for p in re.split(r"\bAND\b", clause)]
    return {
        "procedure": re.search(rf"\bCREATE\s+PROCEDURE\s+({name})", code).group(1),
        "parameters": re.findall(r"(@\w+\s+NVARCHAR\(\d+\))\s*\n\s*AS\b", code),
        "variables": sorted(set(re.findall(r"\bDECLARE\s+(@\w+\s+\w+)", code))),
        "reads": sorted(reads),
        "writes": sorted(writes),
        "temporary_objects": sorted(set(re.findall(r"#\w+", code))),
        "time_functions": sorted({f.upper() for f in re.findall(r"\b(GETDATE|GETUTCDATE|SYSDATETIME|SYSUTCDATETIME|SYSDATETIMEOFFSET|CURRENT_TIMESTAMP)\b", code, re.I)}),
        "local_time_arithmetic": sorted(set(re.findall(r"DATEADD\(\s*\w+\s*,\s*-?\d+\s*,\s*[\w.]+\s*\)", code))),
        "integer_division": sorted(set(re.findall(r"[\w.]+\s*\*\s*\d+\s*/\s*[\w.]+", code))),
        "string_key_comparisons": sorted({f"{a} = {b}" for a, b in re.findall(r"([\w.@]+_code)\s*=\s*([\w.@]+_code)", code)}),
        "null_replacements": sorted(set(re.findall(r"ISNULL\([^()]*\)", code))),
        "outer_join_on_predicates": on_predicates,
        "state_tables": sorted(t for t in set(updates) if t in reads),
        "transaction": {
            "explicit": tx is not None,
            "xact_abort": re.search(r"\bSET\s+XACT_ABORT\s+ON\b", code) is not None,
            "statements_inside": inside,
        },
        "merge_leaves_vanished_groups": bool(merges) and re.search(r"NOT\s+MATCHED\s+BY\s+SOURCE", code) is None,
    }


def task_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def map_package(package: dict, server_time_zone: str) -> dict:
    """Map SSIS-style control flow onto a job plan: tasks, dependencies and run-if conditions."""
    tasks = [t for t in package["tasks"] if "inside" not in t]
    success, failure = {}, {}
    for edge in package["precedence_constraints"]:
        bucket = success if edge["value"] == "Success" else failure
        bucket.setdefault(edge["to"], []).append(task_key(edge["from"]))
    plan = []
    for t in tasks:
        source = t["type"]
        if t.get("contains"):
            inner = [x["type"] for x in package["tasks"] if x.get("inside") == t["name"]]
            source = " + ".join([t["type"], *inner])
        if t["name"] in failure:
            depends, run_if = sorted(failure[t["name"]]), "at_least_one_failed"
        elif t["name"] in success:
            depends, run_if = sorted(success[t["name"]]), "all_succeeded"
        else:
            depends, run_if = [], None
        plan.append({"task_key": task_key(t["name"]), "source": source, "depends_on": depends, "run_if": run_if})
    schedule = package["schedule"]
    return {
        "job": schedule["agent_job"],
        "schedule": {"frequency": schedule["frequency"], "time": schedule["time"], "time_zone": server_time_zone},
        "tasks": plan,
    }


def profile_keys(df: DataFrame, column: str) -> dict:
    """How many values would a binary comparison treat differently from the source collation?"""
    c = F.col(column)
    norm = F.upper(F.rtrim(c))
    row = df.select(
        F.count(F.lit(1)).alias("rows"),
        F.sum(F.when(c.isNull(), 1).otherwise(0)).alias("nulls"),
        F.countDistinct(c).alias("distinct_raw"),
        F.countDistinct(norm).alias("distinct_collation"),
        F.sum(F.when(c.isNotNull() & (c != norm), 1).otherwise(0)).alias("case_or_trailing_variants"),
        F.sum(F.when(c.startswith(" "), 1).otherwise(0)).alias("leading_space"),
    ).first()
    return {k: int(v) for k, v in row.asDict().items()}


# ---------------------------------------------------------------- data-type semantics


def datetime_round(text: str) -> str:
    """Emulate DATETIME storage: fractional seconds move to the nearest 1/300-second tick."""
    whole, _, fraction = text.partition(".")
    micros = int(fraction.ljust(6, "0")[:6])
    ticks = (3 * micros + 5000) // 10000  # nearest tick, halves rounded up
    shown_ms = (ticks * 10 + 1) // 3  # a tick displayed to the millisecond: .000, .003, .007
    moment = datetime.fromisoformat(whole) + timedelta(milliseconds=shown_ms)
    return moment.isoformat(sep=" ", timespec="milliseconds")


# ---------------------------------------------------------------- cutover gate


def cutover_gate(scenario: dict, required_clean_days: int) -> dict:
    """Ready only after enough consecutive clean days since the last code change, and a rehearsed rollback."""
    days = scenario["days"]
    start = max((i for i, d in enumerate(days) if d["code_change"]), default=0)
    streak, last_block = 0, None
    for d in days[start:]:
        owned = d["verdict"] == "explained" and d["exceptions"] and all(e["owner"] for e in d["exceptions"])
        if d["verdict"] == "pass" or owned:
            streak += 1
        else:
            streak, last_block = 0, d
    reasons = []
    if streak < required_clean_days:
        reasons.append(
            f"{streak} of {required_clean_days} consecutive clean days since the code change of {days[start]['business_day']}"
        )
        if last_block is not None:
            if last_block["verdict"] == "explained":
                missing = [e["id"] for e in last_block["exceptions"] if not e["owner"]]
                reasons.append(f"{last_block['business_day']}: exception {', '.join(missing)} has no named owner")
            else:
                reasons.append(f"{last_block['business_day']}: unexplained differences")
    if not scenario["rollback_rehearsed"]:
        reasons.append("rollback to the legacy path has not been rehearsed")
    return {"decision": "ready" if not reasons else "not ready", "clean_days": streak, "reasons": reasons}
