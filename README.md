# SpicyBrain

**Learn it. See it. Use it. Remember it.**

A static, content-driven learning platform. Choose a course, follow its module map, and learn one visual beat at a time. Each module connects **Deck, Handbook and Cards**: concise English teaching, controlled diagrams, optional Samajh analogies, in-context definitions, deliberate answer reveals and exact resumption. Today, Courses, Review and Notebook keep the main route small. Databricks is the first domain; field practice applies the technical foundations.

The complete course has **16 modules, 135 teaching beats and 208 cards**: the original 144 plus 64 researched extensions. All **43 original lessons, 96 checks, 18 SVG diagrams, 12 scenarios and the capstone** remain accessible with their identities and history. New beats add their own questions, staged visuals, complete handbook sections and 16 curated video references with authored alternatives. Video players contact their providers only after an explicit load choice. Original roadmaps and playbooks remain secondary views of the canonical material.

Cinderline, conversations, datasets, targets and figures are fictional or hypothetical. AWS-specific examples are labeled. This is independent education, not official onboarding, an interview question bank, a credential or an employer assessment. Local Python/Spark execution is reported separately; no Databricks execution is claimed.

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
npm run report:sources
# Optional exercise runtime: Python 3.12, Java 17
python -m pip install -r content/exercises/reliable-data/requirements.txt
python content/exercises/reliable-data/run_tests.py --spark --evidence docs/evidence/reliable-data-ci.json
```

`npm run check` validates and generates the content catalog/search before typechecking. It does not depend on install scripts or a previous build.

`npm run preview` serves the root production build on loopback port 4173. Browser acceptance launches its own loopback-only static server on 4183. Root output is `dist/`; the optional nested output is `dist-nested/`. Hash routes need no host rewrite. `report:sources` writes a dated availability report independently from the build gate.

## Study data

Reading requires no account or workspace. Notes, drafts, completion, attempts, review history, bookmarks, and settings stay in this browser and origin in IndexedDB. There is **no automatic sync**, analytics, AI endpoint, or remote learner-state service. Clearing/evicting storage can lose progress. Export/import is manual backup and transfer. Local storage is not a secure vault; keep confidential customer/employer material elsewhere. This is not an offline/PWA app.

## Review and authorship

- [Teacher-first milestone and acceptance boundaries](docs/teacher-first/MILESTONE.md)
- [Complete course coverage](docs/teacher-first/COVERAGE.md), [editorial review](docs/teacher-first/EDITORIAL-REVIEW.md) and [media review](docs/teacher-first/MEDIA-REVIEW.md)
- [Architecture and supported boundaries](docs/ARCHITECTURE.md)
- [Add or revise a content package](docs/AUTHORING.md)
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
