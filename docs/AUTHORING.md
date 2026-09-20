# Content authoring

1. Add `content/courses/<directory>/course.json`. Use `tests/fixtures/photography/content/courses/photo/` as a small complete worked package, or `content/courses/dbxfe/` for the full course. Do not add an app registry entry, route, component or feature flag.
2. Supply globally unique, course-prefixed IDs for course/module/lesson/section/concept/claim/source/asset/question/option/card/scenario/rubric. Keep them immutable through title/file/order changes. IDs start with a lower-case letter and contain lower-case letters, digits or hyphens; see the schema for limits.
3. The course declares schema/content versions, title/subtitle/summary, objectives, prerequisite IDs, tags, review date, change notes, refreshers, modules, source/claim register, glossary/aliases, assets and scenarios. Each module declares ordered `lessonFiles`, objectives, summary, prerequisites and a valid `scenarioId`. Related modules may reference the same canonical scenario without duplicating its identity. Optional `capstoneId` must address a separate capstone scenario. An optional package-specific `contract` enforces minimum distribution; extra topics do not violate it. The independent preservation manifests protect the original launch and accepted study-hub IDs.
4. Each lesson JSON names its safe relative `.md` `bodyFile`. Legacy lessons retain exactly seven kinds: `why`, `understand`, `see`, `deeper`, `customer`, `try`, `revisit`. New or deepened lessons declare `teachingFormat: "flexible"` and choose their sequence; `customer` is not required. Every section carries a stable ID, kind, title and concept/claim/asset references. Prefer `<!-- section:your-stable-section-id -->` Markdown markers, which allow repeated kinds. Legacy unique kind markers remain valid. Unmatched, duplicated or unassigned blocks fail the build. Use kind `solution` for an initially collapsed answer and `exercise` for the independently visible task. Author outcome, prerequisites, mechanism, worked example, complete explained solution, common mistakes/limits, sources and related-topic links. At least two checks and three distinct cards remain required. Estimates are reading-time estimates, not timers.
5. Questions have stable option IDs, one correct option ID, a rationale for every choice and concept/claim mappings. Cards identify their lesson/section and concept/claims. Use plausible misconception distractors; avoid two defensible correct answers. Practice requires context, task, requirements, a full model and reasoning, optional authored disclosures, and at least three anchored weak/partial/strong rubric dimensions. The app labels free-response evaluation as self-assessment.
6. Put original SVGs in `content/assets/` and declare caption, alt, complete text equivalent, provenance/rights and claim mappings. SVGs need `<title>` and `<desc>`; scripts, event handlers, foreign objects and external resources are rejected. Do not put images or executables in Markdown. Supported prose elements are paragraphs, headings h3/h4, lists, emphasis, blockquotes, code, tables and safe links. Diagrams use explicit asset references. No raw HTML, MDX, arbitrary scripts or code evaluation.
7. Read current primary documentation for material product assertions. Record source URL/title/publisher/type/context/access and review dates/caveats; connect documented claims to specific supporting sources, then reference claims on sections/cards/questions/scenarios/assets. Guidance and fiction are separate claim kinds. Availability checks do not prove facts. Avoid real customer information and copied proprietary training.
8. Run `npm run prepare:content`, `npm run check`, `npm run test:e2e` (also create the nested build), and `npm run test:content-extension`. Run the independent source report and inspect the affected lessons/assets in the browser. Update course change notes and editorial review. A normal package addition should change content inputs and generated evidence, not engine logic.

## Revisions and removal

### Teaching modules and beats

Add `content/teaching/<course>/<module>.json` and, when needed, `media.json`; automatic discovery needs no application edit. The complete two-module unrelated example is under `tests/fixtures/photography/content/teaching/photo/`. The validator in `src/teaching-schema.ts` is the exact field contract. A course can use any nonempty module count; the 16-module Databricks release test is a content acceptance test, not a renderer limit.

For each module, declare its canonical lesson IDs, outcomes, starting assumptions, optional bridges and editorial rationale. Author stable-ID concepts (English definition, example, aliases, sources), claims (documented/guidance/fictional) and actual source review evidence with date and version/cloud caveats. Use `[[canonical-concept-id|visible term]]` where an in-context definition helps; ordinary words and code are not auto-linked. Add only supported semantic visuals (`nodes`, `comparison`, `timeline`, `table`, `equation`) with readable labeled states, relations, text equivalent, caption and provenance. Test every state on a phone; never hide a missing diagram behind a generic illustration.

