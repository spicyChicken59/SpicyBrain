# Explained models

## Python bridge

CSV delivers text. An empty string and `None` mean missing under this task's
contract; neither means a measured zero. Convert inside `try`, reject malformed
integer text with a specific reason, then enforce the quantity rule. Zero is
accepted. `solutions/reference.py:parse_bridge` uses a context manager to close
the file, `csv.DictReader` to make dictionaries, a loop to preserve every
record's outcome, and only catches conversion/validation `ValueError`.

The different starter task's complete solution is:

```python
def parse_records(rows):
    accepted, rejected = [], []
    for row in rows:
        value = row.get('units')
        if value is None or value.strip() == '':
            rejected.append({'record_id': row['record_id'], 'reason': 'missing units'})
            continue
        try:
            units = int(value)
        except ValueError:
            rejected.append({'record_id': row['record_id'], 'reason': 'malformed integer'})
            continue
        if units < 0:
            rejected.append({'record_id': row['record_id'], 'reason': 'negative units'})
        else:
            accepted.append({'record_id': row['record_id'], 'units': units})
    return {'accepted': accepted, 'rejected': rejected}

assert parse_records([{'record_id':'s1','units':'11'}])['accepted'][0]['units'] == 11
assert parse_records([{'record_id':'s2','units':None}])['rejected'][0]['reason'] == 'missing units'
assert parse_records([{'record_id':'s3','units':'2.5'}])['rejected'][0]['reason'] == 'malformed integer'
assert parse_records([{'record_id':'s4','units':'0'}])['accepted'][0]['units'] == 0
```

This parser's source contract is CSV-like strings/None; it is not a parser for
every arbitrary Python object. JSON inspection inputs have their own strict
type validator, which rejects string versions and boolean versions explicitly.

## Typed expressions and intermediate results

`SCHEMA` names two string columns and three nullable 32-bit integer columns.
Nullable means the representation can retain missing evidence, not that
missing required quantities are accepted. `try_cast('twelve' AS INT)` yields
null; keep a separate rejection reason. `WHERE inspected_units = NULL` keeps
no rows because ordinary equality with null is unknown. Use `IS NULL`.

The baseline has five retained rows, four distinct deliveries, three valid
revision rows (A1, A2, C1), and one quarantined row (B1). A1 is a valid historical
revision, not an additional current inspection. Selecting current revisions
produces A2 12/1 and C1 8/0. Accepted grain is one inspection. SUM over integer
columns returns bigint totals; the explicit ratio is double. Accepted counts
are 20/1 = 0.05. Mean(1/12, 0/8) = 0.041666… answers a different question.

With A3 14/1 the current output becomes A3 and C1, totals 22/1, rate
0.045454545454545456. Exact replay may increase raw/audit counts; it does not
change accepted rows, totals, publication snapshot identity or simulated
notification count. Full SQL CTEs and their PySpark equivalents are beside one
another in `solutions/spark_transform.py`. Tests compare each against authored
expected rows/types, not just against each other.

## Grain and execution

The tag join yields A/urgent 12/1, A/sampled 12/1, C/routine 8/0. Three rows
sum to 32/2. This is not a data-quality repair: the join changed the grain.
A left semijoin asks whether a match exists and returns each left inspection
once, giving two rows and 20 inspected. An alternative is joining a dimension
whose key uniqueness is proved. Arbitrarily dropping duplicate joined rows is
not a general repair; it could delete genuine distinct facts.

Transformations assemble lazy plans; actions such as `collect` and `count`
execute work. A partition is a chunk assigned to a task. A shuffle exchanges
data so matching/grouped keys can meet. The captured local formatted plan has
actual joins and Exchanges under deliberately fixed two-partition settings
with adaptive planning and automatic broadcast disabled. These settings make
the teaching plan inspectable; they are not production tuning advice.

## Source contract, current state and publication

`reference.py` retains each raw row, validates it, indexes immutable event
payloads and business key/revision payloads, then resolves latest state. All
conflicting evidence remains addressable by raw index. Duplicate event IDs
with equal payloads are deliveries of one event. Distinct event IDs with the
same key/revision/quantities agree; equal revisions with different quantities
conflict. Neither row order nor an arbitrary `row_number` is authority.

