# Study data and review

`spicybrain-study-v2`, IndexedDB database version 2, contains one transactional `study/root` snapshot with schemaVersion 2. Separate maps retain notes, practice drafts, bookmarks, explicit completion, immutable objective attempts, immutable scheduled reviews, derived schedules, extra-practice events, rubric self-assessments and stable section positions. Resume, settings and local-storage disclosure are included. UTC timestamps and stable IDs, rather than lesson order or titles, link evidence.

An explicit completion records a learner choice. Scrolling, answer reveal, a note or a self-rating does not establish mastery. Objective attempts record question revision, lesson contentVersion, selected/correct option IDs, correctness, concept IDs and the complete prompt/options/rationales at submission. Later content edits do not rewrite old scores. Self-assessments are explicitly learner-chosen, not automated grading.

## Transparent schedule v1

Algorithm `spicybrain-simple-v1`; a day is 86,400,000 milliseconds. The calculation accepts an explicit UTC clock value. Given previous interval `p` (initially zero):

| Rating |                               Interval days | Due                               |
| ------ | ------------------------------------------: | --------------------------------- |
| Again  |                                           0 | Review time + 10 minutes          |
| Hard   |             min(365, max(1, ceil(p × 1.2))) | Review time + interval × 24 hours |
| Good   | 3 when p=0; otherwise min(365, ceil(p × 2)) | Same                              |
| Easy   | 7 when p=0; otherwise min(365, ceil(p × 3)) | Same                              |

The shared 365-day cap is intentional. This is a modest product heuristic, not a medical claim or an implementation of a named validated memory algorithm. Local date formatting doesn't change stored instants. Tests include DST-adjacent instants, exact due boundaries, rounding and caps.

Scheduled cards are due when `dueAt <= now`. Material revisions are additionally included with an explicit revised-answer flag. Order is due instant, then stable card ID. The default session limit is 10, settings offer 1–30; the remainder is untouched. New cards are separate, introduced only from opened lessons or explicit selection, with default allowance 3 (up to 10). Extra practice records its own event and cannot change scheduled reviews or due dates. Rating is disabled before reveal. A guarded event ID and atomic event/schedule transaction prevent double taps from duplicating a review. Reloading/interruption preserves committed events; session UI itself isn't a persisted queue.

## Saves, recovery and migration

Each text change immediately updates memory, then joins a serialized transaction queue. Pending operations replay against persisted state; rapid navigation doesn't discard the final edit. Failures show **Unsaved**, keep text editable across app routes, and offer a recovery JSON download and retry. A blocked upgrade allows recovery work; when the other connection closes, pending edits replay over loaded state. Transaction failure never announces success. The browser's unload warning helps while unsaved; closing/discarding the tab can still lose unsaved work. Retry cannot restore a browser API the browser has permanently denied; keep the recovery file and reopen when storage is available.

A synthetic v1 predecessor has the same record families except extra practice. `tests/fixtures/study-v1.json` is explicitly a migration fixture, not a past product release. Initialization migrates and writes schema 2 in a transaction; tests open a real fake-indexeddb version-1 database, retain original IDs/text/timestamps/reviews, upgrade, and reopen. Browser tests separately use native IndexedDB for all main journeys and blocked-upgrade behavior.

## Backup and import

Exports contain a format label, exportedAt, schema version and all personal records/settings. Import validates the whole file before writing (5 MB file limit; 100,000 characters per note/draft field). Malformed/future/oversized/inconsistent records leave existing data intact. Text remains text. Unknown references are previewed and retained for Notebook/export recovery. The UI shows incoming/current counts and conflicts before applying.

Merge is default. Immutable events deduplicate by ID; a different payload under the same immutable ID rejects the merge so neither history is silently rewritten. Conflicting note/draft texts are both retained, with content-derived conflict IDs and collision-safe suffixes. Repeating an unchanged import is idempotent. Later updatedAt wins mutable state/settings, with serialized lexical order as a deterministic tie-break. Schedules are reconstructed from the latest review (event ID breaks equal-time ties). Replace offers export, names the loss, requires explicit confirmation, and commits one atomic snapshot. Reset requires the exact word RESET. Failed replace rolls back; cancellation does nothing.

There is no server copy, automatic sync, encryption vault, or promise that browser storage survives eviction/private browsing/clearing. Origin changes require manual export/import. Database names prevent accidental collision but aren't security boundaries against other same-origin apps. See [MDN IndexedDB](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API) and [storage quotas/eviction](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria), read 2026-09-19.
