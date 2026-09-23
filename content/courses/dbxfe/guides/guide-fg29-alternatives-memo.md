<!-- section:action -->

An alternatives memo compares options on criteria the reader would have chosen without you. Its value is in the honesty of the unknown cells, not in the count of ticks.

1. **State the decision and its constraints** in one paragraph: what must be true of any option, who operates it, what budget and access bound it.
2. **Choose criteria before options.** Correctness mechanism, availability to the decision, recovery, operating effort, access model, reversibility, cost basis, dependency on unverified prerequisites. Write what a good and a poor entry look like for each.
3. **Include the retain option** and, where honest, a coexistence option. An option set without "keep the current path" is a recommendation dressed as a comparison.
4. **Fill cells with facts you can source:** the customer's own measurements, documentation you have read and dated, or a local test. Anything else is "unknown" with a note on how to resolve it.
5. **Do not score.** A weighted sum invites arguing about weights instead of facts. Say in prose which differences matter for this decision.
6. **State what would reverse the recommendation** and which unknowns could do so.
7. **Attribute every vendor-related statement** to the vendor's own current documentation, dated, or leave it unknown.

Evidence to collect: the criteria list with good and poor definitions, the filled matrix with a source per cell, the unknowns list with resolution owners, and the reversal conditions.

Deeper: the retained lessons [Compare options honestly](#/lesson/dbxfe-m11-l01) and [Defend tradeoffs and alternatives](#/lesson/dbxfe-m08-l02), the module [Competition and business value](#/module/dbxfe-m11), and [Architecture reasoning and migration decisions](#/module/dbxfe-m08) for the decision not to migrate yet.

<!-- section:example -->

**Fictional worked example: how Cinderline should produce the plant-one morning defect rate.** Decision: which path the pilot should test, given a three-person data team without continuous support, a weekly correction cycle, a daily decision at 08:00, and a source path not yet reviewed by security.

### Options

- **A. Improve the current path.** Keep the nightly stored procedure; fix the trailing-space duplicate rule, apply the plant-time boundary, add a revision check to the CSV import, and publish the same metric from the ERP.
- **B. New scheduled path on the platform.** One plant, retained raw deliveries, explicit resolution, an accepted-inspection table and an owned metric, read by the existing report.
- **C. Coexistence for a bounded period.** Run A's fixed report and B in parallel for twenty working days, with the old report as the served path until reconciliation passes.

### Criteria and entries

| Criterion | A. Improve current | B. New scheduled path | C. Coexistence |
|---|---|---|---|
| Correctness mechanism | Fixes to three known defects; no retained raw history; correction ordering by file arrival | Retained raw, resolver with revision rule, quarantine; verified locally on synthetic input only | Both, compared daily; the comparison itself is the mechanism |
| Availability to the 08:00 decision | Unknown: current 09:15 to 11:40 is workbook time, not procedure time; procedure finish time not measured | 47 to 71 minutes after source availability in the pilot's five days, synthetic and local | Same as A until cutover |
| Recovery | Rerun the procedure; no replay evidence; no snapshot identity | Replay rehearsed once, 14 minutes | Fallback is inherent for the period |
| Operating effort | DBA already operates it; the three fixes are small; unmeasured ongoing effort | One hour per day in week one, one operator, no backup | Highest: both paths plus the comparison |
| Access model | Existing ERP grants; no new review | New identities, a source path review, region and connectivity pattern unagreed | Both |
| Reversibility | Not applicable; it is the current path | Read path; reversible within the recovery window | Designed for reversal |
| Cost basis | Unknown incremental; DBA time not costed | Hypothetical model only; no measured usage | A plus B plus comparison effort for twenty days |
| Dependency on unverified prerequisites | None new | Source version, CDC permission, security review, operator backup | Same as B |

### Which differences matter here

Two cells decide this memo. First, availability under A is unknown because nobody has measured when the procedure finishes; if it finishes by 07:00 and the workbook is the delay, A may satisfy the 08:00 decision at almost no cost, and the pilot should measure that in its baseline week. Second, B's correctness evidence is local and synthetic; it is stronger in mechanism and weaker in evidence than A's, and the memo says so rather than treating a design property as a result.

### Unknowns and how to resolve them

Procedure finish time (DBA, one week of timestamps); whether the ERP's grants permit the CSV revision check (DBA); the platform's connectivity pattern for the customer's topology (integration specialist, reading current documentation); the actual operating effort of A after the fixes (DBA estimate, then measured).

### Recommendation, and what reverses it

Test C in the form the charter proposes: fix A's three defects anyway, because they are defects in the current path regardless of the pilot; run B for one plant beside it; serve A until reconciliation passes. The recommendation reverses toward A alone if the procedure's finish time is shown to meet the 08:00 decision and the DBA can sustain the fixed path, and toward stopping B if the security review does not approve a path within the pilot window. No option is described as better in general; the memo compares them for this decision, this team and these unknowns.

<!-- section:template -->

### Decision and constraints

- **The decision in one sentence; the constraints any option must satisfy (operators, budget, access, timing); who decides.**

### Criteria

| Criterion | What a good entry contains | What a poor entry contains |
|---|---|---|
| Correctness mechanism, availability, recovery, operating effort, access model, reversibility, cost basis, unverified prerequisites, and any the decision needs | | |

### Options

- **Each option in two or three sentences, including "retain the current path" and, where honest, a coexistence option.**

### Matrix

| Criterion | Option A | Option B | Option C |
|---|---|---|---|
| Each cell: a sourced fact (customer measurement, dated documentation, local test) or "unknown: resolve by ..." | | | |

### Which differences matter

- **Prose naming the two or three cells the decision turns on and why; no scores or weights.**

### Unknowns

| Unknown | Option(s) affected | How to resolve | Owner |
|---|---|---|---|

### Recommendation and reversal conditions

- **The recommendation for this decision, the evidence it rests on, and the findings that would reverse it.**

<!-- section:limits -->

An alternatives memo establishes how options compare on stated criteria using the facts you could source at the time; it cannot establish that any option is better in general, and it should never be read as one. Cells filled from documentation reflect the documentation's date and the configuration it describes, not the customer's environment. Local tests support mechanisms, not production behaviour. An unknown cell is a finding, and a memo with none is suspect. Vendor statements belong to the vendor's own current material and must be dated; nothing in this guide is a vendor comparison. Escalate when a criterion the customer cares about cannot be filled for any option, when a contractual, legal or security commitment is being compared as if it were technical, or when the requested recommendation depends on an unknown nobody owns.
