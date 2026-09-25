# Handoff and next-step email (template)

Fictional exercise. A handoff names owners (roles), dates or decision
conditions, evidence references and open risks. It never states an assumption
as agreed. Use it for the follow-up email, the operator's runbook summary and
the incident review of the failure timeline.

## Follow-up email

Subject: [engagement] — decisions and next evidence

Thank you for [what was disclosed]. Our proposed first scope is [plant,
metric, contract]; [what stays separate]. The synthetic walk explains expected
behaviour; it does not validate [connectivity, network, performance].

| Owner (role) | Please confirm or decide | By (date or condition) |
|---|---|---|
| Operations and quality | business-day boundary; restatement rule; stale-label wording | |
| Analyst | the disputed day's three figures; retirement of the current formula | |
| DBA and data lead | ERP version and topology; extraction permission; delivery labelling on rerun; baseline plan | |
| Security | classification; source-to-cloud path review | |
| Data lead | named operator; conflict-withdrawal owner | |
| Plant controller | baseline hours; start of the incident count | |
| Sponsor | scope and spending authorization (none implied) | |

Review date or condition: [ ]. That review will [finalize the charter /
revise the design / retain the current path while closing a named blocker].

Open risks: [ ].

Please correct any assumption above before we treat it as agreed.

## Operator runbook summary (one page)

- Alert routing: [who, when, what they can do without the DBA]
- Replay: [from retained raw with delivery labels; expected unchanged totals]
- Conflict: [what blocks; who withdraws the erroneous delivery; how the decision is recorded]
- Stale label: [wording the board shows and who can clear it]
- Rollback: [read-path switch; who decides; what is never deleted]
- Windows: [what waits for Tuesday or Thursday]

## Incident review of the failure timeline

| Fact | Hypothesis | Prevention in the design | Owner |
|---|---|---|---|
| | | | |

## Escalation packet (if a blocker stops the pilot)

- What is blocked, since when, evidence reference:
- What was tried:
- Decision requested, from whom, by when:
- What happens if no decision is made:
