# Complete teacher-first course coverage

The course order below is editorial; the renderer accepts any validated nonempty module count. Every original lesson, check, card and asset retains its canonical identity. Each new beat has its own version, visual, substantive handbook and deliberate check. Counts document scope; actual teaching review is recorded separately in [editorial review](EDITORIAL-REVIEW.md), [modules1–8](curriculum-1-8.md) and [modules9–16](CURRICULUM-9-16.md).

| Module | Beats / visuals / stages | Samajh | New objective / self checks | Handbook words | Preserved / extension cards | Videos |
|---|---:|---:|---:|---:|---:|---:|
| 1. Platform mental models and cloud responsibilities | 8 / 8 / 12 | 3 | 7 / 1 | 1,407 | 12 / 4 | 1 |
| 2. Delta tables, commits and snapshots | 9 / 9 / 17 | 4 | 8 / 1 | 1,556 | 6 / 4 | 1 |
| 3. SQL, Python and PySpark transformations | 8 / 8 / 17 | 2 | 8 / 0 | 1,836 | 15 / 4 | 1 |
| 4. Ingestion, quality and changing records | 8 / 8 / 14 | 2 | 7 / 1 | 1,414 | 12 / 4 | 1 |
| 5. Orchestration and recovery | 8 / 8 / 16 | 1 | 8 / 0 | 1,470 | 6 / 4 | 1 |
| 6. SQL analytics and performance | 8 / 8 / 17 | 1 | 8 / 0 | 1,372 | 9 / 4 | 1 |
| 7. Unity Catalog, security and deployment boundaries | 8 / 8 / 15 | 2 | 7 / 1 | 1,380 | 12 / 4 | 1 |
| 8. ML foundations and evaluation | 10 / 10 / 20 | 2 | 9 / 1 | 1,757 | 3 / 4 | 1 |
| 9. GenAI, retrieval and agents | 10 / 10 / 15 | 3 | 0 / 10 | 1,818 | 6 / 4 | 1 |
| 10. Architecture and migration | 10 / 10 / 16 | 3 | 0 / 10 | 1,772 | 9 / 4 | 1 |
| 11. Role, teamwork and the customer journey | 8 / 8 / 9 | 2 | 0 / 8 | 1,433 | 9 / 4 | 1 |
| 12. Discovery and qualification | 8 / 8 / 9 | 2 | 0 / 8 | 1,475 | 9 / 4 | 1 |
| 13. Demos and technical storytelling | 8 / 8 / 10 | 2 | 0 / 8 | 1,567 | 9 / 4 | 1 |
| 14. Proof of value | 8 / 8 / 9 | 2 | 0 / 8 | 1,446 | 9 / 4 | 1 |
| 15. Competition and business value | 8 / 8 / 11 | 2 | 0 / 8 | 1,452 | 9 / 4 | 1 |
| 16. Field execution and end-to-end capstone | 8 / 8 / 8 | 1 | 0 / 8 | 1,497 | 9 / 4 | 1 |

The 96 original objective checks remain unchanged and accessible through canonical references; several are also linked into the new beats. New objective checks use deterministic options/rationales. Free-response checks and applied tasks use model reasoning/self-comparison without an automatic score. Handbook word counts exclude original linked reference bodies, extension explanations and source metadata. All figures and computed teaching values are labeled hypothetical/synthetic where applicable.

## 1. Platform mental models and cloud responsibilities

Stable module: `dbxfe-m03`. Canonical lessons: `dbxfe-m03-l01`, `dbxfe-m03-l03`, `dbxfe-workspace-compute`, `dbxfe-cloud-bridge`.

Taught outcomes:

- Trace a query through identity, governance, compute and storage.
- Distinguish account, workspace, metastore and compute boundaries on AWS.
- Choose the next diagnostic evidence without promising an unverified architecture.

Editorial choice: Request-path and restart examples replace a product-name tour. Two contrasting workloads prevent capability from becoming an invented requirement.

Beat → canonical section → main explanation words:

- `dbxfe-m03-decision` → `dbxfe-m03-l01-understand` → 53; handbook sections: `dbxfe-m03-l01-understand`.
- `dbxfe-m03-responsibilities` → `dbxfe-workspace-compute-responsibilities` → 47; handbook sections: `dbxfe-workspace-compute-responsibilities`.
- `dbxfe-m03-hierarchy` → `dbxfe-m03-l03-understand` → 50; handbook sections: `dbxfe-m03-l03-understand`.
- `dbxfe-m03-boundary` → `dbxfe-workspace-compute-limits` → 52; handbook sections: `dbxfe-workspace-compute-limits`.
- `dbxfe-m03-durability` → `dbxfe-workspace-compute-worked` → 56; handbook sections: `dbxfe-workspace-compute-worked`.
- `dbxfe-m03-network` → `dbxfe-cloud-bridge-path` → 53; handbook sections: `dbxfe-cloud-bridge-path`.
- `dbxfe-m03-workload` → `dbxfe-m03-l01-understand` → 54; handbook sections: `dbxfe-m03-l01-understand`.
- `dbxfe-m03-transfer` → `dbxfe-m03-l03-understand` → 54; handbook sections: `dbxfe-m03-l03-understand`.

