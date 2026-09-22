# Teacher-first curriculum 1–8: disposition, coverage and source register

Reviewed and authored 2026-09-20. Scope: platform, Delta, transformations, ingestion, orchestration, SQL analytics, Unity Catalog/security and ML foundations. App behavior and media verification have separate root-owned evidence.

## Disposition and preservation

The pre-authoring plan was recorded outside the application checkout in `teacher-first-research/curriculum-1-8/DISPOSITION.md`. The corrective teacher-first brief takes precedence over the historical role-first course order. These eight teaching JSON files are an additional authored teaching layer, with new beat/question/concept IDs. They reference 20 existing canonical lessons; their original bodies, 75 owned cards and original question IDs remain untouched. All 75 old cards link to an explanatory beat and retain their canonical IDs. Existing completion is not reclassified as completion of new teaching beats.

Disposition by subject: platform responsibilities precede product selection; Delta uses a connected file/snapshot/commit/history specimen; transformations follow grain through typed rows, weighted totals and join multiplication; ingestion explicitly preserves the corrected global publication gate; orchestration follows failure boundaries and effect reconciliation; analytics diagnoses measured time and business meaning; security adds explicit identities, parent grants and negative tests; ML defines the target before fitting and evaluation. GenAI and customer-facing practice are authored separately.

## Coverage

| Module | Beats / visuals | Objective / self-comparison | Old card links | New extensions | Samajh | Handbook prose words, excluding code |
|---|---:|---:|---:|---:|---:|---:|
| Platform mental models and cloud responsibilities (`dbxfe-m03`) | 8 / 8 | 7 / 1 | 12 | 4 | 3 | 164–194 |
| Delta tables, commits and snapshots (`dbxfe-delta`) | 9 / 9 | 8 / 1 | 6 | 4 | 4 | 167–178 |
| SQL, Python and PySpark transformations (`dbxfe-transformations`) | 8 / 8 | 8 / 0 | 15 | 4 | 2 | 165–183 |
| Ingestion, quality and changing records (`dbxfe-m04`) | 8 / 8 | 7 / 1 | 12 | 4 | 2 | 167–184 |
| Orchestration and recovery (`dbxfe-orchestration`) | 8 / 8 | 8 / 0 | 6 | 4 | 1 | 156–180 |
| SQL analytics and performance (`dbxfe-m05`) | 8 / 8 | 8 / 0 | 9 | 4 | 1 | 154–178 |
| Unity Catalog, security and deployment boundaries (`dbxfe-m06`) | 8 / 8 | 7 / 1 | 12 | 4 | 2 | 164–178 |
| ML foundations and evaluation (`dbxfe-m07`) | 10 / 10 | 9 / 1 | 3 | 4 | 2 | 164–181 |

All 67 main explanations are 46–61 whitespace-delimited words after editorial spacing (glossary markup remains an explicit in-context link). Every beat has a distinct visual, question and additional handbook explanation. Correct answers are rotated deterministically across options without altering stable option IDs or rationales. Five questions are explicitly self-comparison, not machine-scored expertise judgments. Seventeen optional Samajh explanations state their mapping and analogy boundary.

Visual captions state the particular takeaway. Text alternatives include actual nodes, values, relationships, equations and table columns/rows, including all four partition-to-group edges in the shuffle specimen. States retain relevant entities through staged/committed, accepted/blocked and before/after comparisons. No stock illustration or decorative repeated box grid substitutes for the worked quantities.

## Worked-result and source-code audit

- Delta: A0=10 and C=8 give 18; merely staged A1=12 leaves 18; a successful replacement gives 20. Historical reconstruction needs retained metadata and files. The changed C correction gives 20 before commit and 18 after. The basic diagram explicitly simplifies file membership; the deletion-vector extension explains row-level metadata selection.
- Transformations: North 12/1 plus 8/0 gives 20/1 and 5%; the mean of inspection percentages answers a different question. Three event matches multiply the denominator to 60. Changed input adds 5/1: 25/2 and 8%; four events produce 100/8 and the same misleading 8% ratio.
- Ingestion: first-run unkeyed immutable-event disagreement blocks publication despite no fabricated unresolved inspection key. With prior 20/1 plus valid A3 correction, diagnostic candidate 22/1 remains separate from published 20/1, `stale_previous` and the unchanged prior outbox. Conflict evidence remains globally blocking.
- Recovery: after raw retention, prior 20/1 is stale; successful recovery can publish 22/1. Failure after publication leaves 22/1 published and an effect gap. Repeated recovery creates one local snapshot-keyed intent, not a verified external notification. The order-line transfer reconciles 900+400=1300 cents, three current rows including one cancellation.
- Analytics: 30 seconds queue + 5 execution + 10 rendering is 45 end-to-end. A candidate with 10% above 60 seconds cannot meet 95% below 15 even if its median improves.
- Security: basic table read requires SELECT, USE SCHEMA and USE CATALOG; these are not the entire execution/network/policy setup. Correctness includes intended denial under the actual principal.
- ML: candidate TP=3, FP=2, FN=1, TN=14 gives precision 60%, recall 75%, accuracy 85%. Changed TP=4, FP=6, FN=1, TN=9 gives 40%, 80%, 65%. Score thresholds and feature cutpoints are distinguished.

Three complete Python fences are copied exactly from canonical lesson source: Python bridge, the SQL/PySpark weighted transformation, and recovery after raw retention. A byte comparison of each fence with its source passed, including existing line-ending differences. The displayed weighted input contains North and South rows; its null denominator branch is defined but a zero-input row is not falsely described as present. New extension examples are hand-worked and source-reviewed; they are not relabeled executed exercises.

The optional exercise archive remains 57,908 bytes with SHA-256 `32af53617af3591ebf861857a579bd93dd86b4e1981bf4ad01c37a7353e0e4fb`. Its historical corrected 39-test record remains historical. No source, expected fixture, ZIP member or download metadata was edited by this author. This document does not claim a new Spark, Databricks, browser or deployment run.

## Beyond-the-module editorial check

The first draft’s extension set was independently compared against the guided handbook. Repeated core retrieval was replaced before acceptance. The accepted extension explanations teach their new mechanism and worked implication, with source/claim links, a definition and a stated practical reason; the engine links directly to that explanation before review. Draft-only extension IDs were replaced where the topic changed; published canonical card IDs were never reused or changed.

