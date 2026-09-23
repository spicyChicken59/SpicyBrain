# Lab L14 — Governance review: access decisions, filters and masks

**Execution class: T (tabletop).** You work through an authored access table
for fictional Cinderline Components on paper or in a text editor, and a small
local evaluator written with the Python 3.12 standard library checks your
answers against keys written by hand. **A locally evaluated policy table is not
Unity Catalog enforcement.** Nothing here connects to Databricks, runs a
`GRANT`, evaluates a real row filter or authenticates anyone.

## Purpose and outcome

The identity module ends in a threat and access review: a narrow permission
plan and a test matrix with must-fail rows. The Unity Catalog module ends in a
least-privilege design with an escalation packet. This lab is the practice
ground for both. After it you can:

1. decide, for twenty requests, whether a principal may act and which check
   decides: USE CATALOG, USE SCHEMA, the object privilege, ownership, or an
   unknown principal (deny by default);
2. predict the rows and values a row filter and a column mask return to four
   different principals, including an empty result that is not an error;
3. write the narrowest plan that lets a supplier portal read one supplier's
   rows, and prove it narrow with a matrix whose must-fail rows catch a wide
   plan and an administrator shortcut;
4. write an escalation packet that quotes the denial, asks the owner for
   exactly the missing privilege, separates requester, approver and applier,
   and lists negative tests;
5. say what the local check proves and what only the real platform can prove.

## What is executed, and what is not

Executed here: `solutions/evaluator.py`, a simplified model of documented
Unity Catalog privilege rules, applied to the JSON tables in `fixtures/`, and
`run_tests.py`, which compares its results and your answers with the hand keys
in `expected/`.

Not executed, and not claimed: Unity Catalog grants and `SHOW GRANTS` on a real
metastore; row filter and column mask SQL functions evaluated by Databricks;
attribute-based policies; OAuth, workload identity federation or tokens; SCIM
sync; secret scopes; audit log queries. The model's rules are stated in
`DATA.md`, together with where real Unity Catalog is richer (for example the
MANAGE privilege and metastore administrators, which the model leaves out).

## Prerequisites

The Unity Catalog module (three-part names, USE CATALOG, USE SCHEMA and
SELECT) and the identity module (groups, service principals, run-as identities,
row filters and column masks). Reading JSON is enough; no Python needs to be
written.

## Files

| Path | What it holds |
|---|---|
| `fixtures/` | the directory, securables, grants, filter and mask policies, stored rows, requests, the plan matrix, the escalation case, two deliberately broad plans and one altered input |
| `expected/` | keys written by hand from the rules in `DATA.md` |
| `starters/` | your answer files, with deliberate gaps |
| `solutions/` | the evaluator and one complete set of reference answers |
| `TASKS.md`, `SOLUTIONS.md`, `DATA.md` | the tasks, the explained solution and the data dictionary |

## Setup and run

Python 3.12 with the standard library is the whole environment; there is
nothing to install (`requirements.txt` says so).

```sh
cd lab-l14-governance-review
python3.12 run_tests.py                                # 23 tests on the reference answers
python3.12 run_tests.py --evidence local-evidence.json # the same, and write evidence JSON
python3.12 run_tests.py --answers starters             # judge your own answers after editing starters/
python3.12 solutions/evaluator.py                      # print the evaluator's twenty decisions
```

Work each task on paper first, then fill the matching file in `starters/` and
run `--answers starters`. A failing answer is printed with the expected and the
given value side by side. Running the evaluator before answering removes the
point of the exercise.

## Cleanup

The runner writes nothing except the evidence file you name, and it does not
create `__pycache__`. Delete `local-evidence.json` if you wrote one.

## Limits

The model is a schematic of the documented privilege rules, not a copy of
Unity Catalog: ownership here covers only the owned securable, only owners may
grant, service principals are named by display name rather than application
ID, and nested groups are expanded for filters and masks as well as grants,
which you must test on the real platform before relying on it. The review
rules that refuse wide plans are this course's guidance, not a platform rule.
Passing every test proves the answers match the keys; it proves nothing about
a workspace.
