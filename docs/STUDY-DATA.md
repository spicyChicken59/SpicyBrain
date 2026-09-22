# Study data and review

## Teacher-first schema 4 — 20 September 2026

The database remains `spicybrain-study-v2`, native IndexedDB version **2**. The root record is **schema 4**. Strict schema-1/2/3 inputs migrate inside the same read/write transaction; existing notes, drafts, completion, question snapshots, reviews, schedules, extra practice, self-assessments, bookmarks, legacy positions/path context and timestamps are preserved. New maps start empty; old completion never completes a new beat.

`beatPositions` and `beatResume` record course/module/beat/version, visual stage, Deck/Handbook/Cards view, handbook panel/anchor, scroll offset and separate view offsets. `beatChecks` records open/reveal state, selected option and question revision. Existing drafts hold self-comparison reasoning and module tasks. `settings.showSamajh` is exported with the other preferences. Objective attempts additionally carry optional beat ID/version while preserving canonical lesson version and the immutable complete answer snapshot. Explicit beat completion is separate from answers and visits.

Every new field participates in strict backup validation, import preview, timestamp-based merge and the serialized latest-root transaction queue. A handbook/source detour can save its own position without replacing the main learning resume. Optional extension cards are not eligible merely because their source beat was opened: the learner must deliberately select/introduction-review them. The review algorithm below is unchanged.

An older schema-3 client rejects root 4 and cannot commit over it. On a failed migration or unsupported future root, the stored root is untouched. **Download original saved collection** exports that original root losslessly (including the existing framed transport for large backups); a separate recovery download contains any current unsaved draft work. Do not confuse an IndexedDB save with an off-device backup. Storage denial/eviction and closing a tab with unsaved work remain possible loss conditions.

The 16,000,000-byte active UTF-8 budget, grandfathering, 20,000,000-byte ordinary-JSON boundary, larger framed transport, older large monolithic imports, changed-preview guard, divergent text preservation, immutable event conflicts and protected replace/reset remain unchanged. See `tests/teaching-state.test.ts`, native browser migration journeys and the retained boundary/concurrency regressions. No localStorage preference or remote study service was introduced.

Before any later publication, export schema-3 learner state and retain the current application artifact. After migration, recovery requires a build that understands schema 4 or a reviewed lossless forward-compatible recovery tool; restoring the old website alone is not a safe data rollback. This PR does not perform a production-origin migration.

## Historical study-hub schema 3 — 19 September 2026

The study-hub build keeps the existing `spicybrain-study-v2` database name and native database version 2. Its root **record schema is now 3**. Positions and resume can carry an optional stable `pathId`; it is exported, validated, merged with the whole position by the existing timestamp/tie-break rule, and included in import unknown-reference reporting. Nothing is stored in a hidden local-storage preference. Route query parameters identify explicit path context and a temporary return link; they contain no note/search text.

Strict schema-1 and actual baseline schema-2 inputs are validated against their original position shape, then migrated transactionally without changing any record or timestamp. Missing path context stays missing: a direct topic uses its own course as a visibly explained continuation fallback. Removed path IDs remain recoverable; they do not delete study records. Native schema-2/backup migration and path-context round trips are covered by the study-hub tests. The earlier schema-2 description below remains historical reference for the unchanged record families and safety policies.

Lesson and section completion from a different content version is labeled as earlier-version evidence. It does not automatically complete the revised material. Page visits, solution reveals, downloads, and bridge skips do not create completion.

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

Exports contain a format label, exportedAt, schema version and all personal records/settings. Exports and recovery downloads first read the latest persisted root and replay this tab's unsaved operations; if storage cannot be read, recovery falls back to the retained in-memory copy. A download is not a successful browser save. Import validates the whole collection before writing. Malformed, future-version, inconsistent, or disallowed oversized input leaves existing data intact. Text remains text. Unknown references are retained for Notebook/export recovery.

### Capacity and compatibility