| Module | Extension prompts |
|---|---|
| Platform mental models and cloud responsibilities | Is an S3 object version the same as a Delta table version?<br>Does an atomic S3 update to one key imply an atomic update across all table files?<br>An analyst has table SELECT but uses a workspace not bound to an isolated catalog. Is SELECT sufficient?<br>Both 0.0.0.0/0 and 10.2.0.0/16 match destination 10.2.3.4. Which route is selected in this distinct-prefix example? |
| Delta tables, commits and snapshots | Does a logically deleted row always disappear immediately from its Parquet file?<br>A change feed shows A=12 as update_preimage and A=14 as update_postimage. Should a current-state consumer sum them to 26?<br>Why can a metadata-only column rename still break a downstream consumer?<br>Does a Delta transaction-log checkpoint mean the same thing as a streaming-query checkpoint? |
| SQL, Python and PySpark transformations | The second input reverses column order and lacks defective. What does unionByName(..., allowMissingColumns=True) do?<br>Does null-safe equality automatically make a safe business-key join?<br>Which join expresses left-side records with no matching right-side key?<br>A has two tags, B has an empty array and C has a null array. How many rows does explode_outer produce? |
| Ingestion, quality and changing records | Can one pipeline expectation compare a row with a separate historical table?<br>Does one failing expectation always roll back every parallel flow in a triggered pipeline?<br>Why record the Databricks Runtime when reviewing duplicate MERGE matches?<br>Auto Loader retains a new field in _rescued_data. Does that make the field part of the accepted business schema? |
| Orchestration and recovery | Does repair resume a failed task at its last Python line?<br>A downstream publication task reads a missing validation key with a default of true. What risk does that create?<br>A stateful foreachBatch callback only displays two rows and returns. Why might the next batch fail?<br>A cleanup task uses All done, but every dependency is Excluded. Is cleanup guaranteed to run? |
| SQL analytics and performance | Why can aggregate task time exceed wall-clock query duration?<br>What access is needed to view a query profile?<br>May an approximate percentile alone certify an exact requirement that at least 95% of requests finish strictly under 15 seconds?<br>North has inspection quantities 12 and 8. To retain plants totaling at least 20, should WHERE inspected>=20 replace HAVING SUM(inspected)>=20? |
| Unity Catalog, security and deployment boundaries | Does BROWSE mean a principal can SELECT the data?<br>Why review a schema-level SELECT grant differently from one table grant?<br>An analyst sees a masked contact value. What additional evidence is needed before saying access is correctly governed?<br>Does a lineage graph prove every dependency or access path was captured? |
| ML foundations and evaluation | One hundred predictions average 0.80, but 50 cases fail. What does a reliability diagram show?<br>If recall stays 80% and the false-positive rate stays 10%, does precision stay fixed when failures become rarer?<br>Classes A, B and C have support 80, 10 and 10, with recalls 90%, 50% and 0%. Compare macro and support-weighted recall.<br>A run records only models:/Maintenance@champion. Why may that be insufficient to reproduce its predictions later? |

## Beat sequence and canonical anchors

### Platform mental models and cloud responsibilities

Request-path and restart examples replace a product-name tour. Two contrasting workloads prevent capability from becoming an invented requirement.

| Beat | Outcome | Canonical depth anchor |
|---|---|---|
| `dbxfe-m03-decision` — Start with the decision, then the platform | Choose a workload comparison from an actual customer need. | `dbxfe-m03-l01` / `dbxfe-m03-l01-understand` |
| `dbxfe-m03-responsibilities` — Five responsibilities in one query | Trace where a request is named, permitted, executed and stored. | `dbxfe-workspace-compute` / `dbxfe-workspace-compute-responsibilities` |
| `dbxfe-m03-hierarchy` — An account is not a workspace | Place collaboration and governance without confusing their scopes. | `dbxfe-m03-l03` / `dbxfe-m03-l03-understand` |
| `dbxfe-m03-boundary` — Classic and serverless move the compute boundary | Label the operator boundary correctly for an AWS proposal. | `dbxfe-workspace-compute` / `dbxfe-workspace-compute-limits` |
| `dbxfe-m03-durability` — Stop the session: what remains? | Distinguish durable input from session state that must be rebuilt. | `dbxfe-workspace-compute` / `dbxfe-workspace-compute-worked` |
| `dbxfe-m03-network` — Name, route and permission are separate checks | Distinguish DNS, network routing and authorization evidence. | `dbxfe-cloud-bridge` / `dbxfe-cloud-bridge-path` |
| `dbxfe-m03-workload` — Choose compute for the work you will test | Tie a compute choice to a workload and measurable constraints. | `dbxfe-m03-l01` / `dbxfe-m03-l01-understand` |
| `dbxfe-m03-transfer` — Locate the next useful piece of evidence | Explain a changed request without jumping from symptom to architecture promise. | `dbxfe-m03-l03` / `dbxfe-m03-l03-understand` |

### Delta tables, commits and snapshots

One connected file example establishes the mechanism before schema, concurrency and compatibility deepen it.

| Beat | Outcome | Canonical depth anchor |
|---|---|---|
| `dbxfe-delta-folder` — The folder is not the table | Select the files belonging to one committed snapshot. | `dbxfe-m03-l02` / `dbxfe-m03-l02-foundation-mechanism` |
| `dbxfe-delta-stage` — Writing a file is not committing | Predict a failure before commit without promoting staged data. | `dbxfe-m03-l02` / `dbxfe-m03-l02-foundation-example` |
| `dbxfe-delta-commit` — The commit changes the picture | Apply one atomic membership change and exclude the replaced file. | `dbxfe-m03-l02` / `dbxfe-m03-l02-foundation-example` |
| `dbxfe-delta-history` — History needs the evidence to remain | Identify why a historical read can fail despite a visible history entry. | `dbxfe-m03-l02` / `dbxfe-m03-l02-foundation-limits` |
| `dbxfe-delta-meaning` — A correct transaction can contain a wrong answer | Separate table atomicity, source order and metric meaning. | `dbxfe-m03-l02` / `dbxfe-m03-l02-understand` |
| `dbxfe-delta-schema` — A type check is one part of a contract | Distinguish structural schema checks from domain and cross-record checks. | `dbxfe-m03-l02` / `dbxfe-m03-l02-understand` |
| `dbxfe-delta-protocol` — Can every client understand this table? | Plan a feature change around all readers and writers. | `dbxfe-m03-l02` / `dbxfe-m03-l02-foundation-limits` |
| `dbxfe-delta-concurrent` — Validate before accepting a second writer | Explain conflict detection without claiming all writes conflict. | `dbxfe-m03-l02` / `dbxfe-m03-l02-foundation-limits` |
| `dbxfe-delta-transfer` — Predict the changed file set | Transfer snapshot reasoning to a different corrected contribution. | `dbxfe-m03-l02` / `dbxfe-m03-l02-foundation-task` |

