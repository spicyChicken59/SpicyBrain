# Deployment preparation — not authorization

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
