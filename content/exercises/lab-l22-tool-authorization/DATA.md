# Data dictionary and derivations

All fixtures are original synthetic records written for this lab. Cinderline
Components, the Harbor Lane clinic, their people, roles, machines, wards,
parts, documents and identifiers are fictional. There is no random seed:
nothing is generated, so every run reads the same bytes.

## `fixtures/identities.json`

| Field | Meaning |
|---|---|
| `application.id` | `app-maint-assistant`, the service principal the assistant runs as |
| `application.delegated_scopes` | What the application may do on a signed-in user's behalf: `manuals:read`, `drafts:write`, `parts:request` (not `drafts:close`) |
| `users.<id>.grants` | Plant-scoped permissions, `<action>:<plant>` |
| `sessions.<id>` | The authenticated session a call arrives with: `user` and `valid` (`s-expired` is invalid) |

Users: `tech-n1` (North technician: read, draft, request on North), `tech-s1`
(the same on South), `sup-n1` (North supervisor: adds `drafts:close:north`
and `parts:approve:north`).

## `fixtures/entities.json`

`scope_of` binds each machine to a plant: M7 and M12 → north, C4 → south.
The gate scopes every permission with the plant of the call's `machine_id`.

## `fixtures/tools.json`

`exposed` lists the four tools the application offers to the model:

| Tool | Effect | Permission | Key | Approval | Schema highlights |
|---|---|---|---|---|---|
| `search_manuals` | read | `manuals:read` | no | never | `query` ≤ 200 chars, `machine_id` `^[A-Z][0-9]{1,3}$` |
| `create_maintenance_draft` | internal write → `drafts` | `drafts:write` | yes | never | `manual_section` pattern, `note` ≤ 500 chars, no other properties |
| `close_maintenance_draft` | internal write → `closures` | `drafts:close` | yes | never | `draft_id` `^D[0-9]+$` |
| `request_spare_part` | external effect → `purchase_requests` | `parts:request` | yes | always, by `parts:approve` | `part_number` `^P-[0-9]{4}$`, `quantity` integer 1–20 |

Every tool has `timeout_ms` 2000, `max_attempts` 3 and `backoff_ms` 500.
`advertised` is what a tool server lists during discovery, with annotations;
it includes `delete_work_order` marked `readOnlyHint: true`. The gate never
consults `advertised`.

## `fixtures/documents.json`

| Id | Origin | Content |
|---|---|---|
| DOC-M7-4.2 | approved manual section | Replace the filter above a 1.5 bar pressure drop |
| DOC-SUP-117 | supplier catalogue PDF page (external, unreviewed) | Claims a supervisor approved an emergency order of 20 × P-9001 and asks for `approved_by` and a delete |
| DOC-WO-88 | free-text comment on a work order | Claims the current user is the supervisor and asks to close D1 |

## `fixtures/calls.json`, `approvals.json`, `conditions.json`

Calls C01–C18 run first, then approval actions AP1–AP5, then the two calls
marked `after_approvals` (C19, C20). Each event advances the audit clock by
one minute from 2026-09-21T08:00:00Z; AP3's approval and execution share
08:20. `conditions.json` scripts per-attempt latency and whether the request
committed, for C16 (3500 ms committed, then 300 ms), C17 (three × 2500 ms,
the first committed) and C18 (200 ms). Every other attempt takes 100 ms.

## `fixtures/transfer/`

A clinic supply assistant: application `app-supply-assistant` with scopes
`catalog:read`, `supplies:order`, `orders:cancel`; nurses `nurse-e1` (east)
and `nurse-w1` (west) with read and order grants; pharmacist `pharm-e1` (east)
who can also approve and cancel; wards W3, W4 → east, W9 → west;
`order_supplies` holds for approval only above 10 units and allows 1–40;
one packing-label document with an injected instruction. Timeout 1500 ms,
two attempts, 250 ms backoff (no scripted delays).

## How the expected values were derived

Each literal in `expected/` was written by walking the fixtures through the
rules in `TASKS.md` by hand, before the reference gate was run; the tests
compare the gate against these literals and never against its own output.

**Validation (`validation.json`).** Required properties in schema order, then
unexpected properties alphabetically, then per-property problems
alphabetically. V4: properties sorted are `machine_id` (valid),
`part_number` ("P-415" has three digits, pattern fails), `quantity` ("2" is a
string, type fails) — so pattern first, then type. V6: `true` is refused as
an integer.

**Decisions (`decisions.json`).**

