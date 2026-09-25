# Data — Lab L20

All fixtures are original and synthetic: a fictional maintenance library for
Cinderline Components' North and South plants. No manual, value, plant or
person is real; torque, pressure and interval figures are invented for the
exercise and are not maintenance advice. There is no random generator and no
seed: every document, user, question and label was written by hand.

## fixtures/documents.json — 18 documents

Each document has:

| Field | Meaning |
|---|---|
| `doc_id` | Stable id, e.g. `man-m7-r3` |
| `family` | Documents that replace one another share a family (`man-m7` has revisions 2 and 3; 4 and 5 arrive in `update.json`) |
| `title`, `doc_type` | `manual`, `procedure`, `bulletin`, `training note`, `safety notice`, `engineering procedure` or `draft note` |
| `version` | Integer; higher replaces lower within a family once effective |
| `effective_date` | ISO date the version starts to apply (not the date it was loaded) |
| `region` | `north`, `south` or `all` |
| `audience` | Groups allowed to read it: `technician`, `lead`, `engineering`, `contractor` |
| `status` | `approved` or `draft` |
| `sections` | `heading` plus `sentences`, already parsed (parsing is upstream of this lab) |

Every sentence has 11 to 20 words and every section at most 80, so a small
chunk (budget 20 words) is always one sentence and a large chunk (budget 80)
is always one whole section. The library, in short:

| Family (versions) | Region | Audience | Status | What it is there to show |
|---|---|---|---|---|
| `man-m7` (r2 2025-03-01, r3 2026-06-01) | all | technician, lead, engineering | approved | supersession: only the filter interval changed (250 → 200 hours) |
| `man-m8` (r1) | all | staff | approved | a different machine with similar words; "417 mm" stroke |
| `note-press-hydraulics` | all | staff and contractors | approved | explanatory text that shares the query's words but gives no value |
| `draft-m7-relief` | all | staff | **draft** | an unapproved proposal (200 bar) that must never be cited |
| `proc-lockout-north` / `proc-lockout-south` | north / south | technician, lead | approved | the better lexical match belongs to the other plant |
| `eng-m7-overpressure` | all | **engineering only** | approved | a relevant document most callers may not read |
| `man-l2` (r3 2024-02-01, r4 2026-01-15) | all | staff | approved | a second version pair |
| `bul-2023-017`, `bul-2026-004` | all | technician, lead | approved | two valid bulletins, no version link; the newer one applies today |
| `man-c4` (r2) | all | staff | approved | belt tension and a vibration section for the paraphrase test |
| `man-k1` (r1) | all | staff | approved | part number QX-417 |
| `proc-daily-north` / `proc-daily-south` | north / south | technician, lead | approved | each plant's own pre-start checks |
| `notice-guarding` | all | staff and contractors | approved | a recent safety notice |
| `proc-contractor-site` | all | contractor, lead | approved | the only procedure written for contractors |

"Staff" means technician, lead and engineering.

## fixtures/update.json

`man-m7-r4` (effective 2026-09-15, filter every 150 hours) and `man-m7-r5`
(effective 2026-11-01, every 120 hours). Both are approved; both are loaded
into the rebuilt index at once, so the effective date alone decides which one
answers.

## fixtures/users.json

`tech-north` (technician, north), `tech-south` (technician, south),
`contractor-north` (contractor, north), `engineer` (engineering, region `all`).

## fixtures/queries.json — 13 questions

Each question has a caller, an `as_of` date, a purpose and `relevant` chunk
ids for each chunk size. Relevance is binary and means "this chunk contains
the sentence that answers the question for this caller on this date".
`q06` (the contractor asking for the engineering test procedure) has no
relevant chunk: the right outcome is that no authorized source answers. `q07`
labels only bulletin 2026-004: bulletin 2023-017 is still valid, but while the
temporary instruction applies its weekly frequency is not today's answer.

## How the expected literals were produced

`expected/derive_expected.py` is an independent re-implementation of the
contract using only the Python standard library. It shares no code with
`solutions/` and does not import scikit-learn. It:

1. packs sentences into chunks exactly as TASKS.md states;
2. tokenises with the regular expression `(?u)\b\w\w+\b` on lower-cased text
   (tokens of two or more letters or digits; punctuation separates tokens);
3. computes, over every chunk of one index, `idf(t) = ln((1 + n) / (1 + df(t))) + 1`,
   weights each chunk and each question by raw count × idf, scales each vector
   to unit length, and takes the dot product as the cosine;
4. applies the four admission rules and the bulletin bonus (+0.05 when
   0 ≤ `as_of` − `effective_date` ≤ 365 days), sorts by score (rounded to six
   places), then newer effective date, then chunk id;
5. computes recall@1, recall@3, recall@5 and MRR@5 over the 12 graded
   questions, and the 60-word contexts.

It was run once with `--write` to create `expected/*.json`; `run_tests.py`
reads those committed files and never calls the script. The formula in step 3
is the one scikit-learn documents for `TfidfTransformer` with its defaults
(`smooth_idf=True`, `norm='l2'`, `sublinear_tf=False`), so agreement between the
two implementations is a check of the solution, not a copy of it.

## A hand check you can do with a calculator

The governed small index has n = 48 chunks. For `q02` ("What is the M7 press
relief valve setting?") the question's tokens and their document frequencies
(chunks containing the token, header included) give:

| Token | df | idf = ln(49 / (1 + df)) + 1 |
|---|---|---|
| setting | 6 | ln 7 + 1 = 2.9459 |
| relief | 9 | ln 4.9 + 1 = 2.5892 |
| valve | 10 | ln 4.4545 + 1 = 2.4939 |
| m7 | 16 | ln 2.8824 + 1 = 2.0586 |
| press | 28 | ln 1.6897 + 1 = 1.5245 |
| is | 3 | ln 12.25 + 1 = 3.5055 |
| the | 48 | ln 1 + 1 = 1.0 |
| what | 0 | not in the vocabulary, ignored |

"is" is the highest-weighted question word: in this small library it occurs in
only three chunks, so IDF treats it as informative. Neither chunk below
contains it, so it only lengthens the question vector.

The answer chunk, "M7 press service manual. Hydraulic unit. Set the relief
valve to 180 bar with the pump warm and the ram at top dead centre.", has
vector length 13.0588; its "relief" weight is 2.5892 / 13.0588 = 0.1983. The
question's "relief" weight is 0.4022, so "relief" contributes
0.4022 × 0.1983 = 0.0797 to the cosine. Adding the five shared tokens gives
0.0797 + 0.0740 + 0.0504 + 0.0357 + 0.0276 = 0.2674. The training note
contains "setting" twice (2 × 2.9459 = 5.8918 before scaling by its length,
15.912), which alone contributes 0.4576 × 0.3703 = 0.1694, more than any term
of the answer.

For one metric by hand: governed small `q05` returns
`proc-lockout-north:small:1.1` at rank 1 and `...:1.2` at rank 4. Its
relevant set is those two chunks, so recall@1 = 1/2, recall@3 = 1/2,
recall@5 = 2/2 and the reciprocal rank is 1/1.
