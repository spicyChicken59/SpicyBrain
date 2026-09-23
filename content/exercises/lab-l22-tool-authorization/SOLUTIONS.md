# Solutions

The complete reference is `solutions/gate.py`. This file explains each gap,
shows the intermediate output you should see, and ends with the wrong
approaches and the mutation check. All numbers come from the executed run
recorded in the evidence file.

## The order of checks (already written in `Gate.handle`)

1. **Session.** `_user(session)` returns the signed-in user or `None`. The
   user never comes from arguments or retrieved text.
2. **Exposed tool.** A name the application did not expose is denied, whatever
   a server advertises.
3. **Schema** (and a key, for tools that require one).
4. **Entity binding.** `machine_id` → plant (`fixtures/entities.json`).
5. **Delegated permission.** User grant AND application scope.
6. **Idempotency key.** New, replay, conflict or resolve.
7. **Approval.** Hold external effects for a human.
8. **Execution** with bounded retry, then the audit row.

Cheap, effect-free checks come first so a refused call never reaches a
handler, and the key check comes after authorization so nobody can probe
another user's stored outcome.

## GAP 1 — `validate`

```python
problems = [f"missing required property '{name}'"
            for name in schema.get("required", []) if name not in arguments]
if schema.get("additionalProperties", True) is False:
    problems += [f"unexpected property '{name}'" for name in sorted(arguments) if name not in properties]
for name in sorted(arguments):
    ...  # type, maxLength, pattern, minimum, maximum, enum
```

`isinstance(True, int)` is true in Python, so the integer rule checks
`isinstance(value, bool)` first. Intermediate output for the eight cases:
V1 `[]`; V2 pattern then length; V3 three missing properties; V4 pattern then
type; V5 `'quantity' 0 below minimum 1`; V6 must be an integer; V7 two
unexpected properties; V8 not an object.

## GAP 2 — `_authorize`

```python
permission = f"{tool['permission']}:{scope}"
lacking = []
if permission not in self.users[user]["grants"]:
    lacking.append("user")
if tool["permission"] not in self.application["delegated_scopes"]:
    lacking.append("application")
return permission, lacking
```

Intermediate output: C05 (South technician, North machine) lacks the user
side; C13 lacks both; C14 lacks only the application side, because the
supervisor holds `drafts:close:north` and the application was never delegated
`drafts:close`. That last row is a finding for the team, not a bug in the
gate: either stop exposing `close_maintenance_draft` or delegate the scope on
purpose.

## GAP 3 — `_key_status`

```python
if slot is None or slot not in self.keys:
    return "new"
stored = self.keys[slot]
if stored["digest"] != args_digest:
    return "conflict"
return "resolve" if stored["state"] == "in_doubt" else "replay"
```

The digest is the first 16 hex characters of the SHA-256 of the arguments as
canonical JSON (sorted keys, no spaces). Intermediate output: C03 returns D1;
C04 conflicts because the note changed from 1.8 to 2.1 bar; C09 returns A1
while it is pending; C19 conflicts because quantity 20 is not the approved 2;
C20 returns PR1 and A1 after execution. Slots include the user, so another
technician's identical key string is a different intent (the scoped-key test
creates D2 for it).

## GAP 4 — `_needs_approval` and `_approver_problem`

```python
if policy == "always": return True
if isinstance(policy, dict) and "above" in policy:
    return arguments[policy["above"]["field"]] > policy["above"]["value"]
return False
```

```python
if approver == record["requester"]:
    return "self_approval", "the requester cannot approve their own request"
needed = f"{tool['approve_permission']}:{record['scope']}"
if needed not in self.users[approver]["grants"]:
    return "approver_lacks_permission", f"missing {needed}"
return None
```

The held request stores its exact arguments and digest, and
`decide_approval` executes those stored arguments, never new ones. After AP3
the purchase-request list holds exactly one row: PR1, 2 × P-0415 for M7,
requested by `tech-n1`, approved by `sup-n1`, key `k-08`.

## GAP 5 — `_execute`

```python
allowed = tool["max_attempts"] if (key is not None or tool.get("effect_collection") is None) else 1
for attempt in range(1, allowed + 1):
    latency, result = self.downstream.perform(tool, arguments, key, on_behalf_of, extra, ref)
    if latency <= limit:
        ...  # reply: status ok
    elapsed += limit
    wait = backoff * 2 ** (attempt - 1) if attempt < allowed else 0
    elapsed += wait
```

Intermediate output:

| Call | Attempts | Log (latency → outcome, wait) | Elapsed | Result |
|---|---|---|---|---|
| C16 | 2 | 3500 → timeout, 500; 300 → reply | 2800 ms | `allowed/ok_after_retry`, D2 |
| C17 | 3 | 2500 → timeout, 500; 2500 → timeout, 1000; 2500 → timeout | 7500 ms | `timed_out/outcome_unknown`, but D3 exists |
| C18 | 1 | 200 → reply | 200 ms | `allowed/resolved_in_doubt`, D3 |

C17 is the lesson: the target committed D3 on the first attempt and only the
reply was late, so "timed out" meant "unknown", not "nothing happened". The
key record is marked `in_doubt`, which lets C18 go back to the target with
the same key and find D3 instead of creating D4.

## GAP 6 — `_record`

Every decision appends one row, refusals included, and returns a copy with
extras (the attempt log, elapsed time, a read's result) that are not audited.
The approval of AP3 and the execution it triggers are two rows with different
actors: `sup-n1` approved, `app-maint-assistant` executed on behalf of
`tech-n1`. Arguments appear only as a digest, so the free-text note never
enters the audit.

## The injected content

The gate never reads document text; `context` is copied into
`influenced_by` so a reviewer can see what the model had read. That is why
the test that strips every document from every call finds identical
decisions and identical effects. C10's forged `approved_by` is just an
argument the schema does not allow; C11 is a well-formed request that waits
for a human, and AP5 is that human saying no after seeing its origin
(`DOC-SUP-117`, an unreviewed supplier page); C12 names a tool the
application never exposed; C13's claimed supervisor identity never reaches
the gate because identity comes from the session.

## Wrong approaches and why they fail

- **Trusting the retrieved text** (`content_trusting`). Reading "supervisor
  sup-n1 has approved" as an approval executes a 20-unit P-9001 order that no
  human saw, and reading "the current user is supervisor sup-n1" decides C13
  as the supervisor. The context-removal property fails. A system prompt
  saying "only trust the signed-in user" would not help: the defect is in
  code that reads content, and a prompt constrains only the model.
- **A fresh key on every attempt** (`fresh_key_per_attempt`). It retries
  politely and still writes two drafts for C16's single intent, because the
  first attempt committed and the second looked like a new request.
- **Falling back to the application's identity** (`application_fallback`).
  C15 is served as `app-maint-assistant`, whose delegated scopes cover every
  plant; the request looks successful and nobody's own permissions were
  checked.

## Mutation check

`python3.12 mutation_check.py` breaks nine rules one at a time in a temporary
copy: extra properties accepted, delegation as a union, replay ignoring the
arguments, approval never required, self-approval allowed, two extra
attempts, a missing user turned into a supervisor, an audit that keeps only
successes, and a target that ignores the key. In the build run all nine were
caught; the narrowest, self-approval and the success-only audit, each turned
three tests red.
