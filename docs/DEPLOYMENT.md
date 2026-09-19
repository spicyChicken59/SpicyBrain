# Deployment preparation — not authorization

## Current checkpoint — 19 September 2026

The approved study-hub assignment supplies this existing public hosting checkpoint: [SpicyBrain](https://spicybrain.motahir-official.chatgpt.site), Sites project `appgprj_6aaeb1f97b9c8191b7ec8bf746c483c7`, recorded hosting source `8a80f1df37358797c9cec04f66d852294d395c60`. The handoff describes that source as the merged application plus the Sites manifest. This is attributed handoff evidence, not a new verification of the deployed version. GitHub remains the application repository; merging a PR does not publish it to Sites.

This milestone authorizes one implementation PR, with no merge or deployment. Do not create another Site, change repository/hosting settings, enable Pages, change origin, or deploy this PR. Later authorized publication must reverify this same Site identity, source/build hashes, access model, and live learner-state continuity. Local native-storage tests are not a production-origin migration test.

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
