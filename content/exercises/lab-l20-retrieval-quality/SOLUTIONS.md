# Solutions — Lab L20

The complete reference is `solutions/retrieval.py`. This page explains each
gap, shows the intermediate outputs the tests pin, and ends with the wrong
approaches and exactly how they fail. Every number below is a literal in
`expected/*.json` or in `run_tests.py`; scores are cosine similarity rounded to
four places (plus 0.05 where the bulletin freshness bonus applies).

## Gap 1 — chunking

```python
def chunk_document(document, size):
    budget = SIZES[size]
    out = []
    for s_no, section in enumerate(document["sections"], start=1):
        groups, current = [], []
        for sentence in section["sentences"]:
            if current and len(" ".join([*current, sentence]).split()) > budget:
                groups.append(current)
                current = []
            current.append(sentence)
        if current:
            groups.append(current)
        for c_no, group in enumerate(groups, start=1):
            body = " ".join(group)
            out.append(Chunk(chunk_id=f"{document['doc_id']}:{size}:{s_no}.{c_no}", ...))
    return out
```

Packing whole sentences means no chunk ever ends after "Do not"; keeping the
section boundary means a heading is never shared by two unrelated topics.
Result: 48 small chunks (mean 16.1 words) and 26 large chunks (mean 29.73
words). The header (`"M7 press service manual. Hydraulic unit. "`) is added
only to the text the index sees, so a citation still quotes the body.

## Gaps 2 and 3 — permission and the current version

```python
def visible(user, chunk):
    region_ok = chunk.region == "all" or user["region"] == "all" or chunk.region == user["region"]
    return region_ok and bool(set(chunk.audience) & set(user["groups"]))

def current_versions(chunks, as_of):
    best = {}
    for c in chunks:
        if c.status == "approved" and c.effective_date <= as_of:
            best[c.family] = max(best.get(c.family, c.version), c.version)
    return best
```

`admission()` applies the rules in a fixed order and names the first refusal:
`not approved`, `not yet effective`, `superseded`, `not permitted`. On
2026-09-20 the draft proposal is `not approved`, `man-m7-r2` is `superseded`,
and the South lockout procedure is `not permitted` for `tech-north`. On
2026-05-01 `man-m7-r3` is `not yet effective`, so `man-m7-r2` is current.

## Gap 4 — governed search: admit, then rank

```python
def search(index, query, user, as_of, k=TOP_K, doc_types=FRESH_TYPES):
    current = current_versions(index.chunks, as_of)
    rows = [i for i, c in enumerate(index.chunks) if admission(c, user, as_of, current) is None]
    if not rows:
        return []
    scores = index.cosine(query, rows)
    hits = [Hit(index.chunks[i], round(float(s) + freshness_bonus(index.chunks[i], as_of, doc_types), 6))
            for i, s in zip(rows, scores) if s > 0]
    return sorted(hits, key=order_key)[:k]
```

