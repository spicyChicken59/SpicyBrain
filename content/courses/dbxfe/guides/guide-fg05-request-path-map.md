<!-- section:action -->

Draw the map for one concrete request, such as "an analyst runs the morning defect-rate query," before you draw anything general. A map of "the platform" hides the boundary that will fail.

1. **Name the request and the identity making it**: a person through single sign-on, a workload through a service principal or a cloud identity. Write which one, because the permissions that apply are theirs.
2. **Walk the request through five responsibilities in order**: authoring surface, control plane (authentication, authorization, scheduling), compute (where the engine runs and in whose cloud account), storage (which bucket or container, authorized through which credential), and result delivery back to the surface.
3. **At each hop write who owns it**: the customer's cloud account, the platform provider, or the customer's identity provider. Draw the trust boundary where ownership changes.
4. **Mark the cloud-specific pieces with their real names** only where you have confirmed them; otherwise write "not confirmed." An identity model, a network construct and a storage service differ by cloud and are not interchangeable.
5. **For each hop, state the failure you would see there** and how you would tell a permission failure (a definite denial with an identity in it) from a connectivity failure (a timeout or an unresolved name).
6. **List the evidence that confirms the map**: a successful run as the intended identity, a denied run, and the network path as the customer's network owner describes it.

Go deeper: [platform, workspace and compute](#/module/dbxfe-m03), [cloud responsibilities and request paths](#/lesson/dbxfe-cloud-bridge), [draw the cloud and trust boundaries](#/lesson/dbxfe-m06-l03), and the cloud-specific modules for [AWS](#/module/dbxfe-aws), [Azure](#/module/dbxfe-azure) and [Google Cloud](#/module/dbxfe-gcp).

<!-- section:example -->

### Request-path map: Cinderline Components (fictional), morning defect-rate query

Educational cloud choice: AWS, as the capstone assumes; nothing below has been provisioned. Items marked "not confirmed" are what the security lead's review must establish.

#### The request

A reporting analyst at the North plant opens the morning dashboard at 7:40 a.m. and the dashboard runs the accepted defect-rate query for the previous business day.

#### The identity

A human user, authenticated through the customer's identity provider by single sign-on. The permissions that apply are the analyst's, through the reporting-analysts group. The nightly job that produced the table ran as a service principal: a different request path with different permissions, mapped separately.

#### Hops, owners and boundaries

| Hop | What happens | Who owns it | Trust boundary crossed | Confirmed or not |
|---|---|---|---|---|
| 1. Authoring surface | The dashboard issues the saved query | Customer workspace configuration | None | Query saved; the plant-to-workspace route not confirmed |
| 2. Control plane | The identity is verified; the workspace checks the analyst may use the SQL warehouse; the catalog checks USE CATALOG, USE SCHEMA and SELECT on the accepted table | Platform provider's control plane, using the customer's identity provider | Customer identity provider to provider control plane | Group, catalog and schema confirmed |
| 3. Compute | The query runs on a SQL warehouse. If classic, the engine runs in the customer's AWS account inside a VPC the customer configured; if serverless, in provider-managed infrastructure with a connectivity pattern not yet agreed | Customer account (classic) or provider (serverless); not confirmed which | Control plane to compute plane | Not confirmed: classic or serverless, region, private connectivity |
| 4. Storage | The engine reads Delta files from an S3 bucket through a storage credential backed by an IAM role, scoped to an external location for the accepted schema | Customer's AWS account; role trust configured by the customer | Compute plane to customer storage | Not confirmed: bucket and role |
| 5. Result delivery | Rows return to the dashboard in the browser | Provider, then the analyst's network | Compute plane back to the surface | Not confirmed: as hop 1 |

The security lead has said that a "classic" or "serverless" label alone does not satisfy them, which is why hop 3 is drawn with both possibilities and neither chosen.

#### Failures you would see at each hop

Hop 1: the dashboard reports a missing table because its saved query still names a renamed one; the fix is the query, not a grant. Hop 2, permission: a definite error naming the analyst and the missing privilege; the fix is a grant, never an administrator token. Hop 3, connectivity: the warehouse fails to start or the query never begins because the subnet has no route or the outbound rule blocks the control plane; a grant cannot fix that. Hop 4, permission: the query starts and fails on the bucket with an access error naming the role; the IAM policy or the external location is wrong. Hop 4, connectivity: a timeout reaching the storage endpoint, typically a private-endpoint or DNS matter for the network owner. Hop 5: the query completes but the browser shows nothing, usually a corporate proxy, not the platform.

#### Evidence that would confirm the map

A successful run of the saved query as a test analyst identity with the group's privileges and nothing more. A deliberately denied run as an identity outside the group, with the error text captured. The network owner's written description of the routes from plant workstations to the workspace and from compute to storage. Until those three exist, this map is a hypothesis for the review.

#### Conclusion

Complete enough to review, not to build on. Hops 3 and 4 carry most unconfirmed items, and hop 3's owner is itself unconfirmed: the customer's account if classic, the provider if serverless. The plant-to-workspace route for hops 1 and 5 is unconfirmed too, so the next conversation covers both paths with the security lead and the network owner, with this drawing in front of them.

<!-- section:template -->

### Request-path map

#### The request

- One concrete request: who or what issues it, from where, for what result.

#### The identity

- Human or workload; how it authenticates; whose permissions apply; the group or role that carries them.

#### Hops, owners and boundaries

| Hop | What happens here | Who owns this piece (customer account, provider, identity provider) | Trust boundary crossed | Confirmed or not |
|---|---|---|---|---|
| Authoring surface | | | | |
| Control plane: authentication, authorization, scheduling | | | | |
| Compute: engine location, cloud account, network | | | | |
| Storage: service, container, credential, scope | | | | |
| Result delivery | | | | |

#### Failures per hop

- For each hop: what a permission failure looks like there, what a connectivity failure looks like, and who fixes each.

#### Cloud-specific names

- The identity, network and storage constructs by their real names for this cloud, each marked confirmed or not confirmed; never carried over from another cloud.

#### Evidence that confirms the map

- The allowed run, the denied run, and the network owner's description of the route.

<!-- section:limits -->

The map explains one request's path and who owns each piece; it does not establish that any permission is granted, that any route exists, or that a workspace is configured as drawn. It is not a security review, though it is the drawing a reviewer needs, and it is not a network design. Cloud constructs differ, so a map drawn for one cloud says nothing about another, and anything marked "not confirmed" stays a hypothesis until an owner confirms it in writing or a test reproduces it. Escalate when the customer cannot say who owns a hop, when the network owner and the security lead describe different routes, or when a failure cannot be classified as permission or connectivity after one test as the intended identity.
