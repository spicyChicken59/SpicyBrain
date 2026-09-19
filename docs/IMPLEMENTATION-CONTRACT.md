# Implementation contract

Derived from the supplied SpicyBrain_NEXT_BUILDER_PROMPT.pdf (17 pages), provided for this implementation session on 2026-09-19. This is an extracted assignment, not a recovered original Markdown brief. The owner explicitly chose the existing public repository. Account identity details are omitted. No learner study data is included.





SPICYBRAIN


NEXT BUILDER PROMPT
You are Tahir's dedicated SpicyBrain builder in this fresh implementation session. Astra and
Fable retain their existing projects. The guidance project owns product decisions, curriculum
guidance, and independent acceptance review; you own implementation in SpicyBrain only.


1. Mission and authorization
Deliver one coherent milestone: the finished SpicyBrain v1 learning platform and its
complete first course. Include implementation, original course authoring, validation, real
browser testing, and correction of actual defects. Do not hand off a scaffold, a landing page,
sample modules, an audit-only backlog, or promises to fill the course later. Work through the
complete contract below before declaring the milestone ready.

Product: SpicyBrain - Learn it. See it. Use it. Remember it.

Purpose: Make complicated things click through clear explanations, purposeful pictures and
diagrams, worked examples, applied practice, flashcards, retrieval, lesson-linked notes, and
effortless resumption. Build the general learning engine once; subsequent ordinary work should
improve or add content.

Learner context: Assume Tahir is newly in a Databricks customer-facing pre-sales field
engineering role and is learning to do the job. This is not interview preparation. Build
practical understanding, sound customer-facing judgment, technical fluency, and useful everyday
work habits. Explain what to do, why it matters, what good work looks like, when to ask for help,
and how to validate an answer. Do not organize the course around hiring stages, interview
questions, recruiter guidance, or passing an assessment. This explicit clarification supersedes any
interview-preparation framing in the older project brief.

Authorized scope: inspect and work in the existing public repository spicyChicken59/SpicyBrain;
create a focused branch; edit, test, commit, push, and open one implementation PR. Tahir created
this public repository and explicitly reported that choice after the original handoff. This supersedes
the earlier private-creation default for this repository only. Do not create another repository or
change its visibility. A minimal initial README commit on the verified empty repository's main is
permitted solely to establish the PR base. Put all platform and curriculum implementation on the
feature branch. Code, course content, commits, and PR material must be safe for public viewing;
exclude confidential materials and personal study data.

Do not merge, enable auto-merge, change repository visibility, or publish a website under this
assignment. Public source-code work in the user-created repository is authorized; website
deployment is a separate decision and requires Tahir's explicit approval of the exposure model. Do
not add paid services, provision cloud resources, invite collaborators, introduce unattended
agents, or schedule ongoing work. Do not solicit approval again for normal implementation already
authorized here.

SpicyStock, SpicyHome, SpicyCar, and spicyChicken59/design-system are read-only references.
Do not change their files, branches, PRs, workflows, permissions, or deployments. Do not reassign
their builders. Do not expand into other SpicyChicken projects.









2. Verified starting evidence and repository setup
Repository verification: 2026-09-19 at approximately 07:38 UTC, after Tahir created the public
repository. Source/design inspection remains dated 2026-09-19. Treat these as dated
observations, then recheck before mutations.

  Item                            Observed evidence


  Project contract                Supplied SpicyBrain_Project_Brief.pdf, prepared 2026-09-18, 17 pages,
                                  read in full. No SpicyBrain_Project_Brief.md was found in the supplied
                                  workspace or exact-title/short-title file searches. The PDF and Tahir's current
                                  instructions were used. Tahir subsequently clarified that he is newly in the role
                                  and wants job learning, not interview preparation; that clarification
                                  governs this assignment. All operative requirements are reproduced in this
                                  prompt; you do not need attachment access.


  PDF fingerprint                 SHA-256
                                  190c821dd15cb90ecd7fef7c1d981882d1269654a5a849d1622e955f92daf1e4.


  Existing repository             spicyChicken59/SpicyBrain
                                  https://github.com/spicyChicken59/SpicyBrain, repository ID 1376873797, public, not
                                  archived. The authenticated repository lookup now succeeds. Tahir created it;
                                  guidance made no repository changes. The earlier repository-level
                                  404/creation blocker is superseded.


  Target permissions              Repository metadata reports pull, push, admin, maintain, and triage as true.
                                  This verifies the reported account permissions, not a performed write test; the
                                  builder must verify its own session can perform required operations.


  Default branch and              Repository metadata names main as the default, but /branches/main returns
  starting HEAD                   Branch not found and root contents explicitly return This repository is
                                  empty. There is no starting commit SHA or actual branch yet. Do not
                                  fabricate one. Initialize minimally only after rechecking that it is still empty.


  Open PRs and                    The open-PR collection is empty. Actions reports total_count: 0 and no
  workflow runs                   workflow runs. No tests have run for SpicyBrain.


  Shared design                   spicyChicken59/design-system, public, default branch main, source commit
  reference                       14a752dd0269bd6ebbb7080eb0d9e1922cd1ef2c, version v2.13.0. README,
                                  design standard, checklist, visual reading guidance, vendor script, and license
                                  were inspected read-only.


  Sibling reference               SpicyStock main was 9ebf27ca42845d2892fc5868a80a253b1ceadccd. Its
                                  package.json is minimal static/test tooling, not a learning-platform
                                  architecture to copy. No sibling changes were made.









  Item                            Observed evidence


  Deployment                      No SpicyBrain site, production URL, hosting access policy, or live browser
                                  acceptance result has been established by guidance. Deployment inventory
                                  could not be read through the connector because that endpoint is
                                  unsupported; do not turn that limitation into a verified claim of no
                                  deployments. Public repository creation does not authorize website
                                  deployment.


