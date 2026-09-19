# Acceptance evidence

Historical PR #1 evidence follows. Current study-hub work is recorded separately in [STUDY-HUB-ACCEPTANCE.md](STUDY-HUB-ACCEPTANCE.md); the later attributed hosting checkpoint is in [DEPLOYMENT.md](DEPLOYMENT.md). Statements below about publication and PR state describe their original checkpoint.

Builder acceptance work dated **2026-09-19**, on the locally served production build. Independent guidance review reproduced two preservation defects in the initial PR; corrections require independent re-review. No live site is published and no Databricks/cloud execution was performed.

## Production coverage

| Module                                          | Lessons |   Cards | Explained checks | Diagrams | Scenarios |
| ----------------------------------------------- | ------: | ------: | ---------------: | -------: | --------: |
| 01 · Role and customer journey                  |       3 |       9 |                6 |        1 |         1 |
| 02 · Discovery and qualification                |       3 |       9 |                6 |        1 |         1 |
| 03 · Platform and data foundations              |       3 |       9 |                6 |        1 |         1 |
| 04 · Data engineering                           |       3 |       9 |                6 |        1 |         1 |
| 05 · SQL, analytics, and performance            |       3 |       9 |                6 |        1 |         1 |
| 06 · Governance, security, and cloud deployment |       3 |       9 |                6 |        1 |         1 |
| 07 · ML, GenAI, and agents                      |       3 |       9 |                6 |        1 |         1 |
| 08 · Architecture and migration                 |       3 |       9 |                6 |        1 |         1 |
| 09 · Demos and technical storytelling           |       3 |       9 |                6 |        1 |         1 |
| 10 · Proof of value                             |       3 |       9 |                6 |        1 |         1 |
| 11 · Competition and business value             |       3 |       9 |                6 |        1 |         1 |
| 12 · Field execution and capstone preparation   |       3 |       9 |                6 |        1 |         1 |
| **Total**                                       |  **36** | **108** |           **72** |   **12** |    **12** |

A separate capstone includes six required deliverable groups, six stakeholder disclosures, a complete model submission and six anchored rubric dimensions. All totals are computed and checked per module/lesson in [content-counts.json](evidence/content-counts.json).

## Deterministic and browser evidence

`npm run check` passed: production/reference/negative content validation, TypeScript, ESLint, **44 unit/integration tests**, and the production build. Synthetic arithmetic verifies correction/quarantine output and cost/value sensitivity. It is not Databricks execution.

Local runtime: Node 24.19.0, Playwright 1.63.0, actual Chromium 153.0.8010.0, Linux. Desktop 1440×1000; mobile viewport 390×844, plus a touch-enabled mobile context; 320×800 with all stylesheet text sizes doubled independently of viewport. Light/dark and reduced-motion preferences are exercised. Physical devices and assistive-technology hardware were not tested.

The corrected Chromium suite has 15 journeys: the original 12 plus native concurrent-tab import, >5 MB export/recovery restoration, and oversized legacy/framed compatibility. The separate WebKit mobile emulation smoke runs only in the WebKit project. Local WebKit 26.6 / Playwright build 2359 lacks GTK4/GStreamer and related OS libraries; `SKIP_WEBKIT=1` is a limitation, not a pass. CI uses supported Ubuntu dependencies. The initial exact-head CI run passed WebKit, but that older result does not validate these corrections; the PR links the final correction-head run.

