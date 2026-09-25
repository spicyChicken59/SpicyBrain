# Tasks — Lab L15 three-cloud request-path diagnosis

Read one case at a time in `CASES.md`, work each task on paper, then record
your answers in `starters/answers.json` and run
`python3.12 run_tests.py --answers starters`. Symptom AWS-D and the open
question `aws-relay-endpoint-service` are done as worked examples.

## The four classifications

| Classification | Use it when the first failing control on the path… | Typical sign |
|---|---|---|
| `identity` | establishes who acts, and the principal that acted is not the one the design names | a refusal that names the wrong principal |
| `authorization` | checks a privilege, role or policy for the right principal, and it is missing | a refusal that names the right principal and a permission |
| `name-resolution` | resolves a name, and the answer from the asking network is not the private address the design needs | a timeout, or a refusal from a public front door |
| `reachability` | routes, filters or carries the packet (route, security group, NSG, firewall rule, endpoint state) | a timeout with no service error |

Classify by the **first control that fails in path order**, not by the word
in the error. A timeout is never identity or authorization: no grant or role
can make a packet arrive.

## Task 1 — classify six symptoms (`classification`)

For AWS-D, AWS-U, AZ-D, AZ-U, GCP-D and GCP-U, write one of `identity`,
`authorization`, `name-resolution`, `reachability`. Before you start, predict
how many of the six are network failures. Expected behaviour: all four
classifications occur at least once; a wrong entry is reported as
`<symptom>: classification expected …, given …`.

## Task 2 — name the broken control (`brokenControl`)

Walk the symptom's request segments in the order the case sheet lists their
controls, and write the ID of the first control whose authored configuration
fails the request. Use only that cloud's own control table. Expected
behaviour: a control from another cloud's case is refused as
`… is not a control of the <cloud> case (it belongs to: …)`; a control of the
right case that the request never passes through is refused as
`… is not on the request path of …`.

## Task 3 — name the evidence to collect (`evidence`)

List the evidence IDs you would capture, read-only, before changing anything.
Every item must come from the same case's evidence catalogue and sit on the
symptom's request path, and the set must include the evidence that proves the
broken control. `error-record` fits every symptom. Expected behaviour:
permission evidence (for identity and authorization controls) cited for a
network failure, or network evidence cited for a permission failure, is
refused with both families named; missing required items are listed.

## Task 4 — keep the open questions open (`unknowns`)

Each case lists open questions about availability, limits or required
settings. For each row write a `status` and, while it is `unknown until
verified`, a `wouldSettle` naming the dated source or test that would close
it. Expected behaviour: a row may leave `unknown until verified` only with a
source about the same cloud, of kind `documentation page read`,
`account team in writing` or `test result`, with a date; this lab reads no
source, so every row stays open. An SDK field, a Terraform example or another
cloud's answer is refused.

## Stretch, on paper only

For each scenario in `fixtures/transfer/scenarios.json`, apply its changes to
the case in your head and name the new first failing control and its
classification, or say that the request now passes. Which scenario turns a
name-resolution timeout into a reachability timeout, and why could nobody see
that fault before?
