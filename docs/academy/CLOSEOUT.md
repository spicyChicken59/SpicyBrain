# PR #4 continuation checkpoint

Review date: 2026-09-23. Starting branch: `feat/databricks-academy-completion`.
Remote head: `afbe49efc03d10e1950b4ef80598c2fd316a2186`.
Base: `2cde73d902b296ca4bae13dcc31ff6f6ace9e917`.

## Recovery

PR #4 is open and unmerged. The accessible checkouts contained older PR #1
work, with clean working trees, and no academy closeout files or running
academy process. No local academy commits ahead of the remote were found.
The interrupted builder's separate environment is not accessible here; its
uncommitted work cannot be declared lost or recovered. A new worktree tracks
the existing academy branch at the verified remote head. No reset, clean,
force checkout, force push or worktree deletion was performed.

No PR #4 monitor was found among the accessible automations; none was changed.

## Reconciled status

| Item | Classification | Evidence / remaining action |
|---|---|---|
| 48-module implementation, 16 retained video placements, labs and study-data safeguards | Already completed with evidence | Existing content, LEDGER, lab packages and historical acceptance run 55 / 35876280429 on `afbe49e`; preserve them. |
| Source inventory and 32 new-module media candidate records | Partially completed with recoverable files | SOURCE-INVENTORY and MEDIA-DECISIONS preserve the original methods; search results and blocked access do not close review. |
| Lakebase restore and managed pooler corrections | Not started at recovered head | Direct documentation inspection now succeeds. Apply the correction to every affected teaching surface and revision. |
| Claim-level primary-source closeout, eight cases and official-learning crosswalk | Partially completed | Existing review records are reusable only for their actual claims and provenance. Missing direct review remains G14 BLOCKED. |
| New-module video evaluation | Partially completed | 43 leads across 32 module records; no reviewed new placement. G10 BLOCKED. |
| Correct lab-count wording and acceptance statuses | Started by this checkpoint | 532 checks in 20 local-executed labs; 53 in two tabletop packages; 34 in two platform guides; 619 total. |
| Final targeted/browser/full acceptance and lab suites | Not started for continuation | Old run 55 is evidence only for its old head. Record new exact-head CI in PR metadata. |

## Initial access check

On 2026-09-23 the web reader returned the complete primary page text for:

- `https://docs.databricks.com/aws/en/oltp/projects/point-in-time-restore`,
  particularly **What happens after a restore?**, **Creates a new branch, not
  in-place modification**, and **Connections remain unchanged**. Restore
  creates another root branch; adopting recovered data requires a separate
  application decision.
- `https://docs.databricks.com/aws/en/oltp/projects/connection-pooling`,
  particularly **Transaction mode**. The managed pooler documents both
  LISTEN and NOTIFY as unavailable.
- `https://www.youtube.com/@Databricks` returned only a page shell, no
  playable media or transcript. This does not establish that useful videos
  do not exist. Candidate-specific review remains unresolved.

The previous session's documentation block is historical, not evidence that
all sources remain inaccessible now. Only inspected claims may be promoted.
No platform execution, video playback or source inspection is inferred from
link reachability, a snippet, an optional placement or green CI.

## Continuation result — 2026-09-24

The recovery checkpoint was saved remotely on this same branch as `c9c4e6b`.
The shell push had no credentials; the connected GitHub app created the same
reviewable tree, and the local branch reconciled with that commit without a
force update or loss of work. PR #4 is a draft until editorial closeout.

Completed corrections: Lakebase restore and managed LISTEN/NOTIFY teaching;
affected content revisions and course 4.0.1; honest lab counts; explicit blocked
media decisions; four direct-source case reconciliations; nine official-learning
crosswalk reviews. The 16 retained media placements are unchanged. L23’s adaptation guide carried
the same two defects and was corrected and repackaged; its SQL and 18 checks
are unchanged. The other 23 lab ZIPs and original exercise ZIP are unchanged.

### Precise unresolved research

- G10: 32 modules, 43 existing candidate leads. The first YouTube channel check
  returned a shell. A candidate-specific open of
  `https://www.youtube.com/watch?v=UQynsu6qklw` returned `Online fetch throttled`.
  The official Lakebase demo page returned title, duration and description, but
  no transcript or playback. These are access observations, not video rejection.
  No repeated failed media fetches or invented timestamps were used.
