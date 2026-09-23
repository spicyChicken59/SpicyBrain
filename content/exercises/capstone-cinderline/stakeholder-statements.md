# Stakeholder statements (fictional)

Every person, role and quotation here is invented for the SpicyBrain
Cinderline capstone. The first six statements were the practice page's
original disclosures. The revised page also discloses Leo's remark on
operational capacity, the three new voices below (the DBA, the analyst and the
plant controller) and Leo's account of the failure night, whose full
sequence is in `failure-timeline.md`; the other further remarks extend the
statements for this data pack only. No statement is a requirement until
the submission records who accepted it.

## Mara, operations director

Disclosed: “At the 8 a.m. meeting we decide which line to investigate. The
defect rate differs between the analyst workbook and the plant sheet. Hourly
availability sounds useful, but we have not shown that decisions need
continuous updates. I would fund a next step if the metric is trusted and
someone can maintain the feed.”

Further, in conversation: “On 3 March we sent our one free quality engineer to
North Line 1 because both numbers looked bad. East was the real problem and we
saw it a day late. I do not need a faster board; I need to know when a number
is not to be trusted, before the meeting, in words a coordinator understands.”

## Imani, quality lead

Disclosed: “For the pilot, use defective units divided by inspected units.
Inspection IDs persist through corrections and an approved source revision
indicates ordering. Equal key/revision conflicts need investigation. We need
to agree the business-day boundary and whether historical reports are
restated.”

Further: “Corrections go out on Fridays in one file. Once a file was re-sent
because the clerk was unsure it had arrived; once a row was re-typed with a
different quantity at the same revision, and I would rather that blocks the
report than picks a side. If a correction restates last Tuesday, the board
should say so, not quietly change.”

## Leo, data lead

Disclosed: “We can prepare approved synthetic data now. SQL Server
version/topology and CDC permission still need the DBA. Quality CSV approvals
happen periodically. Two engineers can contribute a limited amount of time,
but continuous support is not staffed. We need a named operator before
relying on the new report.”

Further (operational capacity): “Two engineers, about four hours a week each
for eight weeks, then less. One shared DBA whose change windows are Tuesday
and Thursday evenings. Plant IT is staffed 06:00 to 18:00 and nobody is on
call overnight. The corrections file is approved on Fridays, sometimes
mid-week for an urgent case. The analyst who maintains the workbook is away
one week a month and has no backup. Any alert that fires at 23:05 will be read
at 06:30 at the earliest, so the design has to assume that.”

## Noor, security lead

Disclosed: “Do not copy unapproved fields. We must classify real data,
identify human/workload identities, and review the source-to-cloud path. AWS
region and exact connectivity pattern are not agreed. A classic or serverless
label alone does not satisfy our requirements. A specialist review is required
before real-data execution.”

Further: “A file share that anyone in quality can write to is not an approved
source until we say which account writes to it. Whoever proposes a pipeline
identity should show me what it cannot do, not only what it can.”

## Elena, sponsor

Disclosed: “For this exercise only, use an unapproved planning ceiling of
$1,500 for pilot cloud usage; that is not authorization to spend. For the
illustrative annual model, compare 5, 10, and 15 hours/week released over 48
weeks at a hypothetical $60/hour, $12,000 recurring cost, and $15,000 one-time
implementation. Real prices, realized benefit, and complete cost still need
verification.”

Further: “If the honest answer is to fix the spreadsheet formula first, say
so. I would rather fund a small thing that works than a large thing that is
argued.”

## Arun, maintenance lead

Disclosed: “No. We would like a later read-only manual assistant, with
machine/version sources and human escalation. Work-order changes are not
approved. Keep the quality pilot bounded.”

Further: “The sensor historian is mine and it stays out of this. When the
quality figure is trusted, we can talk about whether the manuals are next.”

## Dev, database administrator (new voice)

Source inventory: “The ERP is SQL Server; I will confirm the exact version and
whether it is a single instance or an availability group. Inspections live in
`dbo.Inspection` and `dbo.InspectionResult`, updated in place. A nightly
package copies the day's rows into a reporting database at 22:10; if it fails
and retries, it re-sends rows it had already delivered, so the reporting
database can hold the same inspection twice. Corrections do not touch the
ERP: they arrive as a CSV on a file share with the same inspection ID and a
higher source revision, and the package appends them as new rows. The plant
sheet is pasted from the reporting database and edited afterwards. Change
data capture is not enabled and needs a change request; my windows are
Tuesday and Thursday evenings.”

## Sam, analyst (new voice)

Metric as computed: “The workbook averages the per-row defect rate over every
row in the extract with a positive inspected quantity, grouped by load date.
It does not remove duplicated rows or drop a superseded revision, because the
extract has no flag for either. The plant sheet sums units over whatever rows
are pasted, including a negative quantity someone typed as an adjustment, and
groups by inspection date. On the day we argued about, once I had pasted the
correction in by hand, the workbook said 7.1 percent, the sheet said 10.8
percent, and the figure quality later agreed was 5.0 percent. Nobody is lying;
the three numbers answer three different questions. When a row comes through
with more defects than units I delete it and move on; there is nowhere to
record that.”

## Priya, plant controller (new voice)

Baseline and cost, for this exercise only: “Treat these as hypothetical
planning figures, not audited numbers. The analyst spends about six hours a
week reconciling the workbook and the sheet, the plant coordinator about an
hour a day, and the quality lead about two hours a week chasing corrections:
roughly thirteen hours a week in total. A misdirected morning investigation
costs about four engineer-hours, and a held shipment adds expediting cost of
around $250 per unit affected. We do not log how often the report causes a
wrong decision, so any avoided-cost figure needs its own measurement before
anyone counts it.”
