# Databricks: Build, Explain, Deliver — implementation contract (sanitized)

SpicyBrain's second course release turns the sixteen-module teacher-first
course into an independent, original Databricks learning academy: eight study
tracks, 48 modules, a lab shelf, a field-guide collection, three end-to-end
fictional capstones and eight public case analyses. This document is the
public, sanitized scope. It contains no learner biography, employer
relationship, level, compensation or diagnostic information; personalization
is expressed through the teaching design only (SQL and data-modeling bridges,
deliberate Python/distributed/cloud explanation, optional beginner refreshers,
manufacturing-first examples with cross-industry transfer, English-primary text
with optional Hinglish Samajh analogies).

The academy is independent education. It is not Databricks Academy, not
official onboarding, not a certification and not an employer readiness
standard. It does not rehost, copy or impersonate Databricks training.

## Learner promise

Open a module. Understand one idea through a visual. Make it click with an
optional analogy. Try a question. Consult the illustrated handbook. Apply the
idea. Review it later. Return without reconstructing where you were.

## Preserved baseline

The merged teacher-first release (16 modules, 135 beats, 215 visual states,
135 beat checks, 208 cards, 43 canonical lessons, 96 original checks, 18 SVGs,
12 scenarios, one capstone, 16 reviewed video placements) is retained with its
identities. The sixteen modules are incorporated into the 48-module curriculum
as A1, A3, B1, B3, B6, C3, D1, E1, F1, G1, H1–H6; nothing is cloned into a
second course. The original reliable-data exercise package
(`content/downloads/reliable-data-exercises.zip`, 57,908 bytes, 37 members,
SHA-256 `32af53617af3591ebf861857a579bd93dd86b4e1981bf4ad01c37a7353e0e4fb`)
is unchanged. Study data schema 4 on native IndexedDB version 2 is unchanged.

## Delivery floors (coverage, not quality)

- 48 complete modules in eight tracks; ≥480 substantive teaching beats.
- Every beat: explanation (40–100 words, ≤120), dominant visual with named
  states, a "notice this" prompt, optional Samajh, one explained check,
  handbook depth, Next/Previous orientation.
- ≥10 distinct core cards and 4 researched extension cards per module (≥672).
- 48 applied tasks with model reasoning and explicit rubrics.
- 24 lab packages: 20 locally executed (R), 2 tabletop (T), 2 platform guides
  (P). Every R package is executed in a pinned environment with recorded
  commands, results and fixture/output hashes.
- 32 field guides with an action page, a completed fictional example and a
  blank template.
- Three fictional capstones (Cinderline deepened; service knowledge and
  controlled actions; enterprise coexistence and modernization).
- Eight source-attributed public case analyses and an optional official
  learning crosswalk.
- All existing preservation, accessibility, browser, editorial, content-only
  extension and release-preparation gates.

## Tracks and modules

Canonical IDs are in `content/courses/dbxfe/academy.json` (the machine-readable
contract manifest used by `npm run academy:check`). Labels A1–H6 are contract
labels, not runtime IDs.

| Track | Modules |
|---|---|
| A Platform and working fluency | A1 `dbxfe-m03` (kept) · A2 `dbxfe-python` · A3 `dbxfe-transformations` (kept) · A4 `dbxfe-spark-execution` · A5 `dbxfe-delivery` · A6 `dbxfe-ai-assist` |
| B Reliable data engineering | B1 `dbxfe-delta` (kept) · B2 `dbxfe-delta-writes` · B3 `dbxfe-m04` (kept) · B4 `dbxfe-streaming` · B5 `dbxfe-pipelines` · B6 `dbxfe-orchestration` (kept) |
| C Analytics, performance and economics | C1 `dbxfe-modeling` · C2 `dbxfe-analytical-sql` · C3 `dbxfe-m05` (kept) · C4 `dbxfe-bi` · C5 `dbxfe-genie` · C6 `dbxfe-finops` |
| D Governance and cloud architecture | D1 `dbxfe-m06` (kept) · D2 `dbxfe-identity` · D3 `dbxfe-aws` · D4 `dbxfe-azure` · D5 `dbxfe-gcp` · D6 `dbxfe-sharing` |
| E Machine learning and production evaluation | E1 `dbxfe-m07` (kept) · E2 `dbxfe-features` · E3 `dbxfe-mlflow` · E4 `dbxfe-serving` · E5 `dbxfe-forecasting` · E6 `dbxfe-deep-learning` |
| F GenAI, agents and applications | F1 `dbxfe-genai` (kept) · F2 `dbxfe-retrieval` · F3 `dbxfe-genai-eval` · F4 `dbxfe-tools` · F5 `dbxfe-ai-platform` · F6 `dbxfe-apps` |
| G Architecture, migration and operations | G1 `dbxfe-m08` (kept) · G2 `dbxfe-sqlserver` · G3 `dbxfe-warehouse-migration` · G4 `dbxfe-operations` · G5 `dbxfe-lakebase` · G6 `dbxfe-industry` |
| H Customer discovery, evidence and delivery | H1 `dbxfe-m01` · H2 `dbxfe-m02` · H3 `dbxfe-m09` · H4 `dbxfe-m10` · H5 `dbxfe-m11` · H6 `dbxfe-m12` (all kept) |

Tracks are groupings on the course map, not a compulsory navigation layer.
The suggested primary route is A1 → (optional bridges) → A3 → B1 → B3 → the
transformation/recovery topics, then branches. Field guides and H modules are
reachable throughout. Nothing is locked.

## Architecture decisions

- Content growth is content, not engine: modules are `content/courses/dbxfe/modules/<id>.json`
  package files (module map entry + scenario + sources + claims + course concepts),
  lessons under `lessons/`, teaching modules under `content/teaching/dbxfe/`,
  media placements in `media-<module>.json`, guides/labs/cases as Markdown
  bodies indexed from `course.json`.
- The renderer stays generic: tracks, labs, guides, cases and crosswalk are
  optional course fields validated by `src/content-schema.ts`; an unrelated
  course without them still renders (proved by the content-only extension test).
- Scale: the initial JavaScript keeps only catalog metadata; lesson bodies,
  card text, check text, scenario bodies, guide/lab/case bodies and teaching
  modules load lazily from same-origin JSON with validation and retry.
- No backend, runtime tutor, code runner, AI dependency, analytics, sync or
  workspace access is added. Downloads remain hash-validated static archives
  with the existing member whitelist and bounds.

## Evidence boundaries in this build session

- The build sandbox reaches PyPI but its egress proxy blocks documentation and
  video hosts. Search-result titles and snippets were available; page bodies
  were not. Every new source record says so in `reviewedEvidence`; source
  review is therefore recorded as **search-level, not page-level**, and is a
  named limitation in `ACCEPTANCE.md`.
- No new video placement is marked verified; a documented editorial decision
  per new module (`docs/academy/MEDIA-DECISIONS.json`) names candidates to
  review when a browser with provider access is available, and every new beat
  is complete with its authored visual sequence.
- Local Python, Spark, open-source Delta, MLflow and PostgreSQL executions are
  local executions, not Databricks workspace runs. Nothing is deployed.

## Publication boundary

This branch produces one reviewable pull request. It does not merge, publish,
create previews, change the Site, enable Pages, alter settings or credentials,
or provision cloud resources. `docs/academy/RELEASE.md` prepares the later,
separately authorized publication.
