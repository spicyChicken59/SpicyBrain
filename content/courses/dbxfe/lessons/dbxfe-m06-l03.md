<!-- section:why -->

The customer asks, “Does all processing happen in our AWS account?” A one-size-fits-all answer would misrepresent the deployment choices.

<!-- section:understand -->

A **trust boundary** marks a change in who operates resources or controls access. On AWS, Databricks classic compute runs in the customer's AWS account, while serverless compute runs in a Databricks-managed compute plane. The control plane and customer data resources are separate parts of the architecture. Draw the actual chosen model rather than combining their boundaries into a reassuring but inaccurate picture.

Network reachability and data authorization are independent. A principal can have permission to query a table while a required connection is blocked; a reachable endpoint can still deny the operation. Discover both.

For fictional Cinderline, the source database is restricted, the data classification is not yet confirmed, and the region has not been selected. Those are design inputs. Ask which resources must remain private, who controls DNS and egress, which identities are used, and what security review accepts the path. Bring the specialist in before describing a specific private-connectivity feature as available.

<!-- section:see -->

The schematic shows two **alternative** compute paths, not a recommendation to deploy both. Classic uses a customer-account compute boundary; serverless uses a Databricks-managed boundary. Both need an approved path to customer resources and an authorized identity.

**Fictional discovery example:** security prohibits an unreviewed outbound path from the source. That does not prove either option impossible. It creates a specific feasibility question: which supported path in the intended region satisfies the restriction, with whose approval and operating responsibility?

<!-- section:deeper -->

AWS serverless networking uses regional account-level network connectivity configurations for relevant connectivity management. Feature availability, previews, permitted endpoints, and charging conditions vary; the current source includes availability caveats. This lesson intentionally does not prescribe an endpoint configuration. Classic networking has its own configuration model. Azure and GCP details are not taught as equivalents here because their corresponding setup requirements have not been reviewed for this course.

<!-- section:customer -->

For a security architect: “There are different resource boundaries for classic and serverless compute. We will show the selected AWS model and verify the exact resource path, identity, region, and availability before calling it compliant with your requirements.”

<!-- section:try -->

List six questions needed to validate Cinderline's restricted source path. Include at least one question each about data sensitivity, identities, region, network access, operations, and feature availability.

<!-- section:revisit -->

Ask: Which fields and classifications may be copied? Which human and workload identities act at each step? Which AWS region and resource locations apply? Which ingress/egress and private-access policies must hold? Who owns DNS, firewall, credentials, and incident response? Which supported product features and entitlements satisfy this exact path today?

Document the answers and unresolved conditions with the security specialist and customer owner. Do not mark a generic diagram as an approved network design. An architectural explanation is preparation for validation, not a substitute for it.
