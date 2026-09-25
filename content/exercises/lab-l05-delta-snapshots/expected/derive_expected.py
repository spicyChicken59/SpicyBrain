"""Plain-Python derivation of every number in expected/snapshots.json.

This file imports nothing from Spark or Delta and never calls the solution. It
replays the lab's commit sequence over the fixture rows with dictionaries,
applying the MERGE clause rules exactly as the open-source Delta Lake 4.0.0
documentation states them ("Table deletes, updates, and merges", operation
semantics):

  WHEN MATCHED            -> update every column from the source row
                             (guarded merges: only when source.revision > target.revision)
  WHEN NOT MATCHED        -> insert the source row
  WHEN NOT MATCHED BY SOURCE -> delete, only inside the plant a complete snapshot covers
  two source rows for one matched target row -> the MERGE is refused and nothing changes

The literals at the bottom (history operation names, protocol expectations for
the change data feed and for liquid clustering, the retention defaults) are
copied by hand from the same documentation set, not observed from a run.

run_tests.py asserts that the committed file equals a fresh derivation, then
compares Delta's own answers (snapshots by version, merge metrics, change feed
rows, schema, protocol) with it. A wrong rule here fails the run instead of
hiding, because Delta computes its answers independently.

    python expected/derive_expected.py      # rewrites expected/snapshots.json
"""
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ["inspection_id", "plant", "inspected", "defective", "revision"]
EVOLVED_COLUMNS = COLUMNS + ["inspector"]
CORRECTION = 12           # the corrected inspected count for A at version 2 (the 18 -> 20, not 30 story)
TRANSFER_CORRECTION = 14  # the altered input used by the transfer test


def fixture(name):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def snapshot(table, columns):
    return sorted(({c: r.get(c) for c in columns} for r in table.values()), key=lambda r: r["inspection_id"])


def version_record(table, columns=COLUMNS):
    return {
        "rows": snapshot(table, columns),
        "row_count": len(table),
        "total_inspected": sum(r["inspected"] for r in table.values()),
        "total_defective": sum(r["defective"] for r in table.values()),
    }


def change(row, kind, version):
    return {"inspection_id": row["inspection_id"], "inspected": row["inspected"], "defective": row["defective"],
            "revision": row["revision"], "_change_type": kind, "_commit_version": version}


def dedupe_latest_revision(source):
    """Keep one row per key: the highest revision. This is the guard's first half."""
    best = {}
    for r in source:
        k = r["inspection_id"]
        if k not in best or r["revision"] > best[k]["revision"]:
            best[k] = r
    return sorted(best.values(), key=lambda r: r["inspection_id"])


def merge(table, source, version, guard=False, delete_unmatched_in_plant=None, delete_all_unmatched=False,
          changes=None):
    """One MERGE ON inspection_id. Returns the row-level metrics Delta reports."""
    keys = [r["inspection_id"] for r in source]
    matched_keys = [k for k in keys if k in table]
    if len(set(matched_keys)) != len(matched_keys):
        raise ValueError("two source rows match one target row")
    metrics = {"inserted": 0, "updated": 0, "deleted": 0, "source_rows": len(source)}
    for s in source:
        k = s["inspection_id"]
        if k in table:
            if not guard or s["revision"] > table[k]["revision"]:
                before = dict(table[k])
                table[k] = dict(s)
                metrics["updated"] += 1
                if changes is not None:
                    changes.append(change(before, "update_preimage", version))
                    changes.append(change(s, "update_postimage", version))
        else:
            table[k] = dict(s)
            metrics["inserted"] += 1
            if changes is not None:
                changes.append(change(s, "insert", version))
    if delete_unmatched_in_plant or delete_all_unmatched:
        for k in sorted(table):
            in_scope = delete_all_unmatched or table[k]["plant"] == delete_unmatched_in_plant
            if k not in keys and in_scope:
                gone = table.pop(k)
                metrics["deleted"] += 1
                if changes is not None:
                    changes.append(change(gone, "delete", version))
    return metrics


