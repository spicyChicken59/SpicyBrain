# Module specifications (sanitized contract)

Each module keeps the common Deck/Handbook/Cards/Practice contract from
`AUTHORING-BRIEF.md`; the named practice output below is required in addition.
Retained modules keep their IDs and are deepened, never cloned. "Show" names
the visuals that must exist; "Practice/output" names the applied task and
scenario. "Link" names cross-references instead of duplicated teaching.

## Track A — Platform and working fluency

**A1 Platform mental models and cloud responsibilities** — KEEP `dbxfe-m03`.
Accounts, workspaces, catalogs, compute, storage, notebooks, SQL, data/AI
workloads and the request path; responsibility of each piece before marketing
names; classic/serverless boundaries with cloud-specific diagrams. Show the
same query as author, identity, authorization, execution, storage and result
delivery; contrast a permission failure with a connectivity failure.
Practice: annotated platform map and a two-minute explanation with explicit
unknowns and follow-up evidence. Link D1–D5 rather than duplicating them.

**A2 Python for dependable data work** — NEW `dbxfe-python`.
Values/types, collections, missing values, functions, modules, iteration,
comprehensions when readable, files/JSON/CSV, conversions, exceptions,
assertions, logging, package environments, small tests, type hints and
debugging through concrete data tasks; explain unfamiliar syntax before
relying on it. Show a raw record passing through parsing, validation and
accepted/rejected output; a traceback connected to the failing line and input.
Practice: a tested parser with valid, missing, malformed and conflicting
records plus a clean importable module (Lab L01). Link the original Python
bridge lesson instead of cloning it.

**A3 SQL, Python and PySpark transformations** — KEEP `dbxfe-transformations`.
Explicit schemas, column expressions, null semantics, filtering, projection,
grouping, joins, grain, windows, casting, SQL/PySpark equivalence, local
objects versus distributed columns, care when collecting to the driver.
Preserve the tested examples. Practice: equivalent tested SQL/PySpark
solutions on a changed dataset with a diagnosed plausible wrong answer and
type-sensitive assertions (Labs L02, L03).

**A4 Distributed execution and reading Spark evidence** — NEW `dbxfe-spark-execution`.
Partitions, tasks, stages, driver/executors, transformations/actions, shuffle,
narrow/wide dependencies, join strategies, skew, caching, adaptive plans;
planned operators versus measured runtime. Show a small plan connected to row
movement and a genuinely captured local plan; avoid "more workers is always
faster" and universal tuning rules. Practice: inspect an actual local plan,
predict the expensive boundary, change one variable, compare evidence without
calling a toy run a production benchmark; include an out-of-memory/collection
caution and a skew counterexample (Lab L04).

**A5 Reproducible development, APIs and delivery** — NEW `dbxfe-delivery`.
Git branches/PRs, environment separation, modular notebooks, configuration,
CLI/SDK/REST responsibilities, authentication boundaries, dependency pinning,
tests, CI/CD; Declarative Automation Bundles with the former "Databricks Asset
Bundles" name as a searchable alias and actual command/configuration syntax
preserved. Show local source → validation → reviewed artifact → deployment →
execution as separate states. Practice: an original small project layout and
reviewed deployment configuration with dev/test/prod parameters, unit tests
and a promotion checklist; classify local syntax/schema checks separately
from authenticated bundle validation and workspace deployment; never deploy
(Lab L16).

**A6 AI-assisted development without surrendering verification** — NEW `dbxfe-ai-assist`.
Using documented platform coding assistance to explain code, draft a
transformation, investigate errors and construct tests; bounded task
formulation; verifying generated SQL/Python against independent expected
results; permissions and confidentiality boundaries. Show an intentionally
wrong suggested join, a misleading explanation and a source-supported
correction, labelled authored (not captured AI output). Practice: an
assistance request, a test plan and a corrected implementation. No live AI
dependency, auto-generated assessment or model API is added to SpicyBrain.

## Track B — Reliable data engineering

**B1 Delta tables, commits and snapshots** — KEEP `dbxfe-delta`. Data files,
committed state, log/checkpoint, read snapshots, atomicity, concurrency,
schema versus business correctness, history, protocol compatibility; the
18 → 20, not 30 sequence. Practice: reason through a new commit sequence and
verify selected open-source Delta behaviour locally (Lab L05); retention
prerequisites explicit before historical reads.

