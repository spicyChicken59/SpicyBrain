"""Deliberate comparison helpers: sorted rows as plain values, and schemas.

A relation has no promised row order. Compare rows after an explicit sort on
a key that is unique in that relation, and compare the schema separately:
equal values do not prove equal types.
"""
import datetime
import decimal


def plain(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return str(value)
    if hasattr(value, "asDict"):
        return {key: plain(item) for key, item in value.asDict().items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


def sorted_rows(frame, *keys):
    """Collect after an explicit ORDER BY; keys should identify a row in this relation."""
    return [plain(row) for row in frame.orderBy(*keys).collect()]


def positional_rows(frame):
    """Collect in whatever order the engine returns. Used only to show why that is not a contract."""
    return [plain(row) for row in frame.collect()]


def dtypes(frame):
    return [list(pair) for pair in frame.dtypes]


def same_schema(left, right):
    """StructType equality: names, types, nullability and column order, not values."""
    return left.schema == right.schema


def schema_differences(left, right):
    """Human-readable field-by-field differences, empty when same_schema is true."""
    differences = []
    left_fields = {field.name: field for field in left.schema.fields}
    right_fields = {field.name: field for field in right.schema.fields}
    if [f.name for f in left.schema.fields] != [f.name for f in right.schema.fields]:
        differences.append("column order or names differ: %s versus %s" % (
            [f.name for f in left.schema.fields], [f.name for f in right.schema.fields]))
    for name in sorted(set(left_fields) | set(right_fields)):
        a, b = left_fields.get(name), right_fields.get(name)
        if a is None or b is None:
            differences.append("%s present on one side only" % name)
        elif a.dataType != b.dataType:
            differences.append("%s type %s versus %s" % (name, a.dataType.simpleString(), b.dataType.simpleString()))
        elif a.nullable != b.nullable:
            differences.append("%s nullable %s versus %s" % (name, a.nullable, b.nullable))
    return differences
