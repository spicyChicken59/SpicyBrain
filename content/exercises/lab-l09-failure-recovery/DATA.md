# Data dictionary and derivations

All data is synthetic and was written by hand for this lab; there is no
generator and no random seed. Cinderline Components (line 3 inspections) and
Harbourline (dock scans) are fictional, as are every lot, dock, trailer and
recipient name. No file was copied from a real system.

## Contracts

`fixtures/contract.json` and `fixtures/transfer/contract.json` tell the same
pipeline code what a record is.

| Field | Line 3 value | Harbourline value | Meaning |
|---|---|---|---|
| `name` | `cinderline-line3-inspections` | `harbourline-dock-scans` | Written into every report's content |
| `key` | `["lot"]` | `["dock", "trailer"]` | The business key: one current row per key |
| `measures` | `inspected` (min 1), `defective` (min 0, at most `inspected`) | `expected_pallets` (min 1), `scanned_pallets` (min 0, at most `expected_pallets`) | Integer measures, validated in this order and summed into `totals` |
| `recipients` | `quality-lead`, `line-3-supervisor` | `dock-lead`, `planner`, `carrier-desk` | Who is notified of each published report, in this order |

## Landing files

Each landing file is one export for one business date:

| Field | Meaning |
|---|---|
| `source` | Name of the (fictional) exporting system |
| `business_date` | The day the rows describe, as declared by the export itself |
| `extracted_at` | When the export was written (informational; no rule reads it) |
| `rows[]` | `event_id` (delivery identity), the key fields, `version` (a positive integer, higher replaces lower), the measures |

The files and what each row is for:

| File | Rows | Purpose |
|---|---|---|
| `landing/2026-03-02.json` | e01 L-101 v1 40/2; e02 L-102 v1 25/0 (twice); e03 L-101 v2 42/2; e04 L-103 v1 −5/0 | A duplicate delivery, a correction, a negative count |
| `landing/2026-03-03.json` | e05 L-104 v1 30/1 (twice); e06 L-105 v1 18/0; e07 L-105 v2 20/1; e08 L-106 v1 12/13 | A correction, more defective than inspected |
| `landing/2026-03-04.json` | e09 L-107 v1 36/3; e10 L-108 v1 24/0; e11 L-108 v2 24/1; e12 L-109 v1 "15"/0 | A count sent as text |
| `stale/2026-03-04.json` | The five 2026-03-03 rows, `business_date` 2026-03-03 | Yesterday's export re-delivered into the 2026-03-04 slot |
| `late/2026-03-03-correction.json` | e13 L-104 v2 30/0 | A correction that arrives after 2026-03-03 was published |
| `late/2026-03-03-conflict.json` | e07 L-105 v2 20/**2** | The same event id re-sent with a different payload |
| `transfer/landing/2026-03-05.json` | h01 D1/T-88 v1 12/12; h02 D1/T-89 v1 10/9; h03 D2/T-88 v1 8/8 (twice); h04 D2/T-90 v1 6/null | One trailer at two docks, a missing scan count |
| `transfer/correction/2026-03-05.json` | h05 D1/T-89 v2 10/10 | A correction for the first day |
| `transfer/landing/2026-03-06.json` | h06 and h07 both D1/T-91 v1, 14/14 and 14/13; h08 D2/T-92 v1 9/9 | Two different payloads for one key and version |
| `transfer/correction/2026-03-06.json` | h09 D1/T-91 v2 14/14 | The source's superseding version |

## Rules used to derive the expected values

1. **Retention.** Rows are retained per business date, one copy per
   `event_id`. A row whose `event_id` is new is `added`; the same id with an
   identical payload is a `duplicate`; the same id with a different payload is
   a `conflict`, recorded as `event_conflict` and never overwriting the first
   copy.
2. **Validation** (first failing rule wins, in this order): each key field is
   a non-empty string (`missing key field <f>`); `version` is an integer ≥ 1,
   booleans excluded (`version must be a positive integer`); each measure is
   an integer, booleans excluded (`<m> must be an integer`), at least its
   `min` (`<m> must be at least <min>`), and not above its `max_field`
   (`<m> must not exceed <field>`). Invalid rows are excluded with their
   reason and never take part in version selection.
3. **Resolution.** Per key, the highest valid version wins. Two retained
   events with the same key and that winning version but different measures
   are a `version_conflict`. A conflict blocks only when it touches what
   would be published: an event conflict whose retained row is the winning
   version of its key (or cannot be validated), or a version conflict on the
   winning version. A later valid version supersedes a conflict on an older
   one.
4. **Publication gate.** Any blocking conflict refuses publication
   (`conflict`). The report content is `contract`, `report_date`, `rows`
   (sorted by key, each with `version` and the winning `event_id`), `totals`
   and `excluded` (sorted by `event_id`).
5. **Identity.** `report_id` is the business date, a hyphen and the first 12
   hexadecimal characters of SHA-256 over the content serialized as JSON with
   sorted keys and no spaces. The run id is not part of it.
6. **Views.** For an as-of date: its own report is `current`; otherwise the
   latest earlier report is shown as `stale_previous`; with none,
   `blocked_no_snapshot`. A report published while a later date already has
   one carries `backfill: true`.
7. **Notification.** One outbox entry per report identity and recipient, key
   `notify:<report_id>:<recipient>`. The local channel appends one delivery per
   send, except that a key it has already accepted returns the first delivery
   id and appends nothing.

## Derivations of the expected reports (`expected/reports.json`)

- **2026-03-02.** Retention: five rows, e02 twice, so 4 added and 1
  duplicate. e04 has `inspected` −5 < 1: excluded, `inspected must be at least
  1`. L-101 has v1 (e01) and v2 (e03): v2 wins, 42/2. L-102 v1: 25/0. Totals
  42 + 25 = 67 inspected, 2 + 0 = 2 defective.
- **2026-03-03.** e05 twice: 4 added, 1 duplicate. e08 has 13 defective of
  12 inspected: `defective must not exceed inspected`. L-104 v1 30/1; L-105
  v2 (e07) 20/1 replaces v1 18/0. Totals 30 + 20 = 50 and 1 + 1 = 2.
- **2026-03-04.** 4 added, no duplicate. e12's `inspected` is the text "15":
  `inspected must be an integer`. L-107 36/3; L-108 v2 (e11) 24/1. Totals 36
  + 24 = 60 and 3 + 1 = 4.
- **2026-03-03 corrected.** The late file adds e13, 1 added. L-104 v2 (e13)
  30/0 replaces v1; L-105 unchanged. Totals 30 + 20 = 50 and 0 + 1 = 1.
- **2026-03-04 from stale input.** Without a freshness check, the stale file's
  five rows are retained under 2026-03-04 (4 added, 1 duplicate) and resolve
  exactly as 2026-03-03 did: the same rows and 50/2, labelled 2026-03-04.
- **Harbourline 2026-03-05.** h03 twice: 4 added, 1 duplicate. h04's
  `scanned_pallets` is null: `scanned_pallets must be an integer`. Keys sort
  D1/T-88, D1/T-89, D2/T-88; T-88 appears at both docks because the key has
  two fields. Totals 12 + 10 + 8 = 30 expected, 12 + 9 + 8 = 29 scanned. The
  correction replaces D1/T-89 with v2 10/10: 30 and 30.
- **Harbourline 2026-03-06.** h06 and h07 share key D1/T-91 and version 1
  with 14 against 13 scanned: one `version_conflict` with event ids h06 and
  h07, so the gate refuses. After h09 (D1/T-91 v2 14/14) arrives, v2 wins, the
  v1 conflict no longer touches what would be published, and the report is
  D1/T-91 14/14 and D2/T-92 9/9: totals 23 and 23, nothing excluded.

**Report identities.** The literal ids in `expected/reports.json` and
`expected/transfer.json` were computed from those files' own hand-written
content, not by the solution, with this one-line command run in `expected/`:

```
python3 -c "import hashlib,json;r=json.load(open('reports.json'));print({k:v['content']['report_date']+'-'+hashlib.sha256(json.dumps(v['content'],sort_keys=True,separators=(',',':')).encode()).hexdigest()[:12] for k,v in r.items() if not k.startswith('_')})"
```

(and the same over `json.load(open('transfer.json'))['reports']`).
`run_tests.py` recomputes each id with its own digest function and checks the
literal, then checks the solution's identity against the literal.

## Derivations of the run states

**Setup for the boundary cases** (`expected/boundaries.json`): 2026-03-02
runs cleanly (2 deliveries), then `line3-2026-03-03` fails once at the named
boundary with no retries. The four tasks run in order and each depends on the
previous one, so a failed task leaves every later task `upstream_failed`.

| Boundary | Where the exception is raised | What already happened | Deliveries | View of 2026-03-03 |
|---|---|---|---|---|
| `after_raw_retention` | In `ingest_raw`, after rows are retained | 4 events retained | 2 | `stale_previous` (2026-03-02) |
| `after_resolution` | In `resolve`, after the resolved state is stored | Retained and resolved | 2 | `stale_previous` |
| `before_effect` | In `notify`, after two outbox entries are written as pending | Report published | 2 | `current` |
| `after_effect` | In `notify`, after the first send, before it is marked sent | quality-lead received the report | 3 | `current` |

Each failed attempt writes one alert. A repair re-runs the same run id: the
failed task runs a second time and so do its dependents, so the execution
counts are 2/1/1/1, 1/2/1/1, 1/1/1/2 and 1/1/1/2. After raw retention, the
repair re-reads all five rows and finds every one already retained: 0 added,
5 duplicates. After the effect, the repair re-sends quality-lead's pending
entry with the same key; the channel returns `m3` without appending
(`suppressed` 1), then sends line-3-supervisor's (`m4`): 4 deliveries in
total, 2 for 2026-03-03.

**Retries** (`expected/retries.json`): one extra try for `notify`, one
transient fault after the effect. With the keyed outbox the second try's send
to quality-lead is suppressed: two deliveries. Without a key the second try
sends to both recipients again: quality-lead, quality-lead,
line-3-supervisor. With a fresh key per try the repeat carries a new key the
channel has never seen: the same three deliveries, and the first try's two
entries stay pending forever (2 sent, 2 pending). With a receiver that ignores
keys the outbox is right but the channel appends anyway: three deliveries.
With two faults and one extra try, the first send delivers `m1`, the second
try's send is suppressed and fails again, so the run fails with one delivery;
the repair sends line-3-supervisor's and suppresses quality-lead's again
(`suppressed` 2).

**Stale input** (`expected/stale.json`): after 2026-03-02 and 2026-03-03
(4 deliveries), the shortcut without a freshness check succeeds on every task
and publishes the 50/2 report as 2026-03-04 (6 deliveries). The reference
refuses in `ingest_raw` with `stale_input` before retaining anything, so the
2026-03-04 view is `stale_previous` showing 2026-03-03 and one alert is
written. Repairing the same run id with the fresh 2026-03-04 file runs
`ingest_raw` a second time and publishes 60/4.

**Backfill** (`expected/backfill.json`): 2026-03-02 and 2026-03-04 run; the
2026-03-03 view is `stale_previous` showing 2026-03-02. The backfill run for
2026-03-03 publishes with `backfill: true`, and 2026-03-04 stays current: six
deliveries, the last two flagged. Re-running the succeeded run id returns
`already_succeeded` and changes nothing, even when offered the late
correction file: 2026-03-03 still holds e05–e08. A new run id picks up the
correction (1 added), replaces the report (history holds the first id) and
sends two new deliveries (8). The conflicting re-delivery of e07 is retained
as a conflict (0 added, 0 duplicate, 1 conflict), resolves to 2 rows, 1
excluded and 1 conflict, and the gate refuses; the corrected report stays
current and e07 keeps its first payload (1 defective).

**Transfer** (`expected/transfer.json`): a fault after resolution on the
first Harbourline day leaves no report at all (`blocked_no_snapshot`). The
repair publishes three rows and sends three deliveries; the correction run
replaces the report and sends three more (6). With the coarse key
`notify:<date>:<recipient>`, the correction's keys equal the first report's,
all three entries are already sent, and nobody is told (3 deliveries). The
2026-03-06 conflict refuses publication; its view is `stale_previous` showing
the corrected 2026-03-05 report; the alerts are the injected resolve failure
and the refused gate. Repairing `harbour-2026-03-06` with the same file meets
the same stored conflict and fails again (still 6 deliveries). The new run id
`harbour-2026-03-06-c1` retains h09 (1 added), resolves 2 rows with no
conflict, publishes and notifies all three recipients (9).

**Runbook** (`expected/runbook.json`): the evidence columns are the booleans
and counts above; the boundary is named from them (and from the recorded
reason `stale_input` or `conflict`), never from the injected failure's name.
A receiver that cannot answer whether it holds a key turns both effect
boundaries into `effect_unknown`.
