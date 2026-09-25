# Solutions — Lab L14 governance review

The reference answers are the files in `solutions/`; this page explains them.
Everything below is a local evaluation of an authored table: a locally
evaluated policy table is not Unity Catalog enforcement.

## Task 1 — eight allowed, twelve denied

| Request | Principal and action | Decision | Why |
|---|---|---|---|
| R01, R02 | Maya, Jon SELECT inspections | allow, granted | all three privileges reach them through quality-analysts |
| R03 | Maya SELECT rework_costs | deny, missing-select | usage passes; SELECT is only on inspections |
| R04 | Ravi SELECT rework_costs | allow, granted | schema-level SELECT reaches every table |
| R05 | Omar SELECT inspections | deny, missing-use-catalog | nothing on `quality` |
| R06 | Maya MODIFY inspections | deny, missing-modify | read-only analysts |
| R07 | sp-nightly-ingest MODIFY deliveries | allow, granted | ingest-jobs holds all three |
| R08 | sp-nightly-ingest SELECT inspections | deny, missing-use-schema | usage only on `quality.raw` |
| R09 | Lena SELECT deliveries | allow, owner | data-engineers owns schema and table |
| R10 | Lena SELECT rework_costs | deny, missing-use-schema | ownership of `raw` does not reach `accepted` |
| R11 | Maya READ VOLUME photos | deny, missing-use-schema | no usage on `quality.raw` |
| R12 | sp-nightly-ingest READ VOLUME photos | deny, missing-read-volume | usage passes, no READ VOLUME |
| R13 | Lena READ VOLUME photos | allow, owner | owns the volume |
| R14 | Jon GRANT on inspections | deny, not-owner | holding SELECT is not the right to grant it |
| R15 | Tess GRANT on inspections | allow, owner | quality-platform-owners owns it |
| R16 | Ravi SELECT finance table | deny, missing-use-catalog | nothing on `finance` |
| R17 | sp-supplier-portal SELECT rejections | deny, missing-use-catalog | no grants yet |
| R18 | Priya SELECT inspections | deny, unknown-principal | not in the directory |
| R19 | Maya SELECT rejections | deny, missing-use-schema | no usage on `quality.shared` |
| R20 | Ravi SELECT rejections | allow, granted | all three held |

The order of the checks matters for the reason, not for the decision: R08 and
R11 are denied before anyone asks about SELECT or READ VOLUME.

## Task 2 — same statement, different answers

V1 Maya: I-101, I-103, I-105 with `[masked]` emails. V2 Jon: allowed and zero
rows, because no filter clause admits plant-us-analysts; checking grants would
find nothing wrong. V3 Ravi: all six rows as stored. V4 Omar: denied at the
catalog, so the filter never runs. V5 Ravi on rejections: all five rows.

## Task 3 — the narrow plan

```json
{"newGroups": [], "memberships": [],
 "grants": [
  {"principal": "supplier-portal", "privilege": "USE CATALOG", "securable": "quality"},
  {"principal": "supplier-portal", "privilege": "USE SCHEMA", "securable": "quality.shared"},
  {"principal": "supplier-portal", "privilege": "SELECT", "securable": "quality.shared.supplier_rejections"}]}
```

The matrix after applying it: P1 allow; P2 and P4 missing-use-schema; P3
missing-modify; P5 not-owner; P6 unchanged; P7 R-201 and R-203 with masked
emails. The row filter, not the grant, limits the portal to S-17.

**A wrong approach and why it fails.** The wide plan in
`fixtures/negative/wide_plan.json` grants USE SCHEMA and SELECT on the whole
catalog. It passes P1 and P7, the rows the requester cares about, so a demo
looks perfect; it fails P2 and P4 because the portal can now read inspections
and raw deliveries, and the review rules flag `data-privilege-above-object` and
`use-schema-on-catalog`. The administrator shortcut in `admin_plan.json` adds
the portal to quality-platform-owners: it fails P2, P3 and P5 because
ownership allows reading, writing and granting, and it trips
`owner-group-membership`. Only the must-fail rows expose either mistake.

## Task 4 — the escalation packet

The reference packet quotes the denial (deny, missing-select), names
quality-platform-owners as the owner and Tess, a member, as approver; Jon
requests and Sam, a platform administrator, applies. The proposal creates the
group `rework-reviewers`, adds Jon, grants it SELECT on `rework_costs` only and
expires on 2026-10-07. Its negative tests stay denied after the change: Jon's
MODIFY on the table, Maya's SELECT on it, Jon's SELECT on the finance table.
Granting Jon SELECT directly would work but breaks the grant-to-groups rule,
and asking for SELECT on the schema would pass the request and fail the
review.

## What the tests prove, and what they do not

They prove that your answers match keys written by hand from `DATA.md`, that
the evaluator reproduces those keys, that the starters are incomplete, that
two broad plans fail for the named reasons, and that a membership move changes
access with no grant edited. They do not prove anything about a Databricks
workspace: grants, filters, masks and identities must be tested there with the
real principals.