Your first actions:

1. Verify authenticated identity, the exact existing repository, public visibility, and effective
    read/write permissions in your session. Inspect branches/commits, current branch, clean/dirty
    working tree, open PRs, and intervening work. Read applicable AGENTS.md, CLAUDE.md, README,
    and project documents if they have appeared. Preserve all legitimate newer work; never reset,
    discard, force-push, or overwrite it. Do not recreate the repository or change its visibility.

2. If it is still empty, establish main with one minimal README commit describing SpicyBrain and
    stating that implementation is not yet complete. Record the actual bootstrap SHA. Do not add a
    blanket open-source license to course or brand assets. If another session has initialized it,
    inspect and use that legitimate starting history instead; never overwrite it with your bootstrap.

3. If your session cannot access or write the existing repository, report the exact permission/tool
    blocker and ask for access to this repository, not another creation. Do not infer nonexistence
    from a later 404. Continue useful source/curriculum preparation where possible, but do not
    claim a commit or PR exists unless verified. No API key or password should be requested in
    chat.

4. Branch from the verified actual default-branch HEAD after initialization. Proposed branch:
    feat/spicybrain-v1. Reuse a legitimately existing branch/PR for this same work after inspecting
    it. Record the actual starting SHA and any difference from the empty-repository observations
    above.

5. Save this contract in the repository as public-safe project documentation, clearly derived from
    the supplied PDF and current assignment, including Tahir's public-repository choice. Do not
    claim to have recovered an unavailable original Markdown file. Do not import unrelated
    conversation history or personal data.


3. Product decisions already made
Use React + TypeScript + Vite, static production output, schema-validated content, and
browser-local structured study storage. Select mutually compatible, supported stable
dependencies at implementation time, commit the lockfile, and document the chosen Node
version. Do not inherit a sibling's data pipeline, backend, or operational complexity.

Use JSON metadata and safe Markdown with a small whitelist of teaching blocks. No executable
MDX, arbitrary uploaded HTML, scripts, runtime code evaluation, vector database, or runtime AI
dependency. Build the course catalog and public-content search index from discovered content
manifests. A course must be discoverable without editing a course-specific route, component,
registry in application code, or feature switch.

Use generic hash-based navigation so the static build can support direct lesson links, browser
back/forward, and reloads without assuming a host rewrite service. Stable course, lesson, and








section identifiers own navigation; filenames, display titles, and ordering do not own study state.
Keep data and asset loading base-path-aware and verify both root and nested static serving. If
legitimate existing SpicyBrain architecture is discovered, retain it when it satisfies this contract
rather than rebuilding for a framework preference; document the concrete reason.

Suggested separation:

-   src/: reusable UI, storage, scheduling, search integration, and renderers.

-   content/courses/<course-id>/: course/module/lesson metadata, Markdown, assessments, cards,
    scenarios, glossary, source register, and change notes.

-   content/assets/: original teaching assets with captions, text alternatives, provenance, and
    stable references.

-   public/design-system/: immutable SpicyChicken source snapshot and provenance.

-   scripts/: content validation, index/build preparation, source reporting, and extension
    verification.

-   tests/fixtures/: synthetic study state and a temporary unrelated course; excluded from the
    production catalog.

-   docs/: architecture decisions, content authoring, review schedule, data handling, deployment,
    and acceptance evidence.

V1 must work without a model API, paid provider, Databricks workspace, multiuser backend, or
arbitrary code runner. Reading, visuals, checks, practice, review, notes, search, and export/import
must all be functional locally. Do not display controls for an AI tutor, voice generation, cloud sync,
automatic PDF ingestion, or other excluded features. Do not claim offline/PWA support; it is
outside this milestone.


4. Design and complete user experience
Inspect and pin the verified design source before consuming it:

-   Design README at the inspected commit
    https://github.com/spicyChicken59/design-system/blob/14a752dd0269bd6ebbb7080eb0d9e1922cd1ef2c/README.md

-   Design standard
    https://github.com/spicyChicken59/design-system/blob/14a752dd0269bd6ebbb7080eb0d9e1922cd1ef2c/DESIGN_SYSTE
    M.md

-   Visual recipes, including the reading rail
    https://github.com/spicyChicken59/design-system/blob/14a752dd0269bd6ebbb7080eb0d9e1922cd1ef2c/VISUAL-RECIPE
    S.md

-   Snapshot vendor tool
    https://github.com/spicyChicken59/design-system/blob/14a752dd0269bd6ebbb7080eb0d9e1922cd1ef2c/build/vendor.
    mjs

-   License and brand exception
    https://github.com/spicyChicken59/design-system/blob/14a752dd0269bd6ebbb7080eb0d9e1922cd1ef2c/LICENSE

The inspected system uses cobalt structure, restrained spice actions, flat surfaces, Bricolage
Grotesque headings, Instrument Sans body, IBM Plex Mono labels/code, light/dark/auto themes,
semantic CSS variables, and the original chick. Reuse the mark within Tahir's SpicyChicken









project, preserve its separate rights notice, and do not relicense it as MIT. Name SpicyBrain in type
beside it; do not invent a new mascot or logo. Keep the restrained footer watermark.

Vendor one coherent snapshot with its source commit, version, and SHA-256 provenance. The
README said the v2.13.0 standalone release tag was not yet published: use the committed
snapshot, not an assumed CDN tag. Leave upstream untouched. Load only the runtime pieces
actually used. Use .sc-doc, .sc-reading, chapter navigation, semantic buttons/inputs, and other
suitable family patterns. Page-specific learning layouts may be implemented inside SpicyBrain
using the existing semantic tokens; this contract does not require modifying the shared system.