## 2. Delta tables, commits and snapshots

Stable module: `dbxfe-delta`. Canonical lessons: `dbxfe-m03-l02`.

Taught outcomes:

- Predict table contents from committed membership.
- Separate atomic table changes from correct business inputs.
- Explain retention and reader compatibility before promising a historical read.

Editorial choice: One connected file example establishes the mechanism before schema, concurrency and compatibility deepen it.

Beat → canonical section → main explanation words:

- `dbxfe-delta-folder` → `dbxfe-m03-l02-foundation-mechanism` → 44; handbook sections: `dbxfe-m03-l02-foundation-mechanism`.
- `dbxfe-delta-stage` → `dbxfe-m03-l02-foundation-example` → 51; handbook sections: `dbxfe-m03-l02-foundation-example`.
- `dbxfe-delta-commit` → `dbxfe-m03-l02-foundation-example` → 49; handbook sections: `dbxfe-m03-l02-foundation-example`.
- `dbxfe-delta-history` → `dbxfe-m03-l02-foundation-limits` → 50; handbook sections: `dbxfe-m03-l02-foundation-limits`.
- `dbxfe-delta-meaning` → `dbxfe-m03-l02-understand` → 50; handbook sections: `dbxfe-m03-l02-understand`.
- `dbxfe-delta-schema` → `dbxfe-m03-l02-understand` → 50; handbook sections: `dbxfe-m03-l02-understand`.
- `dbxfe-delta-protocol` → `dbxfe-m03-l02-foundation-limits` → 49; handbook sections: `dbxfe-m03-l02-foundation-limits`.
- `dbxfe-delta-concurrent` → `dbxfe-m03-l02-foundation-limits` → 51; handbook sections: `dbxfe-m03-l02-foundation-limits`.
- `dbxfe-delta-transfer` → `dbxfe-m03-l02-foundation-task` → 51; handbook sections: `dbxfe-m03-l02-foundation-task`.

## 3. SQL, Python and PySpark transformations

Stable module: `dbxfe-transformations`. Canonical lessons: `dbxfe-m04-l01`, `dbxfe-python-bridge`, `dbxfe-dataframes`, `dbxfe-grain-joins`.

Taught outcomes:

- Explain a row’s grain before filtering, grouping or joining.
- Trace equivalent SQL and PySpark transformations over typed input.
- Preserve unknowns and detect multiplying joins with explicit expected output.

Editorial choice: Concrete intermediate rows and matching pairs teach the mechanism. Existing complete locally tested code remains canonical and unchanged.

Beat → canonical section → main explanation words:

- `dbxfe-transformations-grain` → `dbxfe-m04-l01-foundation-start` → 55; handbook sections: `dbxfe-m04-l01-foundation-start`.
- `dbxfe-transformations-python` → `dbxfe-python-bridge-records` → 52; handbook sections: `dbxfe-python-bridge-records`.
- `dbxfe-transformations-schema` → `dbxfe-dataframes-expressions` → 54; handbook sections: `dbxfe-dataframes-expressions`, `dbxfe-dataframes-worked`, `dbxfe-dataframes-solution`.
- `dbxfe-transformations-expressions` → `dbxfe-dataframes-expressions` → 52; handbook sections: `dbxfe-dataframes-worked`, `dbxfe-dataframes-limits`.
- `dbxfe-transformations-weighted` → `dbxfe-m04-l01-foundation-example` → 56; handbook sections: `dbxfe-m04-l01-foundation-example`.
- `dbxfe-transformations-joins` → `dbxfe-grain-joins-cardinality` → 55; handbook sections: `dbxfe-grain-joins-worked`, `dbxfe-grain-joins-plans`.
- `dbxfe-transformations-plan` → `dbxfe-grain-joins-plans` → 50; handbook sections: `dbxfe-grain-joins-plans`.
- `dbxfe-transformations-transfer` → `dbxfe-m04-l01-foundation-task` → 53; handbook sections: `dbxfe-m04-l01-foundation-task`.

## 4. Ingestion, quality and changing records

Stable module: `dbxfe-m04`. Canonical lessons: `dbxfe-m04-l02`, `dbxfe-record-resolution`, `dbxfe-versioned-updates`.

Taught outcomes:

