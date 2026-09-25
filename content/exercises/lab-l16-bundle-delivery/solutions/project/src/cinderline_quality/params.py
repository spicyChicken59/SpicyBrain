"""Job parameters: parse the arguments the bundle passes to the wheel task.

The bundle renders these arguments from its variables for each target (see
BUNDLE.md). Nothing in this module knows which environment it is running in,
and nothing here reads a credential.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import PurePosixPath

IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
REQUIRED = ("--catalog", "--schema", "--alert-threshold")
OPTIONAL = {"--volume-root": "/Volumes"}
EXPORT_VOLUME = "exports"


@dataclass(frozen=True)
class JobParams:
    catalog: str
    schema: str
    alert_threshold: Decimal
    volume_root: str = "/Volumes"


def parse_params(argv: list[str]) -> JobParams:
    """Parse "--name value" pairs; refuse unknown, repeated, missing or unsafe values."""
    values: dict[str, str] = {}
    items = iter(argv)
    for flag in items:
        if flag not in REQUIRED and flag not in OPTIONAL:
            raise ValueError(f"unknown parameter {flag!r}")
        if flag in values:
            raise ValueError(f"parameter {flag} given twice")
        try:
            values[flag] = next(items)
        except StopIteration:
            raise ValueError(f"parameter {flag} has no value") from None
    missing = [flag for flag in REQUIRED if flag not in values]
    if missing:
        raise ValueError("missing parameter(s): " + ", ".join(missing))
    for flag in ("--catalog", "--schema"):
        if not IDENTIFIER.match(values[flag]):
            raise ValueError(
                f"{flag} {values[flag]!r} is not a plain lowercase identifier"
            )
    raw = values["--alert-threshold"]
    try:
        threshold = Decimal(raw)
    except InvalidOperation:
        raise ValueError(f"--alert-threshold {raw!r} is not a number") from None
    if not Decimal("0") < threshold < Decimal("1"):
        raise ValueError("--alert-threshold must be between 0 and 1")
    return JobParams(
        values["--catalog"],
        values["--schema"],
        threshold,
        values.get("--volume-root", OPTIONAL["--volume-root"]),
    )


def table_name(params: JobParams, table: str) -> str:
    """Three-level name for a table in this target's catalog and schema."""
    if not IDENTIFIER.match(table):
        raise ValueError(f"table {table!r} is not a plain lowercase identifier")
    return f"{params.catalog}.{params.schema}.{table}"


def export_dir(params: JobParams) -> PurePosixPath:
    """Folder of the exports volume: <volume root>/<catalog>/<schema>/exports."""
    return PurePosixPath(params.volume_root, params.catalog, params.schema, EXPORT_VOLUME)
