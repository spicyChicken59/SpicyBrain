# Reliable Data Foundations: authored curriculum and review

Builder editorial review, 19 September 2026. This is a self-review of the approved study-hub milestone, not independent learner validation. It supersedes the universal role-first/seven-section assumptions for these authored packages. It does not claim to recover an unavailable original Markdown brief.

The path promises a bounded outcome: explain platform responsibilities and transform changing synthetic input into a trustworthy, replayable analytical result. It does not claim complete Databricks coverage, official onboarding, an internal level rubric or readiness scoring. The existing field-practice material and other introductory technical topics remain accessible.

## Coverage and editorial findings

Every package has outcomes, prerequisite guidance, mechanism, worked example, actionable attempt, a separately revealed explained solution, mistakes/limits, related topics and source/claim links. The five reused lessons retain their original sections and assessment IDs verbatim, add new deeper assessment IDs, and advance to content version 2.0.0. Seven genuinely new topics use new stable IDs. Every package adds two explained checks and three distinct cards; this is 24 new checks and 36 new cards without counting any duplicate copies.

| Package | Canonical ID | Reviewed mechanism/example/transfer evidence |
|---|---|---|
| B1 Python | `dbxfe-python-bridge` | Dictionaries, types, explicit conversion, missing versus None, functions, loops, JSON/CSV, exceptions and assertions are used in a complete parser. The learner adds defects validation to a different input. Corrected truthiness/coercion misconceptions. |
| B2 Cloud | `dbxfe-cloud-bridge` | DNS, routing, compute/storage and principal/action/resource authorization are separated. AccessDenied, DNS failure and timeout support different hypotheses. The learner diagnoses with actual identity/context rather than broad grants. |
| 01 Workspace/storage/compute | `dbxfe-workspace-compute` | Query trace separates authoring, execution, governed access and durable data. Classic versus serverless AWS ownership is labeled. A stopped-session exercise distinguishes durable tables from transient Python state. |
| 02 Delta files/log/snapshots | `dbxfe-m03-l02` | Schematic f0/f1/f2 timeline yields 18/1 then 20/1; scanning all physical files yields wrong 30/2. The changed commit yields 22/1 only after commit. No real log editing or retention reduction is taught. |
| 03 Unity Catalog | `dbxfe-m06-l01` | Hierarchy and managed/external lifecycle are distinct. Access matrix isolates SELECT and parent usage under explicit execution assumptions. Consumer and denied-action tests avoid treating admin success as evidence. |
| 04 DataFrames | `dbxfe-dataframes` | Complete LongType/string schema, null tests, filter, projection, alias and double cast. Intermediate rows/types are explicit. Changed 5/7 and 0/0 inputs test quantities and denominator meaning separately. |
| 05 SQL/PySpark | `dbxfe-m04-l01` | Complete multi-step equivalents with literal rows and type assertions. Inspection-to-plant grain and unit weighting are explicit; correction and zero-denominator transfer cases are explained. |
| 06 Grain/joins/execution | `dbxfe-grain-joins` | Matching-pair arithmetic explains 32/2 versus 20/1, then changed 44/3. Semijoin fits an existence requirement. Lazy actions, partitions, shuffle and actual plan inspection are bounded to local evidence. |
| 07 Identity/order | `dbxfe-m04-l02` | Delivery identity, business key, source revision and arrival are distinct. The original five-row baseline is unchanged. Classification includes replay, redundant evidence, older arrivals, correction, equal-version conflict and missing order. |
| 08 Resolution | `dbxfe-record-resolution` | Raw=5, distinct=4, invalid=1, valid revisions=3, accepted=2. Invalid latest never resurrects older A; C-only 8/0 is diagnostic, not a current report. Full Python and Spark source is readable in the app. |
| 09 Guarded updates | `dbxfe-versioned-updates` | Complete target-copy update preserves original target and guards source uniqueness, newer/equal/older versions. Illustrated Delta SQL names DBR 16.4 LTS and remains unexecuted. Absence is not deletion. |
| 10 Recovery/transfer | `dbxfe-m04-l03` | Named retained_raw and published_snapshot failures distinguish stale data from pending local effect. Recovery compares explicit 22/1 rows/totals. Order-line task uses composite identity, integer cents and explicit cancellation, with full solution. |