- Separate delivery identity, inspection identity and replacement revision.
- Explain quarantine, cross-batch conflicts and invalid latest state.
- Keep accepted diagnostic candidates separate from published reports.

Editorial choice: The five-row baseline and corrected unkeyed conflict remain one canonical authored policy. Visual ledgers reveal population and publication separately.

Beat → canonical section → main explanation words:

- `dbxfe-m04-capture` → `dbxfe-m04-l02-foundation-contract` → 57; handbook sections: `dbxfe-m04-l02-foundation-contract`.
- `dbxfe-m04-identity` → `dbxfe-m04-l02-foundation-contract` → 53; handbook sections: `dbxfe-m04-l02-foundation-contract`.
- `dbxfe-m04-quality` → `dbxfe-record-resolution-worked` → 56; handbook sections: `dbxfe-record-resolution-stages`, `dbxfe-record-resolution-worked`, `dbxfe-record-resolution-reference-code`.
- `dbxfe-m04-latest` → `dbxfe-record-resolution-stages` → 60; handbook sections: `dbxfe-record-resolution-stages`.
- `dbxfe-m04-conflict` → `dbxfe-record-resolution-worked` → 58; handbook sections: `dbxfe-record-resolution-reference-code`, `dbxfe-record-resolution-spark-code`, `dbxfe-record-resolution-solution`.
- `dbxfe-m04-publication` → `dbxfe-record-resolution-solution` → 58; handbook sections: `dbxfe-record-resolution-solution`, `dbxfe-record-resolution-reference-code`, `dbxfe-record-resolution-spark-code`.
- `dbxfe-m04-update` → `dbxfe-versioned-updates-guard` → 54; handbook sections: `dbxfe-versioned-updates-worked`, `dbxfe-versioned-updates-delta-example`, `dbxfe-versioned-updates-solution`.
- `dbxfe-m04-transfer` → `dbxfe-m04-l02-foundation-task` → 52; handbook sections: `dbxfe-m04-l02-foundation-task`.

## 5. Orchestration and recovery

Stable module: `dbxfe-orchestration`. Canonical lessons: `dbxfe-m04-l03`.

Taught outcomes:

- Explain dependency conditions separately from business correctness.
- Predict retained, resolved, published and simulated-effect state after failures.
- Transfer replay reasoning to order-line cancellations and totals.

Editorial choice: Failure locations drive the narrative. The existing executed local exercise is preserved exactly and is not relabeled a Databricks job.

Beat → canonical section → main explanation words:

- `dbxfe-orchestration-dependencies` → `dbxfe-m04-l03-understand` → 51; handbook sections: `dbxfe-m04-l03-understand`.
- `dbxfe-orchestration-boundaries` → `dbxfe-m04-l03-foundation-mechanism` → 51; handbook sections: `dbxfe-m04-l03-foundation-mechanism`.
- `dbxfe-orchestration-raw-failure` → `dbxfe-m04-l03-foundation-example` → 60; handbook sections: `dbxfe-m04-l03-foundation-example`, `dbxfe-m04-l03-pipeline-code`.
- `dbxfe-orchestration-published-failure` → `dbxfe-m04-l03-foundation-task` → 56; handbook sections: `dbxfe-m04-l03-foundation-solution`, `dbxfe-m04-l03-pipeline-code`.
- `dbxfe-orchestration-effects` → `dbxfe-m04-l03-foundation-limits` → 55; handbook sections: `dbxfe-m04-l03-foundation-limits`.
- `dbxfe-orchestration-checkpoint` → `dbxfe-m04-l03-deeper` → 52; handbook sections: `dbxfe-m04-l03-deeper`.
- `dbxfe-orchestration-reconcile` → `dbxfe-m04-l03-foundation-runbook` → 50; handbook sections: `dbxfe-m04-l03-foundation-runbook`.
- `dbxfe-orchestration-transfer` → `dbxfe-m04-l03-transfer-task` → 54; handbook sections: `dbxfe-m04-l03-transfer-task`, `dbxfe-m04-l03-transfer-solution`, `dbxfe-m04-l03-transfer-code`.

## 6. SQL analytics and performance

Stable module: `dbxfe-m05`. Canonical lessons: `dbxfe-m05-l01`, `dbxfe-m05-l02`, `dbxfe-m05-l03`.

Taught outcomes:

- Write a metric contract with population, time and exclusions.
- Separate queue, execution and presentation delays.
- Interpret join/skew/spill/cache evidence and evaluate a controlled performance experiment.

Editorial choice: A45-second dashboard has several possible causes. Worked timing and threshold examples teach evidence-led decisions without platform benchmark claims.

Beat → canonical section → main explanation words:

