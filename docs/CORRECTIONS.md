# PR #1 preservation corrections

Scope: existing `feat/spicybrain-v1` / PR #1 only. Baseline `3bbd1576442a69dbb964f2a8498e7e206d11b291`; base remains `9022872f9215e52d64e11890c21d3022379c6cb3`. No intervening remote changes or repository instructions were found. The final tested commit and CI run are recorded in the PR and each CI artifact's `tested-head.txt`. The site remains unpublished and the PR unmerged; independent re-review is pending.

## Reproduced defects

The untouched baseline production `StudyStore`, with fake-indexeddb, reproduced both reports on 2026-09-19:

| Case                                                       | Before                               | After / failure                                               |
| ---------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------- |
| Stale A merges a different note after B saves              | `note-dbxfe-m01-l01-why`             | Only `note-dbxfe-m01-l01-understand`; B's saved note was lost |
| Stale A merges an empty valid backup                       | `note-dbxfe-m01-l01-why`             | No notes remained                                             |
| 51 real course sections, 100,000 ASCII characters per note | Valid schema; export 5,118,056 bytes | `Import exceeds the 5 MB limit. No data changed.`             |

The earlier green CI did not cover these failures. The new browser journeys below are newly added evidence, not retrospective claims about that run.

## Corrections

1. **Latest-state atomic merge.** Imports are barriers in the edit queue. A readwrite transaction reads the latest database root, applies eligible pending edits, merges/validates and commits together. Later edits retain their sequence and replay afterward. Aborted transactions retain the old database and pending recovery data. Text conflict copies and immutable event deduplication remain unchanged.
2. **Preview matches confirmation.** Preview includes other tabs' saved work and this tab's pending edits. A changed basis rejects the apply attempt, refreshes the preview, and clears replacement confirmation. Both merge and replacement must be applied again. Explicit replacement remains destructive only for the confirmed collection. Downloads refresh from storage and preserve pending edits.
3. **Capacity with backward compatibility.** Ordinary saves use a 16,000,000-byte canonical UTF-8 state budget. Oversized edits remain unsaved and fully recoverable. Existing/restored larger collections are kept intact, with growth paused. Normal JSON transport supports 20,000,000 bytes; larger exports/recovery use a single framed file with 1 MB frame limits. An explicit compatibility reader accepts older large monolithic backups for validation/preview. See the precise policy and memory/quota limits in [STUDY-DATA.md](STUDY-DATA.md). No automatic pruning or truncation occurs.
4. **Fresh checkout.** `npm run check` now generates and validates catalog/search before typechecking. CI runs `npm ci --ignore-scripts`, checks that both generated files are absent, and runs `check` without a preparation prerequisite. README and acceptance instructions agree.

## Regression evidence

`tests/corrections.test.ts` adds eight deterministic regressions:

- Two initialized stores, later persisted note, stale merge and empty merge, then fresh-reader comparison.
- Unsaved edits before import; edits queued after import; preserved note/draft conflicts; duplicate merge; immutable review/schedule retained.
- Both import modes reject changed previews; refreshed confirmation succeeds; edits after the barrier remain.
- Failure after enqueueing the transactional write leaves the entire prior root unchanged; pending work remains exportable and retryable.
- Exact original 5,118,056-byte state restores through both helper and Blob/file reader.
- Exactly 16,000,000 bytes saves; replacing one ASCII character with `é` adds one UTF-8 byte without increasing JS character length, fails the growth check, and remains recoverable.
- A >20 MB legacy collection loads unchanged, exports with bounded frames, restores intact, supports old-file compatibility, refuses growth, and permits reduction.
- Malformed/future/oversized/missing/reordered input cannot alter existing state.

`tests/browser/corrections.spec.ts` adds native IndexedDB browser journeys using only synthetic data:

- Two tabs, notes and practice draft, review history, changed preview, merge, reopen, preserved conflict versions, empty import, injected native transaction abort, and stale destructive confirmation.
- Actual download of a >5 MB backup, file-input upload into a fresh context, all-record comparison, lesson resume/note/draft/review checks, native quota failure, recovery download, and another fresh-context restore.
- Framed large legacy download/upload, old monolithic compatibility, invalid oversized frame rejection, capacity failure and lossless recovery.

The [clean-checkout result](evidence/corrections/clean-checkout.json), [concurrent-tab records](evidence/corrections/native-concurrent-preservation.json), [large-backup comparison](evidence/corrections/large-backup-preservation.json), and [legacy restoration](evidence/corrections/framed-legacy-preservation.json) are committed alongside [screenshots and source-input hashes](evidence/corrections/). Browser-generated JSON evidence records sizes, IDs, stable SHA-256 digests, dates and runtime versions. Screenshots cover refreshed preview, conflict recovery, large restoration and legacy capacity messaging. Evidence files contain synthetic data only. Local Chromium is 153.0.8010.0, Playwright 1.63.0, Node 24.19.0; desktop 1440×1000, new contexts 1280×720. The original suite retains root/nested, mobile/touch, keyboard, reflow, migration and privacy coverage. Local WebKit remains unavailable due to OS libraries; final-head CI supplies its separately reported mobile-emulation result, not physical-device testing.

## Scope and limits

Course/content and the pinned design snapshot are unchanged: 12 modules, 36 lessons, 108 cards, 72 checks, 12 scenarios, 12 diagrams and the separate capstone. The unrelated-course extension test remains required. No cloud executions or publication occurred. Data remains browser-local, manually transferred, and subject to memory, quota, eviction and tab-close loss of unsaved work. The legacy transport exception does not promise unlimited active capacity. Exact final commands, results, clean-checkout evidence and workflow URL are in PR #1.
