<!-- section:why -->

Two dashboards display different defect rates. Before comparing query speed or visualization tools, establish whether they are calculating the same business quantity.

<!-- section:understand -->

A metric contract defines the quantity, grain, numerator, denominator, time basis, exclusions, and owner. **Semantic** in this context means shared meaning: users should not have to reverse-engineer a query to know what a number represents. A dashboard presents the result; it should also reveal freshness and important limitations.

For fictional Cinderline, “defect rate” might mean defective units divided by inspected units, inspections with any defect divided by total inspections, or rejected shipments divided by shipments. All can be legitimate metrics, but they answer different questions. Choose the one that supports the decision and label it clearly.

Databricks SQL provides analytical querying through SQL warehouses and BI interfaces. A warehouse supplies compute for SQL work; it does not automatically reconcile conflicting metric definitions. The customer still needs an agreed data model, access policy, and ownership for business changes.

<!-- section:see -->

**Fictional same data, different questions.** Inspection A has 12 units and 1 defective unit; inspection C has 8 units and no defects.

| Metric | Calculation | Result |
|---|---|---|
| Unit defect rate | 1 defective unit / 20 inspected units | 5% |
| Inspections with a defect | 1 inspection / 2 inspections | 50% |

Neither result is a benchmark. The table teaches why a metric label must name its denominator. A dashboard called “quality 50%” would be ambiguous even if its query is fast.

<!-- section:deeper -->

Define how late corrections affect published history. Does a report show values as known at the original meeting, or restate historical values after correction? Both are defensible if labeled. Confirm the time zone, business-day boundary, and plant identifiers. Trace a selected dashboard figure back through its aggregation to accepted source records; visual plausibility is not reconciliation evidence.

<!-- section:customer -->

For a plant manager: “This view will show defective units divided by inspected units, with the data cut-off beside it. We will keep that different from the percentage of inspections that found any defect, so your team can act on an unambiguous measure.”

<!-- section:try -->

Draft a metric contract for the unit defect rate. Include the denominator, reporting grain, correction policy, freshness label, and owner. State one question you must confirm rather than assume.

<!-- section:revisit -->

A possible contract is: “Accepted defective units divided by accepted inspected units, grouped by plant and business day; zero denominators display ‘not defined,’ not 0%. Historical values are restated after approved corrections and labeled with the latest accepted data cut-off. The quality lead owns the definition, and the analyst validates the calculation.”

Confirm the business-day boundary and restatement policy with the customer. The contract is an educational example; it is not already approved. A small set of representative records should accompany the definition so a later implementation can be checked.