- `dbxfe-m05-metric` → `dbxfe-m05-l01-understand` → 53; handbook sections: `dbxfe-m05-l01-understand`.
- `dbxfe-m05-serving` → `dbxfe-m05-l01-understand` → 58; handbook sections: `dbxfe-m05-l01-understand`.
- `dbxfe-m05-latency` → `dbxfe-m05-l02-understand` → 54; handbook sections: `dbxfe-m05-l02-understand`.
- `dbxfe-m05-execution` → `dbxfe-m05-l02-understand` → 57; handbook sections: `dbxfe-m05-l02-understand`.
- `dbxfe-m05-cache` → `dbxfe-m05-l02-understand` → 53; handbook sections: `dbxfe-m05-l02-understand`.
- `dbxfe-m05-capacity` → `dbxfe-m05-l03-understand` → 60; handbook sections: `dbxfe-m05-l03-understand`.
- `dbxfe-m05-experiment` → `dbxfe-m05-l03-understand` → 54; handbook sections: `dbxfe-m05-l03-understand`.
- `dbxfe-m05-transfer` → `dbxfe-m05-l03-understand` → 56; handbook sections: `dbxfe-m05-l03-understand`.

## 7. Unity Catalog, security and deployment boundaries

Stable module: `dbxfe-m06`. Canonical lessons: `dbxfe-m06-l01`, `dbxfe-m06-l02`, `dbxfe-m06-l03`.

Taught outcomes:

- Explain namespace and managed/external lifecycle responsibilities.
- Reason about basic table-read privileges with representative identities.
- Frame a cloud-labeled access and sharing validation without overclaiming.

Editorial choice: An analyst access case builds from names through privilege conjunctions and negative tests; sharing/deployment are explicit additional boundaries.

Beat → canonical section → main explanation words:

- `dbxfe-m06-names` → `dbxfe-m06-l01-foundation-mechanism` → 53; handbook sections: `dbxfe-m06-l01-foundation-mechanism`.
- `dbxfe-m06-lifecycle` → `dbxfe-m06-l01-understand` → 59; handbook sections: `dbxfe-m06-l01-understand`.
- `dbxfe-m06-principals` → `dbxfe-m06-l02-understand` → 58; handbook sections: `dbxfe-m06-l02-understand`.
- `dbxfe-m06-read` → `dbxfe-m06-l01-foundation-example` → 56; handbook sections: `dbxfe-m06-l01-foundation-example`, `dbxfe-m06-l01-foundation-solution`.
- `dbxfe-m06-negative` → `dbxfe-m06-l02-understand` → 59; handbook sections: `dbxfe-m06-l02-understand`.
- `dbxfe-m06-network` → `dbxfe-m06-l03-understand` → 54; handbook sections: `dbxfe-m06-l03-understand`.
- `dbxfe-m06-sharing` → `dbxfe-m06-l02-deeper` → 57; handbook sections: `dbxfe-m06-l02-deeper`.
- `dbxfe-m06-transfer` → `dbxfe-m06-l01-foundation-task` → 54; handbook sections: `dbxfe-m06-l01-foundation-task`.

## 8. ML foundations and evaluation

Stable module: `dbxfe-m07`. Canonical lessons: `dbxfe-m07-l01`.

Taught outcomes:

- Specify target, horizon, available features and a deployment-matching evaluation split.
- Calculate baseline, confusion-matrix, precision and recall results from synthetic observations.
- Distinguish fitting, threshold choice, inference and monitoring evidence.

Editorial choice: The original leakage lesson becomes a worked prediction-to-decision sequence with actual calculations and visible error tradeoffs. This is foundational evaluation competence, not advanced ML expertise.

Beat → canonical section → main explanation words:

- `dbxfe-m07-target` → `dbxfe-m07-l01-understand` → 54; handbook sections: `dbxfe-m07-l01-understand`.
- `dbxfe-m07-features` → `dbxfe-m07-l01-see` → 55; handbook sections: `dbxfe-m07-l01-see`.
- `dbxfe-m07-split` → `dbxfe-m07-l01-deeper` → 55; handbook sections: `dbxfe-m07-l01-deeper`.
- `dbxfe-m07-fit` → `dbxfe-m07-l01-understand` → 58; handbook sections: `dbxfe-m07-l01-understand`.
- `dbxfe-m07-baseline` → `dbxfe-m07-l01-understand` → 58; handbook sections: `dbxfe-m07-l01-understand`.
- `dbxfe-m07-metrics` → `dbxfe-m07-l01-understand` → 55; handbook sections: `dbxfe-m07-l01-understand`.
- `dbxfe-m07-threshold` → `dbxfe-m07-l01-understand` → 57; handbook sections: `dbxfe-m07-l01-understand`.
- `dbxfe-m07-lifecycle` → `dbxfe-m07-l01-understand` → 59; handbook sections: `dbxfe-m07-l01-understand`.
- `dbxfe-m07-monitor` → `dbxfe-m07-l01-deeper` → 55; handbook sections: `dbxfe-m07-l01-deeper`.
- `dbxfe-m07-transfer` → `dbxfe-m07-l01-try` → 63; handbook sections: `dbxfe-m07-l01-try`.