**B2 Delta writes, evolution and table maintenance** — NEW `dbxfe-delta-writes`.
Inserts/updates/deletes/MERGE, duplicate source matches, guarded updates,
change data feed, schema enforcement/evolution, table features, retention,
compaction, liquid clustering, predictive optimization where supported;
open-source mechanisms versus Databricks-only availability. Show source
matching and target transitions; a maintenance action's effects on files,
reads, compatibility and historical recovery. Practice: a tested small update
sequence and a maintenance decision memo. Never suggest disabling retention
safety checks or destructive commands against shared tables; teach why a
missing incremental row is not a delete.

**B3 Ingestion, quality and changing records** — KEEP `dbxfe-m04`.
Batch/CDC/snapshot choices, source keys, revision/arrival order, managed
connectors versus custom reads, Auto Loader concepts, source history,
quarantine, duplicate deliveries, conflicting current records. Show raw →
valid/invalid/conflicting → resolved → publication decision. Practice: the
preserved Cinderline resolver plus a transfer case (Labs L06, L10); connector
support verified per source/cloud/version.

**B4 Structured Streaming, event time and recovery** — NEW `dbxfe-streaming`.
Micro-batches, triggers, offsets, checkpoints, state, event versus processing
time, watermarks, windows, late arrivals, stream joins, sink effects; where
exactly-once depends on source/sink/operation and where external effects need
safeguards. Show an ordered sequence of file arrivals with late events,
watermark movement, state retention and restart from the same checkpoint.
Practice: a bounded real local streaming experiment with expected window
results and restart evidence; finite fixtures and explicit termination (Lab L08).

**B5 Declarative pipelines and change-data processing** — NEW `dbxfe-pipelines`.
Datasets and flows, streaming tables/materialized views, expectations,
dependency graphs, incremental behaviour, SCD1/SCD2, sequence keys, AUTO CDC,
snapshot-derived changes; Apache Spark Declarative Pipelines versus Databricks
extensions. Show an event sequence producing current and historical
dimensions with late corrections, tied versions and invalid ordering. Practice:
a locally tested reference SCD transformation plus an explicit platform
adaptation not labelled executed (Lab L07).

**B6 Orchestration and recoverable execution** — KEEP `dbxfe-orchestration`.
Tasks/dependencies, parameters, retries, repair, idempotency, backfills,
notifications, quality gates, event evidence, ownership. Show failure after
raw retention, after resolution, before/after an external effect. Practice:
deterministic injected-failure exercise, recovery comparison and an
operations runbook (Lab L09); a green task is not correct business data.

## Track C — Analytics, performance and economics

**C1 Data modeling and metric contracts** — NEW `dbxfe-modeling`. Business
grain, facts/dimensions, conformed keys, slowly changing attributes, star
models, wide tables, aggregation levels, semantic definitions, units, join
cardinality. Show a model and the same metric at incompatible grains.
Practice: model, metric contract and tests catching double-counting, missing
denominators, unit and time-window mismatches (Lab L11). A medallion label is
not a modeled entity.

**C2 Advanced analytical SQL** — NEW `dbxfe-analytical-sql`. Windows, ranking,
deduplication, gaps/islands, temporal logic, semi/anti joins, set operations,
nested/semi-structured fields, safe casts, null-aware calculations; window
frames and time-zone assumptions. Show input partition/order/frame beside
each row's value. Practice: a query portfolio with independently specified
answers including tied order, null input, month boundaries and a
daylight-saving case (Lab L12); source-dialect expressions are not assumed
equal to Spark SQL.

**C3 SQL analytics and performance diagnosis** — KEEP `dbxfe-m05`. Plans and
profiles, scan/pruning, joins, shuffle/skew, caching, compute startup,
queueing, execution, result delivery, concurrency, workload isolation, Photon
with precise source context. Show a slow-dashboard timeline and a plan with a
suspected bottleneck. Practice: diagnosis and controlled experiment with
repeated observations, correctness checks and what remains unproven.

**C4 Business intelligence and semantic delivery** — NEW `dbxfe-bi`. Useful
dashboards, audience/action/metric alignment, filters, permissions, refresh
and freshness communication, semantic metric definitions, AI/BI capabilities,
the business-user experience. Show an original schematic dashboard with
misleading versus defensible labelling linked to its metric contract, marked
schematic. Practice: a dashboard storyboard, metric definitions, access matrix
and acceptance script, with a supported external BI integration discussion.

