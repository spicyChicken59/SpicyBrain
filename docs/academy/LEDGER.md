# Academy completion — work ledger

Resumable state for the `feat/databricks-academy-completion` branch. Each entry
distinguishes **authored** (files exist), **integrated** (registered in
`course.json` / build), **validated** (check scripts and tests pass) and
**reviewed** (editorial pass recorded). "File exists" is never "complete".

## Environment facts (2026-09-23)

- Base: `main` at `2cde73d902b296ca4bae13dcc31ff6f6ace9e917` (tree
  `a0ea4f719728a8fde865545944f4a295b75cae90`), zero open PRs, branches
  `main`, `feat/teacher-first-course`, `feat/study-hub-reliable-data-foundations`,
  `feat/spicybrain-v1` only.
- Node 24.19.0 via nvm (`/opt/nvm`), npm 11.17.0; `npm ci --ignore-scripts` clean.
- Baseline production build: `dist/assets/index-*.js` 1,384,441 B raw /
  365,221 B gzip; CSS 130,115 B / 24,489 B gzip. Baseline unit tests: 141 pass.
- Python 3.12.3 (`/usr/bin/python3.12`), Java 21.0.10 (CI pins Java 17),
  PostgreSQL 16 client/server packages present.
- Lab environments: `<lab-envs>/spark-env` (pyspark 4.0.4, py4j
  0.10.9.9, delta-spark 4.0.0, pandas 3.0.6, pyarrow 25.0.1);
  `<lab-envs>/ml-env` (mlflow 3.16.1, scikit-learn 1.9.1, pandas 3.0.6,
  numpy 2.5.3, scipy 1.18.1).
- Browsers: Playwright 1.63.0 expects Chromium build 1243; the sandbox has
  Chromium 141 (build 1194) at
  `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`, used through
  `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`. WebKit is not installed and cannot be
  downloaded here (`playwright install` fails: download blocked), so WebKit is
  a CI-only gate in this session (`SKIP_WEBKIT=1` locally).
- Network: PyPI reachable. Documentation and video hosts (docs.databricks.com,
  learn.microsoft.com, spark.apache.org, docs.python.org, mlflow.org,
  youtube.com, delta.io) are blocked by the egress proxy for both `curl` and
  the WebFetch tool. WebSearch works and returns titles, URLs and snippets.
  Consequence: no page body can be read in this session; every new source
  record states this in `reviewedEvidence`, and video placements cannot be
  reviewed or playback-verified here.

## Ledger

