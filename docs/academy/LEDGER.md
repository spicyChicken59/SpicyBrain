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
- Lab environments: `/home/user/labenv/spark-env` (pyspark 4.0.4, py4j
  0.10.9.9, delta-spark 4.0.0, pandas 3.0.6, pyarrow 25.0.1);
  `/home/user/labenv/ml-env` (mlflow 3.16.1, scikit-learn 1.9.1, pandas 3.0.6,
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
| 2026-09-23 | Pilot module A4 `dbxfe-spark-execution` + lab L04 | in progress (agent) | no | no | no | |
| 2026-09-23 | Module C2 `dbxfe-analytical-sql` + lab L12 | in progress (agent) | no | no | no | |
| 2026-09-23 | Module D3 `dbxfe-aws` | in progress (agent) | no | no | no | |
| 2026-09-23 | Engine: two-tier catalog lazy loading | in progress (agent) | no | no | no | design in agent brief; SCALE.md expected |
| 2026-09-23 | Labs L02, L03 (retained A3); L06, L10 (retained B3) | in progress (agents) | no | no | no | |
| 2026-09-23 | Field guides FG01–FG16, FG17–FG32 | in progress (agents) | no | no | no | |
| 2026-09-23 | Eight case analyses + crosswalk | in progress (agent) | no | no | no | search-level evidence only |
| 2026-09-23 | Capstones: Cinderline deepening, service knowledge, coexistence | in progress (agents) | no | no | no | fragments under `content/courses/dbxfe/capstones/` |
| 2026-09-23 | Retained-module deepening (cards ≥10, Samajh ≥2, windows beat, adoption) | in progress (agent) | no | no | no | |