Restricted rows are never scored. For `q05` ("How do I lock out a press
before clearing a jam?", North technician):

| Rank | Naive (similarity only) | Governed (admit, then rank) |
|---|---|---|
| 1 | proc-lockout-south 1.1 — 0.6395 | proc-lockout-north 1.1 — 0.1836 |
| 2 | proc-lockout-south 1.2 — 0.2565 | notice-guarding 1.2 — 0.1652 |
| 3 | notice-guarding 1.2 — 0.1803 | man-m8-r1 1.2 — 0.1417 |
| 4 | proc-lockout-north 1.1 — 0.1557 | proc-lockout-north 1.2 — 0.1221 |
| 5 | man-m8-r1 1.2 — 0.1271 | proc-daily-north 1.1 — 0.0959 |

The South procedure is the best lexical match (it says "clearing a jam") and
it is not the North technician's procedure. The contractor's `q06` returns no
engineering chunk; the engineer's `q13` returns it first.

## Gaps 5 and 6 — the metrics

```python
def recall_at_k(ranked, relevant, k):
    return len(set(ranked[:k]) & set(relevant)) / len(relevant)

def reciprocal_rank(ranked, relevant, k=TOP_K):
    for rank, chunk_id in enumerate(ranked[:k], start=1):
        if chunk_id in relevant:
            return 1 / rank
    return 0.0
```

Means are taken over the 12 questions that have a relevant chunk; `q06` has
none and is judged by what it must *not* return.

| Pipeline / size | Mean results | recall@1 | recall@3 | recall@5 | MRR@5 |
|---|---|---|---|---|---|
| naive / small | 5.0 | 0.5417 | 0.6667 | 0.7083 | 0.6458 |
| governed / small | 5.0 | 0.7083 | 0.875 | 0.9583 | 0.8778 |
| post-filter / small (k = 3) | 1.8462 | 0.7083 | 0.75 | 0.75 | 0.8333 |
| naive / large | 5.0 | 0.5833 | 0.8333 | 0.8333 | 0.7083 |
| governed / large | 4.9231 | 0.8333 | 0.9167 | 1.0 | 0.8917 |
| post-filter / large (k = 3) | 2.0 | 0.8333 | 0.9167 | 0.9167 | 0.875 |

Across the 13 questions the naive small pipeline also returned 12 chunks the
caller may not read, 7 superseded chunks, 1 draft and 1 revision not yet in
force; every governed and post-filter count is zero.

**Chunk size.** Large chunks score higher here (recall@1 0.8333 against
0.7083) but put 92.08 words into the top three results against 49.31. Read the
difference with care: recall counts relevant *chunks*, and four questions
(`q05`, `q08`, `q11`, `q13`) have two relevant small chunks but one relevant
large chunk, so small chunks cannot reach recall@1 = 1 on them.

## Gap 7 — context and citations

```python
def assemble_context(hits, budget=CONTEXT_WORDS):
    entries, seen, used = [], set(), 0
    for hit in hits:
        if hit.chunk.body in seen:
            continue
        if used + hit.chunk.words > budget:
            break
        seen.add(hit.chunk.body)
        used += hit.chunk.words
        entries.append({"n": len(entries) + 1, "chunk_id": hit.chunk_id,
                        "citation": citation(hit.chunk, len(entries) + 1), "text": hit.chunk.body})
    return {"words": used, "entries": entries}
```

Stopping (rather than skipping to a smaller chunk) keeps rank order honest. For
`q03` with small chunks the context is 52 words: `[1] man-m7-r3 §Hydraulic unit
(v3, effective 2026-06-01)`, `[2] man-m8-r1 §Hydraulic unit (v1, ...)` and
`[3] note-press-hydraulics §Filters`. The M8 interval (300 hours) is in the
context too, labelled as the M8 manual: the citation is what lets an answer,
or a reviewer, keep the machines apart. `check_citations` rejects any cited
chunk that is not in the context, for example `man-m7-r2:small:1.1` for `q03`.

## The three failure cases, worked

**The wrong chunk wins (`q02`, "What is the M7 press relief valve
setting?").** Governed, small chunks: the training note (0.5192) and the
answer's own neighbour, "Record the relief valve setting..." (0.4209), both
outrank the answer, "Set the relief valve to 180 bar..." (0.2674). Per-term
contributions show why:

| Term | Note | Answer |
|---|---|---|
| setting | 0.1694 | — |
| relief | 0.1309 | 0.0797 |
| press | 0.0681 | 0.0276 |
| valve | 0.0607 | 0.0740 |
| the | 0.0488 | 0.0357 |
| m7 | 0.0414 | 0.0504 |
| **cosine** | **0.5192** | **0.2674** |

The answer says "Set"; TF-IDF compares tokens, not meanings, so "setting" earns
it nothing. The note also repeats "setting", "relief" and "press". With large
chunks the manual's whole hydraulic section rises to rank 2 (0.4218) behind the
note (0.4960), and the 60-word context then holds only the note: the value 180
never reaches it. Naive retrieval is worse: the unapproved draft proposing 200
bar ranks second.

**A newer authorized source changes the context (`q03` plus
`update.json`).** On 2026-09-10 the first result is rev 3 (200 hours); on
2026-09-20 it is rev 4 (150 hours, effective 2026-09-15); on 2026-11-05 it is
rev 5 (120 hours). Rev 5 was loaded into the index in September, but it cannot
answer until its effective date. The question `q04`, asked on 2026-05-01, gets
rev 2 (250 hours), while naive similarity puts rev 3 first although it was not
yet in force.

**A relevant unauthorized document must not be returned (`q05`, `q06`).**
Shown in the Gap 4 table and by `q06`: the contractor's naive list starts with
both engineering chunks (0.4942, 0.3009); the governed list starts with a
guarding notice (0.1985) and contains no engineering text.

## Wrong approaches and why they fail

**Filtering after ranking** (`shortcuts.post_filter_search`, k = 3). For `q05`
the top three over *all* chunks are both South chunks and the North chunk; the
filter then drops the two South chunks and returns one result. Those restricted
chunks were scored and ranked first, so they sat in the retrieval output and in
anything that logs it. For `q11` the South technician loses
`proc-daily-south:small:1.2`, which governed search returns at rank 3. Mean
list length falls to 1.85 and recall@3 to 0.75 (governed: 0.875).

**Asking the model to respect permissions** (`shortcuts.prompt_only_permission`).
The contractor's context for `q06` contains "holds the M7 hydraulic circuit at
220 bar for ten minutes" beside an instruction not to use it. The text was
delivered; nothing was enforced.

**A freshness bonus on every document type.** It lifts the 2026 safety notice
above the North lockout procedure for `q05` (the procedure falls to rank 2).
Limited to bulletins, the same bonus moves bulletin 2026-004 for `q07` from
rank 3 to rank 1 with small chunks and from rank 2 to rank 1 with large ones.
It is still a tuning choice: two questions cannot show that 0.05 or 365 days
is right, only that the scope matters.

**A score threshold as an abstain rule.** The contractor's best score for
`q06` is 0.1985; the correct first answer for `q05` scores 0.1836. Any cut-off
that silences `q06` also drops `q05`. Cosine scores are not calibrated
confidence; abstention needs its own labelled cases.

**What lexical retrieval cannot do (`q08`).** "Why does the belt line shake
after start-up?" shares "belt" with the tension section, which ranks first and
second; the vibration chunk the question needs is fifth, and its second
sentence is not returned. An embedding or hybrid retriever is the usual next
experiment; it is not run here.
