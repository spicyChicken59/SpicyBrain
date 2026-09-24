# Builder editorial review — Databricks: Build, Explain, Deliver

**Builder editorial review, not an independent human learner study.** For each of the eight tracks, and separately for the 32 field guides, the eight case analyses with the crosswalk, and the three capstones, one builder agent read the material in learning order as a skeptical learner, worked every example and recomputed the arithmetic, and altered at least one example to test whether the explanation transfers. A second builder agent reproduced each high and medium finding against the files before changing anything, applied the confirmed ones, recorded the rejected ones with a reason, and re-ran `academy-check` on every module it touched. No learner took part. The summaries below are the editors' own records, lightly normalized: headings nested and build-session scratch paths replaced.

Every change is in this pull request. Retained identities keep their ids; a change of assessed meaning moved the revision and is listed in [`DISPOSITION.json`](DISPOSITION.json) (`academy-disposition.py --check` reports no revision left unmoved).

## Contents

- [Platform and working fluency](#platform-and-working-fluency)
- [Reliable data engineering](#reliable-data-engineering)
- [Analytics, performance and economics](#analytics-performance-and-economics)
- [Governance and cloud architecture](#governance-and-cloud-architecture)
- [Machine learning and production evaluation](#machine-learning-and-production-evaluation)
- [GenAI, agents and applications](#genai-agents-and-applications)
- [Architecture, migration and operations](#architecture-migration-and-operations)
- [Customer discovery, evidence and delivery](#customer-discovery-evidence-and-delivery)
- [Field guides FG01–FG16](#field-guides-fg01fg16)
- [Field guides FG17–FG32](#field-guides-fg17fg32)
- [Case analyses and crosswalk](#case-analyses-and-crosswalk)
- [Capstones](#capstones)
- [Course-level fixes](#course-level-fixes)

## Platform and working fluency

**What this is.** A builder editorial review: one reviewer worked every module by execution and altered its examples, then an editor checked each finding against the files and fixed what held up. It is **not** an independent study of human learners. No learner took part, and nothing here measures learning outcomes.

#### Sequence worked

The reviewer worked the modules in track order:

1. A1 `dbxfe-m03`
2. A2 `dbxfe-python`
3. A3 `dbxfe-transformations`
4. A4 `dbxfe-spark-execution`
5. A5 `dbxfe-delivery`
6. A6 `dbxfe-ai-assist`

For every beat they read the explanation, each visual state, the check or self-check, the Samajh, the hint and the handbook. They also read the card links, extension cards, recap, applied task, lessons (JSON and Markdown) and scenario.

Execution evidence from the reviewer:

| Evidence | Result |
|---|---|
| Lab L01 on CPython 3.12.3 | 36/36; 14/14 mutants caught |
| Lab L04 on PySpark 4.0.4 with OpenJDK 21 | 14/14 |
| Lab L16 | 16/16 |
| Python REPL outputs in the Python module | all reproduced |
| Spark lesson blocks (m04-l01, dataframes, grain-joins) | all ran with their asserts |
| AI-assist fixture queries in SQLite | all reproduced |
| Delivery claims | checked against the Databricks CLI v1.17.0 source and changelog, and databricks-sdk 0.141.0 |

The editor then re-ran the evidence behind each finding they applied:

- **Python 3.12.3:**
  - `12 == 12.0`, `True == 1`, `len({1, True})` and `{(True,), (1,)}`.
  - The bridge's `units()` on `"-3"`, `-3`, `"²"` and `"+4"`.
- **Lab L01:** `expected/primary.json` reason counts sum to 19.
- **SQLite:** the AI-assist fixture queries, including both half-fixes.
- **PySpark 4.0.4 on OpenJDK 21, local[2]:**
  - `QUALIFY` raises `ParseException`.
  - With a 40-row join side and adaptive execution at its defaults, the plan printed before the action shows `SortMergeJoin` under `isFinalPlan=false`.
  - After the action the final plan shows `BroadcastHashJoin BuildRight`, with `AQEShuffleRead local` under both inputs.
- **Lab L16 `summarize_scrap`:** 4001/100000 gives `0.0400` and no alert; 4005/100000 gives `0.0401` and an alert; 10/250 gives `0.0400` and no alert.
- **Lab L16 starter:** the recorded starter results confirm the threshold test fails on formatting first.

#### Altered examples

| Module | Where | Altered input | Result | Teaching holds? |
|---|---|---|---|---|
| m03 | extension card `route-priority` | add 10.2.3.0/24; destinations 10.2.3.4 / 10.2.9.9 / 10.3.0.1 | /24, /16, default route | yes |
| m03 | beat `durability` | correction changes A to 14 before restart | a fresh session reads 22; the old cell's 20 is historical | yes |
| m03 | beats `transfer`, `network` | name resolves, then the connection times out | a transport or path problem, not permissions | yes |
| python | types visual, state `compare` | `12 == 12.0`, `True == 1`, `len({1, True})` | True, True, 1 | **no, fixed** |
| python | beat `validate` | CSV row with `" 007 "` inspected, 8 defective | converts to 7, then `defective_exceeds_inspected` | yes |
| python | logging question | TM-A with TMA-009 at 26 defective | 4,5,6,7,9, then 2,3,8 | yes; rationale reworded |
| python | assert visual | stub keeps the duplicate rule and drops one record | 6 + 18 = 24; the assert still fires | yes; the visual's 9 + 15 is now explained |
| transformations | beat `weighted` | add E with 10 inspected / 0 defective | unit rate 3.33%; average of rates 2.78% | yes |
| transformations | beat `window` | add F=5 | RANK 1,2,2,4; RANGE running total 12,28,28,33 | yes |
| transformations | beat `python` (bridge) | `"-3"` as text and `-3` as an int | "must be an integer" versus "must be nonnegative" | **no, fixed** |
| transformations | beat `transfer` | 2 matching events | 6 pairs, 50/4, 8% | yes |
| spark-execution | lesson task | add East with 600 rows | one Exchange, at most 16 partials, share ≥ 0.714 | yes |
| spark-execution | beat `stage` | 8 input partitions | 8 then 4 tasks; 24 partials | yes |
| spark-execution | applied task | apply the adaptive beat to a 40-row side | expect `BroadcastHashJoin` in the final plan | **no, fixed** |
| delivery | beat `unittests` | 4001/100000 and 4005/100000 | 0.0400 no alert; 0.0401 alert | **no, fixed** |
| delivery | beat `config` | `BUNDLE_VAR_catalog` left exported | the environment variable wins | yes |
| delivery | beat `targets` | every job sets `run_as` | a recommendation, not an error | yes |
| delivery | beat `bundle` | literal include path with the wrong extension | an error | yes |
| ai-assist | beat `join` | second line on order 1003 | draft 3000/100 | yes |
| ai-assist | beat `correction` | pre-aggregate shipments only, keep the inner JOIN | 1550, not 1670 | **no, fixed** |
| ai-assist | beat `errors` | S5 as `05/09/2026` | ANSI parse error, or NULL then the check fires | yes |
| ai-assist | beat `context` | metadata visible without SELECT | names may reach the model; no data samples | **no, fixed** |

#### Findings applied

All medium findings were confirmed against the files and fixed. The low findings were applied where the edit was small and clearly correct.

**Revision and version rules followed.**

- **Retained modules** (`dbxfe-m03`, `dbxfe-transformations`): each changed beat moved to 1.1.0 with a change note.
- **New modules** (unpublished): beat versions stay at 1.0.0.
- **Assessed meaning:** one question's prompt changed, so its revision moved from 1 to 2. Rationale-only and explanation-only edits keep their revision.
- **Lesson `contentVersion`:**
  - Correction-level edits moved to 1.0.1: `dbxfe-workspace-compute`, `dbxfe-cloud-bridge`, `dbxfe-spark-execution-l01` and `dbxfe-delivery-l01`.
  - Material changes moved to 1.1.0: `dbxfe-ai-assist-l01`.

##### Medium findings (all fixed)

**1. dbxfe-python: the types visual said different types never compare equal.**

Where: `content/teaching/dbxfe/dbxfe-python.json`, visual `dbxfe-python-types-visual`, state `compare`, and beat `dbxfe-python-types`.

- The Why cell now reads "str and int: Python never casts text to a number".
- Two new rows: `12 == 12.0 → True` (numeric types compare by value) and `True == 1 → True` (bool is an int).
- The state explanation and provenance now say the two new rows were executed on the same CPython 3.12.3 during this review, not in the lab.
- The text equivalent is updated to match.
- The beat explanation now says only that text is never converted to a number (100 words).
- The handbook adds the numeric exception, including a set of payload tuples merging `(True,)` and `(1,)`.
- The recap is corrected.

**2. dbxfe-python: the scenario's per-kind breakdown summed to 18, not 19.**

Where: `content/courses/dbxfe/modules/dbxfe-python.json`, scenario `dbxfe-python-scenario`, model, section "Why records were refused".

"two negative quantities" now reads "three negative values (negative_inspected_units on CLN-005 and CLN-015, negative_defective_units on CLN-015)". The breakdown now sums to 19.

**3. dbxfe-transformations: the Python beat's handbook said domain checks decide every number.**

Where: `content/teaching/dbxfe/dbxfe-transformations.json`, beat `dbxfe-transformations-python`, handbook, and `startingAssumptions`.

- The handbook now traces `units()` as it actually runs:
  - A JSON `-3` is refused as "quantity must be nonnegative".
  - The text `"-3"` fails `isdigit()` and is refused as "quantity must be an integer".
  - `"²"` passes `isdigit()`, then `int()` refuses it with its own message.
- It names where the bridge's policy differs from the Python module's contract: that contract accepts an optional sign with ASCII digits, gives "-5" a negative_ reason, and numbers positions from 1.
- The handbook is 392 words; its code is unchanged.
- The starting assumption now points to the Python module, with the bridge as an optional, narrower refresher.
- The beat moved to 1.1.0 with a change note.

**4. dbxfe-spark-execution: the Harbourline model answer read a SortMergeJoin screenshot as the plan that ran.**

Where: `content/teaching/dbxfe/dbxfe-spark-execution.json`, `appliedTask`.

- The model answer now starts by asking which plan the screenshot is.
- A 40-row side makes a SortMergeJoin itself something to explain. Under `isFinalPlan=false` it is only the initial plan, and the final plan should show `BroadcastHashJoin` with local shuffle reads. This was verified on PySpark 4.0.4.
- If the final plan still shows SortMergeJoin, the answer finds out why first: a lowered or disabled threshold, an unmeasured size, or a join type that cannot build on the small side.
- The skewed-join-task prediction is kept, but only for a join that really shuffled.
- The broadcast hint remains the first experiment: a planned broadcast also skips the input shuffles that a runtime conversion has already paid for.
- The reasoning is updated, and `dbxfe-spark-execution-adaptive` is added to `beatIds`.

The Cinderline scenario had the same gap. Where: `content/courses/dbxfe/modules/dbxfe-spark-execution.json`, scenario `dbxfe-spark-execution-scenario`.

- "What the plan proves" now starts with the same final-plan check.
- The runtime evidence now names `isFinalPlan` and the join operator.
- Rubric-1 "strong" now includes checking the final plan.

**5. dbxfe-ai-assist: "a table you cannot SELECT contributes nothing" overclaimed the sources.**

Where, in `content/teaching/dbxfe/dbxfe-ai-assist.json`:

- The concept `dbxfe-ai-assist-permission-concept`, example: no privilege means no metadata or samples; visible without SELECT means no data samples.
- The beat `dbxfe-ai-assist-context`:
  - Explanation: without SELECT no data samples are sent; a table with no privilege contributes nothing.
  - Handbook: separates metadata visibility from data reading (ownership, or BROWSE where enabled), pointing to the governance module's privileges reference.
- The visual state `ungranted`: title, explanation and the shipments node now say "no privilege at all"; the text equivalent is updated.
- The question `dbxfe-ai-assist-context-question`: the stem now says "holds no privilege of any kind, not even to see its metadata", so option a is unambiguously right. Its **revision moved from 1 to 2**, and the option a rationale is updated.

Where, in the lesson `content/courses/dbxfe/lessons/dbxfe-ai-assist-l01`:

- `.md`, section `dbxfe-ai-assist-l01-context`: the same correction.
- `.json`, question q2: the option c rationale now says the table's *data* is excluded, not the table entirely. Its revision is kept.

**6. dbxfe-ai-assist: pre-aggregating shipments alone does not make revenue 1670.**

With the draft's inner join, revenue reads 1550 (reproduced in SQLite). It reaches 1670 only once the join is also a LEFT JOIN. Both routes leave Amberline's quantity at 38.

Where:

- The beat `dbxfe-ai-assist-correction`, handbook, in the teaching file.
- `content/courses/dbxfe/modules/dbxfe-ai-assist.json`:
  - The scenario's first disclosure response.
  - Rubric-3 "partial": the finding named rubric-2, but the half-fix wording is in rubric-3.
- The lesson card `dbxfe-ai-assist-l01-card8`: explanation only, so its revision is kept.

##### Low findings applied

**dbxfe-python: the assert visual's 9 + 15 did not follow from "drops the last accepted record".**

Where: visual `dbxfe-python-assert-visual`, nodes `lossy` and `landed` in both states, plus the text equivalent and the beat `dbxfe-python-assert` handbook.

The visual and handbook now say the stub skips the duplicate rule and returns 9 of the 10 records that passed the field checks. So 9 + 15 field rejections = 24. The correct step would turn those 10 records into 7 accepted and 3 duplicate rejections.

**dbxfe-python: the logging question's rationale said only "field rejections" are logged while reading.**

This came from an altered example rather than the findings list. The rationale for option a now says "every validate() rejection, field or cross-field". Its revision is kept.

**dbxfe-transformations: the same inspection IDs meant different records in different beats.**

In the plan visual's `before` state, the South rows D5 and E7 are relabelled P5 and Q7, and the text equivalent matches. The beat `dbxfe-transformations-plan` moved to 1.1.0.

**dbxfe-transformations: the window handbook's filtering advice had no scope.**

The advice is now scoped to the pinned Spark 4.0.4, where `QUALIFY` raises `ParseException` (reproduced). It also notes that Databricks SQL documents `QUALIFY`, and says to check the target runtime. The beat `dbxfe-transformations-window` moved to 1.1.0.

**dbxfe-spark-execution: the hot-key "floor" ignored adaptive skew-join splitting.**

The beat `dbxfe-spark-execution-skew` recap and Samajh boundary now qualify it: "under hash partitioning", and "unless adaptive skew-join handling splits that join partition".

**dbxfe-spark-execution: broadcast was described as copied to every task.**

It is now described as collected on the driver and shipped once per executor, where tasks share it. The driver and executor memory limit is stated. Where:

- The concept `dbxfe-spark-execution-broadcast-concept`, definition.
- The beat `dbxfe-spark-execution-broadcast`: explanation, handbook "When not", and the Samajh mapping and boundary.
- The broadcast visual state explanation, the `dim` node and the text equivalent.
- The question `dbxfe-spark-execution-broadcast-question`, option b rationale.
- The lesson `dbxfe-spark-execution-l01`: card7's explanation and one sentence in the `.md`.

**dbxfe-delivery: the alert rule did not say it compares the rounded rate.**

Where: visual `dbxfe-delivery-unittests-visual`, state `expected`, plus the text equivalent and the beat `dbxfe-delivery-unittests` handbook.

The rule now reads "the rounded rate is strictly above 0.0400". The handbook adds the executed boundary pair: 4001/100000 gives 0.0400 and no alert; 4005/100000 gives 0.0401 and an alert.

**dbxfe-delivery: the starter's threshold test failed on formatting, masking the `>=` gap.**

Where: the same visual, state `starter`, row "rate equal to threshold", plus the handbook.

The row now says the `>=` gap shows only once rounding is fixed. The handbook no longer claims the starter "fails exactly these". It says one failure can hide another.

**dbxfe-delivery and dbxfe-ai-assist: both assumed governance-track material that the platform track never teaches.**

Short definitions and "optional prior reading" pointers were added:

- `dbxfe-delivery`: `startingAssumptions` and `dbxfe-delivery-l01.md`, section `dbxfe-delivery-l01-start` (user, group, service principal).
- `dbxfe-ai-assist`: `startingAssumptions` and `dbxfe-ai-assist-l01.md`, section `dbxfe-ai-assist-l01-start` (principal, SELECT).

**dbxfe-ai-assist: the AGENTS.md / CLAUDE.md claim was stated as settled for any cloud.**

It now carries a hedge: "the Google Cloud custom-instructions page, as previously read (only its title and snippet were re-confirmed)", plus "confirm for your cloud and release". Where:

- The beat `dbxfe-ai-assist-context`, handbook.
- The extension card `dbxfe-ai-assist-extension-instructions`, explanation only, so its revision is kept.
- The lesson's context section.

**dbxfe-m03: the library Samajh merged the requester and the worker.**

The beat `dbxfe-m03-responsibilities` Samajh boundary now says the person who asks, the identity that is checked and the compute that reads are separate, and that a scheduled job may run as a service principal. The beat moved to 1.1.0.

**dbxfe-m03: two code-free lessons implied their own code had been executed.**

Where: `dbxfe-workspace-compute.md` and `dbxfe-cloud-bridge.md`, their `foundation-sources` sections.

Both now say the lesson shows no executable code. They say the bundle's 30-test run covers the Python bridge, DataFrame, grain-and-join and later reliable-data lessons, not this one. Their `contentVersion` moved to 1.0.1.

#### Findings rejected, fully or in part

- **dbxfe-m03, the review-date part of the boilerplate finding.** Rejected. The "read on 19 September 2026" date matches these lessons' own course sources, whose `reviewDate` is 2026-09-19. The 2026-09-20 date belongs to a different source set, the m03 teaching sources.
- **dbxfe-transformations, rewriting `units()` or replacing the beat.** Not taken. The code is the preserved bridge, and it is byte-identical to the downloadable exercise's executed `lesson_examples`. Changing it would break that fidelity. The prose was corrected to match the code instead.
- **dbxfe-spark-execution, card8.** Not changed. Its explanation describes `repartition(n, "plant")`, where the hash does keep all 180 North rows in one partition, so it is accurate as written.
- **dbxfe-spark-execution, option a's text** ("each fact task receives a copy"). Not changed. Tasks do read the executor-shared copy, and editing the option text would change the assessed option. Only the rationales were clarified.
- **dbxfe-delivery, the question stem and a new unit test for 0.04001.** The stem is unchanged, because L6's answer does not depend on it; the rounded-rate rule is now stated in the visual and the handbook. A new test in the lab package is out of scope for this pass: lab files are not module files. The boundary pair was executed and added to the handbook instead.

#### Strengths the review found, kept as they are

- **Numbers survive execution.** All three labs pass. Every REPL output reproduces. The Spark lesson blocks are byte-identical to the executed examples. The fixture arithmetic reproduces.
- **Visual states are arithmetically closed.** The partition, shuffle, salt and join tables reconcile; the Spark tables sum to 240.
- **The delivery module is exceptionally well grounded.** Every CLI behaviour checked matches the pinned v1.17.0 source, and the SDK call matches databricks-sdk 0.141.0.
- **Evidence honesty is consistent.** Workspace states are marked NOT RUN. Assistant output is labelled "authored". Local runs are never presented as benchmarks. Source records say when a page body was not fetched.
- **Checks are well built.** Distractors are plausible misconceptions with mechanism-naming rationales. The altered-input tasks force recomputation rather than recall.
- **Good cross-module threads:**
  - grain and fan-out, from A3's joins into A6's many-to-many correction;
  - the window function, from A3 into A6's price-list task;
  - independent expected values, in A2, A3, A5 and A6;
  - plan versus evidence, from A1 into A4.
- **Samajh analogies are mostly well matched, with honest limits.**

#### Gates run after the edits

- **`node --import tsx scripts/academy-check.ts --module <id>`:** PASS (no failing findings) for all six modules.
- **`python3 scripts/academy-disposition.py --check`:** exit 0. Removed 0, revisionNotMoved 0. It regenerated `docs/academy/DISPOSITION.json`.
- **`node --import tsx scripts/content.ts`** (validate only, no build): exit 0.
- **JSON parse check:** all 14 JSON files written parse. `course.json` and `modules/dbxfe-delivery.json` are unchanged.

#### What remains a limitation

- **No independent human learner study.** Nothing here measures comprehension or learning outcomes.
- **Changed visual states were not rendered in a browser.**
  - The types table, assert nodes, plan labels, broadcast state, unit-test rows and context state are validated for schema and text equivalents only.
  - The phone and desktop capture (VISUAL-REVIEW) should be re-run for these states.
  - Generated files, including `src/generated/search.json`, were not rebuilt here. `prepare:content` was not run, to avoid clobbering concurrent agents; the ordinary content build will pick up the changes.
- **The disposition script cannot see section body changes in retained lessons.**
  - `lesson_family()` resolves `<lesson dir>/<bodyFile>`, but `bodyFile` already starts with `lessons/`. Every section is therefore compared as empty, and zero sections are reported revised across all 16 retained modules.
  - The m03 lesson edits are recorded only through the manual `contentVersion` bumps.
  - This is a defect in `scripts/`, which is outside this assignment, and is left for the engine owner.
- **The window beat's bump is precautionary.** `dbxfe-transformations-window` is new in this release relative to the disposition base, so its move to 1.1.0 protects no published completion.
- **Documentation-host claims remain at search level.**
  - Genie Code context, instructions and trust are unchanged in substance, with stronger hedges.
  - The BROWSE statement relies on the governance module's privileges reference (reviewed 2026-09-20), not a re-fetch.
  - Databricks SQL's `QUALIFY` support is stated from documentation knowledge and was not verified here.
- **The broadcast internals were not demonstrated.** "Collected on the driver, one copy per executor" follows Spark's implementation. A local[2] run cannot show it, because the driver and executor share one JVM.
- **The spark-execution applied answer and scenario model are longer.** The applied answer is now 345 words and the scenario model 442; no floor or ceiling applies to either.

## Reliable data engineering

**Builder editorial review.** This is not an independent human learner study. A builder reviewer read the track as a learner would and reported findings. An editor (this pass) checked each high and medium finding against the files, ran code where a claim could be run, and edited only the files of the six modules.

Modules, in track order: B1 `dbxfe-delta`, B2 `dbxfe-delta-writes`, B3 `dbxfe-m04`, B4 `dbxfe-streaming`, B5 `dbxfe-pipelines`, B6 `dbxfe-orchestration`.

#### How the review was done

The reviewer read the six modules in track order. For each beat that meant:

- the explanation;
- every visual state and its text equivalent;
- the check with its options and rationales, or the self-check with its model answer;
- the Samajh, the hint and the handbook.

After the beats came the card links, extension cards, recap, applied task, concepts, claims and sources. The reviewer also read the lessons each module lists:

- `dbxfe-m03-l02`
- `dbxfe-delta-writes-l01`
- `dbxfe-m04-l02`
- `dbxfe-record-resolution`
- `dbxfe-versioned-updates`
- `dbxfe-streaming-l01`
- `dbxfe-pipelines-l01`
- `dbxfe-m04-l03`

Scenarios read: `dbxfe-m04-scenario`, plus the scenarios in the delta-writes, streaming and pipelines module packages. The reviewer recomputed every worked number from the lab fixtures (L05, L07, L08 and reliable-data), not from the lesson text.

**Code the reviewer ran:**

- the versioned-updates `apply_resolved` block;
- the `LocalPipeline` driver used by `dbxfe-m04-l03` and orchestration, including an altered correction and a later conflict;
- `reconcile_orders`, which returned 1300 cents;
- the lab L08 streaming query on PySpark 4.0.4 with Java 21, both as sequential `availableNow` runs and as a backlog run;
- open-source Delta 4.0.0 checks: MERGE star actions, `withSchemaEvolution()`, OPTIMIZE errors, the change-feed operation name and the protocol upgrade.

**Code the editor ran in this pass,** before changing any text:

- **Delta 4.0.0 on Spark 4.0.4, with `spark.databricks.delta.schema.autoMerge.enabled` unset:**
  - A plain MERGE with `whenMatchedUpdateAll().whenNotMatchedInsertAll()` ignored an extra source column.
  - The same MERGE with `.withSchemaEvolution()` added the column.
  - SQL `MERGE WITH SCHEMA EVOLUTION INTO ...` parsed and merged the rows (A to 2/12/1, C inserted) but added no column. This is new evidence the reviewer did not report.
- **Change data feed:** enabling it moved the table from protocol (1,2) with `[appendOnly, invariants]` to (1,7) with `[appendOnly, changeDataFeed, invariants]`.
- **OPTIMIZE on Delta 4.0.0:**
  - `WHERE inspected_on ...` on an unpartitioned table fails with `DELTA_NON_PARTITION_COLUMN_REFERENCE`.
  - The same statement succeeds on a table partitioned by `inspected_on`.
  - `ZORDER BY (plant)` on a table partitioned by plant fails with `DELTA_ZORDERING_ON_PARTITION_COLUMN`.
  - The same statement succeeds on an unpartitioned table.
- **L07 rows read as JSON on Spark 4.0.4:**
  - With `seq INT` declared, e-09's `"2"` becomes NULL. `seq > 0` gives NULL and `seq IS NOT NULL AND seq > 0` gives false.
  - With the schema inferred, `seq` is a string and `"2" > 0` is true (ANSI on).
- **Lab L09's `resolve_rows`,** on lot L-101 with a valid v1 of 42/2 and a v2 whose `inspected` is null: it published v1 as 42/2, excluded v2 as invalid and reported no conflict.
- **Fixtures read to confirm batch placement:**
  - L07: e-04 is in batch 1, e-08 and e-09 in batch 2, e-15 in batch 3.
  - L08: L1's 09:00-09:10 events are e001 and e003 (landed 09:13), e007 (09:19) and e011 (09:28). Sink calls: batches 3, 5, 7, 7 (replay) and 9. Outboxes: naive 4 → 7 → 10 → 10 → 12, keyed 4 → 7 → 7 → 7 → 9.
  - L05: v0 wrote A at 10/1 revision 1, v1 appended C, v2 ran an UPDATE that set A to 12 and left revision 1, and v3 enabled the change data feed.

#### Altered examples

The reviewer changed one input in each example and recomputed the answer by hand. Three of the eighteen did not hold, and each became a finding that is now fixed.

| Module | Where | Change | Result | Teaching holds |
|---|---|---|---|---|
| delta | folder beat | A0=7, A1=15, C=4 | v0 11, physical 26, v1 19 | yes |
| delta | transfer beat | C1=11, failure then retry | 20, then 23 (31 or 11 if miscounted) | yes |
| delta | meaning beat | A0, A1 and C all committed | 30/2 = 6.67% against 20/1 = 5% | yes |
| delta-writes | scope beat | West snapshot lists W1 only | scoped delete removes 2 rows, unscoped removes 4 | yes |
| delta-writes | guard beat | source A rev 2, D rev 1, E rev 1 | 1 updated, 1 inserted | yes |
| delta-writes | vacuum beat | files replaced day 3; reads on day 9 and day 11 | day 9 read succeeds, day 11 read fails | yes |
| delta-writes | feed and features beats | supplier writes with Delta 2.1 after the feed is enabled | the module predicted the write works; it fails | **no → F4, fixed** |
| m04 | quality beat | add ev5 C/2 = 6/0 | 18/1 = 5.56% | yes |
| m04 | latest beat | A/3 = 5 inspected, 6 defective | A unresolved; publication blocked; 20/1 stays stale_previous | yes |
| m04 | publication beat | A3 = 9/2 plus an unkeyed conflict | candidate 17/2 blocked; 20/1 stays stale_previous | yes |
| streaming | watermark and late beats | 10-minute delay | e011 counted; 09:00 L1 = 36 | yes |
| streaming | applied task | e019 at 09:41:30 | counted; batch 11 emits three windows | yes |
| streaming | replay and sink visuals | sink fails in batch 5 instead | the visuals showed end-of-run totals at the replay | **no → F2, fixed** |
| pipelines | type 1, type 2, late beats | P-200 delete at seq 3, late upsert at seq 2 | no current row; two closed intervals | yes |
| pipelines | snapshots beat | lose snapshot 3 | SUP-B's return to 7 never seen | yes |
| pipelines | scenario model | the scenario's own incremental design | P-400 still at 90 and P-300 at 830 | **no → F1, fixed** |
| orchestration | transfer beat | O7/L1 rev 2 qty 4; replay of O7/L2 rev 1 | 1600 cents; the line stays cancelled | yes |
| orchestration | failure beats and applied task | A3 = 16/2, then a conflicting payload | 24/2, outbox 2, then 24/2 kept as stale_previous | yes (executed) |

#### Findings applied

Versions and revisions follow `docs/AUTHORING.md`:

- In the retained modules (delta, m04, orchestration), a beat whose teaching changed moved from 1.0.0 to 1.1.0 and carries a change note. A lesson whose sections changed has a new `contentVersion`.
- In the new modules (delta-writes, streaming, pipelines), versions stay at 1.0.0.
- One lesson card's answer changed, so its revision moved from 1 to 2.
- No id was removed or renamed.

##### F1 (high): pipelines, an incremental AUTO CDC target cannot un-publish a key

Confirmed from the L07 fixture. e-04 applies P-400 at 90 in batch 1 and e-09 arrives in batch 2. e-08 applies P-300 at 830 in batch 2, and the tie with e-15 appears in batch 3. The fixture's own notes say an incremental maintainer "must ... withdraw a key it had published".

- **Scenario `dbxfe-pipelines-scenario`** (`content/courses/dbxfe/modules/dbxfe-pipelines.json`):
  - The model's Graph section now has `part_events_clean` drop rows at a tied part and sequence. That keeps the AUTO CDC input within its one-update-per-sequence contract, and the model says plainly that this filter cannot take back a part already applied.
  - A new materialized view, `part_withheld`, is recomputed each update from `part_ties` and `part_quarantine`.
  - Finance reads `part_current_published` and `part_history_published`, which anti-join the AUTO CDC targets with `part_withheld`. The lab's alternative is named: rebuild both SCD tables from retained valid history on every update.
  - The Expectations section now routes `has_part` to quarantine (low finding). The model's reasoning, and the partial and strong levels of rubric 2, are rewritten to match. Ids are unchanged.
- **Applied task** (teaching `appliedTask.modelAnswer` and `reasoning`): the same correction for gauges. A blank `gauge_id` now goes to quarantine instead of failing the update (low finding).
- **Row-rules beat handbook and recap:** the handbook says L07 gates only because it recomputes everything. With incremental flows, P-300 stays at 830 and P-400 at 90. The two ways that do work are given.
- **Unplaceable and AUTO CDC beat handbooks:** one sentence each saying that routing a row out does not withhold its key.
- **Module outcome 2:** reworded to "gates what the SCD tables publish".
- **Lesson `dbxfe-pipelines-l01`:** a new bullet in the mistakes section.
- **Option not used:** the reviewer also suggested emitting a withhold or delete event into the CDC source. It was not used. In type 2 history it would record a deletion that never happened. It would also need a sequence above the withheld state, which is exactly what a tie or an unparseable sequence lacks.

##### F2 (medium): streaming, the replay visuals showed end-of-run totals

- **Visual `dbxfe-streaming-replay-visual`:** the "Batch 7 replayed" node now shows 10 messages (naive) and 7 (keyed). The commit node adds that batch 9's two 09:30 windows bring the totals to 12 and 9 by the end of the run.
- **Visual `dbxfe-streaming-sink-visual`, replayed state:** the keyed table shows 7 rows, the naive outbox 10 and the keyed outbox 7. Each node detail gives the end-of-run value (9, 12 for 9 windows, 9).
- **Sink handbook:** now gives both the counts right after the replay and the end-of-run counts.
- Text equivalents are updated for both visuals.

##### F3 (medium): delta-writes, schema evolution scoped to one MERGE

- **Evolution beat:**
  - The handbook now lists four switches, adds a `withSchemaEvolution()` code line, and explains that the 4.0.0 guide page lags the API.
  - The handbook also gives the executed results: the plain MERGE ignored the column, `withSchemaEvolution()` added it, and the SQL `MERGE WITH SCHEMA EVOLUTION` added none.
  - The switches table has a new row, "withSchemaEvolution() on a MERGE (Delta 3.2+)". The state title is now "Four ways to add a column".
  - The explanation mentions "one MERGE's option".
- **Self-check `dbxfe-delta-writes-evolution-self`:** its reasoning (not its model answer) now accepts `withSchemaEvolution()`, so the revision is unchanged.
- **Enforcement beat handbook:** the "MERGE is different" sentence now names both the session setting and the builder method. The enforcement check stays correct as written and is unchanged.
- **New source and claim:**
  - Source `dbxfe-delta-writes-source-merge-api`: the delta-spark 4.0.0 `delta/tables.py`, read locally in the installed wheel.
  - Claim `dbxfe-delta-writes-claim-merge-evolution`, cited by the evolution and enforcement beats.

##### F4 (medium): delta-writes, which writers the change data feed locks out

- **Feed beat handbook, Protocol paragraph:** keeps the feed page's cut-off (Delta 1.2.1). It adds that writer version 7 needs table-feature support, which the compatibility table dates to Delta 2.3.0, so writers on Delta 2.0 to 2.2 cannot write either. The beat now also cites `dbxfe-delta-writes-claim-features`.
- **Features beat handbook:** adds "table-feature support (Delta 2.3.0 or later)".
- **Visual `dbxfe-delta-writes-features-visual`, matrix state:** the change-data-feed row now reads "writers without table features (before Delta 2.3.0) cannot write". The text equivalent is updated.

##### F5 (medium): delta-writes assumed policy that the track teaches later

- `startingAssumptions[1]` now says the policy is stated here and developed in the ingestion module that follows.
- `optionalBridgeLessonIds` gains `dbxfe-versioned-updates` and `dbxfe-m04-l02`.
- The guard beat's handbook says where the versioned-updates lesson sits in the track.
- The start section of lesson `dbxfe-delta-writes-l01` says the same and suggests reading that lesson first.
- The track order in `course.json` is not changed.

##### F6 (medium): delta-writes, A's correction is revision 1 here and revision 2 elsewhere

- **Fixed by explanation.** The clauses beat's handbook has a new paragraph, "Where versions 0 to 3 came from". It says what versions 0 to 3 were and that version 2 was an in-place UPDATE that kept revision 1. It adds that this is a data fix, not how a source correction should arrive, because the guard trusts only revisions that grow.
- The first state of the clauses visual notes the in-place fix.
- The start section of lesson `dbxfe-delta-writes-l01` says the same.
- This also fixes the low finding that the absent and delete beats never said what versions 0 to 2 were.
- **Not done:** changing the lab to write revision 2 (see Limitations).

##### F7 (medium): orchestration, lab L09 resolves more simply than B3

- The transfer beat's handbook has a new paragraph describing L09's simpler contract: highest valid version wins, and invalid rows are removed before selection.
- It gives the executed L-101 counter-example: L09 publishes 42/2, while the ingestion gate marks L-101 unresolved and blocks the report.
- It notes that the lab's own notes attribute these rules to the ingestion module, and says to use L09 for boundaries, run ids, effect keys and freshness only.
- Beat version 1.0.0 → 1.1.0. The lab-side changes are recorded under Limitations.

##### F8 (medium): delta, labels such as A2 and C1 meant two different things

- **Meaning beat handbook:** "A revision 2 (file A1) has 12 inspected and 1 defective; C revision 1 (file C) has 8 and 0".
- **Schema beat handbook:** the labels are spelled out as "A revision 2 = (12, 1)" and "B revision 1 = (-3, 1)".
- **Concurrency visual:** the second writer's file is now `A1b=14`, "Also prepares a replacement of A0". The text equivalent is updated.
- The meaning, schema and concurrent beats are each at 1.1.0 with a change note.

##### Low findings applied

| Finding | Change |
|---|---|
| Streaming clock explanation named the wrong events | Clock handbook now reads: e001 and e003 landed 09:13, e007 09:19, e011 09:28. Option b's rationale in `dbxfe-streaming-clock-question` names all four events; the rationale is clarified and the revision kept. The answer on card `dbxfe-streaming-l01-card3` now says 09:13, 09:19 and 09:28; revision 1 → 2. |
| "Scenario S" undefined in the streaming applied task | The prompt now reads "The lab's one-file-per-run sequence (scenario S in the lesson)". |
| delta-writes OPTIMIZE block could not run on one table | Each line is annotated with the table it needs. A sentence cites both executed error codes and says the lab ran only the first line. |
| delta-writes VACUUM Samajh | The analogy now uses "kal ka akhbaar ... Dadi abhi bhi padh rahi hain", mapped to a reader of an older snapshot. |
| pipelines graph used Lakeflow-only constructs | A handbook paragraph says the worked graph is a Lakeflow pipeline. Under spark-pipelines those nodes become an explicit filter and window-function tables, and the cycle answer does not change. The question is unchanged. |
| pipelines expectations rule mismatch | The SQL is now `CONSTRAINT placeable_seq EXPECT (seq IS NOT NULL AND seq > 0) ON VIOLATION DROP ROW`. The warn default is explained generically, and the type caveat (INT gives NULL, string passes) was executed. |
| pipelines snippets missing imports | The AUTO CDC Python block imports `dp`, `expr` and `struct`; the ties Python line imports `struct`. |
| `part_events` used for two different tables | The joined table in the refresh beat's handbook, visual (4 rows plus text equivalent) and question prompt is now `part_events_named`. The rename is cosmetic, so the question revision is kept. |
| pipelines "fail" justified by a reason drop also meets | Fixed with F1 in the scenario and the applied task. |
| m04 transfer pointed to "the next module" | Now names the orchestration module (B6). `dbxfe-m04-transfer` 1.0.0 → 1.1.0. |
| delta checkpoint extension card pointed to orchestration | Now points to the streaming module's checkpoint beat, recapped in orchestration. The explanation is clarified; revision kept. |
| Empty "For more practice" list | `dbxfe-orchestration.scenarioIds` = `dbxfe-m04-scenario`; `dbxfe-delta.scenarioIds` = `dbxfe-m03-scenario` (the scenario `course.json` maps to each). |
| Stale "passed 30 tests" statement | Now cites the bundle's execution.json (no failures or skips; Python 3.12.14, Spark 4.0.4, Java 17.0.20.1+1) without a count. `dbxfe-m03-l02` also says it displays no code. contentVersion: `dbxfe-m03-l02` 2.0.1 → 2.0.2, `dbxfe-m04-l03` 2.0.1 → 2.0.2, `dbxfe-m04-l02` 2.0.0 → 2.0.1, `dbxfe-versioned-updates` 1.0.0 → 1.0.1. |

#### Findings rejected or only partly applied

No finding was rejected on its merits. Two were fixed only on the module side, because the rest lies outside the files this pass may edit:

- **F6, changing the lab.** The option of having lab L05 write A's correction as revision 2 would change `content/exercises/lab-l05-delta-snapshots` (the solution, the expected snapshots and the bundle). The explanation option was applied instead.
- **F7, the lab side.** The "come from the ingestion module" wording remains in lab L09's `DATA.md`, `README.md`, `solutions/pipeline.py` docstring and `content/courses/dbxfe/labs/lab-l09-failure-recovery.md`. None of these files could be edited in this pass. B6 now states the difference.

#### Checks run after editing

- `node --import tsx scripts/academy-check.ts --module <id>`: **PASS (no failing findings)** for all six modules. The only warnings are ones that existed before: stakeholder disclosures, a thin rationale, short prompts.
- Word counts:
  - Every explanation in the six modules is 100 words or fewer. The one edited explanation, the delta-writes evolution beat, is 77 words.
  - Every handbook stays within 120-400 words. The longest edited one is the delta-writes clauses beat at 392.
- `python3 scripts/academy-disposition.py --check`: **exit 0** (0 removed, 0 revision-not-moved). It rewrote `docs/academy/DISPOSITION.json`.
- Whole-course `node --import tsx scripts/academy-check.ts`: **PASS: academy contract satisfied**.
- `node --import tsx scripts/content.ts` (content validation, read-only): passed.
- `node --import tsx --test tests/teaching-content.test.ts`: 57/57. `tests/content.test.ts`: 28/28.
- Every JSON file written parses, and each was re-serialized in its original format (indent and ASCII escaping).

#### Strengths the review confirmed

- **Streaming numbers.** All of them reproduce by execution on PySpark 4.0.4: batch ids, watermarks, emitted windows, the dropped e011, backlog 36/4, the sliding windows and the landing-time table. The late-row rule is explained, observed, and kept separate from the documented guarantee.
- **Delta-writes MERGE sequence.** It is exact and was executed against lab L05. The absent-key versus scoped-snapshot distinction and the duplicate-match refusal are well taught.
- **Pipelines SCD tables.** The type 1 and type 2 tables, late restatement, ties, snapshot comparison, and the release boundaries of the editions beat all check out against L07 and the tagged Spark sources.
- **m04 publication gate.** "Max observed, then validate" and the unkeyed-conflict gate agree across checks, visuals and handbooks, and its code is identical to the bundle.
- **Orchestration.** The boundary ledger and the snapshot-keyed outbox are precise and honestly limited.
- **Evidence labelling.** Local runs, platform-only features and synthetic data are labelled claim by claim.
- **Distractors.** Each wrong option names a specific misconception.

#### Remaining limitations

- **Lab L05 still writes A's correction as revision 1.** B2 now explains this, but the lab and B1/B3 still differ.
- **Lab L09's own files still describe its simpler contract** as coming from the ingestion module. Only B6 corrects the learner.
- **Pipelines SDP and Lakeflow code is not executed.** That includes the new AUTO CDC imports, `placeable_seq` and the withheld-keys design. Open-source Spark 4.0.4 has no `pyspark.pipelines`. The corrected scenario design (the anti-join views) is reasoned from the lab data and the documented incremental semantics, not run on a workspace.
- **The `withSchemaEvolution()` and SQL `MERGE WITH SCHEMA EVOLUTION` results cover open-source Delta 4.0.0 on one local Spark 4.0.4.** Databricks runtimes document their own MERGE evolution syntax, and it was not checked.
- **The Delta 2.3.0 writer cut-off comes from the 4.0.0 compatibility table.** It was not tested by running Delta 2.0-2.2 clients.
- **`delta.enableChangeDataFeed` was executed on only one table.** It moved that table from protocol (1,2) to (1,7). Whether other starting protocols upgrade the same way was not tested.
- **Visual changes were checked only by the schema and academy checks.** The edited visual states have not been screenshotted at desktop and phone widths in this pass.
- **No human learner has worked the track.** This is a builder editorial review.

## Analytics, performance and economics

**Track:** `track-analytics`, Analytics, performance and economics. It covers `dbxfe-modeling`, `dbxfe-analytical-sql`, `dbxfe-m05` (retained), `dbxfe-bi`, `dbxfe-genie` and `dbxfe-finops`.

**What this record is.** This is a builder editorial review. It is not an independent human learner study. A reviewing agent worked the track and wrote the findings. The editor (this pass) checked every high and medium finding against the files, fixed the ones it confirmed, and applied the small low-severity fixes. No learner took part.

#### How the track was worked

The reviewer worked the six modules in track order: modeling, analytical-sql, m05 (l01–l03), bi, genie, finops. The finops pass included the bridge lesson `dbxfe-workspace-compute`. For each module the reviewer read, in order:

- each beat's explanation, every visual state, the check (or self-check and model answer), the Samajh, the hint and the handbook;
- the card links, extension cards, recap and applied task;
- the lesson JSON and MD;
- the scenario.

The reviewer recomputed every worked number by hand. It re-executed the modeling handbook SQL and the analytical-sql claims on local Spark 4.0.4, and compared the finops worksheet with Lab L13. It also checked prerequisites against the track order in `academy.json`.

The editor then checked each finding against the files and re-ran the claims below on local Spark 4.0.4 (a local path outside the repository):

- `CREATE SCHEMA IF NOT EXISTS quality;` followed by the handbook's `CREATE TABLE ... COMMENT` succeeds, and the comment is stored.
- Plain `SUM(a)/SUM(b)` over a zero denominator raises `DIVIDE_BY_ZERO`. `try_divide` returns NULL for 0/0 and for NULL/NULL.
- For totals 330, 300, 225, 225, 200, `RANK` gives 1, 2, 3, 3, 5, and `DENSE_RANK` gives 1, 2, 3, 3, 4. Four rows are ahead of the fifth, not three.
- Lab L12's `expected/windows.json` has the omitted row 03-02 N (45, 46.67, 3, 3, true).
- On a 4.0–5.0 axis, 4.6 and 4.8 are drawn 0.6 and 0.8 tall. That is a ratio of 1.33, while the true ratio is 4.8/4.6 = 1.043.

#### Altered examples (reviewer's, spot-checked by the editor)

| Module | Where | Alteration | Result | Teaching holds? |
|---|---|---|---|---|
| modeling | manytomany | N1 gets a third version | 8×3+4+5+4 = 37 rows; North 3,250 pieces | yes |
| modeling | units | Case pack of 24 | South 27/420 = 6.43%; naive 2.1% | yes |
| modeling | window | As of Tue 31 Mar | Business days 27, 30, 31 → 800/19 = 2.4%; calendar 500/10 = 2.0% | yes |
| modeling | additivity | N2 inspects 400 with 5 defective | Mean of rates 1.6%; sum of parts 9/600 = 1.5% | yes |
| analytical-sql | frame | Units 50, 40, NULL, 45, NULL, 50 | Row 5 averages 45.0 with 1 measured; running total 185 (Spark) | yes |
| analytical-sql | rank | Add M5 225, M6 200 | RANK 1,2,3,3,3,6; DENSE 1,2,3,3,3,4 (Spark) | yes; the Samajh count was wrong (fixed) |
| analytical-sql | dst | Stop 06:30Z, start 07:30Z | Elapsed 60, wall clock 120 | yes |
| analytical-sql | islands | Add DOWN on 7 Mar | Islands 2–3 and 6–10 (open) | yes |
| m05 | metric | A 15/2, C 5/0 | Unit rate 10%; inspection incidence 50% | yes |
| m05 | transfer | Only 4% exceed 60 s | Only a bound, so the evidence is insufficient | yes |
| m05 | latency | A′ = 10/25/10 | Two components move, so there are two hypotheses | yes |
| bi | binding | Line 4 is 40 units with 4 defective | Plant 41/840 = 4.9%; mean 6.0% | yes |
| bi | labels | Recompute the bar heights | 0.6 vs 0.8 is a third taller, not a doubling | **no (fixed)** |
| bi | refresh | Job finishes at 06:31, or at 05:50 | Monday, or Tuesday | yes |
| bi | filters | Parameter day 3 with line filter 3 | Line 3 at 5.3%; plant at 4.2% | yes |
| genie | semantics | Day 5 becomes 90/1,000 | Ratio 6.8% is above the mean 6.6% | yes (direction is data-specific) |
| genie | path | Line 1's mean exceeds line 2's | A changed line is still wrong arithmetic | yes |
| genie | trusted | Zero-unit line-day | Plain `/` raises DIVIDE_BY_ZERO under ANSI | **no (fixed)** |
| finops | startup | 5-minute startup, fifteen 4-minute jobs | 135 min, of which 55.6% is startup | yes |
| finops | sensitivity | Effort of 4 h/week | 1,040.00; base month 1,260.00 | yes |
| finops | system | Restatement of 6.2 DBU | 6.2 DBU = 3.10 hypothetical USD | yes |
| finops | utilization | auto_stop 10 min | Stops at 08:25 | yes |

#### Findings applied

##### Medium

1. **BI truncated-axis arithmetic** (`dbxfe-bi-labels` handbook, `dbxfe-bi-labels-visual` misleading row, lesson card `dbxfe-bi-l01-card2`).
   - The handbook now says a move from 4.6 to 4.8, about 4 per cent, is drawn "as a bar a third taller: 0.8 against 0.6 above the 4.0 baseline".
   - The visual row now reads "A 4% move (4.6 to 4.8) draws a bar a third taller."
   - Card2's explanation now reads "a 4 per cent move drawn as a bar a third taller". Only the explanation changed, so the revision is kept.
2. **BI late-job timeline out of order** (`dbxfe-bi-freshness-visual`, state `late`).
   - The nodes now run: Tuesday ends 23:59 → refresh 06:30 → freshness line → supervisors read 07:45 → nightly job 08:20.
   - The refresh-to-line connection now says "reads Monday's run". The job hangs off the meeting ("later"), and its detail says it publishes after the meeting, for the next refresh.
   - The alt text, the state explanation and the text equivalent were regenerated from the states. The generator reproduces all 13 original BI text equivalents byte for byte.
3. **BI access matrix did not grant what the datasets read.**
   - The page now reads two governed objects:
     - `accepted.daily_line_rate` feeds the per-line and plant datasets, and the metric view source is now `quality_pilot.accepted.daily_line_rate`.
     - `accepted.publish_status` is a view over `ops.publish_run` that feeds the freshness line.
   - The binding SQL was rewritten. The table keeps a row per line built from the line list, so the "a vanished tile" point moved into the table build.
   - The analysts' and stewards' matrix rows now list USE CATALOG, USE SCHEMA and SELECT on both objects. They appear in both visual states, the permissions handbook, the lesson access table and the scenario model.
   - `dbxfe-bi-permissions-question` (rev 1→2): option a now restores exactly those grants, so the "correct" fix actually restores the tiles.
   - Genie's line "the table the BI dashboards already read" is now true, including the `quality_pilot` catalog.
4. **Genie contradicted BI's snapshot figures and weekday mapping.**
   - Fix, done differently from the reviewer's first suggestion: the contradiction is removed by giving each module an explicit snapshot. The arithmetic is not rewritten.
   - BI now states that day 4 of its five-day reconciliation sheet is Tuesday, the day the Wednesday page covers, and day 3 is Monday. This appears in the binding handbook and the lesson.
   - Genie now states that its figures come from its own Monday-to-Friday week, which does not overlap BI's sheet: day 2 is Tuesday and "yesterday" is Friday. This appears in `startingAssumptions`, the lesson start section, the semantics handbook and the semantics visual caption.
   - Reason: aligning the numbers would change dozens of dependent values across beats, checks, cards and scenarios in both modules. The reviewer's own alternative, to state each module's weekday mapping, resolves the conflict. A single shared table remains a possible later improvement.
5. **Genie's "contracted" trusted function divided plainly.**
   - `try_divide` now appears in the trusted function, the reference query, the lesson path SQL, the semantics measure and the metric-view concept example.
   - The reference query gained `WHERE business_day BETWEEN :first_day AND :last_day`.
   - A benchmark row for the empty case was added: line 4 on Wednesday, one voided inspection, 0 units, expecting "No inspected units", with no rate and no error. It appears in the guarded state of `dbxfe-genie-benchmark-visual`, the benchmark handbook and the lesson example table.
   - The ANSI statement is hedged ("wherever ANSI mode is on … check the warehouse's setting") and cites `dbxfe-modeling-course-claim-ansi`.
6. **"Embedded credentials" meant opposite things in BI and Genie.**
   - The contrast is now stated in the Genie access explanation and handbook, and in lesson card `dbxfe-genie-l01-card10` (explanation only, so the revision is kept).
   - `dbxfe-genie-access-question` (rev 1→2): the rationale for option b now says why the reading fits a dashboard but not an agent.
   - The extension card `dbxfe-genie-extension-dashboard` now says the generated agent's access rule is not stated on the pages reviewed, and must be tested as a viewer identity.
   - The lesson's access section carries the same contrast.
7. **Modeling assumed m05-l01.** `startingAssumptions[1]` and the lesson start section now say:
   - the contract is taught from scratch here;
   - m05-l01 comes later in the track and is an optional short read.

   The track order in `academy.json` is outside this assignment's files, so it was not changed.
8. **BI assumed governance-track grants.**
   - The permissions handbook now carries a primer: the three privileges, a four-statement GRANT example and `SHOW GRANTS`, citing `dbxfe-fact-privileges`.
   - `startingAssumptions[2]` was rewritten.
   - The lesson start and access sections say the later governance track owns the full model.
9. **Analytical-sql worked table dropped row 4** (`dbxfe-analytical-sql-l01.md`, section `worked`). The row `M1 | 2026-03-02 | N | 45 | 46.67 | 3 | 3 | true` was inserted, with one sentence naming the NULL row's frame (55, 45, NULL).
10. **Analytical-sql RANK Samajh count.** It now reads "kyunki chaar log usse aage hain".

##### Low

- **Genie's USE CATALOG/USE SCHEMA assumption.** Rewritten in the assumption and the lesson start, and the access handbook now says "SELECT alone is not enough …".
- **BI refresh morning.** "Posts them on Tuesday morning" is now "Wednesday morning".
- **BI meeting time.** It now reads as one timeline: supervisors read the page at 07:45 before the 8 a.m. meeting. This changed the freshness explanation, the alt text and the node label "Supervisors read 07:45". The decision beat and the scenario already said 8 a.m.
- **BI "no data" overclaim.** A missing grant is now described as a tile that fails with a permission error ("check the exact rendering in a workspace"). The text also says such a tile must never be read as "no inspections". This changed:
  - the permissions explanation, visual and handbook;
  - the credentials explanation and visual;
  - the lesson access section;
  - card `dbxfe-bi-l01-card5` (rev 1→2);
  - the permissions question prompt (in the same revision 2).
- **BI acceptance self-check** (`dbxfe-bi-acceptance-self`, rev 1→2). The count now chooses the wording: "no inspections" when the count is 0, and "no inspected units" when inspections exist but their units total 0.
- **BI and modeling contract vocabulary.** The lesson start section maps units to pieces and `no_units`/`no_inspections` to the displayed words. It names the two display clauses BI adds and says BI's North plant is its own four-line snapshot. The related section was reworded to match.
- **BI lesson check** `dbxfe-bi-l01-q1` (rev 1→2). The rationale for option c now refers to the table's row per line.
- **Genie descriptions self-check** (`dbxfe-genie-descriptions-self`, rev 1→2). The prompt now says what `dr`, `qty` and `rst` hold.
- **Modeling metric view YAML.** Added the `line_id` dimension (as in the Lab L11 SOLUTIONS §6) and a `business_month` dimension, plus one sentence mapping each diagram query to its dimensions.
- **Modeling medallion DDL.**
  - `CREATE SCHEMA IF NOT EXISTS quality;` is now prepended.
  - The text now says the DDL is not one of Lab L11's statements and was run separately; it was re-executed here.
- **Modeling conformed question** (rev 1→2). The prompt now names the left join.
- **Modeling `is_current`.** The column was added to the star and history tables, with one sentence on the one-current-row check.
- **m05 serving (retained).**
  - The handbook introduces Inspection B, replay and `stale_previous`.
  - "20/1" is now "1/20".
  - The evidence node says "conflicting inspection B".
  - Beat `dbxfe-m05-serving` is now 1.0.0→1.1.0, with a change note.
- **m05 transfer "Unresolved" cell (retained)**, done differently from the reviewer's suggestion.
  - The beat itself says 10% "still exceed 60 seconds", and l03 says the candidate "leaves the slowest 10% above 60 seconds". So the cell now reads "Above 60 s (the open problem)" against "Still above 60 s", not "not measured".
  - Beat `dbxfe-m05-transfer` is now 1.0.0→1.1.0, with a change note.
- **Analytical-sql cross-reference.** m05 now "diagnoses where a slow query's time goes: queue, execution and cache".
- **Analytical-sql scenario disclosure.** It now says "after 7 PM New York in winter (EST) or 8 PM in summer (EDT)".
- **FinOps nightly job timeline.** The FinOps job is now requested at 01:30 after a 01:30 export and publishes by about 02:10, which matches BI. The experiment deadline is now "before the morning page's 06:30 refresh" in the handbook and the lesson. This changed the classes visual, the quota visual (three states), the hint, the handbook and `dbxfe-finops-quota-question` (rev 1→2).

#### Findings rejected

- **m05 polish, part:** the spacing and hyphen typos "A versusB" and "B versusC" in the `dbxfe-m05-latency` question prompt and handbook, and "95%-under 15 s" in the `dbxfe-m05-transfer-question` prompt. m05 is a retained module, and `academy-disposition.py --check` treats any prompt change as assessed and any handbook change as teaching. So each fix would need a new question revision or beat version, and learners would see a "revised" notice for no change in meaning. That contradicts AUTHORING's rule that a cosmetic spelling fix keeps its revision. These should be batched with the next substantive revision of those items.
- **Reviewer's non-finding notes** (the Genie semantics caption's direction, the Genie path option c "usually"). These were not findings and were left unchanged.

#### Identity and revision record

- No id was removed or renamed.
- Assessed changes in new modules (revisions bumped even though these modules are unpublished):
  - `dbxfe-bi-permissions-question` 2
  - `dbxfe-bi-acceptance-self` 2
  - `dbxfe-bi-l01-card5` 2
  - `dbxfe-bi-l01-q1` 2
  - `dbxfe-genie-access-question` 2
  - `dbxfe-genie-descriptions-self` 2
  - `dbxfe-modeling-conformed-question` 2
  - `dbxfe-finops-quota-question` 2
- Beat versions in new modules stay at 1.0.0 because the modules are unpublished.
- Retained m05: `dbxfe-m05-serving` and `dbxfe-m05-transfer` are now 1.1.0, with change notes. No m05 question or card changed, and m05 lesson files are untouched.
- Lesson `contentVersion` is unchanged.

#### Checks run

- `node --import tsx scripts/academy-check.ts --module <id>` prints "PASS (no failing findings)" for all six modules (m05 keeps its two pre-existing warnings).
- `python3 scripts/academy-disposition.py --check` exits 0 with `revisionNotMoved` at 0. The run rewrote `docs/academy/DISPOSITION.json`, which also reflects concurrent changes by other agents in m03 and transformations.
- All 16 JSON files written in the six modules parse.
- `scripts/snippet-audit.py` counts are unchanged:
  - modeling: 4 partial, 11 illustrative;
  - analytical-sql: 11 verbatim, 3 lines;
  - finops: 4 illustrative.

#### Strengths (from the review, still true)

- **Modeling:** one executed dataset is threaded through every beat, and every quoted number reconciles with Lab L11. Its handbooks give the mechanism, what to inspect, when not to apply a rule and how to explain it.
- **Analytical-sql:** every block comes from Lab L12, and its product claims were re-executed. Its plan-reading point, that a missing frame clause can give the right numbers under a RangeFrame, is non-obvious and testable.
- **m05:** the bound reasoning for tail latency is correct, including the strict-boundary counterexample.
- **BI:** the filter-versus-parameter distinction, the two-doors model and the acceptance script with outside values and signers are clear, and the ratio arithmetic is exact.
- **Genie:** it handles the rename honestly, and its benchmark design (clarify, refuse, keep the contract, no rows) is applied consistently.
- **FinOps:** its arithmetic matches Lab L13, every rate is labelled hypothetical, and it separates quota from capacity, budgets from policies, and pool idle time from DBUs.
- **Samajh:** the boundaries are specific throughout the track.

#### Limitations that remain

- **Visual captures are stale.** The rendered states captured for visual review (`VISUAL-REVIEW.json`) were not re-taken for the changed states:
  - BI: labels/misleading, freshness normal and late, permissions both states, credentials/individual, metricview/definition;
  - Genie: benchmark/guarded;
  - FinOps: classes/placed, quota (three states);
  - m05: serving/trace, transfer/results.
- **Platform-only statements are syntax-reviewed only.** This covers the Unity Catalog GRANTs (the view is granted with `ON TABLE`), `CREATE FUNCTION`, the metric view YAML with its new dimensions, and the dashboard datasets. None was executed on Databricks.
- **BI and Genie still use two separate synthetic weeks.** They are now explicitly separate, not one shared table. Modeling's lab schema (`cinderline.quality`) differs from the `quality_pilot` catalog used by BI and Genie.
- **Track order is unchanged.** Modeling still precedes m05 in the track; the content no longer depends on m05 first.
- **Documentation claims were not re-read.** Product claims rest on the modules' existing search-level source evidence, because documentation bodies were not fetched in this sandbox.
- **No learner study.** This is a builder editorial review, not an independent human learner study.

## Governance and cloud architecture

**Builder editorial review. This is not an independent human learner study.** No learners were observed. The implementing builder's reviewer and editor did the review on 2026-09-23.

Modules, in learning order: D1 `dbxfe-m06` (retained), D2 `dbxfe-identity`, D3 `dbxfe-aws`, D4 `dbxfe-azure`, D5 `dbxfe-gcp`, D6 `dbxfe-sharing` (all five new).

#### How the review was done

**Reviewer.** The reviewer read each module in order, as a learner meets it. For each beat they read:

- the explanation;
- every state of the main visual;
- the check with all its rationales, or the self-check with its model answer;
- the Samajh mapping and boundary;
- the hint and the handbook.

For each module they also read:

- the card links, the extension cards, the recap and the applied task;
- the concepts, claims and sources;
- the lesson JSON and Markdown;
- the scenario.

They kept a running ledger of terms, principal names, path definitions and the privilege model across modules, and checked every fenced code block by hand. They read the real `databricks-sdk` 0.141.0 wheel to confirm the SDK facts the identity, Azure and sharing modules rely on. They ran `scripts/snippet-audit.py`, compared the identity review matrix with `lab-l14-governance-review` (`fixtures/negative/wide_plan.json`, `expected/negative.json`), and checked the m06 bundle claim against `content/exercises/reliable-data/lesson_examples/manifest.json`. They edited no files.

**Editor.**

- Checked every high and medium finding against the files before touching them.
- Swept all six modules for further instances of each defect class, not only the instances quoted:
  - "runs as its author";
  - `GRANT ... TO` a service principal's display name;
  - joined words;
  - catalog-level `SELECT`;
  - "falls through" to public DNS;
  - "empty result means filter";
  - the public-access default.
- Made every edit through scripts that assert each old value exactly before replacing it.
- Rebuilt the two changed Google Cloud node visuals' text equivalents with a generator. Before using it, confirmed that it reproduces all 7 existing Google Cloud node visuals exactly. Other text equivalents were edited in place.

#### Altered examples

"Holds" means the module's teaching gives the right answer for the reviewer's changed case.

| Module | Where | Altered example | Hand result | Holds? |
|---|---|---|---|---|
| m06 | read beat and check | Analyst lacks USE CATALOG instead of USE SCHEMA | Grant USE CATALOG only; retest allowed read and denied write | yes |
| m06 | l01 access matrix | Owner grants schema-level SELECT to Ben's group | Every current and future reporting table becomes readable; the negative test fails; reject | yes |
| identity | row filter and mask | Jon runs `SELECT *`; a fifth row I-105 (EU-2) is added | Jon 0 rows; Maya 3 masked; Ravi 5 unmasked | yes |
| identity | review matrix, wide state | The "SELECT on catalog quality" plan applied literally | T2 still PERMISSION_DENIED, because USE SCHEMA on quality.accepted is not held | **no, now fixed** |
| identity | failures check | Upstream overwrote the table with an empty batch | 0 rows, no error, for everyone; the cause is the data | **no, now fixed** |
| identity | incident window | Revocation at 15 Sep 10:30 | Window 12 Sep 17:20 – 15 Sep 10:30; audit bound moves | yes |
| aws | unity / denied, catalog | job-nightly lacks USE CATALOG | PERMISSION_DENIED names USE CATALOG; no AWS call | yes |
| aws | denied, storage | Role policy covers only `accepted/2026-09-21/*` | S3 AccessDenied at step 4; KMS is never reached | yes |
| aws | egress | pypi.org allowed, files.pythonhosted.org not | Wheel download times out; it is an allowlist gap | yes |
| aws | denied handbook step 2 | Ravi runs Lena's notebook interactively | Ravi's grants are checked | **no, now fixed** |
| azure | VNet sizing | /25 pair, three 30-node clusters | 123 − 90 = 33 more nodes | yes |
| azure | VNet handbook | /26 host, /25 container | min(59, 123) = 59 | yes |
| azure | routes | UDR 10.20.2.0/24 → firewall added | /24 wins over /22; storage goes to the firewall | yes |
| azure | serverless rule states | Approved on day 15 | EXPIRED after 14 days; recreate; allow 24 h | yes |
| gcp | firewall | Allow at 800, deny at 900; then both at 900 | Allowed; then deny wins the tie | yes |
| gcp | PSC, no-record state and check | Visible zone lacks the tunnel record | NXDOMAIN, not a public answer; workspace-only zone gives an instant resolution error | **no, now fixed** |
| gcp | front end | ENDPOINT level, public access on, one listed endpoint | Contractor refused; laptop only if its IP is on the access list | yes |
| sharing | token rotation | Rotate at day 85 with 3 d; then with 10 d | A ends day 88, B day 175; A cannot be extended past day 90 | yes |
| sharing | revocation tail | Last query 13:59 with 60-minute URLs | Tail ends 14:59 | yes |
| sharing | pushdown | Date predicate AND a local function | 1,840 rows cross | yes |

The editor re-ran the four failing cases against the edited content. All four now hold:

- **Identity, wide plan:** the wide plan is now "USE SCHEMA and SELECT on catalog quality", keeping USE CATALOG, which is `lab-l14`'s `wide_plan.json`. T2 succeeds, and the state explains that catalog SELECT alone would still be refused.
- **Identity, failures check:** the stem now says that a quality lead still gets all 40 rows, which rules out the data.
- **AWS, notebook:** step 2 now says that an interactive notebook runs as the signed-in user.
- **Google Cloud, PSC:** the missing record now yields NXDOMAIN, and the check's stem says "fails at once with a name-resolution error".

#### Findings applied

These version rules apply to the retained module, m06:

- A beat whose teaching changed gets a new version and a change note.
- A check whose options or prompt changed gets a new revision.
- A lesson whose sections changed gets a new `contentVersion`.

In the five new modules, which are unpublished, beat and lesson versions stay at 1.0.0. Checks, self-checks and questions whose prompt, model answer or options changed still move to revision 2. Clarified explanations keep their revision.

| Severity | Module | Location | Change | Version and revision effect |
|---|---|---|---|---|
| high | identity | `dbxfe-identity-review-visual`: wide state title, explanation, caption and text equivalent; review handbook; lesson `dbxfe-identity-l01-example`; card15; q3 option a | The wide plan is now "USE SCHEMA and SELECT on catalog quality" (USE CATALOG kept), matching `lab-l14`. The state and handbook say that catalog SELECT without USE SCHEMA would still be refused on T2. Card15: "USE SCHEMA and SELECT on a whole catalog". q3 option a's rationale: "widens SELECT ... still lacks the USE SCHEMA" | q3 → rev 2; card15 explanation only |
| medium | identity | `dbxfe-identity-failures-question`; card10; failures handbook (Data policy row, worked case); concept `dbxfe-identity-layer-concept` | The stem adds that a quality lead still gets all 40 rows. The rationale, card10 and the concept now read "an empty success while an unfiltered principal still sees the rows". The handbook's first check is the same query as an unfiltered principal; if that is empty too, the data changed | Question → rev 2; card10 explanation only |
| medium | identity | `dbxfe-identity-l01.md`, solution "Export." | "USE CATALOG and USE SCHEMA on the export table's parents, SELECT on that one table and READ on scope logistics-sftp" | Lesson body |
| medium | m06 | `dbxfe-m06-l01.md`, `dbxfe-m06-l01-foundation-sources` | The copied bundle and 30-test boilerplate is replaced with an m06 scope statement: nothing here was executed; the GRANTs are illustrative platform SQL; the path's shared bundle covers the Python and Spark lessons, not this one; practise with the tabletop governance review lab. The downloadId is kept (see rejected) | `dbxfe-m06-l01` 2.0.0 → 2.1.0 |
| medium | aws, sharing | `dbxfe-aws-unity` handbook SQL; `dbxfe-aws-l01-storage` SQL; `dbxfe-sharing-catalogs` handbook SQL | Grants go to `` `<job-nightly-application-id>` `` and `` `<svc-reliability-spark-application-id>` ``, with a comment that SQL names a service principal by its application ID (a group holding it also works) | Handbook and lesson body; no assessed change |
| medium | aws | `dbxfe-aws-denied` handbook, step 2 | "A job runs as its run-as identity, including a notebook run as a job task; a warehouse session, an interactive notebook or a query runs as the signed-in user who runs it, not the notebook's author" | Handbook |
| medium | gcp | `dbxfe-gcp-paths`: explanation, visual (edges, node details, state explanations, caption, regenerated text equivalent), handbook, recap; self-check `dbxfe-gcp-paths-self` | Aligned with AWS and Azure. The control path runs from the control plane to the VM through the relay tunnel the VM opened, or over Databricks' network for serverless. The execution path is the compute running the query as sp-quality-nightly after the Unity Catalog check | Self-check → rev 2 |
| medium | gcp | `dbxfe-gcp-psc-visual` no-record state, node, alt and text equivalent; psc handbook; `dbxfe-gcp-psc-question`; unreachable handbook step 4; card9 | A visible private zone answers NXDOMAIN for a missing name. This is hedged as Cloud DNS behaviour to confirm on its resolution-order page. A public answer means the zone is not visible. The check's stem now says "fails at once with a name-resolution error". Step 4 now distinguishes the public-answer case from NXDOMAIN | Question → rev 2; card9 explanation only |
| medium | gcp | `dbxfe-gcp-differs` private-state row, state explanation and text equivalent; `dbxfe-gcp-frontend` explanation and account state; lesson differs table and private section; `dbxfe-gcp-differs-self` reasoning | Row renamed "Public access default (private access settings field)", with true on Google Cloud and false on AWS. The Azure cell stays "Set on the workspace resource". The frontend explanation now names the `public_access_enabled` field | Reasoning only; no revision |
| low | identity | `dbxfe-identity-secrets-question` | The stem adds "the scope's ACL currently lists only quality-platform-owners (MANAGE)" | Rev 2 |
| low | identity | incident visual `cause` node and text equivalent; incident handbook step 5; `dbxfe-identity-incident-self` | "Lena's script moved to a service principal with OAuth" (the nightly job already runs as sp-nightly-ingest, so the 15 Sep audit row is consistent). The window now runs "from the commit, the earliest moment the token could be copied, to the revocation" | Self-check → rev 2 |
| low | identity | `dbxfe-identity-provisioning` explanation; visual caption | "none of the three grants a Unity Catalog privilege; identity federation carries only the workspace assignment" | — |
| low | m06 | `dbxfe-m06-read` visual and text equivalent, concept `dbxfe-m06-read-concept`; `dbxfe-m06-transfer` explanation | The analyst's object is `quality.reporting.daily_rate` with USE SCHEMA quality.reporting throughout, matching the matrix, the worksheet and the acceptance row | read, transfer → 1.1.0 |
| low | m06 | `dbxfe-m06-principals-question`, option a rationale | "The admin's success may come from ownership or broader grants the analyst does not hold." | Check → rev 2; principals → 1.1.0 |
| low | m06 | `dbxfe-m06-l03.md` deeper; `dbxfe-m06-network` handbook | Points to the Azure and Google Cloud modules in this track, with links, instead of saying those clouds were not reviewed | l03 1.0.1 → 1.1.0; network → 1.1.0 |
| low | m06 | network cloud rows; transfer grant row; sharing node value | "and identity", "SELECT + USE CATALOG + USE SCHEMA", "Named recipient + policy" | Network and transfer are covered by their bumps; the sharing spacing is cosmetic, so that beat keeps 1.0.0 |
| low | aws | `dbxfe-aws-profile` handbook Python | Loads the Delta table root `s3://cinderline-inspections/accepted/`, not a dated subdirectory | — |
| low | aws | `dbxfe-aws-serverless` handbook | Adds the release stage: provider documentation v1.133.0 labels NCC binding and private endpoint rules Public Preview on AWS. Links to the Google Cloud matrix beat | — |
| low | azure | `dbxfe-azure-l01-storage` | Explains `READ FILES`: direct path reads under the location, separate from table SELECT, for engineers only | — |

#### Findings rejected or partly applied

- **m06 bundle, downloadId (partly applied).** The paragraph was replaced, but the `dbxfe-reliable-data-exercises` downloadId stays. The bundle is the Reliable Data Foundations path's shared download, and it is attached to every core lesson of that path, including `dbxfe-cloud-bridge` and `dbxfe-workspace-compute`. The lesson now says plainly that the bundle has nothing for it.
- **Principal names across modules (low, rejected as a rename).** The four principals do not run the same workload:
  - identity's `sp-nightly-ingest` ingests SFTP deliveries into `quality.raw` (SELECT and MODIFY on deliveries, per lab-l14);
  - AWS `job-nightly` reads `quality.accepted.inspections`;
  - Google Cloud `sp-quality-nightly` reads `quality.raw.inspections` from `gs://`;
  - Azure `sp-job-nightly` is a separate example.

  Giving them one name would imply one identity with contradictory grants. Each module introduces its principal in its first worked beat. The AWS SQL comment now says `job-nightly` is a display name.
- **"Three-cloud diagnosis lab" promises (low, rewording rejected).** `lab-l15-three-cloud-diagnosis` is in the academy contract (`academy.json` `labIds`, the D3–D5 lab lists and both capstones), so it is a committed deliverable, not a plan. Calling it "planned" would become false when it lands.
- **Prerequisite half of the same finding (confirmed, blocked, handed to the integrator).** The three cloud lessons build on `dbxfe-m06-l01` and `dbxfe-m06-l03`, so `dbxfe-m06` belongs in their prerequisites. The editor added it to `modules/dbxfe-{aws,azure,gcp}.json` twice. Both times the integrator's `register.py` reset the packages (12:47:20 and 12:52:31 UTC): it rewrites every registered package's `prerequisiteIds` from its own `PREREQS` table on each run. That table is outside this assignment's files, so the packages are left as they were. The fix belongs in `register.py`: set `'dbxfe-aws'`, `'dbxfe-azure'` and `'dbxfe-gcp'` to `['dbxfe-m03', 'dbxfe-m06']`. m06 has no prerequisites, so this adds no cycle.
- **media.json caption "read for04:15-04:49" (low, not applied).** `content/teaching/dbxfe/media.json` is a shared file outside this assignment's file list and is being edited concurrently. Left for the media record owner.

#### Checks run

- `node --import tsx scripts/academy-check.ts --module <id>`: **PASS (no failing findings)** for dbxfe-m06, dbxfe-identity, dbxfe-aws, dbxfe-azure, dbxfe-gcp and dbxfe-sharing. The seven m06 warnings (l02/l03 section kinds, scenario disclosures) predate this review.
- `python3 scripts/academy-disposition.py --check`: **exit 0**. For m06: 0 removed, 0 revisionNotMoved. The run regenerated `docs/academy/DISPOSITION.json`.
- Every changed JSON file parses and keeps its original serialization.
- A link and dropped-Markdown audit of the 7 changed or related lesson bodies, using `src/markdown-audit.ts` against registered modules and lessons: **PASS**.
- The whole-course `academy-check` without `--module` could not complete. It stops on another agent's in-progress module: `Unknown teaching module dbxfe/dbxfe-serving`.

#### Strengths (reviewer's, confirmed by the editor)

- The SDK facts match `databricks-sdk` 0.141.0:
  - redirect `localhost:8020`;
  - the 40-second refresh margin;
  - `github-oidc`;
  - shorten-only `rotate_token`;
  - `IpAccessList`;
  - `AzureManagedIdentityRequest`;
  - `EXTERNAL_USE_SCHEMA`;
  - the NCC `gcp_endpoint`.
- Every numeric visual recomputes correctly: subnet caps, the token timeline (2026-09-23 + 90 d = 2026-12-22), the revocation tail, the incident window, the filter and mask outputs, and the pushdown counts.
- One diagnostic structure transfers across AWS, Azure and Google Cloud: a refusal names its layer, and a timeout names none. Each evidence table's "does not prove" column points to the next row.
- Uncertainty is recorded honestly. Google Cloud serverless private connectivity stays unknown, with the conflicting sources quoted.
- Checks are diagnostic, with specific distractor rationales. The Samajh analogies state their limits.
- The track builds in sequence: m06's conjunction and negative tests become identity's run-as, filters and audit, then the cloud modules' catalog-before-storage order, then sharing's measurable revocation tail.

#### Limitations that remain

- **Not verified against live pages.** The Cloud DNS NXDOMAIN rule is hedged in the text: its resolution-order page was not fetched, because the documentation host is blocked in this build. The rule "SQL names a service principal by its application ID" rests on the identity module's SDK source, not a re-read of the SQL privileges page.
- **Visuals not seen in a browser.** No changed visual state was inspected at desktop or phone width. The changed visuals are:
  - identity: review, incident and provisioning caption;
  - m06: read, transfer, network and sharing;
  - Google Cloud: paths, psc, frontend and differs.

  They need the VISUAL-REVIEW capture.
- **Prerequisites still unfixed.** The prerequisite fix is pending in the integrator's `register.py` (see rejected findings). The module packages carry no content change from this review; `register.py` also re-serializes `modules/dbxfe-azure.json` (indent 1 → 2).
- **The same bundle boilerplate is still elsewhere.** `dbxfe-cloud-bridge`, `dbxfe-workspace-compute` and `dbxfe-m03-l02` still carry it. They are outside this track.
- **lab-l15 is still missing.** `lab-l15-three-cloud-diagnosis` was not in `content/exercises` or `content/courses/dbxfe/labs`. The AWS, Azure and Google Cloud snippet audit cannot run until it exists.

## Machine learning and production evaluation

**What this is.** A builder editorial review of `track-ml`: a builder reviewer's report, then an editor who checked each finding against the files and applied the fixes. It is **not** an independent study with human learners, and no learner outcomes were measured.

Modules: dbxfe-m07, dbxfe-features, dbxfe-mlflow, dbxfe-serving, dbxfe-forecasting and dbxfe-deep-learning. Review date: 2026-09-23.

#### How the reviewer worked through the track

The reviewer took the six modules in track order, as a learner meets them. For each module they read:

- every beat: the explanation, each visual state, the check with its options and rationales (or the self-check and its model answer), the Samajh, the hint, the handbook, the card links and the extension cards
- the recap and the applied task
- the lesson JSON, the lesson Markdown and the scenario

The reviewer then redid every worked example by hand or in a scratch venv:

- m07: the confusion matrices, the threshold sweep and the cutpoint fit
- features: window means, ages, joins and status counts against the L18 fixtures
- mlflow: TP, FP, FN and TN recovered from each run's rates
- serving: capacity, backlog, timings and label arithmetic
- forecasting: MAE, MAPE, MASE, bands, z-scores, threshold totals and precision@k against the L19 fixtures
- deep-learning: the forward pass, loss, gradient, update and memory figures

Code claims were checked by running them. The L18 and L19 lab suites both passed with 0 failures. The deep-learning NumPy example reproduced its output. Each quoted MLflow 3.16.1 behaviour reproduced: the 10,000-row digest, param immutability, skops by default, int64 refused and int32 accepted, extras ignored, the scoring server's 200/200/400, and the SQLite default. The reviewer also read the PyTorch autolog docstring.

Handbook excerpts were compared with the lab solutions using snippet-audit. Finally, the reviewer checked cross-module dependencies: availability time, how the test set is used, and missingness.

#### The reviewer's altered examples

The reviewer changed 19 worked examples. For 14 of them, the teaching still held when the numbers or data changed:

| Module | Altered example | Holds? |
|---|---|---|
| m07 | cutoff 0.50 | yes |
| m07 | a different matrix | yes |
| m07 | irregular training labels, which produce a tie the handbook anticipates | yes |
| m07 | 5% prevalence | yes |
| features | an exact 10:30 match, with `allow_exact_matches` True and False | yes |
| features | a 150-minute limit (ok 6, none 2, stale 3) | yes |
| features | a late reading ingested at 11:35 | yes |
| mlflow | an 8,000-row digest | yes |
| mlflow | `precision_min` 0.25, where nothing is promoted | yes |
| serving | 40 and 75 requests per second | yes |
| serving | a 30 ms lookup, giving 59 ms | yes |
| forecasting | a 25 h miss cost, and 6 h reviews with a 40 h miss | yes |
| forecasting | anomaly z-scores at rate 0.0228 | yes |
| deep-learning | y = 0 and a new input | yes |
| deep-learning | 100 MB fixed plus 20 MB per image, at batches 64 and 96 | yes |

Five altered examples broke the teaching. Each one became a finding below:

- mlflow: C was chosen and certified on the same days, which contradicts m07's rule.
- serving: P-4471 scored 0.12 in batch and 0.42 online.
- serving: `run_date` read from the clock on a next-morning rerun.
- forecasting: Friday's count used before a 16:00 meeting could have it.
- deep-learning: a 4-D batch fed to a "1-D CNN".

#### Findings applied

| Sev. | Module | Where | Change |
|---|---|---|---|
| high | mlflow | `modules/dbxfe-mlflow.json`: scenario `dbxfe-mlflow-scenario` | The context now gives contract 1.0.0's thresholds, the T-1 and T-2 counts on weeks 9–12 (T-1: 19 of 25 faults, 73 warnings; T-2: 21 of 25, 95 warnings) and the rule in use (11 of 25). Two disclosures are added: the records pass the evidence checks, and two ovens were absent from training. The model answer now names weeks 9–12 as a selection period. Rubric-4's strong level names the ovens and the reuse of weeks 9–12. |
| medium | mlflow | beat `dbxfe-mlflow-signature` (explanation, handbook, recap); visual `dbxfe-mlflow-signature-visual` (title, caption, state `contract` retitled "A signature logged from the drifted frame…"); check option b rationale; lesson `…-l01-package` table and a new sentence; mistakes bullet; card10 (revision 1→2); q2 option a rationale; module recap | The text now says the contract gates promotion by reading a logged signature and never sees a request. An illustrative `check_request()` shows how to refuse a request itself; it was executed. |
| medium | mlflow | handbooks of beats `dbxfe-mlflow-compare` and `dbxfe-mlflow-promotion`; self-check `dbxfe-mlflow-promotion-self` reasoning; lesson `…-l01-registry` | Days 85–120 are named as the selection (validation) period, and the handbook says to confirm the candidate on a later untouched period. A new probability threshold must be chosen before day 85 and confirmed after day 120. |
| medium | serving | visual `dbxfe-serving-batch-visual` and beat `dbxfe-serving-batch` explanation | Batch part IDs are now P-4481–P-4484, and P-4481's inputs differ. The batch examples no longer contradict the online P-4471 score of 0.42. |
| medium | serving | beat `dbxfe-serving-request` handbook | One fallback now applies everywhere: the station **fails open**, so the part continues uninspected. This is stated as a design choice with its cost; failing closed would divert to the inspection lane instead. The "inspection lane" fallback sentence is removed. |
| medium | serving | beat `dbxfe-serving-batch` handbook code and text; self-check `dbxfe-serving-batch-self` (revision 1→2) | `run_date` now comes from the job parameter `production_date`, not the clock, and a rerun must name the date it rescores. |
| medium | serving | beat `dbxfe-serving-features` (explanation and handbook); visual caption; `dbxfe-serving-incident` and `dbxfe-serving-drift` handbooks; lesson capacity section; card7 explanation; scenario model | Zero imputation of a missing lookup is now named as the design defect that breaks the features module's missingness policy. The mitigation is an explicit no-score, handled by a rule the owner writes. |
| medium | features | beat `dbxfe-features-delivery` (explanation and handbook); visual `…-delivery-visual`, state `decisions` | The handover row now says neither path works as set. An online lookup at 10:00 serves the same row that is 120 minutes old. The owner can move the decision to 10:35 and score it in batch, or compute it on demand. |
| medium | forecasting | beat `dbxfe-forecasting-horizon` (explanation and handbook); horizon visual, state `origin`; lesson horizon sentence; extension `dbxfe-forecasting-extension-gap` (revision 1→2); scenario context and model | Timing is now stated once and consistently. The core roster is set at 23:00 on Friday, after the night count posts at about 22:00, so the Friday-origin backtest is legitimate. The scenario and the extension card treat a move to a 16:00 meeting as the case that needs `gap=1`. |
| medium | deep-learning | lesson `…-l01-design` (text, table and code) and `…-l01-platform`; teaching baseline visual row; scenario model | The network is a 2-D CNN on `(N, 1, 64, 126)` spectrograms, and the text notes that Conv1d would need `(32, 64, 126)`. The code now uses `y.float()`. |
| medium | deep-learning | beat `dbxfe-deep-learning-ladder` (handbook code, visual node `gpu1`); lesson design code and note; self-check `…-ladder-self` (revision 1→2); applied task; `train-infer` handbook; scenario model | The code now logs epoch time, validation recall and peak memory explicitly with `mlflow.log_metric(…, step=epoch)`. Autolog is stated as full only for Lightning; on a plain loop it logs only SummaryWriter scalars. |
| low | features | check `dbxfe-features-definition-question` option c rationale; beat `dbxfe-features-definition` hint | The rationale no longer relies on a fact taught in the next beat, and the hint now points at the row's key. |
| low | features | `dbxfe-features-definition` and `dbxfe-features-offline` handbooks | The ingestion and closed-window filters are added; they were executed against the L18 fixtures. The FeatureLookup imports are added. |
| low | serving | lesson `…-l01-example` `contract_test.py` | The test reads a downloaded local model directory, so it needs no credentials. Executed on MLflow 3.16.1: 5/5 tests pass. |
| low | serving | beat `dbxfe-serving-request` handbook | `timeout=0.2` is now described as a per-phase socket timeout, not a total deadline. |
| low | serving | incident visual, state `day12`; check `dbxfe-serving-incident-question` (revision 1→2); lesson q1 (revision 1→2); profiling visual | The client-error rate is now 100% from 06:10, because the station is the only caller. The profile figures are now 18/188 = 9.6%, 18/196 = 9.2% and 78/191 = 40.8%. |
| low | serving | `dbxfe-serving-features` and `dbxfe-serving-scorecard` handbooks; card7; scenario | Clauses added saying that serving's "feature freshness" is publish lag, not the features module's value age. |
| low | forecasting | beat `dbxfe-forecasting-uncertainty` handbook | Residuals are now computed explicitly from the model beat's fit. Executed: the fold-4 quantiles are −19.84 and +19.94, matching the lab. |
| low | deep-learning | beat `dbxfe-deep-learning-parallel` handbook; lesson card11 explanation and scaling section | DDP is now described correctly: an initial broadcast, then only gradients are exchanged each step. Buffers are rebroadcast by default. |
| low | deep-learning | beat `dbxfe-deep-learning-finetune` handbook; lesson scaling section | Past tense for Foundation Model Fine-tuning: removal "was scheduled for 14 August 2026, before this review; check what remains". |
| low (part) | m07 | concept `dbxfe-m07-features-concept` example; visual `dbxfe-m07-fit-visual` column header and text equivalent | "A 16:00" and "predict yes if ≥". Neither needs a version change. |

Revisions and versions:

- Changed prompts, answers and model answers carry the revision increments listed in the table.
- Lesson `contentVersion` moved 1.0.0 → 1.1.0 for mlflow, serving, forecasting and deep-learning.
- The new modules keep their beat versions, which is allowed while they are unpublished.
- No IDs were removed or renamed.

#### Findings rejected or deferred

- **High, m07 scenario (confirmed, deferred).** m07 teaches ML evaluation, but it sends learners to `dbxfe-m07-scenario`, a GenAI assistant scenario. The course.json module entry for m07 also carries GenAI summary and objectives. The fix needs three course-level changes:
  1. Add a new m07 scenario object, for example `dbxfe-m07-evaluation-scenario`. It would review a maintenance-prediction proposal: target and horizon, a leaked field, a split that matches deployment, precision and recall at two thresholds, and the owner's decision.
  2. Repoint the m07 module entry's `scenarioId`, and the `scenarioIds` in `content/teaching/dbxfe/dbxfe-m07.json`.
  3. Rewrite m07's `summary` and `objectives` in course.json.

  This editor may change course.json only in "that scenario object". Rewriting `dbxfe-m07-scenario` in place would break `dbxfe-genai`, which uses it as its own scenario, and could collide with the GenAI track's editor. The work is left to the owner of course.json.
- **Low, m07 polish (partly not applied).** Two items were left as they are: "WithTP3" in the `dbxfe-m07-metrics-question` prompt, and "hai.09:00" in the `dbxfe-m07-features` Samajh. m07 is a retained module. The disposition gate requires a question revision or beat version bump for any change to a prompt or Samajh. That bump would show a revision notice to learners, which contradicts AUTHORING's rule that a cosmetic change keeps its revision. Both typos are readable. The same applies to "13 of 20:65%" in the `dbxfe-m07-transfer` handbook, a typo this editor noticed that was not in the report.

#### Strengths the reviewer found

- **Arithmetic.** The arithmetic holds across the track. The only errors were the P-4471 score and the three profile percentages, both now fixed.
- **Numbers come from execution.** The lab suites pass, the NumPy example reproduces its output, and the MLflow 3.16.1 behaviours reproduce.
- **Availability time.** It runs through the whole track: m07's 16:00 repair code, the features module's published-at versus window-end, versioned late data, forecasting origins, and serving's delayed labels.
- **Checks.** Each distractor maps to a named misconception, and each rationale names the mechanism.
- **Honest product claims.** Preview and Beta status is flagged, "NOT EXECUTED" labels are used, and cost is given as drivers without prices.
- **Judgement.** The track teaches judgement, not just vocabulary: break-even costs, precision at capacity, drift as a hypothesis, and evidence before metrics.
- **Samajh.** The analogies map accurately and each states its limit.

#### Verification after editing

- `academy-check --module` prints `PASS (no failing findings)` for all six modules.
- `academy-disposition.py --check` exits 0. It regenerated `docs/academy/DISPOSITION.json` as it always does.
- `scripts/content.ts` validate mode loads the whole catalog, including the lessons, scenarios and teaching modules.
- All edited JSON files parse.
- snippet-audit: mlflow goes from 20 to 21 blocks. The new block is `check_request`, correctly classified as illustrative.

#### Remaining limitations

- The m07 scenario mismatch remains until course.json is edited, as described in the deferred finding above.
- The deep-learning training loop is still unexecuted: no torch was available here. The 2-D CNN input shape, the float target and the autolog scope rest on PyTorch and MLflow documentation. The autolog note was read in the installed MLflow 3.16.1, not run on a GPU.
- The requests timeout semantics and DDP's initial broadcast rest on library documentation, not execution.
- Serving and platform steps remain written but not executed on Databricks.
- In mlflow, only the selection-period caveat was added. The lab still has no separate validation window, and none of its numbers changed.

## GenAI, agents and applications

**Builder editorial review. This is not an independent human learner study.** A builder reviewer read the track as a learner would and recomputed its numbers by execution. The editor then checked every high and medium finding against the files and the lab code before changing anything. No learner took part.

Modules: dbxfe-genai (F1, retained), dbxfe-retrieval (F2), dbxfe-genai-eval (F3), dbxfe-tools (F4), dbxfe-ai-platform (F5), dbxfe-apps (F6). Date: 2026-09-23.

#### Sequence worked

The reviewer read all six modules in order. For each module that covered:

- the teaching JSON beat by beat: explanation, every visual state, the checks and self-checks with every rationale, Samajh, hint and handbook;
- cardLinks, extension cards, the recap and the applied task;
- the lesson JSON and MD;
- the scenario (m07 from course.json, the others from the module packages).

The reviewer also re-ran several things:

- Lab L20's TF-IDF in pure Python.
- Lab L21 (33 tests) and Lab L22 `run_tests.py`. Both pass.
- The per-block snippet-audit logic.

The editor reproduced the key facts before editing:

- **L20:** idf(is) = 3.5055, belt = 3.7932 and the maximum idf = 4.1987 over the 48-chunk small index. `assemble_context` and `check_citations` in `solutions/retrieval.py` were read. The chunk record has no citable column.
- **L21:** `classify` and `retrieval_findings` were read, along with the c02, c04 and t01–t05 `blocking_if_failed` declarations. `citation_correctness` compares citations with the RETRIEVER output. In all 17 traces the LLM span's `context_refs` equal the retrieved refs.
- **L22:** in the transfer fixtures, W3 is East, nurse-e1 holds `[catalog:read:east, supplies:order:east]`, and T06 is denied with "lacking: user".
- **SDK:** databricks-sdk 0.141.0, `DeltaSyncIndexSpec.pipeline_type` says "Storage Optimized endpoints accept only TRIGGERED". The `GenieAPI` docstring is in `dashboards.py`.
- **CLI:** the CLI v1.17.0 CHANGELOG was fetched (SHA-256 f3f705c0…b8956). The rename to Declarative Automation Bundles is listed under v0.295.0.

#### Altered examples (from the review)

The reviewer altered 23 examples. For 14, the teaching still led to the right answer: F1 trace and span timing; F2 RRF, recall@3, budget 50 and idf(belt); F3 abstention denominators; F4 timeout 7000 ms and self-approval; F5 token shape, the 20% switch and the ×2 join; F6 FakeClaims and the 422 schema.

For 9, the teaching failed. Every one of those 9 is now fixed:

| Module | Altered case | Why the teaching failed | Now |
|---|---|---|---|
| F1 | Malicious source: write requested, gate rejects it | The "No unauthorized effect" criterion passed the case; F3 c08 fails it | The criterion now judges the request |
| F2 | Mark notes context-only, then re-run the labels | Context-only changes neither rank nor budget | Taught as a citation control through a `citable` column; ranking remedies are separate |
| F3 | t04 with its executed tool | Routed only to the prompt owner | Also routed to the agent owner and security |
| F3 | F2 large-chunk case: cited, retrieved, but outside the context | F3 passed the citation; F2 rejects it | Correctness is judged against the context given to the model |
| F3 | c02 scored with F2's pass bar | Superseded chunks were counted differently in F2 and F3 | The difference and the declaration's role are now stated |
| F4 | East nurse orders 10 units | Grants and ward site were not given | Both are now given in the prompt |
| F5 | TRIGGERED index lags its source table | "Keeps itself current" was wrong | Now "as fresh as its index" |
| F6 | Leo after the user-token switch | The required grants were missing | Grant step and test added |
| F6 | Old token not revoked until 12:00 | Revocation was an unstated assumption | Now stated |

#### Findings applied

##### High

- **F4, the tools exercise.** `content/courses/dbxfe/lessons/dbxfe-tools-l01.md`, section `dbxfe-tools-l01-exercise`. Added W3 → East, each nurse's grants, and the pharmacist's approve and cancel grants, matching the L22 fixtures. Solution (d) and (f) can now be derived from the prompt.

##### Medium

- **F4 applied task** (`dbxfe-tools.json`, `appliedTask.prompt`). The prompt now gives W3 → East, the nurse's grants, the pharmacist's grants and the document id DOC-LABEL-3.
- **F3 routing of t04** (`dbxfe-genai-eval.json`).
  - Taxonomy visual: rules row 4 now also routes to the agent owner and security when a forbidden tool executed. The transfer row and the text equivalent match.
  - The handbook paragraph on `forbidden_tool_attempted:...:executed` covers the same rule.
  - Applied-task model answer, lesson section `-l01-taxonomy` and solution updated.
  - The lab's class is unchanged (it stays reasoning_failure), so the lab's expected output still holds.
- **F3 superseded evidence (c02 and t02)** (`dbxfe-genai-eval.json`).
  - New handbook paragraph, "Where this differs from the retrieval module". Rule 3 is the lab's rule: a superseded chunk returned beside the required one is not a rule-3 finding. Report F2's superseded count beside the class. Blocking is the owners' declaration.
  - Cases visual `checkable` explanation updated.
  - Self-check `dbxfe-genai-eval-taxonomy-self`: the model answer adds F2's safety count. Revision 1 → 2.
  - Lesson taxonomy and example sections updated.
  - The rule itself was deliberately left unchanged, because it is what Lab L21's code and its altered-input test implement.
- **F3 blocking declarations in the applied task** (`appliedTask.prompt`). The prompt now declares t03, t04 and t05 blocking and t01 and t02 non-blocking, and asks whether any declaration should be challenged. The model answer challenges t02 (a superseded guide for dangerous goods). The lesson task now states that t04 and t05 were declared blocking.
- **F3 citation correctness against the supplied context.** Citation correctness is now judged against the context given to the model, the LLM span's `context_refs`, which equal the RETRIEVER output in L21.
  - Deterministic handbook: table row, plus a new paragraph "Compare with what the model saw".
  - Grounded handbook and the grounded visual's `evidence` row.
  - Cases visual `checkable` row.
  - Lesson line on the scorers.
  - Explanations of cards 3 and 10 (clarified; revisions kept).
  - Scenario model: the citation validator now checks against the context given to the model.
- **F5 index sources** (`dbxfe-ai-platform.json`, `dbxfe-ai-platform-l01.json`).
  - Visual `revised`, index node: "Not synced by the assistant; as fresh as the index…". Connection and text equivalent updated.
  - The handbook now explains the TRIGGERED lag and links to `#/module/dbxfe-retrieval/dbxfe-retrieval-freshness`.
  - Samajh boundary and claim `dbxfe-ai-platform-claim-knowledge` updated.
  - Lesson card7 explanation updated (revision kept).
- **F5 caller identity in the evaluation** (`dbxfe-ai-platform-evaluation` handbook).
  - Each row in the code sketch carries `"caller"`, and `ask_candidate(question, caller)` queries as that caller. An added sentence says a run under the app or evaluator identity cannot decide a permission case.
  - The set visual names Q33's caller.
  - The lesson example and scenario evaluation plan were updated to match.
- **F5 Q19 declared eligible** (`dbxfe-ai-platform.json`).
  - New agreed rule, "No superseded revision cited". The fixed workflow is now blocked until Q19 is fixed.
  - Caption, alt text, text equivalent, explanation and handbook rules updated.
  - Check `dbxfe-ai-platform-evaluation-question`: new correct answer, "neither is eligible yet". Options b and c were rewritten as misconceptions. Revision 1 → 2.
  - Lesson and scenario rules match.
- **F5 scenario, plant separation** (`modules/dbxfe-ai-platform.json`, Responsibilities section). The app now selects each technician's plant assistant from the signed-in identity. A two-plant test is an owned verification item. Per-plant CAN_QUERY with user authorization is recorded as the alternative.
- **F2 context excerpt** (`dbxfe-retrieval-context` handbook). The handbook now quotes Lab L20 `assemble_context` verbatim; the snippet audit classifies it as verbatim.
- **F2 context-only** (`dbxfe-retrieval.json` and the lesson).
  - Authority and wrong-chunk handbooks: context-only is enforced at the citation check through a `citable` column, a design addition that the lab's record lacks. It changes no rank or budget: the note still ranks 0.5192 and still takes 36 of 60 words.
  - Context handbook updated to match.
  - Applied-task chunk record and citation check updated.
  - Self-check `dbxfe-retrieval-wrongchunk-self` (1 → 2): the two measured alternatives are now stemming or hybrid, and a reranker; context-only is kept separate. Self-check `dbxfe-retrieval-authority-self` (1 → 2) updated to match.
  - Lesson chunk table row and context paragraph updated.
- **F1 malicious-source criterion** (retained module).
  - `dbxfe-genai-visual-evaluation` start row and text equivalent now read "No forbidden tool request; a rejected request still fails". The evaluation handbook says the same.
  - Beat `dbxfe-genai-beat-evaluation` 1.0.0 → 1.1.0, with a changeNote.
  - `dbxfe-m07-l03.md`: the revisit wording and the see-table cell were updated.
  - `dbxfe-m07-l03` contentVersion 1.0.1 → 1.1.0.
- **F6 grants under user authorization** (`dbxfe-apps.json`).
  - Scopes visual `filters` state and text equivalent: the reviewers' group needs USE CATALOG, USE SCHEMA and SELECT.
  - New handbook paragraph. It says warehouse access must be confirmed with the warehouse's owner.
  - Self-check `dbxfe-apps-scopes-self` (1 → 2): adds the grant step and a newly-added-reviewer test.
  - Applied-task model answer adds the grants and a P3 test.
  - Lesson solution and scenario alternative updated.

##### Low (all applied)

- **F2 scenario:** the context-only sentence was reworded.
- **F2 metadata check stem:** now names the columns that are kept. Revision 1 → 2.
- **F2 'is' aside:** now "in this question", with belt 3.7932 given as the index-wide counterexample.
- **F2 SDK storage-optimized TRIGGERED restriction:** the SDK passage was verified and added to `dbxfe-retrieval-source-sdk` evidence and to claim `dbxfe-retrieval-claim-index`.
- **F2 chunking block:** labelled as a sketch.
- **F3 c07 in the abstain table:** now labelled "policy refusal; a failure in the taxonomy".
- **F4 idempotency `scope` state:** labelled hypothetical. The draft is now "a separate draft for C4" instead of D2; the caption says the state is hypothetical.
- **F4 C03 wording:** "no new draft" in both the lesson row and the beat explanation.
- **F5 cost:**
  - "plus any burst capacity used (check how burst is billed)";
  - "two to three or four" calls;
  - the equation now reads "3 to 4 steps = 900 to 1,200".
- **Genie space:**
  - F5 handbook aside, with a new source `dbxfe-ai-platform-source-genie` (SDK 0.141.0 `GenieAPI` docstring, read from the local wheel) and a new claim `dbxfe-ai-platform-claim-genie` on the supervisor beat;
  - F4 concept `dbxfe-tools-managed-concept` got a parenthetical definition.
- **F6 rotation:** the 10:00 node, the state explanation, the beat explanation and the check stem now say the old token was revoked at the service. Revision of `dbxfe-apps-secrets-question` 1 → 2.
- **F6 bundles claim:** new source `dbxfe-apps-source-cli-changelog` (CLI v1.17.0 CHANGELOG, fetched and hash-matched) attached to `dbxfe-apps-claim-bundles`.
- **F1 m07-l03 objective:** now "Apply an AI evaluation set …".

#### Findings rejected

None. Every high and medium finding was confirmed against the files and the lab code. Two fixes took the lab-faithful option that the reviewer offered:

- **F3 superseded evidence:** rule 3 was left as the lab's rule, and the difference is explained, rather than extending the rule. Lab L21's `retrieval_findings` and its altered-input test define rule 3, and the lab is outside this edit's scope.
- **F3 t04:** it keeps its lab class and gains a second route, rather than a new class. This keeps the L21 class counts that the module quotes.

#### Strengths confirmed

- F2's numbers reproduce from the L20 fixture.
- Distractors name specific misconceptions.
- The F3, F4 and F5 arithmetic is correct.
- F6's mocked tests trace correctly through the shown handler.
- Product claims are tied to dated artifacts, with availability and pricing left as verification items.
- The track is a coherent chain from F1 to F6, with recurring anchors: Cinderline, M7 and identity at every hop.
- Samajh boundaries are honest.
- Labelling is honest throughout: synthetic, not executed, not deployed.

#### Checks run

- `node --import tsx scripts/academy-check.ts --module <id>`: **PASS (no failing findings)** for all six modules. dbxfe-genai has 7 WARN lines; all come from its legacy lessons and scenario, not from this edit.
- `python3 scripts/academy-disposition.py --check`: revisionNotMoved 0, removed 0.
- Every JSON file written parses.
- `scripts/snippet-audit.py`, run without `--write`: dbxfe-retrieval has 1 verbatim, 1 partial and 2 illustrative blocks.

#### Remaining limitations

- **Lab code was not changed** (outside this edit's scope):
  - L20 still has no `citable` column, so context-only enforcement is taught as a design addition and has not been executed.
  - L21 still compares citations with the RETRIEVER output. The new context rule is not exercised by a trimmed trace, because no L21 trace is trimmed.
- **New modules keep beat version 1.0.0** and lesson contentVersion 1.0.0, as allowed for unpublished modules. Changed checks and self-checks still received revision increments.
- **F6 sources were not fetched.** Apart from the new CLI changelog source, F6's documentation sources remain "as previously read"; the warehouse-access requirement for reviewers is left as an owner verification item.
- **Some product behaviour stays a verification item:**
  - the Genie description is an SDK docstring, and which identity a supervisor's Genie tool call runs with remains unverified;
  - F5 still has no primary source on how burst capacity is billed.
- **Not run by this edit:**
  - the full content build, e2e and browser rendering, because other agents are editing concurrently;
  - a visual inspection of the changed visual states at desktop and phone widths;
  - an independent human learner study.

## Architecture, migration and operations

**This is a builder editorial review.** The reviewer and the editor were both builder agents working from the repository and local execution. It is not an independent study with human learners, and it does not measure how learners actually do.

Modules: `dbxfe-m08` (retained), `dbxfe-sqlserver`, `dbxfe-warehouse-migration`, `dbxfe-operations`, `dbxfe-lakebase`, `dbxfe-industry` (all new and unpublished).

#### Sequence worked

The reviewer read the modules in learning order: m08, SQL Server, warehouse migration, operations, Lakebase, industry. For every beat they read:

- the explanation and every visual state;
- the check or self-check, the Samajh, the hint and the handbook;
- the card links, extension cards, recap and applied task;
- the lesson JSON and markdown, and the scenario.

Each module was rendered to text so that no state or option was skipped.

**The reviewer's execution:**

- **Lab L24:** a copy passed 28/28 on PySpark 4.0.4 with Java 21. Every lab number the SQL Server module quotes was re-derived from the fixtures and expected JSON.
- **Spark snippets:** those from SQL Server, warehouse migration, operations and industry ran on Spark 4.0.4.
- **MERGE:** the insert-only MERGE claim ran on delta-spark 4.0.0.
- **Lakebase SQL:** ran on a throwaway PostgreSQL 16 through lab L23's `pglocal` helper.
- **Genealogy walk:** the pandas walk ran as written.

**Cross-module threads:**

- **Consistent:** the reconciliation and cutover vocabulary: keys before totals, five clean days, the fed fallback, and read-only federation.
- **Contradiction:** the one-writer rule was broken by the Lakebase model answer.
- **Inconsistency:** the status of TIMESTAMP_NTZ differed between the SQL Server and industry modules.

#### Altered examples (23; 17 held, 6 exposed a defect)

| Module | Where | Alteration | Held? |
|---|---|---|---|
| m08 | runbook-times extension card | window 04:15, rollback 35, verify 25, 10-min buffer → 03:05 | yes |
| m08 | offsetting visual | A=12, C=8, E=5 vs A=12, D=13: totals pass, keys fail | yes |
| m08 | transfer visual | warehouse totals equal, item X/Y offset inside East | yes |
| sqlserver | types check/visual/card 8 | 05:59:59.998 → DATETIME .997 → 3 March both paths | yes |
| sqlserver | time visual, plant state | 07:10 NY row put on 11 March | **no**: row 201 was on 10 March, which no label said |
| sqlserver | cutover gate | 13 March fails → 2 of 5, gate closed | yes |
| sqlserver | card 9 / types handbook | 500/150: T-SQL 3, Spark `/` 3.33…, `div` 3 | yes |
| warehouse-migration | tooling report | 405/420 converted, 30 of 38 equal | yes |
| warehouse-migration | validation | day-4 fix restarts the count | yes |
| warehouse-migration | lesson exercise/solution | apply the calendar rule to Spark 3.1 → no 1582 shift | **no**: the solution expected one |
| warehouse-migration | dependency | line_health moves, its writer stays | yes |
| operations | objectives, spent state | objective 82 of 84 → budget 2, 1 left | yes |
| operations | recovery window | queue 22, 3 notebook corrections lost | yes |
| operations | alert + recount SQL | fractions from the module's own recount | **no**: alert returns 0 rows |
| operations | lesson task/revisit | raw kept 60 days → 0 lost | yes |
| lakebase | idempotent intake | M-0005, M-0006, resend | yes (PG16) |
| lakebase | SKIP LOCKED claim | severity/flag-time reorder | yes (PG16) |
| lakebase | applied task | ERP 22:00 = 1, reserve 23:30, upsert 02:00 | **no**: last unit reservable twice |
| industry | contract | 1,000/10, 100/20, 900/9 → 7.33% vs 1.95% | yes |
| industry | quality check | 600/510/60/30 → FPY 85% | yes |
| industry | schedule handbook | alloy expedited to Tuesday | **no**: nothing is late, contrary to the handbook |
| industry | identity handbook | drop QUALIFY with a resend in the batch | **no**: insert-only MERGE inserts both |
| industry | genealogy | A-802 ships in SH-78 | yes |

#### Findings applied (all 9 medium and all 10 low were verified against the files and applied)

The editor re-checked each item by reading the cited files. Items marked **executed** were also run by the editor:

- the Spark checks in the lab environment at a local path outside the repository (PySpark 4.0.4);
- the Lakebase design on a throwaway PostgreSQL 16 cluster through lab L23's `pglocal.py`.

##### Medium

**1. Operations: the scrap-rate unit.**
- *Files:* `dbxfe-operations.json`, alerts handbook SQL and recovery handbook SQL; objectives visual, `spent` state and text equivalent.
- *Change:*
  - The alert compares `scrap_pct` columns, with a `-- percentage points` comment.
  - One sentence states that both columns hold percentages, and that 0.0005 would be the tolerance for fractions.
  - The recount becomes `100.0 * count_if(...) / count(*) AS line3_scrap_pct`.
  - The equation reads `|0.4% − 3.1%| = 2.7 percentage points > 0.05`.
- *Executed:* with percentages the alert returns the L3 row, and the recount returns 3.10.

**2. SQL Server: "row counts alone would have passed".**
- *Files:* `dbxfe-sqlserver.json`, semantic visual `checks` state and text equivalent; beat explanation; handbook flip summary. `dbxfe-sqlserver-l01.json`, question q1 option b rationale.
- *Change:*
  - The text now says that only the report row count passes.
  - A "Detail row count | 11 vs 7, fail" row is added to the visual.
  - The flip summary now lists the row-count failures of the WHERE and session flips (11/9 and 6/5; 6/7), and the report-value failure of DOUBLE money, as `expected/flips_p1.json` records.
  - The q1-b rationale now reads "fails every check but the report row count" (revision kept: rationale only).

**3. SQL Server: the time visual's `plant` state.**
- *File:* `dbxfe-sqlserver.json`, time visual.
- *Change:*
  - Every node label now carries its date.
  - Row 201 (10 March) is replaced by the fixture's 11 March control row 204: 05:45 NY = 04:45 CT, which is 10 March under both rules. The arrows now run in time order: 204 → 206 → 205.
  - The state explanation and the text equivalent are updated to match.
  - Checked against `fixtures/inspections_p2.json` and `legacy_detail_p2.json`.

**4. Industry: insert-only MERGE.**
- *File:* `dbxfe-industry.json`, identity handbook: SQL comment and reason sentence.
- *Change:* the text now says that an insert-only MERGE inserts every unmatched source row, so a resend in the batch lands twice with no error. Only a MERGE that also updates on match fails, with `DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE`.
- *Not re-executed here:* Delta is not installed in the editor's environment. The fix rests on the reviewer's delta-spark 4.0.0 run and on Delta's documented insert-only deduplication semantics.

**5. Industry: the schedule trade-off.**
- *File:* `dbxfe-industry.json`, schedule handbook, "The human decision".
- *Change:* the trade-off now reads "accept O-3 one day late, or pay to expedite its alloy so O-3 runs Tuesday and every order is on time".
- *Checked:* against the visual's due-date schedule, in which every order is on time once the material is ready.

**6. Warehouse migration: the Spark 3.1 calendar.**
- *File:* `dbxfe-warehouse-migration-l01.md`, solution bullet.
- *Change:* the risk is now ANSI mode, on by default since 4.0. No 1582 rebase is expected for files that Spark 3.1 wrote. The `0001-01-01` placeholders need a comparison only if the inventory finds files written by Spark 2.x or Hive.
- *Why:* this matches the module's own Hadoop beat and calendar extension.

**7. Warehouse migration: NULL ordering is not a keyed difference.**
- *Files:* `dbxfe-warehouse-migration.json`, tooling handbook, beat explanation and visual `tests` state with its text equivalent; dialect handbook "What to inspect", recap and explanation; tooling self-check model answer.
- *Change:*
  - Tooling now reads: five differences = four changed keyed values + one row-order difference, found by the report row-order comparison.
  - Dialect now says that sorts need an order-sensitive comparison.
  - The self-check model answer says "proven equal on results". Its revision moves from **1 to 2**.

**8. Operations: the "Stop writers and VACUUM" wording.**
- *Files:* `dbxfe-operations.json`, triage visual `shapes` row and text equivalent; `dbxfe-operations-l01.md`, example table.
- *Change:* now reads "Stop writers; suspend VACUUM and other cleanup".

**9. Lakebase: two writers of stock.**
- *File:* `dbxfe-lakebase.json`, applied task model answer and reasoning.
- *Change:*
  - `part_stock` keeps two facts, each with one writer: the ERP baseline (`erp_on_hand` and `erp_as_of`, written only by the nightly load), and `available`, written by the reservation's atomic conditional update.
  - The nightly load composes rather than overwrites. It locks the part row, then sets `available = erp_on_hand − reservations made after erp_as_of`.
  - The model answer names the assumption to confirm with the ERP owner.
- *Executed on PG16:*
  - The old overwrite design lets a second reservation take the last unit.
  - The composed design leaves `available` at 0 and refuses it.
  - This holds even when the load waits (`wait_event_type = Lock`) on an open reservation transaction.

##### Low

**10. SQL Server lesson excerpt.**
- *File:* `dbxfe-sqlserver-l01.md`, the `#affected_days` excerpt.
- *Change:* restored `i.plant_code = @plant_code`, as in `legacy/sp_daily_inspections.sql`.

**11. SQL Server: the decompose block.**
- *File:* `dbxfe-sqlserver.json`, decompose handbook.
- *Change:* the block now quotes the core of `run_window()` with the lab's signatures (`rows_of(df, columns, key)`, the `keep` filter), and says what was left out.
- *Executed:* the block, run against the lab's `solutions/migration.py`, gives the same state as `run_window()`.

**12. Warehouse migration: division by zero.**
- *Files:* `dbxfe-warehouse-migration.json`, dialect handbook SQL; `dbxfe-warehouse-migration-l01.md`, dialect SQL.
- *Change:* `div` is guarded with `CASE WHEN inspected = 0 THEN NULL ELSE … END`, and the handbook explains why.
- *Executed:* the original raised `[DIVIDE_BY_ZERO]`; the guarded query returns NULL for that row.

**13. Warehouse migration: q3 option c rationale.**
- *File:* `dbxfe-warehouse-migration-l01.json`.
- *Change:* the rationale now says that the federated half still fails while the source is down, and that the merge mixes two as-of times. The one-writer claim is removed. Revision kept: rationale only.

**14. Lakebase: the claim statement.**
- *File:* `dbxfe-lakebase.json`, locks handbook claim UPDATE.
- *Change:* added `claimed_at = now()`, matching `solutions/claim.sql`.

**15. Industry: NULL lot types.**
- *File:* `dbxfe-industry.json`, contract handbook SQL and "What to inspect".
- *Change:* the filter becomes `lot_type IS DISTINCT FROM 'engineering_trial'`, and a check of the NULL `lot_type` count is added.
- *Executed:* `<>` kept 2 of 4 lots, dropping the NULL one; `IS DISTINCT FROM` kept 3.

**16. Operations: severity for an unavailable figure.**
- *File:* `dbxfe-operations.json`, triage handbook severity rules; applied-task model answer and reasoning.
- *Change:*
  - A Sev 2 rule is added for a figure that a scheduled internal decision needs, when it is unavailable or may be lost and its readers have no working fallback.
  - The Sev 3 fallback condition now says "readers have a working fallback".
  - The model answer now justifies Sev 2 from that rule.

**17. SQL Server: global temporary views.**
- *File:* `dbxfe-sqlserver.json`, temp handbook.
- *Change:* one added sentence. Spark global temporary views (`global_temp`) span one application's sessions, vanish with it, are not shared across separate job clusters and carry no owner or history.

**18. TIMESTAMP_NTZ status.**
- *Files:* the SQL Server claim context; the industry claim context, NTZ extension-card explanation and NTZ source caveat.
- *Change:* one hedged wording in both modules: "documented for Databricks SQL and Runtime 13.3 LTS and above; a snippet read on 2026-09-23 marked it Public Preview; check its release status for your workspace". The card revision is kept: its prompt and answer are unchanged.

**19. m08: the label-only sentence.**
- *Files:* `dbxfe-m08-l01.md`, section `deeper`; `dbxfe-m08-l01.json`.
- *Change:*
  - The sentence is replaced with the mechanism. Classic compute runs in the customer's AWS account and network. Serverless compute runs in the serverless compute plane in the Databricks account. So the boundary a review inspects sits in a different place for each.
  - The sentence links to the AWS module, and its wording matches that module's claims.
  - The lesson `contentVersion` moves from **1.0.1 to 1.0.2**. No m08 beat, card or question changed.

#### Findings rejected

None. Every high and medium finding was confirmed, and there were no high findings. Every low finding was a small, clearly correct edit and was applied.

#### Strengths (from the review, confirmed where re-run)

- **Lab-grounded numbers.** The SQL Server module's numbers come from an executed lab, which passed 28/28. The five single-choice flips tie each defect to the check that catches it. The expected JSON confirms the corrected flip summary.
- **One consistent incident.** Operations follows INC-0412 through 15 beats with consistent arithmetic: 218 = 44 + 174, versions 312 to 318, 25 = 9 + 10 + 6, an RTO of 3 h 10 m, and a budget of 84 − 83.
- **Lakebase SQL that runs.** The Lakebase SQL runs on PostgreSQL 16, including under reordered deliveries and queues. The composed stock design was also run here.
- **Honest evidence labels.** Examples include vendor cells left unknown with owners, and Lakebridge status quoted from its package.
- **Correct industry arithmetic.** The arithmetic checks out, and so does the DST example: 1 Nov 2026 is a Sunday, with 01:30 at 06:30Z and 07:30Z.
- **Diagnostic distractors.** The checks carry a mechanism-level rationale for each wrong option.
- **Coherence.** The track reads as one sequence. m08's reversible-migration method is reused at procedure scale in the SQL Server module and at estate scale in the warehouse-migration module.

#### Checks run after editing

- `node --import tsx scripts/academy-check.ts --module <id>` for all six modules: **PASS (no failing findings)**. m08 keeps only its pre-existing warnings: l03 lacks mistakes and sources sections, and the scenario has no disclosures.
- `python3 scripts/academy-disposition.py --check`: exit 0, with `removed 0` and `revisionNotMoved 0`. The script also rewrites `docs/academy/DISPOSITION.json`.
- Every JSON file written parses. Formatting is preserved: indent 1 for new modules, indent 2 for m08, no ASCII escaping.
- Edited handbooks are 245 to 384 words, and edited explanations 69 to 89 words.

#### Limitations that remain

- **MERGE not re-executed.** Delta is not installed in the editor's environment, so the industry MERGE correction relies on the reviewer's delta-spark run and on Delta's documentation.
- **TIMESTAMP_NTZ status not settled.** Both sources were read only as search snippets, because the documentation host is blocked. The wording is now consistent and hedged; the actual status still needs a live read.
- **One m08 edit is invisible to the disposition check.** `academy-disposition.py` keys section bodies by JSON section id (`dbxfe-m08-l01-deeper`), while retained m08 lessons use short markers (`<!-- section:deeper -->`). So the m08 section edit shows only as the lesson `contentVersion` bump, not as a section revision. That is a script limitation outside this editor's scope, which is to touch module files only.
- **Other flagged snippets remain illustrative.** SQL Server snippets are still classed "illustrative" by `snippet-audit.py`. The decompose block now uses the lab's signatures, and executing it against `solutions/migration.py` gives the same state as `run_window()`.
- **Not checked by execution:**
  - platform behaviour on Databricks (serverless and classic boundaries, Lakehouse Sync, TIMESTAMP_NTZ, SQL alerts);
  - rendering of the edited visuals on desktop and phone. The `time` visual's node set changed, so its states should be captured again in the visual review.
- **Not a learner study.** No human learner took the track, and nothing here measures comprehension.

## Customer discovery, evidence and delivery

**Builder editorial review. This is not an independent human learner study.** No learners were observed. Every beat check in this track is a self-check, so learners assess their own answers. The review was carried out on 2026-09-23 by the implementing builder's reviewer and editor.

Modules: H1 `dbxfe-m01`, H2 `dbxfe-m02`, H3 `dbxfe-m09`, H4 `dbxfe-m10`, H5 `dbxfe-m11`, H6 `dbxfe-m12`. All six are retained modules.

#### How the review was done

**Reviewer.** The reviewer read the six modules in track order. For each module they read:

- every beat as `src/teaching.tsx` presents it: outcome, explanation, each visual state with its text equivalent, media, self-check and model answer, Samajh, then the handbook;
- the card links, the four extension cards, the recap and the applied task;
- the three lessons the module lists, including their questions, cards and Markdown sections;
- the module's scenario in `course.json`, its lesson SVGs and its `media.json` entries.

To check claims that cross modules, they also read `dbxfe-m04`, `lessons/dbxfe-record-resolution.md` and `capstones/dbxfe-capstone.json`. They recomputed every number by hand.

**Editor.**

- Checked every high and medium finding against the files.
- Recomputed the arithmetic by running it: +10 − 10 + 12 = 12; dropping the negative rows gives 22; dropping only the restatement gives 0; dropping both correction rows gives 10. A v2 + C = 20/1, a valid A v3 + C = 22/1, and the unkeyed rows add nothing. At 8 h/week the value is −3,960; break-even is 9.375 h/week.
- Found every instance of each defect class across all six modules, not only the instances the reviewer quoted. A scan for spacing defects covered the teaching JSON and the lesson bodies.
- Made the edits through scripts that assert each old value exactly before replacing it.
- Rebuilt changed text equivalents with a generator. Before using it, confirmed that it reproduces all 48 existing visuals exactly.

#### Altered examples

Each example below is the reviewer's changed version of a worked case. "Holds" means the module's teaching still gives the right answer for the changed case.

| Module | Where | Altered example | Hand result | Holds? |
|---|---|---|---|---|
| M01 | evidence beat and check | 50,000 synthetic rows from three plants' schemas, run locally | Three-plant reliability is still unproven | yes |
| M01 | rolled-back extension card | 6 planned: 4 switch, 1 rolls back, 1 postponed | 5 attempted, 4 migrated, 1 rolled back, 1 not attempted | yes |
| M01 | ownership beat vs lesson l02 | The security lead is on leave | Beat, ledger and revisit gave three different owners | **no, now fixed** |
| M02 | unknown-timestamp beat | 40 records, 38 on time | 95.0% meets timing; completeness still fails | yes |
| M02 | clocks beat | Approved 06:50, served 07:42; click answered in 3 s, then 1 s | 52 min freshness; 3 s then 1 s interaction | yes |
| M02 | profile-clock card | 8 refreshes × 1 min + 2 × 20 min | Mean 4.8 min, median 1 min | yes |
| M09 | correction beat | A v1 10/2, C 8/1, A v2 12/2 | 16.67% before, 15.0% after; 30 is double counting | yes |
| M09 | replay visual, change state | Only the unkeyed pair arrives | Candidate stays 20/1; publication gate closed | **no, now fixed** |
| M10 | baseline beat | Baseline 50 min; job starts 30 min after approval | Aligned candidate is 45 min, so a 5 min gain | yes |
| M10 | billing-lag card | +8 / −8 / +11 | Correct 11; drop negatives 19; drop only the restatement **0** | **no, now fixed** |
| M10 | readout beat | Correctness fails; everything else passes | Fix the defect and retest; do not expand | yes |
| M11 | arithmetic and sensitivity beats | 12 h, 50 weeks, $55/h, $10k recurring, $20k implementation | Net 3,000; recurring year 23,000; break-even 10.91 h/week | yes |
| M11 | cost beat | Add 3,000 training and 5,000 dual running | Cost 35,000; net −6,200 at 10 h; break-even 12.15 h/week | yes |
| M11 | allocation and outcome cards | 4,000 pool on a 40/60 split; 80 units, 200 attempts, 50 successes | 1,600 / 2,400; 0.40 per attempt, 1.60 per success | yes |
| M12 | value beat | 8 h/week | −3,960 | yes, but hard to read before the fix |
| M12 | priority beat | Path approved; denominator disputed | The denominator comes first | yes |
| M12 | demo-pilot visual and check | (i) conflict alone; (ii) valid A v3 = 14/1 | (i) 20/1 blocked; (ii) 22/1 comes from the correction | **no, now fixed** |

The editor re-ran the four failing cases against the edited content. All four now hold:

- **M01:** the lesson ledger and revisit now match the beat. The field engineer keeps owning progress, the specialist contributes the analysis, and the customer security lead (or an authorized delegate) accepts.
- **M09 and M12:** the "conflict alone" row gives 20/1, and a separate row gives 22/1 from the valid correction.
- **M10:** the card now says "discarding only the restatement would leave zero".

#### Findings applied

Version changes follow `docs/AUTHORING.md`:

- A beat whose teaching changed gets a new version and a change note.
- A question or self-check whose assessed meaning changed gets a new revision.
- A lesson whose sections changed gets a new `contentVersion`.
- A clarified explanation keeps its revision.

| Severity | Module | Location | Change | Version and revision effect |
|---|---|---|---|---|
| high | M10 | extension card `dbxfe-m10-extension-billing-lag` | Now says: dropping only the restatement leaves 0; only ignoring both correction records keeps the outdated 10; a zero total can mean the restatement has not arrived | Explanation only; card stays at revision 2 |
| medium | M09 | `dbxfe-m09-beat-replay`: visual state `change`, handbook worked boundary | Split into three rows. A valid A v3 = 14/1 gives the diagnostic 22/1. The unkeyed rows are quarantined, add nothing, and close the gate. The "no prior snapshot" row is kept. The handbook works the same case in full, including the "conflict alone stays 20/1" case | Beat 1.0.0 → 1.1.0 |
| medium | M09, M10, M12 | M09 bridges, explanation, handbooks and lesson l02; M10 cases handbook; M12 demo-pilot handbook | Added `dbxfe-record-resolution` as an optional bridge to M09, M10 and M12. The M09 explanation now states the conflict rule and its reason. The exercise is named, and linked, as the Reliable Data Foundations bundle. In l02, ev1 is identified as A revision 1 (10/1) from the shared five-row input, with a link to `dbxfe-m04-l02`. The reviewer had suggested "A's approved revision 2", which does not match the dataset. The l02 card4 explanation now names the exercise | M09 replay and basis beats → 1.1.0; M10 cases → 1.1.0; lesson `dbxfe-m09-l02` → 1.1.0; card4 explanation only |
| medium | M12 | `dbxfe-m12-beat-demo-pilot`: visual, check and handbook | New rows: "Unkeyed provenance conflict alone → 20/1, block" and "Valid A revision 3 while that conflict is open → 22/1 diagnostic, block". Check prompt and model answer rewritten. Inspection B and the publication policy are introduced before they are used | Check `dbxfe-m12-check-demo-pilot` rev 1 → 2; beat 1.0.0 → 1.1.0 |
| medium | M12 | `dbxfe-m12-beat-capstone` explanation | Introduces the inventory transfer case that the check asks about | Beat 1.0.0 → 1.1.0 |
| medium | M12 | capstone handbook; concept `dbxfe-m12-concept-capstone`; `dbxfe-m12-l03` try and deeper sections | Presents six core artifacts, names what the revised capstone adds, lists the added rubric dimensions, and points to the capstone's own requirement list as the contract | Same beat bump; lesson `dbxfe-m12-l03` → 1.1.0 |
| medium | M10 | `dbxfe-m10-beat-execution` explanation | Adds that usage records can arrive later and be retracted or restated, so an early empty view is an observation cutoff. This prepares the learner for the cost check | Beat 1.0.0 → 1.1.0 |
| medium | M02 | `course.json` scenario `dbxfe-m02-scenario` model | The quality lead now accepts the definition and correction rule; "Confirm all four" | Scenarios carry no revision field |
| medium | M01 | `dbxfe-m01-l02.md` see, try and revisit sections | Ledger: the field engineer coordinates, the security specialist contributes the analysis, and the customer security lead accepts. Adds a note on how the roles nest. Try and revisit rewritten to match | Lesson `dbxfe-m01-l02` 1.0.0 → 1.1.0 |
| medium | M11 | arithmetic and sensitivity beats (explanation and handbook); applied task | Restored spaces between list items and around operators | Both beats 1.0.0 → 1.1.0 |
| medium | M12 | `dbxfe-m12-beat-value-assumptions` explanation and handbook | "10 hours/week at 60 dollars/hour"; the input list separated with semicolons | Beat 1.0.0 → 1.1.0 |
| low | M11 | check `dbxfe-m11-check-arithmetic` | Uses a fresh 8-hour input: 23,040 gross, −3,960 net | Rev 1 → 2 |
| low | M02 | clocks and unknown visuals; unknown explanation and handbook; applied task | Spacing fixed; "18 of 20 (90%)"; the completeness failure is stated with its reason | Unknown beat → 1.1.0. The clocks visual edit is cosmetic, so that beat is not bumped |
| low | M10 | execution and readout visuals | "sample v1", "Transform v2: filter repaired", "Data engineer: trace timing" | Covered by those beats' bumps |
| low | M10 | `dbxfe-m10-l03-q1` | The correct option is now "Blocked, because a missing dependency (the operator) prevented the test…" | Rev 1 → 2; lesson → 1.1.0 |
| low | M10 | readout Samajh | Doors that are opened, tried but locked, and never reached map to pass, fail and blocked. The boundary adds that a readout records *why* a door is closed | Beat → 1.1.0 |
| low | M01 | `dbxfe-m01-l03-q1`; gate record in `dbxfe-m01-l03.md` | The quality owner accepts the metric definition; the sponsor accepts the evidence. The gate record's acceptor now includes quality | Rev 1 → 2; lesson → 1.1.0 |
| low | M02 | `dbxfe-m02-l01.md` stakeholder map | Adds a quality-owner row. The analyst's concern becomes reproducibility. A sentence says the diagram's analyst proposes the definition and quality accepts it | Lesson → 1.1.0 |
| low | M02 | check `dbxfe-m02-check-stakeholders` | No longer names its own answer. Three stakeholders' positions are given, and the learner must name the missing acceptance and whose it is | Rev 1 → 2; beat 1.1.0 → 1.2.0 |
| low | M02 | status visual | "CDC enabled" is now "reported by analyst (unverified)". Adds the row "CDC use permitted: assumed" | Beat 1.0.0 → 1.1.0 |
| low | M01, M02, M09, M10, M12 | sources, claims, starting assumptions; handbooks of M09 audience, M10 hypothesis, M12 priority and M12 capstone | "Another employer" → "a different company (GitLab)". "L4" removed; "no job level or readiness rating is implied". The careers page is labelled as one company's public job context | Handbook beats bumped to 1.1.0; source, claim and assumption fields carry no version |
| low | M10 | `dbxfe-m10-beat-charter` explanation and handbook | Introduces the maintenance-knowledge assistant. Says the $1,500 ceiling is the H6 capstone's unapproved planning ceiling | Beat → 1.1.0 |
| low | M12 | `dbxfe-m12-beat-handoff` handbook | Names roles: Imani (quality lead), Mara (operations director), Leo (data lead), Noor (security lead) | Beat 1.1.0 → 1.2.0 |
| low | M09 | card `dbxfe-m09-extension-next-metric` | "Pause after A's revision 2 … inspected quantity (10 to 12) and the unchanged defective count" | Explanation only; rev 2 kept |
| low | M12 | card `dbxfe-m12-extension-unit-definition` | The cross-reference now points to "the benefit-realization discipline of the value beat" | Explanation only; rev 2 kept |
| low | M02 | cards business-unit and profile-clock | "Four hours to two per week"; "that twenty-minute refresh" | Explanation only; rev 2 kept |
| low | M01 | gates visual | Adds a return arrow: Design / demo → Discovery, labelled "definition dispute". Alt text and state text updated | Beat 1.0.0 → 1.1.0 |
| low | M12 | `dbxfe-m12-l02.md` see section | The quality lead confirms correction ordering and restatement; the data lead confirms keys in the source | Lesson → 1.1.0 |
| low | M12 | `dbxfe-m12-l03-q1` | The option explains the term: "share of inspections with any defect (1 of 2) … defective units ÷ inspected units (1 of 20)" | Rev 1 → 2 |
| low | M10 | `course.json` scenario `dbxfe-m10-scenario` model | Acceptance is split to match the M10 matrix: quality plus data lead, operations plus data lead, and the operating owner | Scenarios carry no revision field |
| low | M12 | demo-pilot handbook and visual | Inspection B introduced ("a third inspection, never published"); bridge added | Covered by the demo-pilot bump |

#### Findings not applied

**Media limits typos (M02 and M11).** The typos are in `dbxfe-m02-media-episode.limits` and `dbxfe-m11-media-objection.limits`. The finding is valid, but it is not applied because `content/teaching/dbxfe/media.json` is a shared register outside this pass's editable files. Text for the integrator to apply:

- "from 2008; the linked YouTube upload is from 2017."
- "The lecture date (26 January 2012) differs from the YouTube upload date (6 February)."

**M02 diagram SVG and its asset record.** These still show the analyst supplying the metric definition and no quality owner. The SVG under `content/assets/` and its asset record in `course.json` are outside this pass's scope. The lesson text now states the relationship instead.

**Optional relabel of M01's delivery row ("Recovery: Not tested").** Not changed, because it is already correct:

- In M01 the rehearsal has not been attempted and the operator is only proposed. That is "not tested".
- The M10 q1 case, a test that could not run because its operator was unavailable, is "blocked".

Both labels follow the M10 definitions.

#### Strengths the reviewer confirmed

- Every figure the reviewer recomputed is correct except the billing-lag clause, which is now fixed.
- One Cinderline thread runs from M02 to M12: the A/C correction, the 95%-within-60-minutes criterion and the 5/10/15-hour range. Each module then moves the method to a new domain, which tests transfer rather than recall.
- The track teaches the words for how much evidence supports a claim and then reuses them from module to module. Examples are capability, hypothesis and evidence; pass, fail, blocked and not tested; and agreed, observed and open.
- The mechanisms are taught, not just labelled. M02 works through both illegitimate fixes for a missing timestamp. M09 shows a defect rate falling although no defect was removed.
- Doing less is always a legitimate outcome, so the track does not drift into sales advocacy.
- Product statements are dated, attributed and scoped to edition and cloud, and they never rank vendors.
- Every Samajh states where its analogy stops, and the visuals carry full text equivalents.

#### What remains a limitation

1. **M12 describes a capstone version that is not yet integrated.** The M12 handbook, concept example and lesson l03 describe the revised capstone in `capstones/dbxfe-capstone.json`, which has 12 requirements and 10 rubric dimensions. `course.json` still carries the 6-requirement, 6-dimension version. Until the integration step replaces it, the practice page will not show the added sections that M12 names.
2. **Some bumps are for spacing only.** The disposition gate requires a version change for any explanation or handbook edit. So the M11 arithmetic and sensitivity beats, the M12 value beat and the M02 unknown beat are bumped for spacing fixes. Learners who completed them will see them marked revised.
3. **Revised checks will show a notice.** Six checks moved to a new revision: `dbxfe-m01-l03-q1`, `dbxfe-m10-l03-q1`, `dbxfe-m12-l03-q1`, and the self-checks `dbxfe-m02-check-stakeholders`, `dbxfe-m11-check-arithmetic` and `dbxfe-m12-check-demo-pilot`. Earlier attempts will show a revised-question notice, as designed.
4. **Some lesson changes are not visible to the disposition script.** It keys legacy lesson sections by kind, so it cannot see body changes in them. Those changes are recorded only through the bumped lesson `contentVersion`s.
5. **Course-level change notes were not updated.** These are `course.json` `changeNotes` and `CHANGELOG.md`, both outside this pass's scope. The integrator should add a line.
6. **Changed visuals have not been rendered.** No browser rendering was done in this pass. The visual-review gate should capture:
   - M01 gates
   - M02 status, clocks and unknown
   - M09 replay (change state)
   - M10 execution and readout
   - M12 demo-pilot
7. **The lesson-only fixes are text, not assessment.** The M01 ownership and M02 stakeholder fixes are text changes in retained lessons; no assessment in those lessons exercises them.

#### Checks run

- `node --import tsx scripts/academy-check.ts --module <id>`: PASS (no failing findings) for all six modules, before and after the edits.
- `python3 scripts/academy-disposition.py --check`: exit 0, with 0 removed and 0 `revisionNotMoved`. At course level, only the two scenario models changed (`dbxfe-m02-scenario` and `dbxfe-m10-scenario`).
- Every JSON file written parses.
- Whole-course tests, run in an isolated copy that leaves out only another agent's unregistered `dbxfe-sharing` teaching file:
  - `tests/teaching-content.test.ts`: 57/57 pass.
  - `tests/content.test.ts`: 28/28 pass.
- In the live tree, `tests/teaching-content.test.ts` fails, but only with "Unknown teaching module dbxfe/dbxfe-sharing". That module is concurrent work in progress, not something this pass changed.
- Git: no state-changing commands were run. A concurrent agent's commit `0bc5eac` included `course.json` with the two scenario edits from this pass already in it.

## Field guides FG01–FG16

**Label: builder editorial review.** This is the builder's own review and repair
pass. It is not an independent human study and not official Databricks
training. Scope: the 16 metadata JSON files and 16 Markdown bodies
`content/courses/dbxfe/guides/guide-fg01-*` to `guide-fg16-*`. No other file
was edited. The capstone, its rubric and disclosures, and the Cinderline data
pack are unchanged, so the data pack does not need repackaging.

#### Items opened

- All 32 guide files, FG01 to FG16, read in full before and after editing.
- Reference only, not edited: `academy.json`, `course.json`,
  `src/content-schema.ts`, the capstone `.md` file, and the data pack
  (`README.md`, `stakeholder-statements.md`, `source-inventory.csv`,
  `flawed-metric.md`, `quality-events.csv`).
- Lessons checked: `dbxfe-record-resolution`, `dbxfe-m06-l02`,
  `dbxfe-sqlserver-l01`, `dbxfe-spark-execution-l01`, `dbxfe-genie-l01`,
  `dbxfe-sharing-l01` and `dbxfe-aws-l01`.
- Teaching modules checked: `dbxfe-finops` and `dbxfe-genie`.
- Continuity: a previous, interrupted editor session in this same editorial
  pass had already changed the FG01–FG04 bodies. Those changes were checked
  against each finding and kept. They are recorded below as applied.

#### Findings applied (all 8 high and 16 medium; 13 of 14 low in full, FG14 low in part)

##### High

| # | Guide | Location | Change |
|---|---|---|---|
| 1 | FG09 | Conflict policy; Expected; version line | A conflict now blocks any new report. The last verified snapshot stays visible and is labelled stale; with no earlier snapshot the state is "blocked, no snapshot". Candidate totals are diagnostic only. Adjudication is recorded, plus a higher version in the corrections file; a later version alone does not clear a conflict. This now matches the record-resolution lesson, the capstone's stage 3 and the quality lead's statement. The change carries through FG03 F3 and its acceptance row, the FG11 numerator and the FG13 tile counts. |
| 2 | FG10 | Failure classes; rule paragraph; rehearsal | The invalid row is split in two. A never-valid inspection is excluded and disclosed, and the rate publishes. An invalid or unorderable latest version after a valid state holds the new report. A conflict holds the new report, with the last verified one shown as stale. The rehearsal is restated as held (19 accepted, 1 unresolved, 1 excluded), then published after adjudication (20 accepted, 1 excluded). |
| 3 | FG09 | Test sequence and Expected | The arrivals were rewritten and the expected counts corrected: one inspection unresolved (A), two excluded (B, E), two conflict records, candidate 0 of 8 not published, 1 of 22 after adjudication. The expected output was checked against the lesson's reference resolver (C v1 plus D v2 accepted; event and key-and-version conflicts; excluded B and E; `blocked_no_snapshot`; 22/1 after adjudication). |
| 4 | FG16 | Baselines; Split; Results | Option (b) chosen. The periods are now 48, 12 and 12 weeks: 1,344, 336 and 504 oven-days, with 168 on unseen ovens. Class balance is 84 in 2,184 (3.8%). Warnings a day were recomputed over 84 test days (0.37, 0.40, 0.24, 0.26, 0.13, 0.14). The lower-threshold alternative is now 2.9 a day. |
| 5 | FG16 | Results; Reading; Decision | Rule rows added per oven group: 4 of 11 with 20 warnings on training ovens, 3 of 7 with 11 on unseen ovens. They sum to 7 of 18 and 31. The reading sentences and the decision are derived from these rows. |
| 6 | FG06 | Matrix; tests; Gaps; Conclusion | Added a platform-admins row (deny by policy) and a test for the steward's MODIFY. The steward's reads moved to Positive tests. Untested cells are listed. The conclusion now reads "Six of eight expected denies exercised", naming which two are not. |
| 7 | FG05 | Conclusion | Now says "most" unconfirmed items. Hop 3's owner is itself unconfirmed, and the plant-to-workspace route (hops 1 and 5) is unconfirmed too. |
| 8 | FG07 | Workload 1 | The job starts at 6:45 to absorb an export up to 45 minutes late, and publishing takes 5 minutes, so the run may take 40 minutes. "May take an hour" is removed. The evidence threshold is now an export after 6:45. FG08's condition is aligned to 6:45. |

##### Medium

| # | Guide | Location | Change |
|---|---|---|---|
| 9 | FG03 | Acceptance | F4, F5 and N5 now have acceptance rows. The sign-off says every requirement has a row (prior session; verified). |
| 10 | FG04 | Tradeoffs; Assumptions | The causal claim is now an assumption marked "Guessed, 16 March; D measures it" (prior session; verified). |
| 11 | FG04 | Status; Options; Assumptions | Dated status and decider added. The options are now a table with the same columns for each. Every assumption is dated (prior session; verified). |
| 12 | FG06 | Principals; Matrix; Gaps | Platform-admins deny is by policy. The compensating control is named, hedged to current documentation. |
| 13 | FG07 | Workload 2 | "Not re-executed for each of the eleven viewers" replaces the headcount figure. |
| 14 | FG08 | Managed connector row | Now requires change tracking or CDC on the source tables (the same ungranted DBA permission), plus confirmed support, per current documentation. |
| 15 | FG08 | Freshness; Conditions | Restatement happens on the next nightly run, marked. The reversal condition is now an intraday run over new correction files. |
| 16 | FG08 | Sources; Replay; Change-capture row | ERP rows are updated in place with no revision, so a re-run returns current state and the retained raw export replays a night. Change capture misses the CSV corrections and changes past its retention; schema changes are checked in documentation. The watermark is now modified-time. |
| 17 | FG09 | Ordering; Test sequence | Validity rule added: non-negative integers, defective no more than inspected. The sequence now covers redundant evidence (ev7), an older version after a newer one (ev10), a voided 0/0 state (ev9 D v2), a different-event key-and-version conflict (ev8), and an unorderable record (ev6 on E). |
| 18 | FG11 | "Why the two existing reports disagreed" | Rewritten to the data pack: 7.1%, 10.8% and 5.0% on 2 March. The workbook is a mean of row rates by load date that keeps duplicates and superseded revisions; the sheet sums pasted rows including a negative adjustment. "Neither was wrong" is dropped. |
| 19 | FG12 | Observations; Hypothesis; Experiment; Conclusion | Recorded a sort-merge full outer join with adaptive execution on and no skew split. The slow task read 31,618 rows (4 MB, below the 256 MB default cited in the A4 lesson) and wrote 6.66 million. East's correction rows also carry the placeholder (212 of 400); 31,406 × 212 = 6,658,072. Quarantine is now 31,618 records. |
| 20 | FG13 | Freshness; Access; action step 4; template | Each viewer's own credentials run the queries, hedged to current documentation. The owner row no longer runs as the nightly service principal. A held or not-updated report shows the last verified day as stale. The action step and template now ask for the credential mode. |
| 21 | FG14 | Scope; Failure classification; template | The accepted table is the only table in the space. A `line_rate` SQL function is registered as the trusted asset and the example SQL is listed separately. The wrong-table remedy now uses instruction and example. |
| 22 | FG14 | Table; Reference computation; Review | The unauthorized case is now run as `test-outsider`, who has access to the space but no SELECT, so it can fail. Quarantine moved to "cannot answer". Example-covered questions are scored apart from the 21 novel ones. This matches the Genie lesson's rows (Friday 3.9%, Thursday 4.8%, line 2 Tuesday 5.3% to 4.9%). |
| 23 | FG15 | Action step 2; example; template | One comparison per direction. Cinderline to Halvern: copy, share, or Halvern querying a Cinderline endpoint. Halvern to Cinderline: extract, a Halvern share, or federation. The decision follows from each table. |
| 24 | FG01, FG08, FG09, FG10 | Facts | FG01: the analyst's six hours (prior session). FG08: no ERP revision, corrections on Fridays and ad hoc. FG09 and FG10: corrections never touch the ERP, and versions come from the corrections file. |

##### Low (applied unless noted)

- FG01: date column, "What would stop this", one owner per unknown, ceiling
  and timing constraints (prior session; verified).
- FG02: operations director among the blockers, conflicts grounded in the
  table's quotes, attendees, dated scope, revision log (prior session;
  verified).
- FG03: Exclusions and Sign-off sections (prior session; verified).
- FG04: the status line waits on the security review and an operator (prior
  session; verified).
- FG05: "Confirmed or not" column; a hop 1 failure (renamed table in a saved
  query).
- FG06: the malformed row now has its Reason cell; the steward's raw read
  moved to Positive tests; "one synthetic line, five test days"; grants go "to
  groups and the service principal".
- FG07: auto-stop after 10 idle minutes (about 8:25), per the FinOps
  module's idle-minutes semantics; the warm-up moved to 7:25; Assumptions
  section added; paging owner added.
- FG09: "Equal versions either conflict or ... collapse to one state";
  action step 5 and the template now reflect the blocking policy.
- FG10: Notification section; reused identifiers detected by the resolver
  against history; action step 4 and the template use the new vocabulary.
- FG11: half-open day; daylight-saving rule by local calendar date (23 or 25
  hours; untested); "no inspected units" for a zero denominator; date and
  change log.
- FG13: validation values tied to lines (line 2, day 2: 20, 1, 1; line 4,
  day 5, empty); the conclusion names one primary action and two supporting
  uses.
- FG14: as-of date (Monday after days 1 to 5); wrong-table remedy; a hedged
  sentence on the product's benchmark feature and the Genie Agent name;
  template names trusted assets and the as-of date.
- FG15: JSON summary says "planned revocation rehearsal". The Halvern DBA's
  position is now a dated refusal (18 March), which agrees with the sharing
  lesson's "declined".
- FG16: Run record section with synthetic placeholder identifiers.

#### Findings rejected (with reason)

- **FG14: add `dbxfe-genai` to `moduleIds`.** Rejected. It would give the
  guide three modules beyond its academy listing, which the guide checker
  refuses (two at most). The schema only requires lesson ids to exist, and
  `dbxfe-m07-l03` exists and is linked in the action section.
- **FG14: draw the empty run-log table in the example.** Not applied. The
  example says the run log is "empty so far". The template keeps the table.
  The example is at 697 of the 700-word bound, and an empty table adds no
  information.
- None of the high or medium findings was rejected. Each was reproduced
  against the files and the course sources before it was changed.

#### Strengths confirmed

- Every guide keeps its four section markers in order, and its ids are
  unchanged.
- All 16 bodies parse against `guideSchema`.
- The links, templates, honest mixed outcomes and the stated-versus-measured
  discipline that the reviewer noted are all preserved.
- Cross-guide figures agree:
  - 19/1/1 becomes 20/1/1 after adjudication in FG10 and FG13.
  - 4.8% for line 3 on day 4 appears in FG13 and FG14.
  - The day-2 restatement of 5.3% appears in FG13 and FG14.
  - The 6:45 export threshold appears in FG07 and FG08.
  - Each figure also matches the Genie and sharing lessons.

#### Checks run

- JSON parse of all 16 metadata files: pass.
- `guideSchema` parse (a local path outside the repository, Node 24.19.0): 16/16
  schema OK.
- `check_guides.py` as given: it exits with `KeyError: 'lessonFiles'`.
  `course.json` changed concurrently and now lists 24 modules as
  `{"file": ...}` references.
- A copy of the checker that resolves those references
  (`editorial/guides-a-run/check_guides_resolved.py`): ALL OK. It checks the
  word bounds (every example now 684 to 699 words; action at most 291), the
  links, the module-link count and the JSON contract.
- The FG09 test sequence was run through the record-resolution lesson's
  reference resolver, and its output matches the hand-authored expectation.
- The FG12 and FG16 arithmetic was recomputed by script.

#### Remaining limitations

- No web search in this pass. These product statements rest on the course's
  own recorded lessons and are hedged where the course is:
  - AQE's 256 MB default
  - change tracking and CDC for the connector
  - dashboard credential modes
  - the Genie benchmark feature and its naming
- FG12's join strategy is a fictional observation. It was not executed on a
  runtime.
- The examples sit close to the checker's 700-word bound. Further additions
  need matching cuts.
- `check_guides.py` needs the module-reference fix before others rely on it.
  That script was outside this scope and was not edited.

## Field guides FG17–FG32

**Builder editorial review.** This is not an independent human study. A builder reviewer produced the findings. The editor re-verified each one against the files, recomputing the arithmetic by hand and in Python, and then applied the fixes below. No git, node or network command was run.

#### Scope and items opened

- All 32 files in scope: `content/courses/dbxfe/guides/guide-fg17-*` … `guide-fg32-*`, each `.json` and `.md` read in full.
- References, read only:
  - `content/exercises/capstone-cinderline/stakeholder-statements.md`, `quality-events.csv` and `source-inventory.csv`, for the canonical names (Mara, Imani, Leo, Noor, Elena, Arun, Dev, Sam, Priya), the $1,500 ceiling, the 12,000 and 15,000 figures and the 22:10 package.
  - `academy.json`; `course.json` module titles, including package files; the teaching-module titles; the Field guides section of `docs/AUTHORING.md`.
- This pass continued an earlier, interrupted one. That pass had already applied the FG17–FG22 edits, recorded as scripts in `editorial/fg17-32/edits/fg17…fg22.py`. Each of those edits was re-checked against its finding before this pass continued. The pre-edit snapshot is in `editorial/fg17-32/before/`, matching `before.sha256`.

Only the 16 `.md` bodies changed. All 16 `.json` files are byte-identical to the snapshot and parse. Ids, `bodyFile` values and the four section markers are unchanged. No capstone data pack file changed, so no repackaging is needed.

#### The Cinderline pilot storyline, aligned (medium finding, anchored at FG30)

The examples in FG21–FG32 now tell one sequence. Pilot days are staffed reporting days, and day 1 is Monday 9 March 2026 (FG27).

| When | What happens | Guides |
|---|---|---|
| Before the pilot | Discovery call (10 Feb), demo (19 Feb), charter draft (24 Feb), alternatives memo (26 Feb) | FG24, FG25, FG26, FG27, FG29 |
| Baseline week, 2–6 Mar | The current path is measured on both freshness measures, and reconciliation effort is logged | FG26, FG27, FG29 |
| Before day 1 | The security lead approves real data as an *approved sample* (plant-one fields, nightly export route) after a specialist review of that route. The live source-path review has not started. | FG30, FG32 |
| Days 1–5 | First reconciliation; not accepted | FG22 |
| Days 6–10 | Clean run. Day 8: injected-failure recovery in 14 min and the platform replay. Day 9: resolver failure; the rate is shown stale, nothing wrong is served. | FG27, FG30, FG31 |
| Day 10 | Ledger; readout requests a second run on three named conditions | FG27, FG30 |
| Days 11–15 | Second run; access review on day 14; rollback rehearsed on day 14 (12 min) | FG23, FG32 |
| Day 16 | Cutover. Fallback to day 35; backup covers week one only; reviews on days 18, 20 and 25 | FG23, FG32 |

Each figure now belongs to one event:

- **14 minutes**: only the day-8 injected failure.
- **3.5 hours**: only the week-one total.
- **406 / 18**: only FG22's day 5. FG31's snapshot figures are now 409 / 17.
- **Day-9 failure**: FG27 rows 6, 10 and 11 and FG30 now include it.
- **Replay**: FG27's platform replay is recorded as row 12 (day 8), which supersedes row 4 without editing it.
- **Analyst workbooks**: the two known workbooks stay on the old table, and the third reads the old table, in every guide.

#### Findings applied

##### High (all confirmed and fixed)

- **FG17, Results row "Unauthorized" and Reading the table** (earlier pass, re-verified): the attribution now says "Provisional pass … (wrong stage)", and the open question is whether the platform's filter can be applied at retrieval (data lead).
- **FG21 counts, example intro and the note under the excerpt** (earlier pass, re-verified): "Eleven further procedures, two further import jobs and twenty-one further reports". That gives 3+11=14 procedures, 1+2=3 import jobs and 1+21=22 reports.
- **FG21 scope boundary, example intro** (earlier pass, re-verified): the sensor historian is out of scope. Sensor data enters only through `sensor staging`, read by the two procedures carded in the inventory.
- **FG22 day 5, Key comparison, Totals and the day-5 paragraph** (earlier pass, re-verified and trimmed). Both defects are now in the old path:
  - The five keys only in old are trailing-space, null-revision copies.
  - The five keys only in new are rows the old path's collation-sensitive join loses.
  - Old = 401+5 = 406 and new = 401+5 = 406. The two groups cancel by coincidence, and the text says so.
  - The null-revision quarantine stays on day 5, because the copies carry the null revision. This keeps FG27 rows 8–9 aligned.
- **FG25, failure list row "Replay"**: changed to "32 / 2 instead of 20 / 1". A double-counted A v2 gives 12+12+8 = 32 inspected and 1+1+0 = 2 defective.
- **FG28, "Which input flips the sign"**: at 10 hours, year one turns positive only if realization reaches about 0.99 (28,500 / 28,800), or about 0.94 with no dual operation (27,000 / 28,800).
- **FG29, example intro and matrix column B**: the memo is now dated 26 February 2026, before the pilot. B's cells hold only what existed then:
  - "Unknown: no platform run yet; measured from pilot day 1"
  - "Replay shown locally (demo log, 19 Feb); platform recovery unrehearsed"
  - "data lead estimates under an hour a day (25 Feb)"

##### Medium (all confirmed and fixed)

**FG17–FG22 (fixed by the earlier pass, re-verified)**

- **FG17, steps 1, 2 and 5**:
  - freshness is given for each collection;
  - the three blocking failures were agreed in writing before the run;
  - a run record is added;
  - the two missing case classes are listed and added before the rerun.
- **FG18, cross-user case and boundary row**: the result is labelled a stub test. The platform run with two real identities is pending and is a launch blocker.
- **FG19, Findings**: the platform rerun now covers the denied, replayed and timed-out cases with the real delegated grants.
- **FG19, Idempotency**: the key is now a client-generated intent id, and the matrix gains a "Second note" case.
- **FG20, three fixes**:
  - `reviewer` is removed from ClaimRequest; identity comes from the platform, and a body naming a reviewer is rejected.
  - A "View the queue" trace is added.
  - An invariant that the disposition and status commit together is added, with its test, the isolation relied on and recovery.
- **FG21, inventory excerpt**:
  - Schedule, Volume and Last change columns are added, and the owner is named (Dev).
  - The pilot's unknowns are rated medium, and the pilot starts only when the first two conditions close.
- **FG22, day-3 row**: two late-arriving inspections (new keys), with the as-of rule violated.

**FG23–FG32 (fixed in this pass)**

- **FG23, Cleanup deferral**: a new section covers nothing deleted before day 35, who accepts the cleanup, and the two conditions on the workbooks.
- **FG23, Entry conditions**: the operator row now reads "Partly met" (the backup covers week one of four) and is verified by the operations director. Reconciliation is verified by the quality lead. The data lead, who gives the technical go, verifies no condition. The backup gap is a named risk, reviewed on day 20.
- **FG24, After the session**: the denominator and the approval rule are proposed definitions, confirmed in writing the next day. The restatement remark is now an open charter question, because the demo itself moved a reported rate from 5.56% to 5%. FG26's roles table was aligned with this.
- **FG25, failure list and What happened**: the time box, the offline-diagnosis owner (data lead) and the retest owner (presenter) are now in the plan written the day before. During the meeting the presenter follows that plan rather than improvising.
- **FG26, Baseline and Criteria**:
  - Freshness is now "served by 07:45 plant time, and within 60 minutes of source availability, on at least 4 of 5 days".
  - The baseline records clock time, and the baseline week measures both freshness measures.
  - One sentence says what each part tests.
- **FG27, ledger row 9**: now reads "A null revision is invalid | Nobody; the resolver assumes it and quarantines such rows".
- **FG27, ledger rows 7 and 10**: row 7 is split.
  - Row 7 is the current reconciliation effort, measured on the current process in the baseline week: 5.5 h, which contradicts the 2–4 h estimate.
  - Row 10 is the pilot operator's daily log for days 6–10 (0.5, 0.4, 0.9, 1.6, 0.4 h). It is tied to the per-day criterion and is contradicted on day 9.
- **FG27, sources and dates**: every row now has a named person with a date, a dated document, or a concrete path or run id, and the example states day 1's date and the time zone.
- **FG28, Inputs and Excluded**: the 12,000 is labelled as supplied, with its coverage not stated. Operator effort is explicitly excluded, with the reason and its size (about 240 h, or 14,400, more than the 9,600 base recurring net). The flip section points to this.
  - The line was not split, because the 12,000 is the sponsor's canonical figure and splitting it would invent a breakdown.
- **FG29, criteria and matrix**: good and poor definitions for every criterion are added, and each cell has a source or reads "unknown", with its owner.
- **FG30, Business meaning**:
  - Freshness "cannot be judged until the operations director defines when the clock starts".
  - The latencies are quoted as 47–71 minutes.
  - "A rate the quality lead accepts" replaces "both accept".
- **FG30, Cost on its basis**: incurred cost is measured over days 1–10: $410 against the hypothetical $1,500 ceiling, and 7.3 operator hours (3.5 + 3.8).
- **FG30, real data and the review**: "What was tested" names the approved sample and who approved it. The second run stays inside that sample, and the security lead's written confirmation is one of the three conditions.
- **FG31, Impact**: no downstream effect was sent because the nightly run failed before the notification step and the reruns ran the resolution task alone. `snap-0319-a` is retained and unpublished.
- **FG32, Adoption precedes the access review**: the access review is on day 14 and cutover on day 16, and the workbooks stay on the old table.
- **FG32, single points of failure**: all four components without a backup, and the unasked director, are carried forward with the review that looks at them (day 20 or day 25).
- **Storyline**: aligned, as in the section above.

##### Low (applied)

- **FG17**: the conclusion now reads "Not ready to start the pilot", and the rerun set is corrected.
- **FG18**: sections for system and scope, expected outcome per case, and re-review triggers are added.
- **FG19**: the logging fix is moved to the validation layer, and audit storage and retention are given.
- **FG20**: the dated `claimed_at` replaces the placeholder, and the owners of the open questions are named.
- **FG22**:
  - thresholds are marked as fixed before the run;
  - the exception names Imani and a date;
  - rows for days 1–2 are added.
- **FG23**: one day scheme (rehearsal on day 14, cutover on day 16).
- **FG24**: a timed rehearsal (14:20 against 15:00) and a Label column are added.
- **FG25**: the failure time now reads "5:00 delivered; 5:10 error".
- **FG26**:
  - replay and recovery are accepted by someone other than the executor;
  - the operator is named "Oskar", which is unused elsewhere (FG23 and FG32 as well);
  - the change log is dated.
- **FG27**:
  - "Charter criterion (freshness)" replaces "Charter hypothesis";
  - "all seven fields";
  - row 2 was removed from the shown rows for length, so its month/five-weeks mismatch no longer appears.
- **FG28**: the dual-operation input is ordered 3,000 / 1,500 / 0 (low / base / high), and the measurement claim is corrected.
- **FG29**: option A's reversibility is filled in.
- **FG30**: the three conditions are named, and the review date is given (day 10, 16:00).
- **FG31**:
  - the nightly run id `r-8814` is added, and every run is listed with its time;
  - "all three failed runs";
  - the local runs are said to have stubbed the lookup;
  - one question goes to the specialist, with the second deferred.
- **Link labels**: FG19 and FG31 now read "Orchestration and recovery", and FG23 and FG29 read "Architecture and migration", matching the displayed titles.

##### Same-class defects found during the sweep, and fixed

- FG22's example had grown to 729 words after the earlier pass; it is trimmed to 686.
- FG32's action section linked only one module, and the checker requires 2–4; "Field execution and capstone" is added.
- FG29's option A cited the trailing-space defect, which is only discovered on pilot day 5. It now cites the retry duplicates the DBA had already reported (Dev's statement).
- FG26's prerequisites still said the baseline effort would be measured in week one; this is corrected to the baseline week.
- FG23's rehearsal finding "backup added to alerts" contradicted FG32's day 9 and is removed.
- FG23's third workbook "reads the new table" contradicted FG30 and FG32; it now reads the old table and blocks cleanup.
- FG27 and FG30 still said the SQL Server version was not supplied, although FG21 makes the pilot conditional on it. The open item is narrowed to the topology.
- FG31's ids are aligned with the dated calendar: `q-0319`, `snap-0318-a` and `snap-0319-a`.

#### Findings rejected

None. Two findings were fixed in a different form from the one suggested:

- **FG26 freshness**: the reviewer suggested keeping the 60-minute latency as a diagnostic only. It stays as the second part of the criterion. The hypothesis is tested by clock time, and the ledger's and readout's open question about when the clock starts still decides the result.
- **FG22 day 5**: option (a) was applied, but the null-revision quarantine stays on day 5, attached to the duplicate copies, instead of moving to another day.

#### Strengths confirmed

- Every body has exactly the four markers, and every template is blank.
- Every limits section says what the guide cannot establish and when to escalate.
- Every link resolves.
- The outcomes are honest and mixed: FG17 is not ready, FG22 not accepted, FG27 has a failed criterion, and FG30 has one criterion not yet judged and one blocked.
- The examples keep synthetic, stub and local evidence visibly labelled.
- Every organization in the examples is fictional. No public case analysis is in scope.

#### Checks run

- All 16 JSON files in scope parse and are unchanged.
- The requested a local path outside the repository exits 1 before checking anything: it raises `KeyError: 'lessonFiles'`, because course.json modules are now `{"file": …}` package entries, and it covers only FG01–16. It was not modified.
- `editorial/fg17-32/check_guides_17_32.py` applies the same rules (markers, word bounds, headings, link forms and targets, 2–4 module links in the action, JSON keys, ids, module and lesson ids) with package-file resolution. Result: **ALL OK** for FG17–FG32 (`check-after.log`).
- A presence check confirmed every applied fix above in the files.

#### Remaining limitations

- The guides are not yet registered in course.json, so the real build has not validated them. The shared checker needs the package-file fix before it can cover them.
- Several examples now sit at 697–700 of the 700-word bound, leaving no room for additions.
- FG24 and FG25 remain alternative tellings of the same demo, one where it succeeds and one where it fails. Each is labelled hypothetical, and neither was changed.
- FG18's attack cases remain prose, each with its expected and observed outcome, rather than the template's table.
- FG20's example reviewer id `leo.d` shares the data lead's first name. It was not flagged and was not changed.
- Nothing in these guides depends on external documentation, and no platform behaviour is asserted beyond what is hedged in the text.

## Case analyses and crosswalk

**This is a builder editorial review, not an independent study.** The editor checked each high and medium finding from the builder's review against the repository and, where possible, against search results. The editor then applied or rejected each finding. Edits were limited to `content/courses/dbxfe/cases/*`. No capstone file, data pack or guide was changed (`dataPackChanged: false`), and no git command was run.

#### Items opened

- All 17 files in scope, read in full before and after editing:
  - `content/courses/dbxfe/cases/case-*.json` and `case-*.md`, for all eight cases: att-hadoop-event-migration, barilla-factory-operations, coinbase-soon-ingestion, cvs-health-knowledge-rag, getyourguide-warehouse-unification, nab-warehouse-decommission, petrobras-mlops-automation, rivian-delta-go.
  - `content/courses/dbxfe/cases/crosswalk.json`.
  - A pre-edit copy of all 17 is at a local path outside the repository.
- Read-only supporting files:
  - Schemas and rendering: `src/content-schema.ts` (case, source and crosswalk schemas, body audit), `src/collections-model.ts` (`reporterText`), `src/collections.tsx` (`CaseFacts`, `ModuleLinks`, `Crosswalk`), `src/markdown-audit.ts`.
  - Course structure: `content/courses/dbxfe/academy.json`, `content/courses/dbxfe/course.json` (module titles), `docs/academy/CONTRACT.md`, `docs/academy/MODULE-SPECS.md`, `docs/AUTHORING.md`.
  - Teaching content: `content/teaching/dbxfe/dbxfe-spark-execution.json`, the teaching-file titles, and lessons `dbxfe-deep-learning-l01`, `dbxfe-ai-platform-l01`, `dbxfe-delivery-l01` and `dbxfe-apps-l01`.
  - Scripts: `scripts/content.ts` and `scripts/academy-source-review.py`.
- Search re-check on 2026-09-23. The reviewer's session had used up its search budget; this session had budget left. Ten WebSearch queries were run, on:
  - the Petrobras session speakers;
  - the CVS session speaker, and its YouTube listing and date;
  - the Rivian Delta-Go post, and its date and author;
  - the GetYourGuide serverless and IP-range snippet (once open, once restricted to `getyourguide.careers`);
  - Coinbase SOON's earlier architecture (restricted to `coinbase.com`);
  - the NAB 95 percent figure (open, then restricted to `databricks.com`), and the author of the LinkedIn post.

  All results are search-level only: titles, URLs and the search tool's summaries. No page was opened.

#### Findings applied

##### High

1. **Rivian: reporter was labelled "joint"** (`case-rivian-delta-go.json` `reporter`; `.md` "Who reports this and how"). Confirmed. The reporter is now free text: `Delta Lake project blog (author not verified)`. The body says authorship is not visible and records the reporter as the project blog with its author unverified. The summary now opens "A Delta Lake project blog post describes…".
2. **CVS: summary turned headcount into platform reach** (`case-cvs-health-knowledge-rag.json` `summary`). Confirmed. Search confirms that 300,000+ is the organisation's headcount. The summary now reads: the organisation "reportedly employs more than 300,000 people … no user or adoption count is visible".
3. **Crosswalk "Get Started With Generative AI": claimed "the same ground as F1 to F3"** (`note`, `moduleIds`). Confirmed. F1 to F3 do not teach fine-tuning, and "the same ground" claims equivalence.
   - The note now names which related modules teach prompts and retrieval, retrieval engineering, evaluation, fine-tuning and platform governance, and says "No equivalence is claimed."
   - `dbxfe-deep-learning` and `dbxfe-ai-platform` were added to `moduleIds`.
   - One correction to the reviewer's wording: the note says fine-tuning "is taught", not "planned". `dbxfe-deep-learning-l01` now exists and teaches fine-tuning versus retrieval.
4. **NAB: two figures without a source in "Architecture as described"** (`.md` Architecture, Missing information). Confirmed.
   - The 456-use-cases figure is deleted; no source for it was found.
   - The 95 percent figure now has a source. It is a LinkedIn post whose title is "NAB migrates 95% of workloads to Databricks SQL, boosts ...", by a Databricks employee according to the author's profile title in search results. Search restricted to `databricks.com` did not find the 95 percent figure on the customer page.
   - The post is recorded as a second source, `case-nab-warehouse-decommission-social-post`. The figure moved to "Evidence and its limits", attributed to that post, with what it counts marked unknown.
   - Missing information now asks what the 95 percent counts.

##### Medium

5. **NAB summary stated requirements as achievements and implied a complete move.** Confirmed as an inconsistency. The summary is rewritten: the counts describe the old estate, and the vendor's claims are attributed to the vendor.
   - Search shows the customer page itself states "safeguarding regulatory compliance and uninterrupted business processes" as an outcome. So the new summary says "the vendor says…" rather than the reviewer's "stated as requirements".
   - The Constraints and Evidence sections were aligned with this. Architecture now opens "Per the vendor…".
6. **GetYourGuide: contradictory serverless sentences** (`.md` Architecture). Confirmed.
   - Search restricted to `getyourguide.careers` shows the blog's own snippet saying Databricks serverless compute, used for serverless SQL warehouses, runs in a compute layer within the Databricks account with its own IP range. The snippet also names the VPC and MySQL RDS database behind the external Hive metastore that had to be made reachable.
   - The sentence is rewritten to attribute this to the blog. The claim "unconfirmed" and the reference to the vendor-page title are removed.
7. **Coinbase: "a separate summary" had no source** (`.md` The problem). Confirmed. Its origin could not be found, so the sentence was dropped. "The earlier warehouse" in Evidence now refers to "what the previous path was".
8. **Facts from pages outside the recorded source** (Petrobras, CVS, Rivian, GetYourGuide). Confirmed. Each page these facts rely on was found by search and recorded as a source, with URL, publisher, access and review dates, and a caveat:
   - Petrobras: two Data + AI Summit speaker pages (Petrobras presenter; Databricks senior solutions architect), and the YouTube recording, dated 7 July 2025 in search results.
   - CVS: the YouTube recording, dated 23 July 2024 in search results.
   - Rivian: `github.com/rivian/delta-go`.
   - GetYourGuide: needed no new source (see item 6).
   - The bodies and source contexts now point to these records.
9. **Barilla: "maintainable by a small team"** (`.md` What transfers). Confirmed. Now reads: "…one way to keep 150 pipelines maintainable without a hand-built job per source; the source does not say how large the team is."
10. **AT&T: "Spark keeps intermediate data in memory"** (`.md` Architecture, General analysis). Confirmed; it conflicts with the linked Spark module. Rewritten: Spark chains narrow steps within a stage and avoids writing each intermediate job's output to replicated HDFS, but shuffles still write to local disk and read over the network. The text points to "Distributed execution and reading Spark evidence" under Related modules.
11. **Rivian: unlabelled S3 inference and "at the time"** (`.md` Constraints, Architecture, Missing information). Confirmed.
    - The inference is removed from the "as far as the summary states" list. It is now a labelled "General analysis, not stated by the source", which says S3 is not named and that whether the pattern applies depends on the post's unverified date.
    - Not applied: the reviewer's "(added by AWS in 2024; confirm before publishing)". An editor's note cannot ship to learners, and the date was not re-checked.
    - Added to "Not stated": the object store, and whether the Spark writers run on Databricks or self-managed Spark. Added to Missing information: the writers' engine and commit coordination, and whether they are compatible with the DynamoDB log store.
12. **Crosswalk: internal contract labels (A1–H6, lettered tracks) in notes; module order did not match the notes.** Confirmed: CONTRACT.md says the labels are not runtime IDs. Every note now names topics and refers to "the related modules listed", and each row's `moduleIds` is ordered to match its note.

##### Low (applied)

- **AT&T**:
  - Evidence now says the 30 percent is stated for compute costs, and that nothing is said about storage, licensing or operations.
  - `dbxfe-warehouse-migration` added to `moduleIds`.
  - `publishedAt` set to `Data + AI Summit 2024 (session day not verified)`.
- **Barilla**:
  - The summary no longer places the use cases "across twenty factories", and now opens "A Data + AI Summit session describes…".
  - "reported by Barilla" changed to "given in the session abstract" in two places.
  - `publishedAt` set to `Data + AI Summit 2023 (session day not verified)`.
- **Coinbase**:
  - "instead of three patches" replaced with the source's "unified manner".
  - The source context now says the post *names* the team as SOON's builders, rather than that the team wrote it.
  - `dbxfe-m04` added to `moduleIds`.
- **CVS**: `publishedAt` set to `Data + AI Summit 2024 (session day not verified)`.
- **Petrobras**:
  - The summary and Architecture now note that the course teaches the product as Declarative Automation Bundles.
  - `publishedAt` set to `Data + AI Summit 2025 (session day not verified)`.
- **NAB**: "Who reports" now gives the real reason for using the customer page: its snippets carry the estate counts.
- **Crosswalk**:
  - `access` now reads "Not stated in the search snippet (page not read)".
  - The paid row reads "Not stated as free in the search snippet, which names self-paced and weekly instructor-led formats and a purchase through a subscriptions catalog". This was adapted from the reviewer's wording, which implied self-paced is paid.
  - "(free training)" removed from the title; "flagship" removed; "matching" changed to "overlapping"; the description of `dbxfe-m04` corrected; the unsupported "suggested route" claim dropped.
- **Jargon, all eight cases and the crosswalk**: "not fetched in this build (egress blocked)" is replaced everywhere with "The page itself could not be opened when this analysis/row was written; only its search-result title and snippets were read."

  **Side effect worth recording:** `scripts/academy-source-review.py` classifies any text matching `fetched in this build` as `read-this-build`, even when the text is negated. Under the old wording, all eight case sources and all ten crosswalk rows would have been inventoried as *read in this build*. They now classify as `search-level`, and the validator below checks this.

#### Findings rejected or not applied

- **"All eight cases (retained evidence)": record the snippet text behind each figure** (low). Not applied, for three reasons:
  - The proposed places, a sidecar under `docs/academy/evidence`, are outside this assignment's editable scope.
  - The original build's snippet text no longer exists anywhere, so it cannot be recreated.
  - Search summaries are paraphrases by the tool, not verbatim snippets.

  Partial mitigation: the six new source records name the search date in their caveat. This file lists the queries run and what they confirmed (below). Recommended owner: whoever writes `docs/academy/evidence`.

No high or medium finding was rejected.

#### What the search re-check confirmed (search-level, 2026-09-23)

- **Rivian**: title, URL and figures (80,000+ vehicles, 9.8 million records per second, 20 nonstop Spark workers, about $500 a day, 10 commits per second, the DynamoDB log store, SQS on Kubernetes). The post's author and date remain unknown.
- **NAB**: the customer page's estate counts (thousands of daily feeds, nearly a thousand use cases, more than 140 reporting suites), more than 1,200 staff, and "safeguarding regulatory compliance and uninterrupted business processes". The 95 percent figure appears in the LinkedIn post title only.
- **GetYourGuide**: the 20 percent operational-cost reduction, and the blog's serverless and IP-range snippet.
- **CVS**: 300,000+ employees, and the presenter as a lead director of machine learning.
- **Petrobras**: the abstract (MLflow, Databricks Asset Bundles, Unity Catalog; days to hours), both speakers' affiliations, and the recording date.
- **Coinbase**: SOON's description. The "scheduler-driven ETL" claim was not found.
- **Not re-checked**: AT&T's 30 percent and Barilla's figures.

#### Checks run (all pass)

- Every JSON file in scope parses under `python3 -m json.tool` and Node `JSON.parse`. Formatting is preserved: 2-space indent, trailing newline.
- a local path outside the repository (Node 24.19.0 with tsx) passes: 8 cases, 14 sources and 10 crosswalk rows. It checks:
  - the repository's own `caseSchema`, `sourceSchema` and `crosswalkSchema`;
  - that `sourceIds` equal the embedded sources' ids, and that source ids are unique;
  - that every `moduleId` resolves in `academy.json`;
  - that each body has the seven `###` sections in order and no links;
  - that no build jargon or placeholders remain, and no A1–H6 labels, "same ground", "flagship" or "matching" remain in the crosswalk;
  - that the credit sentence is present;
  - that every caveat and crosswalk note classifies as `search-level` under the source-review script's rules.

  **Negative control:** run against the pre-edit copies, the same validator reports 36 problems.
- The repository's `auditMarkdown` passes over all eight bodies: nothing would be dropped by the renderer and there are no links.
- The six new source ids appear nowhere else in `content/`, `src/`, `scripts/` or `docs/`.
- No string matches the build's unsafe-content or unresolved-marker patterns.
- `check_guides.py` was not run: no guides are in scope.

#### Strengths kept

- Every body keeps the seven-section shape, and figures stay tied to their source.
- Source statements stay separate from labelled "General analysis" or "General context".
- "Evidence and its limits" and "Missing information" still ask concrete, answerable questions.
- Case pages still state that outcomes were not reproduced, and every crosswalk row still says completion here is independent study with no external credit.

#### Remaining limitations and notes for the integrator

- **Search-level evidence only.** Every source, old and new, rests on search results. No page, video, repository or post was opened. Affiliations, dates and figures are as search reported them.
- **Dates still unverified.** Coinbase, GetYourGuide, NAB and Rivian keep `publishedAt: null`. The four conference cases carry the event year with the session day marked unverified.
- **New sources to integrate.** Case sources grew from 8 to 14. When the cases are registered in `course.json`, include every entry in each case's `sources` array. Rivian's reporter is free text, shown verbatim by `reporterText()`.
- **Names in source titles.** Petrobras's two speaker-page records carry the presenters' names in their titles and URLs. They are public conference speakers; the analysis text itself still uses only their roles.
- **Out of scope; fix in `scripts/academy-source-review.py`.** Its `read-this-build` rule matches negated phrasing such as "not fetched in this build". That wording is still used in about ten teaching files (for example `dbxfe-mlflow`, `dbxfe-features`, `dbxfe-sqlserver`, `dbxfe-analytical-sql`), so their sources may be misclassified as read in this build when the inventory is written.
- **Word counts.** Case bodies now run 505 to 659 words; Rivian is the longest. No rule sets a length limit.

## Capstones

**Label:** builder editorial review. This is not an independent human study, and no learner tested these changes. The editor checked every high and medium finding against the files and recomputed every figure with a script before changing anything. Scope was the three dbxfe capstones (Cinderline `dbxfe-capstone`, Harrowgate `dbxfe-capstone-service-knowledge`, Northbrook `dbxfe-capstone-coexistence`) and their data packs.

#### Items opened

- `content/courses/dbxfe/capstones/*` (3 scenario JSON files and 3 guide pages).
- Every file of `content/exercises/capstone-cinderline/`, `capstone-service-knowledge/` and `capstone-coexistence/`, including the templates, documents and reconciliation files.
- Reference only: `course.json` (to check that Cinderline's original disclosures and rubric are byte-identical) and `academy.json`.

#### Result

- **Findings applied:** all 36. That is 8 high, 18 medium and 10 low. One high finding is not fully applied: the optional part of Cinderline's source-admission finding (a refused plant-sheet row) was declined; see below.
- **Findings rejected:** none. Two optional parts of findings were declined (see below).
- **Data pack changed:** yes, in all three packs. The integrator must repackage them.
- **What stayed the same:**
  - Every id, title, lessonId, claimId, rubric id, requirement text and disclosure question.
  - Cinderline's original 6 disclosures and 6 rubric dimensions are still byte-identical to `course.json`.
  - All 12 original Cinderline requirements are still present.
  - The row counts: 26 inventory rows, 46 matrix rows, 20 event rows, 22 questions.

#### Findings applied

##### Cinderline

- **H: "North counted twice" contradicted the events file.** Only inspection A was re-sent. Fixed in:
  - disclosures 7 (Dev) and 9 (Leo);
  - `failure-timeline.md`: rows 23:05, 01:10 and 11:15, and the summary of facts;
  - `stakeholder-statements.md` (Dev);
  - `source-inventory.csv` S03 `duplicate_behaviour`;
  - `flawed-metric.md` Definition A;
  - model §1 and §5.
- **H: no delivery-completeness rule.**
  - A per-package-run rule is now stated in the pack README (new section).
  - The derived-states rows now say North is held after D1 and D2, and published at 11:15 when D3 completes the run.
  - `received_at` is redefined so that D1 at 01:10 is consistent with the timeline.
  - `failure-timeline.md` rows 01:10, 06:40, 11:15 and 16:30 now give `evidence_as_of` as 11:15.
  - `flawed-metric.md`: the C column is relabelled "applied to the same rows", the 07:30 cell is corrected, and the "produces two" paragraph is rewritten.
  - Model: §3 adds a Completeness field; §4 adds completeness to the publication gate; §5 and the technical appendix follow the rule; the §14 handoff asks about a completion marker.
- **H: the workbook broke its own load-date grouping.**
  - East for load date 3 March is now 19.2%, before and after Friday. The Friday rows are filed under the later load date.
  - North: the A3 row stays at 7.7% for 3 March. The sheet figure is 9.3% if pasted.
  - The same class of error was swept elsewhere: the North 3 March workbook figure is now 4.9%, because the nightly run appended A v2 into load date 4 March. Point 5 of "Why … mislead" and the load-date sentence in model §2 were aligned.
- **H: source admission could not be applied.**
  - The README now lists the approved channels. The sheet and the workbook are refused.
  - S03 is reworded: its reporting table is a derived copy, and its extract step is the delivery channel for S01 and S02.
  - The README states that B arrived through the extract and is quarantined after admission.
  - Model §2 is fixed, and §3 now says "five pasted rows, including B's negative quantity".
- **M: 13 hours was called "measured".** Model §11 and `templates/value-model.md` now call it a hypothetical figure, to be measured.
- **M: §5 did not separate facts from hypotheses.** §5 was rewritten with separate facts and hypotheses. It now says "Nobody acts on 6.7% or 12.0% at 07:30, or on 7.1% and 10.8% later".
- **M: no fit to the available capacity.**
  - §10 adds a 64 engineer-hour capacity table (2 engineers × 4 h × 8 weeks).
  - It names what is dropped first and what is never dropped.
  - The staffed days are scheduled outside the analyst's absence week, or a stand-in is named.
  - The reasoning was corrected to match.
- **L: counts and labels.**
  - README: "20 delivered rows (16 distinct events)", and "D7 is unused and the ids are not in time order".
  - `stakeholder-statements.md`: the opening paragraph is corrected.
  - Guide page: "five staged disclosures and six requirements (twelve in total)".
- **L: attribution of the night's cost.** Fixed in the `failure-timeline.md` cost paragraph.
- **L: 95% of deliveries.** Now a count-based criterion in `templates/pov-charter.md` and model §10. §13 reads out in the charter's own statuses (fail, not "partial").

##### Harrowgate

- **H: the supervisor row contradicted a blocking failure.** The `authorization-matrix.csv` supervisor row now requires the endorsement for restricted supplements. The row count stays at 46. Model §2 and the negative tests in §5 were updated.
- **H: the list of allowed actions contradicted itself.** One scope is now used throughout: link plus a held draft. Status changes stay with the technician. Updated in §3, §5, the appendix adapters, and §9 ("read, link and held-draft pilot").
- **M: no blocking metric for injection.** Added a blocking row to §4 (q11). Also added a deterministic check using an embedded-instruction flag and the event log.
- **M: the AP-7 header did not match the section rules.**
  - The header in `hfs-sm-ap7-2-0.md` now gives an audience per section.
  - Model §2 applies audience per section chunk.
  - The README explains audience groups and inheritance.
- **M: the template mapping was wrong.**
  - The README maps `recommendation.md` to Requirements 3, 6 and 9, and states that requirement 8 has no template.
  - Guide Stage 8 was updated to match.
- **M: discovery had unknowns without owners.** Every unknown and assumption in §1 now has an owner. The run budget was moved to the facts.
- **M: the question breakdown added up to 23.** §4 now reads 15 + 2 + 5.
- **L: small errors in the model's demo and metrics.**
  - The demo uses q02 as a south level-1 technician.
  - The verbatim metric is "q04 seven steps and q05 step 5".
  - "The only order input that claims an approval" replaces the old wording.
  - The positive and negative testers are now separate people.
  - A q10 denied-action step was added to the demo (now nine minutes).
- **L: q17 gave the wrong site.** Changed to site 14 in `questions.json`.
- **L: q18 "cite" was undefined.** The `mustNotCite` field note defines "cite" as "cited as authority". It also covers q08 offering §3. The §4 table and the trace record named-but-not-cited sources separately.
- **L: audience values were not roles.** The README now defines the groups.
- **L: first names were reused across capstones.**
  - Harrowgate's parts manager Priya is now Idris.
  - At Northbrook: Vale's data lead is now Katja, Vale's security lead is now Mateus, and the CFO is now Beatrix.

##### Northbrook

- **H: segmentation double-counted a row.**
  - Model §4 now has a full 26-row table: 20 stay, 1 coexist, 2 in wave 1, 3 not yet.
  - TR-FIN is moved to "stay" (a file transfer is not a share).
  - The driver counts now match the table.
- **H: the sensitivity conclusion was false.**
  - No single input crosses the ceiling. The combinations that do are P+L (486,000), P+M+O (454,000) and L+M+O (455,000).
  - Fixed in the worksheet's worked answer, model §9 and §10, and the partial level of rubric 7.
- **M: the three-cloud matrix was unsupported.**
  - §3 now shows rows 1–11 with each cell's status.
  - The Azure/AWS sentence is corrected.
  - Every dependency on an unknown cell is marked in §4, §5 and §6.
  - "Already approved" was replaced by "in use today (DEP-04, DEP-05)".
  - Each estate now has a sentence on classic versus serverless compute.
- **M: 210, 15 and 140 were not in the pack.** These figures are now labelled assumptions, owned by the data lead and checked against the query logs. The roughly 290 remaining Conduit jobs are placed.
- **M: blackout dates and scope appeared only in a worksheet.** The dates and scope are now in the context and in the pack README. "For finance and order systems" was dropped.
- **M: the cross-estate cases were incomplete.**
  - §5 now has a four-row table with recipient, who can revoke, freshness, cost line and failure behaviour.
  - The supplier-quality consumer is labelled an assumption.
  - The cross-estate status of the Line Pulse feed is explained.
- **M: re-pointing came before the rehearsal.**
  - The rollback rehearsal is now in week 6.
  - Cutover is the last re-point plus link revocation, by Friday 4 December.
  - A communication line was added.
  - §10's date was corrected.
- **M: Line Pulse was undated, and the notice rule stranded consumers.**
  - Line Pulse, finance and Tessaly now have dated, owned conditions (27 November, 29 January, weeks 1–2).
  - The notice rule now requires a dated destination for every Granite producer and consumer.
- **M: the paths were not compared on the same criteria.**
  - §2 adds an eight-criterion table.
  - Path A's cost is marked unknown.
  - Vale's network assessment is added to Path A's conditions and to the §12 reversal conditions.
- **M: the worksheet arrived already completed.** `cost-sensitivity.md` now lists inputs and "What to compute". Totals, conclusions and the model label were moved under "Worked answer (read after your attempt)". The README and guide page mention it.
- **M: rubric 5's weak level cited a non-existent total.** It now cites the 62,500.00 value difference.
- **M: Ingrid's disclosure contradicted the estate.** Disclosure 4 now scopes the region approval to storage only. Model §1 matches.
- **L: the ERP shared Granite's name.** `inventory.csv` NB-ERP-01 is now "Northbrook ERP (fictional)".
- **L: "one cause".** The context now reads "disagree by a specific, explainable amount".

#### Parts declined, with reasons

- **Cinderline: add a plant-sheet row that admission refuses** (optional in the finding). Not added. It would change the preserved event data and the derived-state walk. The admission rule is now stated and can be tested against the three named channels.
- **Northbrook: page title and publisher for each matrix cell.** Not named. No documentation page was read or confirmed in this build, and naming unread titles would state as certain what search could not confirm. The model instead names the kind of source (the Databricks documentation for that cloud and the provider's own documentation, each with the date it was read) and marks no cell as sourced.

#### Checks run

- **All JSON files parse.** That is the 3 capstone files and `questions.json`.
- **All CSV files keep their row and column counts.**
- **Ids and structure are unchanged.** A scripted comparison against the originals confirms it.
- **Cinderline's originals are byte-identical** to `course.json`: disclosures 1–6 and rubric 1–6.
- **Every new figure was recomputed:**
  - Cinderline: 6.7, 7.1, 7.7, 9.3, 19.2, 12.0, 4.9, 3.7, 68.5, 52.6, 5.6, 5.0 and 4.5%.
  - Northbrook worksheet: 282,500 / 375,000 / 513,000, the single-input and minimal combinations, and 1,120,000.
  - Capacity: 64 hours.
  - The weekdays of all dates cited.
- **`check_guides.py` failed on an unrelated change.** It stopped with `KeyError: 'lessonFiles'` because `course.json` now references module files as `{file}` (a concurrent change). A copy that resolves those references reports **ALL OK**. The capstone guide pages are outside that script's scope and have no section markers (none before or after).

#### Strengths (kept)

- **Cinderline**
  - Its identity is preserved.
  - Its events match the reliable-data fixtures value for value.
  - The value model is reproducible, and the mixed readout still ends in a decision.
- **Harrowgate**
  - The corpus, question set and disclosures agree on every value.
  - Refusals cite policy and name the missing approval.
- **Northbrook**
  - The inventory and dependency counts are exact.
  - The reconciliation fixture has two interacting causes that recompute exactly.
  - The matrix honestly ships unsourced.
- **All three**
  - Fiction is labelled consistently.
  - They make no claims about price, availability or savings.
  - They disclaim credentials and readiness.

#### Remaining limitations

- **The capstones are not registered yet.** No content gate reads them.
- **The integrator has regeneration work to do:**
  - Generated copies (for example `public/teaching/bodies/dbxfe-capstone.json`) must be regenerated.
  - The three packs must be repackaged.
- **Several reference answers are one defensible choice among several:**
  - Cinderline follows a per-package-run completeness rule. A per-plant marker is named as a design option, not adopted.
  - Harrowgate's model keeps status changes with the technician. Its template still lets a learner choose otherwise.
  - Northbrook's Path A remains unpriced (stated as unknown). Its wave-1 job counts remain labelled assumptions.
- **Some first names are still reused across the academy:**
  - Priya remains Cinderline's controller.
  - Tomasz and Marcus remain at Harrowgate.
  - Other academy content outside this scope also reuses these names (lab-l14, dbxfe-identity).
- **Nothing here was validated with learners.** All sources remain confirmed only to the level the sandbox allowed.

## Course-level fixes

Two confirmed findings needed changes outside the files the track editors could touch. The integrator applied them in the same builder editorial pass. This is not an independent human learner study.

#### m07 gets its own ML-evaluation scenario (high, machine-learning track)

The ML reviewer found that `dbxfe-m07` now teaches ML foundations and evaluation and owns only lesson `dbxfe-m07-l01`. Its course entry, though, still carried the GenAI summary and objectives from before the release split the module, and it sent learners to `dbxfe-m07-scenario`, "Scope a read-only maintenance assistant", which is the GenAI module's scenario.

- **New scenario.** `dbxfe-m07-evaluation-scenario`, "Review a press-failure warning before Cinderline relies on it". A contractor's 97%-accuracy press-failure model splits five-minute sensor messages at random and trains on `stoppage_reason`, a field written after the stoppage. The analyst's rebuilt evidence covers 400 press-days, 20 stoppages, a 24-hour horizon decided at 06:00, fitting on January to June and scoring on July to August at cutoffs 0.60 and 0.35 beside the current rule and never-warn, with September to October sealed.
- **What the learner does.** Define the target and decision time, reject the leak and the random split, work precision and recall from counts, recommend a threshold from the planner's costs and a crew capacity of two inspections a day, and keep the sealed period untouched.
- **What it contains.** Four requirements, four disclosures and a four-dimension rubric.
- **Arithmetic.** Every figure was recomputed by script, and each confusion matrix sums to 400. At 0.60: 9/15 = 60% precision, 9/20 = 45% recall. At 0.35: 15/36 ≈ 41.7% and 15/20 = 75%. The current rule: 7/25 = 28% and 7/20 = 35%.
- **Course entry.** m07's `scenarioId`, `summary` and `objectives` now describe what it teaches, and its teaching module lists the new scenario.
- **The old scenario.** `dbxfe-m07-scenario` is byte-identical and remains the GenAI module's scenario.

#### Lab L09 says its resolver is a simplification (medium, reliable-data track)

The lab's README said its record-resolution rules came from the ingestion module. They are simpler: the lab keeps the highest *valid* version, while the ingestion gate takes the highest observed version first and blocks publication on unresolved conflicts. The track editor fixed the orchestration handbook but could not edit the lab.

- **The README** now calls the lab's rules a simplification and sends publication decisions to the ingestion module. The handbook's pointer matches.
- **The lab** was re-executed from source and from its rebuilt download, and both matched the committed evidence. The download's SHA-256 moved in `course.json`.

## Continuation correction — 2026-09-24

The earlier editorial completion statements do not close G10/G14 or the
source-dependent teaching and case gates. Two confirmed Lakebase defects
survived that review: restore was taught as an in-place production rewind,
and generic pooler behavior was substituted for managed NOTIFY support.

Both now match directly inspected primary documentation. The restore visual,
handbook, model answer, canonical lesson, scenario, glossary and card were
corrected. Beats move to 1.1.0; the affected self-check and cards move to
revision 2; the lesson is 1.1.0 and course 4.0.1. The scenario carries a
revision notice. IDs, saved responses, notes, reviews and schedules are retained.

Four accessible case articles were reconciled, including previously incorrect
claims that published latency, migration scope and the NAB percentage were
unavailable. Nine learning crosswalk pages were directly inspected; the mapping
and prerequisites were corrected. See CASE-CROSSWALK-REVIEW.json for sections.
Four session pages and one catalog entry remain blocked; no video was watched.

CLAIM-REVIEW.json records remaining claim-level work. Source-count checks and
mechanical tests do not supply the missing editorial conclusions.
