# SpicyBrain

**Learn it. See it. Use it. Remember it.**

A static, content-driven learning app for explanations, diagrams, applied practice, retrieval, notes, and resumption. Its first course is **Databricks pre-sales field engineering**, independent role-ramp material for someone new to the job. It is not official onboarding, interview preparation, a credential, or an employer assessment.

The complete course contains 12 modules, 36 lessons, 108 flashcards, 72 explained questions, 12 original diagrams, 12 applied scenarios, and a separate fully worked capstone. Cinderline Components, all customer conversations, datasets, targets, and commercial figures are fictional or hypothetical. AWS is the educational cloud. No real Databricks execution is claimed.

## Run locally

Node **24.19.0** (see `.nvmrc`) and npm. Dependencies are pinned in `package-lock.json`.

```sh
npm ci
npm run prepare:content
npm run dev
```

For production acceptance:

```sh
npm run check
APP_BASE=/SpicyBrain/ APP_OUT=dist-nested npm run build
npx playwright install --with-deps chromium webkit
npm run test:e2e
npm run test:content-extension
npm run report:sources
```

`npm run preview` serves the root production build on loopback port 4173. Browser acceptance launches its own loopback-only static server on 4183. Root output is `dist/`; the optional nested output is `dist-nested/`. Hash routes need no host rewrite. `report:sources` writes a dated availability report independently from the build gate.

## Study data

Reading requires no account or workspace. Notes, drafts, completion, attempts, review history, bookmarks, and settings stay in this browser and origin in IndexedDB. There is **no automatic sync**, analytics, AI endpoint, or remote learner-state service. Clearing/evicting storage can lose progress. Export/import is manual backup and transfer. Local storage is not a secure vault; keep confidential customer/employer material elsewhere. This is not an offline/PWA app.

## Review and authorship

- [Architecture and supported boundaries](docs/ARCHITECTURE.md)
- [Add or revise a content package](docs/AUTHORING.md)
- [Study data, migration, and review algorithm](docs/STUDY-DATA.md)
- [Source review and current caveats](docs/SOURCE-REVIEW.md)
- [Builder editorial review of every lesson and diagram](docs/EDITORIAL-REVIEW.md)
- [Acceptance evidence and limitations](docs/ACCEPTANCE.md)
- [Deployment preparation — no hosting selected or published](docs/DEPLOYMENT.md)
- [Verified starting state](docs/STARTING-STATE.md) and [assignment derived from the supplied PDF](docs/IMPLEMENTATION-CONTRACT.md)

The SpicyChicken design source is pinned to `14a752dd0269bd6ebbb7080eb0d9e1922cd1ef2c` / v2.13.0, with immutable file hashes in `public/design-system/provenance.json`. The source CSS is copied to generated CSS with its remote font import removed; fonts are served locally. Only CSS and the original chick marks are loaded. [Design and font rights](docs/ATTRIBUTION.md) remain separate. No blanket license is granted for original course or brand assets.

The implementation PR is for independent review. It does not merge or publish a website, provision cloud resources, or establish independent acceptance.