Prioritize reading comfort: about 65-70 characters per prose line, comfortable body size, generous
spacing, clear hierarchy, and expandable depth. Do not cram learning into a stock dashboard.
Preserve the family typography and use reader-specific sizing in SpicyBrain when needed. Avoid
decorative metrics, large animated backgrounds, compulsory timers, guilt-based streaks, or
medical efficacy claims. Motion must be purposeful, optional, and disabled by reduced-motion
preferences.

Implement all surfaces:

  Surface                         Required behavior


  Start / Resume                  Honest first-run empty state and one obvious primary action. Later resume the
                                  exact lesson and stable section, with sensible scroll-position restoration after
                                  rendering. Offer a small optional study session, due-card review, or one
                                  practice exercise as secondary choices. After a break, show the last real topic
                                  and one gentle next action.


  Courses                         Content-driven catalog and course map with outcomes, prerequisites, optional
                                  refreshers, estimated reading time labeled as an estimate, and explicit lesson
                                  completion. No locked filler or "coming soon" entries. Free navigation supports
                                  learners who already know a foundation.


  Lesson reader                   Clear explanations, substantive worked examples/visuals, expandable
                                  technical detail, a customer-facing explanation, checks, notes/bookmarks,
                                  source access, previous/next lesson navigation, and focus mode. Focus mode
                                  keeps a visible exit and essential controls.


  Practice                        All 12 scenarios and the capstone, response drafting and persistence,
                                  structured requirements, revealable model responses, and anchored
                                  educational rubrics. Free responses use explicit self-assessment; no pretend
                                  automated evaluation.


  Review                          Reveal before rating; Again/Hard/Good/Easy; predictable due ordering;
                                  manageable session size; separate new-card introduction and extra practice;
                                  truthful empty and completed-session states.


  Search                          Course titles and text, glossary terms and aliases, and local notes. Label result
                                  type and course; navigate to the relevant lesson/section or note. Index
                                  personal notes only on-device. Return honest no-results states.


  Notebook                        Searchable lesson-linked notes, bookmarks, unresolved-question state,
                                  autosave status, editing, and return-to-source links. Preserve drafts on failure
                                  and show unsaved state honestly.








    Surface                       Required behavior


    Settings / study data         Theme and focus/session preferences; local-storage disclosure; complete
                                  versioned export/import with merge/replace preview; protected reset. Export
                                  is a manual transfer/backup action, not cloud sync.


Navigation must be calm on desktop and phone. Support keyboard-only operation, visible focus,
meaningful landmarks/headings, labeled form controls, touch targets, readable code, and
diagrams with zoom/reset and a text equivalent. A modal zoom view must close with Escape and
return focus; a nonmodal view must not claim modal semantics. Avoid page-wide horizontal
overflow at narrow widths or text zoom. Diagrams/code may have clearly labeled internal scrolling
where necessary.

Keep educational wording in the product. Build evidence, schema terminology, and
implementation instructions belong in developer documentation unless they help the learner make
a decision.


5. Complete initial course
Display title: Databricks pre-sales field engineering. Subtitle: A practical learning path for
someone new to the role. Assume Tahir is already in the role. Teach the work: understand the
platform, investigate customer needs, explain choices clearly, design and demonstrate
appropriate solutions, gather evidence, and collaborate effectively. This is independent personal
role-ramp material, not official Databricks employee onboarding, an official syllabus, a credential,
or an employer-endorsed assessment. There is no interview-preparation track.

Do not frame L4 as a target to attain or infer an internal title-to-level mapping. Do not invent an
internal leveling rubric, quotas, performance scorecard, promotion rule, compensation guidance,
hiring prediction, or "L4 readiness" score. Public role guidance can inform general responsibilities,
with its limits stated. Any first-weeks or 30/60/90-day suggestions must be labeled as SpicyBrain's
optional learning suggestions, not Databricks' internal ramp plan. Do not invent internal systems,
account procedures, required certifications, or employer deadlines.

Required production catalog totals:

-    12 complete modules, with 3 substantive lessons each: 36 lessons.

-    At least 108 useful flashcards: normally at least 3 distinct cards tied to each lesson.

-    At least 72 explained knowledge checks: at least 2 per lesson, including meaningful
     application rather than only vocabulary recognition.

-    12 applied scenarios: one per module, each with task, context, model response, reasoning,
     and rubric.

-    At least 12 meaningful teaching diagrams: at least one per module, with explanatory
     captions and accessible text. A repeated diagram with a changed title does not count as a new
     teaching diagram.

-    One additional end-to-end fictional customer capstone, not double-counted as one of the
     12 module scenarios.