This conservative authored policy blocks publication for every unresolved
identity conflict, including one discovered in older retained history or with
no attributable inspection key. Known affected keys are separately unresolved.
There is no automatic adjudication in this exercise. An invalid latest revision
for a key with earlier valid evidence blocks that key rather than reviving its
old value. An unordered observation for a known valid key also blocks: latest
cannot be proved. A key that has never had valid evidence, such as B, is
quarantined and explicitly excluded under a separate accepted-coverage policy.
Unkeyed malformed input remains in quarantine. Publication never means complete
source coverage; it reports accepted inspections and disclosed exclusions.

During unresolved A, accepted preparation contains only C 8/0; **8/0 is not a
publishable new current report**. Publication is blocked. If a verified 20/1
snapshot exists it remains `stale_previous`; on a first blocked run there is
`blocked_no_snapshot`. The current accepted preparation, rejected evidence,
and previous published report are deliberately separate.

An empty unresolved-key list proves only that no usable affected key was
identified. The two `unkeyed` rows have null inspection IDs, quantities 2 and 3,
and the same event ID. Both remain quarantined; their event payloads conflict.
On a first run there are no accepted candidates, publication is false, status
is `blocked_no_snapshot`, and no snapshot/effect exists. After a verified
baseline, receiving this conflict alongside A v3 leaves a diagnostic 22/1
candidate but preserves the published 20/1 snapshot as `stale_previous`, with
no second effect. Reverse order and replay cannot restore trustworthy provenance.
Missing, empty, whitespace-only and null keys do not become invented identities.

The gate therefore checks both `not conflicts` and `not blocked`. This does
not block all quarantine: isolated invalid B and two unrelated unkeyed events
still follow the stated accepted-only coverage policy when no identity conflict
exists. A blank event ID itself provides no immutable identity to compare.

SQL and PySpark expose `event_conflicts`, `revision_conflicts`, `unresolved`
and a one-row `publication` decision relation. Its three counts describe
event conflicts, revision conflicts and unresolved usable keys; all must be
zero for `publication_allowed`. Read that decision instead of inferring safety
from accepted rows or an empty unresolved relation. Spark produces diagnostic
relations only; `LocalPipeline` alone simulates snapshots and local effects.
For empty candidate input SQL SUM returns null totals while Python sum gives
zero totals; neither representation is a publishable report in this blocked case.

## Failure and recovery

`reference.py:guarded_upsert` separately models target behavior: absent key is
inserted, a strictly higher revision replaces the row, an older arrival does
nothing, and equal-and-identical is a replay. Equal-but-different is an error.
Source key uniqueness is checked before updating; the function returns a new
state and does not mutate the caller's target. Updating only A leaves C intact:
absence from this incremental source is not a deletion instruction. The caller
must still enforce the publication gate; an upsert cannot resolve a source
conflict or turn partial coverage into a complete report. This is executed local
Python reference behavior, not execution of Delta MERGE.

Baseline publication has five raw observations and one local effect. Failure
after retaining A3 leaves six raw observations, previous published totals
20/1, and `stale_previous`. Recovery recomputes from those six rows, publishes
22/1, and records a second local effect. Failure after resolution similarly
leaves the old snapshot explicitly stale. Failure after publication leaves
correct 22/1 reporting but a pending effect; recovery records that effect once
using snapshot identity. Repeated recovery does not create a third effect.

All storage here is Python memory; a process exit loses it. Production recovery
requires retained durable input, versioned target state, durable orchestration,
publication consistency, and an actual transactional outbox/recipient contract.
This exercise proves none of those services. It illustrates boundaries so a
learner can ask the right recovery questions.

## Transfer rationale

The order-line business key is (order_id, line_id), not either part alone.
For O7/L1, revision 2 replaces 2×300 cents with 3×300 = 900. O7/L2 revision 2
is an explicit cancellation tombstone; it contributes zero but remains current
at revision 2. O8/L1 contributes 2×200 = 400. Total is 1300 cents across two
active lines; three current line records include the cancellation. A late
O7/L2 v1 upsert cannot replace its tombstone. Absence from a later incremental
batch never deletes anything. A conflicting O7/L1 v2 quantity 4 makes current
revenue ambiguous, so this transfer model raises and refuses to publish totals.

Integer cents avoids introducing binary floating-point currency rounding into
this exercise; real currencies, taxes and rounding require a richer contract.
The cancellation rule differs from inspection quantity validation, demonstrating
why reliable transformations begin with domain identity and source semantics.
