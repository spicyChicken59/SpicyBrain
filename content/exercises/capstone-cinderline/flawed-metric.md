# The defect rate as Cinderline computes it today (fictional)

Everything here is original fiction for the SpicyBrain capstone. The people,
systems, files and numbers are invented; the arithmetic is real and can be
re-derived from `quality-events.csv`.

Two definitions of "defect rate" are in use, and both are wrong in ways that
sometimes agree and sometimes disagree. Neither is malicious. Both survived
because on a clean night they produce nearly the same number.

## Definition A: the analyst workbook (S06)

For each row of the nightly reporting extract (S03) the workbook computes
`rate = defective_units / inspected_units`, then reports, per plant and
**load date**, the **average of the row rates** over rows whose
`inspected_units` is greater than zero. In spreadsheet terms it is an
average-if over a rate column with the condition "inspected > 0".

What the extract contains matters more than the formula:

- A package retry re-sends rows it had already delivered, so the same
  inspection appears more than once. The extract has no event identity, so
  the workbook cannot tell a re-delivery from a second inspection.
- Corrections from the file share (S04) are appended as new rows. The
  superseded revision stays, so both A version 1 and A version 2 are averaged.
- Rows with a non-positive inspected quantity are silently excluded. The
  workbook never says how many rows it dropped or why.
- Grouping is by load date, so a correction loaded on the 3rd is counted
  against the 3rd, whatever day the inspection belongs to.
- A row where defective exceeds inspected produces a rate above 100%. The
  analyst notices, deletes the row by hand, and records nothing.

## Definition B: the plant sheet (S05)

The plant coordinator pastes the extract into a shared sheet each morning and
edits it. The sheet reports, per plant and **inspection date**,
`SUM(defective_units) / SUM(inspected_units)` over whatever rows are present.
Typed adjustments are added as extra rows; a negative inspected quantity has
been used to "take units back out". Pasting a corrected extract adds rows; it
never replaces them.

## Definition C: the contract (what the capstone asks you to write)

Per plant and **business day of the inspection**: total defective units over
total inspected units of **accepted** inspections, where an accepted
inspection is the highest valid approved revision of each `inspection_id`,
exact re-deliveries count once, invalid rows are quarantined and disclosed,
and a conflicting delivery blocks publication while the last verified
snapshot stays visible and is labelled stale. This is the preserved
reliable-data publication policy; the capstone guide and the pack README
restate it. The contract path also holds a plant until its delivery is
complete (the pack README states the rule). The tables below apply
Definition C to the same rows the workbook and the sheet had at each moment,
which is not always what the contract path would have published then; the
failure timeline shows that.

## Worked figures from `quality-events.csv`

### North, business day 2026-03-02 (the disputed day)

| Moment | Rows the workbook sees | Definition A | Definition B (sheet) | Definition C applied to the same rows |
|---|---|---|---|---|
| 07:30 on 3 March (extract only) | A1 10/1, A1 again 10/1, B −3/1, C 8/0 | mean(0.100, 0.100, 0.000) = **6.7%** | (1+1+1+0) / (10+10−3+8) = 3/25 = **12.0%** | A v1 10/1, C 8/0 → 1/18 = **5.6%**; B quarantined; the approved A v2 is on the share but not in these rows |
| After the 10:40 hand paste of A2 12/1 | as above plus A2 | mean(0.100, 0.100, 0.083, 0.000) = **7.1%** | 4/37 = **10.8%** | A v2 12/1, C 8/0 → 1/20 = **5.0%**; B quarantined |
| After the 11:15 manual rerun (a third copy of A1) | as above plus A1 again | mean(0.100, 0.100, 0.100, 0.083, 0.000) = **7.7%** | 5/47 = **10.6%** | unchanged: **5.0%** (an older revision cannot replace v2) |
| After Friday's approved A3 14/1 (6 March) | A3, twice (the file was re-sent), loaded with the next nightly run | **7.7%**, unchanged for load date 3 March; the two A3 rows are filed under the later load date and averaged into that night's inspections | as above plus A3 twice, if pasted: 7/75 = **9.3%** | A v3 14/1, C 8/0 → 1/22 = **4.5%**, published once; the re-send changes nothing |