Use stable, namespaced IDs such as dbxfe-m01-l01, independent of paths and order. These
example IDs are product content IDs, not employer levels.








  Module                Three required lessons                    Module                      Minimum
                                                                  scenario/output             teaching diagram


  1. Role and           1. What pre-sales field engineering       Build an opportunity        Responsibility
  customer              contributes. 2. Partnering with           plan with                   swimlane with
  journey               account executives, specialists,          responsibilities,           decision/evidence
                        partners, and delivery teams. 3.          unknowns, and next          handoffs.
                        Moving from discovery to evidence,        steps.
                        decision, and handoff.


  2. Discovery          1. Business outcomes, stakeholders,       Produce a discovery         Stakeholder/outco
  and                   and consequences. 2. Current              brief and prioritized       me/evidence map.
  qualification         technical landscape and constraints.      questions from an
                        3. Measurable success criteria and        incomplete
                        missing information.                      conversation.


  3. Platform           1. Lake, warehouse, lakehouse, and        Give a plain-English        Storage/compute/ta
  and data              workload fit. 2. Cloud, object storage,   platform narrative          ble-format/governa
  foundations           compute, table formats, and               and a small                 nce responsibilities,
                        transactions. 3. Explain the              architecture sketch.        with limitations.
                        Databricks platform through a
                        customer's needs.


  4. Data               1. SQL/Python/PySpark foundations         Work an                     Ingestion and
  engineering           for the role. 2. Ingestion, CDC, batch    ingestion-to-serving        quality flow
                        versus streaming, and incremental         design and a                showing duplicates,
                        processing. 3. Orchestration, data        synthetic data              late data,
                        quality, retries, idempotency, and        transformation              quarantine, and
                        failure handling.                         exercise with exact         replay.
                                                                  expected output.


  5. SQL,               1. Warehouse, BI, semantic metric,        Explain a diagnosis         A diagnostic
  analytics, and        and dashboard use cases. 2.               plan using synthetic        decision tree
  performance           Diagnose a slow query using               query/workload              distinguishing
                        evidence. 3. Concurrency, sizing, cost    evidence.                   query, data-layout,
                        tradeoffs, and business-user                                          and compute/concu
                        experience.                                                           rrency causes.


  6.                    1. Unity Catalog objects and              Produce security            AWS-context
  Governance,           governance responsibilities. 2.           questions and a             trust/access
  security, and         Identity, privileges, ownership, and      least-privilege access      boundaries
  cloud                 sharing. 3. Network/deployment            design with explicit        distinguishing
  deployment            boundaries and security discovery.        assumptions.                classic and
                                                                                              serverless
                                                                                              deployment.


  7. ML, GenAI,         1. Model lifecycle, data leakage,         Design an AI use case       Retrieval and
  and agents            baselines, and evaluation. 2.             with an evaluation          tool-use flow with
                        Retrieval, serving, tools, and when an    set, acceptance             authorization,
                        agent is justified. 3. Governance,        criteria, and human         evaluation, and
                        monitoring, safety, cost, and failure     escalation.                 failure boundaries.
                        modes.









  Module                Three required lessons                  Module                      Minimum
                                                                scenario/output             teaching diagram


  8. Architecture       1. Current state to target state. 2.    Defend a target             Current/transition/t
  and migration         Reliability, performance, cost, and     architecture and an         arget architecture
                        interoperability tradeoffs. 3. Phased   alternative, then           with reconciliation
                        migration, reconciliation, rollback,    stage a reversible          and rollback.
                        and explicit assumptions.               migration.


  9. Demos and          1. Discover the demo's audience and     Write a short demo          Demo narrative
  technical             decision. 2. Tell a business and        script, evidence plan,      with a visible
  storytelling          technical story using evidence. 3.      and fallback path.          recovery branch.
                        Handle failure and questions you
                        cannot answer.


  10. Proof of          1. Baselines and measurable success.    Produce a bounded           Hypothesis-to-test-t
  value                 2. Scope, roles, test data, and         proof-of-value charter      o-evidence decision
                        execution. 3. Evidence, blockers, and   and evidence-based          map.
                        a decision readout.                     readout.


  11.                   1. Honest comparisons tied to           Write a decision            Cost/value driver
  Competition           workload criteria. 2. Objections,       memo with                   map using clearly
  and business          coexistence, and alternatives. 3.       alternatives and a          hypothetical inputs.
  value                 Cost/value models with stated inputs    sensitivity
                        and limits.                             calculation.


  12. Field             1. Prioritize opportunities and         Prioritize a fictional      Account decision
  execution and         coordinate the account team. 2. Write   week and produce an         loop with owners,
  capstone              useful follow-ups, escalation notes,    escalation/handoff          unresolved risks,
  preparation           and handoffs. 3. Synthesize a           with owners and             and next evidence.
                        complete customer engagement and        decision dates.
                        assess its evidence.


Keep optional foundational refreshers accessible without making the learner repeat them. Teach
jargon when it first appears and include a useful glossary with aliases. Do not assume access to
Tahir's other conversations or private employer materials. Connect each lesson to a real
new-in-role moment: preparing for a customer call, understanding an architecture discussion,
shadowing a demo, investigating a technical question, coordinating with a specialist, or writing a
clear follow-up. Scenario feedback should improve work quality, not simulate an interviewer's
score. Include reusable public-safe discovery checklists, explain-back examples, demo preparation
notes, proof-of-value templates, and handoff examples as authored course content, not a separate
feature campaign.

Every lesson must implement this authored teaching sequence:

1. Why it matters: one practical customer task or decision and clear learning outcomes.

2. Understand it: original plain-English explanation that defines necessary concepts and
    distinguishes common confusions.

3. See it: a purposeful diagram, annotated image, sequence, calculation, or worked example;
    state what the visual teaches. All 36 lessons need this teaching element even though only 12
    distinct diagrams are the minimum.








4. Go deeper: accurate technical detail, assumptions, prerequisites, limitations, and
    cloud/version context, expandable without hiding the essential explanation.

5. Say it to a customer: a concise explanation suitable for a specified business or technical
    audience, without unsupported promises.

6. Try it: a decision, calculation, design task, retrieval response, or scoped technical exercise
    with enough information to attempt it.

7. Check and revisit: rationale for the answer, at least two knowledge checks, at least three
    useful cards, note/bookmark access, and reachable sources.

A substantive lesson teaches something the learner can explain or use: it has a developed
example, reasons behind choices, at least one important limitation or misconception, and practical
transfer. A paragraph followed by repeated cards is not a lesson. Do not inflate counts with
repeated prompts, synonyms, generic advice, or diagram decorations. Aim for a manageable main
reading path with optional depth; reading-time estimates are estimates, not promises. Word count
alone is not the editorial quality gate.

Cards should test one clear concept and include a useful answer, explanation, lesson/concept
links, and source references where factual. Questions require stable option IDs, correct answer
IDs, explanations for correct and incorrect choices, and concept mappings. Persist submitted
attempts with the question/content version so later edits do not rewrite past evidence. Objective
scores identify what was assessed. Answer reveal, note-taking, scrolling, and clicking Complete do
not establish mastery.


