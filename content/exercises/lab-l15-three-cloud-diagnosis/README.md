# Lab L15 — Three-cloud request-path diagnosis

**Execution class: T (tabletop).** You diagnose six authored symptoms across
three separate fictional deployments of Cinderline Components, one on AWS, one
on Azure and one on Google Cloud, on paper or in a text editor. A small local
evaluator written with the Python 3.12 standard library checks your answers
against keys written by hand. **A diagram proves nothing is deployed:** every
request path in this package is a text table, and nothing here resolves a
name, sends a packet, reads a policy or contacts AWS, Azure, Google Cloud or
Databricks.

## Purpose and outcome

The three cloud modules (AWS deployment and network boundaries, Azure
deployment and network boundaries, Google Cloud deployment and network
boundaries) each end in the same practice: follow one request through its
paths, then diagnose one denied and one unreachable request in the order the
request travels. This lab puts the three side by side without letting them
blur. After it you can:

1. read a request path as a text table and say which identity acts on each
   hop, and which control sits at each boundary;
2. classify a symptom as **identity**, **authorization**, **name resolution**
   or **reachability** by finding the first control on the path that fails,
   not by the word in the error;
3. name that control using the cloud's own objects (a KMS key policy, an Azure
   role assignment, a Cloud DNS private zone), never another cloud's;
4. name the evidence to collect, from the case's own evidence catalogue, and
   keep permission evidence and network evidence apart;
5. keep an open question open: a row about availability stays *unknown until
   verified* until a dated source about that cloud settles it;
6. predict how the first failure moves when one fault is fixed, including a
   fix that exposes a second fault of a different class.

## What is executed, and what is not

Executed here: `solutions/diagnose.py`, a simplified model that walks each
case's authored controls in path order (run-as, catalog grants, storage
identity, allow lists, DNS zones, routes, filters, endpoint states), and
`run_tests.py`, which compares its walks and your answers with the hand keys
in `expected/`.

Not executed, and not claimed: any cloud API or console read; DNS resolution;
routing and filtering by real VPC route tables, security groups, NSGs or
firewall rules; AWS PrivateLink, Azure private endpoints or Google Cloud
Private Service Connect; serverless network connectivity configurations;
authorization by IAM, bucket or key policies, Azure role assignments or Cloud
Storage IAM; Unity Catalog privilege checks; any job run; any provisioning.
The model's rules, and where each real service is richer, are in `DATA.md`.

## Prerequisites

The three cloud modules named above, and the Unity Catalog basics of USE
CATALOG, USE SCHEMA and SELECT. Reading JSON and Markdown tables is enough; no
Python needs to be written, and no cloud account is needed.

## Files

| Path | What it holds |
|---|---|
| `CASES.md` | the case sheet: each cloud's deployment, identities, request path, controls, evidence catalogue, symptoms and open questions, as text tables |
| `fixtures/aws.json`, `fixtures/azure.json`, `fixtures/gcp.json` | the same three cases as data |
| `fixtures/negative/` | three deliberately wrong answer sets: relabelled, wrong layer, off path |
| `fixtures/transfer/scenarios.json` | eleven altered configurations for the stretch task |
| `expected/` | keys written by hand from the rules in `DATA.md` |
| `starters/answers.json` | your answer file, with one worked symptom and one worked open question |
| `solutions/` | the evaluator and one complete set of reference answers |
| `TASKS.md`, `SOLUTIONS.md`, `DATA.md` | the tasks, the explained solution and the data dictionary |

## Setup and run

Python 3.12 with the standard library is the whole environment; there is
nothing to install (`requirements.txt` says so).

```sh
cd lab-l15-three-cloud-diagnosis
python3.12 run_tests.py                                # 30 tests on the reference answers
python3.12 run_tests.py --evidence local-evidence.json # the same, and write evidence JSON
python3.12 run_tests.py --answers starters             # judge your own answers after editing starters/answers.json
python3.12 solutions/diagnose.py --table azure         # print one case's request path table
```

Work each task on paper from `CASES.md` first, then fill
`starters/answers.json` and run `--answers starters`. Every problem is printed
as one line, for example `AZ-U: brokenControl expected …, given …`. Running
`solutions/diagnose.py` without `--table` prints every walk, which removes the
point of the exercise; do it last.

## Cleanup

The runner writes nothing except the evidence file you name, and it does not
create `__pycache__`. Delete `local-evidence.json` if you wrote one.

## Limits

The model is a schematic, not a simulator of any cloud. It checks one flow on
one port, treats a security group as allow rules only, applies priority rules
with the lowest number deciding and a deny winning a tie, matches routes by
longest prefix, and treats a DNS zone as answering privately only in the
networks it serves. Real services add much more: explicit denies in IAM,
condition keys, inherited Google Cloud policies, network ACLs, firewall
policies above a VPC, propagation delays and ports the current documentation
lists. Hostnames ending in `.example` stand in for regional names. Passing
every test proves that your answers match the keys; it proves nothing about
any deployment.
