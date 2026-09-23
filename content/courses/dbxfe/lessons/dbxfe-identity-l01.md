<!-- section:dbxfe-identity-l01-outcome -->

After this lesson you can answer three questions about any Databricks request at Cinderline: who authenticated, whose permissions applied, and where it could fail. You can tell users, service principals and groups apart; choose between OAuth user-to-machine, machine-to-machine and workload identity federation; keep a secret out of code; predict what a row filter and a column mask return; and read audit rows as evidence after a leaked token. The practice is a threat and access review with a narrow permission plan and a test matrix.

<!-- section:dbxfe-identity-l01-start -->

This lesson builds on the Unity Catalog module and does not repeat it. [Unity Catalog names and basic access](#/lesson/dbxfe-m06-l01) teaches three-part names and the three grants a reader needs, and [Design least-privilege access](#/lesson/dbxfe-m06-l02) teaches testing the identity that will do the work, including a denial. [Cloud responsibilities and request paths](#/lesson/dbxfe-cloud-bridge) separates identity, authorization and reachability on one request. Here the focus moves along the path: how a principal proves who it is, whose identity a job carries, what filters and masks do to a result, and what the audit log can prove afterwards.

<!-- section:dbxfe-identity-l01-identities -->

**Principals.** A user is a person identified by an email address. A service principal is an identity for jobs, scripts, apps and CI/CD, identified by an application ID. A group collects users, service principals and other groups, and its members inherit its grants. The Databricks SDK recommends running production jobs as service principals, so interactive users need no write privilege in production, and assigning workspace access and Unity Catalog policies to groups rather than to people.

**Provisioning and federation.** SCIM provisioning copies users, groups and memberships from the identity provider into the Databricks account and removes a user deprovisioned there. Identity federation keeps those identities at account level and assigns them to workspaces as USER or ADMIN. Token federation lets the account accept tokens from a trusted identity provider and exchange them for Databricks tokens. Only SCIM creates or removes principals, and none of the three grants a privilege.

<!-- section:dbxfe-identity-l01-oauth -->

| Flow | For | What the caller holds |
|---|---|---|
| OAuth U2M | a person using a tool | cached tokens after a browser sign-in |
| OAuth M2M | a service principal | client ID and an OAuth secret |
| Workload identity federation | a CI or runtime workload | nothing stored; a token from its own platform |
| Personal access token | integrations without OAuth | a long-lived bearer token |

In U2M, a tool opens the browser, receives an authorization code on a localhost listener, and exchanges it with a PKCE verifier for access and refresh tokens; every call acts as the person. In M2M, the client-credentials grant trades the service principal's client ID and secret for an access token, and a bad secret fails at the token endpoint before any object is named. In federation, a policy accepts a token only if its issuer, subject and audience match, so a pull-request run cannot act as the deploy principal. Databricks recommends OAuth over personal access tokens and federation over stored secrets whenever possible.

Tokens are bearer credentials: whoever holds one is its owner to the API. They leak through committed notebooks, job output, URLs and chat, and a password change does not revoke them; only revocation or expiry does.

<!-- section:dbxfe-identity-l01-secrets -->

A secret scope's ACL grants READ, WRITE or MANAGE. Code reads a value at run time, and the permission checked is that of the identity running the command:

```python
# Synthetic teaching example; not executed.
password = dbutils.secrets.get(scope="supplier-sftp", key="password")
```

Grant READ to the group of the workload's service principal, MANAGE to a few owners, and nothing to `users`. Databricks redacts recognised values in notebook output, but its SDK states that a permitted reader can still reveal a secret, so the ACL is the control. One scope per integration keeps READ on one credential from exposing another.

<!-- section:dbxfe-identity-l01-runas -->

**Whose permissions.** Interactive queries act as their user. A job acts as its run-as identity, and as its creator when none is set. When Ravi triggers the nightly job, the write is checked against sp-nightly-ingest, not Ravi, so permission to trigger or edit a job that runs as a service principal is indirect access to that principal's grants.

**Where it fails.** An authentication error names no object. A workspace refusal comes before any catalog check. PERMISSION_DENIED names the missing privilege and securable. A row filter or column mask raises nothing: fewer rows or replaced values come back. A secret ACL refuses the secrets call, and an unreachable path times out. Reproduce as the acting principal, fix one layer, and rerun one request that must still fail.

<!-- section:dbxfe-identity-l01-policies -->

A row filter and a column mask are SQL functions attached to a table and evaluated for each caller:

```sql
-- Synthetic teaching example; not executed.
ALTER TABLE quality.accepted.inspections
  SET ROW FILTER quality.governance.plant_rows ON (plant);
ALTER TABLE quality.accepted.inspections
  ALTER COLUMN inspector_email SET MASK quality.governance.inspector_email_mask;
```

For four stored inspections, Maya in plant-eu-analysts receives the two EU rows with masked emails, Ravi in quality-leads receives all four unmasked, and Jon, whom no clause admits, receives zero rows and no error. An attribute-based access control (ABAC) policy moves the same functions up a level: defined on a catalog, schema or table, it matches columns by governance tag and applies to everything beneath, so a new tagged table is covered and an untagged column is not. Creating one needs MANAGE; verify its status and supported compute for the workspace first.

<!-- section:dbxfe-identity-l01-audit -->

The audit log system table, system.access.audit, ties each event to a time, a service and action, the acting identity, request parameters, a source address and a response. An account admin enables the access schema; grant reading it to a security group only. On AWS, audit logs can also be delivered as JSON files to the account's bucket, usually within minutes and sometimes later, so record when each query ran.

After a token exposure: revoke first; fix the exposure window from the moment the token could be copied to its revocation; query the owner's rows inside that window for unfamiliar addresses and actions; list everything the identity could reach; rotate every secret it could read; then remove the cause. Audit rows show what an identity did, not what anyone did with the data afterwards.

<!-- section:dbxfe-identity-l01-example -->

The portal must show supplier S-17 its own rejected inspections.

| Principal | Securable | Privilege | Reason |
|---|---|---|---|
| supplier-portal group | catalog quality | USE CATALOG | reach the schema |
| supplier-portal group | schema quality.shared | USE SCHEMA | reach the table |
| supplier-portal group | table supplier_rejections | SELECT | the only data needed |

sp-supplier-portal belongs to supplier-portal and authenticates with workload identity federation, or M2M where federation is unavailable. The table carries a row filter for S-17 and a mask on inspector emails.

The test matrix, run as sp-supplier-portal and never as an administrator: SELECT on supplier_rejections is allowed; SELECT on quality.accepted.inspections is denied; MODIFY on supplier_rejections is denied; rows for supplier S-22 number zero; inspector emails are masked; Maya's SELECT on supplier_rejections is denied. A plan granting SELECT on the whole catalog passes every row except the second: the must-fail rows are the evidence. Requester, approving owner, applying administrator and security reviewer are four different people.

<!-- section:dbxfe-identity-l01-task -->

Cinderline adds a plant-manager dashboard and a nightly export to a logistics partner. Write the review: the principal each uses and how it authenticates, grants on the lowest securables that work, secret scope entries, the row filter or mask each needs, a test matrix with at least three must-fail rows each, who approves and applies, and the audit query that would show the export's reads last week. Mark anything you cannot verify, such as feature status or the partner's identity provider, as unknown.

<!-- section:dbxfe-identity-l01-solution -->

**Dashboard.** Plant managers sign in with U2M. An account group plant-managers, maintained by SCIM, holds USE CATALOG on quality, USE SCHEMA on quality.accepted and SELECT on inspections; the row filter gains one clause per manager group and the mask keeps inspector emails hidden. Must-fail rows: another plant's rows (zero), MODIFY on inspections (denied), anything in quality.raw (denied).

**Export.** The job runs as sp-logistics-export, whose group holds SELECT on one export table and READ on scope logistics-sftp. Must-fail rows: SELECT on inspections (denied), WRITE on the scope (denied), a plant manager reading the export table (denied).

**Duties and evidence.** The quality lead requests, the schema owner approves, a platform administrator applies, and security reviews the permission-change rows and the matrix output. Audit query: secrets getSecret rows for logistics-sftp and table reads by sp-logistics-export over seven days, grouped by day. Unknown: attribute-based policy status, the partner's transfer protocol and audit delivery delay.

<!-- section:dbxfe-identity-l01-limits -->

Running production jobs as a person; granting to users instead of groups; treating SCIM, identity federation and token federation as one thing; putting tokens or secrets in code, notebooks, URLs or chat; believing a password change or a deleted commit contains a leaked token; granting MANAGE or admin membership to clear an error; testing as an administrator; reading an empty result as a permission error; assuming an untagged column is covered by an attribute-based policy. None of this is a security certification or a compliance control, and feature status, supported compute and regional availability must be verified for the real workspace.

<!-- section:dbxfe-identity-l01-sources -->

The documentation host is blocked in this build and the build's search allowance was used up, so primary references were read in full on 23 September 2026 from Databricks-authored open-source repositories at pinned tags: the Databricks SDK for Python v0.141.0 (identity, authentication, OAuth, secrets, jobs, catalog and token modules), the Databricks Terraform provider v1.133.0 documentation and the dbt-databricks v1.12.5 row filter and column mask macros. Two documentation pages, the audit log system table reference and the row filters and column masks page, were not re-confirmed; details that rest only on them are marked where used. Nothing was executed against a workspace.

<!-- section:dbxfe-identity-l01-links -->

[Unity Catalog names and basic access](#/lesson/dbxfe-m06-l01) owns the grants this lesson assumes. [Design least-privilege access](#/lesson/dbxfe-m06-l02) owns testing the working identity. [Draw the cloud and trust boundaries](#/lesson/dbxfe-m06-l03) and the [AWS deployment module](#/module/dbxfe-aws) own the network layer that a timeout points to. The Azure and Google Cloud modules cover their own identity providers and managed identities.

<!-- section:dbxfe-identity-l01-revisit -->

Work the exercise on paper, then compare with the solution row by row, especially the must-fail rows. Review the cards after a day. Opening a section or revealing the solution records no completion; mark completion yourself when you can produce the review without notes.
