# Capstone 3: enterprise coexistence and modernization

Northbrook Holdings, a fictional industrial group, has acquired Vale
Components and inherited three estates on three clouds, one of them under a
data-residency rule. The CIO's memo asks for one platform by year end. This
capstone asks you to find out what the evidence actually supports, and to say
so to two audiences. Open it at `#/practice/dbxfe-capstone-coexistence`; the
data pack lives under `content/exercises/capstone-coexistence/`.

Everything in the engagement is fictional or hypothetical. No workspace,
cloud account, paid service or model call is needed, and none is executed.

## What makes this one different

The first capstone (Cinderline) builds one bounded pilot from a first
conversation. The second builds a service-knowledge assistant with controlled
actions. This one starts with an answer already assumed by executives and
tests it against contracts, dependencies, security boundaries, residency,
latency, a blackout and a budget ceiling. The best submission is not a
migration plan for everything; it is a segmented decision in which some
workloads stay, some coexist through governed sharing, some migrate in waves,
and some are deliberately not migrated yet, with a dated condition for
reconsidering each.

## Stages

1. **Read the brief and open the disclosures deliberately.** The brief is
   missing most of what you need on purpose. Each of the eight stakeholder
   disclosures changes something: a contract date, an undocumented
   dependency, a security condition, a residency rule that covers metadata, a
   budget ceiling, a BI team's parity rule, the real latency need, and what the
   CIO would accept. Record what each one changed and what is still unknown.
2. **Segment the workloads.** Place all 26 inventory rows using
   `workload-segmentation.md`. Name the driver for each placement and the
   evidence it needs. Add the disclosed dependencies to `dependencies.csv`
   marked as disclosed.
3. **Fill the three-cloud matrix honestly.** Every cell starts as
   "unknown — needs verification". Source what you can from each cloud's own
   current documentation; leave the rest marked and turn them into open
   questions with owners. A cell filled from memory is still unknown.
4. **Decide sharing or federation versus movement** for the four cross-estate
   datasets, each with recipient, revocation, freshness, cost and failure
   behaviour.
5. **Design security and operations:** three identity boundaries, the
   security objection met without cross-estate group membership, a residency
   control that covers metadata, audit evidence, owners and runbook entries.
6. **Reconcile.** The two totals files disagree. Find both causes, state the
   corrected totals, and define the parallel-run gate before you read the
   worked answer.
7. **Plan wave 1's cutover and rollback** inside the quarter, around the
   blackout and the notice date, with a rehearsal and a rollback owner.
8. **Complete the cost worksheet** as a range against the ceiling, with
   currency, period, units and exclusions, and no real prices or savings
   claims.
9. **Write both readouts and the decision record** from the templates, with a
   concise presentation sequence and a section on what the evidence does not
   justify.
10. **Reveal the model and self-assess** against the seven rubric dimensions.
    A different path is not wrong if its unknowns and conditions are as
    explicit.

## Supporting modules

- [Architecture reasoning and migration decisions](#/module/dbxfe-m08): two
  defensible architectures, the decision not to migrate yet, reversible
  migration, reconciliation and rollback.
- [Warehouse and distributed-platform migrations](#/module/dbxfe-warehouse-migration):
  inventory, workload segmentation, waves, dependency mapping, BI continuity.
- [Sharing, federation and interoperability](#/module/dbxfe-sharing):
  governed sharing versus federation versus movement; recipients, revocation,
  freshness, cost and failure behaviour.
- [AWS](#/module/dbxfe-aws), [Azure](#/module/dbxfe-azure) and
  [Google Cloud](#/module/dbxfe-gcp) deployment and network boundaries: the
  questions matrix and why each column is sourced separately.
- [Unity Catalog and governance responsibilities](#/module/dbxfe-m06) and
  [Identity, authorization and audit](#/module/dbxfe-identity): trust
  boundaries, least privilege, audit evidence.
- [Compute choices, cost and FinOps reasoning](#/module/dbxfe-finops): the
  sensitivity worksheet, exclusions, no invented discounts.
- [Business intelligence and semantic delivery](#/module/dbxfe-bi): what the
  BI team's parity rule protects.
- [Production operations, observability and recovery](#/module/dbxfe-operations):
  runbooks, owners, recovery objectives.
- [Discovery and qualification](#/module/dbxfe-m02),
  [Competition, coexistence and business value](#/module/dbxfe-m11) and
  [Execution, written communication and capstones](#/module/dbxfe-m12):
  missing information, objections as information, executive and technical
  writing.

## Supporting labs and field guides

Labs: L24 migration reconciliation (`lab-l24-migration-reconciliation`), L15
three-cloud diagnosis (`lab-l15-three-cloud-diagnosis`), L13 cost model
(`lab-l13-cost-model`), L14 governance review (`lab-l14-governance-review`).
Field guides: FG04 architecture decision, FG15 sharing/federation choice,
FG21 migration inventory, FG22 reconciliation, FG23 cutover and rollback,
FG28 cost/value model, FG29 alternatives memo, FG30 executive readout, FG31
escalation packet, FG32 handoff and adoption plan, FG02 stakeholder map and
FG03 requirements contract.

## How the pack is used

`inventory.csv` and `dependencies.csv` are the facts you start from and are
intentionally incomplete. `workload-segmentation.md` is the worksheet you
complete. `three-cloud-questions.md` is a template whose cells you either
source or leave marked. The `reconciliation/` folder is a fixture with a
worked answer to read only after your attempt. `cost-sensitivity.md` gives
hypothetical inputs and a formula; change one input at a time. The
`templates/` folder gives the structures for the three written outputs. The
pack creates nothing to clean up.

## Boundaries

The self-assessment is educational reflection, not an independent review, a
credential or a readiness measure. The pack asserts no product availability,
price, benchmark or vendor comparison; where a real fact belongs, the honest
entry is "check current documentation" with a source you would cite.
