*Tabletop (T). Worked on paper or in a text editor; a small evaluator written
with the Python 3.12 standard library checks the answers against keys written
by hand. A locally evaluated policy table is not Unity Catalog enforcement:
nothing here connects to Databricks, runs a GRANT or evaluates a real row
filter.*

### What this lab is for

The identity module ends in a threat and access review, and the Unity Catalog
module ends in a least-privilege design with an escalation packet. Both need
the same skill: reading an access table and predicting, before anyone runs a
query, who may do what, which check decides, and what a filtered query
returns. This lab gives you a small, fully authored table for fictional
Cinderline Components and four tasks on it. Every answer is checkable, and two
deliberately broad plans show why must-fail tests matter more than must-succeed
ones.

### The authored world in one table

| Principal | Member of (after nesting) | Grants reaching it |
|---|---|---|
| Maya (user) | plant-eu-analysts, quality-analysts | USE CATALOG quality; USE SCHEMA quality.accepted; SELECT on inspections |
| Jon (user) | plant-us-analysts, quality-analysts | the same three |
| Ravi (user) | quality-leads | USE CATALOG quality; USE SCHEMA and SELECT on the accepted schema; USE SCHEMA quality.shared; SELECT on supplier_rejections |
| Lena (user) | data-engineers | USE CATALOG quality; owns schema quality.raw and its table and volume |
| Tess (user) | quality-platform-owners | owns catalog quality and the accepted and shared schemas and tables |
| sp-nightly-ingest | ingest-jobs | USE CATALOG quality; USE SCHEMA quality.raw; SELECT and MODIFY on deliveries |
| sp-supplier-portal | supplier-portal | nothing yet |

Two tables carry policies. `inspections` has a row filter that shows every row
to quality-leads and only plants EU-1 and EU-2 to plant-eu-analysts, and a mask
that replaces `inspector_email` with `[masked]` for everyone but quality-leads.
`supplier_rejections` has a filter that shows supplier S-17's rows to the
supplier-portal group and a similar mask.

The model's rules are short. A read or write needs USE CATALOG, then USE SCHEMA
(on the schema or the catalog), then the object privilege (on the object, the
schema or the catalog); the first missing one names the denial. Ownership
counts as every privilege on the owned securable only. Only owners may grant.
There are no deny entries: anything not granted is denied.

### Task 1 — twenty decisions

You decide twenty requests. Three illustrate the pattern. Maya's SELECT on
`inspections` is allowed: all three privileges reach her through nested
groups. Maya's SELECT on `rework_costs` is denied with `missing-select`: both
usage checks pass, but analysts hold SELECT only on `inspections`. The nightly
service principal's SELECT on `inspections` is denied with
`missing-use-schema`: its group has usage only on `quality.raw`, so the
question of SELECT never arises. The final count is eight allowed and twelve
denied, including an unknown principal (`priya@cinderline.example`) denied by
default and a GRANT request by Jon denied with `not-owner`, because holding
SELECT is not the right to grant it.

### Task 2 — one statement, four answers

The same `SELECT *` on `inspections` returns:

| Principal | Result |
|---|---|
| Maya | 3 rows (I-101, I-103, I-105), every email `[masked]` |
| Jon | allowed, 0 rows, no error |
| Ravi | all 6 rows as stored |
| Omar | denied at the catalog check; the filter never runs |

Jon's empty result is the lesson: his grants are complete, and no clause of the
filter admits his group. Checking grants would find nothing wrong.

### Task 3 — the portal's narrow plan

The portal must read supplier S-17's rejections with emails masked, and nothing
else. The narrow plan is three grants to the existing supplier-portal group:
USE CATALOG on `quality`, USE SCHEMA on `quality.shared`, SELECT on
`supplier_rejections`. Its matrix:

| Row | Request | Result |
|---|---|---|
| P1 | portal SELECT supplier_rejections | allow |
| P2 | portal SELECT inspections | deny, missing-use-schema |
| P3 | portal MODIFY supplier_rejections | deny, missing-modify |
| P4 | portal SELECT raw deliveries | deny, missing-use-schema |
| P5 | portal GRANT on supplier_rejections | deny, not-owner |
| P6 | Maya SELECT supplier_rejections | deny, missing-use-schema |
| P7 | portal rows | R-201 and R-203, emails masked |

### The failure cases

A wide plan granting USE SCHEMA and SELECT on the whole catalog passes P1 and
P7, so a demo looks perfect, and fails P2 and P4; the review rules report
`data-privilege-above-object` and `use-schema-on-catalog`. An administrator
shortcut that adds the portal to quality-platform-owners fails P2, P3 and P5,
because ownership lets it read, write and grant, and reports
`owner-group-membership`. The tests assert these exact failing rows and rule
names, so a broad plan cannot pass by accident.

### Task 4 — the escalation packet

Jon needs read-only access to `rework_costs` for two weeks. The packet quotes
the denial (`missing-select`), names quality-platform-owners as owner and Tess,
a member, as approver, keeps Jon as requester and Sam as applier, proposes a
new group `rework-reviewers` holding SELECT on that one table until 2026-10-07,
and lists negative tests that stay denied afterwards. The tests apply the
proposal and re-run the request and every negative test.

### The altered input

A transfer file moves Maya to finance and adds a filter clause for US plants,
editing no grant. Maya is then denied at the catalog check, and Jon's query
returns I-102, I-104 and I-106 with masked emails. Access moved because
membership and policy moved.

### What the tests prove, and what they do not

The 23 tests prove that the evaluator reproduces keys written by hand from the
stated rules, that the reference answers match them, that the starters are
incomplete, that two broad plans fail for the named reasons, and that a
wrong answer is reported with both values. They prove nothing about a
Databricks workspace: real Unity Catalog adds the MANAGE privilege and
metastore administrators, names service principals by application ID, and
evaluates filter functions whose group checks must be tested there with the
real principals.

### Setup and cleanup

With Python 3.12 and nothing else: `python3.12 run_tests.py` checks the
reference answers, `python3.12 run_tests.py --answers starters` checks yours.
The runner writes only an evidence file you name and creates no cache
directory; delete that file when you are done.