6. Fictional customer and capstone
Use a coherent original fictional company, Cinderline Components, across multiple modules,
with a few contrasting scenarios to avoid teaching only one architecture. Label the company,
conversations, datasets, metrics, and commercial numbers as fictional or hypothetical wherever
they could be mistaken for real evidence.

Suggested authored starting facts: a manufacturer with three plants, an ERP on SQL Server,
quality CSV exports, separate sensor events, inconsistent daily reporting, a small data team, and
an exploratory maintenance-knowledge assistant. Its initial brief is incomplete. For teaching
examples choose AWS as the primary cloud, explicitly as an educational choice; do not imply it
is Tahir's assigned cloud or a real customer's environment. Explain Azure/GCP differences only
after checking the corresponding primary documentation.

Author staged stakeholder disclosures, not a perfect requirement sheet. Include questions about
freshness, identity, data sensitivity, network access, operational ownership, budget, and what
would change the buying decision. A static "ask/reveal this stakeholder response" teaching pattern
is acceptable if clearly authored, not an AI chat. Several defensible designs should remain
possible.

Use synthetic input tables/files and fully explain expected output. Sample budgets, latency goals,
volumes, engineering capacity, and projected savings must be explicitly hypothetical. A proposed
target is not an observed result. Do not imply guaranteed cost, performance, savings, compliance,
or product availability.

The capstone requires:

-   A discovery plan, stakeholders, missing information, and clarified assumptions.








-     Current-state and proposed architecture, at least one meaningful alternative, cloud context,
      trust boundaries, operational ownership, and a phased migration/rollback plan.

-     A concise customer demo narrative and an honest fallback if the demonstration fails.

-     A proof-of-value charter with baseline, data/test scope, roles, acceptance thresholds, and a
      decision readout template.

-     A transparent cost/value argument using labeled hypothetical inputs, sensitivity, and
      exclusions.

-     An objection response and a next-step email/handoff with owners and open risks.

-     A complete model submission with reasoning, not just an outline, and an educational rubric
      covering discovery, technical correctness, tradeoffs, communication, measurable evidence,
      and uncertainty. Define what weak, partial, and strong performance looks like for each
      dimension. Self-assessment remains labeled as such.

No real Databricks workspace is required. Included code examples are inspectable/copyable
instructional material, not an in-app arbitrary runner. Label examples as illustrative unless actually
executed. A deterministic local calculation test is distinct from a real Databricks execution.
Optional workspace lab instructions must specify prerequisites, permissions, applicable
cloud/runtime, possible costs, cleanup, and an accurate execution status. Never show "lab passed"
because the learner clicked a button.


7. Sources, claim honesty, and editorial review
Re-read primary sources during authoring. The following are starting references inspected by
guidance on 2026-09-19, not a complete bibliography or proof of every future lesson claim.
Follow through to specific feature, configuration, limitation, and cloud pages before teaching
detailed behavior. A search snippet or a reachable landing page is insufficient.

    Reference                                                 Scope and use


    Databricks go-to-market careers                           Public customer-outcome/teamwork framing; not an
    https://www.databricks.com/company/careers/go-to-ma       internal L4 rubric.
    rket


    Databricks training and certification                     Breadth of public learning areas; does not endorse
    https://www.databricks.com/learn/training/home            this syllabus or confer a credential.


    Well-architected introduction, AWS                        Architecture source gateway and principles.
    https://docs.databricks.com/aws/en/lakehouse-architect
    ure/


    Well-architected framework, AWS                           Architecture tradeoffs; verify relevant detailed
    https://docs.databricks.com/aws/en/lakehouse-architect    sections.
    ure/well-architected/


    High-level architecture, AWS                              Account/workspace concepts and classic/serverless
    https://docs.databricks.com/aws/en/getting-started/hig    boundaries.
    h-level-architecture









  Reference                                                   Scope and use


  Getting started tutorials, AWS                              Technical exercise references; not execution
  https://docs.databricks.com/aws/en/getting-started/         evidence.


  Lakeflow Connect, AWS                                       Ingestion overview; connector-specific support
  https://docs.databricks.com/aws/en/ingestion/overview       requires its own source.


  Spark Declarative Pipelines, AWS documentation              Current pipeline concepts and terminology at
  https://docs.databricks.com/aws/en/ldp/                     inspection time.


  Lakeflow Jobs, AWS                                          Workflow concepts; reverify limits instead of copying
  https://docs.databricks.com/aws/en/jobs/                    remembered values.


  Data warehousing on Databricks, AWS                         SQL/BI interfaces and links to performance evidence.
  https://docs.databricks.com/aws/en/sql/


  Optimization recommendations, AWS                           Starting point for performance lessons; detailed
  https://docs.databricks.com/aws/en/optimizations/           features have prerequisites and caveats.


  Unity Catalog, AWS                                          Governance concepts; do not infer that every feature
  https://docs.databricks.com/aws/en/data-governance/u        applies to every object, compute type, or cloud.
  nity-catalog/


  Machine learning, AWS                                       ML lifecycle source gateway.
  https://docs.databricks.com/aws/en/machine-learning/


  Build agents, AWS                                           Agent lifecycle, retrieval, serving, and evaluation
  https://docs.databricks.com/aws/en/agents                   source gateway. The older /generative-ai/guide/
                                                              URL redirected here during inspection.


  Databricks pricing                                          Verify any real pricing inputs, date, workload,
  https://www.databricks.com/product/pricing                  edition, cloud, region, and excluded costs.
                                                              Hypothetical calculations must remain labeled.


  MDN IndexedDB                                               Local structured storage and API behavior.
  https://developer.mozilla.org/en-US/docs/Web/API/Index
  edDB_API


  MDN storage quotas and eviction                             Origin-scoped storage, quotas, and data-loss
  https://developer.mozilla.org/en-US/docs/Web/API/Stora      limitations.
  ge_API/Storage_quotas_and_eviction_criteria


  Vite getting started                                        Verify toolchain requirements, production build, and
  https://vite.dev/guide/ and static deployment               preview commands.
  https://vite.dev/guide/static-deploy.html


  GitHub Pages overview                                       A possible future static host, not an approved
  https://docs.github.com/en/pages/getting-started-with-      deployment or an assurance of private access.
  github-pages/what-is-github-pages