## 9. GenAI, retrieval and agents

Stable module: `dbxfe-genai`. Canonical lessons: `dbxfe-m07-l02`, `dbxfe-m07-l03`.

Taught outcomes:

- Design a bounded retrieval answer with inspectable source/version evidence.
- Separate information quality from authority to act.
- Diagnose a failed answer and propose an honest evaluation and deployment decision.

Editorial choice: Each beat develops one mechanism or decision with inspectable inputs. The final changed case tests transfer; preserved canonical lessons provide their original depth and historical anchors.

Beat → canonical section → main explanation words:

- `dbxfe-genai-beat-task` → `dbxfe-m07-l02-understand` → 53; handbook sections: `dbxfe-m07-l02-understand`, `dbxfe-m07-l02-deeper`.
- `dbxfe-genai-beat-context` → `dbxfe-m07-l02-understand` → 46; handbook sections: `dbxfe-m07-l02-understand`, `dbxfe-m07-l02-deeper`.
- `dbxfe-genai-beat-chunks` → `dbxfe-m07-l02-understand` → 50; handbook sections: `dbxfe-m07-l02-understand`, `dbxfe-m07-l02-deeper`.
- `dbxfe-genai-beat-permission` → `dbxfe-m07-l02-understand` → 50; handbook sections: `dbxfe-m07-l02-understand`, `dbxfe-m07-l02-deeper`.
- `dbxfe-genai-beat-citations` → `dbxfe-m07-l02-understand` → 54; handbook sections: `dbxfe-m07-l02-understand`, `dbxfe-m07-l02-deeper`.
- `dbxfe-genai-beat-tools` → `dbxfe-m07-l02-understand` → 49; handbook sections: `dbxfe-m07-l02-understand`, `dbxfe-m07-l02-deeper`.
- `dbxfe-genai-beat-trace` → `dbxfe-m07-l03-understand` → 47; handbook sections: `dbxfe-m07-l03-understand`, `dbxfe-m07-l03-deeper`.
- `dbxfe-genai-beat-evaluation` → `dbxfe-m07-l03-understand` → 45; handbook sections: `dbxfe-m07-l03-understand`, `dbxfe-m07-l03-deeper`.
- `dbxfe-genai-beat-judges` → `dbxfe-m07-l03-understand` → 50; handbook sections: `dbxfe-m07-l03-understand`, `dbxfe-m07-l03-deeper`.
- `dbxfe-genai-beat-transfer` → `dbxfe-m07-l03-understand` → 53; handbook sections: `dbxfe-m07-l03-understand`, `dbxfe-m07-l03-deeper`.

## 10. Architecture and migration

Stable module: `dbxfe-m08`. Canonical lessons: `dbxfe-m08-l01`, `dbxfe-m08-l02`, `dbxfe-m08-l03`.

Taught outcomes:

- Translate a requirement into owned responsibilities and conditional interfaces.
- Defend meaningful alternatives using the same evidence basis.
- Plan reconciliation, cutover and recovery with explicit data consequences.

Editorial choice: Each beat develops one mechanism or decision with inspectable inputs. The final changed case tests transfer; preserved canonical lessons provide their original depth and historical anchors.

Beat → canonical section → main explanation words:

- `dbxfe-m08-beat-responsibilities` → `dbxfe-m08-l01-understand` → 52; handbook sections: `dbxfe-m08-l01-understand`, `dbxfe-m08-l01-deeper`.
- `dbxfe-m08-beat-constraints` → `dbxfe-m08-l01-understand` → 53; handbook sections: `dbxfe-m08-l01-understand`, `dbxfe-m08-l01-deeper`.
- `dbxfe-m08-beat-alternatives` → `dbxfe-m08-l02-understand` → 47; handbook sections: `dbxfe-m08-l02-understand`, `dbxfe-m08-l02-deeper`.
- `dbxfe-m08-beat-query-copy` → `dbxfe-m08-l02-understand` → 54; handbook sections: `dbxfe-m08-l02-understand`, `dbxfe-m08-l02-deeper`.
- `dbxfe-m08-beat-assumptions` → `dbxfe-m08-l01-understand` → 47; handbook sections: `dbxfe-m08-l01-understand`, `dbxfe-m08-l01-deeper`.
- `dbxfe-m08-beat-population` → `dbxfe-m08-l03-understand` → 51; handbook sections: `dbxfe-m08-l03-understand`, `dbxfe-m08-l03-deeper`.
- `dbxfe-m08-beat-offsetting` → `dbxfe-m08-l03-understand` → 54; handbook sections: `dbxfe-m08-l03-understand`, `dbxfe-m08-l03-deeper`.
- `dbxfe-m08-beat-cutover` → `dbxfe-m08-l03-understand` → 49; handbook sections: `dbxfe-m08-l03-understand`, `dbxfe-m08-l03-deeper`.
- `dbxfe-m08-beat-rollback` → `dbxfe-m08-l03-understand` → 50; handbook sections: `dbxfe-m08-l03-understand`, `dbxfe-m08-l03-deeper`.
- `dbxfe-m08-beat-transfer` → `dbxfe-m08-l02-understand` → 55; handbook sections: `dbxfe-m08-l02-understand`, `dbxfe-m08-l02-deeper`.