- G14: `CLAIM-REVIEW.json` identifies 792 pending claims and one partially reviewed
  compound claim by ID, source URL and affected content. Unchanged claims from the accepted
  base are matched by content digest so valid prior evidence is reused. The available legacy
  source evidence is preserved; completing claim-to-section verification remains
  work to do. Access to these pending URLs has **not** universally failed.
- Four case primary pages did not supply their session body: AT&T, CVS Health
  and Petrobras redirected to a generic Summit page; Barilla returned not
  accessible. One direct attempt per exact URL is recorded in
  `CASE-CROSSWALK-REVIEW.json`; no generic landing page is counted as a session read.
- The Generative AI Application Deployment and Monitoring crosswalk URL returned
  a web-reader internal error without a body. Its current scope and prerequisites
  remain unconfirmed. The other nine public-page reviews do not establish account
  enrollment entitlement or access to gated course material.

### Validation provenance

Local `npm run check` passes 162 tests, typecheck, lint and the production build.
The Lakebase module audit passes. All 27 lab/data-pack ZIPs match source members;
retained disposition remains 2,435 identities, zero removed or unversioned.
The lab manifest independently totals 532 / 53 / 34 checks by execution class.

The targeted browser command was attempted at 1440 and 390 widths, but Chromium
failed before opening a page: the execution environment denied its singleton
socket. This is not rendered evidence and is not hidden by a skip. Browser and
pinned lab execution are delegated to the existing authorized PR CI workflow;
no workflow settings were changed. Final run/job/artifact IDs belong in PR
metadata, avoiding a self-referential commit/run cycle.

## Accessible-source follow-up — 2026-09-24

The prior stop combined actual access failures with unfinished accessible work.
Direct source inspection continued: 23 Lakebase records are now resolved,
including the earlier partial authentication/scale-to-zero claim. The ledger
now has 770 pending, 136 retained, 18 reviewed and 8 corrected-and-reviewed
claims. All 26 documented claims in the Lakebase module have an explicit review.
This does not complete the remaining modules' reviews.

Corrections include Postgres 18 in the supported version list; the current
Lakebase CDF name at the former Lakehouse Sync URL; enabling password connections
on new projects; the existing app service principal's matching Postgres role;
and the fact that an empty SKIP LOCKED result does not prove an empty queue.
The synced-table handbook now allows automatic CDF as well as write-time CDF.
Relevant beats, the canonical lesson and changed assessed items have new
revisions. Course version is 4.0.2. L23's documentation is repackaged; SQL,
checks and historical execution evidence are preserved.

Run 59 / 35938294952 passed on 9b640e9 before this follow-up (162 tests,
64 browser journeys, all 24 packages / 619 checks). It is not evidence for the
new content. New exact-head CI will be recorded in PR metadata after the
release manifest is refreshed. Manual screenshot inspection remains blocked
by the recorded artifact-transfer HTTP 403; no repeated transfer was attempted.
G10/G14 and affected editorial gates remain BLOCKED. Media and the five
unavailable case/crosswalk pages retain their recorded access outcomes.

### 2026-09-24 — Genie Code claim review checkpoint

All 20 documented AI-assistance claims now have explicit primary-section decisions.
The ledger has 750 pending, 136 retained, 29 reviewed and 17 corrected-and-reviewed
claims. Current teaching corrects former-URL redirects, approval behavior, the
partner-powered setting removal timeline, billing provenance and try_cast
exceptions. June reader snapshots are explicitly dated; they do not override
September AWS guidance. Course 4.0.3, lesson 1.2.0 and affected assessed revisions
preserve stable identities and immutable earlier answers.

The handbook browser selector fix is on fb2ad75283e439af33f3a1b2dc3ff21674d1ae25.
Run 61 / 35956712137 failed only its two new handbook selectors; labs passed.
Run 62 / 35957524319 tests the fixed head and does not cover this later teaching.
Final 4.0.3 build manifest and exact-head CI are pending; G10/G14 and affected
editorial gates remain BLOCKED. Media access failures are unchanged and were
not retried. No source quota or access failure is asserted for pending claims.