For each material factual claim, record a stable claim/source link with URL, title, publisher, source
type, section or claim description, applicable product/cloud/runtime context, access date, review
date, and any availability/preview/uncertainty caveat. Connect source records to the lesson
sections, cards, questions, or diagrams they support. Do not mark an entire course "official"
because some sources are official.

Keep official documented product facts, general professional advice, fictional examples,
and personal notes visibly distinguishable without overwhelming the reader. Detailed
professional recommendations may be original educational guidance but must not masquerade as
Databricks policy. Use original prose and diagrams. Do not reproduce proprietary training or large
copied passages. Record media permission/attribution; a publicly viewable screenshot is not
automatically reusable. Schematics must be labeled schematics, never presented as captured
product UI.

For vendor comparisons, first define the workload and decision criteria, then check each vendor's
own current primary documentation. Include credible coexistence/retain-current-state options.
Avoid blanket superiority claims and manufactured benchmarks. Do not publish a competitive
claim from memory.

Review every lesson and each diagram for instructional value, correctness, readable labels, and
misleading simplifications. Produce an editorial coverage matrix with actual findings and
corrections. Automated schemas prove structure, not truth. Label a builder self-review as such; do
not claim independent or expert review unless a separate reviewer actually performed it.


8. Stable content and versioning contract
Every course package must declare course/module/lesson IDs and relationships, ordered catalog
metadata, objectives, prerequisite links, summaries, tags, glossary/aliases, content/schema
version, authored sections, asset references, assessments/cards/scenarios/rubrics, source/claim
register, review dates, and change notes.

Make IDs global or explicitly course-namespaced and stable through renames/reordering. Store
personal state against IDs, not an array index, URL slug, title, or file path. Use stable section IDs
for resume and note links. Unknown/removed content references must remain recoverable, with
an explanation and safe fallback navigation; do not delete associated notes or silently attach them
to another lesson.

A material card-answer or assessed-concept change must preserve old review/attempt history and
flag revised learning material for review. Cosmetic spelling/title changes should not reset learning.
Record the content revision reviewed/answered. Explain the distinction in the authoring guide and
test both cases. Never retroactively change an old score to match a new answer key.

The validator must fail on missing required metadata/teaching sections, duplicate IDs, invalid
prerequisite relationships, broken internal or concept references, missing assets/text alternatives,
malformed answer sets, invalid correct option IDs, missing distractor rationales, unresolved source
IDs, unsafe paths/URL schemes, and missing/placeholder production material. Counts must be
checked by module and lesson, not just global totals. Use explicit negative fixtures so the gate
demonstrably rejects broken content. Do not reject a legitimate explanatory example merely
because it quotes a placeholder term; validate published structure and unresolved authoring
markers deliberately.

External URL availability and source freshness belong in a separate report with date and status. A
transient network failure is not automatically a course-rendering defect, and HTTP 200 is not a







truth check. Surface important unresolved source gaps honestly; do not mark unverifiable
technical assertions as reviewed.


9. Learning evidence, review schedule, and study state
Keep separate records for explicit section/lesson completion, objective quiz attempts and concept
evidence, scheduled card reviews, extra practice, and scenario/capstone self-assessments.
Summaries may say "2 questions answered correctly," "review these missed concepts," or
"scenario not attempted." Do not aggregate these into fabricated mastery, activity, streaks,
credentials, or readiness.

Implement one documented, deterministic, modest spaced-review algorithm. Use this SpicyBrain
simple schedule v1 unless an existing tested scheduler already satisfies the contract and is
preserved with an explicit decision:

-   Inject a clock; store UTC timestamps and algorithm/content version on review events. Define
    one interval day as 24 hours. Local display dates do not alter stored instants.

-   Store intervalDays, initially zero. Again: reset interval to zero, due in 10 minutes. Hard:
    interval min(365, max(1, ceil(previousInterval * 1.2))) days. Good: interval 3 days if previous
    is zero, otherwise min(365, ceil(previousInterval * 2)). Easy: interval 7 days if previous is
    zero, otherwise min(365, ceil(previousInterval * 3)). Hard/Good/Easy due time is review time
    plus the resulting interval. The shared cap is intentional; document it.

-   This is a transparent product heuristic, not a medical claim or an implementation of a named
    validated scheduling algorithm. Explain it briefly to the learner and fully in developer
    documentation.

-   Unseen cards are "new," not fabricated overdue work. Enroll/introduce cards from studied
    lessons or explicit learner selection. Give new-card introduction a small separate allowance.
    Scheduled due cards are those with dueAt <= now.

-   Order scheduled due cards by due timestamp, then stable card ID. Default session limit: 10
    cards, adjustable within a modest range. Capping a session must not erase, mark reviewed, or
    reschedule the remaining queue. Interrupted sessions preserve committed reviews.

-   Rating is unavailable until answer reveal. Commit one immutable event and the schedule
    update atomically; double taps/reloads must not create duplicate review events. Preserve the
    distinction between Again/Hard/Good/Easy in actual due dates.