See [machine-readable coverage](evidence/reliable-data-coverage.json), [pre-edit disposition](CURRICULUM-DISPOSITION.md), and [exact preservation audit](evidence/curriculum-preservation-audit.json). The audit compares all 36 original bodies (normalizing only newlines), 252 section metadata records, 108 cards and 72 complete check/option/rationale sets against the immutable baseline. The totals are 43 lessons, 144 cards and 96 checks, with the original 12 module scenarios, 12 diagrams and capstone retained, plus six new diagrams. Counts are structural evidence and do not replace the findings above.

## Visual review

The six new original SVGs were rendered in local Chromium and inspected in [the contact sheet](evidence/reliable-data-diagrams.png). Their labels, arithmetic and arrow meaning were read against their attached lesson. Every SVG includes title/description and content metadata supplies caption, alt text, complete text equivalent, provenance and claim links. They depict request ownership, snapshot membership, catalog grants, matching-pair multiplicity, unresolved latest revision and failure boundaries. No image depicts an invented product screen.

The contact sheet establishes asset-level visual inspection; the complete reader, zoom dialog, themes, mobile reflow and keyboard controls require the separate production-browser acceptance evidence. Original diagrams remain unchanged.

## Execution honesty and review corrections

The [actual local exercise tests](EXERCISES.md) passed 30 tests with zero failures/errors/skips using Python 3.12.14, Spark 4.0.4 and Java 17.0.20.1+1. [Seven displayed-code hashes](evidence/displayed-code-verification.json) were rechecked against the executed manifest after final source-embed synchronization. A passing schema, arithmetic prediction or illustrative SQL block is not a Databricks run. The initial Spark 4.0.1 local attempt exposed the upstream Windows/Python worker defect and was replaced before completion claims. Full commands, versions, fixture hashes and outputs belong in the exercise evidence, not inferred from this editorial review.

Editorial corrections made before handoff: aligned the transfer text with actual O7/L1 current 900-cent line and O7/L2 cancellation; changed the recovery driver to read the actual `batches.json` correction; distinguished the introductory LongType expression demo from the stricter IntegerType event contract; made diagnostic candidate totals versus publication status explicit; preserved complete original material while adding separately attempted deepening tasks. Five new card drafts that overlapped older recall prompts were replaced with distinct uncommitted-file, projection, zero-denominator, redundant-delivery and denied-access applications before release. New questions use one correct answer and a rationale for each distractor; old questions/cards are unchanged and remain historical evidence when already answered.

## Source review scope

New/deepened mechanisms were checked against current primary pages on 19 September 2026. Python language references use the 3.12 documentation; Spark references use 4.0.4 instead of a moving latest URL. Databricks and AWS pages are reviewed as AWS-context mechanisms, not executed environments. A separate source-availability check is not a substitute for this claim reading.

| Claim group / package use | Specific source reading and limit |
|---|---|
| `dbxfe-foundation-python` · B1, full local source | Python data structures, control flow/functions, files/JSON, exceptions and csv.DictReader. Language behavior supports the explanation; strict quantity parsing is authored policy. |
| `dbxfe-foundation-cloud` · B2 | AWS S3 object model, IAM policies, VPC route tables and Route 53 DNS. Conceptual request responsibilities only; no account/network provisioning or test. |
| `dbxfe-fact-architecture` · 01 | Databricks high-level AWS architecture: customer-account classic compute and Databricks-managed serverless plane. Region, type and resource path require separate checks. |
| `dbxfe-fact-delta`, `dbxfe-fact-delta-protocol` · 02 | Delta data files plus log, committed table versions and supported client features. Original simplified timeline is not a full transaction-log representation or guaranteed physical rewrite strategy. |
| `dbxfe-fact-unity`, `dbxfe-fact-privileges` · 03 | Unity Catalog hierarchy/lifecycle and Privilege Model 1.0 basic table reads requiring SELECT plus parent usage. Fictional matrix explicitly fixes other execution assumptions. |
| `dbxfe-foundation-spark` · 04–06, 08 | Pinned quickstart, NULL semantics, DataFrame.join and DataFrame.explain. DataFrame expressions, null predicates, semijoin semantics and formatted plan scope; actual synthetic outputs come from independent arithmetic/local tests. |
| `dbxfe-foundation-policy` · 07–10 | Original conservative replacement/reconciliation/publication policy. Source links support implementation mechanisms only, not an official business rule. |
| `dbxfe-fact-merge` · 09 | Current MERGE page explicitly distinguishes DBR 16.0+ duplicate matching from <=15.4 LTS. DBR 16.4 LTS release page identifies the illustrative environment; no Delta execution claim. |
| `dbxfe-fact-jobs`, `dbxfe-fact-pipelines`, `dbxfe-fact-expectations` · 08/10 | Jobs coordinates tasks; declarative pipelines and Databricks-managed context are distinguished; row-quality actions do not prove source reconciliation or external-effect idempotency. |

