# Cinderline capstone guide

Cinderline Components is the academy's shared fictional manufacturer. This
capstone, *Cinderline: from first conversation to a defensible decision*, asks
you to carry one quality-data engagement from the first conversation to a
handoff a customer could act on. Open it at `#/practice/dbxfe-capstone`.

**The original capstone identity is retained.** The scenario keeps its ID,
title, lesson links, claim links, its six original disclosure questions and
its six original rubric dimensions. The 2026-09-23 revision added five staged
disclosures, twelve requirements, a longer model with two architectural paths
and a mixed-outcome readout, four further rubric dimensions and this data
pack. Drafts and self-assessments you made against the earlier version remain
valid evidence of that version; nothing is reset, and the practice page shows
an earlier-version notice rather than hiding your work.

## What the customer keeps

Cinderline does not abandon its SQL Server ERP or its nightly ETL package.
Duplicate rows from package retries, corrections that arrive as CSV files with
the same inspection ID and a higher revision, two disagreeing morning reports,
a dashboard that shows its refresh time rather than the freshness of its
evidence, and a data team with a few hours a week are the situation you
design inside, not obstacles to assume away.

## Stages

1. **Discovery synthesis.** Read the stakeholder statements and the source
   inventory; name the decision, the acceptance roles, facts, unknowns and the
   evidence that would change the buying decision. Modules:
   [H2 discovery](#/module/dbxfe-m02) and [H1 teamwork](#/module/dbxfe-m01);
   guides `guide-fg01-discovery-brief`, `guide-fg02-stakeholder-map`,
   `guide-fg03-requirements-contract`.
2. **Source semantics and the metric contract.** Separate systems of record
   from derived copies, name the approved revision signal, and write a
   contract with grain, denominator, exclusions, business day, restatement,
   freshness and staleness. Reproduce the disputed day's three figures.
   Modules: [C1 modeling](#/module/dbxfe-modeling),
   [C4 business intelligence](#/module/dbxfe-bi); labs
   `lab-l11-modeling-metrics`, `lab-l10-contracts-quarantine`; guide
   `guide-fg11-metric-contract`.
3. **Ingestion, publication and recovery policy.** Walk the events delivery
   by delivery under the preserved reliable-data policy: the five rows give
   accepted A v2 12/1 and C v1 8/0 with B quarantined, totals 20/1 at 5%;
   replay changes no accepted total; an older revision cannot replace a newer
   one; a valid A v3 14/1 gives 22/1 once; conflicting deliveries block
   publication; a later conflict keeps the last verified 20/1 snapshot
   explicitly stale. Modules: [B3 ingestion](#/module/dbxfe-m04),
   [B1 Delta](#/module/dbxfe-delta), [B2 writes](#/module/dbxfe-delta-writes),
   [B6 orchestration](#/module/dbxfe-orchestration); labs
   `lab-l06-record-resolution`, `lab-l09-failure-recovery`; guides
   `guide-fg08-ingestion-decision`, `guide-fg09-cdc-contract`,
   `guide-fg10-quality-response`.
4. **Stale versus current evidence.** Read the failure timeline, separate
   facts from hypotheses, and show how an explicitly stale, dated snapshot
   would have changed the 8 a.m. decision. Module:
   [G4 operations](#/module/dbxfe-operations); guide
   `guide-fg31-escalation-packet`.
5. **Governed architecture, two paths.** Compare a governed lakehouse path on
   AWS with a path that strengthens the existing SQL Server and ETL estate,
   on the same criteria, and say what reverses your provisional choice.
   Modules: [G1 architecture](#/module/dbxfe-m08),
   [D1 governance](#/module/dbxfe-m06), [D2 identity](#/module/dbxfe-identity),
   [D3 AWS](#/module/dbxfe-aws), [G2 SQL Server](#/module/dbxfe-sqlserver);
   labs `lab-l14-governance-review`, `lab-l15-three-cloud-diagnosis`; guide
   `guide-fg04-architecture-decision`.
6. **Migration, reconciliation and rollback.** Waves, a reconciliation matrix
   where matching totals alone are insufficient, cutover conditions and a
   read-path rollback within the DBA's change windows. Modules:
   [G3 warehouse migration](#/module/dbxfe-warehouse-migration); lab
   `lab-l24-migration-reconciliation`; guides `guide-fg21-migration-inventory`,
   `guide-fg22-reconciliation`, `guide-fg23-cutover-rollback`.
7. **Demo, presentation sequence and proof of value.** A synthetic
   correction walk with an explain-back question and an honest fallback, a
   readout sequence for the meeting, and a charter whose criteria can fail.
   Modules: [H3 demos](#/module/dbxfe-m09), [H4 proofs of value](#/module/dbxfe-m10);
   guides `guide-fg24-demo-script`, `guide-fg25-demo-failure-plan`,
   `guide-fg26-pov-charter`, `guide-fg27-evidence-ledger`.
8. **Value model, alternatives, handoff.** Reproducible hypothetical
   arithmetic with sensitivity and exclusions, an alternatives memo that
   includes fixing the spreadsheet, and a handoff with owners, conditions and
   open risks. Modules: [H5 value](#/module/dbxfe-m11),
   [C6 FinOps](#/module/dbxfe-finops), [H6 execution](#/module/dbxfe-m12);
   lab `lab-l13-cost-model`; guides `guide-fg28-cost-value-model`,
   `guide-fg29-alternatives-memo`, `guide-fg30-executive-readout`,
   `guide-fg32-handoff-adoption-plan`.

## Using the data pack

The pack lives at `content/exercises/capstone-cinderline/`. Its README is the
data dictionary and carries the accepted-state table you should be able to
reproduce by hand. `source-inventory.csv` feeds stage 1;
`stakeholder-statements.md` feeds stages 1, 4 and 8; `flawed-metric.md`
feeds stage 2; `quality-events.csv` feeds stages 3 and 7, with its single
`what-if-conflict` row applied to the verified 20/1 baseline in a separate
fresh simulation; `failure-timeline.md` feeds stages 4 and 6. The seven
templates give each written deliverable a shape. Fill them before you open
the model; the practice page's rubric is a self-assessment you compare your
own draft against, not a grade.

## What the capstone is not

The pack executes nothing and proves nothing about any cloud platform. The
publication policy is fictional teaching policy, not a product guarantee. The
money is hypothetical and labelled. Several designs can be defensible if their
assumptions and evidence are clear, and a mixed or negative readout is a
legitimate outcome of a good submission.
