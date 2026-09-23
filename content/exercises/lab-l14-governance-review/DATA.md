# Data dictionary and derivations — Lab L14

Every file in `fixtures/` is synthetic and authored for this lab. Cinderline
Components, its people, groups, service principals, catalogs and rows are
fictional; addresses use the reserved `example` domain. No generator and no
random seed are involved: the files are the literal inputs.

## The model's rules

These are the rules the evaluator implements and the keys were derived from.
They follow the documented Unity Catalog privilege model in simplified form.

1. **Identities.** A principal acts with its own grants and with those of every
   group that contains it, directly or through nested groups.
2. **Deny by default.** The grant table has no deny entries. A principal that
   is not in the directory is denied (`unknown-principal`), as is any request
   no check allows.
3. **Reading or writing an object** (a table or a volume) runs three checks in
   order, and the first that fails names the denial:
   USE CATALOG on the catalog (`missing-use-catalog`); USE SCHEMA granted on
   the schema or on the catalog (`missing-use-schema`); the object privilege
   granted on the object, its schema or its catalog (`missing-select`,
   `missing-modify`, `missing-read-volume`, `missing-write-volume`).
4. **Ownership.** Owning a securable counts as holding every privilege on that
   securable itself, and lets its owner grant on it. It does not cascade to
   children. An allowed request whose object privilege comes from ownership
   is reported as `owner`; one that comes from a grant as `granted`.
5. **Grant requests** (`GRANT`) are allowed only to the owner (`not-owner`
   otherwise). Real Unity Catalog also lets holders of MANAGE and metastore
   administrators grant; the model leaves them out.
6. **Row filters** keep a row when the caller belongs to a rule's group and the
   row's value is in that rule's values (`*` is every value). Several matching
   rules add up; no matching rule means no rows, and never an error.
7. **Column masks** return the stored value to members of an unmasked group and
   the replacement `[masked]` to everyone else. The column is always present.

## Files

| File | Contents |
|---|---|
| `principals.json` | 7 users, 3 service principals and 12 groups with their members; `quality-analysts` contains the two plant groups |
| `securables.json` | catalogs `quality` and `finance`, 4 schemas and 6 objects (5 tables, 1 volume), each with an owning group |
| `grants.json` | 13 grants: `principal`, `privilege`, `securable` |
| `policies.json` | the `plant_rows` and `supplier_rows` row filters and two masks on `inspector_email` |
| `tables.json` | 6 stored inspections and 5 stored supplier rejections |
| `requests.json` | Task 1: requests R01–R20 |
| `row_requests.json` | Task 2: queries V1–V5 |
| `plan_matrix.json` | Task 3: rows P1–P7 run after your plan |
| `escalation_case.json` | Task 4: Jon's denied read of `rework_costs` |
| `negative/wide_plan.json`, `negative/admin_plan.json` | two deliberately broad plans |
| `transfer/changes.json`, `transfer/requests.json` | the altered input: Maya moves to finance and the filter gains a US clause |

Group memberships after expansion: Maya → plant-eu-analysts, quality-analysts;
Jon → plant-us-analysts, quality-analysts; Ravi → quality-leads; Lena →
data-engineers; Omar → finance-owners, finance-analysts; Tess →
quality-platform-owners; Sam → platform-admins; sp-nightly-ingest →
ingest-jobs; sp-supplier-portal → supplier-portal; sp-ci-deploy → deployers.

## How each key was derived (by hand)

**`expected/decisions.json`.** R01 and R02: quality-analysts holds USE CATALOG
on `quality`, USE SCHEMA on `quality.accepted` and SELECT on the table →
allow, granted. R03: Maya passes both usage checks, but SELECT is granted only
on `inspections` → deny, missing-select. R04: quality-leads holds SELECT on the
schema, which reaches `rework_costs` → allow, granted. R05: Omar's groups hold
nothing on `quality` → missing-use-catalog. R06: no MODIFY for analysts →
missing-modify. R07: ingest-jobs holds all three for MODIFY → allow. R08:
ingest-jobs has USE SCHEMA only on `quality.raw` → missing-use-schema. R09:
data-engineers holds USE CATALOG, owns `quality.raw` (USE SCHEMA by ownership)
and owns the table → allow, owner. R10: data-engineers has no usage on
`quality.accepted` → missing-use-schema. R11: analysts lack USE SCHEMA on
`quality.raw` → missing-use-schema. R12: ingest-jobs passes both usage checks
but holds no READ VOLUME → missing-read-volume. R13: ownership of schema and
volume → allow, owner. R14: Jon is not in quality-platform-owners → not-owner.
R15: Tess is → allow, owner. R16: nothing on `finance` → missing-use-catalog.
R17: supplier-portal holds nothing yet → missing-use-catalog. R18: Priya is
not in the directory → unknown-principal. R19: analysts lack USE SCHEMA on
`quality.shared` → missing-use-schema. R20: quality-leads holds all three →
allow, granted.

**`expected/visible.json`.** V1: Maya matches the plant-eu-analysts rule
(EU-1, EU-2), so I-101, I-103 and I-105 remain; she is not a quality lead, so
all three emails read `[masked]`. V2: Jon's groups match no rule → allowed,
zero rows. V3: Ravi matches `*` and is unmasked → all six rows as stored. V4:
Omar is denied before any filter runs → missing-use-catalog, no rows. V5: Ravi
on the rejections table → all five rows as stored.

**`expected/plan_matrix.json`.** With USE CATALOG on `quality`, USE SCHEMA on
`quality.shared` and SELECT on `supplier_rejections` for supplier-portal: P1
allow; P2 and P4 missing-use-schema (no usage on `accepted` or `raw`); P3
missing-modify; P5 not-owner; P6 Maya missing-use-schema as before; P7 the
S-17 rows R-201 and R-203 with emails masked. A plan is judged on decision and
rows only, because a different but still narrow plan can deny for another
reason.

**`expected/negative.json`.** Wide plan (USE SCHEMA and SELECT on the whole
catalog): P2 and P4 become allowed, so those rows fail; the review rules
report `data-privilege-above-object` and `use-schema-on-catalog`. Admin plan
(portal added to quality-platform-owners): ownership of `accepted` and the
tables allows P2, P3 and P5, so those fail; P4 still fails the usage check
because data-engineers owns `quality.raw`; the rule reported is
`owner-group-membership`.

**`expected/transfer.json`.** After Maya leaves plant-eu-analysts she is no
longer in quality-analysts, and finance-analysts holds nothing on `quality` or
`finance` → T1 and T5 missing-use-catalog. Jon is unchanged for T2; the new
clause admits US-1 and US-2, so T3 returns I-102, I-104 and I-106 masked. T4:
Ravi still sees all six rows. The grant table is identical before and after.

**`expected/escalation.json`.** Jon's request is denied with missing-select
(R03's shape for another analyst); the owning group is quality-platform-owners;
the only privilege to request is SELECT on `rework_costs`; any valid proposal
must turn the request into an allow.
