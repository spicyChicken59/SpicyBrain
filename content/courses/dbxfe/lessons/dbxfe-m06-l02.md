<!-- section:why -->

A demo only works under an administrator account. Before calling access validated, reproduce the intended user's path and permissions.

<!-- section:understand -->

**Identity** establishes who or what is acting. A **principal** may be a user, group, or service principal. **Authorization** determines what that principal may do. Ownership and administration can permit broader actions than ordinary use, so an administrator's successful query does not demonstrate least-privilege consumer access.

For a Unity Catalog table under the documented privilege model, the reader needs the relevant SELECT privilege plus usage privileges on its catalog and schema. That is an object-access requirement; it does not establish a reachable network path or the complete workspace/compute setup.

In fictional Cinderline, analysts should read accepted reporting data without automatically gaining raw sensitive input or write access. A workload identity that builds accepted tables may need different privileges from a dashboard viewer. Grant to appropriate groups where the customer's identity design supports it, and test both allowed and denied operations with representative identities.

<!-- section:see -->

**Fictional access matrix; proposed, not configured.**

| Principal | Required work | Intentionally not required |
|---|---|---|
| Reporting analysts | Read approved daily metric | Modify raw inspections |
| Pipeline identity | Read approved source; write accepted output | Administer the entire account |
| Quality steward | Inspect quarantined records under policy | Unrestricted access to unrelated data |

This matrix is a starting point. Translate it into exact privileges and test identities only after confirming object types and the customer's policies.

<!-- section:deeper -->

Scope sharing as a separate decision: recipient, data subset, permitted use, freshness, revocation, and audit expectations. Do not infer that an internal group grant is automatically an external-sharing setup. The exact product path and available sharing features require current documentation. Avoid copying a broad ALL PRIVILEGES grant from a tutorial into a customer plan. Review inherited privileges and ownership that could make a negative test misleading.

<!-- section:customer -->

For security: “We will define the work each identity needs, grant the smallest supported scope, and test allowed and denied actions. A successful administrator demo is only a preliminary functional check, not evidence that the analyst's access is correct.”

<!-- section:try -->

A fictional analyst has SELECT on the reporting table but cannot query it. Write a diagnosis checklist that includes catalog/schema usage, execution access, identity, network path, and evidence collection without proposing blanket admin access.

<!-- section:revisit -->

Confirm the effective identity and exact error, then inspect SELECT and the parent USE CATALOG/USE SCHEMA privileges, inherited permissions, workspace/compute access, and the relevant network path. Test the intended action with the intended principal and collect a public-safe error description. Ask the platform or security owner to validate the missing boundary.

Do not grant account-wide administration merely to remove the error. A narrow failed test is useful evidence. After correction, test that the analyst can read the permitted metric and still cannot modify the raw input.