## 11. Role, teamwork and the customer journey

Stable module: `dbxfe-m01`. Canonical lessons: `dbxfe-m01-l01`, `dbxfe-m01-l02`, `dbxfe-m01-l03`.

Taught outcomes:

- Distinguish a capability, a customer hypothesis and observed evidence.
- Assign ownership, contribution and acceptance without inventing authority.
- Choose the smallest evidence step that advances a real customer decision.

Editorial choice: Each beat develops one mechanism or decision with inspectable inputs. The final changed case tests transfer; preserved canonical lessons provide their original depth and historical anchors.

Beat → canonical section → main explanation words:

- `dbxfe-m01-beat-evidence` → `dbxfe-m01-l01-understand` → 52; handbook sections: `dbxfe-m01-l01-understand`, `dbxfe-m01-l01-deeper`.
- `dbxfe-m01-beat-decision` → `dbxfe-m01-l01-understand` → 49; handbook sections: `dbxfe-m01-l01-understand`, `dbxfe-m01-l01-deeper`.
- `dbxfe-m01-beat-ownership` → `dbxfe-m01-l02-understand` → 55; handbook sections: `dbxfe-m01-l02-understand`, `dbxfe-m01-l02-deeper`.
- `dbxfe-m01-beat-handoff` → `dbxfe-m01-l02-understand` → 52; handbook sections: `dbxfe-m01-l02-understand`, `dbxfe-m01-l02-deeper`.
- `dbxfe-m01-beat-specialist` → `dbxfe-m01-l02-understand` → 50; handbook sections: `dbxfe-m01-l02-understand`, `dbxfe-m01-l02-deeper`.
- `dbxfe-m01-beat-gates` → `dbxfe-m01-l03-understand` → 52; handbook sections: `dbxfe-m01-l03-understand`, `dbxfe-m01-l03-deeper`.
- `dbxfe-m01-beat-delivery` → `dbxfe-m01-l03-understand` → 52; handbook sections: `dbxfe-m01-l03-understand`, `dbxfe-m01-l03-deeper`.
- `dbxfe-m01-beat-transfer` → `dbxfe-m01-l03-understand` → 54; handbook sections: `dbxfe-m01-l03-understand`, `dbxfe-m01-l03-deeper`.

## 12. Discovery and qualification

Stable module: `dbxfe-m02`. Canonical lessons: `dbxfe-m02-l01`, `dbxfe-m02-l02`, `dbxfe-m02-l03`.

Taught outcomes:

- Ask neutral questions that separate the requested tool from the decision.
- Trace data, timing, corrections, identities and ownership through the current path.
- Write measurable criteria without inventing a baseline or excluding inconvenient records.

Editorial choice: Each beat develops one mechanism or decision with inspectable inputs. The final changed case tests transfer; preserved canonical lessons provide their original depth and historical anchors.

Beat → canonical section → main explanation words:

- `dbxfe-m02-beat-episode` → `dbxfe-m02-l01-understand` → 51; handbook sections: `dbxfe-m02-l01-understand`, `dbxfe-m02-l01-deeper`.
- `dbxfe-m02-beat-stakeholders` → `dbxfe-m02-l01-understand` → 50; handbook sections: `dbxfe-m02-l01-understand`, `dbxfe-m02-l01-deeper`.
- `dbxfe-m02-beat-clocks` → `dbxfe-m02-l01-understand` → 47; handbook sections: `dbxfe-m02-l01-understand`, `dbxfe-m02-l01-deeper`.
- `dbxfe-m02-beat-trace` → `dbxfe-m02-l02-understand` → 52; handbook sections: `dbxfe-m02-l02-understand`, `dbxfe-m02-l02-deeper`.
- `dbxfe-m02-beat-status` → `dbxfe-m02-l02-understand` → 54; handbook sections: `dbxfe-m02-l02-understand`, `dbxfe-m02-l02-deeper`.
- `dbxfe-m02-beat-criterion` → `dbxfe-m02-l03-understand` → 49; handbook sections: `dbxfe-m02-l03-understand`, `dbxfe-m02-l03-deeper`.
- `dbxfe-m02-beat-unknown` → `dbxfe-m02-l03-understand` → 58; handbook sections: `dbxfe-m02-l03-understand`, `dbxfe-m02-l03-deeper`.
- `dbxfe-m02-beat-transfer` → `dbxfe-m02-l03-understand` → 54; handbook sections: `dbxfe-m02-l03-understand`, `dbxfe-m02-l03-deeper`.

