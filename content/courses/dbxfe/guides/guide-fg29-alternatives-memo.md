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

Deeper: the retained lessons [Compare options honestly](#/lesson/dbxfe-m11-l01) and [Defend tradeoffs and alternatives](#/lesson/dbxfe-m08-l02), the module [Competition and business value](#/module/dbxfe-m11), and [Architecture and migration](#/module/dbxfe-m08) for the decision not to migrate yet.

<!-- section:example -->

**Fictional worked example: how Cinderline should produce the plant-one morning defect rate.** Written 26 February 2026, before the pilot. Decision: which path the pilot should test, for a three-person data team without continuous support, weekly corrections, a daily decision at 08:00 and a source path security has not reviewed.

### Options

- **A. Improve the current path.** Keep the nightly procedure; remove the duplicates a package retry leaves, apply the plant-time boundary and add a revision check to the CSV import.
- **B. New scheduled path on the platform.** One plant; retained raw deliveries, explicit resolution and an owned metric, read by the existing report.
- **C. Coexistence for a bounded period.** A's fixed report and B in parallel, A served until reconciliation passes.

### Criteria, good and poor

Agreed with the sponsor first. Good: a measurement on the customer's data, a dated document or a dated local test, sourced. Poor: a design property or an estimate presented as a result. Correctness: shown on real corrections, not asserted; availability: a measured finish time, not a schedule; recovery: a timed reversal, not a described one; effort: logged hours, not an impression; access: reviewed identities, not assumed grants; reversibility: a rehearsed way back, not the word "reversible"; cost: a labelled basis, not a total; prerequisites: each with an owner.

### Matrix

| Criterion | A. Improve current | B. New scheduled path | C. Coexistence |
|---|---|---|---|
| Correctness mechanism | Fixes to three known defects; no retained raw history; corrections ordered by file arrival (DBA, 25 Feb) | Retained raw, revision rule, quarantine; shown only locally on synthetic fixtures (demo log, 19 Feb) | Both, compared daily |
| Availability to 08:00 | Unknown: 09:15 to 11:40 is workbook time, not procedure time; baseline week measures it (DBA) | Unknown: no platform run yet; measured from pilot day 1 (data lead) | As A until cutover |
| Recovery | Rerun the procedure; no replay evidence or snapshot identity (DBA, 25 Feb) | Replay shown locally (demo log, 19 Feb); platform recovery unrehearsed | Old path is the fallback |
| Operating effort | Unknown: fixes not yet sized (DBA) | Unknown: data lead estimates under an hour a day (25 Feb) | Unknown: A plus B plus a daily comparison |
| Access model | Existing ERP grants; no new review (security lead, 24 Feb) | New identities and a source path review; region unagreed (security lead, 24 Feb) | Both |
| Reversibility | Each fix changes the numbers served; revert by redeploying the prior procedure; the boundary fix restates history and needs the quality lead's approval | Read path; the old report keeps running, so reverting is repointing a link (design, unrehearsed) | Built for reversal; unrehearsed |
| Cost basis | Unknown increment; DBA time not costed | Hypothetical model only (sponsor's figures) | A plus B plus comparison effort |
| Unverified prerequisites | None new | Source version, CDC permission, security review, operator backup (charter draft, 24 Feb) | As B |

### Which differences matter here

Two cells decide this memo. Nobody has measured when A's procedure finishes; if by 07:00, with the workbook the delay, A may meet the 08:00 decision at almost no cost. B's correctness evidence is local and synthetic: stronger in mechanism, weaker in evidence than A's, and the memo says so rather than treating a design property as a result.

### Unknowns and how to resolve them

Procedure finish time (DBA, a week of timestamps); the size of A's fixes, and whether ERP grants permit the CSV check (DBA); B's availability and effort (data lead, in the pilot); connectivity for the customer's topology (integration specialist, current documentation).

### Recommendation, and what reverses it

Test C as the charter proposes: fix A's three defects regardless of the pilot; run B for one plant beside it; serve A until reconciliation passes. This reverses toward A alone if the procedure finishes in time for 08:00 and the DBA can sustain it, and toward stopping B if security approves no path within the pilot window. No option is called better in general, only for this decision, team and set of unknowns.

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
