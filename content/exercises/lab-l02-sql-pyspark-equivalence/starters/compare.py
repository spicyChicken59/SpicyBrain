"""Starter: comparison helpers. Fill the TODOs.

plain() must turn dates into ISO strings and Row objects into dicts so that
collected rows can be compared with JSON literals.
"""
import datetime


def plain(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if hasattr(value, "asDict"):
        return {key: plain(item) for key, item in value.asDict().items()}
    return value


def sorted_rows(frame, *keys):
    raise NotImplementedError("TODO: orderBy(*keys), collect, plain() each row")


def positional_rows(frame):
    raise NotImplementedError("TODO: collect without ordering; used only to show why that fails")


def dtypes(frame):
    return [list(pair) for pair in frame.dtypes]


def same_schema(left, right):
    raise NotImplementedError("TODO: compare StructType objects, not dtypes alone")