Exact publishers, URLs, dates, context and caveats live in `course.json`; claim IDs connect them to sections, checks, cards and assets. Unchanged introductory material retains the baseline review record rather than being presented as newly independently reviewed. Re-review after material documentation changes; no source-availability result is a truth certification.

## Bounded publication-gate correction — 19 September 2026

The initial milestone review and 30-test evidence above remain historical. They did not cover the independently reproduced conflict whose event ID was nonempty but whose inspection IDs were unusable. Guidance's two failing cases came from isolated execution of the reviewed source on Python 3.13.5/Linux; they were not independent browser, Spark or Databricks acceptance. The correction is part of the same PR #2 and implements the already stated original exercise policy, without changing a Databricks factual claim or the 43-lesson inventory.

The affected `dbxfe-record-resolution` explanation, worked example, attempt and revealed solution now distinguish three things: row quarantine, global provenance conflict evidence and the list of attributable unresolved inspection keys. Missing/null/empty/whitespace-only inspection IDs do not supply an artificial business key. A contradictory nonempty event ID still blocks a new report. The first-publication example therefore requires `blocked_no_snapshot`, no published snapshot and no simulated effect. The cross-batch example may prepare A v3 plus C at 22/1 diagnostically, but must retain the exact previous 20/1 snapshot as `stale_previous` with its effects unchanged. Baseline B's disclosed, nonconflicting exclusion remains permitted.

The embedded complete Python and SQL/PySpark sources are synchronized from the corrected authored files through the supported `sync_lesson_examples.py` workflow before final execution and packaging. The Spark teaching explicitly requires consuming the global publication decision and conflict counts; zero unresolved-key rows alone are insufficient. Spark exposes transformations/diagnostics, while the separate Python simulation controls the modeled published snapshot and local outbox. No website deployment or real notification is involved.

Material version decisions preserve identity and prior evidence:

| Item | Change | Reason |
|---|---|---|
| `dbxfe-record-resolution` | 1.0.0 → 1.1.0 | Adds the missing-key provenance example and repairs the complete source implementation taught by this package. |
| `dbxfe-record-resolution-foundation-q2` | Revision 1 → 2 | The diagnostic-versus-published question now assesses the unkeyed conflict and valid correction together. Option IDs and the correct-option ID stay stable; previous prompts/options/selected answers remain historical records. |
| `dbxfe-record-resolution-foundation-card1` | Revision 1 → 2 | Extends the quarantine/current-state distinction to global conflict evidence without an attributable key. Existing review events remain revision-1 history; normal revised-material behavior applies. |
| Remaining cards/questions | No revision change | Their meaning and answers are unchanged. A content correction does not justify manufacturing revisions for unrelated assessments. |
| Course | 2.0.0 → 2.0.1 | Records this bounded material correction in course change notes. |

Other actual consumers were inspected: the identity/ordering topic already blocks unresolved identity conflicts without a keyed-only exception; guarded updates already require the resolver's `publication_allowed` gate; LocalPipeline and its recovery lesson already obey that gate. Their independent displayed examples and assessment meanings need no change. Final corrected run counts, source/snippet/archive hashes and production-reader revision-preservation evidence are recorded in the correction acceptance evidence, rather than attributed to the initial green run above. This remains builder editorial review, not independent learner validation.
