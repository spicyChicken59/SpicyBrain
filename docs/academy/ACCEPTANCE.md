# Acceptance record — Databricks: Build, Explain, Deliver

Every gate is **PASS**, **FAIL** or **BLOCKED**, with the kind of evidence
behind it:

- **executed**: a command, test or browser run whose output is in this
  repository or in CI;
- **inspected**: a builder read the artefact and recorded what was found;
- **not run**: stated with the reason.

"Builder" means this build session and its agents. Nothing here is an
independent human study, an official Databricks review, or a claim that a
learner will pass anything.

Head under review: see the pull request (PR #4,
`feat/databricks-academy-completion`) for the exact head and its CI run. The
last content and code commit is recorded as `sourceCommit` in
[`release-manifest.json`](release-manifest.json). Later commits change only
documents and release records.

## Continuation status

The 2026-09-23 continuation found two factual Lakebase defects and unfinished
source and media review. Affected gates below are BLOCKED; their older evidence
is retained as historical provenance, not sufficient current acceptance.
See [`CLOSEOUT.md`](CLOSEOUT.md) for recovery and the unresolved requirements.

The 2026-09-25 continuation added explicit claim decisions for every priority
area, corrected 70 claims in fourteen modules, the Petrobras case attribution
and the L15 Azure service-tag row, and ran the rendered checks locally, which
the earlier environment could not. It changes no gate to PASS that depends on
unread sources; G10 and G14 stay BLOCKED. Remaining work is listed claim by
claim in [`CLAIM-LEADS.md`](CLAIM-LEADS.md).

## Gates