def naive_merge_rows(target_rows, source_rows):
    """WHEN MATCHED THEN UPDATE SET * and WHEN NOT MATCHED THEN INSERT *, replayed over lists so that a key can
    appear twice. Only a MATCHED key with two source rows is ambiguous; unmatched source rows are each inserted."""
    target_keys = {r["inspection_id"] for r in target_rows}
    matched = [r["inspection_id"] for r in source_rows if r["inspection_id"] in target_keys]
    if len(matched) != len(set(matched)):
        raise ValueError("two source rows match one target row")
    out = []
    for t in target_rows:
        hits = [r for r in source_rows if r["inspection_id"] == t["inspection_id"]]
        out.append(dict(hits[0]) if hits else dict(t))
    out += [dict(r) for r in source_rows if r["inspection_id"] not in target_keys]
    inserted = len([r for r in source_rows if r["inspection_id"] not in target_keys])
    rows = sorted(({c: r.get(c) for c in COLUMNS} for r in out), key=lambda r: (r["inspection_id"], r["revision"]))
    return {"rows": rows, "metrics": {"inserted": inserted, "updated": len(matched), "deleted": 0,
                                      "source_rows": len(source_rows)}}


def derive(correction=CORRECTION):
    table, versions, changes = {}, {}, []
    # v0: write A.  v1: append C.  A missing incremental row is never a delete: nothing below removes A.
    for r in fixture("initial_a.json"):
        table[r["inspection_id"]] = dict(r)
    versions["0"] = version_record(table)
    for r in fixture("append_c.json"):
        table[r["inspection_id"]] = dict(r)
    versions["1"] = version_record(table)
    # v2: UPDATE A SET inspected = correction. The old file stays on disk, so a reader that sums every
    # Parquet file in the directory counts A twice: written A + written C + rewritten A.
    table["A"]["inspected"] = correction
    versions["2"] = version_record(table)
    directory_sum = (fixture("initial_a.json")[0]["inspected"] + fixture("append_c.json")[0]["inspected"]
                     + correction)
    # Files: version 0 wrote one file holding only the initial rows, version 1 one more; the UPDATE rewrites
    # the file that holds A (copying its other rows, of which there are none) and leaves the old one on disk.
    initial = fixture("initial_a.json")
    update_v2 = {"rows_updated": 1, "rows_copied": len(initial) - 1, "files_removed": 1, "files_added": 1,
                 "data_files_on_disk": 3, "files_in_current_version": 2}
    # v3: ALTER TABLE ... SET TBLPROPERTIES (delta.enableChangeDataFeed = true) changes no row.
    versions["3"] = deepcopy(versions["2"])
    # v4: incremental MERGE (matched -> update, not matched -> insert). A is absent from the source and untouched.
    metrics = {"4": merge(table, fixture("incremental_day2.json"), 4, changes=changes)}
    versions["4"] = version_record(table)
    # Day 3 as delivered: two rows for D. A naive MERGE must be refused; nothing changes.
    day3 = fixture("incremental_day3.json")
    try:
        merge(deepcopy(table), day3, 5)
        raise AssertionError("the duplicate source must be refused")
    except ValueError:
        pass
    duplicate = {"key": "D", "rows": sum(1 for r in day3 if r["inspection_id"] == "D"),
                 "source_rows": len(day3), "distinct_keys": len({r["inspection_id"] for r in day3})}
    # The same day-3 delivery merged naively into a copy of version 3, where D does not exist yet: nothing is
    # ambiguous for a MERGE (A has one source row, D and E match nothing), so it commits, inserts D twice and lets
    # A's stale revision-0 replay overwrite revision 1. The duplicate error protects matched keys only.
    first_arrival = naive_merge_rows(versions["3"]["rows"], day3)
    # v5: the guarded fix: one row per key (highest revision), update only when the source revision is newer.
    deduped = dedupe_latest_revision(day3)
    guard_skipped = {"inspection_id": "A", "source_revision": 0, "target_revision": table["A"]["revision"]}
    metrics["5"] = merge(table, deduped, 5, guard=True, changes=changes)
    versions["5"] = version_record(table)
    # The wrong approach, on a copy of version 5: an unscoped NOT MATCHED BY SOURCE DELETE treats every row the
    # South snapshot did not mention as retired, so North's A and C go too.
    unscoped = deepcopy(table)
    unscoped_metrics = merge(unscoped, fixture("snapshot_south.json"), None, guard=True, delete_all_unmatched=True)
    # v6: a complete snapshot of plant South: absence there means retired, so E is deleted; North is out of scope.
    metrics["6"] = merge(table, fixture("snapshot_south.json"), 6, guard=True, delete_unmatched_in_plant="South",
                         changes=changes)
    versions["6"] = version_record(table)
    # Schema enforcement refuses F (extra column) and changes nothing; v7 appends it with explicit evolution.
    for r in fixture("append_f_inspector.json"):
        table[r["inspection_id"]] = dict(r)
    versions["7"] = version_record(table, EVOLVED_COLUMNS)
    # v8: OPTIMIZE rewrites files, never rows.
    versions["8"] = deepcopy(versions["7"])
    counts = {}
    for c in changes:
        counts[c["_change_type"]] = counts.get(c["_change_type"], 0) + 1
    return {
        "correction": correction,
        "versions": versions,
        "directory_parquet_sum_after_version_2": directory_sum,
        "update_version_2": update_v2,
        "merge_metrics": metrics,
        "duplicate_source": duplicate,
        "deduped_day3": deduped,
        "duplicate_on_first_arrival": first_arrival,
        "guard_skipped": guard_skipped,
        "unscoped_snapshot_merge": {"rows": snapshot(unscoped, COLUMNS), "metrics": unscoped_metrics},
        "change_feed_versions_4_to_6": sorted(changes, key=lambda c: (c["_commit_version"], c["inspection_id"],
                                                                       c["_change_type"])),
        "change_feed_counts": dict(sorted(counts.items())),
        "schema_before_evolution": COLUMNS,
        "schema_after_evolution": EVOLVED_COLUMNS,
        "rows_with_null_inspector_after_evolution": sorted(k for k, r in table.items() if r.get("inspector") is None),
        "row_with_inspector": {"inspection_id": "F", "inspector": "QA-2"},
    }


