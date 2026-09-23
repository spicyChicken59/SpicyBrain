*Local-executed (R): scikit-learn 1.9.1 `TfidfVectorizer` on Python 3.12,
one machine, no network. This is lexical TF-IDF retrieval: not neural
embeddings, not an approximate nearest-neighbour index and not Databricks AI
Search (formerly Vector Search). Everything below can be studied without
installing anything.*

### What this lab is for

Before an assistant writes a word, a retrieval step has already decided which
passages it may see. If that step returns a superseded revision, another
plant's procedure or a passage that shares the question's words without
answering it, fluent writing cannot repair the result. The retrieval module
teaches the mechanisms; this lab makes you build a small governed retriever,
measure it with recall@k and MRR, and watch three failures happen on purpose.

### The data, briefly

Eighteen fictional maintenance documents from Cinderline's North and South
plants, already parsed into sections and sentences. Each carries a family, a
version, an effective date, a region, an audience and a status. Four callers
ask thirteen labelled questions.

| Document | Why it is there |
|---|---|
| M7 press manual, rev 2 and rev 3 | rev 3 changed one number: filter every 200 hours, not 250 |
| Press hydraulics training note | shares the words of a settings question but gives no value |
| Draft: raise M7 relief valve to 200 bar | status `draft`; must never be cited |
| North and South lockout procedures | each plant may read only its own |
| M7 overpressure test | audience `engineering` only |
| Bulletins 2023-017 and 2026-004 | both valid; the newer temporary instruction applies today |
| C4 conveyor, K1 compressor, L2 lathe manuals | ordinary lookups, a paraphrase and a part number |

Two later M7 revisions (effective 15 September and 1 November) wait in a
separate file for the altered-input test.

### Task by task, with the intermediate output

**Chunking (gap 1).** Sentences are packed into chunks of at most 20 words
(`small`) or 80 words (`large`) without crossing a section. Because every
sentence here has 11–20 words, small chunks are single sentences (48 of them,
mean 16.1 words) and large chunks are whole sections (26, mean 29.73 words).
The index sees `"<title>. <heading>. <body>"`, so "M7 press service manual.
Hydraulic unit." travels with every sentence of that section.

**Admission (gaps 2 and 3).** Four rules run before anything is scored:
approved status, effective on the question's date, the current version of its
family, and visible to the caller (region matches and a group is in the
audience). On 20 September the draft is refused as `not approved`, M7 rev 2 as
`superseded`, and the South lockout procedure as `not permitted` for a North
technician.

**Governed search (gap 4).** Only admitted chunks are scored. For "How do I
lock out a press before clearing a jam?" asked by a North technician,
similarity alone ranks the South procedure first and second (0.6395 and
0.2565) because it literally says "clearing a jam"; governed search returns
the North procedure first (0.1836) and no South chunk at all.

**Metrics (gaps 5 and 6).** Over the twelve questions that have a relevant
chunk:

| Pipeline | recall@1 | recall@3 | recall@5 | MRR@5 | words in top 3 |
|---|---|---|---|---|---|
| naive, small chunks | 0.5417 | 0.6667 | 0.7083 | 0.6458 | — |
| governed, small chunks | 0.7083 | 0.875 | 0.9583 | 0.8778 | 49.31 |
| governed, large chunks | 0.8333 | 0.9167 | 1.0 | 0.8917 | 92.08 |

Large chunks score higher here and nearly double the words sent onward. Four
questions have two relevant small chunks but one relevant large chunk, so the
two columns count different units; compare them with that in mind.

**Context (gap 7).** Hits are added in rank order until 60 words are spent,
repeated text is skipped, and each entry carries a citation such as
`[1] man-m7-r3 §Hydraulic unit (v3, effective 2026-06-01)`. A citation check
rejects any cited chunk that is not in the context.

### The three failure cases

**The wrong chunk wins.** "What is the M7 press relief valve setting?" The
training note scores 0.5192 and the answer's neighbouring sentence ("Record
the relief valve setting...") 0.4209; the answer ("Set the relief valve to
180 bar...") scores 0.2674 and ranks third. The term "setting" alone gives the
note 0.1694; the answer says "Set", which TF-IDF treats as a different token.
With large chunks the manual section is second, and the 60-word context holds
only the note: the value never arrives.

**A newer authorized source changes the context.** With the update loaded,
the same filter question returns rev 3 (200 hours) on 10 September, rev 4
(150 hours) on 20 September and rev 5 (120 hours) on 5 November. Rev 5 was in
the index all along; its effective date kept it out.

**A relevant unauthorized document is not returned.** The contractor asking
for the overpressure test gets no engineering chunk, whereas similarity alone
ranks both engineering chunks first. The engineer asking the same question
gets the procedure first.

Two shortcuts are tested to fail. Filtering *after* ranking returns on average
1.85 of 3 results, scores the South chunks before dropping them, and loses a
South technician's relevant chunk. Asking the model to "not use" restricted
passages leaves "holds the M7 hydraulic circuit at 220 bar" in the
contractor's context.

### What the tests prove and do not prove

The 28 tests prove that the scikit-learn solution reproduces rankings, scores,
metrics and contexts that an independent standard-library implementation wrote
into `expected/`; that no governed result breaks an admission rule, checked
from the metadata by the test itself; that the freshness bonus is scoped to
bulletins (on every type it lifts a safety notice above the lockout
procedure); and that no single score threshold separates the contractor's
unanswerable question from a correct low-scoring answer. They do not show how
embeddings, hybrid search or a reranker would do on this library, how any
managed service behaves, whether an answer written from these contexts would
be grounded, or anything about a real question mix: thirteen authored
questions are a teaching set, not a benchmark.

### Setup, run and cleanup

Create a virtual environment outside the lab folder, install
`requirements.txt` (scikit-learn 1.9.1 and its pinned dependencies), then from
the lab folder run `python run_tests.py --evidence evidence.json`. To check
your own work, fill the seven gaps in `starters/retrieval.py` and run
`python run_tests.py --starter`. Afterwards delete `evidence.json` and remove
the virtual environment; the runner writes nothing else.
