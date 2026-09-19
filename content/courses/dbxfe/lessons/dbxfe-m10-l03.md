<!-- section:why -->

The pilot ends with several good results and one unresolved access problem. A useful readout preserves the mixed evidence and helps the customer choose what to do next.

<!-- section:understand -->

A decision readout compares observed results with the agreed criteria on the actual tested scope. Separate pass, fail, not tested, and blocked. A blocked test is not a pass; it may be a dependency rather than a defect, but it still limits the conclusion.

For fictional Cinderline, sample reconciliation may pass while recovery remains untested and network access is conditional. Report each result, the evidence location, exceptions, owner, and recommended next action. Do not combine these into a single impressive score that conceals a blocking condition.

Interpret evidence in decision terms: expand a bounded slice, revise the design, collect missing evidence, retain the current path, or stop. Explain why the recommendation follows. Preserve the original threshold and any agreed scope changes so a future reviewer can understand what was actually tested.

<!-- section:see -->

**Hypothetical readout; no real execution.**

| Criterion | Status | Evidence / next action |
|---|---|---|
| Synthetic correction totals | Pass in a local deterministic check | Exact A/C outputs match |
| Real source connectivity | Not tested | Customer approval and environment needed |
| Recovery on the deployed path | Not tested | Rehearsal after configuration |
| Metric meaning | Proposed | Quality/operations acceptance needed |

The conclusion is readiness to review a test design, not readiness to expand a production deployment.

<!-- section:deeper -->

Distinguish a defect from a limitation of the test. A wrong aggregation is a defect; a synthetic sample's lack of production skew is a scope limitation; missing access is a blocker. All matter, but they imply different actions. Record costs on their actual basis and distinguish incurred usage from projected operation. A readout can recommend stopping if the evidence does not justify further investment.

<!-- section:customer -->

For the sponsor: “The local logic check supports the correction rule on the synthetic inputs. Source connectivity and deployed recovery are still untested, so we recommend resolving access and running the bounded pilot before making an expansion decision.”

<!-- section:try -->

Write a five-line readout for a fictional pilot where correctness passed, freshness missed the agreed target, and recovery was blocked by an unavailable operator. Include the recommendation and owners.

<!-- section:revisit -->

“Correctness passed on the agreed population; evidence is the key/total reconciliation record. Freshness missed the agreed target; the data engineer owns diagnosis using the recorded timing distribution. Recovery was blocked because an operating owner was unavailable, so it remains untested. The customer data lead will nominate the operator and schedule the rehearsal. We recommend a bounded correction/retest before expansion, retaining the current reporting path meanwhile.”

This preserves real success without allowing it to cancel a failure or missing test. It also provides concrete next evidence rather than an open-ended request to keep experimenting.
