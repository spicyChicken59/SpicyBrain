# Builder editorial review

Completed 2026-09-19. Scope: all **36 lesson bodies**, all **72 question/answer/rationale sets**, all **108 cards and their concept/claim links**, all **12 original diagrams** (rendered and visually inspected), all **12 module scenarios**, and the separate full capstone model/rubric. This is the implementing builder’s self-review; independent guidance acceptance is pending. Schema tests prove structure, not truth.

The review checked explanations and actionable exercises, misconceptions, answer uniqueness, worked arithmetic, source scope, fiction labels, audience explanations, diagrams/text equivalents, and evidence limits. Findings below describe the actual review or correction. No cloud or workspace exercise was executed.

| Lesson                                                                | Review finding / correction                                                                                           |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `dbxfe-m01-l01` · What field engineering contributes                  | Capability/hypothesis/evidence are distinguished; synthetic demo scope stays bounded.                                 |
| `dbxfe-m01-l02` · Work with the account team                          | Handoff separates owner/contributor/acceptor; unconfirmed ownership is labeled.                                       |
| `dbxfe-m01-l03` · Move from discovery to decision                     | Decision gate preserves a positive sample result and an unresolved operating risk.                                    |
| `dbxfe-m02-l01` · Find the outcome behind the request                 | Neutral discovery questions avoid invented causal financial savings.                                                  |
| `dbxfe-m02-l02` · Map the current technical landscape                 | Connector promise remains conditional; replaced trivial quiz distractors with arrival-order/transport misconceptions. |
| `dbxfe-m02-l03` · Define success and expose missing information       | 18/20 is correctly 90%; the missing timestamp is not dropped from the denominator.                                    |
| `dbxfe-m03-l01` · Lake, warehouse, lakehouse: start with the workload | Retain-current-state retailer alternative is credible; no blanket vendor ranking.                                     |
| `dbxfe-m03-l02` · Separate storage, compute, tables, and governance   | Table transactions are separated from business correctness; improved protocol-mismatch distractors.                   |
| `dbxfe-m03-l03` · Explain the platform through customer needs         | Classic/serverless boundaries stay cloud-specific and conditional in the customer narrative.                          |
| `dbxfe-m04-l01` · Use SQL and Python to explain a transformation      | Grain and weighted 5% versus unweighted 4.17% are correct; SQL/PySpark are illustrative.                              |
| `dbxfe-m04-l02` · Choose ingestion and incremental semantics          | Five-row input reconciles to A v2+C, B quarantined, 20/1; local deterministic test added.                             |
| `dbxfe-m04-l03` · Make a pipeline recoverable                         | External effects remain separate from table commits; retry distractors now target realistic idempotency errors.       |
| `dbxfe-m05-l01` · Build a metric people can trust                     | Unit rate 5% and inspection incidence 50% are distinct; zero denominator is undefined.                                |
| `dbxfe-m05-l02` · Diagnose a slow query                               | Synthetic queue/execution/transfer timing is labeled; cache/profile limitations preserved; distractors clarified.     |
| `dbxfe-m05-l03` · Balance concurrency, latency, and cost              | Median improvement cannot satisfy a failed tail criterion; cost claims remain hypothetical.                           |
| `dbxfe-m06-l01` · Understand Unity Catalog responsibilities           | External lifecycle and governed access are separated; direct storage bypass remains a check.                          |
| `dbxfe-m06-l02` · Design least-privilege access                       | SELECT plus parent usage and intended identity are explicit; quiz answer set checked for ambiguity.                   |
| `dbxfe-m06-l03` · Draw the cloud and trust boundaries                 | Two AWS compute alternatives are labeled; exact private-network configuration/availability stays unverified.          |
| `dbxfe-m07-l01` · Start ML with a baseline and a valid target         | Prediction timing excludes post-repair data; added direct primary leakage source to section/card/check claims.        |
| `dbxfe-m07-l02` · Choose retrieval or a tool-using agent              | Rewrote an ambiguous retrieval-guarantee question so only one choice answers the required remaining checks.           |
| `dbxfe-m07-l03` · Evaluate quality, risk, and operating cost          | Unauthorized disclosure blocks the proposed expansion; model judges are fallible, not safety certificates.            |
| `dbxfe-m08-l01` · Turn current state into a target design             | Analytical copy does not transfer ERP authority; source assumptions have owners.                                      |
| `dbxfe-m08-l02` · Defend tradeoffs and alternatives                   | Scheduled and incremental alternatives depend on source timing/operating capacity.                                    |
| `dbxfe-m08-l03` · Migrate with reconciliation and rollback            | Matching totals can hide different keys; rollback retains a viable fed old path.                                      |
| `dbxfe-m09-l01` · Discover the demo audience and decision             | Demo intent follows the audience decision; no compulsory feature tour.                                                |
| `dbxfe-m09-l02` · Tell a story with visible evidence                  | 1/18≈5.56% becomes 1/20=5%; expected versus observed results are explicit.                                            |
| `dbxfe-m09-l03` · Recover from failure and unknown questions          | Failure fallback is prepared evidence, never a claimed live run; unknown compatibility gets an owner.                 |
| `dbxfe-m10-l01` · Build a baseline and a hypothesis                   | Five-day technical evidence excludes company-wide scrap savings.                                                      |
| `dbxfe-m10-l02` · Write the charter before execution                  | Unapproved budget blocks paid execution; assistant is a separate scope decision.                                      |
| `dbxfe-m10-l03` · Read out evidence and make a decision               | Pass/fail/blocked/not-tested stay separate; local synthetic pass is backed by the deterministic test.                 |
| `dbxfe-m11-l01` · Compare options honestly                            | Current state/coexistence stay credible; no memory-based competitor claim.                                            |
| `dbxfe-m11-l02` · Handle objections as information                    | Operating capacity can change or pause the proposal; partner commitments remain conditional.                          |
| `dbxfe-m11-l03` · Make a transparent value calculation                | Verified low/base/high, break-even 9.375 h/week and six-hour net −$9,720; no real prices used.                        |
| `dbxfe-m12-l01` · Prioritize the next useful field action             | Priority follows blocking uncertainty; optional learning rhythm is not employer policy.                               |
| `dbxfe-m12-l02` · Write follow-ups people can act on                  | Follow-up distinguishes discussed/agreed/observed; no fabricated approval or root cause.                              |
| `dbxfe-m12-l03` · Assemble the customer engagement                    | Synthesis carries one metric across all artifacts; self-assessment does not imply readiness.                          |

