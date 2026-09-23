# Authorization and state boundary — template

Fictional engagement: Harrowgate Field Services. `authorization-matrix.csv` is the starting matrix; adapt it, do not assume it is enforced anywhere.

## 1. Identities

| Identity | Who or what | Where its permissions come from | What it may never do |
|---|---|---|---|
| Asking user | | | |
| Assistant service identity | | | |
| Ticket Desk integration | | | |
| Parts Requisition integration | | | |

## 2. Where each fact lives

| Fact | Lives in the application / a governed table / the model context / the document | Why |
|---|---|---|
| Asker's level and region | | |
| Coastal endorsement | | |
| Document status and effective date | | |
| Ticket assignment | | |
| Approval ids | | |
| Conversation so far | | |

## 3. Actions

| Action | Allowed for | Approval step | Reversible? | Idempotency key | Logged fields |
|---|---|---|---|---|---|
| Link document to ticket | | | | | |
| Change ticket status (not closed) | | | | | |
| Prepare draft requisition | | | | | |
| Submit requisition | denied to the assistant | | | | |
| Close ticket | denied to the assistant | | | | |

## 4. Denied-action response

Write the exact sentence pattern the assistant uses when refusing: the action, the policy id and section, the missing approval, and the offered alternative.

## 5. Untrusted content

How instructions found in a note, document or chat message are treated (use `injection-fixture.md`); what is reported to whom; what is logged.

## 6. Negative tests

List the identities and requests you would test to prove a denial, not only an allowance.
