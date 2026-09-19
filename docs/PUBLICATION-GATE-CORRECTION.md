# PR #2: unkeyed provenance conflict correction

This is a bounded correctness correction within the approved Study Hub + Reliable Data Foundations milestone. Repository `spicyChicken59/SpicyBrain`, branch `feat/study-hub-reliable-data-foundations`, starting correction head `88e81ebb456d631f0fc30de875ea5c85439dfefa`, unchanged main/base `a3e858937ef72b0f7a6a474650def0b7b9e8ab23`. The existing [PR #2](https://github.com/spicyChicken59/SpicyBrain/pull/2) records the final correction commit and exact-head workflow/job/artifact links. Nothing in this document authorizes website publication.

## Reproduced failure, kept separate from corrected runs

Guidance independently executed the unchanged reference on Python 3.13.5/Linux: three controls passed and two regressions failed. That isolated review did not include the full repository, browser, Spark or Databricks acceptance. Guidance reported that GitHub network failure prevented cloning/rendering the full product; this correction does not recast that review as independent browser certification.

Before editing, the builder separately reproduced both cases on Python 3.12.14/Windows using the unchanged reviewed source. The [original reproduction evidence](evidence/publication-gate-original-reproduction.json) records the source commit, Git blob `a892130d93ade7c14040d0158a8bf3ae7f4e3f2a`, source SHA-256, runtime, raw/conflict/quarantine evidence and the two failed semantic assertions. Each case ran independently so the first failure could not hide the second.

| Reproduction | Unchanged source | Required corrected behavior |
| --- | --- | --- |
| First report: conflicting `unkeyed` event payloads with null inspection IDs | Recorded conflict, empty unresolved keys, incorrectly published an empty report and one local effect | Preserve rows/conflict; `publication_allowed=false`, `blocked_no_snapshot`, no report or effect |
| Baseline, first unkeyed row, then its contradiction plus A v3=14/1 | Incorrectly replaced 20/1 with 22/1 and added a second effect | Diagnostic candidate may be 22/1; exact prior 20/1 report remains `stale_previous`, with effects unchanged |

## Smallest coherent policy correction

The Python gate now requires both no blocked inspection keys and no conflict evidence. The conflict list remains global evidence; no fake inspection key is created. Raw payloads, quarantine reasons and conflict indices remain available. Nonconflicting quarantine and baseline B's disclosed accepted-only exclusion continue to permit publication.

SQL and PySpark keep their transformation role. Both expose actual event/revision conflict evidence and a one-row publication decision with independent conflict and unresolved-key counts. Unusable inspection IDs cannot become business-revision identities or fake unresolved keys. A nonempty event ID can still identify contradictory payloads without an inspection key. Their publication relation is a diagnostic decision; only the separate Python `LocalPipeline` simulates the published snapshot and idempotent local outbox.

The original exercise policy is being implemented consistently; this is not a new Databricks requirement. No cloud execution, real notification or website deployment is involved.

## Learner-facing material and evidence preservation

The complete corrected Python and Spark sources are embedded in the existing resolution lesson and included in the regenerated download. The worked example, attempt, solution and bundle instructions explain the first-run block and why a valid 22/1 candidate cannot replace a verified 20/1 report while global provenance remains unresolved.

Lesson `dbxfe-record-resolution` advances from 1.0.0 to 1.1.0; the existing publication question q2 and quarantine/conflict card1 advance from revision 1 to 2 because their assessed scope changes. Course metadata advances to 2.0.1. All IDs and other assessment revisions are preserved. The [editorial review](RELIABLE-DATA-CURRICULUM.md#bounded-publication-gate-correction--19-september-2026) records these decisions. Inventory remains 43 lessons and the same ten-core/two-bridge path.

The focused production-browser regression seeds actual prior q2/card1 definitions copied from the reviewed commit, an earlier-version note, lesson/section completions, objective attempt, review event and schedule. It checks revision notices while preserving those records and timestamps through source/solution expansion, download and reload. It verifies the entire rendered Python/Spark source against files and hashes actual downloaded bytes. Desktop 1440px uses root serving; 390px uses the nested production build. This is builder browser evidence with synthetic learner state, not physical-device or independent learner validation.

## Corrected local validation

The [local acceptance manifest](evidence/publication-gate-local-acceptance.json) was derived from the completed command logs and actual reader/download evidence. All existing applicable tests were retained.

| Gate | Observed result |
| --- | --- |
| Clean installation and app/content checks | `npm ci --ignore-scripts`, then `npm run check`: content preparation/validation, TypeScript, ESLint, 68 deterministic tests passed with no failures/skips, root production build. |
| Static serving | `/` and `/SpicyBrain/` production builds passed, with actual navigation and download checks. |
| Complete browser suite | 22 passed: 21 Chromium and one retained WebKit mobile-emulation journey. Playwright 1.63.0; Chromium 153.0.8010.12; local Windows 11. No required browser test skipped. |
| Content-only extension | Photography course/path/playbook, rename/reorder/revision and cleanup passed; manifest asserts `runtimeSourceChanges: []`. |
| Link availability | 37/37 URLs reachable; kept separate from source/claim review. This correction changes original exercise policy implementation, not external product facts. |
| Full source exercise suite | 39 passed, zero failures/errors/skips: 26 Python tests plus 13 Spark/displayed-example tests. Python 3.12.14, Temurin Java 17.0.20.1+1, Spark 4.0.4/Py4J 0.10.9.9. [Actual outputs and hashes](evidence/reliable-data-execution.json). |
| Extracted downloadable ZIP | Independently extracted 37 members; CRC/path checks and byte-for-byte source comparison passed. The complete extracted Python/Spark suite also passed 39 tests with zero failures/errors/skips and exit 0. [Bundle checks](evidence/reliable-data-bundle-check.json), [actual extracted execution](evidence/publication-gate-extracted-execution.json). |
| Displayed-code reconciliation | All 11 manifest entries match current lesson fences and tested source/fragments. Exact embedded resolver and SQL/PySpark implementations execute the corrected decision tests. [Verification](evidence/displayed-code-verification.json). |

The nine added exercise tests cover both independently reproduced cases, missing/null/empty/spaces/tabs/Unicode-space keys, forward/reversed/repeated deliveries, cross-batch retained history, quarantine-only controls and the actual SQL/PySpark decision boundary. Existing known-key conflicts, invalid current versions, older/equal versions, valid corrections, failure recovery and effect idempotency still pass. Spark's `SUM` of an empty candidate is null while Python's empty sum is zero; tests preserve that engine distinction and neither candidate is a published report during conflict.

Screenshots from the final local production run were visually inspected for readable prose, revision notices, expanded source, solution and internal code scrolling. The screenshots and per-reader JSON contain only synthetic state:

| View | Desktop 1440px | Mobile layout 390px |
| --- | --- | --- |
| New worked example | [Desktop example](evidence/publication-gate/publication-gate-example-1440.png) | [Mobile example](evidence/publication-gate/publication-gate-example-390.png) |
| Explained solution | [Desktop solution](evidence/publication-gate/publication-gate-solution-1440.png) | [Mobile solution](evidence/publication-gate/publication-gate-solution-390.png) |
| Corrected Python gate | [Desktop source](evidence/publication-gate/publication-gate-decision-reference-code-1440.png) | [Mobile source](evidence/publication-gate/publication-gate-decision-reference-code-390.png) |
| SQL/PySpark decision | [Desktop source](evidence/publication-gate/publication-gate-decision-spark-code-1440.png) | [Mobile source](evidence/publication-gate/publication-gate-decision-spark-code-390.png) |
| Earlier completion notice | [Desktop revision](evidence/publication-gate/publication-gate-revision-1440.png) | [Mobile revision](evidence/publication-gate/publication-gate-revision-390.png) |
| Revised card, future original due date | [Desktop review](evidence/publication-gate/publication-gate-review-1440.png) | [Mobile review](evidence/publication-gate/publication-gate-review-390.png) |

The [desktop](evidence/publication-gate/publication-gate-reader-1440.json) and [mobile](evidence/publication-gate/publication-gate-reader-390.json) records verify that the earlier note, lesson/section completions, complete historical q2 attempt, card1 review and schedule retain all fields/timestamps after expanding, downloading, entering review and reloading. Card1 appears as revised while its original due date is still in the future; it was not rerated. The actual downloaded bytes match both the course-declared hash and the packaged ZIP.

Current SHA-256 values:

- Download ZIP: `32af53617af3591ebf861857a579bd93dd86b4e1981bf4ad01c37a7353e0e4fb` (37 entries, 57,908 bytes).
- `solutions/reference.py`: `cc4a8f46270e8f1c3e1ab4a4a24d85af3b4c9611f3983fa2656ed73f87a43510`.
- `solutions/spark_transform.py`: `792a33b243ee4799a9382a3ddd7e9c4aa7080ee68de6ec611d52abcf405e1f10`.
- Local source-run outputs: `d1a0ebc09100e02eec22b323526530e4c5c88a40c87e4844d29f616be2dc7bfd`.

These are actual source-run hashes, not labels copied from the initial 30-test run. Platform-sensitive execution plans and line endings can change output/input hashes across Windows and Linux; each run records its own bytes and environment. The PR must separately record its final-head CI evidence.

The source and extracted runs produced the same output SHA-256 above. Their recorded elapsed durations were 278.188 and 276.859 seconds respectively. The extracted runner's generic `command` label uses the repository-style path; the bundle-check record specifies the actual standalone invocation `python run_tests.py --spark --evidence <repository-evidence-output>`.

Both Windows runs printed `ERROR: Access denied` after their successful test output and exited 0; a subsequent process check found no remaining Java process. The message's underlying cause was not established. This observation did not bypass or skip any required test.

## Release boundary

This correction preserves application/storage/review algorithms, import protections, large-backup policies and the shared design snapshot. The existing Site and origin remain untouched; its recorded hosting identity is continuity context only. Ready for independent re-review only once PR #2's final-head evidence passes. **Not merged or deployed.**

The existing static-catalog bundle advisory remains (current local JavaScript approximately 403 KB gzip); this correction does not claim measured performance at scale. No new access or publication capability was needed.
