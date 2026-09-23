# Authoring brief for academy modules

This is the working standard for every new module in *Databricks: Build,
Explain, Deliver*. Read it together with `docs/AUTHORING.md` (the engine
contract), `src/content-schema.ts` and `src/teaching-schema.ts` (the exact
field contracts) and one finished exemplar: `content/teaching/dbxfe/dbxfe-delta.json`
with `content/courses/dbxfe/lessons/dbxfe-m03-l02.{json,md}`. The check
`node --import tsx scripts/academy-check.ts --module <moduleId>` must print
`PASS (no failing findings)` before a module is considered authored.

**Read `docs/academy/KIT.md` first.** It holds real excerpts of the finished
new-module exemplar (`dbxfe-aws`, D3): the module package, lesson JSON and
Markdown body, one beat with its visual, a Samajh, objective and self checks,
card links, an extension card, recap, applied task, sources/claims/concepts and
a media decision record. Do not read the full exemplar files; if a shape is
unclear, print only the element you need with a one-line python command.

### Lessons from the pilot (apply them)

- **Write with a generator.** Author each large JSON file from a Python
  generator script in the scratch directory (`python3 gen_<module>.py`), then
  parse-check it; fix findings with targeted edits rather than re-reading whole
  files. Split the generator into parts if it grows past ~40 KB.
- **Cross-module links.** Markdown links of the form `#/module/<id>` may target
  only modules already registered in `content/courses/dbxfe/course.json`: the
  sixteen retained modules and `dbxfe-aws`. Other academy modules are still
  being written; name them by title in prose (e.g. "the streaming module"). The
  course map and module recap provide navigation between modules. Teaching
  JSON must not link to other modules at all (the runtime validates one module
  at a time); lesson Markdown may link to the registered modules above and to
  `#/lesson/<id>` of retained lessons.
- **Partial work may already exist.** An earlier author may have been
  interrupted. Before writing, list your assigned paths (and the scratch files
  named in your assignment); keep anything correct and complete, finish or
  replace the rest, and never leave a half-written file.
- **Registration is the integrator's.** Never edit `course.json`, other
  modules, `src/`, `scripts/`, `tests/` or shared docs. Your teaching file is
  auto-discovered by the build once registered; until then only the isolated
  check sees it.
- **Honest sources.** Documentation hosts are blocked from this sandbox; use
  WebSearch to confirm titles and URLs and record the limitation in
  `reviewedEvidence` exactly as in the kit. Never invent a URL.


## 1. Files a new module owns

For module id `dbxfe-<slug>` (already assigned in `content/courses/dbxfe/academy.json`):