### SQL, Python and PySpark transformations

Concrete intermediate rows and matching pairs teach the mechanism. Existing complete locally tested code remains canonical and unchanged.

| Beat | Outcome | Canonical depth anchor |
|---|---|---|
| `dbxfe-transformations-grain` — Say what one row means | Track the grain before and after grouping. | `dbxfe-m04-l01` / `dbxfe-m04-l01-foundation-start` |
| `dbxfe-transformations-python` — A record needs deliberate conversion | Read a Python record and explain accepted versus rejected parsing results. | `dbxfe-python-bridge` / `dbxfe-python-bridge-records` |
| `dbxfe-transformations-schema` — Unknown is not zero | Explain schema, null checks and three-valued filtering. | `dbxfe-dataframes` / `dbxfe-dataframes-expressions` |
| `dbxfe-transformations-expressions` — A Column describes work | Distinguish a lazy expression from an executed result. | `dbxfe-dataframes` / `dbxfe-dataframes-expressions` |
| `dbxfe-transformations-weighted` — Sum the counts before dividing | Compute equivalent SQL/PySpark results with an explicit denominator. | `dbxfe-m04-l01` / `dbxfe-m04-l01-foundation-example` |
| `dbxfe-transformations-joins` — A join makes matching pairs | Predict multiplication and choose an appropriate corrected relation. | `dbxfe-grain-joins` / `dbxfe-grain-joins-cardinality` |
| `dbxfe-transformations-plan` — Read a plan as an explanation of work | Interpret scan/filter/join/aggregate/shuffle without inferring a benchmark. | `dbxfe-grain-joins` / `dbxfe-grain-joins-plans` |
| `dbxfe-transformations-transfer` — Change the population and predict again | Recompute a metric and defend a nonmultiplying join on new input. | `dbxfe-m04-l01` / `dbxfe-m04-l01-foundation-task` |

### Ingestion, quality and changing records

The five-row baseline and corrected unkeyed conflict remain one canonical authored policy. Visual ledgers reveal population and publication separately.

| Beat | Outcome | Canonical depth anchor |
|---|---|---|
| `dbxfe-m04-capture` — Incremental says what you revisit | Distinguish a bounded batch from source change semantics. | `dbxfe-m04-l02` / `dbxfe-m04-l02-foundation-contract` |
| `dbxfe-m04-identity` — One event, one inspection, one revision | Classify replay, redundancy and conflict without arbitrary winners. | `dbxfe-m04-l02` / `dbxfe-m04-l02-foundation-contract` |
| `dbxfe-m04-quality` — Keep the rejected row visible | Trace the baseline population through replay, quarantine and replacement. | `dbxfe-record-resolution` / `dbxfe-record-resolution-worked` |
| `dbxfe-m04-latest` — Do not resurrect an older valid state | Select the highest observed revision before judging whether it is publishable. | `dbxfe-record-resolution` / `dbxfe-record-resolution-stages` |
| `dbxfe-m04-conflict` — A conflict can exist without a usable key | Apply the corrected global publication gate to unkeyed contradictory payloads. | `dbxfe-record-resolution` / `dbxfe-record-resolution-worked` |
| `dbxfe-m04-publication` — A candidate is not a published report | Keep diagnostic 22/1 separate from the last verified 20/1 report. | `dbxfe-record-resolution` / `dbxfe-record-resolution-solution` |
| `dbxfe-m04-update` — Resolve first, then guard replacement | Apply version-aware update rules without treating a no-op as conflict resolution. | `dbxfe-versioned-updates` / `dbxfe-versioned-updates-guard` |
| `dbxfe-m04-transfer` — Replay changes evidence counts, not authority | Predict business invariants and publication after changed cross-batch evidence. | `dbxfe-m04-l02` / `dbxfe-m04-l02-foundation-task` |

### Orchestration and recovery

Failure locations drive the narrative. The existing executed local exercise is preserved exactly and is not relabeled a Databricks job.

| Beat | Outcome | Canonical depth anchor |
|---|---|---|
| `dbxfe-orchestration-dependencies` — A dependency is a reason to wait | Construct a task graph whose publication requires the right evidence. | `dbxfe-m04-l03` / `dbxfe-m04-l03-understand` |
| `dbxfe-orchestration-boundaries` — Four boundaries leave four kinds of evidence | Locate what is durable or visible at an explicit failure point. | `dbxfe-m04-l03` / `dbxfe-m04-l03-foundation-mechanism` |
| `dbxfe-orchestration-raw-failure` — Recover after retaining the correction | Predict recovery from raw evidence without duplicating business state. | `dbxfe-m04-l03` / `dbxfe-m04-l03-foundation-example` |
| `dbxfe-orchestration-published-failure` — A published report is not undone by a later failure | Recover an effect gap without publishing a duplicate business result. | `dbxfe-m04-l03` / `dbxfe-m04-l03-foundation-task` |
| `dbxfe-orchestration-effects` — A retry is not exactly-once delivery | Explain the acknowledgment gap for an external side effect. | `dbxfe-m04-l03` / `dbxfe-m04-l03-foundation-limits` |
| `dbxfe-orchestration-checkpoint` — A checkpoint belongs to a query | Explain why deleting or sharing checkpoint state changes recovery semantics. | `dbxfe-m04-l03` / `dbxfe-m04-l03-deeper` |
| `dbxfe-orchestration-reconcile` — Green is a task result, not a business conclusion | Compare post-recovery business outputs with an independent ledger. | `dbxfe-m04-l03` / `dbxfe-m04-l03-foundation-runbook` |
| `dbxfe-orchestration-transfer` — An order line changes the grain | Transfer ordering/replay policy to a composite key and explicit cancellation. | `dbxfe-m04-l03` / `dbxfe-m04-l03-transfer-task` |

### SQL analytics and performance

A45-second dashboard has several possible causes. Worked timing and threshold examples teach evidence-led decisions without platform benchmark claims.

