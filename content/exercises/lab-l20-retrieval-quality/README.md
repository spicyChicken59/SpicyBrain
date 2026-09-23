# Lab L20 — Retrieval quality on a governed lexical baseline

**Execution class: R (local-executed).** The reference solution and its 28
tests run on one machine with Python 3.12 and scikit-learn 1.9.1
(`requirements.txt`). Nothing runs on Databricks, nothing calls a model, and
nothing needs a network connection.

**What this lab is not.** It is lexical TF-IDF retrieval built with
scikit-learn's `TfidfVectorizer`. It is **not** neural embeddings, **not** an
approximate nearest-neighbour index, and **not** Databricks AI Search (the
managed service formerly called Vector Search). Its numbers describe one
synthetic library of 18 documents and 13 labelled questions; they are not a
benchmark of any product or technique.

## Purpose

A retrieval step decides which passages an answer is allowed to see. This lab
makes that decision inspectable. You chunk a small maintenance library two
ways, index it with TF-IDF, apply four admission rules *before* ranking
(approved status, effective date, current version, the caller's permission),
add a small freshness preference for bulletins, assemble a 60-word context
with citations, and grade the result with recall@k and MRR against labelled
relevant chunk ids. Then you watch three failures happen on purpose: the wrong
chunk wins, a newer authorized revision changes the answer context, and a
relevant document the caller may not read must never be returned.

## Outcome

After the lab you can:

- explain from per-term contributions why a chunk that does not contain the
  answer outranks one that does;
- show that filtering after ranking both scores restricted chunks and starves
  the result list, and that a prompt instruction is not a permission check;
- compare two chunk sizes on recall@1, recall@3, recall@5, MRR@5 and the
  words they put into a context;
- name what lexical retrieval misses (a paraphrase) and what it gets right
  (an exact part number).

## Prerequisites

Python you can read (functions, dictionaries, list comprehensions), the idea
of a SQL `WHERE` clause, and the retained GenAI module's distinction between
relevance and permission.

## Files

| Path | What it holds |
|---|---|
| `fixtures/documents.json` | 18 original synthetic documents: family, version, effective date, region, audience, status, sections, sentences |
| `fixtures/update.json` | Two later revisions of the M7 manual for the altered-input test |
| `fixtures/users.json` | Four callers with groups and a region |
| `fixtures/queries.json` | 13 questions with caller, date, purpose and relevant chunk ids for each chunk size |
| `expected/*.json` | Literal expected outputs written by the independent derivation |
| `expected/derive_expected.py` | Standard-library re-implementation used to write those literals (see DATA.md) |
| `solutions/retrieval.py` | Reference solution |
| `starters/retrieval.py` | Your starting point: seven marked gaps |
| `starters/shortcuts.py` | Two wrong approaches the tests prove wrong |
| `run_tests.py` | The unittest runner and evidence writer |

## Setup

Create a virtual environment outside this folder (so it never ends up in a
copy of the lab), activate it, and install the pins:

```bash
python3.12 -m venv ~/venvs/l20
source ~/venvs/l20/bin/activate
python -m pip install -r requirements.txt
```

## Run

From this directory:

```bash
python run_tests.py --evidence evidence.json
```

The runner prints each test, then a short summary; `--evidence` writes the
full record (versions, counts, SHA-256 hashes of every fixture, expected file,
solution, starter and produced output). To test your own work, fill the gaps
in `starters/retrieval.py` (see TASKS.md) and run
`python run_tests.py --starter`: the same 27 behaviour tests run against your
module instead of the reference solution. An unfinished gap shows up as an
error naming it (`NotImplementedError: GAP 4: ...`).

## Cleanup

Delete `evidence.json` if you wrote it here, deactivate the environment and
remove it (`deactivate`, then `rm -rf ~/venvs/l20` on Linux or macOS). The
runner writes no other file and leaves no `__pycache__` behind.

## Limits

- Thirteen authored questions are not a real question mix; every rate here
  is a property of this fixture.
- Relevance labels are binary and were written by the author; graded
  relevance and disagreement between labellers are out of scope.
- IDF is computed over every chunk in the index, including chunks a caller
  may not read. Admission decides which rows are scored, but corpus
  statistics still include restricted text; a design that must not leak even
  that uses separate indexes per audience.
- No answer is generated, so groundedness (whether an answer is supported by
  its context) is not measured here; it needs answers and a human or
  model-based judge.
- Hybrid search, reranking and embeddings are discussed in the module but not
  executed here.