-   "Extra practice" may reveal and revisit cards but must not mutate scheduled due dates/history.
    Label that behavior. Revised-card review flags preserve historical evidence and require an
    actual review of the new revision to clear.

Use IndexedDB (a thin supported wrapper is acceptable) for notes, drafts, completion, attempts,
review events/state, bookmarks, and settings. Namespace the database specifically for
SpicyBrain. Handle blocked upgrades, denied access, quota/write failures, and reloads visibly. Do
not silently lose a note because an autosave raced navigation. Preserve unsaved drafts in memory
and offer a usable manual copy/download recovery when storage is unavailable. "Saved in this
browser" is different from "export downloaded."

Disclose at first meaningful save and in Settings: study data stays in this browser and site
origin; there is no automatic cross-device sync; clearing/evicting browser storage can
lose it; export/import is the manual backup/transfer path. IndexedDB is not a secure vault.









Do not require personal data to study the course. No notes, response drafts, searches, or notebook
exports go to GitHub, analytics, AI, or a server by default.

Versioned export/import must include all personal study records, stable IDs, original timestamps,
content versions, review events, settings, and a schema version. Validate the whole import before
writing; reject malformed, unsupported-future, oversized, or invalid records without changing
existing state. Do not execute imported text/markup. Preview record counts, conflicts, and
unknown content references before committing.

-   Merge default: deduplicate events by immutable event ID; preserve both conflicting note
    texts rather than silently discarding one; use a documented deterministic policy for mutable
    state/settings; retain unknown content references for recovery. Repeat-import must be
    idempotent for unchanged records.

-   Replace: clearly show what will be replaced, offer an export first, and require explicit
    confirmation. Use an atomic transaction or equivalent rollback so a failed import never leaves
    half-replaced data. Protect Reset similarly.

-   Test at least one real storage/export schema migration using a synthetic older-schema fixture.
    Label it as a migration test fixture, not evidence that an earlier production release existed.
    Preserve text, IDs, timestamps, and review history.


10. Repository CI and deployment preparation
Provide reproducible commands and CI gates for installation, type checking/linting, content
validation, unit/integration tests, production build, real browser acceptance, and the content-only
extension test. Suggested script names: validate:content, typecheck, lint, test, build, test:e2e,
test:content-extension, and check. Implement and document the actual commands; a named but
missing command is a defect. Put external source/link checks in their own report command.

Run CI on the implementation PR with minimum necessary permissions and no deployment
credentials. Treat repository files, PRs, CI logs, screenshots, and uploaded build/test artifacts as
potentially public. Use only synthetic learner data and public-safe evidence; do not claim artifacts
are private because they require a GitHub login to download. No deploy-on-push, public preview
links, Pages enablement, public tunnels, or site publication under this prompt. No analytics or
remote learner-state services.

Initial acceptance environment: production build served locally, using a loopback preview where
supported by the execution environment, plus real browser evidence and a reproducible static
build. If the available browser cannot reach the local preview, report that concrete capability gap
and use another permitted local browser/test runtime; do not make the site public to get a
screenshot.

Prepare docs/DEPLOYMENT.md with exact build/output/base-path instructions and a release checklist.
Recommend a dedicated origin for eventual hosting; browser storage is scoped to origin, not
repository path. A separate database name prevents accidental collisions but is not a security
boundary against other apps on the same origin. Explain that moving to a new domain/origin
requires export/import.

Hosting remains unselected until its access model is verified. For any later hosted release,
document audience, authentication/access enforcement, treatment of static assets and preview
URLs, costs if any, deployment SHA, rollback, and signed-in/signed-out checks. A private
repository does not make a website private; a hard-to-guess URL is not authentication. If public








hosting is proposed, first deliver the complete reviewed artifact and then ask Tahir to approve that
concrete exposure. No live production claim until a deployed build is actually authorized and
tested.


11. Acceptance journey and required tests
Test the production build, not only the development server. Fix real defects within this milestone
and rerun affected gates. A passing workflow, code inspection, screenshots alone, or a builder
assertion is insufficient.