**C5 Natural-language analytics with Genie** — NEW `dbxfe-genie`. The current
Genie family's distinct roles, domain curation, trusted data, example SQL,
business semantics, benchmark questions, uncertainty, access and quality
review; current terminology with older names searchable. Show question →
semantic interpretation → SQL → result → validation and an ambiguous
question needing clarification. Practice: a benchmark set with expected
SQL/result properties, authorized and unauthorized cases, misleading prompts
and a review process; an authored benchmark is not a live-agent claim.

**C6 Compute choices, cost and FinOps reasoning** — NEW `dbxfe-finops`.
Workload-specific compute decisions, utilization, startup/queueing,
concurrency, job versus interactive work, quotas, cost attribution, system
evidence, unit economics, spend governance. Show a sensitivity model
separating compute, platform usage, storage, movement, operations and
migration assumptions with source dates or synthetic labels. Practice: a
reproducible cost worksheet in safe local formats and a controlled
performance/cost experiment (Lab L13); explicit currencies, periods, units;
no personalized financial advice, invented discounts or guaranteed savings.

## Track D — Governance and cloud architecture

**D1 Unity Catalog and governance responsibilities** — KEEP `dbxfe-m06`.
Object hierarchy, ownership, privileges, managed/external responsibilities,
lineage, discovery, policy enforcement, governance evidence. Show one principal
attempting operations across catalog/schema/table/volume. Practice: a
least-privilege design with positive/negative cases and an escalation packet
(Lab L14); a matrix simulation is not Unity Catalog enforcement.

**D2 Identity, authorization and audit** — NEW `dbxfe-identity`. Human and
workload identities, groups, OAuth flows, service principals,
federation/provisioning distinctions, secrets, credential scope, row/column
controls, attribute-based policies where supported, audit events, incident
evidence. Show who authenticates, whose permissions apply, where a request
can fail. Practice: threat/access review with a narrow permission plan and a
test matrix; least privilege, separation of duties, token exposure mistakes;
no real tokens, no broad admin grants as a fix, no compliance certification.

**D3 AWS deployment and network boundaries** — NEW `dbxfe-aws`. AWS-specific
workspaces, compute planes, VPCs/subnets, routing/DNS, private connectivity,
storage access, IAM roles, keys, outbound restrictions in supported patterns.
Show author/query/storage/control paths with distinct trust boundaries.
Practice: annotated architecture, permissions/network evidence checklist and
a diagnostic sequence for one denied and one unreachable request (Lab L15).
Not an Azure diagram relabelled; no provisioning.

**D4 Azure deployment and network boundaries** — NEW `dbxfe-azure`.
Azure-specific workspace/resource relationships, Microsoft Entra identities,
managed identities/service principals, storage authorization, virtual
networks, private endpoints/DNS, routing, serverless boundaries. Show two
supported patterns with different responsibilities. Practice: a sourced Azure
design and failure diagnosis where storage access and application access are
separate (Lab L15); no implied parity with AWS.

**D5 Google Cloud deployment and network boundaries** — NEW `dbxfe-gcp`.
Organization/project/workspace boundaries, service accounts, IAM/storage,
networks, supported private-connectivity patterns, serverless/classic
responsibilities. Show request paths with named identities and resource
ownership. Practice: sourced GCP architecture and a test/evidence matrix
marking unverified availability as unknown (Lab L15). Across D3–D5 a common
questions matrix with separate sourced answers.

**D6 Sharing, federation and interoperability** — NEW `dbxfe-sharing`.
Governed sharing, query federation, ingestion versus access-in-place, open
table formats, catalog interoperability, Iceberg/Delta considerations,
recipient permissions, fresh/stale data, clean-room boundaries where
supported. Show data movement, enforcement and ownership for three
alternatives. Practice: select and defend a pattern for a fictional partner
collaboration including revocation, cost, freshness and failure behaviour;
current OpenSharing/Delta Sharing nomenclature without renaming protocol
identifiers or SDK calls.

## Track E — Machine learning and production evaluation

**E1 Machine-learning foundations and trustworthy evaluation** — KEEP `dbxfe-m07`.
Targets, prediction time, features, baselines, splits, leakage,
classification/regression, imbalance, metric choice, thresholds; enough
probability/statistics to interpret results. Show a leaking feature on a
timeline and two confusion matrices with different consequences. Practice: a
CPU-local baseline and corrected evaluation with a limitations report (Lab L17).

**E2 Features, point-in-time correctness and data contracts** — NEW `dbxfe-features`.
Feature transformations, temporal joins, entity keys, missingness, quality,
reuse, training/serving consistency, future-data leakage; platform feature
capabilities after the mechanism. Show observations, feature availability
times and labels on one timeline. Practice: a point-in-time feature dataset
with tests rejecting future information, duplicate entity-time rows and
mismatched transformation logic (Lab L18); batch versus online as choices.

