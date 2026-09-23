# Lab L16 data dictionary and derivations

All data is synthetic, written by hand for this lab. Cinderline Components,
its production lines, groups, hosts and service principal IDs are fictional.
No generator or random seed is involved; every file is literal.

## fixtures/inspections.json — one export day (14 September 2026)

One object per shift inspection record.

| field | type | meaning |
|---|---|---|
| `line_id` | string | production line, e.g. `L2` |
| `shift` | string | shift label; carried, never used by the rules |
| `inspected` | integer ≥ 0 | parts inspected in the shift |
| `scrapped` | integer ≥ 0, ≤ inspected | parts scrapped in the shift |

| # | line | shift | inspected | scrapped | outcome |
|---|---|---|---:|---:|---|
| 0 | L1 | A | 480 | 12 | counted |
| 1 | L1 | B | 520 | 14 | counted |
| 2 | L2 | A | 300 | 15 | counted |
| 3 | L2 | B | 300 | 12 | counted |
| 4 | L3 | A | 250 | 10 | counted |
| 5 | L2 | C | 40 | 45 | rejected: scrapped exceeds inspected |
| 6 | L4 | A | 0 | 0 | counted (idle line) |
| 7 | L1 | C | −5 | 0 | rejected: inspected must be a non-negative integer |
| 8 | L3 | B | (missing) | 3 | rejected: missing inspected |
| 9 | L5 | A | 7 | 1 | counted |

Derivation of `expected/scrap_summary.json` (threshold 0.0400, alert when the
rate is strictly greater):

- L1: 480 + 520 = 1000 inspected, 12 + 14 = 26 scrapped; 26 / 1000 = 0.026 →
  `0.0260`; not above 0.0400.
- L2: 300 + 300 = 600, 15 + 12 = 27 (record 5 is not counted); 27 / 600 =
  0.045 → `0.0450`; above.
- L3: 250, 10 (record 8 is not counted); 10 / 250 = 0.04 → `0.0400`; equal,
  so not above.
- L4: 0, 0 → no rate (`null`), no alert.
- L5: 7, 1; 1 / 7 = 0.142857… → half up at four places `0.1429`; above.

Rows are sorted by `line_id` as text. Rejections keep their input position.

`expected/entry_point_summary.json` is the same rows and rejections wrapped
with the arguments the `test` target resolves to (`cinderline_test`,
`quality`, `0.0400`), because the runner feeds the entry point exactly those
arguments. The refusal text for `dev` is the parameter parser's message for a
schema that still contains `${workspace.current_user.short_name}`.

## fixtures/inspections_transfer.json — the altered day (15 September 2026)

| # | line | inspected | scrapped | outcome |
|---|---|---:|---:|---|
| 0 | L1 | 500 | 20 | counted |
| 1 | L1 | 500 | 21 | counted |
| 2 | L6 | 32 | 1 | counted |
| 3 | L2 | true | 2 | rejected: inspected must be a non-negative integer (a boolean is not a count) |
| 4 | L2 | 200 | "3" | rejected: scrapped must be a non-negative integer (text is not a count) |
| 5 | L4 | 0 | 0 | counted (idle line) |
| 6 | L7 | 9 | 0 | counted |

- L1: 1000, 41; 41 / 1000 = 0.041 → `0.0410`; above.
- L4: no rate, no alert.
- L6: 1 / 32 = 0.03125 exactly; half up → `0.0313` (half even would give
  `0.0312`); not above.
- L7: 0 / 9 = 0 → `0.0000`; not above.
- L2 has no row: both of its records were rejected.

## fixtures/bundle_mutations.json — 21 changes to the reviewed configuration

Each entry names the file (`databricks.yml` or `resources/scrap_job.yml`), an
operation (`set`, `delete`, `append`), a path of keys and list indices, and a
value. `expected/bundle_findings.json` lists, for each, the rule and location
that must fire; they were written from the rule definitions in
`bundlecheck.py`'s `RULES` table, one mutation at a time, before the checker
first ran. The reviewed configuration itself must produce no finding.

## fixtures/broken_blocks.md — two syntax cases

A repeated `dev:` key on line 7 of a `databricks.yml` block and a tab used for
indentation on line 8 of a `resources/scrap_job.yml` block. The expected
messages in `expected/syntax_findings.json` are PyYAML's own wording for those
two errors.

## Configuration values in solutions/project/BUNDLE.md

| target | mode | catalog | schema | alert_threshold | run_as | root path |
|---|---|---|---|---|---|---|
| dev | development | cinderline_dev | quality_${workspace.current_user.short_name} | 0.0400 (default) | none | default `~/.bundle/cinderline_scrap/dev` |
| test | production | cinderline_test | quality | 0.0400 (default) | 00000000-0000-0000-0000-00000000a001 | fixed, in that principal's folder |
| prod | production | cinderline_prod | quality | 0.0400 (default) | 00000000-0000-0000-0000-00000000b001 | fixed, in that principal's folder |

`expected/resolved_targets.json` is this table written out: `${bundle.name}`
is `cinderline_scrap`, `${bundle.target}` is the target's own name, and a
target's value wins over a variable's default. The hosts end in `.example`, a
reserved domain; the principal IDs are placeholders in UUID form.

## expected/starter_findings.json and expected/starter_unit_results.json

Written from the gaps marked in `starters/`: eight findings for the starter
`BUNDLE.md` (see SOLUTIONS.md, task 2), and for the starter package six of
fourteen tests not passing: five failures from the rounding, formatting,
threshold and rejection gaps, and one error from dividing by zero for L4.

## expected/classification.json

The twelve rows of the table printed at the end of every run, with the class
and status of each step. The runner adds an evidence column computed during
the run; the tests compare every other column with this file.
