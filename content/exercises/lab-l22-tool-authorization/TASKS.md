# Tasks

Predict on paper before you run anything. Every value you are checked against
was written by hand from the fixtures and the rules below before the gate was
run (`DATA.md` shows each derivation), so a prediction you can defend is worth
more than a green run. Work in `starters/gate.py`; judge it with
`python3.12 run_tests.py --starter`. The order of checks in `Gate.handle` is
already written: session, exposed tool, schema (plus a key for tools that
need one), entity binding, delegated permission, idempotency key, approval,
execution. Read it first.

## 1. GAP 1 — enforce the schema in code

Implement `validate(schema, arguments)`. It returns `[]` for valid arguments,
otherwise a list of problems in this order: missing required properties (in
the schema's `required` order), unexpected properties when
`additionalProperties` is false (alphabetical), then per-property problems
(alphabetical by property name). Message formats, exactly:

| Problem | Message |
|---|---|
| not an object | `arguments must be a JSON object` |
| missing | `missing required property 'note'` |
| not allowed | `unexpected property 'priority'` |
| wrong type | `'quantity' must be an integer` / `'note' must be a string` |
| too long | `'note' longer than 500 characters` |
| pattern | `'part_number' does not match ^P-[0-9]{4}$` |
| range | `'quantity' 50 above maximum 20` / `'quantity' 0 below minimum 1` |

A boolean is not an integer here, although Python says `True` is an `int`.
Expected behaviour: the eight cases in `expected/validation.json`, for example
`{"part_number": "P-415", "quantity": "2", ...}` gives two problems, pattern
first, then type.

## 2. Predict the first seven decisions

Without running anything, write the decision and reason for C01 to C07 in
`fixtures/calls.json`. Expected behaviour: C01 `allowed/ok` (a read returns
three document ids for M7); C02 `allowed/ok` creating draft D1; C03
`replayed`; C04 `conflict`; C05 `denied/insufficient_scope`; C06 and C07
`malformed/schema_violation`. Explain why C06 is malformed rather than
"discouraged": `priority` is not a property and `additionalProperties` is
false, so there is no value of `priority` the gate would accept.

## 3. GAP 2 — delegated permission is an intersection

Implement `Gate._authorize(user, tool, scope)`. The required permission is
`f"{tool['permission']}:{scope}"`, where the scope is the plant bound to the
call's machine. Return `(permission, lacking)`: `lacking` contains `"user"` if
the user's grants miss the permission, then `"application"` if the
application's `delegated_scopes` miss `tool["permission"]`. Expected
behaviour: C05 `missing drafts:write:north (lacking: user)`; C13
`missing drafts:close:north (lacking: user, application)`; C14 — the North
supervisor holds `drafts:close:north` — `missing drafts:close:north
(lacking: application)`.

## 4. GAP 3 — one intent, one key

Implement `Gate._key_status(slot, args_digest)`. A slot is `(user, tool,
key)`; the gate stores the argument digest and a state for each. Return
`"new"` for no slot or an unseen one, `"conflict"` when the stored digest
differs, `"resolve"` when the stored state is `"in_doubt"`, and `"replay"`
otherwise. Expected behaviour: C03 returns D1 with no second draft; C04 and
C19 are conflicts; C09 replays the pending approval A1; C20 replays the
executed request and returns PR1 and A1.

## 5. GAP 4 — approval binds a named person to exact arguments

Implement `Gate._needs_approval(tool, arguments)`: `"always"` holds, `"never"`
does not, and `{"above": {"field": "quantity", "value": 10}}` holds when that
argument is greater than the value. Implement `Gate._approver_problem`:
self-approval is refused first (`self_approval`), then the approver needs
`f"{tool['approve_permission']}:{record['scope']}"`
(`approver_lacks_permission`, detail `missing parts:approve:north`).
Expected behaviour: C08 and C11 are held as A1 and A2 with no purchase
request; AP1 `self_approval`; AP2 `approver_lacks_permission`; AP3 writes two
rows (the supervisor's `approved`, then the application's
`executed_after_approval` with PR1); AP4 `already_decided`; AP5 rejects A2.

## 6. GAP 5 — bounded retry, same key every time

Implement `Gate._execute(tool, arguments, key, on_behalf_of, extra, ref)`.
Call `self.downstream.perform(...)` up to `tool["max_attempts"]` times (once
only for a write that has no key). A reply whose latency exceeds
`tool["timeout_ms"]` is a timeout: add `timeout_ms` to the elapsed time, then
wait `backoff_ms * 2 ** (attempt - 1)` unless it was the last attempt. Return
`{"status": "ok" or "timed_out", "attempts", "elapsed_ms", "log", "result"}`
where each log entry is `{"attempt", "latency_ms", "outcome": "reply" or
"timeout", "backoff_ms"}`. Expected behaviour (`expected/retries.json`): C16
succeeds on attempt 2 after 2800 ms; C17 times out three times, 7500 ms, and
reports `outcome_unknown` although the target committed D3 on the first
attempt; C18, the same key later, returns D3 in 200 ms with no D4.

## 7. GAP 6 — one audit row per decision

Implement `Gate._record(...)`. Each row carries `seq`, `at`, `event`, `ref`,
`actor`, `on_behalf_of`, `executing_identity`, `tool`, `args_digest`,
`idempotency_key`, `decision`, `reason`, `detail`, `attempts`, `effect_id`,
`approval_id` and `influenced_by`. Append a copy to `self._audit` and return
a copy that also carries the non-audited extras. Refusals are rows too.
Expected behaviour: 26 rows for the 25 events (AP3 writes two); tallies
allowed 5, replayed 4, conflict 2, denied 7, malformed 3, approval_required 2,
timed_out 1, approved 1, rejected 1; no note text appears in any row.

## 8. The injected cases

Read `fixtures/documents.json`. DOC-SUP-117 claims a supervisor approved an
emergency order and asks for `approved_by` and a delete; DOC-WO-88 claims the
current user is a supervisor. Predict C10 to C13. Expected behaviour: C10
`malformed` (`unexpected property 'approved_by'`); C11 held as A2, no
purchase; C12 `denied/tool_not_exposed` even though the server advertises the
tool with `readOnlyHint: true`; C13 decided for `tech-n1`, not the supervisor.
Then explain why removing every document from every call changes no decision
(the test `test_decisions_are_identical_without_retrieved_content`).

## 9. The transfer

Open `fixtures/transfer/`: a clinic supply assistant, wards bound to sites,
and an approval policy that holds only orders above 10 units. Predict T01 to
T08 and TA1 to TA3 before running. Expected behaviour: T01 executes O1 at
once; T02 is held; T03 is denied for another site's ward; T04 replays O1;
T05 is malformed (45 above 40); T06 is denied because the nurse lacks
`orders:cancel:east` although the application holds the scope; T07 is held;
T08 executes cancellation X1; TA1 approves and executes O2; TA2 rejects A2;
TA3 finds A2 already decided.

## 10. Say why the shortcuts fail

Read `starters/shortcuts.py`. For each shortcut, name the property it breaks
and the fixture case that exposes it. Expected behaviour: trusting retrieved
text executes a 20-unit P-9001 order and decides C13 as the supervisor;
a fresh key per attempt creates two drafts for C16's one intent; falling back
to the application serves C15 with nobody signed in.