| Beat | Outcome | Canonical depth anchor |
|---|---|---|
| `dbxfe-m05-metric` — 5% and 50% can both be correct | Name the numerator and denominator before comparing reports. | `dbxfe-m05-l01` / `dbxfe-m05-l01-understand` |
| `dbxfe-m05-serving` — The dashboard is the last mile | Trace a visible metric back to accepted records and its freshness. | `dbxfe-m05-l01` / `dbxfe-m05-l01-understand` |
| `dbxfe-m05-latency` — The same 45 seconds can mean different work | Decompose end-to-end delay before choosing a remedy. | `dbxfe-m05-l02` / `dbxfe-m05-l02-understand` |
| `dbxfe-m05-execution` — Inspect rows, imbalance and spilled work | Connect profile evidence to a bounded query hypothesis. | `dbxfe-m05-l02` / `dbxfe-m05-l02-understand` |
| `dbxfe-m05-cache` — A cached answer is a different experiment | Identify cache conditions that confound performance comparisons. | `dbxfe-m05-l02` / `dbxfe-m05-l02-understand` |
| `dbxfe-m05-capacity` — Faster one query and serving many are different goals | Distinguish latency, throughput and concurrency in a capacity decision. | `dbxfe-m05-l03` / `dbxfe-m05-l03-understand` |
| `dbxfe-m05-experiment` — Change one hypothesis and keep the denominator | Design an interpretable cost/performance comparison. | `dbxfe-m05-l03` / `dbxfe-m05-l03-understand` |
| `dbxfe-m05-transfer` — A better median can still fail the goal | Read a performance result against its original acceptance criterion. | `dbxfe-m05-l03` / `dbxfe-m05-l03-understand` |

### Unity Catalog, security and deployment boundaries

An analyst access case builds from names through privilege conjunctions and negative tests; sharing/deployment are explicit additional boundaries.

| Beat | Outcome | Canonical depth anchor |
|---|---|---|
| `dbxfe-m06-names` — A three-part name locates an asset | Read catalog.schema.object without treating it as an access grant. | `dbxfe-m06-l01` / `dbxfe-m06-l01-foundation-mechanism` |
| `dbxfe-m06-lifecycle` — Who manages the files after the table changes? | Distinguish managed/external lifecycle and business ownership. | `dbxfe-m06-l01` / `dbxfe-m06-l01-understand` |
| `dbxfe-m06-principals` — Test the identity that will do the work | Distinguish human, group and workload principals in a proposed access matrix. | `dbxfe-m06-l02` / `dbxfe-m06-l02-understand` |
| `dbxfe-m06-read` — Three basic grants work together | Evaluate parent usage and table-read requirements as a conjunction. | `dbxfe-m06-l01` / `dbxfe-m06-l01-foundation-example` |
| `dbxfe-m06-negative` — A useful test includes a denial | Explain the evidence gained by allowed and prohibited operations. | `dbxfe-m06-l02` / `dbxfe-m06-l02-understand` |
| `dbxfe-m06-network` — A grant cannot repair an unreachable path | Separate access-control and connectivity diagnosis in AWS context. | `dbxfe-m06-l03` / `dbxfe-m06-l03-understand` |
| `dbxfe-m06-sharing` — Sharing adds a recipient and a lifecycle | Define external sharing scope and limits before treating an internal grant as sufficient. | `dbxfe-m06-l02` / `dbxfe-m06-l02-deeper` |
| `dbxfe-m06-transfer` — Make the consumer test concrete | Write a bounded diagnosis and acceptance statement for a failed analyst query. | `dbxfe-m06-l01` / `dbxfe-m06-l01-foundation-task` |

### ML foundations and evaluation

The original leakage lesson becomes a worked prediction-to-decision sequence with actual calculations and visible error tradeoffs. This is foundational evaluation competence, not advanced ML expertise.

| Beat | Outcome | Canonical depth anchor |
|---|---|---|
| `dbxfe-m07-target` — A warning needs a decision time | Define a prediction target and horizon that support an action. | `dbxfe-m07-l01` / `dbxfe-m07-l01-understand` |
| `dbxfe-m07-features` — Keep tomorrow’s answer out of today’s inputs | Classify fields by actual availability rather than predictive correlation. | `dbxfe-m07-l01` / `dbxfe-m07-l01-see` |
| `dbxfe-m07-split` — The held-out data should resemble the future job | Choose time and entity separation for the intended deployment. | `dbxfe-m07-l01` / `dbxfe-m07-l01-deeper` |
| `dbxfe-m07-fit` — Fitting chooses a rule from examples | Explain model fitting and why zero training error does not prove future performance. | `dbxfe-m07-l01` / `dbxfe-m07-l01-understand` |
| `dbxfe-m07-baseline` — 80% accuracy can mean no warnings | Use a simple baseline to interpret an imbalanced prediction problem. | `dbxfe-m07-l01` / `dbxfe-m07-l01-understand` |
| `dbxfe-m07-metrics` — Count the four outcomes before naming a score | Calculate precision, recall and accuracy from one confusion matrix. | `dbxfe-m07-l01` / `dbxfe-m07-l01-understand` |
| `dbxfe-m07-threshold` — A score is not the action | Predict how an explicit threshold changes alerts and errors. | `dbxfe-m07-l01` / `dbxfe-m07-l01-understand` |
| `dbxfe-m07-lifecycle` — Training creates an artifact; inference uses it | Separate fitting, tracked model artifacts, batch predictions and request-time lookup. | `dbxfe-m07-l01` / `dbxfe-m07-l01-understand` |
| `dbxfe-m07-monitor` — Changed data is a signal to investigate | Separate data drift, model performance and workflow outcomes after deployment. | `dbxfe-m07-l01` / `dbxfe-m07-l01-deeper` |
| `dbxfe-m07-transfer` — Read the errors before recommending rollout | Calculate changed metrics and write an honest next-step recommendation. | `dbxfe-m07-l01` / `dbxfe-m07-l01-try` |

## Source register

The following records contain original paraphrases of the particular supporting passages. Product facts, original teaching guidance and fictional examples are separate claim kinds. A listed source does not certify every adjacent sentence or the invented Cinderline policy. Dates are review dates; publication dates are null unless directly established, because a last-updated label is not necessarily a publication date. Cloud/runtime and access-path limits are part of each record.

There are 62 module source records using 59 distinct URLs. Sources repeated between platform and security are independently linked to their relevant claim context. New Apache Spark API extension references identify current 4.2.0 documentation and the APIs’ earlier introduction; they do not change or assert new execution under the existing Spark 4.0.4 exercise pin. Current CDF documentation dated September 16 distinguishes automatic and legacy modes; this distinction is not flattened into a universal enablement recipe.

Media sources and exact reviewed segments are documented by the separate media curator and joined by the root implementation. No video was approved based solely on its title or description by this curriculum author.

### Platform mental models and cloud responsibilities — primary sources