## 13. Demos and technical storytelling

Stable module: `dbxfe-m09`. Canonical lessons: `dbxfe-m09-l01`, `dbxfe-m09-l02`, `dbxfe-m09-l03`.

Taught outcomes:

- Write a demo intent around the audience’s next decision.
- Explain a correction and replay with visible evidence rather than a click tour.
- Recover from failed execution or an unknown answer without inventing success.

Editorial choice: Each beat develops one mechanism or decision with inspectable inputs. The final changed case tests transfer; preserved canonical lessons provide their original depth and historical anchors.

Beat → canonical section → main explanation words:

- `dbxfe-m09-beat-audience` → `dbxfe-m09-l01-understand` → 55; handbook sections: `dbxfe-m09-l01-understand`, `dbxfe-m09-l01-deeper`.
- `dbxfe-m09-beat-story` → `dbxfe-m09-l02-understand` → 54; handbook sections: `dbxfe-m09-l02-understand`, `dbxfe-m09-l02-deeper`.
- `dbxfe-m09-beat-basis` → `dbxfe-m09-l02-understand` → 57; handbook sections: `dbxfe-m09-l02-understand`, `dbxfe-m09-l02-deeper`.
- `dbxfe-m09-beat-correction` → `dbxfe-m09-l02-understand` → 62; handbook sections: `dbxfe-m09-l02-understand`, `dbxfe-m09-l02-deeper`.
- `dbxfe-m09-beat-replay` → `dbxfe-m09-l02-understand` → 55; handbook sections: `dbxfe-m09-l02-understand`, `dbxfe-m09-l02-deeper`.
- `dbxfe-m09-beat-explainback` → `dbxfe-m09-l01-understand` → 55; handbook sections: `dbxfe-m09-l01-understand`, `dbxfe-m09-l01-deeper`.
- `dbxfe-m09-beat-failure` → `dbxfe-m09-l03-understand` → 54; handbook sections: `dbxfe-m09-l03-understand`, `dbxfe-m09-l03-deeper`.
- `dbxfe-m09-beat-transfer` → `dbxfe-m09-l03-understand` → 49; handbook sections: `dbxfe-m09-l03-understand`, `dbxfe-m09-l03-deeper`.

## 14. Proof of value

Stable module: `dbxfe-m10`. Canonical lessons: `dbxfe-m10-l01`, `dbxfe-m10-l02`, `dbxfe-m10-l03`.

Taught outcomes:

- Connect a testable hypothesis to a comparable baseline and accepted criteria.
- Write a scoped charter with owners, prerequisites, stop conditions and change control.
- Read out pass, fail, blocked and not-tested results without averaging away a gate.

Editorial choice: Each beat develops one mechanism or decision with inspectable inputs. The final changed case tests transfer; preserved canonical lessons provide their original depth and historical anchors.

Beat → canonical section → main explanation words:

- `dbxfe-m10-beat-hypothesis` → `dbxfe-m10-l01-understand` → 53; handbook sections: `dbxfe-m10-l01-understand`, `dbxfe-m10-l01-deeper`.
- `dbxfe-m10-beat-baseline` → `dbxfe-m10-l01-understand` → 51; handbook sections: `dbxfe-m10-l01-understand`, `dbxfe-m10-l01-deeper`.
- `dbxfe-m10-beat-criteria` → `dbxfe-m10-l01-understand` → 50; handbook sections: `dbxfe-m10-l01-understand`, `dbxfe-m10-l01-deeper`.
- `dbxfe-m10-beat-charter` → `dbxfe-m10-l02-understand` → 49; handbook sections: `dbxfe-m10-l02-understand`, `dbxfe-m10-l02-deeper`.
- `dbxfe-m10-beat-cases` → `dbxfe-m10-l02-understand` → 50; handbook sections: `dbxfe-m10-l02-understand`, `dbxfe-m10-l02-deeper`.
- `dbxfe-m10-beat-execution` → `dbxfe-m10-l02-understand` → 50; handbook sections: `dbxfe-m10-l02-understand`, `dbxfe-m10-l02-deeper`.
- `dbxfe-m10-beat-readout` → `dbxfe-m10-l03-understand` → 53; handbook sections: `dbxfe-m10-l03-understand`, `dbxfe-m10-l03-deeper`.
- `dbxfe-m10-beat-transfer` → `dbxfe-m10-l03-understand` → 54; handbook sections: `dbxfe-m10-l03-understand`, `dbxfe-m10-l03-deeper`.