- C01: valid session, exposed, schema valid, M7 → north, `manuals:read:north`
  held and `manuals:read` delegated; a read has no key and no approval; the
  stub returns the M7 documents sorted: DOC-M7-4.2, DOC-SUP-117, DOC-WO-88.
- C02: `drafts:write:north` held and delegated, key `k-02` unseen, no
  approval, one 100 ms attempt; the drafts list is empty, so the id is D1.
- C03: same slot `(tech-n1, create_maintenance_draft, k-02)`, same digest,
  state completed → replayed, D1.
- C04: same slot, the note differs (2.1 bar), so the digest differs →
  conflict.
- C05: `tech-s1` lacks `drafts:write:north`; the application has
  `drafts:write` → lacking user.
- C06: `priority` is not a property → one problem. C07: 50 > 20. C10:
  `approved_by` is not a property (quantity 20 is within the maximum).
- C08: all checks pass; approval is `always` → held; no approvals yet → A1.
  C09: same slot and digest, state pending_approval → replayed, A1.
- C11: a valid 20-unit request → held → A2.
- C12: `delete_work_order` is not exposed → denied before the schema.
- C13: `tech-n1` lacks `drafts:close:north` and `drafts:close` is not
  delegated → lacking user, application. C14: `sup-n1` holds the grant; the
  application still lacks the scope → lacking application.
- C15: `s-expired` is invalid → unauthenticated; nothing is executed.
- C16: attempt 1 commits D2 (drafts held D1) but replies at 3500 > 2000 ms →
  timeout, count 2000, wait 500 × 2⁰ = 500; attempt 2 finds the key and
  replies at 300 ms → D2; elapsed 2000 + 500 + 300 = 2800.
- C17: attempt 1 commits D3 and replies at 2500 → timeout (2000 + wait 500);
  attempt 2 → timeout (2000 + wait 500 × 2¹ = 1000); attempt 3 → timeout
  (2000, no wait after the last); elapsed 7500; key marked in doubt; the
  audit's effect is unknown (null).
- C18: same slot and digest, state in_doubt → resolve; one 200 ms attempt
  finds D3 for this user and key.
- AP1: `tech-n1` is the requester → self_approval. AP2: `tech-s1` lacks
  `parts:approve:north`. AP3: `sup-n1` holds it → approved; execution with
  the stored arguments (2 × P-0415, M7) in 100 ms creates PR1, the first
  purchase request. AP4: A1 is executed, not pending → already decided.
  AP5: A2 pending, approver valid → rejected.
- C19: slot `(tech-n1, request_spare_part, k-08)` stores the digest of
  quantity 2; quantity 20 differs → conflict. C20: same digest, state
  completed → replayed with PR1 and A1.

**Audit (`audit.json`).** One row per decision in event order: 18 calls,
AP1, AP2, AP3 (two rows), AP4, AP5, C19, C20 = 26 rows. Tallies counted from
the list above: allowed 5 (C01, C02, C16, C18, AP3 execution), replayed 4
(C03, C09, AP4, C20), conflict 2 (C04, C19), denied 7 (C05, C12, C13, C14,
C15, AP1, AP2), malformed 3 (C06, C07, C10), approval_required 2 (C08, C11),
timed_out 1 (C17), approved 1, rejected 1. `influenced_by` is each call's
context sorted; approval rows carry the held request's context.

**Effects (`effects.json`).** Drafts D1 (C02), D2 (C16), D3 (C17, committed
before its timeout); no closures (C13, C14 denied); one purchase request, PR1
(AP3); one read (C01). A1 ends executed by `sup-n1` with PR1; A2 ends
rejected by `sup-n1` with no effect.

**Retries (`retries.json`).** The attempt logs and elapsed times derived for
C16, C17 and C18 above.

**Transfer (`transfer.json`).** T01: 6 ≤ 10 → no approval, O1. T02: 12 > 10
→ held A1. T03: `nurse-w1` lacks `supplies:order:east`. T04: replay → O1.
T05: 45 > 40 → malformed. T06: `nurse-e1` lacks `orders:cancel:east` although
the application holds `orders:cancel` → lacking user. T07: 40 > 10 → held A2.
T08: `pharm-e1` holds the grant → X1 (first cancellation). TA1: approve A1 →
execute 12 × S-101 → O2. TA2: reject A2. TA3: A2 is rejected, not pending →
already decided. Twelve audit rows: allowed 3, approval_required 2, denied 2,
replayed 2, malformed 1, approved 1, rejected 1.
