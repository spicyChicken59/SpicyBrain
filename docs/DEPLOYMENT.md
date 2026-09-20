# Deployment preparation — not authorization

## Current attributed checkpoint — 20 September 2026

The supplied publishing-session record identifies the existing public [SpicyBrain Site](https://spicybrain.motahir-official.chatgpt.site), project `appgprj_6aaeb1f97b9c8191b7ec8bf746c483c7`, published **version 2**, version ID `appgprj_6aaeb1f97b9c8191b7ec8bf746c483c7~appgver_6754ac42328c819184b64047b0de68fb`, source main `e3bfb97414026e223696312e987879608cc34416`, and hosting snapshot `b8a53637079caae4dba7d1e3438da5d831c9a235`. That session reported live same-origin migration, desktop/mobile/export/import checks and 73 exact non-HTML file hashes; inspected Cloudflare JavaScript Detections injection caused an HTML CSP warning. These remain **attributed historical publication evidence**, not a new live-origin verification by this teacher-first milestone. No CSP script policy was weakened. GitHub remains the application repository; merging does not publish to Sites.

This milestone authorizes one implementation PR, with no merge or deployment. Do not create another Site, change repository/hosting settings, enable Pages, change origin, or deploy this PR. Later authorized publication must reverify this same Site identity, source/build hashes, access model, and live learner-state continuity. Local native-storage tests are not a production-origin migration test.

The existing version-2 Site and its recovery materials remain unchanged. Version1 was already incompatible with version2's migrated data. This PR introduces root record schema4 while retaining native database version2: after any future migration, the version2 website's schema3 client must refuse writes. A later release needs a tested schema4-compatible recovery artifact and exported backup; rolling back website files alone cannot undo or safely read that migration. No destructive downgrade is included.

The initial record below is historical and describes the pre-publication state; it does not imply that the recorded Site is now absent.

## Historical initial preparation

No site was published, Pages enabled, tunnel created, deployment secret added, or cloud resource provisioned. Hosting and access model remain unselected. Public source in this user-created repository is authorized; that does not authorize website publication.

Build with Node 24.19.0:

```sh
npm ci
npm run prepare:content
npm run check
# Root or relocatable directory:
APP_BASE=./ npm run build
# Fixed nested directory:
APP_BASE=/SpicyBrain/ APP_OUT=dist-nested npm run build
```

Publishable static files would be the entire output directory, retaining relative paths, fonts, licenses, and content/design assets. Do not publish source fixtures, local backups or test reports as website content. Hash links such as `/SpicyBrain/#/lesson/dbxfe-m01-l01/dbxfe-m01-l01-understand` reload without a rewrite service. Serve the directory over HTTP(S), not `file://`. `npm run preview` is a local check, not a production host. The automated static server exercises both outputs without SPA rewrites.

Use a dedicated origin for eventual hosting. IndexedDB is scoped to origin, not repository path; another app on the same origin may access this database. Moving origins requires export/import. Serving a private repository does not make the resulting website private, and an obscure URL is not authentication. No offline/PWA availability is promised.

Before any later authorized release, document and obtain agreement on:

- Audience and public/private access enforcement, including static assets and preview URLs.
- Hosting cost and operational owner; deployment SHA and reproducible build.
- Signed-in/signed-out access checks, root/nested link and asset behavior, CSP/security headers.
- Manual learner backup guidance before origin changes; no uploaded personal state.
- Rollback artifact and procedure, preserving study IDs/revisions and avoiding destructive state migration.
- Independent acceptance findings and explicitly approved public exposure if public hosting is proposed.

The current CI has `contents: read`, checks the PR head, and uploads only synthetic evidence. It has no deploy-on-push step or publishing credentials. Build output is prepared for review; it is not a live release. [Vite static deployment reference](https://vite.dev/guide/static-deploy.html), read 2026-09-19.