# Literals copied by hand from the open-source Delta Lake 4.0.0 documentation (docs/source at tag v4.0.0):
# history operation names (delta-utility.md), the change data feed's protocol row and the liquid clustering
# warning (versioning.md, delta-clustering.md), and the retention defaults (delta-batch.md, delta-utility.md).
DOCUMENTED = {
    "history_operations": ["WRITE", "WRITE", "UPDATE", "SET TBLPROPERTIES", "MERGE", "MERGE", "MERGE",
                           "WRITE", "OPTIMIZE"],
    "change_feed_enabled_at_version": 3,
    "change_feed_protocol": {"table_feature": "changeDataFeed", "min_reader_version": 1,
                             "min_writer_version_at_least": 4},
    "clustered_table_protocol": {"table_features": ["clustering", "domainMetadata"], "min_reader_version": 1,
                                 "min_writer_version": 7, "clustering_columns": ["plant"]},
    "retention": {"deleted_file_retention_default_hours": 168, "log_retention_default_days": 30,
                  "retention_check_setting": "spark.databricks.delta.retentionDurationCheck.enabled",
                  "retention_check_expected_value": "true",
                  "refused_retain_hours": 0},
    "refusals": {
        "duplicate_source": "DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE",
        "change_feed_before_enablement": "DELTA_MISSING_CHANGE_DATA",
        "schema_mismatch_text": "A schema mismatch detected when writing to the Delta table",
        "vacuum_retention_text": "Are you sure you would like to vacuum files with such a low retention period",
    },
    "optimize": {"files_after_compaction": 1, "second_run_files_added": 0, "second_run_files_removed": 0},
}


def derive_all():
    return {
        "_derivation": "Plain-Python replay of the commit sequence over fixtures/ (see DATA.md); base uses the "
                       "correction 12, transfer uses 14. The 'documented' block is copied by hand from the "
                       "open-source Delta Lake 4.0.0 documentation. No Spark or Delta code produced any value here.",
        "base": derive(CORRECTION),
        "transfer": derive(TRANSFER_CORRECTION),
        "documented": DOCUMENTED,
    }


if __name__ == "__main__":
    out = ROOT / "expected" / "snapshots.json"
    out.write_text(json.dumps(derive_all(), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out}")
