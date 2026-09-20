# Teacher-first corrective milestone

The accepted application provided a document reader and reliable local study tools, but did not provide the requested small visual teaching sequence. This change makes **course → module → beat** the main journey and completes all sixteen Databricks modules in **Deck, Handbook and Cards**, with 135 beats, 215 visual states, 135 newly authored checks, 208 total cards and sixteen curated video references. It preserves the useful original course and study history. This is one scoped implementation PR, not a new enhancement programme.

## Starting state and authority

Verified repository `spicyChicken59/SpicyBrain`, ID `1376873797`, public, unarchived, default `main`, with pull/push/admin access reported by the active connection. Initial open-PR list was empty. Main was `e3bfb97414026e223696312e987879608cc34416`, tree `374b7e10d3004bf7a8bed8032286b0d985545173`; rechecked during final acceptance with no intervening main change. The clean local prior branch was at accepted head `16a09f48f206f25dda800d7440713318ba146942`, whose tree matched main. A fresh `feat/teacher-first-course` branch was created from fetched `origin/main`; no reset, overwrite or force push was used.

The explicit assignment authorized edits, testing, commit, push and one PR. No merge, auto-merge, publication, remote preview/tunnel, schedule, settings/secret change, paid service, cloud provisioning or sibling/shared-design edit is included. The user-supplied prompt and local HTML specimen were read. Synced project sources and the original project brief were treated as read-only references.

The current public version-2 Site remains unchanged. Its reported publication/migration checkpoint is attributed in [DEPLOYMENT.md](../DEPLOYMENT.md). This milestone does not claim a new production-origin migration or a compatible rollback to older schema 3 website files after schema 4 migration.

## Complete teaching and preservation

- [Full ordered coverage matrix and beat/section mapping](COVERAGE.md), with [machine-readable counts](../evidence/teacher-first/coverage.json).
- [Full editorial review](EDITORIAL-REVIEW.md), [technical modules](curriculum-1-8.md), [field/GenAI/architecture modules](CURRICULUM-9-16.md) and [extension disposition](EXTENSION-AUDIT-9-16.json). Every module's explanation, visual states, handbook, check reasoning, analogies, recap and transfer task was read. Forty initially repetitive extensions were replaced before approval.
- [Canonical disposition](DISPOSITION.md) and [complete identity/hash record](disposition.json): 43 lessons, 144 original cards, 96 questions/options/rationales, 18 original SVGs, 12 scenarios and one complete capstone remain. Original lesson bodies, exercise sources, downloads and design assets are unchanged. New beat completion is separate from old section completion.
- [Media selection/review register](MEDIA-REVIEW.md), canonical source/claim registers in each module and [actual consent/playback evidence](../evidence/teacher-first/media-playback.json). Current primary product facts, original professional guidance and fictional scenarios are labeled separately. Original video/caption/slide content is not rehosted.

Visual inspection covers all 215 authored states at both desktop and phone widths: [first eight modules](VISUAL-QA-1-8.md), [last eight modules](visuals-9-16/README.md). The first-half pass used installed Chrome 153.0.8010.50; the second-half and functional suites used pinned Chromium.

All main explanations are at most 120 words; this is an editing check, not evidence of educational quality. Handbook sections contain additional mechanics, worked examples, limits and precise original references. Beyond cards have their own fully taught handbook anchors and deliberate introduction; opening their source beat does not silently add them to review.

## Architecture and learner state

The engine remains static React/TypeScript/Vite with local search and browser-local IndexedDB. Teaching modules and search/media data are lazy same-origin JSON, validated before use; each module is capped at 750,000 bytes. The original lesson catalog is retained in the initial bundle, so Vite's existing large-chunk advisory remains. There is no runtime AI, arbitrary code execution, account, paid provider, workspace dependency, sync or analytics. Videos are optional and contact the provider only after consent.

Root schema 4 keeps native IndexedDB version 2. Strict 1/2/3 migration retains all original fields/timestamps and adds new empty beat families plus the Samajh preference. All persisted new fields participate in backups/import/merge. Exact beat, visual state, per-view position, handbook context, check draft and preference resume independently of explicit completion and immutable assessment/review events. Main resume survives source/handbook detours. [Study-data semantics and forward-compatible recovery](../STUDY-DATA.md) explain the failure and rollback boundaries.

The actual old main `StudyStore` and content schema were extracted and executed unchanged against synthetic IndexedDB. They accepted a genuine schema 3 fixture but refused schema 4 initialization/change/replacement without changing its bytes, retaining an unsaved old-client draft. [Exact source hashes and results](OLD-CLIENT-EXECUTION.json) distinguish this module execution under fake-indexeddb from a claim of running the old browser UI.

## Acceptance evidence and its limits

Local runtime: Node 24.19.0, Playwright 1.63.0, Chromium 153.0.8010.12 and Playwright WebKit. Browser phone sizes are **emulation**, not physical iPhone/Safari testing. All private-looking test text and import fixtures are synthetic.