- **dbxfe-m03-source-architecture** — [High-level architecture](https://docs.databricks.com/aws/en/getting-started/high-level-architecture) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Object hierarchy separates account/workspace/metastore. Classic compute resources are in the customer AWS account; serverless compute is in the Databricks-managed plane.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: AWS context only. Serverless workspaces and serverless compute are related but distinct choices; storage responsibilities depend on workspace type.
- **dbxfe-m03-source-compute** — [Compute](https://docs.databricks.com/aws/en/compute/) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Compute overview distinguishes workload resources including SQL warehouses and resources for notebook and job work.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Workload support, region and entitlement require current target-specific verification.
- **dbxfe-m03-source-storage** — [What is Amazon S3?](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) (Amazon Web Services); reviewed 2026-09-20.
  - Reviewed passage: How S3 works identifies bucket/key/object. Data consistency section describes atomic single-key updates but no general atomic update across multiple keys.
  - Context: AWS S3 primary documentation read 2026-09-20.
  - Limit: General-purpose object-storage concepts; do not confuse S3 object versioning with a Delta table version.
- **dbxfe-m03-source-route** — [Configure route tables](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html) (Amazon Web Services); reviewed 2026-09-20.
  - Reviewed passage: A VPC route table supplies destination/target rules directing network traffic.
  - Context: AWS VPC primary documentation read 2026-09-20.
  - Limit: A route alone does not establish all reachability, TLS or resource authorization.
- **dbxfe-m03-source-dns** — [What is Amazon Route 53?](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/Welcome.html) (Amazon Web Services); reviewed 2026-09-20.
  - Reviewed passage: DNS resolution translates a domain name into a destination used to reach a resource; Route 53 also offers registration and health checks.
  - Context: AWS DNS primary documentation read 2026-09-20.
  - Limit: Successful resolution alone proves neither end-to-end transport nor permission.
- **dbxfe-m03-source-workspace-binding** — [Workspace-catalog binding](https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/workspace-catalog-binding) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: An isolated catalog can restrict access to assigned workspaces; an unbound workspace is denied even when the user holds object privileges.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Bindings add a workspace boundary; they do not grant the underlying object privileges. Default workspace catalogs have special default binding behavior.
- **dbxfe-m03-source-route-priority** — [How route priority works](https://docs.aws.amazon.com/vpc/latest/userguide/route-tables-priority.html) (AWS); reviewed 2026-09-20.
  - Reviewed passage: AWS VPC routing generally selects the most specific matching destination, called longest prefix match; equal/overlapping routes have additional precedence rules.
  - Context: Primary Amazon VPC guide reviewed 2026-09-20.
  - Limit: AWS VPC context only. The example compares distinct IPv4 prefixes, not every equal-prefix, propagated-route or prefix-list tie.

### Delta tables, commits and snapshots — primary sources

- **dbxfe-delta-source-delta** — [What is Delta Lake in Databricks?](https://docs.databricks.com/aws/en/delta/) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Introduction and update sections describe Parquet data plus a transaction log, atomic table operations and schema enforcement.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: This simplified classic replacement model does not depict every Delta feature or update implementation.
- **dbxfe-delta-source-concurrency** — [Concurrency control](https://docs.delta.io/concurrency-control/) (Delta Lake); reviewed 2026-09-20.
  - Reviewed passage: Optimistic concurrency section separates reading, staging files, and validating a commit; conflict matrix distinguishes ordinary INSERT pairs from overlapping changes.
  - Context: Open-source Delta Lake; read 2026-09-20.
  - Limit: Open-source Delta documentation on supported storage. Metadata/protocol changes and target features can introduce other conflicts.
- **dbxfe-delta-source-history** — [Work with table history](https://docs.databricks.com/aws/en/tables/history) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Time-travel retention requires log and data files. RESTORE is a new data-changing operation with downstream duplicate-processing risk.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: AWS page has runtime-specific age limits; a history entry alone is not backup evidence.
- **dbxfe-delta-source-protocol** — [Delta Lake feature compatibility and protocols](https://docs.databricks.com/aws/en/tables/features/feature-compatibility) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Reader/writer requirements and feature tables establish that client compatibility depends on enabled table features; an upgrade can exclude older clients.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Confirm the precise runtime, table features and every reader/writer before changing production tables.
- **dbxfe-delta-source-deletion-vectors** — [Deletion vectors in Databricks](https://docs.databricks.com/aws/en/tables/features/deletion-vectors) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Deletion vectors record row modifications in metadata and readers apply them when resolving table state; logical removal can precede physical file rewrite.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: The core file-membership visual is a simplified table without deletion vectors. Support depends on client and operation; no feature is enabled or data purged.
- **dbxfe-delta-source-column-mapping** — [Rename and drop columns with Delta Lake column mapping](https://docs.databricks.com/aws/en/tables/features/column-mapping) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Column mapping supports metadata-only logical renames and drops without rewriting data files; non-additive changes can affect streaming readers and legacy path-based readers.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Runtime, protocol, mapping mode and downstream limitations must be checked; no ALTER command is executed.
- **dbxfe-delta-source-change-feed** — [Use change data feed: change data feed schema](https://docs.databricks.com/aws/en/tables/features/change-data-feed) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Change records include insert, delete, update_preimage and update_postimage labels plus a table commit version; preimage is before and postimage is after the update.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: The September 16 page distinguishes automatic CDF requiring Runtime 19+ and eligible Unity Catalog tables from legacy Delta CDF. Check the selected mode and retention; this card only interprets change metadata.

### SQL, Python and PySpark transformations — primary sources

- **dbxfe-transformations-source-frame** — [PySpark DataFrame quickstart, 4.0.4](https://spark.apache.org/docs/4.0.4/api/python/getting_started/quickstart_df.html) (Apache Software Foundation); reviewed 2026-09-20.
  - Reviewed passage: Creation, column access, filtering, grouping and SQL sections distinguish typed lazy DataFrames, column expressions, actions and the shared SQL execution engine.
  - Context: Apache Spark 4.0.4 primary API documentation.
  - Limit: Pinned local Spark 4.0.4. This is not a Databricks Runtime compatibility or production performance claim.
- **dbxfe-transformations-source-null** — [Spark 4.0.4 NULL semantics](https://spark.apache.org/docs/4.0.4/sql-ref-null-semantics.html) (Apache Software Foundation); reviewed 2026-09-20.
  - Reviewed passage: Comparison and aggregate sections distinguish unknown comparisons, explicit null checks, COUNT(*) and COUNT(column).
  - Context: Apache Spark 4.0.4 SQL reference.
  - Limit: Null-safe equality expresses a different rule; choosing it requires a business meaning for missing keys.
- **dbxfe-transformations-source-join** — [Spark 4.0.4 JOIN reference](https://spark.apache.org/docs/4.0.4/sql-ref-syntax-qry-select-join.html) (Apache Software Foundation); reviewed 2026-09-20.
  - Reviewed passage: Inner joins combine matching rows; left-semi returns left rows with a match and left-anti those without one.
  - Context: Apache Spark 4.0.4 SQL reference.
  - Limit: Join type does not establish input key uniqueness or business grain.
- **dbxfe-transformations-source-plan** — [DataFrame.explain, 4.0.4](https://spark.apache.org/docs/4.0.4/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.explain.html) (Apache Software Foundation); reviewed 2026-09-20.
  - Reviewed passage: Explain API supports logical/physical plan views and formatted plan output.
  - Context: Apache Spark 4.0.4 API reference.
  - Limit: A planned operator is not observed runtime latency; adaptive execution can change plans.
- **dbxfe-transformations-source-python** — [Python 3.12 data structures](https://docs.python.org/3.12/tutorial/datastructures.html#dictionaries) (Python Software Foundation); reviewed 2026-09-20.
  - Reviewed passage: Dictionary and iteration sections explain keyed records and traversal; a dictionary is not a declared tabular schema.
  - Context: Python 3.12.14 documentation.
  - Limit: Python 3.12 language reference, not a distributed execution model.
- **dbxfe-transformations-source-csv** — [Python 3.12 csv module](https://docs.python.org/3.12/library/csv.html#csv.DictReader) (Python Software Foundation); reviewed 2026-09-20.
  - Reviewed passage: DictReader maps header fields to records; ordinary CSV reading returns strings and requires deliberate numeric conversion.
  - Context: Python 3.12.14 documentation.
  - Limit: CSV dialect and malformed-row policy remain application decisions.
- **dbxfe-transformations-source-union-name** — [DataFrame.unionByName](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.unionByName.html) (Apache Software Foundation); reviewed 2026-09-20.
  - Reviewed passage: unionByName aligns columns by name; allowMissingColumns=True fills absent fields with null. The API dates to 2.3 and the missing-column option to 3.1.
  - Context: Apache Spark primary API reference identifies PySpark 4.2.0 on 2026-09-20. APIs predate the unchanged Spark 4.0.4 exercise pin; these additional examples are hand-worked, not newly executed.
  - Limit: Name alignment does not prove unit, meaning or type compatibility; optional extension only, no new execution claim.
- **dbxfe-transformations-source-explode-outer** — [pyspark.sql.functions.explode_outer](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.functions.explode_outer.html) (Apache Software Foundation); reviewed 2026-09-20.
  - Reviewed passage: explode_outer emits a row per array/map element and emits a null result for empty or null input, unlike ordinary explode.
  - Context: Apache Spark primary API reference identifies PySpark 4.2.0 on 2026-09-20. APIs predate the unchanged Spark 4.0.4 exercise pin; these additional examples are hand-worked, not newly executed.
  - Limit: The operation changes output grain; a null placeholder is not a known list element. API dates to 2.3.

### Ingestion, quality and changing records — primary sources

- **dbxfe-m04-source-ingestion** — [What is Lakeflow Connect?](https://docs.databricks.com/aws/en/ingestion/overview) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Connector categories include CDC database ingestion, files, streaming and query-based ingestion; service model and source support differ.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: A synthetic JSON batch is not a verified connector or a production CDC architecture.
- **dbxfe-m04-source-expectations** — [Manage data quality with pipeline expectations](https://docs.databricks.com/aws/en/ldp/expectations) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Expectations evaluate record-level SQL Boolean constraints; retain/drop/fail actions differ, and constraints cannot query other tables.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: These mechanics do not implement the course’s global retained-history conflict or publication policy.
- **dbxfe-m04-source-merge** — [Upsert into a Delta Lake table using merge](https://docs.databricks.com/aws/en/delta/merge) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: MERGE can apply inserts/updates/deletes; duplicate-match handling differs between Runtime 16.0+ and 15.4 LTS and below.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: The illustrated target remains Runtime 16.4 LTS, unexecuted. Resolve business ambiguity before MERGE on either runtime.
- **dbxfe-m04-source-rescued-data** — [Auto Loader schema inference: rescued data column](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/schema) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: The rescued-data column retains fields absent from the schema or mismatched by type/case, with source-file context; rescue evolution mode keeps new columns there without evolving the schema.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Behavior depends on configured schema/evolution/parser options. Preserving a field does not validate or adjudicate it; no Auto Loader stream is executed.

### Orchestration and recovery — primary sources

- **dbxfe-orchestration-source-jobs** — [Lakeflow Jobs](https://docs.databricks.com/aws/en/jobs/) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Jobs coordinates tasks and triggers, represents workflow dependencies and exposes task/run monitoring.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Task status alone is not evidence of reconciled business state or exactly-once external effects.
- **dbxfe-orchestration-source-dependencies** — [Configure task dependencies](https://docs.databricks.com/aws/en/jobs/run-if) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Run-if conditions depend on upstream success, failure or completion; independent upstream work can execute in parallel.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: A completion condition is not the same as all prerequisites succeeding.
- **dbxfe-orchestration-source-repair** — [Troubleshoot and repair job failures](https://docs.databricks.com/aws/en/jobs/repair-job-failures) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Repair reruns unsuccessful/dependent tasks from their beginning using current settings; the documentation explicitly says Jobs does not make tasks idempotent.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Review partial outputs and changed settings before repair. No cloud repair is executed in this course.
- **dbxfe-orchestration-source-checkpoint** — [Structured Streaming checkpoints](https://docs.databricks.com/aws/en/structured-streaming/checkpoints) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Checkpoints record per-query offsets, commits and state; deleting/changing location starts fresh, and each query needs its own location.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Restart compatibility depends on query/source/state changes and runtime; not all changes support an old checkpoint.
- **dbxfe-orchestration-source-foreach** — [Use foreachBatch to write to arbitrary data sinks](https://docs.databricks.com/aws/en/structured-streaming/foreach) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: foreachBatch supplies micro-batch output and batch identity; custom sink logic must address duplicate writes and failure handling.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Custom external effects are not automatically exactly-once because upstream processing has checkpoints.
- **dbxfe-orchestration-source-excluded-chain** — [Configure task dependencies](https://docs.databricks.com/aws/en/jobs/run-if) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Run if condition options, notes: when every dependency is Excluded, the dependent task is also Excluded regardless of condition; exclusion cascades.
  - Context: Databricks Lakeflow Jobs on AWS; product behavior, not a configured customer job.
  - Limit: Original hypothetical workflow or arithmetic, not an executed product test. Databricks Lakeflow Jobs on AWS; product behavior, not a configured customer job.
- **dbxfe-orchestration-source-task-values** — [Use task values to pass information between tasks](https://docs.databricks.com/aws/en/jobs/task-values) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Set task values: JSON representation at most 48 KiB; set/get are Python notebook functions. Get notes discourage defaults that hide missing keys or wrong task names.
  - Context: Lakeflow Jobs task metadata; dynamic references are supported by tasks accepting parameters.
  - Limit: Original hypothetical workflow or arithmetic, not an executed product test. Lakeflow Jobs task metadata; dynamic references are supported by tasks accepting parameters.
- **dbxfe-orchestration-source-full-consumption** — [Use foreachBatch to write to arbitrary data sinks](https://docs.databricks.com/aws/en/structured-streaming/foreach) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Completely consume each batch DataFrame: stateful queries must consume the full batch or restart; partial consumption can fail the next batch. The example contrasts show(2) with complete consumption.
  - Context: Structured Streaming with stateful operators and foreachBatch on Databricks; this is not a rule that every bounded batch query must collect all data.
  - Limit: Original hypothetical workflow or arithmetic, not an executed product test. Structured Streaming with stateful operators and foreachBatch on Databricks; this is not a rule that every bounded batch query must collect all data.

### SQL analytics and performance — primary sources

- **dbxfe-m05-source-sql** — [Data warehousing on Databricks](https://docs.databricks.com/aws/en/sql/) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: SQL warehouses execute analytical work through SQL, notebooks, Jobs and BI interfaces; metric views can centralize reusable metric calculations.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Capability does not establish an agreed customer definition or a performance advantage.
- **dbxfe-m05-source-profile** — [Query profile](https://docs.databricks.com/aws/en/sql/user/queries/query-profile) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Profiles expose operators, rows and resource metrics. Aggregate task time differs from wall time; cached queries may lack profiles; ownership or monitoring permission is required.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: An execution profile does not include every dashboard/user-perceived delay.
- **dbxfe-m05-source-capacity** — [SQL warehouse sizing, scaling and queuing behavior](https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-behavior) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Size and cluster count concern different resource dimensions; serverless and classic/pro workload management differ.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: No fixed instance size, queue limit, cost rate or proportional speedup is assumed. Verify target type/region/configuration.
- **dbxfe-m05-source-skew** — [Skew and spill](https://docs.databricks.com/aws/en/optimizations/spark-ui-guide/long-spark-stage-page) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Spill moves execution data from memory to disk; skew appears when a few tasks take much longer than others.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Symptoms require actual stage/task evidence; no single threshold is taught as a universal diagnosis.
- **dbxfe-m05-source-cache** — [Query caching](https://docs.databricks.com/aws/en/sql/user/queries/query-caching) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Result caching avoids recomputation; local result cache and serverless remote result cache have different lifecycles.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: UI, result and disk caches differ; AI/BI dashboards have their own cache behavior. Do not infer a cold run from warehouse restart alone.
- **dbxfe-m05-source-having** — [HAVING clause](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select-having) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: HAVING filters GROUP BY results; permitted expressions use grouping expressions, aggregates or constants. Examples distinguish grouped-result conditions.
  - Context: Databricks SQL and Databricks Runtime; arithmetic below is an original hypothetical fixture.
  - Limit: Original hypothetical workflow or arithmetic, not an executed product test. Databricks SQL and Databricks Runtime; arithmetic below is an original hypothetical fixture.
- **dbxfe-m05-source-approximate-percentile** — [approx_percentile aggregate function](https://docs.databricks.com/aws/en/sql/language-manual/functions/approx_percentile) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: The function returns an approximate percentile; a positive integer accuracy parameter trades memory for accuracy. It is a synonym of percentile_approx.
  - Context: Databricks SQL and Runtime. The exact acceptance-count recommendation below is original measurement guidance.
  - Limit: Original hypothetical workflow or arithmetic, not an executed product test. Databricks SQL and Runtime. The exact acceptance-count recommendation below is original measurement guidance.

### Unity Catalog, security and deployment boundaries — primary sources

- **dbxfe-m06-source-unity** — [What is Unity Catalog?](https://docs.databricks.com/aws/en/data-governance/unity-catalog/) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: The object model uses catalog.schema.object for tables and other assets and distinguishes managed from external lifecycle responsibility.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Governance coverage and object capabilities depend on supported operations; names alone grant no access.
- **dbxfe-m06-source-privileges** — [Unity Catalog privileges reference](https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/privileges-reference) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: SELECT on a table also requires parent USE CATALOG and USE SCHEMA. BROWSE enables discovery rather than data read; parent grants can inherit to current/future objects.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Privilege Model 1.0; older metastores and additional access policies/configuration need review. Beta fine-grained DML is not used as a general requirement.
- **dbxfe-m06-source-external** — [Work with external tables](https://docs.databricks.com/aws/en/tables/external) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Dropping an external table removes the registered table without deleting its underlying cloud files.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Cloud lifecycle, direct path access and external writers remain explicit responsibilities; no DROP is executed.
- **dbxfe-m06-source-managed** — [Unity Catalog managed tables](https://docs.databricks.com/aws/en/tables/managed) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Managed table data lifecycle includes delayed deletion after drop/recovery period; managed differs from external file ownership/lifecycle.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Do not promise an exact recovery duration without checking current configuration and runtime. No lifecycle command is executed.
- **dbxfe-m06-source-network** — [Serverless compute plane networking](https://docs.databricks.com/aws/en/security/network/serverless-network-security/) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: The Databricks-managed serverless plane needs configured connectivity to customer resources, with networking cost/availability context.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: AWS only; exact region, endpoints, workspace type and feature availability require specialist verification.
- **dbxfe-m06-source-architecture** — [High-level architecture](https://docs.databricks.com/aws/en/getting-started/high-level-architecture) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Classic compute uses the customer AWS account; serverless compute uses the Databricks-managed plane; workspaces attach to governance context.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Do not copy Azure/GCP network resource instructions into this AWS example.
- **dbxfe-m06-source-sharing** — [What is OpenSharing?](https://docs.databricks.com/aws/en/opensharing) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Current sharing overview distinguishes recipient paths and allows revoking future access at defined granularities.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: The historical delta-sharing URL now redirects here. Revoking service access does not erase recipient copies already obtained; confirm asset/client support.
- **dbxfe-m06-source-lineage** — [Lineage in Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Lineage documentation lists operation/object coverage limits, including path-based column lineage and some UDF patterns.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Lineage is dependency evidence, not complete proof of correctness, authorization or all external activity.
- **dbxfe-m06-source-masks** — [Row filters and column masks](https://docs.databricks.com/aws/en/data-governance/unity-catalog/filters-and-masks/) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Column masks are query-time functions returning original or masked column values; row filters restrict returned rows. Supported access paths and runtimes have explicit limits.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Table-level masks differ from ABAC policies and dynamic views. They are query visibility controls, not proof of encryption or universal protection of every external path.

### ML foundations and evaluation — primary sources

- **dbxfe-m07-source-ml** — [Machine learning on Databricks](https://docs.databricks.com/aws/en/machine-learning/) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: The overview covers preparation, training, tracking, deployment and monitoring as distinct lifecycle responsibilities.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Platform capabilities do not establish a valid target, enough representative labels or useful customer outcomes.
- **dbxfe-m07-source-leakage** — [Common pitfalls and recommended practices](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage) (scikit-learn developers); reviewed 2026-09-20.
  - Reviewed passage: Leakage section separates information available at prediction from later information; preprocessing must be fitted only on training data and consistently applied.
  - Context: scikit-learn primary user guide.
  - Limit: scikit-learn 1.9.1 documentation reviewed 2026-09-20; principles are general ML reasoning, not a Databricks execution.
- **dbxfe-m07-source-split** — [Cross-validation: evaluating estimator performance](https://scikit-learn.org/stable/modules/cross_validation.html) (scikit-learn developers); reviewed 2026-09-20.
  - Reviewed passage: Holdout discussion separates fitting, tuning and final evaluation; time-dependent and grouped data require split strategies reflecting those dependencies.
  - Context: scikit-learn 1.9.1 primary user guide.
  - Limit: No single split guarantees useful deployment; label timing, entity overlap and representation still need review.
- **dbxfe-m07-source-metrics** — [Metrics and scoring: quantifying prediction quality](https://scikit-learn.org/stable/modules/model_evaluation.html) (scikit-learn developers); reviewed 2026-09-20.
  - Reviewed passage: Binary classification section defines confusion-matrix counts, precision TP/(TP+FP), recall TP/(TP+FN) and threshold-dependent measures.
  - Context: scikit-learn 1.9.1 primary user guide.
  - Limit: The course uses exact small synthetic counts; no confidence, benchmark or clinical claim is made.
- **dbxfe-m07-source-threshold** — [Tuning the decision threshold for class prediction](https://scikit-learn.org/stable/modules/classification_threshold.html) (scikit-learn developers); reviewed 2026-09-20.
  - Reviewed passage: Decision-threshold discussion separates score estimation from the action threshold and warns against fitting/tuning on the same data.
  - Context: scikit-learn 1.9.1 primary user guide.
  - Limit: A probability threshold is an operational choice; default 0.5 is not a universal business optimum.
- **dbxfe-m07-source-tracking** — [ML Experiment Tracking](https://mlflow.org/docs/latest/ml/tracking/) (MLflow); reviewed 2026-09-20.
  - Reviewed passage: Tracking records run parameters, metrics, artifacts and metadata so experiments can be compared and reproduced.
  - Context: MLflow current primary tracking documentation.
  - Limit: A logged metric can still come from a flawed evaluation; tracking is not a correctness certificate.
- **dbxfe-m07-source-inference** — [MLflow Serving: concepts and how it works](https://mlflow.org/docs/latest/ml/deployment/) (MLflow); reviewed 2026-09-20.
  - Reviewed passage: Concepts describes a model artifact with dependencies and inference schema; How it works describes loading that packaged model into an inference server.
  - Context: Current primary MLflow deployment documentation, reviewed 2026-09-20; no particular hosting target is executed.
  - Limit: Packaging and inference deployment do not establish valid evaluation or a universal serving/freshness guarantee.
- **dbxfe-m07-source-monitor** — [Data profiling](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/data-profiling) (Databricks); reviewed 2026-09-20.
  - Reviewed passage: Profiling supports data and inference-table quality/drift observations over time.
  - Context: Databricks on AWS; primary documentation reviewed 2026-09-20.
  - Limit: Data drift is not identical to predictive failure; outcome labels and workflow measurements may arrive later.
- **dbxfe-m07-source-calibration** — [Probability calibration: calibration curves](https://scikit-learn.org/stable/modules/calibration.html) (scikit-learn developers); reviewed 2026-09-20.
  - Reviewed passage: Calibration curves compare a bin’s mean predicted probability with its observed positive fraction; bin sample counts matter.
  - Context: Primary documentation reviewed 2026-09-20; scikit-learn pages identify version 1.9.1.
  - Limit: A small observed bin is uncertain; calibration evidence is population-dependent and is not causal benefit.
- **dbxfe-m07-source-precision-api** — [precision_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_score.html) (scikit-learn developers); reviewed 2026-09-20.
  - Reviewed passage: Precision is true positives divided by true plus false positives.
  - Context: Primary documentation reviewed 2026-09-20; scikit-learn pages identify version 1.9.1.
  - Limit: The prevalence experiment is original synthetic arithmetic holding recall and false-positive rate fixed; real population changes need fresh evidence.
- **dbxfe-m07-source-recall-api** — [recall_score: averaging and support](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.recall_score.html) (scikit-learn developers); reviewed 2026-09-20.
  - Reviewed passage: Macro averaging weights class recalls equally; weighted averaging weights each class by its true sample count, called support.
  - Context: Primary documentation reviewed 2026-09-20; scikit-learn pages identify version 1.9.1.
  - Limit: A chosen averaging rule does not encode every operational consequence; report class-level counts too.
- **dbxfe-m07-source-registry** — [MLflow Model Registry: versions and aliases](https://mlflow.org/docs/latest/ml/model-registry/) (MLflow); reviewed 2026-09-20.
  - Reviewed passage: A registered model contains numbered versions; a model alias is a mutable named reference to a particular version.
  - Context: Current primary MLflow model-registry documentation; deployment integrations differ.
  - Limit: Alias reassignment does not prove that an already loaded process or independently configured endpoint has switched models.

## Validation boundary

The author performed JSON parsing, exact owned-card coverage, explanation-length checks, worked arithmetic review, all-three embedded-code comparisons, source/claim linkage review, and archive hashing. Independent editorial review corrected a missing pair of shuffle arrows and the extension/core repetition described above. The root implementation owns the complete schema validator and browser/accessibility/persistence evidence. The author’s direct validator attempt did not reach content loading because the restricted Windows runtime returned `uv_os_get_passwd ENOMEM` inside tsx; this is not represented as a content-validation pass.