### 2026-09-24 — Genie Agents claim review checkpoint

All 23 documented Genie Agents claims now have explicit decisions: 727 pending,
136 retained, 43 reviewed, 26 corrected-and-reviewed across the academy.
Current pages resolve the old URLs and document companion dashboard credentials,
shared prompt context, conversation privacy and Chat-mode trusted answers.
Affected teaching, cards and the standalone scenario are versioned; course
4.0.4 keeps all content identities. The old trusted-assets URL redirects to
setup; the actual quality-tuning and response sections support the corrected claim.

Run 62 passed its browser step but was superseded and cancelled when the Genie
Code checkpoint was pushed; it is not a passing full-suite run. Run 63 tests
b8be663f338ed97e2fde1419adf761d92606023d, before this Genie Agents change.
Manifest refresh and final exact-head acceptance/labs remain pending. G10/G14
and affected editorial gates remain blocked.

## Continuation — 2026-09-25: claim closeout in the priority areas

Starting point: remote head `8ea004e519f5200cea2d8826a3b041712ebb809a`, whose
CI run 35959071529 passed (acceptance job 107503527791, labs job 107503527559;
artifacts 10791319657 and 10791449099). The branch had not moved since
2026-09-24 05:14 UTC and no other session was working on it. Every commit of
this continuation sits on top of that head; nothing was reset or force-pushed.
This environment is a builder continuation, not an independent human review.

### Access in this environment

One request per host on 2026-09-25T07:36:54Z through the session egress proxy
returned `CONNECT tunnel failed, response 403` for docs.databricks.com,
www.databricks.com (the Barilla session page), learn.microsoft.com,
docs.aws.amazon.com and www.youtube.com (the CVS Health recording). Publisher
source repositories on raw.githubusercontent.com, PyPI and Google API discovery
documents were reachable. Nothing was routed around the block: no archive,
cache, mirror or CI relay. Unlike the 2026-09-24 environment, local Chromium
runs here, so the rendered checks below were executed.

### Claim decisions

Fourteen modules had no claim-level decisions: identity, AWS, Azure, Google
Cloud, apps, BI, AI platform, serving, retrieval, tools, sharing, Delta writes,
operations and GenAI evaluation. Together with the owner's Lakebase, Genie and
AI-assistance reviews, they cover every priority area in the brief. Each module's
claims were researched and then verified by a separate agent. Each agent
re-read the evidence itself at pinned commits: the Databricks SDK for Python
0.141.0, the Terraform provider, the CLI and the developer-documentation source
(databricks/devhub), open-source Delta Lake, MLflow, the MCP SDK and
specification, urllib3, azure-docs and Google API discovery documents. An
interface read supports the interface only, and open-source documentation
supports open-source behaviour only. Three adversarial review rounds followed:
round 1 had 69 findings (22 medium), round 2 had 30 (5 medium) and round 3 had
4 (low). A fix pass after each round applied 109 items and rejected 8, each
rejection with a reason. The last content finding was applied and checked
directly.

352 claims now carry an explicit decision with reviewer, date, method, verbatim
evidence, supporting sections, gaps and any correction with the versions it
moved: 68 reviewed, 24 corrected-and-reviewed, 232 partial and 28 still
pending. The commit message of `47cfa49` says 349 decisions; the ledger holds
352. Ledger totals: 111 reviewed, 50 corrected-and-reviewed, 232 partial,
403 pending and 136 retained. Of the 403 pending claims, 375 in 20 modules have
no decision yet. [`CLAIM-LEADS.md`](CLAIM-LEADS.md) is generated from the
ledger and lists every open claim with the gap its decision records, including
the page that would settle it.