| Gate | Status | Evidence type | Evidence |
|---|---|---|---|
| G01 Repository integrity | PASS | executed | Base `2cde73d`, the merged teacher-first release; zero open PRs at start. Only this repository was written: no sibling application and no design-system repository was changed. No history was rewritten and nothing was merged or published. Build ledger: [`LEDGER.md`](LEDGER.md). |
| G02 Complete curriculum | PASS | executed | `node --import tsx scripts/academy-check.ts --write` → [`COVERAGE.md`](COVERAGE.md) / [`COVERAGE.json`](COVERAGE.json): 48 modules in 8 tracks, 580 beats (floor 480), 1,367 visual states, 824 cards (632 core + 192 extension; floor 672), an applied task with model reasoning and a rubric in every module, 24 labs, 32 field guides, 3 capstones, 8 case analyses, 10 crosswalk rows. No failing finding. |
| G03 Canonical preservation | PASS | executed | `python scripts/academy-disposition.py --check` → [`DISPOSITION.json`](DISPOSITION.json): 2,435 retained identities, 0 removed, 193 revised with their revision or version moved, 0 revisions left unmoved, 29 clarifications that kept their revision by rule. The original exercise ZIP is byte-identical (SHA-256 `32af5361…`). |
| G04 Beat teaching quality | BLOCKED | executed + inspected | `academy-check` fails a module on: an explanation outside 35–120 words; a generic or duplicate beat title; a handbook under 100 words; a visual whose text equivalent omits a state or node; a check without explained choices; placeholder text. The builder editorial review of every track ([`EDITORIAL-REVIEW.md`](EDITORIAL-REVIEW.md)) worked every example, altered examples to test transfer, and applied the confirmed findings. |
| G05 Visual correctness | BLOCKED | executed + inspected | `node scripts/visual-review.mjs` over every state of every beat's dominant visual, in five viewport/theme contexts → [`VISUAL-REVIEW.json`](VISUAL-REVIEW.json): 48 modules, 580 beats and 6,835 state renders across five contexts (1440×900 and 390×844 in both themes, 320×568 light). No render had a count mismatch with the authored state, a clipped label or sideways overflow. axe ran on the first beat of every module in every context, 240 pages, with 0 violations, and there were 0 page errors. The run used the candidate build `cb733cd`; later commits change loaders, the practice page and Sources panels, not visual rendering. 16 representative screenshots, two per track, are in [`evidence/visual/`](evidence/visual/) and were inspected by the builder. Arithmetic and state order were checked in the editorial reviews. Re-run on 2026-09-25 on the content of `4223bf5` (root build, loopback): 48 modules, 580 beats and 6,835 state renders in the same five contexts, 0 failing renders, 240 axe pages with 0 violations, 0 page errors (`VISUAL-REVIEW.json`). The corrected states of this continuation were inspected at desktop and phone width. The rendered-DOM criteria hold; the gate stays BLOCKED because the facts inside the visuals depend on the unfinished claim review (G14). |
| G06 Samajh quality | PASS | executed + inspected | 188 beats carry an optional Samajh analogy, at least 2 per module, each 25–120 words with a mapping and a boundary (`academy-check`). Preference, collapse and reopen, and keyboard access are covered in `tests/browser/teacher-first.spec.ts`. Wording was reviewed per track. |
| G07 Handbook usefulness | BLOCKED | executed | The e2e suite and the collections fixture cover anchors, independent panel scrolling, new-tab context, mobile return, the per-track handbook and print. Handbook depth was reviewed in the editorial reviews. |
| G08 Assessment correctness | BLOCKED | executed | Deterministic answer checks, unanswered, changed and double-submitted answers, and revision snapshots, in the unit and e2e suites. Every check's rationale was reviewed per track; changed assessed meaning moved revisions (G03). |
| G09 Cards and scheduling | BLOCKED | executed | Every module has at least 10 core and exactly 4 extension cards, with no duplicate prompt anywhere in the course (`academy-check`). Filters, detours, interrupted reviews, revised cards and caps are covered in the e2e suite. |
| G10 Media evidence and privacy | BLOCKED | executed privacy checks + incomplete editorial review | The 16 retained placements are unchanged. All 32 new-module records are now `blocked-review`, preserving 43 candidate leads and their history. No new playback, timestamp or transcript review is claimed. `MEDIA-REVIEW.md` and `CLOSEOUT.md` record the access limits. Optional placement does not waive candidate evaluation. On 2026-09-25 youtube.com, databricks.com and the documentation hosts again returned 403 at CONNECT through this environment's egress proxy; no video was opened, and none of the 32 records is converted to no-placement without an actual evaluation. |
| G11 Real local labs | PASS | executed | [`LABS.json`](LABS.json): 24 labs, 20 local-executed labs with 532 checks, two tabletop packages with 53 checks, and two platform guides with 34 checks (619 total), run in their recorded environments. Checks in a tabletop package or platform guide do not establish platform execution. CI's `labs` job rebuilds each environment from exact pins, re-executes every lab from its committed ZIP, and compares the result with the committed evidence. The original exercise ZIP is extracted and its advertised commands run in CI. The tabletop labs (L14, L15) and platform guides (L16, L23) record their platform steps as not executed. |
| G12 Source, snippet and download identity | PASS | executed | `tests/browser/download-identity.spec.ts` compares the bytes served by the root and nested builds with the manifest hashes. [`SNIPPETS.json`](SNIPPETS.json): 286 displayed code blocks, 22 verbatim from a lab, 8 whose lines all appear in one, 31 partial and 225 illustrative (platform-only statements, labelled). `package-labs.py --check` matches every download to its source directory member for member. |
| G13 Field guides and capstones | BLOCKED | executed + inspected | Builder review of the 32 guides, 8 cases, the crosswalk and 3 capstones, with fixes applied. `tests/browser/capstones.spec.ts` checks, for each capstone: the revision notice, the data pack bytes against the manifest, a draft kept across a reload, the disclosures, the model answer and a recorded self-assessment. `tests/browser/academy-pages.spec.ts` checks every lab, guide, case and capstone page at 390 px and at 320 px with doubled text. Revisited 2026-09-25: all eight cases were re-audited for attribution. The Petrobras case's presenter attribution was corrected to search level, and every figure in the other seven is attributed to its reporter. Four session pages (AT&T, Barilla, CVS Health, Petrobras) remain unread, so the case analyses still rest partly on search-level summaries; the gate stays BLOCKED (`CASE-CROSSWALK-REVIEW.json`). |
| G14 Source and capability review | BLOCKED | partial direct inspection | `CLAIM-REVIEW.json` deduplicates 932 documented claims: 136 retain prior evidence, 111 are reviewed, 50 are corrected and reviewed, 232 are partial and 403 are pending; 375 of the pending claims, in 20 non-priority modules, have no decision yet. Every claim in the priority areas (recovery, identity, cloud networking, managed services, Genie, AI Search and agents, sharing and federation, Lakebase) has an explicit decision. This is a work inventory, not an assertion that the pending sources are inaccessible; [`CLAIM-LEADS.md`](CLAIM-LEADS.md) lists each open claim with the source that would settle it. The URL inventory now records 179 body reads, 4 package-source reads, 83 earlier-release URLs, 273 search-only, 55 unconfirmed and 17 without a method; URL counts cannot pass this gate. `CASE-CROSSWALK-REVIEW.json` records four directly reviewed cases and nine crosswalk entries, with four session pages and one catalog page unresolved. |
| G15 Fresh learner journey | PASS | executed | `tests/browser/teacher-first.spec.ts` and `study-hub.spec.ts` take an empty collection through to the first check. |
| G16 Returning learner journey | PASS | executed | `tests/browser/reading-position.spec.ts` and `teacher-first.spec.ts` cover detours and resume. |
| G17 Existing native data | PASS | executed | Schema-3/4 fixtures migrate without clearing storage (`tests/study.test.ts`, `study-hub.spec.ts`). Same-origin forward, rollback and return between the released build and this candidate: [`evidence/rollback.json`](evidence/rollback.json). |
| G18 Concurrency and failure | PASS | executed | Stale-tab, transaction-abort, malformed-import and blocked-storage tests are retained and green. Failed lesson, scenario and reference loads each recover through Retry without losing drafts (`tests/browser/lazy-bodies.spec.ts`). |
| G19 Capacity and legacy transport | PASS | executed | UTF-8 boundary, >5 MB export, framed import and monolithic import tests are retained and green. |
| G20 Accessibility and responsive UI | PASS | executed | axe in both themes on every academy page kind (`academy-pages.spec.ts`), and on the first beat of every module in all five contexts (`visual-review.mjs`). Every academy page is checked at 390 px and at 320 px with doubled text, with no sideways scrolling. Keyboard, reduced-motion and focus checks are in the e2e suite, and CI runs WebKit. |
| G21 Scale and safe loading | PASS | executed | [`SCALE.md`](SCALE.md). At 48 modules the gate first **failed**: initial JS 2,213,006 B, +59.8% over the baseline. The reference-tier split brought it to 1,477,751 B raw (+6.7%; ceiling +15%) and 337,148 (−7.3% against the baseline) B gzip. Failed body and reference loads recover (`lazy-bodies.spec.ts`). An independent adversarial review of the split looked through three lenses (correctness, failure and accessibility, tests). It reported 14 findings, and a separate agent reproduced each one. All are fixed, each with a test that fails without the fix, and eight deliberate regressions were each caught. |
| G22 Unrelated content-only extension | PASS | executed | `npm run test:content-extension`: the photography fixture carries tracks, a route, a lab with a download and a guide. It is renamed, exported and imported, and cleaned up with no engine change (`docs/evidence/content-extension.json`). |
| G23 Exact-head CI | BLOCKED | executed locally; exact-head CI pending at document freeze | Run 55 / 35876280429 applies only to `afbe49e` (artifacts 10759390993 and 10757548905), and run 35959071529 only to `8ea004e`. On 2026-09-25, on the content of `4223bf5` in this environment: `npm run check` passes 206 tests, typecheck, lint and the build; the full Chromium browser suite passes 65 of 65 against the root and nested builds (WebKit is not installed here; CI runs its 3 WebKit tests); the visual review passes (G05); the disposition, package, lab-manifest, claim-ledger and claim-leads checks pass; and lab L15, the one lab whose files changed, re-runs from its source directory and from its ZIP with 30 of 30 checks matching the committed evidence. The exact-head CI run, jobs and artifacts of the pushed head are recorded in PR #4 metadata, avoiding a self-referential commit. |
| G24 Editorial challenge | BLOCKED | inspected | [`EDITORIAL-REVIEW.md`](EDITORIAL-REVIEW.md): a builder review of each track with altered examples, one per guide set, the cases and crosswalk, and the capstones. Every high and medium finding was reproduced before it was fixed, and rejections are recorded with reasons. Revisited 2026-09-25: the editorial challenge did not catch the factual defects that claim review later found (the Lakebase and Genie corrections on 2026-09-24 and 70 corrections in fourteen modules on 2026-09-25), so it cannot stand as evidence of factual accuracy. The three adversarial claim-review rounds of 2026-09-25 are claim-review evidence, not a replacement for the editorial challenge. The gate stays BLOCKED until claim review completes. |
| G25 Release package and privacy | BLOCKED | manifest refreshed separately; editorial release still blocked | `RELEASE.md` and `release-manifest.json` describe the 4.0.5 bytes, rebuilt on 2026-09-25 from a clean tree of the source commit the manifest records. The manifest records its source commit; final exact-head CI is kept in PR metadata. Public-safety checks pass locally. The existence of a byte manifest does not authorize release or close G10/G14. |

