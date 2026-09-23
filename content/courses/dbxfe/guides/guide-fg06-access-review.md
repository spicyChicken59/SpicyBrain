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

Reviewed on synthetic objects in a test catalog. Real-data objects are not yet created, so every result below must be repeated once they are; this review establishes the design and the test method, not the production state.

#### Principals

| Principal | Work it does | Type |
|---|---|---|
| `north-reporting-analysts` | Read the published daily rate and its exclusion counts | Group of human users |
| `quality-stewards` | Read quarantined and conflicting rows; record adjudications | Group of human users |
| `svc-quality-nightly` | Read raw inspections and correction exports; write accepted and quarantine tables | Service principal |
| `platform-admins` | Own the catalog; grant privileges | Group; excluded from data reads in this design |
| `test-outsider` | None | Test user in no pilot group |

#### Objects

Catalog `quality_pilot`; schemas `raw`, `accepted`, `quarantine`; tables `raw.inspections`, `raw.corrections`, `accepted.daily_line_rate`, `quarantine.conflicts`; one SQL warehouse for reporting; one job compute for the nightly run.

#### Matrix, expected outcomes

| Principal | Object | Action | Expected | Reason |
|---|---|---|---|---|
| reporting analysts | `accepted.daily_line_rate` | SELECT | Allow | The published report |
| reporting analysts | `raw.inspections` | SELECT | Deny | Raw rows carry fields not yet classified |
| reporting analysts | `quarantine.conflicts` | SELECT | Deny | Conflicts are the steward's to adjudicate |
| reporting analysts | `accepted.daily_line_rate` | MODIFY | Deny | Nobody edits the published rate by hand |
| quality stewards | `quarantine.conflicts` | SELECT | Allow | Adjudication |
| quality stewards | `raw.inspections` | SELECT | Allow, provisional | Needed to adjudicate; the security lead must confirm field classification |
| quality stewards | `accepted.daily_line_rate` | MODIFY | Deny | Adjudications flow through the pipeline, not manual edits |
| nightly service principal | `raw.*` | SELECT | Allow | Its input |
| nightly service principal | `accepted.*`, `quarantine.*` | MODIFY | Allow | Its output |
| nightly service principal | catalog `quality_pilot` | Grant or own | Deny | A pipeline does not administer its own catalog |
| test outsider | any table | SELECT | Deny | Not in any group |
| every principal above | reporting warehouse | Use | Allow for analysts and stewards; deny for the service principal, which uses job compute |

Every allow on a table implies USE CATALOG and USE SCHEMA on its parents; those were granted to the group, not to individuals.

#### Negative tests executed

| Test | Identity used | Result | Evidence |
|---|---|---|---|
| Read raw inspections | Test analyst in `north-reporting-analysts` | Denied; error names the identity and the missing SELECT | Captured error text |
| Read quarantine | Same | Denied | Captured error text |
| Modify the published rate | Same | Denied | Captured error text |
| Own the catalog | `svc-quality-nightly` | Denied | Captured error text |
| Read the published rate | `test-outsider` | Denied | Captured error text |
| Read raw inspections | Test steward | Allowed, 5 rows | Provisional; flagged for the security lead |

#### Positive tests executed

The test analyst read the published rate (five rows, one per test day). The service principal's nightly job wrote both output tables and read nothing outside `raw`. No test used an administrator identity.

#### Gaps

Row-level separation between plants is not tested because only one plant is in scope; when a second joins, the analysts' allow must be re-examined with a row filter or per-plant views. Audit-log review is not tested; the security lead has not said which events they want retained. The stewards' raw read is provisional.

#### Conclusion

The design gives each principal only its work and every deny that matters has been exercised with error text captured. It is not approved: one allow is provisional and two cells are untested, and everything was run on synthetic objects. Send the matrix and the captured errors to the security lead with the three gaps named, and repeat the whole run on the real objects once they exist.

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