- The active-study budget is **16,000,000 UTF-8 bytes of canonical compact `JSON.stringify(state)`**, including record metadata and immutable histories. It is not a JavaScript character count or a disk-quota promise. Each text field still allows at most 100,000 UTF-16 code units, as in the original schema and browser textareas.
- Ordinary writes exceeding that budget and increasing the previously persisted state's byte size are not committed. The app labels them unsaved, retains the complete pending edit, and offers the same lossless recovery download as a storage failure. A size-reducing edit can recover from this condition. No note, draft, or history is silently truncated, pruned, or discarded.
- **Previously accepted larger states are grandfathered.** Loading, migration, merge and confirmed replacement can preserve/restore them intact. They remain readable and exportable; only non-growing ordinary edits can save above the budget. New notes, attempts, reviews, or resume metadata may be unsaved until enough space is freed. Restoring backups is an explicit compatibility exception, not a way to claim unrestricted active study capacity. Export before intentionally shortening text or replacing a collection.
- Standard `.json` backups are accepted through **20,000,000 UTF-8 bytes**, including envelope and formatting. Export automatically switches larger snapshots—including unsaved recovery work—to **one `.jsonl` framed backup file**. Each frame is at most 1,000,000 UTF-8 bytes; each payload fragment is at most 100,000 UTF-16 code units. Strict header/version, frame numbering/count, reconstructed byte length and the complete original study schema are checked. Missing, reordered, extra, overlong or invalid frames reject the entire import. Fragment boundaries preserve surrogate pairs on reassembly.
- There is no fixed aggregate cap on the **legacy/recovery transport**, because the previous build accepted unbounded collections. Framed files are read in 64 KiB slices with bounded individual frames. The completed collection still occupies memory for validation and the single-root transaction; framing is not an unlimited-memory or streaming-database claim. Browser memory and IndexedDB quota can prevent a large restore. On failure, existing data remains intact and the original file is retained by the user.
- An older monolithic JSON export larger than 20 MB is rejected by the default reader without writes. The UI offers **Open older large backup**, an explicit compatibility reader using bounded slices followed by full schema validation. This keeps older exports restorable instead of stranding data at a new threshold. That exceptional reader may need substantial memory; it never skips validation or writes before the preview/confirmation flow.

Thus the 51 × 100,000-character note reproduction (5,118,056 export bytes) round-trips normally. The exact active boundary, one additional UTF-8 byte, >20 MB framed export/recovery and old monolithic compatibility paths have separate regressions. Simply raising an import ceiling would not establish these guarantees.

### Atomic merge, preview and replacement

Merge is the default. It joins the same serialized queue as edits, opens a native IndexedDB **readwrite** transaction, reads the latest persisted root inside that transaction, replays pending operations through the import's queue position, merges and validates, then writes and waits for transaction completion. Other tabs' committed records cannot be replaced by the importing tab's stale snapshot. Edits queued after import remain pending and replay over the committed result. A failed import aborts the entire transaction and leaves pending work recoverable.

Immutable events deduplicate by ID; a different payload under the same immutable ID rejects the merge. Conflicting note/draft texts are both retained with content-derived conflict IDs and collision-safe suffixes. Repeating an unchanged import is idempotent. Later updatedAt wins mutable state/settings, with serialized lexical order as a tie-break. Schedules derive from the latest immutable review, with event ID breaking equal-time ties.

Preview reads the latest persisted data plus local pending edits. Applying either import mode compares that exact preview basis against the transaction's latest state. If another tab or a queued edit changed it, nothing is imported: the preview refreshes and the user must apply again. Replacement also clears its destructive confirmation checkbox. Replacement remains explicitly destructive for the confirmed collection; edits made after it was queued are retained. Reset still requires the exact word RESET. Cancel writes nothing; transaction failures roll back.

There is no server copy, automatic sync, encryption vault, or promise that browser storage survives eviction/private browsing/clearing. Origin changes require manual export/import. Database names prevent accidental collision but aren't security boundaries against other same-origin apps. See [MDN IndexedDB](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API) and [storage quotas/eviction](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria), read 2026-09-19.
