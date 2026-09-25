<!-- section:why -->

A customer leaves a call expecting a security answer and a migration plan. Three teammates think someone else owns the follow-up. Prevent that failure by making contributions, ownership, and acceptance explicit.

<!-- section:understand -->

An **owner** is the person accountable for moving a defined action to its next state. A **contributor** supplies expertise or work. An **acceptor** decides whether the result satisfies the need. One person may hold several roles, but leaving them unnamed creates risk.

In this course's fictional account team, the account executive coordinates commercial context; the field engineer connects technical discovery to evidence; a security specialist addresses network and identity questions; a delivery partner helps establish implementation effort. These are suggested collaboration responsibilities, not Databricks internal job definitions. Confirm how your actual team works.

A warm handoff transfers the question and its context, not just a person's email address. State what was asked, why it matters, what is known, what is still uncertain, and what response is needed by when. Ask the recipient to acknowledge ownership. The field engineer can coordinate the follow-up without pretending to own every implementation task.

<!-- section:see -->

**Fictional handoff ledger.** The customer needs a decision on a limited quality-data pilot.

| Action | Proposed owner | Contributor | Customer acceptance |
|---|---|---|---|
| Define a freshness target | Operations lead | Field engineer | Written target and measurement window |
| Review network path | Field engineer (coordinates the review) | Security specialist (feasibility analysis) | Approved path and open conditions, accepted by the customer security lead |
| Estimate migration effort | Delivery lead | Data engineer | Scope, assumptions, exclusions |

The table exposes a missing role: someone must operate the pipeline after the pilot. Add that owner before calling the plan deliverable. Notice the network row: the specialist who acknowledges the request owns that analysis as their contribution, the field engineer still owns moving the combined review forward, and only the customer security lead can accept the path.

<!-- section:deeper -->

Ownership is not the same as access. A delivery lead may own a task but still need approvals and permissions. Avoid assigning an absent teammate a deadline as if it were accepted. Use “proposed owner, pending confirmation” and escalate the dependency if it blocks a decision. Document the smallest useful handoff; copying an entire transcript can bury the actual request.

<!-- section:customer -->

For a technical lead: “I will coordinate the response. Your security lead and our specialist need to confirm the network assumptions; the delivery lead will validate implementation effort. We will return one combined view with owners and any unresolved conditions.”

<!-- section:try -->

Draft a handoff for this fictional question: “Can the quality feed use our restricted network?” You know the source is SQL Server, but cloud region, permitted egress, and source version are unknown. Name who coordinates the combined review, the specialist you are asking to contribute the feasibility analysis, who accepts the result, and the acknowledgement you need.

<!-- section:revisit -->

A strong handoff says: “Security review requested for the proposed quality-data pilot. SQL Server source is known; source version, region, permitted network paths, and data classification are still unconfirmed. Requested contributor: network specialist, please confirm you can take the feasibility analysis and list the minimum details you need. I will coordinate the combined response as the field engineer. The customer security lead will accept or reject the resulting path and its assumptions before we include it in the pilot plan.”

This is better than forwarding “please advise” because it preserves the decision, the gaps, and who accepts the answer. It also avoids treating an unconfirmed assignment as a commitment.
