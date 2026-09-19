<!-- section:why -->

Two designs can both be technically possible. You need to explain why one is preferable under current constraints and what evidence would change your recommendation.

<!-- section:understand -->

A tradeoff is a choice between outcomes that cannot all be maximized under the same constraints. Lower latency may require more continuous operation; fewer moving parts may limit flexibility; a new standard may improve consistency while creating migration work. Name the requirement that justifies each cost.

For fictional Cinderline, compare a scheduled quality feed with an incremental low-latency path. If the decision occurs at shift change and the source approves corrections in batches, scheduled processing may be sufficient. If operators must react during the shift and valid source updates are available continuously, incremental processing may become more useful. Neither recommendation should be independent of source timing and operational capacity.

A meaningful alternative differs in consequences, not just logo placement. Include retain/improve-current-state, staged coexistence, and the proposed target where relevant. Document why an option was not selected and the condition that would cause you to reconsider.

<!-- section:see -->

**Fictional comparison, no measured performance claims.**

| Criterion | Scheduled feed | Incremental path |
|---|---|---|
| Decision timing | Candidate for shift-change need | Candidate for within-shift need |
| Source requirement | Approved periodic extract | Reliable change semantics and allowed access |
| Operations | Bounded runs and reruns | Ongoing state, lag, and recovery monitoring |
| Evidence needed | Completion before decision; reconciliation | Lag distribution, correctness, and recovery |

The decision criteria come before the preferred design. Unknowns are not silently scored as wins.

<!-- section:deeper -->

Architecture reliability includes recovery from failure, not merely steady-state availability. Ask what fails, how the failure is detected, what can be lost, and how service resumes. Interoperability also needs explicit checks: formats, table features, readers/writers, interfaces, and ownership across systems. Cost should include migration and ongoing operation. Avoid a precise weighted score when the inputs are guesses; a transparent qualitative comparison may be more honest.

<!-- section:customer -->

For a sponsor and architect: “The scheduled option may meet the shift-change need with less continuous operation. The incremental option is worth testing if decisions need fresher updates. We will compare both against agreed correctness, timing, recovery, and operating-effort criteria.”

<!-- section:try -->

Choose a provisional design when the fictional source approves corrections every four hours, the decision happens once daily, and the small team has no continuous-support rotation. Name the condition that would make you reconsider.

<!-- section:revisit -->

A scheduled feed is a reasonable provisional choice, provided it reliably finishes before the daily decision and reconciles approved corrections. It matches the current source cadence and limited operating capacity. Reconsider if the business needs within-shift decisions, the source makes timely changes available, and an appropriate operating model is established.

Do not describe the choice as universally cheaper or more reliable. Those outcomes need a measured cost and recovery basis. The recommendation is conditional on this fictional workload and can change when requirements change.