70 decisions record a correction. Examples: system schemas can also be enabled
by a metastore admin; AWS same-group ingress is required, and instance profiles
also serve serverless SQL; Azure outbound, managed resource group and access
connector wording; GCP OIDC scope and Cloud KMS policy location; custom agents
now run in Databricks Apps, with `agents.deploy()` the legacy path; Genie Agent
naming; job failure notifications also cover canceled or skipped runs; VACUUM
removes only unreferenced files; built-in judges run outside Databricks in
MLflow 3.16.1; Delta DROP FEATURE, overwriteSchema and conditional MERGE
failure; app credentials and row filters; dashboard publish entitlements and
schedule warehouses; clean-room output expiry and `shared_as` scope; UniForm
can be turned off while column mapping and the protocol upgrade cannot; the AI
Search score threshold; MCP token audience; and urllib3's retry scope. Beats,
assessed items and lessons carry new versions and revisions, with change notes
in plain words. Stable identities are unchanged; the disposition check reports
2,435 retained identities, 0 removed and 0 unmoved revisions. Course 4.0.5.

### Regression protection

`tests/claim-corrections-2026-09-25.test.ts` has 41 tests covering 39
substantive corrections, the Genie Agent naming and the text equivalents of
changed visuals. All 41 fail on the pre-correction content and pass on the
corrected content. A mutation pass reintroduced 40 old statements, and each
turned exactly its own test red. Of 58 same-meaning rewordings, 57 were caught;
of 31 held-out rewordings, 29. All 18 near-miss controls stayed green. The
prover found the Agent Bricks correction incomplete: two surfaces still said
Agent Bricks agents are configured rather than coded. Both were corrected, and
the tightened check fails on the previous text. `tests/py/test_claim_leads.py`
keeps the blocker report in step with the ledger.

`scripts/academy-quote-check.py` re-checks every verbatim evidence quote in
`CLAIM-REVIEWS.json` against its pinned source; decision texts that name
"verify_quotes.py" refer to the build-session copy of the same matcher. On
2026-09-25 it verified 1,878 of 1,878 quotes, the owner's decisions included,
and it rejects an altered quote (exit 1). It needs network access to the
pinned sources and is not part of `npm run check`.

### Other corrections and audits

- Source provenance: 38 records said "as previously read" about pages this
  build never read. They now say what was and was not read. The source-review
  classifier counted "not a read in this build" as a read; that negation is now
  handled and tested.
- Cases: all eight were re-audited for attribution. The Petrobras case said its
  speaker pages name the presenters, although only search results for those
  pages were seen; it now says so. The other seven attribute every figure to
  its reporter. Fresh 2026-09-25 searches contradicted none of the four blocked
  cases. They stay blocked.
- Lab L15: the Azure case sheet gave the default outbound rules' destinations
  as address ranges. Microsoft's NSG reference (azure-docs `194fd50`) names the
  VirtualNetwork and Internet service tags; the sheet now names them and says
  it draws them as CIDRs. The fixture, keys and 30 checks are unchanged. The
  evidence was regenerated, the lab repackaged and its download hash updated.
- Lakebase restore window: the owner's "2–30 days, default 7" matches search
  results for the documentation page's slider. The SDK and Terraform references
  (`ProjectSpec.history_retention_duration`) accept 2–35 days through the API.
  This is recorded as a lead, not a correction.
- Coverage warnings: 109 warning findings are 106 distinct retained items, each
  with its own reason in `warning-dispositions.json`.

### Rendered and executed evidence in this environment

- The owner's six closeout browser tests (Lakebase restore and pooler, Genie
  Agents, Genie Code; 1440 and 390 px) passed locally on `cc7be0e`.
- The visual review of the owner's three corrected modules passed on `cc7be0e`:
  470 state renders in five contexts, 0 failing, 15 axe pages with 0 violations,
  0 page errors. Screenshots of the restore, pooler, Genie access and AI-assist
  states were inspected.
- The full-course visual review and the full Chromium suite on the final
  content head are recorded in `ACCEPTANCE.md` (G05, G23).

### Still blocked

- G10: no candidate video could be opened. The 32 new-module records stay
  `blocked-review` and none is converted to no-placement without an actual
  evaluation.
- G14: 375 claims in 20 non-priority modules have no decision. 260 decided
  claims are partial or pending because the pages that would settle them are
  unreadable here; `CLAIM-LEADS.md` names each one. The AT&T, Barilla, CVS
  Health and Petrobras session pages, and the Generative AI Application
  Deployment and Monitoring catalog page, remain unread.
