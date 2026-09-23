# Tasks — Lab L14 governance review

Work each task on paper with `fixtures/` and the rules in `DATA.md`, then
record your answers in the matching file in `starters/` and run
`python3.12 run_tests.py --answers starters`. Reason codes:

| Code | Meaning |
|---|---|
| `granted` | allowed; the object privilege comes from a grant |
| `owner` | allowed; it comes from ownership |
| `missing-use-catalog` | denied at the catalog usage check |
| `missing-use-schema` | denied at the schema usage check |
| `missing-select`, `missing-modify`, `missing-read-volume` | denied at the object privilege |
| `not-owner` | a GRANT request by someone who does not own the securable |
| `unknown-principal` | the principal is not in the directory |

## Task 1 — twenty decisions (`starters/decisions.json`)

For each request in `fixtures/requests.json`, write `decision` (`allow` or
`deny`) and `reason`. R01 is done as an example. Expected behaviour: every
entry answered; a wrong entry is reported with the expected and the given
value. Before you start, predict how many of the twenty are allowed.

## Task 2 — what the query returns (`starters/visible.json`)

For each query in `fixtures/row_requests.json`, write the decision and reason
of the SELECT, and for an allowed one the rows in stored order with masked
values written `[masked]`. V4 is done as an example. Expected behaviour: an
allowed query can return an empty list; a denied one has no `rows`.

## Task 3 — the supplier portal's plan (`starters/plan.json`)

The portal runs as `sp-supplier-portal`, already a member of `supplier-portal`.
It must read supplier S-17's rows of `quality.shared.supplier_rejections`
with inspector emails masked, and nothing else. Add `grants` (and, only if you
need them, `newGroups` and `memberships`). Expected behaviour: every row of
`fixtures/plan_matrix.json` gives the key's decision and rows, and the review
rules report nothing: no MANAGE or ALL PRIVILEGES, grants to groups only, data
privileges on the object not on a schema or catalog, USE SCHEMA on a schema,
and no new member in a group that owns anything.

## Task 4 — the escalation packet (`starters/escalation.json`)

Jon needs read-only access to `quality.accepted.rework_costs` for two weeks
(`fixtures/escalation_case.json`). Fill the packet: who requests, the exact
denial the evaluator gives, the owning group, an approver who belongs to it,
an applier, a proposal (a new group, its member, one grant and an `expires`
date), at least two negative tests with `expected: deny`, and a one-line
justification. Expected behaviour: requester, approver and applier are three
different people; the proposal grants only the privilege the denial names, on
only that table; after the proposal Jon's request is allowed and every
negative test is still denied.

## Stretch, on paper only

Apply `fixtures/transfer/changes.json` in your head: which of your Task 1 and
Task 2 answers change, and why did no grant have to be edited?
