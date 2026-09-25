<!-- section:action -->

A demo is a short argument with evidence. Write the argument first, then choose the smallest set of screens that prove it, then decide how deep to go for the people in the room.

1. **Name the business question and the decision behind it.** One sentence each. If you cannot write them, you are not ready to demo; go back to discovery.
2. **State the expected result before you start.** The audience should know what a success looks like and be able to check it on screen.
3. **Plan the evidence moments.** Each is a point where the audience can verify something themselves: rows rather than a percentage, a total that changes for a stated reason, a replay that changes nothing. Three to five moments in fifteen minutes.
4. **Write the explain-back question** you will ask after the main moment, so the audience says the rule in their own words.
5. **Set depth by audience.** For each moment, write the business version and the technical version. Do not present both to everyone.
6. **Label what is synthetic, prepared or live**, and what the demo does not prove.
7. **Prepare the setup checklist and the fallback**, then rehearse once with a timer.

Evidence to collect: the script with timings, the expected results written before the session, the setup checklist, and afterwards the audience's explain-back answer and any question you could not answer.

Deeper: the retained lessons [Discover the demo audience and decision](#/lesson/dbxfe-m09-l01) and [Tell a story with visible evidence](#/lesson/dbxfe-m09-l02), the module [Demos that teach and prove](#/module/dbxfe-m09), and [Discovery and qualification](#/module/dbxfe-m02) for finding the decision before the script.

<!-- section:example -->

**Fictional worked example: Cinderline, fifteen minutes, the disputed morning defect rate.** Two audiences will see versions of this script on different days: the operations director and the quality lead first, the data lead and the DBA a week later.

### Business question and decision

Question: which defect rate should the 08:00 meeting trust when the analyst workbook and the plant sheet disagree? Decision: whether a one-plant pilot of a single accepted-inspection path is worth chartering. Expected result, stated up front: after an approved correction, the rate changes once, from about 5.56% to 5%, and replaying the same correction changes nothing.

### Script with evidence moments

| Time | Step | Evidence moment | Business depth | Technical depth | Label |
|---|---|---|---|---|---|
| 0:00 | Intent | None | "We follow one correction into the rate. Synthetic data; this proves nothing about your source connection." | Same sentence, plus the note that the path is a local run, not the platform | Spoken |
| 2:00 | Baseline | Rows: A v1 10 inspected, 1 defective; C v1 8, 0. Total 18 / 1 | Show the two rows and the total; say 5.56% | Show the inspection key and revision columns; name the accepted-state rule | Synthetic, run live locally |
| 5:00 | Correction | A v2 12 / 1 arrives; total becomes 20 / 1 | "One row changed once. The rate is 5%." Ask what they would do differently at 08:00 with this number | Show that raw v1 is retained and the accepted state carries v2 only; show the ordering rule on revision | Synthetic, run live locally |
| 8:00 | Replay | Deliver A v2 again; total stays 20 / 1 | "A repeated file does not double count." | Show the snapshot id is unchanged; mention idempotency without the word | Synthetic, run live locally |
| 10:00 | Invalid record | B with a negative inspected quantity is quarantined; total unchanged | "Bad data waits for a person; it does not vanish or get counted." | Show the quarantine row and the reason code | Synthetic, run live locally |
| 12:00 | Explain-back | Audience answer recorded | "Which denominator does this rate use, and who decides when a correction is approved?" | "What happens if two revisions carry the same number?" | Live answer |
| 14:00 | Close | Next evidence named | Metric acceptance, approved sample, operating owner | Source version and topology, CDC permission, path review | Spoken |

### Depth decisions

The business audience never sees the revision column; they see a row change and a rate change. The technical audience never hears "trusted metric"; they see the ordering rule and the retained raw row and are asked where it would break. Both audiences hear the same three labels: synthetic input, locally executed, source connectivity untested.

### Setup checklist

Fixture files present and hashed; local run completed once this morning with the expected totals; the script rehearsed once end to end with a timer, 14:20 against 15:00; screens arranged so rows and totals are visible together; the prepared static table open in a second window, labelled "prepared, not live"; the fallback plan printed; a timer.

### What the demo does not prove

Connectivity to the ERP, performance on real volumes, the platform's behaviour, or that the customer's actual corrections follow the revision rule. Those are the next evidence, and the close says so in the same breath as the result.

### After the session (hypothetical)

The quality lead answered the explain-back with "defective units over inspected units, corrections approved by me weekly" and added that historical reports are not restated. The denominator and the approval rule went into the charter draft as proposed definitions, which she confirmed in writing the next day. The restatement remark went in as an open question, because the demo had just moved a reported rate from 5.56% to 5%: how are corrections to already-reported days shown? The operations director asked whether the rate could be shown per line; that was recorded as an unverified request, not a commitment.

<!-- section:template -->

### Business question and decision

- **Question:** what the audience wants to know, in their words. **Decision:** what they will do differently depending on the answer. **Expected result:** stated before the demo begins, checkable on screen.

### Audience

- **Who is in the room, what each person accepts or decides, and which depth each needs.**

### Script

| Time | Step | Evidence moment (what the audience can verify) | Business depth | Technical depth | Label (synthetic / prepared / live) |
|---|---|---|---|---|---|

### Explain-back question

- **The question, the answer you hope to hear, and what you will do if the answer differs.**

### Setup checklist

- **Inputs and their hashes, a completed dry run with expected outputs, screen layout, the prepared fallback material and its label, a timer.**

### What this demo does not prove

- **A short list stated in the close: connectivity, performance, platform behaviour, real-data semantics.**

### After the session

- **Explain-back answer as given, questions you could not answer, requests recorded as unverified, next evidence with owners.**

<!-- section:limits -->

A demo script establishes that an audience saw a stated behaviour on stated inputs and could say the rule back. It cannot establish anything about the customer's real sources, volumes, permissions or performance, and a demo that ran on a local fixture is evidence about the fixture. The explain-back answer is evidence of understanding on that day, not of agreement to a design. Requests made during the session are requests until someone with authority accepts them. Escalate, or stop and re-plan, when you cannot name the decision the demo serves, when the audience's definition of the metric differs from the one you built, or when a question about supported versions or connectivity arises that only a specialist can answer.
