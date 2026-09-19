<!-- section:why -->

You are shadowing a customer architecture discussion. Instead of reciting a product menu, connect each capability to a need the customer has actually expressed.

<!-- section:understand -->

A platform narrative has a small number of links: the customer decision, the data required, the processing and serving path, governance, and the evidence needed to validate the proposal. Start with the decision and end with what remains to be checked.

For fictional Cinderline, the operational question is which line needs investigation at shift change. A possible path combines approved inspection records and quality corrections, applies an agreed metric, and serves the result to an analyst or dashboard. Databricks offers ingestion, transformation, SQL analytics, and governance capabilities relevant to such a path. The existence of these capabilities does not choose the exact source connector, network model, or operating plan.

Use a capability only when its responsibility is clear. Ingestion moves data; orchestration coordinates work; governance does not itself define the defect metric. If the customer asks about an unfamiliar feature, locate current documentation and involve a specialist before expanding the design. Saying “I need to validate that boundary” is more useful than filling the gap with a product name.

<!-- section:see -->

**Fictional explanation ladder.**

| Audience question | Useful response |
|---|---|
| Why change anything? | Reconcile quality information before the decision |
| How would data flow? | Approved sources → interpreted quality records → agreed metric → serving |
| Who can use it? | Named identities and least-privilege access, reviewed with security |
| How do we know it helps? | Compare the accepted metric, freshness, and operating effort against a baseline |

Explain the same system at different depth. Do not offer a different truth to each audience.

<!-- section:deeper -->

Databricks accounts, workspaces, and Unity Catalog metastores have different roles. A workspace is a collaboration and workload environment; the account is a higher-level management construct. On AWS, classic and serverless compute have different deployment boundaries. Those details matter when security asks who operates which resources. Keep cloud context visible and verify region-specific requirements rather than importing assumptions from another cloud.

<!-- section:customer -->

For the operations director: “The proposed path brings approved quality inputs into one defined calculation so your team can investigate the same number. We will verify freshness and reconciliation on a bounded sample, and confirm who owns access and failed runs before expanding it.”

<!-- section:try -->

Write a 60-second explanation for the fictional security lead. Include the data path, identities, classic/serverless boundary as an unresolved choice, and one question that must be answered before drawing a final network design.

<!-- section:revisit -->

A defensible response: “We propose an analytical copy of approved quality records, with access granted to named groups and workload identities. On AWS, classic compute would run in your account while serverless uses a Databricks-managed compute plane; we have not chosen which fits your restrictions. Which data classifications and permitted connectivity paths must this flow satisfy? We will validate the exact region and supported networking pattern with the security specialist before finalizing the architecture.”

Notice the distinction between documented deployment responsibility and a still-unmade customer choice. The narrative stays concise because it names the deciding question.
