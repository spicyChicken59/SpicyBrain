# Lab L22 — Tool calls behind an application-side policy gate

**Execution class: R (local-executed).** The reference gate and its 41 tests
run on one machine with Python 3.12 and the standard library only
(`requirements.txt` pins nothing because nothing is installed). Nothing calls
a model, nothing contacts a network, and nothing runs on Databricks.

**What this lab is not.** There is no language model: twenty scripted tool
proposals in `fixtures/calls.json` stand in for what a model might emit, which
makes every run identical. There is no MCP server or client, no OAuth token
and no real permission system: sessions, grants and scopes are small JSON
records. Timeouts are simulated with scripted latencies on an event clock, so
nothing waits. Every "effect" (a draft, a closure, a purchase request) is an
append to a Python list inside the process; no message is sent, nothing is
bought and no system changes. The results show that the gate's logic behaves
as specified; they say nothing about any platform's permissions, network or
transactions.

## Purpose

A model can propose a tool call; only your application can execute it. This
lab builds the piece in between: a policy gate that decides every proposal
from the signed-in user's identity, the application's delegated scopes, the
tool's schema, an idempotency key and an approval policy, and writes one audit
row per decision. Then it attacks the gate with the cases that matter:
another plant's machine, an argument the schema forbids, a forged approval
inside a supplier's PDF page, a tool the application never exposed, a missing
user credential, a reply that arrives too late after the write already
committed, and a second click on an approval.

## Outcome

After the lab you can:

- predict the decision and reason for any proposal, in the order the gate
  checks: session, exposed tool, schema, entity binding, delegated
  permission, idempotency key, approval, execution;
- show that delegated permission is an intersection of the user's grants and
  the application's scopes, and that a missing user credential is refused
  rather than replaced by the application's identity;
- show that retrieved text cannot supply identity, approval or a tool, because
  the gate never reads it: every decision is identical with the content
  removed;
- explain why a timeout is an unknown outcome and how one key per intent turns
  a retry, a replay and a later recovery into lookups instead of duplicates;
- specify an approval step and an audit row that a reviewer can rely on.

## Prerequisites

Python you can read (functions, dictionaries, classes), JSON, and the course's
GenAI module on retrieval and tool boundaries. The tools module in the GenAI
track explains every rule used here.

## Files

| Path | What it holds |
|---|---|
| `fixtures/identities.json` | The application's service principal and delegated scopes, three users with plant-scoped grants, four sessions (one expired) |
| `fixtures/entities.json` | Machine to plant binding used to scope every permission |
| `fixtures/tools.json` | Four exposed tools with JSON Schema inputs, permission, key, approval, timeout and retry policy; five tools a server advertises, one with a misleading read-only hint |
| `fixtures/documents.json` | Three retrieved documents with their origin; two contain injected instructions |
| `fixtures/calls.json` | Twenty scripted proposals C01 to C20, each with a session, arguments, a key and the documents in context |
| `fixtures/approvals.json` | Five human approval actions AP1 to AP5 |
| `fixtures/conditions.json` | Scripted latencies for C16 to C18 (the timeout cases) |
| `fixtures/transfer/` | The altered input: a clinic supply assistant with a threshold approval policy |
| `expected/*.json` | Hand-derived literal outputs (derivations in `DATA.md`) |
| `solutions/gate.py` | Reference gate, downstream stub and replay runner |
| `starters/gate.py` | Your starting point: six marked gaps |
| `starters/shortcuts.py` | Three wrong approaches the tests prove wrong |
| `run_tests.py` | The unittest runner and evidence writer |
| `mutation_check.py` | Optional: breaks nine rules one at a time and confirms the tests notice |

## Setup

Nothing to install. Check the interpreter:

```bash
python3.12 --version
```

Only CPython 3.12.3 was run for this package; other recent CPython versions are
expected to behave the same but were not tested.

## Run

From this directory:

```bash
python3.12 run_tests.py --evidence evidence.json   # the reference solution
python3.12 run_tests.py --starter                  # your completed starters/gate.py
python3.12 mutation_check.py                       # optional: nine mutations, all should be caught
```

The runner prints each test and a short summary; `--evidence` also writes a
JSON record with versions, test counts, and SHA-256 hashes of fixtures,
expected files, code and produced outputs.

## Cleanup

`run_tests.py` writes only the evidence file you name, and it disables
bytecode caching so no `__pycache__` appears. `mutation_check.py` works in a
temporary copy that is deleted when each mutation finishes. Delete
`evidence.json` when you are done.

## Limits

- The gate is a teaching reference, not a security library: no rate limits,
  no key expiry, no concurrency control and no persistence across runs.
- A scripted proposal is not a model. A real model may propose calls these
  fixtures never imagined; the injection property (decisions identical
  without content) is tested for these fixtures only.
- Grants, scopes and sessions stand in for a platform's permissions, tokens
  and Unity Catalog privileges. Rerun denial, replay and timeout cases against
  the real platform with real identities before trusting a design.
- Cinderline Components, the clinic, their people, machines, parts, documents
  and identifiers are fictional.
