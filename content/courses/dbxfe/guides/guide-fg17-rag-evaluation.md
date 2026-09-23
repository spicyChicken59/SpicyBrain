<!-- section:action -->

Start from the decision the assistant is meant to support and the sources that are allowed to inform it. Everything else in the plan follows from those two facts.

1. **Fix the source set.** List every document collection with its owner, version rule, permission scope and freshness expectation. A passage outside this list can never be a correct citation, however relevant it reads.
2. **Write the cases before you look at any output.** Cover answerable questions, missing evidence, unauthorized material, outdated-versus-current versions, ambiguous wording and adversarial source text. Each case names the expected behaviour (answer with citation, abstain, escalate, deny) and the evidence you will inspect.
3. **Score the stages separately.** Record the retrieved chunks, the identity used, the assembled context, the answer and any tool request as distinct observations, so a wrong answer is attributed to retrieval, reasoning or policy rather than to "the model".
4. **Run, capture, classify.** Keep a trace per case. Compute rates only within a class; an average across classes hides the blocking ones.
5. **Declare blocking failures in advance:** an unauthorized disclosure, an invented citation, or a source instruction that gains authority blocks expansion regardless of average helpfulness.
6. **Record what the run cannot show:** real traffic, human-review coverage, judge calibration, cost under load.

Evidence to collect: the source inventory, the case file with expected properties, one trace per case, a failure count by class and attribution, and the list of blocking results with their case ids.

Go deeper on retrieval mechanics in [Document processing and retrieval](#/module/dbxfe-retrieval), on harnesses and traces in [GenAI evaluation and failure analysis](#/module/dbxfe-genai-eval), on the tool boundary in [Tools, MCP and action authorization](#/module/dbxfe-tools), and revisit the retained lesson [Evaluate quality, risk, and operating cost](#/lesson/dbxfe-m07-l03).

<!-- section:example -->

**Fictional worked example: Cinderline's read-only maintenance assistant.** The maintenance lead wants technicians to find the approved procedure for a machine and version, with the source shown. No tool exists; work-order changes are out of scope.

### Decision and source set

The decision is whether a bounded technician pilot at one plant can start. Sources: approved machine manuals (owner: maintenance lead; versioned by revision letter; readable by all plants), plant procedures (owner: each plant's operations lead; plant-scoped permission), and a folder of superseded manual revisions that is *not* an allowed citation but is still on the shared drive. Sensor-alarm notes were requested and refused: no owner, no version rule.

### Case set

Twenty cases were written before any run: twelve answerable, four with missing evidence, two requesting another plant's procedure under a plant-one identity, and two whose source passage contains an instruction ("raise an urgent work order now"). Expected behaviours were agreed with the maintenance lead in writing.

### Results by class (hypothetical run, one afternoon, human-reviewed)

| Class | Cases | Expected | Observed | Attribution |
|---|---|---|---|---|
| Answerable | 12 | Answer, correct revision cited | 10 correct; 2 cited a superseded revision | Retrieval: chunk metadata lacked revision |
| Missing evidence | 4 | Abstain or escalate | 3 abstained; 1 invented a section number | Reasoning: citation not validated against index |
| Unauthorized | 2 | Deny | 2 denied | Policy: identity filter at retrieval |
| Adversarial source | 2 | Quote as content, no action | 2 quoted, no action | No tool exists; re-test when one is added |

### Reading the table

The two superseded citations are one defect, not two: the superseded folder was indexed, and revision metadata never reached the chunk. Fixing the index and adding revision to the metadata is a retrieval change, and the twelve answerable cases must be rerun afterwards. The invented section number is the blocking result. It occurred on a missing-evidence case, which is exactly where a fluent guess costs most, and it would have looked like a good answer to a reader who did not check. A citation validator that rejects any reference not present in the retrieved set is the proposed control; it is a deterministic check, not a judge.

The unauthorized cases passed, but the trace showed the plant-two passage was retrieved and then filtered before generation. That is enforcement at the wrong stage. The requirement is that the identity filter applies at retrieval so the passage never enters context; the data lead owns confirming which stage the platform's permission filter runs at. Until that is confirmed the pass is provisional.

The adversarial cases passed trivially because there is nothing to act on. The record says so, and the cases stay in the set so they are rerun the day any tool is proposed.

### What this run does not show

Twenty authored questions are not the technicians' real question mix; latency and cost were not measured; the human review was one person, the maintenance lead, on one afternoon; no model judge was used, so there is no judge calibration to report.

### Conclusion

Not ready to expand. Two changes (revision metadata, citation validator), one confirmation (filter stage), one full rerun with the same twenty cases plus any failures observed during the rerun. The pilot decision is deferred to that rerun, and the readout will carry this table beside the new one.

<!-- section:template -->

### Decision and scope

- **Decision the assistant supports:** one sentence naming who decides what, and what a wrong answer would cost.
- **Out of scope:** capabilities explicitly excluded (actions, other plants, safety advice).

### Source inventory

| Collection | Owner | Version rule | Permission scope | Freshness expectation | Allowed as citation? |
|---|---|---|---|---|---|
| Name the collection, not "documents" | A named role who can answer questions about it | How the current version is identified | Who may read it, enforced where | How stale it may be before it is wrong | Yes / No, with reason |

### Case set (written before any run)

| Case id | Class | Input | Expected behaviour | Evidence to inspect | Blocking if failed? |
|---|---|---|---|---|---|
| Stable id | Answerable / missing / unauthorized / outdated / ambiguous / adversarial | The exact question and identity | Answer with citation / abstain / escalate / deny | Retrieved set, context, answer, tool request | Yes / No |

### Run record

- **Date, version of sources, version of application, identities used:** enough to rerun.
- **Who reviewed outputs and how:** person or deterministic check; a judge is named as a judge.

### Results by class

| Class | Cases | Passed | Failed | Attribution (retrieval / reasoning / policy) |
|---|---|---|---|---|

### Blocking results

- Case id, what happened, proposed control (deterministic where possible), owner, retest condition.

### What this run cannot show

- Traffic realism, coverage of human review, judge calibration, latency and cost basis, permissions enforcement stage.

### Decision and next step

- Expand / revise / rerun / stop, with the evidence line each rests on and the date of the next review.

<!-- section:limits -->

This guide establishes how an assistant behaved on the cases you wrote, on the source versions you recorded, under the identities you used. It cannot establish safety across inputs you did not write, and a high pass rate on authored cases is not a production quality claim. Permission enforcement lives in the platform and its data layer; a prompt that asks the model to respect permissions is not evidence of enforcement. A model judge, if you use one, reports agreement with its own instructions until you calibrate it against human-reviewed examples. Escalate rather than retest when a run shows any unauthorized disclosure, an answer that could affect safety, or a policy question about which sources may be indexed at all.
