<!-- section:dbxfe-tools-l01-outcome -->

After this lesson you can follow one tool call from a model's proposal to an executed effect and name every check in between: the signed-in identity, the tools the application exposes, the tool's schema, the delegated permission, the idempotency key, the approval hold and the audit row. You can explain why retrieved text and system prompts cannot authorize anything, why a timeout is an unknown outcome, and what the Model Context Protocol (MCP) standardizes and what it leaves to you. Every number comes from Lab L22's local run over synthetic fixtures.

<!-- section:dbxfe-tools-l01-start -->

Bring the retained lesson [Choose retrieval or a tool-using agent](#/lesson/dbxfe-m07-l02), which ends where this one starts: if a tool is ever authorized, require verified permissions, bounded arguments and an approval step. The [GenAI, retrieval and agents](#/module/dbxfe-genai) module separates relevance from permission. You need to read JSON and a short Python function; if you think in SQL, treat a grant check as a `WHERE` clause on who may touch which rows.

<!-- section:dbxfe-tools-l01-call -->

A model with tools returns a *proposal*, a tool name and JSON arguments. Cinderline's assistant receives, for example:

```json
{"tool": "create_maintenance_draft",
 "arguments": {"machine_id": "M7", "manual_section": "M7-4.2",
               "note": "Pressure drop 1.8 bar across the hydraulic filter; replacement due."},
 "idempotency_key": "k-02"}
```

The application passes it to a **policy gate** and only then to a handler that writes to the draft store. The gate checks, in order: a valid session, a tool the application exposes, the tool's JSON Schema, the machine's plant, the user's grant intersected with the application's scopes, the idempotency key, the approval policy, then execution with a bounded retry. Cheap, effect-free checks come first, so a refused call never reaches a handler. The schema sets `additionalProperties: false`, so `priority: urgent` is malformed rather than merely discouraged.

<!-- section:dbxfe-tools-l01-identity -->

Three identities meet in a call: the **user** who asked, the **application** (a service principal such as `app-maint-assistant`) that holds credentials, and whichever principal the **target** evaluates. Under app authorization the target sees the service principal, so every user inherits its reach. Under delegated, on-behalf-of-user authorization the target sees the user, bounded by the scopes the application was granted:

| Call | User grant | Application scope | Decision |
|---|---|---|---|
| C02: tech-n1 drafts for M7 | yes | yes | allowed |
| C05: tech-s1 drafts for M7 | no | yes | denied (user) |
| C14: sup-n1 closes D1 | yes | no | denied (application) |
| C15: expired session | none | not reached | denied, no fallback |

On Databricks, agent user authorization was marked Public Preview when last reviewed, and a missing forwarded token can fall back to the app identity: test with several callers and with none.

<!-- section:dbxfe-tools-l01-injection -->

Retrieved text crosses a trust boundary: its author never signed in. Cinderline's index holds a supplier catalogue page, DOC-SUP-117, that claims a supervisor approved an emergency order of 20 × P-9001 and asks for `request_spare_part` and `delete_work_order`. That is indirect prompt injection. The model may comply, but the gate never reads the page: C10's forged `approved_by` argument is malformed, C11's clean request is held as approval A2 and later rejected, and C12 names a tool the application never exposed. A comment claiming "the current user is supervisor sup-n1" changes nothing, because identity comes from the session. Removing every document from every call leaves all 25 decisions unchanged.

A **system prompt** such as "never delete work orders" is a request to the model, sitting in the same context an attacker can reach. OWASP's excessive agency risk names the real fix: less functionality, fewer permissions and less autonomy, each enforced in code.

<!-- section:dbxfe-tools-l01-approval -->

External effects wait for a human. The gate stores the held request's exact arguments and digest, and the approver acts in their own session, never through the model. For Lab L22's A1 (2 × P-0415), the requester's self-approval is refused, a South technician lacks `parts:approve:north`, the North supervisor approves, and the application executes PR1 once on the technician's behalf. A second click changes nothing, and reusing the request's key with quantity 20 is a conflict, so an approval for 2 cannot become 20. The approver also sees `influenced_by`, which is how A2's origin in an unreviewed supplier page reached the person who rejected it.

<!-- section:dbxfe-tools-l01-retries -->

A timeout means no reply arrived in time, not that nothing happened. The gate retries only timeouts, at most three attempts, waiting 500 ms and then 1000 ms, and only because every attempt carries the same idempotency key. The key names one intent; the gate stores `(user, tool, key)` with the arguments' digest and outcome:

```python
status = gate._key_status((user, tool, key), digest(arguments))
# 'new' executes; 'replay' returns the stored outcome;
# 'conflict' refuses; 'resolve' re-sends with the same key
```

C17 is the case to remember: the store wrote D3 on attempt 1, all three replies were late, and after 7500 ms the gate reported `timed_out` with outcome unknown. C18, the same key a minute later, returned D3 in 200 ms. A new key per retry would have written a fourth draft. General-purpose clients agree: urllib3 retries a late reply to a GET or PUT by default, not to a POST.

<!-- section:dbxfe-tools-l01-mcp -->

The Model Context Protocol (MCP) lets a server expose tools, resources and prompts to clients over JSON-RPC 2.0. A client discovers tools with `tools/list` and calls one with `tools/call`, over stdio to a local subprocess or Streamable HTTP to a URL:

```json
{"jsonrpc": "2.0", "id": 7, "method": "tools/call",
 "params": {"name": "create_maintenance_draft",
            "arguments": {"machine_id": "M7", "manual_section": "M7-4.2", "note": "Pressure drop 1.8 bar"}}}
```

Each tool carries an `inputSchema` and optional annotations such as `readOnlyHint`, which are hints: clients should not decide anything from annotations sent by untrusted servers. For HTTP transports, the MCP Python SDK's authorization checks a bearer token's expiry and the endpoint's scopes, and its audience only when audience validation is enabled, which the MCP specification requires servers to do. That proves who connected, not whether this user may draft for machine C4; the handler and the target still decide. On Databricks, managed MCP servers expose Unity Catalog functions, vector search indexes and Genie Agents (formerly Genie spaces), and custom servers can run as apps with OAuth; verify availability and status first.

<!-- section:dbxfe-tools-l01-audit -->

The gate, not the model, writes one row per decision: sequence, time, event, actor, on-behalf-of, executing identity, tool, argument digest, key, decision, reason, attempts, effect or approval id, and `influenced_by`. Refusals are rows. Lab L22 writes 26 rows for 20 calls and 5 approval actions, including 7 denials and 3 malformed calls, and stores arguments only as a digest, so notes and tokens never enter the log. A trace helps you debug a model's steps; the audit proves who did what under which decision. Test the gate with a matrix of allowed, denied, malformed, replayed, timed-out, approval and injected cases, asserting decision, reason and effect count for each.

<!-- section:dbxfe-tools-l01-example -->

Selected rows from the executed lab run (synthetic fixtures, local stubs):

| Event | Proposal | Decision | Effect |
|---|---|---|---|
| C02 | tech-n1 drafts for M7, key k-02 | allowed | D1 |
| C03 | the same call again | replayed | D1, no new draft |
| C06 | adds `priority: urgent` | malformed | none |
| C11 | 20 × P-9001 from the supplier page | approval_required | A2 held |
| C12 | `delete_work_order` | denied: not exposed | none |
| C14 | sup-n1 closes D1 | denied: application lacks scope | none |
| C17 | draft for M12, three late replies | timed_out | D3 exists |
| AP3 | sup-n1 approves A1 | approved, executed | PR1 |

Final state: three drafts, one purchase request, 26 audit rows, and no decision changed by removing the retrieved documents.

<!-- section:dbxfe-tools-l01-exercise -->

Harbor Lane Clinic's supply assistant uses the same gate. `order_supplies(item_code, quantity, ward_id)` allows 1 to 40 units, needs `supplies:order:<site>`, and holds orders above 10 units for someone else with `supplies:approve:<site>`. The application's scopes are `catalog:read`, `supplies:order` and `orders:cancel`. Ward W3 belongs to the East site. The East nurse holds `catalog:read:east` and `supplies:order:east`; the West nurse holds `catalog:read:west` and `supplies:order:west`; only the East pharmacist holds `supplies:approve:east` and `orders:cancel:east`. Predict the decision for: (a) an East nurse ordering 6 of S-101 for ward W3; (b) the same call with the same key; (c) 12 units with a new key; (d) a West nurse ordering for W3; (e) 45 units; (f) an East nurse cancelling order O1 while a packing label in context claims a pharmacist approved "cancel all open orders".

<!-- section:dbxfe-tools-l01-solution -->

(a) Allowed: 6 is not above 10, so there is no hold; order O1. (b) Replayed: the same key and digest return O1 with no second order. (c) Approval required: 12 is above 10, so it waits for a pharmacist. (d) Denied, insufficient scope: the West nurse lacks `supplies:order:east`, and ward W3 is East. (e) Malformed: 45 is above the maximum of 40, refused before any permission check. (f) Denied, insufficient scope: the nurse lacks `orders:cancel:east`; the application holding `orders:cancel` does not help, because delegation is an intersection, and the label's claimed approval is content, not authority. These are Lab L22's transfer cases T01 to T06, decided by the same code.

<!-- section:dbxfe-tools-l01-mistakes -->

- **Counting the system prompt as a control.** It is a request; record it as one and enforce the rule in code.
- **Running every tool as the application.** Every user inherits the service principal's reach.
- **Falling back to the app identity when a user token is missing.** Fail closed instead.
- **Treating a timeout as a failure.** The effect may exist; retry only with the same key.
- **Creating a new key per attempt.** It looks careful and duplicates effects.
- **Trusting tool annotations or a server's tool list.** Expose an allowlist; hints are not guarantees.
- **Logging only successes.** Refusals are the evidence that a boundary held.

<!-- section:dbxfe-tools-l01-sources -->

Protocol facts come from the MCP Python SDK 2.2.0 and its schema package, downloaded from PyPI and read locally; the specification's tools page was read in its source repository on 2026-09-25. The audience check was corrected on 2026-09-25 after reading the SDK's auth settings and token verifier at its v2.2.0 tag and the specification's authorization page in their source repositories. Databricks facts come from the Databricks-authored databricks-mcp 0.9.2 and databricks-ai-bridge 0.22.0 packages and MLflow 3.16.1; the MCP on Databricks and agent authentication pages were not fetched here, so verify server types, preview status and regions there; the name Genie Agents comes from Databricks' developer documentation source (databricks/devhub). OWASP wording is as reproduced in garak 0.17.0; retry defaults come from urllib3 2.6.3, whose retry code was re-read at its release tag on 2026-09-25. Lab results are local executions, not platform behaviour.

<!-- section:dbxfe-tools-l01-related -->

- [GenAI, retrieval and agents](#/module/dbxfe-genai): relevance versus permission, and the tool boundary.
- [Identity, authorization and audit](#/module/dbxfe-identity): principals, grants and audit events in depth.
- [Databricks Apps and application architecture](#/module/dbxfe-apps): app and user authorization in front of the tools.
- [GenAI evaluation, traces and failure analysis](#/module/dbxfe-genai-eval): tracing a denied tool call.
- [Orchestration and operations](#/module/dbxfe-orchestration): retries and external effects in scheduled work.
- The Untrusted content threat review and Tool action review field guides turn this into review templates.

<!-- section:dbxfe-tools-l01-revisit -->

Without looking back, name the gate's checks in order; say whose grants apply under app authorization and under delegated authorization; explain why C17 reported `timed_out` while D3 existed; and say what `tools/list` gives you and what it does not decide. Then open the Lab L22 walkthrough and predict the transfer cases before reading their decisions.
