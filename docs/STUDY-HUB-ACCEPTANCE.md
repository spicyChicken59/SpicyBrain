# Study-hub acceptance — 19 September 2026

Builder verification for the approved [study-hub milestone](STUDY-HUB-MILESTONE.md). Starting base: `a3e858937ef72b0f7a6a474650def0b7b9e8ab23`; branch: `feat/study-hub-reliable-data-foundations`. The PR records the final head, exact-head workflow, job and artifact links. This document records local observations; it is not independent learner validation or deployment acceptance.

The initial results below describe the milestone at `88e81ebb456d631f0fc30de875ea5c85439dfefa`. They did not cover the subsequently reproduced unkeyed provenance conflict. The bounded same-PR correction, original failures, corrected execution and affected-reader evidence are recorded in [PUBLICATION-GATE-CORRECTION.md](PUBLICATION-GATE-CORRECTION.md). The original green workflow is not acceptance for the correction head.

## Before and after

The prior entry started a role-oriented course. The new Today offers the content-defined Reliable Data Foundations path, while a returning learner retains the actual saved topic/section. Learn provides roadmaps, direct topics and task references into the same canonical content. Practice, scenarios and the capstone remain accessible. Explicit path context governs previous/next; a direct topic visibly falls back to its own course. Search/playbook detours preserve the original resume, including a detour to another section of the same topic. Revised and removed content states are explained rather than silently completed or reset.

Real local production screenshots are in [before/after evidence](evidence/study-hub/): desktop 1440×1000, mobile viewport 390×844, narrow 320×844 and large-text reflow. The before captures used the baseline interface and content with only the documented Windows build/server compatibility and record-schema support in place; they are not a claim of rerunning the old commit unchanged. The evidence manifest records source hashes. The after screenshots are synthetic browser captures, not product mockups.

## Observed gates

| Evidence class | Result |
| --- | --- |
| App/content deterministic checks | `npm run check`: preparation, preservation/schema validation, TypeScript, ESLint, **68 tests passed**, production build. |
| Static serving | Root `dist` and `/SpicyBrain/` nested `dist-nested` production builds passed; real root/nested navigation and assets exercised. |
| Browser | **20 journeys passed**: 19 Chromium and one WebKit mobile emulation smoke. Chromium 153.0.8010.12, Playwright 1.63.0, Windows; WebKit 26.6. No physical-device claim. |
| New journey | Fresh path, take/skip bridge without completion, prerequisites/outcomes, explained solution reveal, single check set, served ZIP download, mobile/narrow/reduced-motion views. |
| Context | Same canonical topic through two paths and directly; previous/next, reload/back/forward, section resume, search/playbook/same-topic detours, removed path, all-complete and revised-topic cases. |
| Baseline upgrade | Native baseline schema-2 root and actual schema-2 JSON backup, with every record family and historical timestamps; schema-3 path-context export and fresh-context file import. See [native migration evidence](evidence/study-hub/after/baseline-v2-migration.json). |
| Safety regressions | Concurrent stale-tab/empty merge, pending edits and divergent notes/drafts, changed-preview reconfirmation, native transaction abort, malformed/future imports, exact 16 MB/+1 UTF-8 byte capacity, >5 MB download/import/recovery, >20 MB framed and old monolithic compatibility, denied/quota/blocked storage, review boundaries/revisions and separate extra practice. |
| Accessibility/privacy | Keyboard use, visible focus, diagram Escape/focus return/zoom, light/dark axe checks, touch emulation, code/table internal scroll, 320px doubled-text reflow, no page overflow; synthetic private markers absent from production files/network requests. |
| Content-only extension | Final isolated photography course/path/playbook check passed. Rename/reorder/revision preserves state; cleanup removes fixture inputs. [Manifest](evidence/content-extension.json) asserts `runtimeSourceChanges: []`. |
| Source availability | 37/37 URLs reachable, recorded separately from factual claim review. Reachability does not validate a claim. |

The fixed-size legacy regression continues to reproduce the original **5,118,056-byte** backup. Its IDs/order are pinned to the original 36-lesson sections so curriculum additions cannot silently change that reproduction. Existing safety tests were retained.

## Curriculum and execution

The [coverage/editorial matrix](RELIABLE-DATA-CURRICULUM.md) covers ten core topics and two bridges. Catalog totals: **43 lessons, 144 cards, 96 checks, 18 diagrams, 12 scenarios and one capstone**. Five existing canonical topics are deepened; seven new topics use new IDs. The [disposition map](CURRICULUM-DISPOSITION.md) and [exact preservation audit](evidence/curriculum-preservation-audit.json) retain all 36 original bodies, 252 section records, 108 cards and 72 original full question/option/rationale sets. Old assessment answers were not rewritten to manufacture a revision; new assessed mechanisms receive new IDs. Materially deepened lesson versions are incremented.

The local exercise run actually executed **30 tests, zero failures/errors/skips**, using Python **3.12.14**, Temurin Java **17.0.20.1+1**, Spark **4.0.4**, and Py4J **0.10.9.9**. It covers independent literal rows/types/intermediate expectations, baseline, replay, older arrivals, correction, invalid/current unresolved state, cross-batch conflicts, guarded updates, injected boundaries, local effect idempotency and an order-line transfer task. Seven exact displayed examples and their changed-input tasks were executed; [displayed-code verification](evidence/displayed-code-verification.json) matches their final hashes. [Execution evidence](evidence/reliable-data-execution.json) includes fixture/program/output hashes, versions, results and an actual local Spark plan. The extracted ZIP separately passed 21 Python tests plus archive integrity/path/security checks.

The initial Spark 4.0.1 Windows worker attempt failed; the documented upstream issue led to the compatible 4.0.4 exercise-only maintenance update and a complete rerun. Windows launcher cleanup printed an access-denied message after the successful suite; exit status was zero and a subsequent check found no remaining Java process. This is recorded as environment behavior, not a skipped test. See [EXERCISES.md](EXERCISES.md) for reproduction.

**No Delta or Databricks workspace, Jobs, cloud permissions, networking or real notification execution occurred.** Delta/Databricks instructions explicitly identify reviewed, unexecuted target environments. Local programs do not establish scalable production streaming or performance. All data and customer scenarios are fictional. Editorial review was performed by the builder team, not independent learners.

## Limits and release boundary

The complete static catalog remains one bounded client bundle (approximately 394 KB gzip JavaScript); the build emits its existing large-chunk advisory. This is not a measured production-scale performance claim. Study state remains browser/origin-local, with no automatic sync; browser eviction and closing unsaved work can still lose data. Existing export/recovery limitations are documented in [STUDY-DATA.md](STUDY-DATA.md).

The existing Site checkpoint is attributed in [DEPLOYMENT.md](DEPLOYMENT.md), not freshly deployed or verified here. This milestone changes no hosting settings, origin, secrets, cloud resources, schedules or sibling repositories. The shared design files remain untouched. Ready for independent review only after the PR's exact-head workflow passes; **NOT merged or deployed**.
