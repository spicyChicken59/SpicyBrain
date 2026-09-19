<!-- section:dbxfe-python-bridge-start -->

This optional bridge assumes you can read a SELECT, a WHERE condition and a table. You do not need to know Python. Skip it if you can explain the code below; skipping records no completion. The examples run locally with Python 3.12 and require no cloud account. This parser handles one record at a time. Resolving repeated deliveries and business revisions comes later.

<!-- section:dbxfe-python-bridge-records -->

A Python dictionary maps keys to values, much like a named record. A list holds an ordered collection; here it holds records. Unlike a SQL table, a list has order, can mix types and does not enforce a schema. The dictionary {"inspection_id": "A", "inspected_units": "12"} contains two strings. The characters "12" are not an integer until deliberately converted. Missing a dictionary key is different from storing None, Python's explicit absent-value object. SQL NULL comparisons and Python None tests are not identical: use "value is None" for the latter.

A function defined with def accepts inputs and returns a result. Indentation defines its body. An if condition chooses a branch; a for loop visits elements; append adds an element to a list. A tuple groups a fixed set of values such as (accepted, rejected). The caller can unpack those two values into two variables. Imports make named library functionality available; they do not read a file until you call it.

For quantity input we accept actual integers or digit-only strings after trimming whitespace. We reject booleans, fractions, null and malformed strings. This is a teaching input policy, not a universal rule: int(3.7) would truncate and int(True) would produce 1, which would hide defects here. Type conversion is a business decision when the input is ambiguous.

<!-- section:dbxfe-python-bridge-worked -->

~~~python
import json
import csv
from io import StringIO

def units(value):
    if type(value) is int:
        result = value
    elif isinstance(value, str) and value.strip().isdigit():
        result = int(value.strip())
    else:
        raise ValueError("quantity must be an integer")
    if result < 0:
        raise ValueError("quantity must be nonnegative")
    return result

def parse(rows):
    accepted, rejected = [], []
    for index, row in enumerate(rows):
        try:
            key = row.get("inspection_id")
            if not isinstance(key, str) or not key.strip():
                raise ValueError("inspection_id is required")
            if "inspected_units" not in row:
                raise ValueError("inspected_units is missing")
            count = units(row["inspected_units"])
            accepted.append({"inspection_id": key.strip(),
                             "inspected_units": count})
        except ValueError as error:
            rejected.append({"index": index, "raw": row,
                             "reason": str(error)})
    return accepted, rejected

rows = json.loads('[{"inspection_id":"A","inspected_units":"12"},'
                  '{"inspection_id":"B","inspected_units":null},'
                  '{"inspection_id":"C"}]')
accepted, rejected = parse(rows)
assert accepted == [{"inspection_id": "A", "inspected_units": 12}]
assert [r["reason"] for r in rejected] == [
    "quantity must be an integer", "inspected_units is missing"]
csv_rows = list(csv.DictReader(StringIO(
    "inspection_id,inspected_units\nD,8\nE,eight\n")))
assert parse(csv_rows)[0] == [{"inspection_id": "D", "inspected_units": 8}]
~~~

json.loads converts the JSON text to Python values, including JSON null to None. DictReader uses the CSV header for dictionary keys and leaves cell values as strings. enumerate supplies a zero-based index so rejection evidence can point to an input. get returns None if the key is absent; the separate membership check distinguishes absent quantity from an explicit null. raise creates an exception; except handles this expected validation failure and preserves the raw record. An assertion compares a result to an independently written expectation and raises if they differ. Assertions are learning tests, not the only production validation: optimized Python may omit them.

For a real local fixture, use a context manager so a file closes even on error:
~~~python
with open("fixtures/baseline.json", encoding="utf-8") as handle:
    rows = json.load(handle)
~~~
The file path is relative to the process working directory. A missing file raises FileNotFoundError before record validation. Do not catch every exception and pretend the batch was empty.

<!-- section:dbxfe-python-bridge-task -->

Predict accepted records and all rejection reasons for X with " 7 ", Y with 2.5, Z with True, an empty inspection key with 4, and W with no quantity. Then extend parse to require defective_units, using the same conversion policy and rejecting a defective quantity greater than inspected. Test a valid 7/2 record, a missing defective field, and an impossible 7/8 record. Write the predictions before opening the solution.

<!-- section:dbxfe-python-bridge-solution -->

Only X is accepted, with integer 7. Y and Z fail the integer policy; the empty key fails required identity; W reports a missing inspected field. The changed parser adds these lines after count is calculated and before append:
~~~python
if "defective_units" not in row:
    raise ValueError("defective_units is missing")
defects = units(row["defective_units"])
if defects > count:
    raise ValueError("defective_units exceeds inspected_units")
accepted.append({"inspection_id": key.strip(),
                 "inspected_units": count,
                 "defective_units": defects})
~~~
Replace the original append with this one. The existing except block still preserves failures. The valid 7/2 result has integer quantities; missing defects reports the missing-field reason; 7/8 reports the relationship failure. A literal expected accepted list should be [{"inspection_id":"X","inspected_units":7,"defective_units":2}]. A separate expected reason list checks that failures were not silently discarded. Catching ValueError is deliberate: a programming error should still stop the program visibly.

<!-- section:dbxfe-python-bridge-limits -->

Mutating the input record can destroy evidence of an original malformed value. Build a fresh accepted record and retain the raw one. "if not value" treats zero as false and would wrongly reject a legitimate zero; test missing/null explicitly. A Python loop over this tiny list is convenient learning code, not a distributed Spark plan. Later PySpark column expressions describe work on rows; they are not ordinary Python values.

<!-- section:dbxfe-python-bridge-links -->

[DataFrames, schemas and column expressions](#/lesson/dbxfe-dataframes) turns these local records into a distributed table model. [Duplicates and conflicts](#/lesson/dbxfe-record-resolution) adds the cross-record rules intentionally absent from this parser. Language mechanisms are linked to Python documentation in Sources; parsing policy and Cinderline examples are original fiction.

<!-- section:dbxfe-python-bridge-foundation-sources -->

Primary documentation was read on 19 September 2026. Open Sources below for exact publishers, cloud/runtime context and limitations. Official mechanisms, original professional guidance and fictional records are distinct. These examples do not establish a Databricks execution, production performance, configured permissions or complete source coverage. The optional downloadable bundle provides setup, input files, independent expected outputs, starter tasks and complete solutions. The local acceptance run passed 30 tests with no failures or skips using Python 3.12.14, Apache Spark 4.0.4 and Java 17.0.20.1+1, including the complete displayed Python/SQL examples and changed input cases. The bundle includes exact fixture/output hashes and execution evidence. These results do not include Delta or Databricks execution; the reader itself does not execute code.

<!-- section:dbxfe-python-bridge-revisit -->

Try the explained checks, then review the linked cards. A reveal, visit or optional bridge skip does not record a pass or mastery. Mark completion only when you choose; assessment and review evidence remain separate.
