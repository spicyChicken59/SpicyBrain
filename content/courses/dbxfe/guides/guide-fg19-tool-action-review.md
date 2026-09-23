<!-- section:action -->

Review one tool at a time. A tool is a promise that a call with certain arguments will have a certain effect under a certain identity, and the review checks every clause of that promise before the model can make the call.

1. **Card the tool.** Name, effect class (read, write, external effect), target system, data touched, who asked for it and for which decision.
2. **Identity.** Which principal executes: the end user by delegation, a service principal, or the application's own identity. Which permissions apply at the target, and which calls must fail for a user who lacks them. Test the failure with a real second identity.
3. **Scope.** Argument constraints: allowlists, ranges, entity binding to the caller's plant or team, row limits, time windows. Constraints belong in the schema and the handler, not in the prompt.
4. **Approvals.** Which effect classes require a human, who that is, how the approval is recorded and how the model's request is kept apart from the human's decision.
5. **Idempotency.** A key per intent, the behaviour on retry, timeout and duplicate delivery, and what the caller sees when the outcome is unknown.
6. **Audit evidence.** Fields logged (actor, key, arguments, result, approval, timestamp), where they live, retention, and which fields are sensitive.
7. **Test matrix.** Run allowed, denied, malformed, replayed and timed-out calls through a local stub and record what happened.

Evidence to collect: the tool card, the test matrix with observed results, the audit rows produced by the tests, and the list of unknowns with owners.

Deeper: [Tools, MCP and action authorization](#/module/dbxfe-tools) for the harness, [Identity, authorization and audit](#/module/dbxfe-identity) for principals and audit events, [Orchestration and recovery](#/module/dbxfe-orchestration) for retries and external effects, and the retained lesson [Choose retrieval or a tool-using agent](#/lesson/dbxfe-m07-l02).

<!-- section:example -->

**Fictional worked example: a "draft work order" tool for Cinderline's manual assistant.** The maintenance lead has said that work-order changes are not approved. A technician still wants a way to capture "this machine needs attention" without leaving the assistant. The proposal is a tool that writes a *draft* to a staging table that a supervisor reviews; nothing reaches the ERP.

### Tool card

- **Name:** `create_maintenance_draft`. **Effect class:** write, internal only. **Target:** staging table `maintenance_drafts` in the plant schema. **Data touched:** machine id, cited manual section, free text, requesting user, timestamp. **Decision served:** a supervisor deciding whether to open a real work order.

### Identity

The application runs under its own identity for reading manuals, but the draft is written on behalf of the technician. The delegated identity carries a write grant on `maintenance_drafts` only. The application's service principal has no grant on any ERP object, so a bug in the tool cannot reach the ERP by accident. Denial test: a technician from plant two calling with a plant-one machine id must be refused by the authorization layer, not by the prompt.

### Scope

Arguments: `machine_id` must exist in the caller's plant; `manual_section` must be one of the sections retrieved in the current conversation; `note` is at most 500 characters; `priority` is not an argument at all, because the supervisor sets it. A request for "urgent" is therefore malformed, not merely discouraged.

### Approvals

Every draft lands in a supervisor queue. The queue is the approval; the tool call never becomes a work order on its own. Unknown: the queue's owner at plant one has not been named, and the review records that as a launch condition.

### Idempotency

Key: a client-generated intent id, minted when the technician confirms the note and kept for retries, hashed with user, machine id and manual section. A replayed call with the same key returns the existing draft id and writes nothing new; a second, different note on the same machine and section that day carries a new intent id and creates a second draft, because the key is per intent, not per day. A timed-out call reports "outcome unknown, safe to retry with the same key".

### Audit

Each row records actor, key, arguments, result, timestamp and, later, the supervisor's decision. Rows live in an audit table in the plant schema, kept thirteen months, readable by the supervisor group and the security lead. The `note` field may contain personal remarks, so it is stored but excluded from any export used for reporting.

### Test matrix (local stub, hypothetical results)

| Case | Input | Expected | Observed |
|---|---|---|---|
| Allowed | Plant-one technician, plant-one machine, retrieved section | Draft created, audit row written | As expected |
| Denied | Plant-two technician, plant-one machine | Refused at authorization | Refused; audit row records the denial |
| Malformed | `priority: urgent` supplied | Rejected by schema before handler | Rejected; no audit row (finding: log it) |
| Replayed | Same key twice | One draft, same id returned | One draft |
| Second note | Same machine and section, different note, same day | Second draft, new id | Two drafts |
| Timed out | Stub delays 5 s beyond limit | "Unknown" to caller; retry with key creates nothing new | One draft after retry |

### Findings and decision

One defect: schema rejections were not logged, so a burst of malformed calls would be invisible. Fixed in the validation layer, where the rejection happens, so a schema rejection now writes an audit row; retested. One unknown: the real staging table's transaction behaviour on the platform is untested locally; the stub is not the platform. The tool is acceptable as a draft-only capability, conditional on a named queue owner and a platform-side rerun of the denied, replayed and timed-out cases with the real delegated grants, since the stub cannot establish the platform's permission or transaction behaviour. ERP writes remain out of scope, and the review says so in its first line so that nobody reads "tool approved" as "work orders approved".

<!-- section:template -->

### Tool card

- **Name and effect class:** read / write / external effect; the target system and the objects touched.
- **Decision served and requester:** who asked for the tool and which human decision it feeds.
- **Explicitly out of scope:** effects this tool must never have.

### Identity

- **Executing principal:** delegated user / service principal / application identity, and why.
- **Permissions at the target:** the exact grants; the grants deliberately absent.
- **Denial cases:** an identity that must fail, and where the refusal is enforced.

### Scope

| Argument | Constraint | Enforced where | Malformed example |
|---|---|---|---|
| Name | Allowlist, range, entity binding, size | Schema / handler / target | A concrete rejected input |

### Approvals

- **Effect classes requiring a human, the approver's role, how the approval is recorded, and how the model's request is kept separate from the decision.**

### Idempotency and failure

- **Key definition, retry behaviour, timeout behaviour, duplicate delivery behaviour, what the caller sees when the outcome is unknown.**

### Audit evidence

- **Fields logged, storage location, retention, sensitive fields and their handling, who can read the log.**

### Test matrix

| Case | Input | Expected | Observed | Evidence location |
|---|---|---|---|---|
| Allowed / Denied / Malformed / Replayed / Timed out | | | | |

### Findings, unknowns, decision

- Defects with fixes and retest status; unknowns with owners; the conditional decision in one sentence.

<!-- section:limits -->

This review establishes that a tool behaved as its card promises under a local stub, with the identities and arguments you tried. It cannot establish the target system's real transaction, retry or permission behaviour; those need a run against the platform with the actual grants, and the review should say which cases were rerun there. Approval recorded in a queue is evidence of a human step only if the queue has a named owner who acts on it. Audit rows prove what was logged, not that everything relevant was logged. Escalate rather than proceed when a tool would write to a system of record, when the executing identity holds broader grants than the card states, or when a denial case passes only because of prompt wording.
