<!-- section:why -->

The pilot starts tomorrow, but one team expects three plants and another expects only a synthetic example. A written charter turns those mismatched expectations into explicit decisions before work expands.

<!-- section:understand -->

A charter is a compact agreement about why the test exists, what it includes, how it runs, who owns the work, and how the result will be judged. It does not need to be long. It needs to eliminate the ambiguities that would make a result uninterpretable.

For fictional Cinderline, identify the plant and data population, approved fields, source/correction semantics, test window, environment, and workload. List measurable thresholds, including correctness and recovery rather than only a latency target. Assign customer acceptors and technical owners. Define budget and access prerequisites before executing anything that can spend money or touch real data.

A stop condition states when to pause: missing access approval, unexpected sensitive data, spending outside the authorized bound, or a failure that makes the comparison invalid. A change-control note records any scope revision with its effect on the evidence. Do not silently add a second use case during the test.

<!-- section:see -->

**Reusable charter fields, with fictional entries.**

| Field | Cinderline proposal |
|---|---|
| Purpose | Decide whether to expand a trusted quality feed |
| Scope | One approved plant; five staffed reporting days |
| Data | Defined inspection keys/revisions; approved fields only |
| Criteria | Key/total reconciliation, agreed freshness, safe replay, owned failures |
| Roles | Data lead executes; quality lead accepts meaning; security approves access |
| Limits | Budget and environment require explicit agreement |
| Stop | Unapproved data/access or invalid measurement basis |
| Readout | Results, exceptions, costs, remaining risks, decision |

The unagreed budget is an open prerequisite, not permission to proceed.

<!-- section:deeper -->

Describe test-data representativeness. Synthetic data can validate logic, but it may not exercise real source latency, skew, schema changes, or permissions. A real sample may omit rare but consequential failure cases. Use purposeful synthetic edge cases alongside permitted representative data, and label each evidence type. Optional cloud execution would need approved credentials, permissions, runtime/region, cost limits, cleanup, and an actual run record; none is automatically provided by this course.

<!-- section:customer -->

For the project team: “Before execution, let us agree the one-plant population, exact success criteria, access and spending limits, and who accepts each result. If those change, we will update the charter and say what the changed test can still establish.”

<!-- section:try -->

A fictional sponsor asks to add the maintenance assistant halfway through the quality pilot. Write a response that preserves useful momentum without silently mixing two different acceptance tests.

<!-- section:revisit -->

A useful response acknowledges the interest and proposes a separate scoped follow-up: “The assistant has different data, access, and evaluation requirements. We can record it as a next decision, but adding it now would change the quality pilot's scope and effort. Let us finish the agreed evidence or explicitly revise the charter, budget, owners, and readout before starting the new use case.”

The point is not rigidity. It is maintaining an interpretable test and informed agreement about additional work.
