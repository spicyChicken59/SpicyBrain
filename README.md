# SpicyBrain

**Learn it. See it. Use it. Remember it.**

A static, content-driven learning platform. Choose a course, follow its module map, and learn one visual beat at a time. Each module connects **Deck, Handbook and Cards**: concise English teaching, controlled diagrams, optional Samajh analogies, in-context definitions, deliberate answer reveals and exact resumption. Today, Courses, Review and Notebook keep the main route small.

The Databricks course is **Databricks: Build, Explain, Deliver**, an independent academy of **48 modules in eight tracks**:

- platform and working fluency;
- reliable data engineering;
- analytics, performance and economics;
- governance and cloud architecture;
- machine learning and production evaluation;
- GenAI, agents and applications;
- architecture, migration and operations;
- customer discovery, evidence and delivery.

It has **580 teaching beats**, **1,367 visual states** and **824 cards** (632 core, 192 extension), a check on every beat and an applied task in every module. Nine suggested routes run through it. An essential route covers the platform through to tables you can trust, and eight deeper routes follow particular interests. Every route is optional reading order, never a lock.

Beside the modules sit:

- a **lab shelf of 24 labs**: 20 executed locally in pinned environments, 2 tabletop exercises and 2 platform guides, each download hash-validated;
- **32 field guides**, each with an action page, a completed fictional example and a template you can draft in the Notebook;
- **three capstones** with data packs;
- **eight source-attributed public case analyses**;
- an optional crosswalk to official learning paths.

The sixteen modules of the earlier release are part of the academy with their identities and history intact: all 43 original lessons, 96 checks, 18 SVG diagrams, the scenarios, the Cinderline capstone and 16 reviewed video placements. Video players contact their providers only after an explicit load choice.

Cinderline, Harrowgate, Northbrook, the conversations, datasets, targets and figures are fictional or hypothetical. Cloud-specific examples are labelled with their cloud. This is independent education. It is not Databricks Academy, not official onboarding, not an interview question bank, not a credential and not an employer assessment, and it earns no credit with any publisher. Local Python/Spark/ML execution is reported per lab; no execution on the Databricks platform is claimed.

## Run locally

Node **24.19.0** (see `.nvmrc`) and npm. Dependencies are pinned in `package-lock.json`.

```sh
npm ci
npm run prepare:content
npm run dev
```

For production acceptance from a fresh checkout (no generated files are required beforehand):

```sh
npm ci --ignore-scripts
npm run check
APP_BASE=/SpicyBrain/ APP_OUT=dist-nested npm run build
npx playwright install --with-deps chromium webkit
npm run test:e2e
npm run test:content-extension
npm run test:collections
npm run report:sources
# Optional exercise runtime: Python 3.12, Java 17
python -m pip install -r content/exercises/reliable-data/requirements.txt
python content/exercises/reliable-data/run_tests.py --spark --evidence docs/evidence/reliable-data-ci.json
```

The academy's labs are checked the way CI's `labs` job checks them: every download must match its source directory, then each local-executed lab runs from its extracted ZIP in the environment its evidence records (Python 3.12 and Java 17; exact pins only):

```sh
python scripts/package-labs.py --check
python scripts/lab-requirements.py spark > spark-pins.txt && python -m venv .labs/spark && .labs/spark/bin/python -m pip install -r spark-pins.txt
python scripts/lab-requirements.py ml > ml-pins.txt && python -m venv .labs/ml && .labs/ml/bin/python -m pip install -r ml-pins.txt
python scripts/run-labs.py --from-zip --python python --spark-python .labs/spark/bin/python --ml-python .labs/ml/bin/python --evidence-dir test-results/labs
```

`npm run check` validates and generates the content catalog/search before typechecking. It does not depend on install scripts or a previous build.

`npm run preview` serves the root production build on loopback port 4173. Browser acceptance launches its own loopback-only static server on 4183. Root output is `dist/`; the optional nested output is `dist-nested/`. Hash routes need no host rewrite. `report:sources` writes a dated availability report independently from the build gate.

## Study data

Reading requires no account or workspace. Notes, drafts, completion, attempts, review history, bookmarks, and settings stay in this browser and origin in IndexedDB. There is **no automatic sync**, analytics, AI endpoint, or remote learner-state service. Clearing/evicting storage can lose progress. Export/import is manual backup and transfer. Local storage is not a secure vault; keep confidential customer/employer material elsewhere. This is not an offline/PWA app.

## Review and authorship

Academy release (this milestone):

- [Sanitized implementation contract](docs/academy/CONTRACT.md) and [acceptance record, gates G01–G25](docs/academy/ACCEPTANCE.md)
- [Coverage](docs/academy/COVERAGE.md), [preservation and revisions](docs/academy/DISPOSITION.json) and [lab manifest](docs/academy/LABS.json)
- [Builder editorial review](docs/academy/EDITORIAL-REVIEW.md), [source review](docs/academy/SOURCE-REVIEW.md) and [media review](docs/academy/MEDIA-REVIEW.md)
- [Visual review of every state](docs/academy/VISUAL-REVIEW.json) and [scale and loading](docs/academy/SCALE.md)
- [Release candidate, study-data compatibility and rollback](docs/academy/RELEASE.md)

Earlier releases and general reference:

- [Teacher-first milestone and acceptance boundaries](docs/teacher-first/MILESTONE.md)
- [Teacher-first coverage](docs/teacher-first/COVERAGE.md), [editorial review](docs/teacher-first/EDITORIAL-REVIEW.md) and [media review](docs/teacher-first/MEDIA-REVIEW.md)
- [Architecture and supported boundaries](docs/ARCHITECTURE.md)
- [Add or revise a content package](docs/AUTHORING.md), including tracks, routes, labs, field guides, cases and capstones
- [Study data, migration, and review algorithm](docs/STUDY-DATA.md)
- [Source review and current caveats](docs/SOURCE-REVIEW.md)
- [Builder editorial review of every lesson and diagram](docs/EDITORIAL-REVIEW.md)
- [Study-hub assignment and boundaries](docs/STUDY-HUB-MILESTONE.md)
- [Study-hub acceptance evidence](docs/STUDY-HUB-ACCEPTANCE.md) and [historical initial acceptance](docs/ACCEPTANCE.md)
- [Technical curriculum and source review](docs/RELIABLE-DATA-CURRICULUM.md)
- [Executable local exercises and evidence](docs/EXERCISES.md)
- [Recorded hosting checkpoint — this milestone does not publish](docs/DEPLOYMENT.md)
- [Verified starting state](docs/STARTING-STATE.md) and [assignment derived from the supplied PDF](docs/IMPLEMENTATION-CONTRACT.md)

The SpicyChicken design source is pinned to `14a752dd0269bd6ebbb7080eb0d9e1922cd1ef2c` / v2.13.0, with immutable file hashes in `public/design-system/provenance.json`. The source CSS is copied to generated CSS with its remote font import removed; fonts are served locally. Only CSS and the original chick marks are loaded. [Design and font rights](docs/ATTRIBUTION.md) remain separate. No blanket license is granted for original course or brand assets.

The implementation PR is for independent review. It does not merge or publish a website, provision cloud resources, or establish independent acceptance.