## 15. Competition and business value

Stable module: `dbxfe-m11`. Canonical lessons: `dbxfe-m11-l01`, `dbxfe-m11-l02`, `dbxfe-m11-l03`.

Taught outcomes:

- Compare current, new and coexisting paths on common decision criteria.
- Use current vendor documentation for specific mechanisms without inventing a universal winner.
- Calculate hypothetical value and sensitivity while distinguishing capacity from cash savings.

Editorial choice: Each beat develops one mechanism or decision with inspectable inputs. The final changed case tests transfer; preserved canonical lessons provide their original depth and historical anchors.

Beat → canonical section → main explanation words:

- `dbxfe-m11-beat-criteria` → `dbxfe-m11-l01-understand` → 48; handbook sections: `dbxfe-m11-l01-understand`, `dbxfe-m11-l01-deeper`.
- `dbxfe-m11-beat-mechanisms` → `dbxfe-m11-l01-understand` → 48; handbook sections: `dbxfe-m11-l01-understand`, `dbxfe-m11-l01-deeper`.
- `dbxfe-m11-beat-coexistence` → `dbxfe-m11-l01-understand` → 52; handbook sections: `dbxfe-m11-l01-understand`, `dbxfe-m11-l01-deeper`.
- `dbxfe-m11-beat-objection` → `dbxfe-m11-l02-understand` → 50; handbook sections: `dbxfe-m11-l02-understand`, `dbxfe-m11-l02-deeper`.
- `dbxfe-m11-beat-cost` → `dbxfe-m11-l03-understand` → 54; handbook sections: `dbxfe-m11-l03-understand`, `dbxfe-m11-l03-deeper`.
- `dbxfe-m11-beat-arithmetic` → `dbxfe-m11-l03-understand` → 57; handbook sections: `dbxfe-m11-l03-understand`, `dbxfe-m11-l03-deeper`.
- `dbxfe-m11-beat-sensitivity` → `dbxfe-m11-l03-understand` → 58; handbook sections: `dbxfe-m11-l03-understand`, `dbxfe-m11-l03-deeper`.
- `dbxfe-m11-beat-transfer` → `dbxfe-m11-l02-understand` → 51; handbook sections: `dbxfe-m11-l02-understand`, `dbxfe-m11-l02-deeper`.

## 16. Field execution and end-to-end capstone

Stable module: `dbxfe-m12`. Canonical lessons: `dbxfe-m12-l01`, `dbxfe-m12-l02`, `dbxfe-m12-l03`.

Taught outcomes:

- Prioritize the action that changes the next customer decision.
- Write an owned follow-up and a precise specialist escalation.
- Assemble the complete fictional Cinderline engagement without contradictory assumptions or inflated readiness claims.

Editorial choice: Each beat develops one mechanism or decision with inspectable inputs. The final changed case tests transfer; preserved canonical lessons provide their original depth and historical anchors.

Beat → canonical section → main explanation words:

- `dbxfe-m12-beat-priority` → `dbxfe-m12-l01-understand` → 53; handbook sections: `dbxfe-m12-l01-understand`, `dbxfe-m12-l01-deeper`.
- `dbxfe-m12-beat-followup` → `dbxfe-m12-l02-understand` → 52; handbook sections: `dbxfe-m12-l02-understand`, `dbxfe-m12-l02-deeper`.
- `dbxfe-m12-beat-escalation` → `dbxfe-m12-l02-understand` → 50; handbook sections: `dbxfe-m12-l02-understand`, `dbxfe-m12-l02-deeper`.
- `dbxfe-m12-beat-discovery-design` → `dbxfe-m12-l03-understand` → 52; handbook sections: `dbxfe-m12-l03-understand`, `dbxfe-m12-l03-deeper`.
- `dbxfe-m12-beat-demo-pilot` → `dbxfe-m12-l03-understand` → 60; handbook sections: `dbxfe-m12-l03-understand`, `dbxfe-m12-l03-deeper`.
- `dbxfe-m12-beat-value-assumptions` → `dbxfe-m12-l03-understand` → 57; handbook sections: `dbxfe-m12-l03-understand`, `dbxfe-m12-l03-deeper`.
- `dbxfe-m12-beat-handoff` → `dbxfe-m12-l02-understand` → 52; handbook sections: `dbxfe-m12-l02-understand`, `dbxfe-m12-l02-deeper`.
- `dbxfe-m12-beat-capstone` → `dbxfe-m12-l03-understand` → 52; handbook sections: `dbxfe-m12-l03-understand`, `dbxfe-m12-l03-deeper`.
