# Lab L21 — Evaluation harness, traces and a failure taxonomy

**Execution class: R (local-executed).** The reference solution and its 33
tests run on one machine with Python 3.12 and the standard library only
(`requirements.txt` lists no packages). Nothing runs on Databricks, nothing
calls a model, a hosted judge or an endpoint, and nothing needs a network
connection.

**What this lab is not.** The answers and traces are **authored fixtures**,
written by hand and labelled `"fixture_kind": "authored"`; they are not model
outputs, and the run says nothing about how any model behaves. The harness is
**not MLflow**: it borrows MLflow's span vocabulary (span type, parent,
status, inputs, outputs, attributes) so that the reading transfers, but it
imports no MLflow code. There is **no judge score** anywhere: the loader
refuses a fixture that carries one. Twelve cases are a teaching set, not a
benchmark.

## Purpose

An evaluation is only as good as the properties it checks and the evidence it
reads. This lab builds a small deterministic harness for Cinderline
Components' fictional maintenance assistant. Each case states its expected
properties before any answer exists: sources it must cite, whether it must
abstain, tools it must not call, tools it must call with exact arguments, and
fields the structured answer must carry. Deterministic scorers check those
properties against the final answer and the trace. A classifier then reads
each trace, span by span, and names the failure class: **retrieval failure**,
**reasoning failure**, **denied tool** or **policy block**, together with the
span where the case first departed from its expectations and the control, if
any, that contained it. Finally you validate a scorer against reference
verdicts and watch a deliberately lenient citation check get rejected.

## Outcome

After the lab you can:

- write expected properties as checkable fields rather than adjectives;
- implement citation correctness (retrieved, citable, required) and explain
  why citation *presence* is not correctness;
- detect a forbidden tool from TOOL spans and tell a denied attempt from an
  executed one;
- classify a failure from a trace and say which span to fix and who owns it;
- validate a scorer against reference verdicts before letting it gate a
  release, and name what the run cannot show.

## Prerequisites

Python you can read (functions, dictionaries, list comprehensions), the idea
of a SQL `WHERE` clause, and the retained GenAI module's distinction between
retrieval, generation, tools and evaluation. Lab L20 (retrieval quality) is
useful background but not required.

## Files

| Path | What it holds |
|---|---|
| `fixtures/sources.json` | Six sources with revision status, citation permission and reader scopes; two tools with their grants |
| `fixtures/cases.json` | Twelve cases with case class, identity and expected properties; blocking declared in advance |
| `fixtures/answers.json` | The final answer for each case: rendered text and structured fields |
| `fixtures/traces.json` | One trace per case: AGENT, RETRIEVER, LLM, TOOL and GUARDRAIL spans |
| `fixtures/reference_verdicts.json` | Author-written citation verdicts used to validate scorers |
| `fixtures/transfer/` | Five cases for Harbourline Freight, a fictional freight forwarder, with different sources, tools and guardrail |
| `expected/*.json` | Hand-typed expected literals (derivations in `DATA.md`) |
| `solutions/evalharness.py` | Reference solution and command-line report writer |
| `starters/evalharness.py` | Your starting point: five marked gaps (Tasks 2 to 6) |
| `run_tests.py` | The unittest runner and evidence writer |
| `TASKS.md`, `SOLUTIONS.md`, `DATA.md` | Tasks, explained solutions, data dictionary |

## Setup

Use Python 3.12. There is nothing to install; the standard library is enough.
The lab was executed with CPython 3.12.3.

## Run

```bash
python run_tests.py                 # 33 tests against the reference solution
python run_tests.py --starter       # the same tests against your starter copy
python solutions/evalharness.py --fixtures fixtures --out report-out --label cinderline-pilot
python solutions/evalharness.py --fixtures fixtures/transfer --out report-out-transfer --label harbourline-transfer
```

The report writer prints one line of class counts and writes
`report.json` and `report.md` into the output directory.

## Cleanup

The test runner writes its temporary copies and reports into the system
temporary directory and deletes them before it exits. If you ran the report
writer yourself, delete `report-out/` and `report-out-transfer/`. Nothing else
is created.

## How the vocabulary maps to MLflow 3

| This lab | MLflow 3 concept (names checked against the mlflow 3.16.1 package) |
|---|---|
| `cases.json` with `expected` | Evaluation dataset records with `inputs` and `expectations` |
| a scorer function returning pass, fail or not applicable | A code-based scorer written with the `@scorer` decorator, which may return a bool, a number, `"yes"`/`"no"` or a `Feedback` |
| `span_type` RETRIEVER, LLM, TOOL, GUARDRAIL | `mlflow.entities.SpanType` members of the same names |
| `authz.decision`, `policy.decision` attributes | Span attributes your own application would record; MLflow does not decide them |
| reference verdicts | Human feedback logged as assessments with a `HUMAN` source |

The mapping is conceptual. Running your own scorers through
`mlflow.genai.evaluate()` needs MLflow installed and, for LLM judges, a
configured judge model; none of that is part of this lab.

## Limits

- Authored fixtures show how the harness classifies; they cannot show how
  often a failure happens in real traffic.
- Reference verdicts were written by the lab author, not a review panel.
- The classifier's earliest-divergence rule looks at the first retrieval
  span and the first generation span; a long agent loop can go wrong at a
  later step, which needs per-step expectations.
- The authorization and policy decisions are read from the trace; the lab
  does not enforce them. Enforcement belongs to the application and platform.