| Gate | Observed assertions                                                                                                                                                                                                                                                                                         |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A    | Honest zero-activity start; 12 module/36 lesson map; all required distribution validated.                                                                                                                                                                                                                   |
| B    | Direct root/nested links, reload, back/forward, stable-section resume, focus exit, diagram zoom/reset/Escape/focus return, notes and bookmarks; no automatic completion.                                                                                                                                    |
| C    | Unanswered rejection, incorrect then correct attempts, all rationales, guarded double submit, original content/revision snapshots. Option-order changes are also checked in the extension.                                                                                                                  |
| D    | Native browser fixed clock exercises all four ratings, exact UTC due dates, before/at due, interruption, reveal guard, separate new allowance, session limit and unchanged extra-practice schedule. Unit tests cover caps, rounding, DST and ID tie order.                                                  |
| E    | Module scenario and capstone drafts, all stakeholder disclosures, full model, explicit per-dimension self-assessment and reload.                                                                                                                                                                            |
| F    | Title/body/CDC alias and synthetic note search, type/course labels, source navigation and immediate navigation after final edit.                                                                                                                                                                            |
| G    | Export and fresh-context import compare actual records; duplicate/conflicting/unknown merge, replace preview/cancel/confirm, future/invalid rejection and reset protection. Synthetic actual database/export v1 migration retains evidence.                                                                 |
| H    | Denied/quota storage with in-memory recovery downloads; blocked native upgrade; failed SVG and bad route; malformed import; native transaction abort retains old snapshot. Unique synthetic note marker absent from production JS/CSS and captured request URLs/payloads; all runtime requests same-origin. |
| I    | All lessons/questions/cards and diagrams reviewed; explicit broken fixtures rejected. Sources/limitations documented separately.                                                                                                                                                                            |
| J    | Complete photography fixture discovered/rendered/searched/reviewed with content-input changes only.                                                                                                                                                                                                         |
| K    | Actual note/completion/attempt/review records survive renamed/reordered module/lesson titles and files; material revision flagged and old history retained; release cleanup excludes fixture.                                                                                                               |
| L    | Real screenshots for all main surfaces; keyboard-only note entry, visible focus, modal return, touch review/diagram, light/dark axe checks, reduced motion, 390px and 320px doubled-text reflow.                                                                                                            |

## Reproduce

```sh
npm ci --ignore-scripts
npm run check
APP_BASE=/SpicyBrain/ APP_OUT=dist-nested npm run build
npx playwright install --with-deps chromium webkit
npm run test:e2e
npm run test:content-extension
npm run report:sources
```

In this constrained local environment, set `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` to the available local Chromium executable and `SKIP_WEBKIT=1`. The preview/test server must be started by the same command environment as the browser; separate tool sessions have isolated loopback contexts. No tunnel or public hosting was used to obtain browser evidence.

The CI workflow installs with lifecycle scripts disabled, asserts that catalog/search generated files are absent, and runs the now self-preparing `npm run check`. It checks out the exact PR head, records it in `test-results/tested-head.txt` **after** the runner creates its results directory, and uploads only synthetic screenshots/traces/reports. Its URL, run ID, conclusion and actual head SHA belong in the PR handoff after the run exists; no older green run is attributed to newer code. Local screenshots were generated from the implementation working tree before the first feature commit; [build-inputs.json](evidence/build-inputs.json) identifies their matching code/content inputs. Exact-head reruns and CI evidence are linked in the PR.

## Evidence files and limits

[Screenshots](evidence/screenshots/) cover Start, map, reader/dialog, practice/capstone, review, search/notebook, import and themes/recovery/reflow. The viewport is encoded by the test: `mobile-*` is 390×844, `13-narrow-text-zoom` is 320×800 at doubled text, other images are 1440×1000 except the fresh import context (1280×720). [Diagram contact sheet](evidence/diagram-contact-sheet.png) was visually inspected. All learner text in this evidence is deliberately synthetic.

[Extension manifest](evidence/content-extension.json) includes the actual added/renamed content file diff and empty engine diff. [Source availability](evidence/source-availability.json) records 23/23 HTTP 200 probes separately from the [claim review](SOURCE-REVIEW.md). A reachable URL does not prove its lesson true. [Editorial matrix](EDITORIAL-REVIEW.md) covers the complete review scope and corrections.

The build has a large-chunk advisory (about 305 KB gzip JavaScript) because the complete bounded course and search index ship together. No measured production-scale performance claim is made. Local storage can be lost or denied; unsaved memory can be lost on tab closure; there is no automatic sync. A recovery download is not a persisted browser save. WebKit local launch is unavailable; CI and physical-device status must be reported separately. No known failing Chromium acceptance assertion remains at the reported passing run. The preservation corrections and final-head CI are reported separately in the PR handoff.

## PR #1 preservation corrections

The baseline `3bbd1576442a69dbb964f2a8498e7e206d11b291` reproduced the independent review exactly: another store's saved note disappeared on merge, an empty merge erased it, and the valid 51-note export was rejected at 5,118,056 bytes. See [correction evidence](CORRECTIONS.md) for the focused regressions and final-run links in the PR. These are new preservation tests, not claims about the earlier green suite.