| File | Purpose |
|---|---|
| `content/courses/dbxfe/modules/dbxfe-<slug>.json` | Module package: `{ "module": {...}, "scenarios": [...], "sources": [...], "claims": [...], "concepts": [...] }`. The `module` object is the course-map entry (`id`, `title`, `summary`, `objectives`, `prerequisiteIds`, `lessonFiles`, `scenarioId`). `scenarios` holds this module's applied scenario (rubric ≥3, `isCapstone: false`). `sources`/`claims`/`concepts` are COURSE-level registers used by the lesson's sections, cards and questions (concepts need `lessonId`/`sectionId`). |
| `content/courses/dbxfe/lessons/dbxfe-<slug>-l01.json` + `.md` | One canonical lesson (`teachingFormat: "flexible"`, `contentVersion: "1.0.0"`), with `<!-- section:<stable-id> -->` markers. ≥2 questions, ≥10 cards (these are the module's core cards), 600–1,800 words across sections, kinds including `outcome`/`prerequisites`, `mechanism`, `example`, `exercise`, `solution`, `mistakes`, `sources`, `related`, `revisit`. Code and tables live here and in the handbook. A second lesson is allowed when the material genuinely splits. |
| `content/teaching/dbxfe/dbxfe-<slug>.json` | The teaching module (`schemaVersion: 1`, `courseId: "dbxfe"`, `moduleId`, `lessonIds` = exactly the package's lessons). Beats, visuals, module-level sources/claims/concepts, checks, cardLinks for EVERY lesson card, exactly 4 extension cards, recap, applied task. |
| `docs/academy/media-decisions/dbxfe-<slug>.json` | Video research record (see §7). No `media-<slug>.json` is written in this build because playback and captions cannot be reviewed here. |
| `content/exercises/<lab-id>/…` | Only when the module owns a lab (see LAB-BRIEF.md); the lab is a separate task. |

Do not edit `course.json`, other modules, `src/`, `scripts/`, tests or the
design snapshot. The integrator registers the package in `course.json`.

## 2. Identity rules

- IDs: lowercase, start with a letter, letters/digits/hyphens, prefixed
  `dbxfe-<slug>-`. Keep every ID immutable once written. Never reuse an
  existing ID for a new meaning (search the repo before choosing).
- Beat IDs `dbxfe-<slug>-<word>`, visual IDs `…-<word>-visual`, question IDs
  `…-<word>-question` with options `…-question-a|b|c|d`, self-questions
  `…-<word>-self`, module concepts `…-<word>-concept`, module sources
  `…-source-<word>`, module claims `…-claim-<word>` plus the two conventional
  claims `dbxfe-<slug>-guidance` (kind guidance) and `dbxfe-<slug>-fiction`
  (kind fictional). Lesson section IDs `dbxfe-<slug>-l01-<word>`, cards
  `dbxfe-<slug>-l01-card<n>`, lesson questions `dbxfe-<slug>-l01-q<n>`, course
  concepts `dbxfe-<slug>-l01-<word>-concept`, scenario `dbxfe-<slug>-scenario`
  with rubric `…-scenario-rubric-<n>`, extension cards
  `dbxfe-<slug>-extension-<word>` with concept `…-extension-<word>-concept`.
- Beat `version` "1.0.0"; card/question `revision` "1".

## 3. The beat contract (11–16 beats; usually 11–13)

The academy floor is 480 beats over 48 modules and the retained modules carry
136, so every new module needs at least 11 beats; `academy-check --module`
fails below that.

Every beat teaches one idea or one reasoning step and has:

1. `title`: a claim the learner can carry ("A replacement is not another row
   to add"), never "Overview", "Key concepts", "Deep dive". Unique in the module.
2. `outcome`: what the learner can do after it (one sentence).
3. `explanation`: 40–100 words of plain English (hard cap 120). One idea.
   Concrete records, request paths, intermediate outputs, cause → effect.
   Use `[[concept-id|visible term]]` for at most 1–3 taught concepts. No
   headings, no code blocks (code belongs in the handbook and lesson).
4. `visualId`: the dominant visual (see §4). The beat's explanation must
   point at what to notice in it ("notice that A1 is excluded").
5. `samajh` (optional, ≥2 per module, more for abstract mechanisms): §5.
6. `questionIds`: one check about the idea just taught (§6). Objective
   questions live in module `questions`; open ones in `selfQuestions`.
7. `hint` (optional): a nudge, never the answer.
8. `handbook.markdown`: 120–400 words of real depth: mechanism, worked
   example with numbers, code where relevant (fenced ```python / ```sql),
   implementation detail, limits, troubleshooting, what to inspect. This is
   where the eight questions get answered across the module (what is it, why
   use it, how does it work, when not, what fails, what to inspect, how to
   explain it, how to demonstrate honestly). `handbook.sourceSectionIds`
   names the lesson section(s) that carry the original depth for this beat.
9. `recap`: one sentence the Today page can show.
10. `changeNote`: "New academy beat." for new modules.
11. `mediaIds`: `[]` in this build.

Opening a beat, changing a state, revealing an answer or moving Next never
counts as completion; the engine enforces that. Do not write "you have now
mastered".

## 4. Visuals (one per beat; `nodes`, `comparison`, `timeline`, `table`, `equation`)

A visual externalizes a mechanism: movement, membership, ordering, state,
comparison, cardinality, boundaries, causality, uncertainty, an observable
result. Each visual needs `title`, `alt`, `caption` (label synthetic numbers
"Synthetic teaching example"), `textEquivalent` (every state title and every
node label/table cell, in reading order), `provenance` ("Original SpicyBrain
authored visual; synthetic values; no copied product screenshot or executed
cloud result." or, when it reflects a real local run, say which lab produced
it), `claimIds`, and 1–12 `states`. Consecutive states must differ in their
mechanism (nodes/connections/table/equation), not only in prose. A state with
`nodes` needs ≥2 nodes (each with `status` selected/context/excluded/pending/
warning and a `detail`), or a `table` (columns + ≥1 rows), or an `equation`
string. Use a mix across the module: request/trust-boundary diagrams (nodes +
connections), before/after membership (nodes with selected/excluded), tiny
datasets with highlighted intermediate outputs (table states), join
cardinality, timelines (kind timeline, nodes in time order), plan trees
(nodes with connections), matrices (table), equations with interpreted values.
Keep labels short so they stay legible at 390px.

## 5. Samajh (Hinglish analogies)

Natural, warm, informal Hinglish in Latin letters, 25–120 words (typically
40–90), one precise mapping sentence (`mapping`, English) from the familiar
situation to the technical parts, and an English `boundary` saying where the
analogy stops being accurate. Do not reuse one metaphor across the module
(the check warns after two uses of the same household image). No condescension,
forced slang, jokes-as-answers or unexplained transliteration. English stays
primary; Samajh is optional and collapsible.

## 6. Checks

- Objective (`questions`): 3–5 options, one correct, a specific `rationale`
  for every option (why right / why the misconception is wrong), no two
  defensible answers, the answer must not be visible in the title. Prefer
  output prediction, error diagnosis, counterexamples, choosing an experiment
  or a tradeoff about the specific idea just taught.
- Open (`selfQuestions`): `modelAnswer` ≥25 words that a learner can compare
  against, `reasoning` ≥12 words on why it works and acceptable alternatives.
  The engine labels these self-comparison; never imply machine grading.
- Mechanism/coding modules (`checkStyle: objective-heavy` in academy.json)
  need ≥50% objective checks with well-specified, checkable results.
- `conceptIds` ≥1 per check; `claimIds` for factual content.

## 7. Sources, claims, concepts and honesty

- `sources`: current primary documentation with `title`, `url` (https),
  `publisher`, `reviewedAt` ("2026-09-23"), `publishedAt` (null unless known),
  `context` (cloud/runtime/edition), `caveat`, `reviewedEvidence`. **This
  build sandbox blocks documentation hosts.** Use WebSearch to confirm the
  page title and URL and to read the snippet; then write `reviewedEvidence` in
  this shape: `"Search-result title and snippet confirmed 2026-09-23; page
  body not fetched in this build (documentation host blocked by the sandbox
  egress proxy). Passage relied on, as previously read: …"`. Never claim to
  have read a page in this session. Prefer the source index in
  `docs/academy/CONTRACT.md` and Databricks/Apache/Microsoft/Google/AWS/
  MLflow/scikit-learn primary pages. Do not invent URLs; if unsure of a
  URL, use the documented landing page from the index.
- **When web search is unavailable** (the build session's search budget is
  finite and was exhausted on 2026-09-23): first reuse a source record that
  another module already confirmed by search (same URL, title and publisher;
  keep its original `reviewedAt` and say whose confirmation it was). Otherwise
  cite only a documentation landing page you are sure exists, and write
  `reviewedEvidence` that says plainly the URL and title were not confirmed in
  this build session; hedge or drop any detail that only such a page would
  support. Never present a URL recalled from memory as confirmed. CI's
  `npm run report:sources` probes every URL and lists the unreachable ones,
  which the integrator corrects or removes before release.
- `claims`: `documented` (needs sourceIds), `guidance` (original professional
  reasoning), `fictional` (synthetic records/organizations). Every beat,
  visual, check and card cites the claims it rests on.
- Preview, private-preview or region-specific features are named as such in
  `context`/`caveat`, never turned into universal recommendations. Newer
  product names (Declarative Automation Bundles, Genie Agents, Genie One, AI
  Search, OpenSharing, Lakeflow) are used with their former names as
  searchable `aliases` on concepts; CLI commands, config keys, API resources
  and protocol identifiers are never mechanically renamed.
- No invented product UI, customer logos, real telemetry, fabricated
  screenshots, pricing or benchmark numbers presented as measured. Synthetic
  numbers are labelled synthetic. Real prices need a current source, date,
  currency, unit and region — otherwise say "check current pricing".
- No learner biography, job title, employer or level anywhere.
- Concepts (module-level): `term`, `aliases`, `definition` (≥6 words, one
  authoritative definition), `example` (concrete), `sourceIds`. Define
  acronyms at first use.

## 8. Cards

- Core cards = the lesson's `cards` (≥10, distinct, each mapped in
  `cardLinks` to the beat that teaches it). Extension cards = exactly 4
  `extensionCards` with `beatId`, `whyItMatters` and their own concept and
  documented claim; each is a genuinely researched related question with its
  own sufficient explanation, not a paraphrase of a core card.
- Prompt ≥5 words, answer ≥8 words, explanation ≥25 words (enough to
  understand, not "correct"). Mix formats: explain a mechanism, predict a
  result, spot a misconception, choose a diagnostic next step, contrast
  alternatives, interpret a small diagram, state a limitation. No trivia,
  no obscure numeric limits, no prompt whose answer is in the title.

## 9. Recap, applied task, scenario

- `recap.markdown` ≥30 words with the module's through-line and a transfer
  challenge; `recap.visualId` reuses the module's best summary visual.
- `appliedTask`: a concrete task on a changed dataset/situation, `modelAnswer`
  ≥60 words, `reasoning` ≥15 words, `beatIds` ≥2.
- Package `scenarios[0]`: context, task, ≥3 requirements, `model` ≥120 words,
  `reasoning`, rubric ≥3 (`weak`/`partial`/`strong` anchored), ≥1 authored
  stakeholder `disclosures`. Fictional organizations only; a mixed or
  negative outcome is welcome where honest.

## 10. Media research record (`docs/academy/media-decisions/<moduleId>.json`)

```json
{
  "moduleId": "dbxfe-<slug>",
  "date": "2026-09-23",
  "decision": "no-placement",
  "reason": "Video hosts and captions are unreachable from the build sandbox; a placement cannot be reviewed or playback-verified. The beat sequence is complete with authored visuals.",
  "suggestedBeatId": "dbxfe-<slug>-<beat>",
  "candidates": [
    { "title": "…", "creator": "…", "url": "https://…", "foundVia": "web search 2026-09-23", "whyRelevant": "…", "reviewed": false }
  ]
}
```

List 2–3 candidates from official/original creators when search finds them
(Databricks, Delta Lake, Apache Spark, Microsoft Learn, MLflow, 3Blue1Brown,
Stanford). Never invent a URL; omit a candidate rather than guess.

## 11. Style

English primary, second person, concrete over abstract, manufacturing examples
first (Cinderline Components is the shared fictional manufacturer; other
fictional names are welcome) with one transfer to another industry where it
helps. SQL and data-modeling bridges for a SQL-fluent reader; Python,
distributed execution and cloud identity/networking explained deliberately.
Label simplifications as schematics. Never require a Databricks workspace,
a paid service or an LLM call to understand the material.

## 12. Definition of authored

`node --import tsx scripts/academy-check.ts --module dbxfe-<slug>` passes with
no FAIL lines, warnings are read and either fixed or justified in the agent's
final report, the eight questions are answered somewhere in the module, and
the contract topics from `academy.json` are genuinely taught (not merely
mentioned).
