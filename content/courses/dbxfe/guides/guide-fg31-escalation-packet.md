<!-- section:action -->

An escalation packet lets someone who was not there act without asking you the first five questions. Write it in the order a specialist reads: what is happening, who it affects, how to see it again, what you have, what you want.

1. **Symptoms**, in observable terms with times and zones: what failed, what was displayed, what the logs said. No cause yet.
2. **Impact**: which decision, report or user is affected, since when, and what they are seeing instead. Say whether data is stale, wrong or unavailable; those are different problems.
3. **Reproduction**: the smallest sequence that shows the symptom again, how many times you tried and how many times it reproduced. "Intermittent" needs a count.
4. **Environment and versions**: platform components, runtime versions, region, identity used, the change made most recently before the symptom.
5. **Logs and evidence**: excerpts with credentials, paths containing user names and customer records removed; the run or job identifier; where the full logs are.
6. **What you tried** and what each attempt showed, including the ones that changed nothing.
7. **Hypotheses**, labelled as such, with the observation that supports each.
8. **The precise request**: one question a specialist can answer, or one action with a named owner, and when the next update is due either way.

Evidence to collect: timestamps, the reproduction record with counts, sanitized log excerpts, the version list, and the list of attempts with outcomes.

Deeper: the retained lessons [Write follow-ups people can act on](#/lesson/dbxfe-m12-l02) and [Orchestration, failure, and reconciliation](#/lesson/dbxfe-m04-l03), [Production operations, observability and recovery](#/module/dbxfe-operations) for separating facts from hypotheses on an incident timeline, and [Orchestration and recovery](#/module/dbxfe-orchestration) for failure after raw retention and before an external effect.

<!-- section:example -->

**Fictional worked example: the Cinderline pilot pipeline stops after retaining raw deliveries.** Written by the operator on pilot day 9 for the data lead and the integration specialist. Times are plant local; identifiers and versions are fictional.

### Symptoms

At 05:42 the nightly run wrote the raw delivery for day 9 (batch `q-0319`, 409 rows) and then stopped at the resolution task with the message "task failed: resolver exited with status 3" and no further text. The accepted-inspection table still shows day 8's snapshot `snap-0318-a`. The morning report displayed day 8's totals with the stale label, as designed.

### Impact

The 08:00 meeting used day 8's rate with the stale label visible; the operations director was told at 06:30. No wrong number was shown; the number was a day old and said so. No downstream effect was sent: the nightly run failed before the notification step, and the reruns executed the resolution task alone; `snap-0319-a` (06:14) is retained and unpublished.

### Reproduction

Rerunning the resolution task alone from the retained raw delivery reproduced the failure on 2 of 3 attempts (06:05 failed, 06:14 succeeded, 06:22 failed). The successful attempt produced snapshot `snap-0319-a` with 409 inspected and 17 defective, which matches the re-cut old report for day 9. Running the resolver locally over a copy of batch `q-0319` succeeded 5 of 5 times, with the approval lookup stubbed to answer at once, so the local runs say nothing about the lookup.

### Environment and versions

Platform workspace `cl-pilot` in the agreed region; job `quality-nightly` version 14; resolver task on runtime version 16.x (fictional); pipeline identity `sp-quality-pilot`; the most recent change before the symptom was on day 7, when the operator added a 20-second timeout to the CSV approval lookup task. Day 8's run, after that change, completed normally.

### Logs and evidence

Excerpt from the resolver task log, sanitized:

```
05:42:11 resolver start batch=q-0319 rows=409
05:42:13 approval lookup: 1 correction pending, approver=[removed]
05:42:33 approval lookup timed out after 20s
05:42:33 resolver exit status=3
```

Full logs: job run identifiers `r-8814` (nightly, 05:42, failed), `r-8815` (06:05, failed), `r-8816` (06:14, succeeded), `r-8817` (06:22, failed). Snapshot `snap-0319-a` from the successful rerun is retained and not yet published, pending this escalation.

### What was tried

Rerun three times (above). Local run five times (above). Checked that the raw delivery is complete: 409 rows, hash matches the CSV import log. Checked the approval store is reachable from the workspace: a manual query returned in 0.4 seconds at 06:30, after the failures.

### Hypotheses (not conclusions)

1. The approval lookup intermittently exceeds the 20-second timeout added on day 7; supported by the timeout line in the logs of all three failed runs and by day 8's success being a run with no pending correction, so the lookup returned quickly. 2. A network path between the workspace and the approval store is slow at 05:40 specifically; not supported by anything yet, since the only manual check was at 06:30.

### Precise request

To the integration specialist: is a 20-second budget for the approval store lookup reasonable from this workspace at 05:40? A follow-up question, how to observe that latency over a week, waits for this answer. To the data lead: approve publishing `snap-0319-a`, which matched the re-cut report, or say why it should wait. Next update from the operator by 12:00 today whether or not either answer arrives, and the day-10 run will keep the 20-second timeout unless the data lead says otherwise, so that the evidence stays comparable.

<!-- section:template -->

### Symptoms

- **What failed or misbehaved, when (time and zone), what was displayed or logged; no cause.**

### Impact

- **Which decision, report or user is affected, since when, what they see instead; whether data is stale, wrong or unavailable; any downstream effect sent or withheld.**

### Reproduction

- **The smallest sequence, the number of attempts, the number that reproduced, and any successful attempt's output.**

### Environment and versions

- **Components and versions, region, identity used, the most recent change before the symptom and whether a run after that change succeeded.**

### Logs and evidence

- **Sanitized excerpts (credentials, user paths and customer records removed), run identifiers, where the full logs are, what is retained and unpublished.**

### What was tried

| Attempt | Time | Result |
|---|---|---|

### Hypotheses

- **Each labelled as a hypothesis, with the observation that supports it or "not supported yet".**

### Precise request

- **One answerable question or one action per recipient, the recipient's name, when the next update is due either way, and what you will do meanwhile.**

<!-- section:limits -->

An escalation packet establishes what was observed, how often it reproduced and what was tried; it does not establish the cause, and a hypothesis stays a hypothesis until an observation confirms it. Reproduction counts are evidence about the attempts you made, in the window you made them, and an intermittent symptom can hide from a small sample. Sanitized logs are evidence only if the sanitization removed nothing the specialist needs; say what was removed. A packet cannot grant the specialist access, and it should not promise a fix date. Escalate further, to the customer's own owners, when the impact includes a wrong number acted on rather than a stale one labelled, when credentials or customer records appear in any artifact, or when a retained-but-unpublished snapshot would be needed for a decision before the packet is answered.
