# The night the report was stale (fictional timeline, 2–3 March 2026)

Original fiction for the SpicyBrain capstone. Times, systems and people are
invented. The table separates what a log or message would show (a fact within
the fiction) from what someone inferred (a hypothesis), and adds what the
contract path described in the capstone would have shown instead. Use it as
the input for the "stale versus current evidence" section of your submission
and for the G4-style incident review in the handoff.

## Timeline

| Time | What the logs and messages show (fact) | Who noticed | Hypothesis (labelled) | What the contract path would show |
|---|---|---|---|---|
| 2 Mar 22:10 | Nightly ETL package starts; step 1 extracts North inspections for 2 March | nobody | — | Delivery D1 begins; rows retained raw with delivery identity |
| 22:48 | North extract completes; East extract waits on a lock held by a month-end batch | nobody | The month-end batch is the cause (unconfirmed) | East delivery still pending; nothing published for East |
| 23:05 | Package fails at the load step; the on-failure retry re-runs the whole package, re-exporting North a second time | nobody | — | The re-export is the same events delivered again; accepted state unchanged |
| 23:31 | Second attempt fails on East again; failure email lands in a shared mailbox | nobody until 06:30 | — | Alert routed to the operator's 06:30 check with the delivery status, not to a mailbox |
| 3 Mar 01:10 | Dashboard refresh runs on schedule over the partial reporting database: North present twice, East showing 1 March rows | nobody | — | North: publication blocked, "incomplete delivery"; East: "no delivery for 2 March"; last verified snapshots shown and labelled stale |
| 06:40 | `QC_Corrections_20260303.csv` with A version 2 (12/1) lands on the share | quality clerk | — | Delivery D2 admitted; if D1 were complete, North would publish 20/1 at 5.0% with `evidence_as_of 06:40` |
| 07:30 | Board reads "Updated 01:10". Workbook: North 6.7%. Sheet: North 12.0%. East looks normal | analyst, coordinator | "North Line 1 has a problem" | Board reads: North stale, reason incomplete delivery; East no delivery; no number nobody can date |
| 08:00 | Morning meeting sends the one available quality engineer to North Line 1 | operations director | Decision based on North's two numbers | Meeting escalates the missing delivery and defers the North judgement |
| 10:40 | Quality notices the correction was not applied; the analyst pastes A v2 into the workbook by hand: workbook 7.1%, sheet 10.8% | quality lead, analyst | "The correction fixed it" | Nothing to do; the correction was admitted at 06:40 |
| 11:15 | DBA reruns the package by hand: North exported a third time (ev-late), East rows arrive | DBA | — | Delivery D3: ev-late agrees with history and is older than v2; East publishes E, F, G at 5/44 = 11.4% |
| 11:40 | East step re-run once more; G delivered again | DBA | "Just to be safe" | Delivery D6: same event, no change |
| 13:00 | Analyst deletes "duplicate" rows in the reporting database by hand; no record of which rows | analyst | "Now the numbers are right" | Not possible: raw evidence is retained, accepted state is derived, nothing is deleted |
| 16:30 | Workbook shows 7.7% for North (three copies of A1 plus A2); sheet 10.6% | analyst | — | 5.0%, `evidence_as_of 06:40` |
| 4 Mar 08:00 | Meeting sees East for the first time: G, Line 4, 3 defects in 9 units | operations director | "Should have been yesterday's investigation" | Was visible at 11:15 on 3 March with an honest freshness label |

## What the night cost (hypothetical, labelled)

These figures come from the fictional plant controller's statement and are
planning assumptions, not measurements. Cinderline does not log how often the
report misdirects a decision; the capstone asks you to keep this line out of
the base value case until it does.

- One misdirected investigation: about 4 engineer-hours, a hypothetical $60
  per hour, $240.
- One East batch held a day later than necessary: 9 units at a hypothetical
  $250 expediting cost per unit, $2,250.
- Manual reconciliation on 3 March: analyst, coordinator and quality lead,
  roughly 5 hours between them, on top of the ordinary weekly reconciliation.

## Facts versus hypotheses, summarized

Facts within the fiction: the package retried and re-exported North; East was
missing at 01:10; the correction file existed from 06:40; the board carried a
refresh time and no evidence time; rows were deleted by hand at 13:00.

Hypotheses: that the month-end batch caused the lock; that North Line 1 had a
problem; that the hand paste "fixed" the figure; that deleting rows made the
numbers right. Each needs its own evidence before it enters a design.

## Questions this timeline should add to discovery

- Who is at work at 06:30 and can act on an alert?
- What does "updated" on the board mean today, and what should it mean?
- Who is allowed to delete rows in the reporting database, and how would
  anyone know it happened?
- Which of the 2 March figures did each person see, and when?
