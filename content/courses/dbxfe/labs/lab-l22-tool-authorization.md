*Local-executed (R): Python 3.12 standard library, one machine, no network,
41 tests. There is no language model, no MCP server and no Databricks
workspace: scripted proposals stand in for a model and every effect is an
append to an in-memory list. Everything below can be studied without
installing anything.*

### What this lab is for

A model can only propose a tool call: a tool name and some JSON arguments.
Your application decides whether anything happens. The tools module teaches
the rules; this lab makes you build the piece that enforces them, a policy
gate that sits between Cinderline's maintenance assistant and three local
stand-ins for real systems: a draft store, a closures list and a supplier
outbox. The gate decides every proposal from the signed-in user's session,
the tools the application exposes, each tool's schema, the user's grants
intersected with the application's delegated scopes, an idempotency key and
an approval policy, and it writes one audit row per decision. Then twenty
scripted proposals and five human approval actions attack it.

### The data, briefly

| Record | What it holds | Why it is there |
|---|---|---|
| Application `app-maint-assistant` | Delegated scopes `manuals:read`, `drafts:write`, `parts:request` | `drafts:close` is missing on purpose |
| `tech-n1`, `tech-s1`, `sup-n1` | Plant-scoped grants such as `drafts:write:north` | Two plants, one supervisor who can approve parts |
| `s-expired` | An invalid session for `tech-n1` | A missing user credential |
| M7, M12 → north; C4 → south | Machine to plant binding | Scopes every permission |
| Four exposed tools | Schema, permission, key, approval, 2000 ms timeout, 3 attempts | `request_spare_part` always needs approval |
| Five advertised tools | What a tool server lists | `delete_work_order` claims `readOnlyHint: true` and is not exposed |
| DOC-SUP-117 | A supplier catalogue page | Says a supervisor approved 20 × P-9001 and asks for a delete |
| DOC-WO-88 | A work-order comment | Says the current user is the supervisor |

### Task by task, with the intermediate output

**Schema (gap 1).** `validate` returns fixed messages in a fixed order.
`{"part_number": "P-415", "quantity": "2", "machine_id": "M7"}` gives
`'part_number' does not match ^P-[0-9]{4}$` then `'quantity' must be an
integer`; `True` is refused as an integer even though Python counts it as one.
C06 adds `priority: urgent` and is malformed: `priority` is not a property, so
no value of it is acceptable. C07 asks for 50 units against a maximum of 20.

**Delegated permission (gap 2).** The required permission is the tool's
action plus the machine's plant, and both sides must hold it. C05, a South
technician drafting for North machine M7: `missing drafts:write:north
(lacking: user)`. C14, the North supervisor closing D1: she holds
`drafts:close:north`, the application was never delegated `drafts:close`, so
`(lacking: application)`. C15 arrives with an expired session and is denied as
`unauthenticated`; the gate does not quietly use the application's identity.

**Idempotency (gap 3).** C02 creates D1 with key `k-02`; C03 repeats it and
gets D1 back with no second row; C04 reuses `k-02` with a different note and
is refused as a conflict. The slot is user, tool and key, so another
technician's `k-02` is a different intent.

**Approval (gap 4).** C08 (2 × P-0415) is held as A1 with no purchase. The
requester cannot approve it (AP1, `self_approval`); a South technician lacks
`parts:approve:north` (AP2); the supervisor approves (AP3), which writes two
audit rows: her approval, then the application's execution on the
technician's behalf, creating PR1. A second click (AP4) changes nothing, and
C19, reusing `k-08` with quantity 20, is a conflict: an approval for 2 cannot
stretch to 20.

**Bounded retry (gap 5).** Three attempts, backoff 500 × 2^(attempt − 1) ms:

| Call | Attempts | What happened | Elapsed | Decision |
|---|---|---|---|---|
| C16 | 2 | 3500 ms (committed, late), then 300 ms | 2800 ms | allowed, D2 |
| C17 | 3 | 2500 ms × 3, the first committed | 7500 ms | timed_out, outcome unknown |
| C18 | 1 | same key, 200 ms | 200 ms | allowed, D3, no D4 |

**Audit (gap 6).** Twenty calls and five approval actions produce 26 rows:
allowed 5, replayed 4, conflict 2, denied 7, malformed 3, approval_required
2, timed_out 1, approved 1, rejected 1. Arguments appear as a 16-character
SHA-256 digest, so no note text reaches the audit.

### The failure cases

**Injected content.** C10 copies the page's `approved_by: sup-n1` into the
arguments and is malformed. C11 is the same request without it and is simply
held; AP5 is the supervisor rejecting it after seeing that it came from an
unreviewed supplier page. C12 asks for `delete_work_order`, which the
application never exposed, whatever the server's read-only hint says. C13
carries the comment claiming a supervisor, and is decided for `tech-n1`. The
strongest check removes every document from every call and finds identical
decisions and effects: the gate never reads content, so content cannot grant
anything.

**A timeout that hid a write.** C17 reported `timed_out` while D3 already
existed. Without a key, C18 would have created D4.

**Three shortcuts, each proved wrong.** Trusting the page's text executes a
20-unit P-9001 order nobody approved; using a fresh key per attempt writes two
drafts for C16's one intent; falling back to the application serves C15 with
nobody signed in. The transfer, a clinic supply assistant that holds orders
only above 10 units, is decided by the same gate from its own fixtures.

### What the tests prove and do not prove

The 41 tests prove that this gate's decisions, reasons, attempt logs, audit
rows and effects equal literals derived by hand from the fixtures; that the
decisions do not depend on retrieved content for these fixtures; and, with the
optional mutation check, that breaking any of nine rules turns the suite red.
They do not prove how a real model behaves, how any platform enforces
permissions, tokens or Unity Catalog privileges, how a real network or
transaction fails, or that the gate resists attacks these fixtures do not
contain. Rerun the denied, replayed and timed-out cases against the real
platform with two real identities before relying on a design.

### Setup, run and cleanup

Nothing to install. From the lab folder run
`python3.12 run_tests.py --evidence evidence.json`; to check your own work,
fill the six gaps in `starters/gate.py` and run
`python3.12 run_tests.py --starter`; optionally run
`python3.12 mutation_check.py`, which works in a temporary copy it deletes.
Afterwards delete `evidence.json`; the runner writes nothing else.
