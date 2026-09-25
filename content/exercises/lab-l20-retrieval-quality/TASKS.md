# Tasks — Lab L20

Work in `starters/retrieval.py`. Everything outside the seven gaps already
works. After each gap, run `python run_tests.py --starter`; tests that depend
on an unfinished gap report `NotImplementedError: GAP n`. Gap 1 comes first
because every other test needs chunks.

The fixed contract (DATA.md has the details): chunk budgets of 20 words
(`small`) and 80 words (`large`); whole sentences only; a chunk never crosses a
section; chunk ids `<doc_id>:<size>:<section>.<chunk>` counted from 1; the
index text is `"<title>. <heading>. <body>"`; the context budget is 60 words.

## Gap 1 — pack sentences into chunks

`chunk_document(document, size)` returns one `Chunk` per group of consecutive
sentences whose joined body is at most `SIZES[size]` words. Start a new chunk
when adding the next sentence would exceed the budget; a sentence longer than
the budget is a chunk of its own.

Expected behaviour: 48 small chunks and 26 large chunks over the 18 documents;
every small chunk is exactly one sentence (every sentence in this library has
11–20 words); every large chunk is a whole section. `man-m7-r3:small:1.2` has
the body "Set the relief valve to 180 bar with the pump warm and the ram at
top dead centre."

## Gap 2 — permission

`visible(user, chunk)` is true when the regions match (either side `all`
counts as a match) **and** at least one of the caller's groups appears in the
chunk's audience.

Expected behaviour: `tech-north` cannot see `proc-lockout-south`;
`contractor-north` cannot see `eng-m7-overpressure` or `man-m7-r3`;
`engineer` (region `all`, group `engineering`) sees the engineering procedure
but not the South lockout procedure, whose audience is technicians and leads.

## Gap 3 — the current version

`current_versions(chunks, as_of)` maps each family to the highest **approved**
version whose effective date is on or before `as_of`. The caller does not
change the answer: a superseded revision stays superseded even for someone who
could read it.

Expected behaviour: `man-m7` is version 2 on 2026-05-01 and version 3 on
2026-09-20; `draft-m7-relief` has no current version at all; with
`update.json` added, `man-m7` is 3 on 2026-09-14, 4 on 2026-09-15 and 5 on
2026-11-01.

## Gap 4 — governed search

`search(index, query, user, as_of, k=5, doc_types=FRESH_TYPES)` admits first
(`admission(...) is None`), scores only the admitted rows with
`index.cosine(query, rows)`, adds `freshness_bonus`, drops chunks whose cosine
is zero, sorts with `order_key` and keeps `k`.

Expected behaviour: for `q05` (a North technician asking how to lock out a
press before clearing a jam) the first result is `proc-lockout-north:small:1.1`
and no `proc-lockout-south` chunk appears anywhere in the list, although the
naive ranking puts both South chunks first. For `q06` the contractor receives
no `eng-m7-overpressure` chunk; for `q13` the engineer's first result is that
procedure.

## Gaps 5 and 6 — recall@k and reciprocal rank

`recall_at_k(ranked, relevant, k)` is the share of the relevant chunks found
in the first `k` results. `reciprocal_rank(ranked, relevant, k=5)` is
`1 / rank` of the first relevant chunk within the first `k`, or 0.0.

Expected behaviour on the hand example: ranked `a b c d e f`, relevant
`c x` gives recall@1 = 0, recall@3 = 0.5, recall@5 = 0.5 and reciprocal
rank = 1/3; a relevant chunk at rank 6 gives 0.0 at k = 5.

## Gap 7 — context assembly with citations

`assemble_context(hits, budget=60)` walks the hits in rank order, skips a hit
whose body text is already included, stops at the first hit that would take
the total past the budget, and numbers citations from 1 in the form
`[n] <doc_id> §<heading> (v<version>, effective <date>)`.

Expected behaviour: for `q02` with large chunks the context holds only
`note-press-hydraulics:large:1.1` (36 words), because the M7 manual's
hydraulic section would take it past 60 words; the relief valve value never
reaches the context.

## Investigations (after the tests pass)

1. **Why the wrong chunk wins (q02).** Call `index.explain(query, chunk_id)`
   for the training note, the answer's neighbour and the answer. Which single
   term separates the note from the answer, and why does TF-IDF not match
   "setting" to "Set"?
2. **Filter before or after?** Run `shortcuts.post_filter_search` for `q05`
   and `q11` with `k=3`. Count the results, list what it dropped, and say
   which relevant chunk it lost for the South technician.
3. **A prompt is not a permission.** Run `shortcuts.prompt_only_permission`
   for `q06`. Find the restricted sentence in the returned context.
4. **A newer revision arrives.** Rebuild the index with `update.json` added
   and ask `q03` on 2026-09-10, 2026-09-20 and 2026-11-05. Record the interval
   each context would give.
5. **Chunk size.** Fill in this table from your run: chunks, mean chunk words,
   recall@1, recall@3, recall@5, MRR@5 and mean words in the top three, for
   each size. Which size would you choose for this library, and what would
   you measure next before deciding?
6. **Freshness scope.** Compare `q07` with `doc_types=FRESH_TYPES`,
   `doc_types=()` and `doc_types=None`, and `q05` with `doc_types=None`. Write
   one sentence on why the bonus is limited to bulletins.
7. **Thresholds.** Compare the contractor's top score for `q06` with the
   correct first result for `q05`. Can one cut-off make `q06` abstain without
   losing `q05`?