Use synthetic personal data and a controllable clock. At minimum, verify desktop Chromium at
1280px or wider and a real browser mobile viewport around 390px; check 320px/200% text zoom
for reflow. Exercise keyboard-only input, light/dark themes, reduced motion, and meaningful touch
behavior. Run a WebKit mobile-profile smoke if supported; call it emulation, not a physical
iPhone/Safari test. Record browser/runtime/version and any untested device limitation.

  Gate                            Journey and pass evidence


  A. First visit and              Fresh storage shows zero invented activity. Catalog includes exactly the
  complete catalog                intended 12 modules/36 complete lessons, meets the other minimums, and
                                  has no "coming soon" production content. All lesson/scenario/capstone/source
                                  links resolve.


  B. Learn and resume             Start a lesson, navigate to a later stable section, expand technical depth,
                                  open/zoom/reset a teaching diagram, use its text equivalent, enter/exit focus
                                  mode, save a note/bookmark, refresh, leave/return, and resume the saved
                                  lesson/section. Back/forward and a directly opened lesson URL work.
                                  Completion changes only through an explicit learner action.


  C. Knowledge checks             Answer a question incorrectly, see the correct rationale and explanations of
                                  distractors, retry correctly, and inspect retained separate attempts. Test
                                  option reordering using stable IDs, unanswered submission, double submit,
                                  scoring totals, and correct content-version association. No "mastered" claim
                                  follows a click.


  D. Review                       Prove reveal-before-rating and exact Again/Hard/Good/Easy calculations from
                                  the injected clock. Check just-before/at/after due boundaries, UTC/local display
                                  and daylight-saving edges, no-new/no-due/overdue states, interrupted
                                  sessions, queue limits, double taps, and extra practice that leaves the
                                  schedule unchanged. Test a material revision and a cosmetic edit.


  E. Practice and                 Attempt a scenario, persist a draft, reveal its model response, record a labeled
  capstone                        rubric self-assessment, and reopen it. Complete the capstone journey through
                                  all required deliverables and its model submission. No fake code execution or
                                  automatic free-response grade.


  F. Search and                   Search a title, an acronym/alias, lesson body text, and a unique synthetic note
  notebook                        phrase. Results are correctly labeled and open the right course/section/note.
                                  Edit a note, mark an unresolved question, and verify autosave and immediate
                                  navigation do not drop the final edit.









  Gate                            Journey and pass evidence


  G. Persistence and              Verify browser reload/reopen, study-state restoration, export -> clean-context
  transfer                        import round trip, duplicate merge, conflicting-note preservation, replace
                                  preview/cancel/confirm, invalid/future-version rejection, unknown lesson
                                  references, migration, and rollback on an injected failure. Compare actual
                                  records/IDs/timestamps, not just a success toast.


  H. Failure and privacy          Inject unavailable storage, quota/write failure, blocked upgrade, bad
                                  route/missing content, failed asset fetch, and malformed import. Show
                                  recoverable failure states with no false save. Search a unique synthetic note
                                  marker in production files and captured network payloads: it must be absent.
                                  Personal text must not enter URLs, logs, remote search requests, analytics, or
                                  CI artifacts except explicitly synthetic test fixtures.


  I. Content integrity and        Validate every production item, required distribution, source/concept
  editorial quality               mappings, assets, accessible alternatives, correct answers, and absence of
                                  filler. Demonstrate validator failures using intentionally broken fixtures.
                                  Inspect every authored diagram and review all lessons for meaningful
                                  explanations/examples, misconceptions, and source support; document the
                                  actual review scope and findings.


  J. Content-only second          In an isolated test copy/fixture, add a complete small unrelated course such as
  course                          "Exposure and composition in photography" using only the documented
                                  content directories. Without modifying app
                                  routes/components/search/review/storage logic, it appears in Courses, renders
                                  lessons/assets/checks/scenarios, is searchable, supports notes/progress, and
                                  contributes cards to Review. The catalog renderer must not impose the
                                  Databricks 12-module contract on unrelated courses.


  K. Stable identity and          Save notes, completion, quiz attempts, and card history, then rename/reorder
  extension cleanup               test lessons and modules without changing IDs. State and source links survive.
                                  Reorder filenames too. Remove production test-course content and verify the
                                  release build excludes it; keep only isolated non-production fixtures and
                                  reproducible tests.


  L. Visual and                   Real desktop/mobile screenshots and interaction evidence cover Start,
  interaction acceptance          catalog, reader/diagram, practice, review, search/notebook, and import
                                  preview. Check readable typography, long content/notes, visible focus, touch
                                  targets, focus return, theme contrast, reduced motion, and no uncontrolled
                                  page overflow. A beautiful screenshot does not substitute for the behavior
                                  tests above.


For the content-only extension gate, produce the actual diff/file manifest showing changes
confined to content inputs (generated outputs may regenerate normally) and the
commands/browser assertions used. This is a required release gate, not a theoretical architecture
claim.

For source accuracy, verify product facts against the specific current primary pages, including
feature availability and cloud/runtime boundaries. Label anything you could not verify; do not
silently replace missing evidence with confident prose. No requirement to execute paid/cloud labs;
unexecuted optional labs must remain explicitly unexecuted.








12. PR, handoff, and stopping condition
Work in one bounded implementation branch and one PR for this initial milestone; multiple
cohesive commits are appropriate. A draft PR may hold work in progress, but it must not be
presented as completed until the contract passes. Do not fragment the agreed first course into
future milestones. If the context window fills, checkpoint accurate progress and remaining gates,
then continue the same milestone. Do not promise perfect first-draft output or unattended
background completion.

Before the ready-for-review handoff, record and check the actual PR head SHA. Report CI runs tied
to that exact head; do not attribute an older green run to newer code. Investigate consequential
failures and correct them. Do not mark skipped/unavailable browser tests as passed. Preserve
useful partial work and report a precise external blocker when it genuinely prevents a gate.

The PR description and final handoff must include:

1. Exact repository URL and visibility, starting SHA, branch, final head SHA, PR URL, and any setup
    or permission limitation.

2. Concrete delivered behavior and the complete content-count table, including per-module
    coverage and the capstone.

3. Architecture/content authoring decisions, source review date, noteworthy cloud/availability
    caveats, and the inspected design snapshot provenance.

4. Commands run, results, workflow URLs/run IDs/head SHAs, and failures/skips with reasons.

5. Real browser evidence with viewport/browser/date and the tested build SHA. Separate code
    observations, deterministic test results, real browser results, real Databricks
    executions, and builder claims. If there were no cloud executions, say so.

6. Export/import/migration/privacy evidence and clear browser-local/no-sync/data-loss limitations.

7. The reproduced content-only second-course result and concise tested instructions for adding a
    future teaching package.

8. Remaining defects or access blockers, and an honest deployment status: locally verified/ready
    for review is not a live production release.

Do not call the result independently accepted until the guidance project actually checks it. Do not
merge or publish under this prompt. Stop when the complete implementation/course passes the
available required gates and the PR is ready for independent review, or when a concrete external
blocker prevents completion and has been accurately reported with preserved work. Fix
demonstrated acceptance defects within this same milestone when returned by the reviewer.

After the agreed release is accepted, stop feature expansion. The normal next change is an
authorized content package, better explanations/visuals/practice, a factual correction, a genuine
bug fix, or necessary dependency/security maintenance. Uploading material to a ChatGPT project
does not automatically publish it to SpicyBrain. Future publishing should be a reviewed
content-only PR wherever the learning engine already supports it.

Build the learning engine once. Then make the brain smarter.
