<!-- section:why -->

After discovery, the customer wants a target architecture. The diagram should explain what changes and why, while preserving the constraints that could still change the design.

<!-- section:understand -->

A target architecture is a proposal for responsibilities and interactions that satisfy stated requirements. Start from the current path and the business outcome, then identify what must change. Mark data movement, processing, serving, identity, trust boundaries, and operational owners. A box with no owner is an unresolved part of the proposal.

For fictional Cinderline, the current path is ERP and corrected CSVs into analyst workbooks. A target could retain source ownership while creating an accepted quality dataset and a defined reporting interface. The source system remains the system of record for inspection entry; the analytical copy does not become a new operational ERP merely because it is convenient to query.

Attach assumptions to the design. We assume a permitted extraction path, stable inspection identity, an agreed correction order, and a customer team that can operate the feed. Each assumption needs an owner and validation. Show the data you need, not every platform capability that could someday exist.

<!-- section:see -->

**Fictional architecture delta.**

| Responsibility | Current | Proposed change |
|---|---|---|
| Inspection entry | SQL Server ERP | Retained |
| Corrections | CSV and analyst interpretation | Explicit accepted-revision rule |
| Shared metric | Several workbook definitions | One owned definition and served result |
| Failures | Manual discovery | Named alerts, quarantine, replay owner |

The delta makes the scope reviewable. It also exposes that a metric agreement and operating change are as important as the new data path.

<!-- section:deeper -->

Data copies create responsibilities: retention, deletion, sensitivity, synchronization, and reconciliation. A simplified diagram should state what it omits, such as detailed network routing or disaster-recovery configuration. Under the AWS teaching choice, classic/serverless compute boundaries must match the intended deployment. A conceptual sketch is not evidence that permissions, network paths, or production recovery have been configured.

<!-- section:customer -->

For an architect: “We propose retaining the ERP as the inspection system of record and creating a governed analytical path for the agreed quality metric. The design is conditional on source access, correction semantics, and operating ownership; we will validate those before expanding scope.”

<!-- section:try -->

Sketch Cinderline's target as five responsibilities: sources, raw retention, accepted records, serving, and operations. Add a trust boundary and identify two assumptions that would materially change the design.

<!-- section:revisit -->

A defensible sketch retains source owners, copies only approved records into raw retention, resolves identity/version and quality into accepted records, and exposes the agreed metric through a serving interface. Operations spans freshness monitoring, rejected-data investigation, and replay. Mark the selected compute/customer-data boundary and leave network configuration conditional.

Two material assumptions are source extraction permission and reliable correction ordering. If either fails, the design may need an approved batch path or a different reconciliation process. Make that alternative visible rather than drawing an unconditional arrow.
