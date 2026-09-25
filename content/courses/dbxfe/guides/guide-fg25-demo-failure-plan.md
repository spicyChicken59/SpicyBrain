<!-- section:action -->

Plan the failure before the session, in the same document as the script, so that when a step fails you are reading rather than improvising.

1. **List the steps that can fail live** and, for each, what the audience will see: an error, a blank screen, a wrong number, a hang.
2. **Prepare labelled local material** for each: a static table or a locally computed output whose inputs and outputs match the script, marked "prepared, not live" in the material itself, not only in your words.
3. **Write the honest sentence** you will say, in observable terms: what did not complete, what the prepared material shows, and that the live step is not counted as passed.
4. **Set a troubleshooting time box** (two or three minutes) and decide in advance who takes diagnosis offline.
5. **Decide what still can be agreed** without the live result: the metric definition, the expected behaviour, the next test.
6. **Capture evidence safely:** the failing step, the public-safe error context, the time, the environment; no credentials, no customer records.
7. **Write the follow-up** before you leave the building: what was agreed, what remains unverified, the owner, the next update time.

Evidence to collect: the failure list with prepared material per step, the captured error context, the record that the step was not passed, and the follow-up note as sent.

Deeper: the retained lessons [Recover from failure and unknown questions](#/lesson/dbxfe-m09-l03) and [Write follow-ups people can act on](#/lesson/dbxfe-m12-l02), the module [Demos that teach and prove](#/module/dbxfe-m09), and [Field execution and capstone](#/module/dbxfe-m12) for the escalation that follows.

<!-- section:example -->

**Fictional worked example: the Cinderline correction demo, step three fails.** The script runs locally over fixture files. At 5:00 the correction file is delivered; at 5:10 the run stops with an error naming a file path and a permission.

### The failure list, written the day before

| Step | Possible failure | Audience sees | Prepared material | Honest sentence |
|---|---|---|---|---|
| Baseline load | Fixture missing | Empty table | Static baseline table, labelled | "The load did not run; this table shows the inputs we intended." |
| Correction | Run error | Error text | Static before/after table with the rule beside it | "The correction step did not complete. This is prepared output, not a run." |
| Replay | Duplicate counted | 32 / 2 instead of 20 / 1 | None; this is a real defect, say so | "That is wrong, and it is the kind of defect the pilot must catch. I will not explain it away now." |
| Quarantine | Row silently dropped | Total unchanged, no quarantine row | Static quarantine row | "The row vanished instead of waiting; that is a defect." |

Time box: three minutes. Offline diagnosis: the data lead. Retest: the presenter.

### What happened (hypothetical)

At 5:10 the correction run errored. The presenter read the honest sentence for that row, opened the prepared table in the window already labelled "prepared, not live", and continued: "The rule we intended is that A version 2 replaces version 1, so the total becomes 20 inspected and 1 defective. We can agree whether that is the right rule now. What we cannot do is count this step as executed."

The operations director asked, "So did it work or not?" Answer: "No. The live step failed. The prepared table is what we expected to see."

Troubleshooting stopped at the three-minute box. The error mentioned a path under the presenter's home directory and a permission, which suggested an environment problem rather than a logic problem, but the presenter said "suggests" and did not name a cause. As the plan named, the data lead took diagnosis offline after the session, and the presenter kept the retest.

### What was still agreed

The quality lead confirmed the denominator and the weekly approval rule. Both leads agreed that replay must not double count and that invalid rows must be visible. Those three sentences were read back and accepted as the definition to carry into the charter. Nothing about execution was agreed.

### Evidence captured

Time of failure, the step, the fixture hashes, the error text with the home-directory path replaced by a placeholder, the local environment description (interpreter version, machine), and the audience's three agreed sentences. No screenshots of the error were shared, because the path contained a user name.

### Follow-up sent that afternoon

"Thank you for the time this morning. The baseline step ran and showed 18 inspected and 1 defective. The correction step did not complete, so the 20 / 1 result you saw was prepared output, not an execution. We agreed the metric definition (defective units over inspected units, corrections approved weekly by the quality lead) and two behaviours the pilot must show: no double counting on replay, and visible quarantine of invalid rows. The data lead will look at the failed step's environment; I will rerun the full sequence and send either the recorded output or a specific blocker by Thursday. Nothing in this note validates source connectivity or production behaviour."

### What the plan did not cover

A question about whether the platform supports the customer's SQL Server version arose during the wait. It was recorded as unknown with the integration specialist as owner. The failure plan now has a row for "unknown compatibility question" with the sentence "I have not checked that version; let us record it."

<!-- section:template -->

### Steps that can fail

| Step | Failure mode | What the audience sees | Prepared material (labelled) | Honest sentence | Is this a defect or an environment issue? (decide only if observable) |
|---|---|---|---|---|---|

### Time box and offline owner

- **Minutes allowed for live troubleshooting, who takes diagnosis offline, who owns the retest.**

### What can still be agreed without the live result

- **Definitions, expected behaviours, next tests; each read back and attributed to the person who agreed.**

### Evidence capture

- **Time, step, input identities or hashes, error context with paths and names replaced, environment description; a list of what must not be captured (credentials, customer records, user names).**

### Follow-up note

- **What ran and showed; what did not complete and was shown as prepared; what was agreed and by whom; owner of diagnosis; owner of retest; next update date; the sentence stating what the note does not validate.**

### Unknown questions

- **Question, what you know, the uncertain part, the owner, how the answer returns.**

<!-- section:limits -->

A failure plan establishes that a failed step was reported as failed, that the audience could still discuss intended behaviour on labelled material, and that a follow-up with owners was sent. It cannot establish the cause of the failure; an error message suggests, and diagnosis belongs to the named owner after the session. It cannot turn agreement on definitions into agreement on a design or a purchase. Prepared material is evidence of intent, not of behaviour, however carefully it was computed. Escalate when the same step fails on the retest, when a failure exposes credentials or customer data on a shared screen, or when the audience treats the prepared output as a result despite the label; that last case needs a written correction, not a quiet omission.
