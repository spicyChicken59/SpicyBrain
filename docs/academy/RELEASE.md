# Release candidate — Databricks: Build, Explain, Deliver

This records what a later, separately authorized publication would ship and
how to check it. It is not an authorization to publish: this PR merges
nothing, publishes nothing, enables no Pages, creates no preview or tunnel,
and changes no Site, origin, access model, repository setting or secret.

## Closeout status

This candidate is **not ready for release**. G10/G14 and source-dependent
editorial gates remain blocked; see CLOSEOUT.md. The manifest verifies bytes,
not research completion. Final CI provenance belongs in PR #4 metadata. The current manifest still records
the prior 4.0.2 build; a clean 4.0.3 refresh is pending at this checkpoint.

## Candidate

| Item | Value |
|---|---|
| Source commit | the `sourceCommit` recorded in [`release-manifest.json`](release-manifest.json), built from a clean tree; the commit that adds the manifest changes nothing else |
| Node | 24.19.0 |
| Course | `dbxfe`, contentVersion `4.0.3`, "Databricks: Build, Explain, Deliver" |
| Modules / tracks / routes | 48 / 8 / 9 |
| Labs / field guides / cases / capstones | 24 (20 local-executed, 2 tabletop, 2 platform guides) / 32 / 8 / 3 |
| Build manifest | [`release-manifest.json`](release-manifest.json): every file of `dist/` and `dist-nested/` with its size and SHA-256, and the content manifest with every download's SHA-256 |
| Initial JavaScript | 1,477,751 B raw / 337,148 B gzip (+6.7% raw over the 1,384,441 B baseline; ceiling +15%), measured at `09cba75`. See [`SCALE.md`](SCALE.md) |

Regenerate the manifest from a clean checkout of the candidate with
`npm ci --ignore-scripts && npm run check && APP_BASE=/SpicyBrain/ APP_OUT=dist-nested npm run build && python scripts/release-manifest.py --out docs/academy/release-manifest.json`.
A publishing session compares the bytes it uploads with this listing and the
bytes it serves afterwards with the same listing.

## Study data compatibility

- Root record **schema 4** and native IndexedDB database **version 2** are
  unchanged. `src/study.ts` differs from the released base (`2cde73d`) only in
  TypeScript signatures (`applyReview` takes a card identity, `reviewQueue` is
  generic); the persisted schema, migrations and database version are
  byte-identical in behaviour.
- New material adds records of kinds that already exist: beat notes and
  completions for new modules, and field-guide drafts, which are ordinary
  notes whose section is the guide id. Nothing new is written that the
  released client cannot read. The reference tier added for G21 is a
  static content file, not study data.
- **Executed same-origin procedure** (`scripts/release-rollback-check.ts`,
  evidence [`evidence/rollback.json`](evidence/rollback.json)): one loopback
  origin and one persistent browser profile serve the released build, then the
  candidate, then the released build again (a rollback of website files), then
  the candidate again. Every record written at each step survives every later
  step. The released client opens the candidate's records without an error
  and lists every note on new material with its full text: a note whose
  lesson it does not have is shown under "Removed lesson · note preserved",
  a field-guide draft (filed under a retained lesson) under that lesson, and
  both with the section marked unavailable. Returning to the candidate
  reattaches them to their beat and their guide.

## Recovery materials

- **Export before publishing.** Settings → *Export all study data* writes the
  complete collection (framed JSONL above 5 MB). Import is merge-by-default
  with a preview; *Replace* asks for confirmation.
- **Rollback.** Replacing the candidate's files with the released build's
  files is safe for study data (above). No destructive downgrade exists or is
  needed.
- **Unreadable state.** A future-schema or damaged root is never overwritten;
  the notice offers *Download recovery data* and *Download original saved
  collection*.

## Synthetic same-origin migration procedure for the publishing session

1. Before replacing files, open the live Site in a fresh profile, create
   synthetic study data (a lesson note, a bookmark, a completion, an answered
   check) and export it.
2. Upload the candidate. Verify the served bytes against
   `release-manifest.json` (same path, size and SHA-256 for every file).
3. Reload the same profile on the same origin: the synthetic records are
   present and unchanged; add a beat note on a new module and a field-guide
   draft; export again.
4. If rolling back, restore the previous files and reload: the records from
   steps 1 and 3 are present; notes on new material are listed as preserved.
5. Record the dates, the Site identity and the byte comparison. Delete the
   synthetic profile.

## Privacy

`tests/public-safety.test.ts` fails on build-machine paths, proxy settings or
scratch locations in content, lab packages, evidence and decisions. No
learner biography, job title, employer relationship, level, compensation or
diagnostic information appears in the application, content, metadata,
screenshots, documents or this PR. The application sends no analytics and
contacts no provider before an explicit consent choice (video only).