| Requested journey        | Concrete evidence                                                                                                                                                                                                               |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A: course/module/beat    | Root and nested production browser journeys; every module opens; only explicit completion changes completion.                                                                                                                   |
| B: predict/reveal/reason | Deterministic option/rationale scoring; self-comparison disclosed; reveal/navigation is not mastery.                                                                                                                            |
| C: visual/definition     | Every authored visual/state inspected at 1440 and 390; keyboard, hover, touch, measured viewport placement, Escape and focus return checks.                                                                                     |
| D: handbook              | Exact beat and extension anchors, desktop independent panel scroll, mobile return/draft, new-tab detour, full course assembly and print stylesheet checks.                                                                      |
| E: media                 | All 16 actual consent-gated app players advanced; no provider requests before choice; blocked-player fallback, original link and authored equivalent checked separately.                                                        |
| F: cards                 | Original identities, core/beyond/topic filtering, explicit introduction, exact explanation links, shared review queue and separate extra practice.                                                                              |
| G: leave/resume          | Reload, main resume, module-local latest position, per-view offsets, visual/check state, cross-tab handbook save, removed/revised content and detour regressions.                                                               |
| H: migration             | Genuine native IndexedDB2 schema 3 seed with every original family; edit/export/fresh-context import; exact field comparison. Existing native1/2, two-tab import, pending edits and transaction-abort tests retained.           |
| I: failure/budgets       | Denied/quota/blocked storage; original failed-migration recovery; malformed/future data;16 MB UTF-8 boundaries, >5 MB historical export and >20 MB framed/legacy transports.                                                    |
| J: access/layout         | 1440/390/320, light/dark/system, 200% text reflow, reduced motion, keyboard/touch, axe and modal focus. Exhaustive diagram checks supplement representative screenshots.                                                        |
| K: hosting/exercises     | Root and `/SpicyBrain/` production builds; valid downloads, exact original snippets and unchanged ZIP. Actual Python/Spark execution is a separate CI step.                                                                     |
| L: unrelated course      | Content-only two-module/four-beat photography fixture: Deck/Handbook/Cards, definitions, Samajh, safe fixture media, search, study, notes, review, rename/reorder/revision, export/import and cleanup; engine hashes unchanged. |

Local final checks passed **141 deterministic tests**, typecheck/lint and both production builds. The full Chromium/WebKit run passed **43 journeys**; after the final typed media-reference correction and full-course handbook test, all **20 affected browser cases** passed. The final complete suite has 45 cases and is verified again at the exact PR head in CI. The unrelated course proof also passed after the exact extension anchor assertion was updated.

`npm ci --ignore-scripts`, `npm run check`, root/nested builds, Chromium/WebKit journeys, `npm run test:content-extension` and `npm run report:sources` are run locally. The current availability report checks 170 source/media records across 127 unique reachable URLs; link reachability is explicitly separate from actual claim review.

The exercise package remains **57,908 bytes, 37 members**, SHA-256 `32af53617af3591ebf861857a579bd93dd86b4e1981bf4ad01c37a7353e0e4fb`. The workflow pins Python 3.12, Java 17, Spark 4.0.4 and Py4J 0.10.9.9 and executes the 39 exercise tests anew. These are actual local-process Python/Spark tests on the CI runner, not Databricks executions; illustrative Delta SQL/diagram state changes are not executed lab evidence. The global conflicting-event publication gate and retained stale report policy are unchanged.

The final PR description records the **final commit, exact-head workflow/job/artifact and inspected result**, avoiding a self-referential SHA in committed documentation. The workflow checks the PR head, writes `tested-head.txt`, and uploads synthetic browser/source/extension/exercise evidence. It has no deployment trigger. Historical workflow 35471426108 is only the starting release evidence, never evidence for this change.

Before and final after screenshots are in `docs/evidence/teacher-first/`; full automated journey screenshots and functional observations are also in the exact-head CI artifact. [Interaction research](UI-RESEARCH.md) explains the concrete defects corrected during iteration. Native visual review logs distinguish full-resolution inspection from compact overview previews.

No independent learner study, clinical efficacy, official Databricks curriculum/leveling judgment, production-origin migration, physical device coverage or actual Databricks workspace execution is claimed. A green suite does not prove Tahir's preference; the reviewable course is complete enough to evaluate directly. Work stops at the complete PR. Any later publication requires its own explicit authorization and compatible schema 4 recovery plan.

## Representative before and after

| View                   | Before                                                                       | After                                                                                                                                            |
| ---------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Today, desktop         | [Original reader-era start](../evidence/teacher-first/before/today-1440.png) | [Course start](../evidence/teacher-first/after/today-1440-light.png)                                                                             |
| Teaching, desktop      | [Original lesson](../evidence/teacher-first/before/reader-1440.png)          | [Controlled commit beat](../evidence/teacher-first/after/deck-1440-light.png)                                                                    |
| Teaching, phone        | [Original lesson](../evidence/teacher-first/before/reader-390.png)           | [Dark deck](../evidence/teacher-first/after/deck-390-dark.png)                                                                                   |
| Module reference/cards | —                                                                            | [Handbook panel](../evidence/teacher-first/after/handbook-1440-light.png), [extension cards](../evidence/teacher-first/after/cards-390-dark.png) |
