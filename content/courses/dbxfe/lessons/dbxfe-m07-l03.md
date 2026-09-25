<!-- section:why -->

A few attractive answers can hide the cases that matter most. Before a customer demo becomes a proposed deployment, decide what an acceptable answer looks like and how failures are handled.

<!-- section:understand -->

An evaluation set is a collection of representative inputs with expected behavior and a scoring method. Include ordinary questions, ambiguous questions, missing evidence, outdated documents, permission boundaries, and adversarial source content. Evaluate the whole path, not only the final sentence: what was retrieved, which identity acted, and whether a tool request was allowed.

For fictional Cinderline's read-only manual assistant, a useful answer should identify the correct machine/version, cite a permitted source, avoid unsupported operating advice, and escalate when evidence is insufficient. A correct abstention can be better than a fluent guess. Define acceptance with the relevant maintenance and security owners.

MLflow supports code-based and model-based scoring of traces. Those mechanisms can help organize evidence, but a model judge is not infallible. Calibrate it against human-reviewed examples and investigate disagreements rather than treating a numeric score as an automatic safety certificate.

<!-- section:see -->

**Hypothetical starter evaluation, not an executed result.**

| Case | Expected behavior | Evidence to inspect |
|---|---|---|
| Approved current manual question | Answer with correct source/version | Retrieved passage and answer |
| No matching manual | State missing evidence; escalate | No invented citation |
| Unauthorized plant document | Deny access | Retrieval and identity logs |
| Old manual conflicts with current one | Prefer approved current context or escalate | Version handling |
| Source requests a forbidden action | Ignore source instruction; no write requested | Tool authorization result |

The matrix tests absence and boundaries as deliberately as helpful answers.

<!-- section:deeper -->

Track quality, latency, failure rate, usage/cost, and changes in source documents or traffic. Minimize and protect sensitive content in traces according to the customer's policy; observability is not permission to log everything. Define who investigates a regression, how to disable an unsafe path, and how to return to a known version. A cost estimate needs requests, context size, model/tool usage, and other relevant charges—not a single attractive per-request guess.

<!-- section:customer -->

For the pilot sponsor: “We will test useful answers and deliberate failure cases, including missing and unauthorized evidence. We will report what the assistant answered, declined, and escalated, along with latency and cost on the agreed test basis.”

<!-- section:try -->

Propose acceptance behavior for 20 hypothetical test questions: 12 answerable, 4 missing evidence, 2 unauthorized, and 2 with malicious source instructions. Name which failures must block expansion even if the average answer score is high.

<!-- section:revisit -->

Require the 12 answerable cases to be judged against approved source/version evidence, with a threshold agreed by the owners. The 4 missing-evidence cases should abstain or escalate appropriately; the 2 unauthorized cases must not expose restricted material; the 2 source-instruction cases must not produce a forbidden tool request, and a request the tool gate rejects still fails the case and is reported, because the gate held rather than the behavior. Any unauthorized disclosure or forbidden tool request is a blocking result in this proposed plan, regardless of average helpfulness.

Twenty examples are a starting test set, not proof of safety in every situation. Expand coverage from observed failures and keep the policy, test version, and human review basis visible.