**E3 MLflow, experiments and reproducibility** — NEW `dbxfe-mlflow`. Runs,
parameters, metrics, artifacts, datasets, packaging, signatures,
environments, comparison, registry responsibilities, promotion; open-source
MLflow versus Databricks-managed integration. Show two comparable runs and an
apparently superior but unreproducible run. Practice: a local tracked
experiment with reproducible artifacts, a clean rerun, a versioned model
contract and an evidence-based promotion decision (Lab L17).

**E4 Inference, serving and model operations** — NEW `dbxfe-serving`.
Batch/online inference, request/response contracts, latency/concurrency,
feature access, deployment/rollback, monitoring, drift, delayed labels, model
quality, incident response; data drift versus verified quality loss. Show a
request trace and a monitoring timeline with known versus hypothesized
problems. Practice: a local contract test, an operational scorecard and a
staged release/rollback runbook; managed serving explicitly unexecuted.

**E5 Forecasting, anomalies and practical model selection** — NEW `dbxfe-forecasting`.
Temporal validation, naive baselines, horizon, leakage, seasonality,
uncertainty, anomaly thresholds, false-positive load, decision-oriented
metrics, a small ranking/recommendation comparison. Show rolling-origin
validation and a threshold change affecting inspection load. Practice: a
reproducible forecasting or anomaly example with baseline, backtest, failure
cases and honest uncertainty (Lab L19); no safety or financial guarantees.

**E6 Deep learning and accelerated workloads** — NEW `dbxfe-deep-learning`.
Tensors, network intuition, embeddings, training versus inference, batching,
GPU memory, fine-tuning versus retrieval, distributed training, resource
tradeoffs. Show tensor dimensions, a small forward computation and a
memory/batch tradeoff. Practice: a tiny CPU-executed example plus a sourced
accelerated-workload design with unexecuted GPU instructions labelled; when a
simpler model or non-ML solution is better.

## Track F — GenAI, agents and applications

**F1 Models, retrieval and agents: different responsibilities** — KEEP `dbxfe-genai`.
Tokens/context, probabilistic generation, prompts, retrieval, grounding,
embeddings, tool use, application state, authorization, citations,
evaluation; deterministic workflow versus model response versus agentic loop.
Practice: choose a pattern and explain its failure modes without an LLM call.

**F2 Document processing and retrieval engineering** — NEW `dbxfe-retrieval`.
Source authority, parsing/chunking, metadata, permissions, version/freshness,
lexical and vector retrieval, hybrid search, ranking/reranking, context
assembly, citations, retrieval evaluation; current AI Search capabilities.
Show why the wrong chunk wins, how a newer authorized source changes context,
why an unauthorized document must not be returned. Practice: an executed local
retrieval experiment over synthetic documents with labelled queries and
metrics (Lab L20); TF-IDF is not managed vector search.

**F3 GenAI evaluation, traces and failure analysis** — NEW `dbxfe-genai-eval`.
Test datasets, expected properties, groundedness, relevance, abstention, tool
correctness, adversarial cases, deterministic checks, human review,
model-judge limits; current MLflow evaluation/tracing concepts. Show a trace
separating retrieval failure, reasoning failure and a denied tool. Practice: a
local evaluation harness and failure taxonomy with inspectable cases (Lab L21);
stubbed outputs identified as fixtures; no manufactured judge scores.

**F4 Tools, MCP and action authorization** — NEW `dbxfe-tools`. Tool schemas,
identities, delegated permissions, trust boundaries, retries, timeouts,
idempotency keys, approvals, audit trails, prompt-injection resistance;
protocol transport versus authorization enforcement. Show untrusted retrieved
content requesting an action and the application rejecting it under policy.
Practice: an executed local tool-stub harness with allowed, denied, malformed,
replayed and timed-out calls (Lab L22); a system prompt is not access control.

**F5 Managed AI building blocks and platform choices** — NEW `dbxfe-ai-platform`.
Documented roles of foundation-model access, AI functions, Agent Bricks
patterns, Knowledge Assistant/Supervisor/custom agents, model serving,
governance gateways, evaluation integration; verified names and status. Show
a decision table based on customization, data access, operations, evaluation
and risk. Practice: a supported-pattern selection with alternatives, explicit
availability/cost assumptions and an evaluation plan; when simple retrieval
beats autonomous tool selection; no parity inferred from launch blogs.

