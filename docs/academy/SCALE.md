# Scale: the two-tier catalog

The course is about to grow from 16 to 48 modules (3× lessons, cards and
scenarios). The initial JavaScript must not grow by more than 15% over the
baseline measured at `main` (`dist/assets/index-*.js`: 1,384,441 B raw).
This page records what the split changed and how each view behaves,
measured with `npm run measure:bundle` (`scripts/measure-bundle.mjs`, zlib
level 9 for gzip; hosts compress differently, so compare runs of the script
with each other) and a Playwright request log
(`tests/browser/lazy-bodies.spec.ts`, evidence in
`test-results/evidence/request-counts.json`).

## What moved where

The initial bundle now imports only the **catalog tier**
(`src/generated/catalog.json`, `teaching-index.json`, `paths.json`): every
identity, title, mapping, count, rubric, source/claim/concept record and
asset description, with cards and questions as `{id, revision, …}`
references. The **body tier** is one static file per lesson, scenario, lab,
guide and case under `public/teaching/bodies/<id>.json`, fetched on demand,
Zod-validated and identity-checked against the catalog before it is cached
(`src/bodies.ts`, `src/catalog.ts`). Extension-card text stays inside each
module's JSON, which the index references by `{id, revision, lessonId,
sectionId, beatId}`.

## Sizes at 16 modules

Measured on this checkout on 2026-09-23, before and after the split, with
the same content inputs for the initial bundle and the generated catalog
files (other content files were being edited concurrently, which is why the
lazy module and search totals differ slightly between the two rows).

| Artifact                                  |  Before (raw) | Before (gzip) |  After (raw) | After (gzip) |
| ----------------------------------------- | ------------: | ------------: | -----------: | -----------: |
| `dist/assets/index-*.js` (initial JS)     |     1,384,441 |       363,613 |  **916,247** |  **226,797** |
| `dist/assets/index-*.css`                 |       130,115 |        24,460 |      130,115 |       24,460 |
| `src/generated/catalog.json` (inlined)    |       598,464 |       143,785 |      212,215 |       31,260 |
| `src/generated/teaching-index.json`       |       173,018 |        41,636 |       84,529 |       14,951 |
| `src/generated/paths.json` (inlined)      |        10,099 |         2,744 |       10,099 |        2,744 |
| `public/teaching/bodies/*.json` (56 files) |             0 |             0 |      454,722 |      164,715 |
| `public/teaching/<course>-<module>.json`  |     1,012,185 |       256,817 |    1,038,364 |      264,859 |
| `public/teaching/search.json`             |       786,975 |       210,069 |      798,697 |      214,283 |
| `public/teaching/media.json`              |        43,370 |        10,489 |       43,370 |       10,489 |

The initial JavaScript shrank by 468,194 B raw (−33.8%) and 136,816 B gzip
(−37.6%). The bundle shrank by almost exactly the raw bytes removed from the
two inlined JSON files (436,748 B at the first cut), so inline JSON costs
about one bundle byte per byte and the non-content code is about 609 KB.

## Projection to 48 modules

At 16 modules the inline content tier is 306,843 B (catalog + index +
paths). If every part of it triples with the course, the initial bundle
becomes about 609 KB + 3 × 307 KB ≈ 1,530 KB, **+10.5%** over the 1,384,441 B
baseline against the 15% ceiling of 1,592,107 B. The projection is an
upper bound where course-level sources, claims, concepts and assets also
triple; the fixed parts (refreshers, change notes, course summary) do not
grow. It is a projection, not a measurement of 48-module content.

Three details were trimmed from the design to earn that margin, each
because nothing at runtime reads it from the inline tier: card references
carry `id`, `revision`, `lessonId` and `sectionId` only (concept and claim
ids travel with the card text, which every consumer has loaded before it
needs them); the teaching index no longer repeats a module's `outcomes` and
`startingAssumptions` (the module JSON carries them); and its `referenceIds`
list only the module's check identities (questions and self-questions), the
sole module-level ids a study record can cite in an import preview. Without
those three the projection was about +16.5%.

## Requests per view

From the request log of a fresh Chromium context: counts are the requests
made when the view opens (the first row includes the document, script,
stylesheet, fonts and icons; later rows are hash navigations within the
same document, so they list only what the view itself fetched).

| View                                                       | Requests | Teaching files fetched                                                          |
| ---------------------------------------------------------- | -------: | ------------------------------------------------------------------------------- |
| Today (`#/`)                                               |       10 | none                                                                            |
| Course map (`#/course/dbxfe`)                              |        1 | none                                                                            |
| One lesson (`#/lesson/dbxfe-m01-l01`)                      |        3 | `bodies/dbxfe-m01-l01.json`                                                     |
| One module beat (`#/module/dbxfe-delta/<beat>`)            |        4 | `dbxfe-dbxfe-delta.json`, `bodies/dbxfe-m03-l02.json`, `media.json`             |
| Practice page (`#/practice/dbxfe-m02-scenario`)            |        2 | `bodies/dbxfe-m02-scenario.json`                                                |
| Review page (`#/review`)                                   |        1 | none (due counts come from the catalog tier)                                    |
| Review session (introduce 3 new cards)                     |        1 | `bodies/dbxfe-m03-l01.json` (one lesson body per lesson in the session pool)    |

A module workspace loads its module and the bodies of its owned lessons,
plus any lesson whose check a beat reuses, in parallel. A review session
resolves core cards through their lesson bodies and extension cards through
their module, all promise-cached, so revisiting a lesson or module within
the same document makes no second request. The scheduled-cards history panel
fetches prompts only when it is opened. Course handbook assembly still loads
every module of the course, only on request.

## What is unchanged

`search.json`, `media.json`, the per-module teaching JSON and its
750,000-byte cap, Vite's chunk-size warning limit, every route and ID, the
study schema and its migrations, and the content-only extension proof, whose
runtime-change filter already treats `public/teaching/**` as generated
output.

## Course collection views (measured 2026-09-23)

`npm run measure:bundle` in two isolated copies of the same commit and the
same content (17 registered modules and 8 tracks, no labs, guides, cases or
routes yet), before and after the generic collection views: track-grouped
course map, named routes, lab shelf, field guides with a notebook draft, case
analyses, crosswalk, capstone revision notice and data packs, per-track
handbook, re-entry cue and next-in-track. Every generated catalog, search and
lazy file is byte-identical in both rows; only the code and the stylesheet
changed.

| Artifact                                      | Before (raw) | Before (gzip) | After (raw) | After (gzip) |
| --------------------------------------------- | -----------: | ------------: | ----------: | -----------: |
| `dist/assets/index-*.js` (initial JS)         |      946,094 |       232,703 | **972,208** |  **239,140** |
| `dist/assets/index-*.css`                     |      130,115 |        24,460 |     136,061 |       25,476 |
| `src/generated/catalog.json` (inlined)        |      234,591 |        35,694 |     234,591 |       35,694 |
| `src/generated/teaching-index.json`           |       91,937 |        16,541 |      91,937 |       16,541 |
| `public/teaching/search.json`                 |      866,695 |       232,439 |     866,695 |      232,439 |
| `public/teaching/bodies/*.json` (58 files)    |      485,606 |       174,144 |     485,606 |      174,144 |
| `public/teaching/<course>-<module>.json` (17) |    1,196,947 |       299,042 |   1,196,947 |      299,042 |

The initial JavaScript grows by 26,114 B raw (+2.8% over the previous build,
1.9% of the 1,384,441 B baseline) and 6,437 B gzip, and stays at 70.2% of the
baseline (ceiling 1,592,107 B). Of the new code, `src/collections.tsx` is
about 18 KB minified and `src/collections-model.ts` about 2.4 KB;
`src/academy.css` adds 5.9 KB of CSS. Today and the course map make no new
request; a lab, guide or case page fetches its one body file;
`#/handbook/<course>?track=<track>` fetches only that track's modules (request
logs in `npm run test:collections` and
`tests/browser/course-collections.spec.ts`).

Projection, not a measurement. The final gate run, after modules E2 and G5
were registered (19 modules), measured the initial JavaScript at 1,034,218 B
raw and 250,623 B gzip (74.7% of the baseline) with an inline content tier of
398,635 B (catalog 278,884 + index 109,652 + paths 10,099). The two added
modules cost about 31 KB of inline JSON each, against an average of about
19.8 KB for the first 17, because their packages bring more course-level
sources, claims and concepts. If the remaining 29 modules cost the same, the
inline tier reaches about 1.30 MB and the initial JavaScript about 1.93 MB
(+40% over the baseline); scaling the 19-module tier proportionally (×48/19)
still gives about 1,643 KB (+18.7%). The collections' own catalog entries come
on top: the 32 guides, 8 cases with their sources and 10 crosswalk rows on
disk strip to 33,473 B, and 24 labs at the size of the four indexed so far to
about 19 KB. The views added here are 26 KB of that total; the 15% ceiling
needs a second split of the inline tier before the full course is registered
(for example source context and caveats, claim descriptions and concept
definitions in lazily loaded files, and lab outcome, environment and evidence
or guide and case summaries in their bodies). The collection pages could also
become a lazily loaded chunk (about 13 KB).

The review fixes that followed (handbook scope links instead of a select,
an explained empty track handbook, an h2 per field-guide part, the
crosswalk's unpinned first column and "More columns" hint on a phone, own-key
title lookups) add 1,503 B raw and 704 B gzip to the initial JavaScript and
915 B raw and 90 B gzip to the stylesheet, measured with
`npm run measure:bundle` in two isolated copies of the same 33-module content
before and after them. The build-time Markdown audit (`src/markdown-audit.ts`,
the renderer's own remark-parse with remark-gfm) adds nothing to the bundle:
`validateCourses` never reaches the app, and react-markdown already ships that
parser. It parses each lesson section, scenario text and lab, guide or case
body once per build, about 0.6 ms a body (`validateCourses` over 26 modules:
30 ms before, 370 ms after on a first call; repeated calls on the same text
reuse the parse).