## Diagram review

Rendered all SVGs in Chromium and inspected [the contact sheet](evidence/diagram-contact-sheet.png). Checked label clipping, arrow meaning, contrast, original-schematic labeling, accessible caption/alt/text equivalence, and the relevant lesson attachment. Each diagram teaches a different relationship; none is captured product UI.

| Module | Visual relationship and inspection finding                                                             |
| ------ | ------------------------------------------------------------------------------------------------------ |
| 01     | Role/contribution/handoff swimlanes; no official employer org-chart claim.                             |
| 02     | Stakeholder concerns converge on a discovery brief; each has a distinct evidence need.                 |
| 03     | Storage/table/compute responsibilities and governance/business rules remain distinct.                  |
| 04     | Correction and quarantine paths include an owner and replay loop; expected A/C totals are correct.     |
| 05     | Diagnostic branches separate waiting, execution and delivery; all return to one controlled test.       |
| 06     | Classic and serverless are explicit alternatives with different ownership boundaries.                  |
| 07     | Read-only evidence flow and optional authorized tool action are separate; human escalation is visible. |
| 08     | Current and target parallel paths pass a reconciliation gate; retain/rollback remains reachable.       |
| 09     | Demo success and failed-execution fallback are separate branches with honest labels.                   |
| 10     | Evidence readout branches to expand, revise/retest, or retain/stop.                                    |
| 11     | Both benefit and cost inputs feed net value; hypothetical arithmetic matches the lesson.               |
| 12     | Current decision, evidence, risk and next action form a revisiting loop; no activity score.            |

## Practice and capstone

All 12 scenarios have distinct contexts/tasks, requirements, complete model reasoning and three anchored rubric dimensions. The capstone has six authored stakeholder disclosures, six required deliverable groups and six rubric dimensions. Its complete model includes discovery and owners, current/target/alternative, AWS identity boundaries, phased migration/cutover/rollback, a full demo/failure script, charter and readout, low/base/high value arithmetic, objection response and a complete next-step email. Several defensible designs remain possible. No automatic free-response grade or official level mapping is claimed.

## Corrections discovered in platform acceptance

Fixed blocked-upgrade text replay, ambiguous quiz wording/distractors, actual-vs-next review dates, remote font-import stripping, revised-question notice, and narrow large-text intrinsic sizing. Browser test selectors were corrected where a wrapping label included its form value; those were test errors, not evidence of lost drafts. The extension browser now reloads the bundle after rebuilding, rather than treating a hash-only navigation as a new build. See acceptance logs for final results.