## Findings recorded by the gates, and what was done

- **G21 failed, then passed.** The inline catalog grew to 1.2 MB with the
  full course. The reference tier moved course sources, claims and glossary
  text, section claim ids and scenario rubric levels into lazily loaded files,
  with identity checks. Details and measurements are in [`SCALE.md`](SCALE.md).
- **The rollback check under-tested itself.** It raced the lazy guide body
  and silently skipped the guide draft, and it snapshotted storage while an
  edit was still queued. Both were corrected, and the draft is now required
  and exercised.
- **The source review over-reported pages read.** Its classifier matched
  "fetched in this build" inside "page body not fetched in this build", and
  counted 450 URLs as read where the records say 113. Negations are now
  discarded before classification. A record that says its own page was not
  fetched can never count as read, and one that says it was not checked is
  unconfirmed.
- **Coverage warnings.** [`COVERAGE.md`](COVERAGE.md) lists 109 warning
  findings, all on retained material. They are 106 distinct items, because
  the m03 scenario is reported twice and the m04 scenario three times (once
  per lesson that uses it):
  - 93 on 31 retained canonical lessons, each lacking the new solution,
    mistakes and sources sections (three per lesson);
  - 10 on retained scenarios without stakeholder disclosures;
  - three on retained check prompts that are short but complete.

  Each of the 106 items has its own decision and reason in
  [`warning-dispositions.json`](warning-dispositions.json). All 106 are
  kept: changing any of them would move revisions that learners have already
  answered against, for no change in meaning.
  `tests/py/test_warning_dispositions.py` fails if a warning has no decision
  or a decision outlives its warning. The one warning on an authoring note
  (the Delta module's editorial rationale) was fixed earlier.

## Not run, and why

- **No Databricks or cloud workspace was used.** The tabletop and
  platform-guide labs record their platform steps as not executed, and every
  local execution is labelled with its local runtime.
- **The interrupted session had documentation/video access failures.** The
  continuation directly inspected specific pages recorded in the new review
  ledgers. Four session pages, one catalog page and video review remain
  unresolved; the rest of the claim backlog is incomplete review, not a
  claim of universal network failure.
- **No independent human learner study.** Every review here is a builder
  review.
- **Nothing was merged, published or deployed.** No Pages, preview, tunnel,
  Site identity, origin, access model, repository setting, secret, schedule
  or paid service was changed. No Databricks or cloud resource was
  provisioned.
