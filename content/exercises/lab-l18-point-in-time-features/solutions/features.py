"""lab-l18-point-in-time-features: reference solution (local pandas).

One transformation (`compute_features`) produces every feature row, for
training and for serving. A feature row carries two times:

* ``feature_time``: the end of the two-hour window (start, end] it describes;
* ``available_at``: the scheduled run that published this version of it.

A training row may use a feature row only if it was published at or before
the row's prediction time, so the join runs on availability, never on
feature_time alone. Late readings never rewrite a published row; they add a
new version with a later ``available_at``.

Executed locally with pandas 3.0.6 and numpy 2.5.3 on CPython 3.12. Nothing
here runs on Databricks; the machines, schedule and policies are fictional.

    python solutions/features.py            # primary replay, as JSON
    python solutions/features.py --late     # with fixtures/late_observations.csv
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"

KEY_COLUMNS = ["machine_id", "feature_time", "available_at"]
FEATURE_COLUMNS = ["temp_mean_2h", "vib_max_2h", "reading_count_2h", "vib_count_2h", "low_coverage"]
FEATURE_TABLE_COLUMNS = KEY_COLUMNS + FEATURE_COLUMNS + ["source_max_ingested_at"]
LABEL_COLUMNS = ["machine_id", "prediction_time", "event_at", "label_time", "label"]
STATUS_OK, STATUS_NONE, STATUS_STALE = "ok", "none_available", "stale"
LABEL_KNOWN, LABEL_NOT_YET = "known", "not_yet_known"
PUBLISHED_AFTER, INGESTED_AFTER = "published_after_prediction", "source_ingested_after_prediction"


class FeatureContractError(ValueError):
    """A delivery, feature table or label table broke the written contract."""


class DuplicateEntityTimeError(FeatureContractError):
    """Two rows claim the same entity at the same time key."""


class FutureInformationError(FeatureContractError):
    """A row would use information that did not exist at its prediction time."""

    def __init__(self, message: str, rows: list[dict] | None = None):
        super().__init__(message)
        self.rows = rows or []


class TransformationMismatchError(FeatureContractError):
    """Two implementations of the transformation disagree on identical input."""

    def __init__(self, message: str, differences: list[dict] | None = None):
        super().__init__(message)
        self.differences = differences or []


# ------------------------------------------------------------------ loading
def _utc(frame: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    for column in columns:
        frame[column] = pd.to_datetime(frame[column], utc=True)
    return frame


def load_contract(path: str | Path = FIXTURES / "feature_contract.json") -> dict:
    contract = json.loads(Path(path).read_text(encoding="utf-8"))
    contract["run_times"] = [pd.Timestamp(value) for value in contract["run_times"]]
    return contract


def load_consumers(path: str | Path = FIXTURES / "consumers.json") -> dict:
    consumers = json.loads(Path(path).read_text(encoding="utf-8"))
    for policy in consumers.values():
        policy["training_cutoff"] = pd.Timestamp(policy["training_cutoff"])
    return consumers


def load_observations(*paths: str | Path) -> pd.DataFrame:
    frames = [pd.read_csv(path, dtype={"machine_id": "str"}) for path in paths]
    frame = pd.concat(frames, ignore_index=True)
    frame = _utc(frame, ("observed_at", "ingested_at"))
    frame["temp_c"] = frame["temp_c"].astype("float64")
    frame["vibration_mm_s"] = frame["vibration_mm_s"].astype("float64")
    return frame.sort_values(["machine_id", "observed_at"], kind="stable").reset_index(drop=True)


def load_labels(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"machine_id": "str"})
    frame = _utc(frame, ("prediction_time", "event_at", "label_time"))
    frame["label"] = frame["label"].astype("int64")
    return frame[LABEL_COLUMNS].reset_index(drop=True)


# ---------------------------------------------------------------- contracts
def refuse_duplicates(frame: pd.DataFrame, keys: list[str], what: str) -> None:
    """One entity at one time key is one row. Two rows with the same key make
    every later join pick by storage order, so refuse them and name the key."""
    duplicated = frame[frame.duplicated(keys, keep=False)]
    if not duplicated.empty:
        first = duplicated.sort_values(keys, kind="stable").iloc[0]
        identity = " ".join(f"{key}={plain(first[key])}" for key in keys)
        count = int((frame[keys] == first[keys]).all(axis=1).sum())
        raise DuplicateEntityTimeError(f"duplicate entity-time {what}: {identity} appears {count} times")


def validate_observations(observations: pd.DataFrame, contract: dict) -> None:
    """A delivery the feature job refuses rather than aggregates."""
    unknown = sorted(set(observations["machine_id"]) - set(contract["entities"]))
    if unknown:
        raise FeatureContractError(f"unknown entity key in observations: {unknown}")
    if observations[["machine_id", "observed_at", "ingested_at"]].isna().any().any():
        raise FeatureContractError("null entity key or timestamp in observations")
    refuse_duplicates(observations, ["machine_id", "observed_at"], "reading")
    if (observations["ingested_at"] < observations["observed_at"]).any():
        raise FeatureContractError("a reading was ingested before it was observed")


def validate_feature_table(features: pd.DataFrame, contract: dict) -> None:
    """Keys, times and quality rules every consumer relies on."""
    missing = [column for column in FEATURE_TABLE_COLUMNS if column not in features.columns]
    if missing:
        raise FeatureContractError(f"missing feature columns: {missing}")
    if features[KEY_COLUMNS + ["source_max_ingested_at"]].isna().any().any():
        raise FeatureContractError("null entity key or timestamp in feature table")
    refuse_duplicates(features, KEY_COLUMNS, "feature row")
    grid = pd.Timedelta(hours=contract["window_hours"])
    if (features["feature_time"] != features["feature_time"].dt.floor(grid)).any():
        raise FeatureContractError("feature_time is not a window end on the contract grid")
    if (features["available_at"] < features["feature_time"]).any():
        raise FeatureContractError("available_at precedes the end of the window it describes")
    stamped_early = features[features["source_max_ingested_at"] > features["available_at"]]
    if not stamped_early.empty:
        detail = "; ".join(
            f"{row.machine_id} window {row.feature_time.isoformat()} published {row.available_at.isoformat()} "
            f"uses a reading ingested {row.source_max_ingested_at.isoformat()}"
            for row in stamped_early.sort_values(KEY_COLUMNS, kind="stable").itertuples(index=False)
        )
        raise FeatureContractError(f"{len(stamped_early)} row(s) claim readings ingested after they were published: {detail}")
    if (features["reading_count_2h"] < 1).any():
        raise FeatureContractError("feature row with no readings")
    if ((features["vib_count_2h"] < 0) | (features["vib_count_2h"] > features["reading_count_2h"])).any():
        raise FeatureContractError("vib_count_2h outside [0, reading_count_2h]")
    bounds = contract["columns"]["temp_mean_2h"]
    if ((features["temp_mean_2h"] < bounds["min"]) | (features["temp_mean_2h"] > bounds["max"])).any():
        raise FeatureContractError(f"temp_mean_2h outside the plausible range [{bounds['min']}, {bounds['max']}]")
    if (features["vib_max_2h"] < 0).any():
        raise FeatureContractError("negative vib_max_2h")
    if (features["vib_max_2h"].isna() != (features["vib_count_2h"] == 0)).any():
        raise FeatureContractError("vib_max_2h must be null exactly when the window has no vibration value")
    expected = features["reading_count_2h"] < contract["expected_readings_per_window"]
    if (features["low_coverage"].astype(bool) != expected).any():
        raise FeatureContractError("low_coverage disagrees with reading_count_2h")


def validate_labels(labels: pd.DataFrame, contract: dict) -> None:
    unknown = sorted(set(labels["machine_id"]) - set(contract["entities"]))
    if unknown:
        raise FeatureContractError(f"unknown entity key in labels: {unknown}; known entities are {contract['entities']}")
    refuse_duplicates(labels, ["machine_id", "prediction_time"], "label")
    past = labels[labels["event_at"].notna() & (labels["event_at"] <= labels["prediction_time"])]
    if not past.empty:
        first = past.iloc[0]
        raise FutureInformationError(
            f"outcome event at or before its prediction time: machine_id={first['machine_id']} "
            f"prediction_time={first['prediction_time'].isoformat()} event_at={first['event_at'].isoformat()}"
        )
    early = labels[labels["label_time"] <= labels["prediction_time"]]
    if not early.empty:
        first = early.iloc[0]
        raise FutureInformationError(
            f"label known at or before its prediction time: machine_id={first['machine_id']} "
            f"prediction_time={first['prediction_time'].isoformat()}"
        )


def assert_no_future_information(joined: pd.DataFrame) -> None:
    """Refuse any joined row built from something that did not exist yet.

    Two independent checks: the row was published after the prediction time,
    or (lineage) a reading behind the row was ingested after the prediction
    time, which catches a table whose availability stamps are wrong."""
    rows = []
    for row in joined.itertuples(index=False):
        if pd.isna(row.feature_time):
            continue
        reason = None
        if row.available_at > row.prediction_time:
            reason = PUBLISHED_AFTER
        elif row.source_max_ingested_at > row.prediction_time:
            reason = INGESTED_AFTER
        if reason:
            rows.append({
                "machine_id": row.machine_id,
                "prediction_time": row.prediction_time.isoformat(),
                "feature_time": row.feature_time.isoformat(),
                "available_at": row.available_at.isoformat(),
                "reason": reason,
            })
    if rows:
        detail = "; ".join(f"{r['machine_id']} at {r['prediction_time']} ({r['reason']})" for r in rows)
        raise FutureInformationError(f"{len(rows)} row(s) use future information: {detail}", rows)


# ----------------------------------------------------------- transformation
def window_end(observed_at: pd.Series, window_hours: int) -> pd.Series:
    """End of the window (start, end] containing each reading: a reading at
    exactly 10:00 belongs to the window ending 10:00, not the next one."""
    return observed_at.dt.ceil(pd.Timedelta(hours=window_hours))


def compute_features(observations: pd.DataFrame, run_at: pd.Timestamp, contract: dict) -> pd.DataFrame:
    """THE transformation, used by the batch job and by any request path.

    Uses only readings ingested at or before run_at, for windows that have
    ended by run_at. One row per (machine_id, feature_time)."""
    known = observations[observations["ingested_at"] <= run_at].copy()
    known["feature_time"] = window_end(known["observed_at"], contract["window_hours"])
    known = known[known["feature_time"] <= run_at]
    grouped = known.groupby(["machine_id", "feature_time"], as_index=False).agg(
        temp_mean_2h=("temp_c", "mean"),
        vib_max_2h=("vibration_mm_s", "max"),        # max skips missing values
        reading_count_2h=("temp_c", "size"),          # rows, missing or not
        vib_count_2h=("vibration_mm_s", "count"),    # non-missing values only
        source_max_ingested_at=("ingested_at", "max"),
    )
    grouped["reading_count_2h"] = grouped["reading_count_2h"].astype("int64")
    grouped["vib_count_2h"] = grouped["vib_count_2h"].astype("int64")
    grouped["low_coverage"] = grouped["reading_count_2h"] < contract["expected_readings_per_window"]
    grouped["available_at"] = run_at
    return grouped[FEATURE_TABLE_COLUMNS].sort_values(["machine_id", "feature_time"], kind="stable").reset_index(drop=True)


def build_feature_table(observations: pd.DataFrame, contract: dict) -> pd.DataFrame:
    """Replay the publication schedule. A (machine, window) row is published
    at the first run after its window closes, and again only when the readings
    behind it changed (a late arrival), as a new version with a later
    available_at. Published versions are never rewritten."""
    validate_observations(observations, contract)
    published: list[pd.DataFrame] = []
    last_signature: dict[tuple, tuple] = {}
    for run_at in sorted(contract["run_times"]):
        computed = compute_features(observations, run_at, contract)
        changed = []
        for row in computed.itertuples(index=False):
            key = (row.machine_id, row.feature_time)
            signature = (int(row.reading_count_2h), row.source_max_ingested_at)
            changed.append(last_signature.get(key) != signature)
            last_signature[key] = signature
        published.append(computed[np.array(changed, dtype=bool)])
    table = pd.concat(published, ignore_index=True)
    table = table.sort_values(KEY_COLUMNS, kind="stable").reset_index(drop=True)
    validate_feature_table(table, contract)
    return table


# ------------------------------------------------------------------ the join
def _typed(joined: pd.DataFrame) -> pd.DataFrame:
    """A left join that finds no feature row fills NaN, which silently turns
    integer counts into floats (3 becomes 3.0). Restore the contract types:
    nullable integers and a nullable boolean, so a missing value stays missing."""
    for column in ("reading_count_2h", "vib_count_2h"):
        joined[column] = joined[column].astype("Int64")
    joined["low_coverage"] = joined["low_coverage"].astype("boolean")
    return joined


def point_in_time_join(labels: pd.DataFrame, features: pd.DataFrame, contract: dict) -> pd.DataFrame:
    """For each label row: among feature rows of the same machine published at
    or before prediction_time, the newest window, and of that window the newest
    version. No such row: the feature columns stay null."""
    validate_labels(labels, contract)
    validate_feature_table(features, contract)
    left = labels.reset_index(names="label_row")
    candidates = left.merge(features, on="machine_id", how="inner")
    candidates = candidates[candidates["available_at"] <= candidates["prediction_time"]]
    chosen = (
        candidates.sort_values(["label_row", "feature_time", "available_at"], kind="stable")
        .groupby("label_row", as_index=False)
        .tail(1)
    )
    feature_part = chosen[["label_row"] + KEY_COLUMNS[1:] + FEATURE_COLUMNS + ["source_max_ingested_at"]]
    joined = _typed(left.merge(feature_part, on="label_row", how="left").drop(columns="label_row"))
    assert_no_future_information(joined)
    return joined.reset_index(drop=True)


def asof_join_on_availability(labels: pd.DataFrame, features: pd.DataFrame, contract: dict) -> pd.DataFrame:
    """pandas.merge_asof on available_at alone: the most recently PUBLISHED row.
    Safe from future information, but equal to point_in_time_join only while
    no older window is republished after a newer one (see the late task)."""
    validate_labels(labels, contract)
    validate_feature_table(features, contract)
    right = features.sort_values(["available_at", "feature_time"], kind="stable")
    left = labels.sort_values("prediction_time", kind="stable")
    joined = pd.merge_asof(
        left, right, left_on="prediction_time", right_on="available_at", by="machine_id",
        direction="backward", allow_exact_matches=True,
    )
    joined = _typed(joined)
    assert_no_future_information(joined)
    return joined.sort_values(["machine_id", "prediction_time"], kind="stable").reset_index(drop=True)


# --------------------------------------------------------- missingness policy
def assess(prediction_time: pd.Timestamp, feature_time, max_age_minutes: int) -> tuple[int | None, str]:
    """The ONE missingness rule, shared by training and serving:
    no row -> none_available; older than the consumer's limit -> stale;
    otherwise ok. The limit is inclusive: exactly max_age_minutes is ok."""
    if feature_time is None or pd.isna(feature_time):
        return None, STATUS_NONE
    age = int((prediction_time - feature_time) / pd.Timedelta(minutes=1))
    return age, STATUS_STALE if age > max_age_minutes else STATUS_OK


def build_training_set(labels: pd.DataFrame, features: pd.DataFrame, contract: dict, policy: dict,
                       join=None) -> pd.DataFrame:
    """Point-in-time join, then the shared missingness rule and label maturity.
    Values stay on every row so each decision can be inspected; training_rows
    keeps only usable rows. `join` defaults to point_in_time_join; the late
    task passes asof_join_on_availability to compare the two."""
    joined = (join or point_in_time_join)(labels, features, contract)
    assessed = [assess(row.prediction_time, row.feature_time, policy["max_feature_age_minutes"])
                for row in joined.itertuples(index=False)]
    joined["feature_age_minutes"] = pd.array([age for age, _ in assessed], dtype="Int64")
    joined["feature_status"] = [status for _, status in assessed]
    joined["label_status"] = np.where(joined["label_time"] <= policy["training_cutoff"], LABEL_KNOWN, LABEL_NOT_YET)
    return joined.sort_values(["machine_id", "prediction_time"], kind="stable").reset_index(drop=True)


def training_rows(training_set: pd.DataFrame) -> pd.DataFrame:
    usable = (training_set["feature_status"] == STATUS_OK) & (training_set["label_status"] == LABEL_KNOWN)
    return training_set[usable].reset_index(drop=True)


# ------------------------------------------------------------------ serving
def online_store_at(features: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    """What an online store can hold at `now`: for each machine, the newest
    window published by then, newest version. A republished OLDER window never
    replaces a newer one (a last-write-wins upsert keyed by machine would)."""
    published = features[features["available_at"] <= now]
    latest = published.sort_values(["machine_id", "feature_time", "available_at"], kind="stable").groupby("machine_id").tail(1)
    return latest.set_index("machine_id")


def serve_features(features: pd.DataFrame, machine_id: str, now: pd.Timestamp, policy: dict) -> dict:
    """Serving path: a key lookup in the online store, then the SAME
    missingness rule as training. A missing feature is reported, never filled."""
    store = online_store_at(features, now)
    row = store.loc[machine_id] if machine_id in store.index else None
    feature_time = None if row is None else row["feature_time"]
    age, status = assess(now, feature_time, policy["max_feature_age_minutes"])
    response = {"machine_id": machine_id, "prediction_time": now,
                "feature_time": feature_time, "available_at": None if row is None else row["available_at"]}
    for column in FEATURE_COLUMNS:
        response[column] = None if row is None else row[column]
    response["feature_age_minutes"] = age
    response["feature_status"] = status
    return {key: plain(value) for key, value in response.items()}


def assert_same_transformation(training_fn, serving_fn, observations: pd.DataFrame, run_at: pd.Timestamp, contract: dict) -> None:
    """Run both implementations on identical input and refuse any difference,
    naming each (machine, window) and each column with both values."""
    expected = training_fn(observations, run_at, contract).set_index(["machine_id", "feature_time"])
    actual = serving_fn(observations, run_at, contract).set_index(["machine_id", "feature_time"])
    differences = []
    for key in sorted(set(expected.index) | set(actual.index)):
        if key not in expected.index or key not in actual.index:
            differences.append({"machine_id": key[0], "feature_time": key[1].isoformat(),
                                "columns": {"row": ["present" if key in expected.index else "absent",
                                                    "present" if key in actual.index else "absent"]}})
            continue
        changed = {}
        for column in FEATURE_COLUMNS:
            left, right = plain(expected.loc[key, column]), plain(actual.loc[key, column])
            if left != right:
                changed[column] = [left, right]
        if changed:
            differences.append({"machine_id": key[0], "feature_time": key[1].isoformat(), "columns": changed})
    if differences:
        raise TransformationMismatchError(json.dumps(differences, sort_keys=True), differences)


# ------------------------------------------------------------- serialization
def plain(value):
    """JSON-safe scalar: ISO timestamps, None for any missing value, ints, bools, floats."""
    if value is None or value is pd.NaT or value is pd.NA:
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return None if np.isnan(value) else float(value)
    return value


def records(frame: pd.DataFrame, columns: list[str] | None = None) -> list[dict]:
    selected = frame if columns is None else frame[columns]
    return [{column: plain(value) for column, value in row.items()} for row in selected.to_dict(orient="records")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--late", action="store_true", help="include fixtures/late_observations.csv")
    args = parser.parse_args()
    contract, consumers = load_contract(), load_consumers()
    paths = [FIXTURES / "observations.csv"] + ([FIXTURES / "late_observations.csv"] if args.late else [])
    features = build_feature_table(load_observations(*paths), contract)
    policy = consumers["failure_warning"]
    training = build_training_set(load_labels(FIXTURES / policy["label_file"]), features, contract, policy)
    print(json.dumps({"feature_table": records(features),
                      "training_set": records(training.drop(columns=["event_at"])),
                      "training_rows": len(training_rows(training))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
