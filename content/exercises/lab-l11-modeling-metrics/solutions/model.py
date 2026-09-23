"""Load lab L11 fixtures into local Spark and run the named statements in model.sql.

The Python here only loads JSON with explicit schemas, registers temporary views
and passes named parameters; every modelling decision lives in model.sql.
"""
import json
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent

SOURCES = {
    # view name: (fixture file, schema DDL)
    "silver_inspections": ("inspections.json",
                           "inspection_id STRING, line_id STRING, shift_id STRING, inspected_at TIMESTAMP_NTZ, "
                           "inspected_qty BIGINT, defective_qty BIGINT, uom STRING"),
    "dim_line": ("dim_line.json",
                 "line_sk INT, line_id STRING, line_name STRING, plant_id STRING, supervisor STRING, "
                 "valid_from DATE, valid_to DATE, is_current BOOLEAN"),
    "dim_plant": ("dim_plant.json", "plant_id STRING, plant_name STRING"),
    "dim_shift": ("dim_shift.json",
                  "shift_id STRING, shift_name STRING, starts STRING, ends STRING, crosses_midnight BOOLEAN"),
    "dim_date": ("dim_date.json", "date DATE, day_name STRING, is_business_day BOOLEAN, month STRING, note STRING"),
    "unit_conversion": ("unit_conversion.json", "uom STRING, pieces_per_uom BIGINT"),
}
CONVERTERS = {
    "inspected_at": datetime.fromisoformat,
    "valid_from": date.fromisoformat,
    "valid_to": date.fromisoformat,
    "date": date.fromisoformat,
}


def statements(path=HERE / "model.sql"):
    """Split model.sql on '-- name: <statement>' lines."""
    found, name, lines = {}, None, []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("-- name:"):
            if name:
                found[name] = "\n".join(lines).strip()
            name, lines = line.split(":", 1)[1].strip(), []
        elif name:
            lines.append(line)
    if name:
        found[name] = "\n".join(lines).strip()
    return found


def plain(value):
    """Collected values as JSON-friendly Python (dates to ISO strings)."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def load_rows(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def to_tuples(records, ddl):
    columns = [part.strip().split(" ")[0] for part in ddl.split(",")]
    out = []
    for record in records:
        row = []
        for column in columns:
            value = record[column]
            if value is not None and column in CONVERTERS:
                value = CONVERTERS[column](value)
            row.append(value)
        out.append(tuple(row))
    return out


class Model:
    """One fixture set (baseline or transfer) registered as temporary views."""

    def __init__(self, spark, fixture_dir, contract_params, overrides=None, sql_path=None):
        self.spark = spark
        self.dir = Path(fixture_dir)
        self.sql = statements(Path(sql_path) if sql_path else HERE / "model.sql")
        run = load_rows(self.dir / "run.json")
        self.params = dict(contract_params,
                           period_start=date.fromisoformat(run["period_start"]),
                           period_end=date.fromisoformat(run["period_end"]),
                           as_of=date.fromisoformat(run["window_as_of"]))
        self.overrides = overrides or {}

    def register(self):
        for view, (file_name, ddl) in SOURCES.items():
            records = self.overrides.get(view) or load_rows(self.dir / file_name)
            frame = self.spark.createDataFrame(to_tuples(records, ddl), ddl)
            frame.createOrReplaceTempView(view)
        for view in ("silver_dated", "quarantine", "fact_inspection"):
            self.frame(view).createOrReplaceTempView(view)
        return self

    def frame(self, name):
        return self.spark.sql(self.sql[name], args=self.params)

    def table(self, view):
        return self.spark.table(view)

    def rows(self, name):
        return [{key: plain(value) for key, value in row.asDict().items()} for row in self.frame(name).collect()]

    def column(self, name):
        return [next(iter(row.values())) for row in self.rows(name)]

    def register_reports(self):
        self.frame("line_day").createOrReplaceTempView("report_line_day")
        self.frame("plant_day").createOrReplaceTempView("report_plant_day")

    def window(self, kind):
        """kind is business, calendar or weekday; returns (dates, business-day count, totals)."""
        self.frame("window_%s_dates" % kind).createOrReplaceTempView("window_dates")
        dates = self.column("window_%s_dates" % kind)
        business_days = self.rows("window_business_day_count")[0]["business_days"]
        return dates, business_days, self.rows("window_totals")
