<!-- section:why -->

A customer asks, “Why not keep what we have?” Treat that as a legitimate architecture and investment question, not an objection to defeat with a generic battlecard.

<!-- section:understand -->

Start a comparison with the workload, constraints, and accepting stakeholders. Decide which criteria matter: correctness, latency under a stated load, source compatibility, governance, operating effort, migration risk, and total cost. Then compare each option on the same basis.

Keep current state and coexistence credible. A platform may fit new workloads while the customer retains a stable existing report. The cost and risk of migrating everything can exceed the benefit of the first use case. A phased design can be a valid outcome rather than a compromise to hide.

For fictional Cinderline, compare improving the scheduled SQL path, introducing a shared analytical quality path, and staged coexistence. This course does not claim one vendor is universally faster, cheaper, or more secure. A detailed product comparison would need each vendor's current primary documentation and a fair workload test. Marketing labels alone are insufficient evidence.

<!-- section:see -->

**Fictional evidence matrix.**

| Criterion | Improve current path | New analytical path | Coexistence |
|---|---|---|---|
| Metric correctness | Test shared definition | Test shared definition | Test consistency across paths |
| Migration work | Smaller proposed change | Larger proposed change | Temporary dual operations |
| Future reuse | Need to assess | Need to assess | Need to assess |
| Source/access fit | Verify | Verify | Verify both |

“Need to assess” is an honest cell. It should not be replaced with a green check merely because one option is preferred.

<!-- section:deeper -->

If numerical scoring is used, show weights and evidence quality. Do not assign precise ratings to unknown features or subjective impressions. If a criterion is mandatory, such as an approved access boundary, a high average score elsewhere cannot compensate for failing it. Record feature version/cloud/region and the date of product assertions. A competitor's limitation may change; a remembered claim is not sufficient for a customer-facing recommendation.

<!-- section:customer -->

For the sponsor: “Keeping and improving the current path is a real option. Let us compare it with the proposed path and coexistence using your required outcomes, migration effort, and operating constraints. Where evidence is missing, we will say so.”

<!-- section:try -->

A fictional comparison slide says “our option is always faster and cheaper.” Rewrite it as a testable, workload-specific comparison without inventing a benchmark.

<!-- section:revisit -->

A better statement: “For the agreed one-plant quality workload, compare end-to-end freshness, query latency under the same concurrent use, correctness, operating effort, and total cost basis. Include the current path and record source/cloud/configuration conditions. We have not measured a performance or cost advantage yet.”

This is less dramatic but more useful. It tells the customer how a preference could become a defensible conclusion and leaves room for the evidence to favor another option.