Three workbook numbers and four sheet numbers for one plant and one day, and
the workbook files the day's last correction under another date altogether.
Applied to the same rows, Definition C moves only when a newer approved
revision is present (5.6% without A v2, 5.0% with it, 4.5% with A v3) and
never for a copy. The contract path, which admits a correction when it lands
and holds a plant until its delivery is complete, would have published two:
5.0% at 11:15 on 3 March, when the manual rerun completed the delivery, and
4.5% on 6 March, each carrying the time its evidence was taken. Before 11:15
it would have shown the last verified snapshot, labelled stale.

### East, business day 2026-03-02

East's rows arrived only with the 11:15 manual rerun, and the East step was
run once more at 11:40, so G was delivered twice. Friday's file corrected F;
the workbook, grouping by load date, files that correction under the next
nightly run's date, not under 3 March.

| Definition | Rows | Figure |
|---|---|---|
| A (workbook, load date 3 March) | E 20/2, F1 15/0, G 9/3, G 9/3 | mean(0.100, 0.000, 0.333, 0.333) = **19.2%**, before and after Friday |
| A (workbook, Friday's rows) | F2 15/1, F2 15/1, loaded with the next nightly run | filed under that later load date and averaged into that night's inspections, never against 2 March |
| B (sheet, after Friday) | E, F1, G, G, F2, F2 summed by inspection date | 10/83 = **12.0%** |
| C (contract, after Friday) | E 20/2, F v2 15/1, G 9/3 | 6/44 = **13.6%** (before Friday: 5/44 = 11.4%) |

### North, business day 2026-03-03 (a clean night)

A over the night's own rows J, K and L: mean(0.000, 0.111, 0.000) = **3.7%**.
B: 1/30 = **3.3%**. C: 1/30 = **3.3%**. Over its own rows a clean night gives
close answers, which is why nobody questioned the formulas. The workbook,
though, files J, K and L under load date 4 March together with the A v2 row
that the 3 March nightly run appended from the corrections file, so the
figure it actually shows is mean(0.083, 0.000, 0.111, 0.000) = **4.9%**.

### East, business day 2026-03-03 (an invalid row)

M was exported as 7 inspected, 9 defective. A (load date 4 March, M and N
only): mean(1.286, 0.083) = **68.5%**
until the analyst deletes M by hand, then **8.3%**. B: 10/19 = **52.6%** until
someone edits the sheet. C: N 12/1 = **8.3%**, with M disclosed as quarantined
(defective exceeds inspected) and its count shown beside the figure.

## Why the current definitions mislead

1. **Mean of rates.** A 9-unit inspection and a 20-unit inspection weigh the
   same, so the reported figure is not the share of inspected units that were
   defective. The question the 8 a.m. meeting asks is about units.
2. **Duplicates inflate the denominator.** Without event identity, an ETL
   retry silently changes the number.
3. **Superseded revisions stay in the population.** A correction adds a row
   instead of replacing a state, so the figure moves in the wrong direction
   for the wrong reason.
4. **Silent exclusion.** The negative quantity in B and the impossible
   quantity in M disappear or get deleted by hand. The contract quarantines
   and discloses them; the workbook hides them.
5. **Load date is not business day.** A correction for the 2nd is counted
   against whichever day it happened to be loaded.
6. **No freshness statement.** The board shows when it refreshed, not which
   deliveries its number rests on, so a stale number looks current.
7. **No publication decision.** Nothing can say "do not trust this figure
   today"; there is only a number.

## What this document is not

It is not a claim about any real product, and it does not say that the
workbook's author is at fault. It shows why a metric contract must name grain,
denominator, exclusions, time boundary, restatement, freshness and staleness
before any platform is chosen.
