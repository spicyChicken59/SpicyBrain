<!-- section:action -->

Run the review before real data is loaded and again before anyone outside the build team is given access. A review that consists of an administrator's successful query proves nothing about the analyst.

1. **List the principals by the work they do**, not by who they are: reporting analysts, the pipeline's workload identity, the quality steward, the platform administrator. Use groups where the customer's identity design supports them.
2. **List the objects by hierarchy**: catalog, schema, table, view, volume, and the compute each principal needs to reach them. Include the raw and quarantine objects, not only the published ones.
3. **Fill the matrix with an expected outcome per principal, object and action**: allow or deny. Every allow needs a reason tied to the work; every principal needs at least one deny that matters.
4. **Write the negative tests first**: the analyst attempting to read raw inspections, the pipeline identity attempting to administer the catalog, an identity outside every group attempting the published table. A denied test with its error text is the evidence the security lead asked for.
5. **Execute with representative identities**, never with your own, and record the exact error for each deny and the row count for each allow.
6. **Record gaps as gaps**: an untested cell is "not tested," not "passed."

Go deeper: [Unity Catalog and governance](#/module/dbxfe-m06), [design least-privilege access](#/lesson/dbxfe-m06-l02), [identity, authorization and audit](#/module/dbxfe-identity) for workload identities and audit events, and [sharing and federation](#/module/dbxfe-sharing) when a principal is outside the organisation.

<!-- section:example -->

### Access review: Cinderline Components (fictional), North plant pilot

Run on synthetic objects in a test catalog; every result must be repeated on real objects once they exist, so this establishes the design and the test method, not the production state.

#### Principals

| Principal | Work it does | Type |
|---|---|---|
| `north-reporting-analysts` | Read the published rate and exclusion counts | Group of human users |
| `quality-stewards` | Read quarantine; record adjudications | Group of human users |
| `svc-quality-nightly` | Read raw tables; write accepted and quarantine tables | Service principal |
| `platform-admins` | Own the catalog; grant privileges | Group; no data reads, by policy |
| `test-outsider` | None | Test user in no pilot group |

#### Objects

Catalog `quality_pilot`; schemas `raw`, `accepted`, `quarantine`; tables `raw.inspections`, `raw.corrections`, `accepted.daily_line_rate`, `quarantine.conflicts`; a reporting SQL warehouse; job compute for the nightly run.

#### Matrix, expected outcomes

| Principal | Object | Action | Expected | Reason |
|---|---|---|---|---|
| reporting analysts | `accepted.daily_line_rate` | SELECT | Allow | The published report |
| reporting analysts | `raw.inspections` | SELECT | Deny | Fields not yet classified |
| reporting analysts | `quarantine.conflicts` | SELECT | Deny | The stewards' to adjudicate |
| reporting analysts | `accepted.daily_line_rate` | MODIFY | Deny | No hand edits |
| quality stewards | `quarantine.conflicts` | SELECT | Allow | Adjudication |
| quality stewards | `raw.inspections` | SELECT | Allow, provisional | Adjudication; field classification unconfirmed |
| quality stewards | `accepted.daily_line_rate` | MODIFY | Deny | Adjudications flow through the pipeline |
| nightly service principal | `raw.*` | SELECT | Allow | Its input |
| nightly service principal | `accepted.*`, `quarantine.*` | MODIFY | Allow | Its output |
| nightly service principal | catalog `quality_pilot` | Grant or own | Deny | A pipeline does not administer its catalog |
| platform admins | `raw.inspections` | SELECT | Deny by policy | An owner can grant itself SELECT; see gaps |
| test outsider | any table | SELECT | Deny | Not in any group |
| every principal above | reporting warehouse | Use | Allow analysts and stewards; deny the service principal | The nightly job uses job compute |

Each table allow implies USE CATALOG and USE SCHEMA on its parents, granted to groups and the service principal, never to individuals.

#### Negative tests executed

| Test | Identity used | Result | Evidence |
|---|---|---|---|
| Read raw inspections | Test analyst | Denied; error names the identity and the missing SELECT | Error text |
| Read quarantine | Same | Denied | Error text |
| Modify the published rate | Same | Denied | Error text |
| Modify the published rate | Test steward | Denied | Error text |
| Own the catalog | `svc-quality-nightly` | Denied | Error text |
| Read the published rate | `test-outsider` | Denied | Error text |

#### Positive tests executed

The test analyst read the published rate (five rows: one synthetic line, five test days). The test steward read `quarantine.conflicts`, and raw inspections provisionally, flagged for the security lead. The nightly job wrote both output tables and read nothing outside `raw`. No test used an administrator identity.

#### Gaps

Not tested: the service principal's use of the reporting warehouse; the outsider against tables other than the published rate. The platform-admins deny is policy only; the proposed compensating control (an owner group with no data consumers, plus review of grant events) needs checking against current documentation. Row-level separation between plants is untested with one plant in scope; a second plant needs a row filter or per-plant views. Audit-log review is not tested; the security lead has not said which events to retain.

#### Conclusion

Six of eight expected denies were exercised with error text captured, the outsider's only against the published rate; the other two are listed under gaps. Not approved: one allow is provisional, the gaps are open, and everything ran on synthetic objects. Send the matrix, errors and gaps to the security lead; repeat the run on real objects once they exist.

<!-- section:template -->

### Access review

#### Scope and state

- Which catalog, schemas and objects; whether they are synthetic or real; the date and who executed the tests.

#### Principals

| Principal (group or service identity) | Work it does | Type (human group, service principal, test user) |
|---|---|---|

#### Objects

- Catalog, schemas, tables, views, volumes and compute in scope, including raw and quarantine objects.

#### Matrix, expected outcomes

| Principal | Object | Action | Expected (allow or deny) | Reason tied to the work |
|---|---|---|---|---|

#### Negative tests

| Test | Identity used (never your own) | Result | Evidence captured (error text, event) |
|---|---|---|---|

#### Positive tests

- Each expected allow that was exercised: identity, action, row count or effect, evidence.

#### Gaps

- Every cell not tested, every provisional allow, and what would close each.

#### Reviewer

- Who receives the matrix and evidence, what they must confirm, and what changes once real objects exist.

<!-- section:limits -->

The review establishes that a set of privileges behaves as expected for the identities tested on the objects tested at the time of testing; it does not establish that the privilege model is complete, that inherited or ownership rights are absent elsewhere, or that a network path exists for any principal. A matrix on paper is a design; only executed tests are evidence, and tests on synthetic objects say nothing about real ones until repeated. It is not a compliance assessment and does not classify data. Escalate when a test must be run as an administrator to succeed, when a required deny cannot be produced, when the customer proposes a broad grant to clear an error, or when field classification is unknown for an object someone needs to read.