| Date | Item | Authored | Integrated | Validated | Reviewed | Notes |
|---|---|---|---|---|---|---|
| 2026-09-23 | Branch, environment, baseline measurements | — | — | yes | — | see above |
| 2026-09-23 | Schema: tracks/labs/guides/cases/crosswalk; module package files; `media-*.json` | yes | yes | typecheck+validate | — | `src/content-schema.ts`, `scripts/content.ts` |
| 2026-09-23 | `scripts/academy-check.ts` (isolated module check + course audit) | yes | yes | smoke | — | |
| 2026-09-23 | Academy contract manifest `content/courses/dbxfe/academy.json` | yes | yes | — | — | 48 modules, 24 labs, 32 guides |
| 2026-09-23 | Baseline browser walk of `main` build (16 routes × desktop/phone × dark/light) | yes | — | yes | — | `docs/academy/evidence/baseline/manifest.json`; fresh profile, synthetic only |
| 2026-09-23 | `scripts/package-labs.py` deterministic lab packaging | yes | — | smoke | — | |
| 2026-09-23 | Module D3 `dbxfe-aws` | yes | yes (registered) | academy-check PASS | spot-checked | 13 beats, 12 core, 4 ext, 4 Samajh |
| 2026-09-23 | Engine: two-tier catalog lazy loading | yes | yes | unit 145, e2e 47, extension PASS (agent copy); clone re-validation in progress | — | initial JS 916,247 B raw / 226,797 B gzip; `docs/academy/SCALE.md` |
| 2026-09-23 | Labs L02, L03 (retained A3); L06, L10 (retained B3) | yes | packaged, indexed; not yet in course.json | run-labs.py re-execution PASS (9/9/24/19) | — | |
| 2026-09-23 | Field guides FG01–FG32 | yes (64 files) | not yet (links target unregistered modules) | guideSchema + contract ids PASS | pending | |
| 2026-09-23 | Eight case analyses + crosswalk | yes (17 files) | no | shape + refs | pending editorial | search-level evidence only; publishedAt unknown for all eight |
| 2026-09-23 | Capstones: Cinderline deepening, service knowledge, coexistence | yes | not yet | scenarioSchema PASS; Cinderline identities preserved | pending | fragments under `content/courses/dbxfe/capstones/` |
| 2026-09-23 | Retained-module deepening | yes | yes | academy-check PASS ×16; 179 core cards, 37 Samajh, 136 beats | pending | one extension card revision → 2 |
| 2026-09-23 | Wave 2 modules: B2+L05, B4+L08, B5+L07, A2+L01, C1+L11, C6+L13, E2+L18, E3+L17 | in progress (agents) | no | no | no | |
| 2026-09-23 | Wave 3 modules: D4, D5, D6, C4, C5, E4, F5, F6 | in progress (agents) | no | no | no | |
| 2026-09-23 | Engine: tracks course map, lab shelf, guides, cases, crosswalk, capstone notices | in progress (agent) | no | no | no | |
| 2026-09-23 | Container restart (about 05:17 UTC); authoring resumed in four workflows (two authors each) plus the engine-views workflow | — | — | — | — | assignments in the integrator's scratch assignment file; partial work reused only where correct |
| 2026-09-23 | Labs CI job (`package-labs --check`, per-runtime pins, `run-labs --from-zip`) | yes | yes | CI green at 34665ad | — | a relative-path defect found by CI and fixed |
| 2026-09-23 | Gates: download identity (root + nested), public safety, original ZIP extracted and executed in CI | yes | yes | clean-clone PASS | — | public-safety test caught build-machine paths in two lab packages; fixed |
| 2026-09-23 | Disposition check (`scripts/academy-disposition.py`) | yes | yes | 2,435 retained identities, 0 removed | — | 12 materially deepened retained beats versioned 1.1.0 |
| 2026-09-23 | Reader: saved place kept above the first section (G16) | yes | yes | regression test fails without fix; flaky detour test 8/8 | — | found by an intermittent e2e failure |
| 2026-09-23 | A2 `dbxfe-python` + L01 (36 tests) | yes | registered | academy-check PASS; lab from source and ZIP | pending | mutation check shipped in the package |
| 2026-09-23 | A4 `dbxfe-spark-execution` + L04 (14 tests) | yes | registered | academy-check PASS; lab from source and ZIP | pending | adaptive build side varies; test accepts either |
| 2026-09-23 | C2 `dbxfe-analytical-sql` + L12 (51 tests) | yes | registered | academy-check PASS; lab from source and ZIP | pending | |
| 2026-09-23 | E2 `dbxfe-features` + L18 (25 tests) | yes | registered | academy-check PASS; lab from source and ZIP | pending | |
| 2026-09-23 | G5 `dbxfe-lakebase` + L23 (18 tests, platform guide on local PostgreSQL 16) | yes | registered | academy-check PASS; lab from source and ZIP | pending | ten Lakebase steps recorded as not executed |
| 2026-09-23 | Registration policy | — | — | — | — | teaching JSON is auto-discovered, so a module is committed only together with its `course.json` registration; guides/cases/labs/capstones register once every linked module exists |
| 2026-09-23 | Lab walkthroughs: H1 dropped, H2→H3 (the renderer shows h3/h4 only) | yes | yes (14 committed; new ones fixed at integration) | ZIPs unchanged | — | `8c6b13b` |
| 2026-09-23 | Engine: generic collection views (tracks map, routes, lab shelf, guides, cases, crosswalk, capstone notices, Markdown audit) | yes | yes | check, nested build, prettier, `test:collections` 22, extension proof; CI green at `ff04aa3` | independent diff review: 5 medium + 3 low, all fixed with failing tests | `ab9a8ef` |
| 2026-09-23 | G22: photography fixture carries tracks, a route, a lab with a download and a guide; extension proof covers them, renames, export/import and cleanup | yes | yes | isolated: check 159 unit, extension PASS; CI green | — | `a44d77d` |
| 2026-09-23 | D4 `dbxfe-azure` | yes | registered | academy-check PASS; isolated unit tests | pending | `e73bb2c` |
| 2026-09-23 | F4 `dbxfe-tools` + L22 (41 tests; mutation check 9/9 re-run) | yes | registered | academy-check PASS; lab from source and ZIP | pending | `ff04aa3` |
| 2026-09-23 | Agent quota exhausted 08:10–10:10 UTC: every author, fixer and reviewer stopped mid-work; partial files kept on disk and reused | — | — | — | — | relaunched at 10:12 with fewer concurrent agents |
| 2026-09-23 | E5 `dbxfe-forecasting` + L19 (41 tests), completed from the stopped author's files | yes | registered | academy-check PASS; lab from source and ZIP | pending | `c501c7d` |
| 2026-09-23 | Package source caveats now state how each URL was checked (15 records); media and source review generators | yes | yes | prepare:content in isolation | — | `d772bed` |