**F6 Databricks Apps and application architecture** — NEW `dbxfe-apps`.
Front-end/back-end/data path, application identities, authorization, secrets,
user context, state, dependencies, request validation, serving, operational
responsibility; link G5 for transactional design. Show browser → application →
data/model/tool with separate trust boundaries. Practice: an original
application blueprint, local mocked contract tests and a deployment guide;
a local mock is not a deployed app; nothing added to SpicyBrain's runtime.

## Track G — Architecture, migration and operations

**G1 Architecture reasoning and migration decisions** — KEEP `dbxfe-m08`.
Requirements, constraints, assumptions, alternatives, tradeoffs, current
well-architected principles across reliability, security, governance,
performance, operations, cost, interoperability. Show two defensible
architectures including a decision not to migrate yet. Practice: decision
record, annotated target, unresolved questions, staged migration plan and
what would reverse the recommendation.

**G2 SQL Server and on-premises modernization** — NEW `dbxfe-sqlserver`.
Stored-procedure decomposition, SSIS-style orchestration mapping, source
semantics, incremental state, temporary objects, data types, transactions,
nulls, collation/time behaviour, scheduling, reconciliation. Show an original
small on-premises pipeline and an intentionally non-equivalent translation.
Practice: dependency inventory, tested target transformation, source-to-target
checks and a coexistence/cutover plan (Lab L24); no SQL Server execution
claimed; no real employer schemas.

**G3 Warehouse and distributed-platform migrations** — NEW `dbxfe-warehouse-migration`.
Inventory, workload segmentation, dependency mapping, dialect differences,
security models, data movement, BI continuity, validation, tooling, phased
coexistence; legacy warehouses, Hadoop/Spark and other cloud platforms from
each vendor's primary material. Show migration waves and a reconciliation
matrix with risk classes. Practice: a migration assessment and a defendable
pilot → parallel run → cutover → rollback sequence (Lab L24); automated
conversion proves no equivalence.

**G4 Production operations, observability and recovery** — NEW `dbxfe-operations`.
System evidence, logs, metrics, lineage, ownership, alerting, incident
triage, service objectives, dependency failures, recovery objectives,
runbooks; availability versus durability versus freshness versus correctness.
Show a fictional incident timeline separating facts from hypotheses.
Practice: evidence-based diagnosis, recovery plan, communication update and
prevention review with recovery validation and data-loss windows; table
history alone is not a backup strategy.

**G5 Lakebase, Postgres and operational state** — NEW `dbxfe-lakebase`.
Transactional versus analytical access, relational modeling, connection
management, authentication, transactions, concurrency, application state,
branches/recovery, analytical integration per current Lakebase documentation.
Show operational requests and analytical pipelines as different
responsibilities. Practice: transactional application design, locally tested
SQL on real PostgreSQL where available, and a platform compatibility checklist
(Lab L23); SQLite is never called Postgres; freshness/consistency tradeoffs of
synchronization.

**G6 Manufacturing and cross-industry solution patterns** — NEW `dbxfe-industry`.
Original patterns for quality analytics, traceability, maintenance,
scheduling/supply constraints, demand, document knowledge, engineering data;
event identity, units, timestamps, asset hierarchies, business grain; transfer
to retail, financial services and healthcare without compliance or safety
advice. Show operational source → governed data → decision → responsible
human action. Practice: a use-case brief with metric contract, architecture,
risks, evaluation criteria and a realistic "not enough evidence yet" outcome.

## Track H — Customer discovery, evidence and delivery (all retained)

**H1** `dbxfe-m01` teamwork and the customer decision journey (opportunity
collaboration brief, responsibility map). **H2** `dbxfe-m02` discovery and
qualification (interview plan, synthesis, prioritized follow-ups with partial
disclosures). **H3** `dbxfe-m09` demos and technical storytelling (short and
extended scripts, setup checklist, recorded-evidence fallback). **H4**
`dbxfe-m10` proofs of value (charter, test matrix, evidence log, blocker
communication, mixed-result readout). **H5** `dbxfe-m11` competition,
coexistence and business value (neutral comparison with unknown cells,
alternatives memo, reproducible fictional value model). **H6** `dbxfe-m12`
execution, written communication and capstones (executive summary, technical
handoff, escalation packet, next-step email over the three capstones);
discovery, correctness, tradeoffs, communication and evidence assessed
separately; no readiness percentage, hiring judgment or credential.