Each beat links its canonical lesson/section and shared visual/concept/claim/check IDs. Keep the main explanation concise; explain mechanics, worked cases, code, limits and troubleshooting in `handbook.markdown`. `handbook.sourceSectionIds` points to essential original depth rather than pasting every legacy section. Optional Samajh has natural Hinglish text, an explicit mapping and an English boundary. Do not add an empty Samajh control. Self-questions need a model answer and reasoning; objective questions need deterministic answers and rationale for every option. Recap and applied task must teach transfer, with a worked solution.

Map original cards through `cardLinks`; do not clone their scheduling identities. New `extensionCards` need stable IDs/revisions, concepts, claims, exact beat/reference anchors, a fully taught answer/explanation and `whyItMatters`. Audit them against the deck and handbook: a paraphrased recall card is not a researched extension. Each is also rendered at its exact handbook extension anchor, so **Revisit this explanation** reaches sufficient teaching. Core/extension labels indicate provenance, not confidence. Introductions require a learner choice.

Media records include actual reviewed evidence and method, candidate comparisons, creator/original URL, known or unknown publication/duration/segment metadata, language/caption availability, cloud/version limits, placement, watch-for/use-next prompts and an authored illustrated fallback. Reference its ID on the chosen beat. Check the real segment and its captions/companion; an HTTP200 does not approve teaching. Only mark `embeddingStatus: verified` after real in-app consent/playback verification. Use the narrow allowed YouTube privacy-enhanced URL shape; never download/rehost a creator's video/slides or insert arbitrary frames. Unknown/unavailable players retain their external original and equivalent teaching.

Increment the beat version for a material teaching change and the question/card revision for changed assessment meaning. Cosmetic title/order changes keep identities/revisions. New beats never inherit old section completion; old attempts/reviews remain immutable evidence. Add changed content to search through the ordinary content build, run the existing acceptance/extension checks, inspect every visual and update the coverage/editorial/media record. Generated public files are not hand-edited.

A cosmetic title/spelling/reordering change preserves the card/question `revision`; it must not reset history. Material answer or assessed-concept changes increment the respective revision and lesson/course `contentVersion`, with a change note. Prior attempts retain the original prompt/options/correct choice/version. Prior review events retain the old revision. Changed cards are surfaced for an actual new-revision review, even if their previous schedule is later; the UI discloses that these are included. Old question attempts receive a revised-question notice until the new revision is answered.

Never reuse a removed ID for a different concept. Removed notes/drafts and history remain recoverable; obsolete source links land on an explained fallback. Breaking prerequisites or leaving unresolved required assets is a validation error, not an acceptable way to remove a lesson.

## Paths and playbooks

Add a JSON file under `content/paths/`. Discovery is automatic. A path is an ordered view of existing canonical lessons, including lessons from more than one course. It does not create another note, completion, card or question identity. The unrelated photography example is `tests/fixtures/photography/content/paths/photography.json`.

```json
{
  "schemaVersion": 1,
  "id": "sample-path",
  "title": "An intentional sequence",
  "summary": "A concrete learning outcome in a useful order.",
  "outcomes": ["Explain and apply the concept."],
  "startingAssumptions": ["State what the learner is expected to know."],
  "defaultStart": false,
  "groups": [
    {
      "id": "sample-group",
      "title": "Build the model",
      "purpose": "Explain why these topics belong together.",
      "lessonIds": ["existing-lesson-id"]
    }
  ],
  "prerequisites": [],
  "optionalBridges": [],
  "playbooks": []
}
```

The IDs in this illustrative snippet must be replaced with valid catalog targets before publication. Only one path may declare `defaultStart: true`; the Today page reads that content metadata. Each prerequisite is `{lessonId, requiredLessonId, explanation}`. Each optional bridge is `{lessonId, beforeLessonIds, explanation}`. Nothing is locked. Bridge lessons are separate from core groups; opening a bridge does not complete it. Prerequisites and bridge dependencies are checked for missing targets and cycles alongside canonical lesson prerequisites.

Each playbook is `{id, title, summary, targets}`. A target requires `courseId` and a human-readable `label`, plus either `lessonId` with optional `sectionId`, `scenarioId`, or neither to link to the course. Refer to an existing action section instead of duplicating the lesson body. Targets are validated against their owning course in the full catalog.

Use `#/lesson/<lesson-id>/<section-id>?path=<path-id>` to enter an explicit sequence. Legacy links without path context still work and use a disclosed course fallback. Path IDs are navigation preferences only; titles, files and display order never own learning evidence. Keep a bridge useful even when entered directly. Path JSON also supplies searchable roadmap and playbook titles.

## Downloadable exercises

Put a local `.zip` bundle under `content/downloads/`, then declare course `downloads` entries containing `id`, `title`, `description`, safe relative `path`, `mediaType: "application/zip"`, and the lowercase SHA-256 hash. Add its ID to each relevant lesson's `downloadIds`. The path is relative to `content/downloads/`, for example `reliable-data-exercises.zip`. The build copies only validated, referenced bundles into generated `public/content-downloads/`; it never runs their contents.

Archives may contain `.md`, `.txt`, `.json`, `.csv`, `.py`, `.sql` and `.toml` files. Limits are 20 MB compressed, 50 MB total declared expanded size and 200 entries. Traversal, absolute or reserved paths, symlinks, encryption, duplicate/case-colliding names and unsupported compression are rejected. The exact bytes must match the manifest checksum. Explain setup, dependencies, expected outputs and known limits in the bundle. Preserve an attempt/solution distinction; do not describe illustrative code as executed cloud evidence. Regenerate the archive and checksum after any bundled-file change.

For Reliable Data Foundations, keep `solutions/` as the source of the complete embedded resolution/Spark/recovery code. From the repository root with the documented Python 3.12/Java 17 environment:

```sh
python content/exercises/reliable-data/sync_lesson_examples.py --embed-source
python content/exercises/reliable-data/run_tests.py --spark --evidence docs/evidence/reliable-data-execution.json
python content/exercises/reliable-data/package_bundle.py --output content/downloads/reliable-data-exercises.zip --execution docs/evidence/reliable-data-execution.json
```

The helper updates four stable source sections and regenerates the 11-entry displayed-example manifest. Without `--embed-source` it validates those source sections while regenerating the manifest; stale embedded code fails. Tests compare snippet hashes and full/source-fragment content, as well as the relevant actual Python/SQL/PySpark behavior. Packaging requires a successful complete pinned Spark run with no skips and matching tested source hashes. After packaging, set the course download's SHA-256 to the newly reported digest, run content validation, extract that exact ZIP into a separate directory, and run `python run_tests.py --spark --evidence extracted-execution.json` there. Verify the extracted files against source and the bundle's execution evidence. The app never runs the helper or downloaded code.

After a material correction, increment the affected lesson version and only the cards/questions whose assessed meaning changed. Inspect the rendered explanation, full source expansion, revealed solution and actual download on desktop/mobile production builds. Seed earlier-version study records and confirm revision notices without modifying their saved evidence. These checks supplement the ordinary milestone gates; they do not turn a local test into a Databricks execution.

## Launch preservation

`content/preservation/dbxfe-launch.json` records the original module, lesson, section, card, question, option, scenario, asset and capstone IDs from the pinned launch commit. The build validates every listed identity against the current content, while allowing new lessons and different navigation grouping. This gate replaces the old exact 12-by-3 ceiling. It protects identities and coverage, not prose quality; editorial review still evaluates whether retained and new material teaches something useful.

## Reproduced extension proof

`npm run test:content-extension` adds the original photography fixture (2 modules, 4 lessons, 12 cards, 8 checks, 2 diagrams, 2 scenarios), its roadmap and task playbook using only `content/courses/photo/**`, `content/assets/photo-*.svg` and `content/paths/photography.json`. It verifies roadmap discovery, a path order deliberately different from course order, canonical playbook links, all lesson/scenario rendering, asset loading, checks, search, notes, bookmarks, completion and review. It renames module/lesson titles, reverses ordering and question options, and changes JSON/Markdown filenames while retaining IDs. Actual stored notes, completions, attempts and immutable card history are compared. A material revision is then reviewed. Cleanup removes the course and path fixture and verifies production again contains only `dbxfe`, with orphan notes still recoverable.

The exact added/changed/deleted paths and before/after hashes are in [content-extension.json](evidence/content-extension.json). `runtimeSourceChanges: []` is asserted, not inferred. The fixture is committed only under tests and never appears in the production build.
