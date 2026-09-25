import { test } from "node:test";
import assert from "node:assert/strict";
import {
  cp,
  mkdir,
  mkdtemp,
  readdir,
  readFile,
  rm,
  writeFile,
} from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import {
  buildContent,
  contentBodies,
  courseReferences,
  root,
  stripCourse,
} from "../scripts/content.ts";
import {
  bodyErrors,
  bodyExpectations,
  bodySchema,
  checkBody,
  checkReferences,
  createBodyLoader,
  createReferenceLoader,
  referenceErrors,
  referencesSchema,
} from "../src/bodies.ts";
import type {
  CatalogCourse,
  ContentBody,
  CourseReferences,
  LessonBody,
} from "../src/catalog-types.ts";
import type { TeachingIndexEntry } from "../src/teaching-schema.ts";

// One build from one read of the production content, so the catalog, index
// and bodies compared below were written from the same in-memory courses.
const out = await mkdtemp(join(tmpdir(), "spicybrain-split-out-"));
const full = await buildContent(join(root, "content"), out);
const catalogRaw = await readFile(
  join(out, "src/generated/catalog.json"),
  "utf8",
);
const catalog = JSON.parse(catalogRaw) as CatalogCourse[];
const indexRaw = await readFile(
  join(out, "src/generated/teaching-index.json"),
  "utf8",
);
const index = JSON.parse(indexRaw) as TeachingIndexEntry[];
const bodiesDirectory = join(out, "public/teaching/bodies");
const readBody = async (id: string) =>
  bodySchema.parse(
    JSON.parse(await readFile(join(bodiesDirectory, `${id}.json`), "utf8")),
  );
const referencesDirectory = join(out, "public/teaching/references");
const readReferences = async (courseId: string) =>
  referencesSchema.parse(
    JSON.parse(
      await readFile(join(referencesDirectory, `${courseId}.json`), "utf8"),
    ),
  ) as CourseReferences;
test.after(() => rm(out, { recursive: true, force: true }));

test("the initial catalog carries identities and mappings, never section markdown or card/question text", () => {
  assert.deepEqual(catalog, JSON.parse(JSON.stringify(full.map(stripCourse))));
  for (const course of catalog) {
    // Sources, claims and glossary concepts are identities only: their text
    // is the reference tier.
    for (const item of [
      ...course.sources,
      ...course.claims,
      ...course.concepts,
    ])
      assert.deepEqual(Object.keys(item), ["id"]);
    for (const lesson of course.modules.flatMap((m) => m.lessons)) {
      for (const section of lesson.sections)
        for (const key of ["markdown", "claimIds", "conceptIds"])
          assert.equal(key in section, false, `${section.id}.${key}`);
      for (const card of lesson.cards)
        assert.deepEqual(Object.keys(card).sort(), [
          "id",
          "lessonId",
          "revision",
          "sectionId",
        ]);
      for (const question of lesson.questions)
        assert.deepEqual(Object.keys(question).sort(), [
          "conceptIds",
          "id",
          "revision",
        ]);
    }
    for (const scenario of course.scenarios)
      for (const key of [
        "context",
        "task",
        "model",
        "reasoning",
        "disclosures",
        "requirements",
        "claimIds",
      ])
        assert.equal(key in scenario, false, `${scenario.id}.${key}`);
    // A rubric keeps its dimension ids and names (saved self-assessments are
    // keyed by the ids); its level descriptions are in the body.
    for (const scenario of course.scenarios)
      for (const dimension of scenario.rubric)
        assert.deepEqual(Object.keys(dimension).sort(), ["criterion", "id"]);
    for (const item of [
      ...(course.labs ?? []),
      ...(course.guides ?? []),
      ...(course.cases ?? []),
    ])
      assert.equal("body" in item, false, item.id);
  }
  for (const entry of index)
    for (const card of entry.extensionCards)
      assert.deepEqual(Object.keys(card).sort(), [
        "beatId",
        "id",
        "lessonId",
        "revision",
        "sectionId",
      ]);
  for (const entry of index) {
    assert.equal("outcomes" in entry, false);
    assert.equal("startingAssumptions" in entry, false);
  }
  // The serialized bytes, not only the shape: authored prose that lives only
  // in a body must be absent. (A card answer may legitimately repeat a
  // glossary definition, which stays inline, so those are not sampled.)
  const lesson = full[0].modules[0].lessons[0],
    scenario = full[0].scenarios[0];
  for (const text of [
    lesson.sections[0].markdown,
    lesson.questions[0].options[0].rationale,
    lesson.cards[0].explanation,
    scenario.context,
    scenario.model,
    scenario.rubric[0].strong,
    scenario.requirements[0],
    full[0].sources[0].caveat,
    full[0].claims[0].description,
    full[0].concepts[0].definition,
  ])
    assert.equal(catalogRaw.includes(JSON.stringify(text).slice(1, -1)), false);
  assert.ok(index[0].extensionCards[0]);
  assert.equal(indexRaw.includes('"prompt"'), false);
  assert.equal(indexRaw.includes('"answer"'), false);
  assert.equal(indexRaw.includes('"whyItMatters"'), false);
  assert.equal(catalog.length, full.length);
});

test("every lesson, scenario, lab, guide and case body is emitted, validates, and reconstructs the full content", async () => {
  const expectations = bodyExpectations(catalog);
  const files = new Set(await readdir(bodiesDirectory));
  assert.ok(expectations.size > 0);
  assert.equal(files.size, expectations.size, "no stray or missing bodies");
  for (const [id, expected] of expectations) {
    assert.ok(files.has(`${id}.json`), id);
    const body = await readBody(id);
    assert.equal(checkBody(body, expected), body);
  }
  for (const course of full) {
    for (const lesson of course.modules.flatMap((m) => m.lessons)) {
      const body = (await readBody(lesson.id)) as LessonBody;
      assert.deepEqual(body.cards, lesson.cards);
      assert.deepEqual(body.questions, lesson.questions);
      assert.deepEqual(
        body.sections,
        Object.fromEntries(lesson.sections.map((s) => [s.id, s.markdown])),
      );
      assert.deepEqual(
        body.sectionClaims,
        Object.fromEntries(lesson.sections.map((s) => [s.id, s.claimIds])),
      );
      assert.equal(body.contentVersion, lesson.contentVersion);
    }
    for (const scenario of course.scenarios) {
      const body = await readBody(scenario.id);
      assert.equal(body.kind, "scenario");
      if (body.kind === "scenario") {
        assert.equal(body.context, scenario.context);
        assert.equal(body.task, scenario.task);
        assert.equal(body.model, scenario.model);
        assert.equal(body.reasoning, scenario.reasoning);
        assert.deepEqual(body.disclosures, scenario.disclosures);
        assert.deepEqual(body.requirements, scenario.requirements);
        assert.deepEqual(body.rubric, scenario.rubric);
        assert.deepEqual(body.claimIds, scenario.claimIds);
      }
    }
    // The reference tier reconstructs the course's full records in order and
    // matches the catalog's identities.
    const references = await readReferences(course.id);
    assert.deepEqual(references, courseReferences(course));
    assert.deepEqual(references.sources, course.sources);
    assert.deepEqual(references.claims, course.claims);
    assert.deepEqual(references.concepts, course.concepts);
    assert.equal(
      checkReferences(
        references,
        catalog.find((c) => c.id === course.id)!,
      ),
      references,
    );
    assert.deepEqual(
      contentBodies(course).map((b) => `${b.kind}:${b.id}`),
      [
        ...course.modules.flatMap((m) =>
          m.lessons.map((l) => `lesson:${l.id}`),
        ),
        ...course.scenarios.map((s) => `scenario:${s.id}`),
        ...(course.labs ?? []).map((l) => `lab:${l.id}`),
        ...(course.guides ?? []).map((g) => `guide:${g.id}`),
        ...(course.cases ?? []).map((c) => `case:${c.id}`),
      ],
    );
  }
  // Extension cards keep their text inside the module JSON; the index holds
  // matching identities.
  for (const entry of index) {
    const module = JSON.parse(
      await readFile(join(out, "public", entry.url), "utf8"),
    ) as { extensionCards: { id: string; revision: string }[] };
    assert.deepEqual(
      module.extensionCards.map((c) => [c.id, c.revision]),
      entry.extensionCards.map((c) => [c.id, c.revision]),
    );
  }
});

test("labs, guides and cases publish stripped catalog entries and kind-specific body files", async () => {
  const temp = await mkdtemp(join(tmpdir(), "spicybrain-split-"));
  try {
    await cp("tests/fixtures/photography/content", join(temp, "content"), {
      recursive: true,
    });
    const courseDir = join(temp, "content/courses/photo"),
      coursePath = join(courseDir, "course.json");
    const course = JSON.parse(await readFile(coursePath, "utf8"));
    const moduleId = course.modules[0].id,
      lessonId = "photo-m01-l01",
      conceptId = course.concepts[0].id;
    course.sources = [
      ...course.sources,
      {
        id: "photo-source-synthetic",
        title: "Synthetic photography reference",
        url: "https://example.com/photography-reference",
        publisher: "Synthetic fixture",
        type: "primary reference",
        context: "A test-only source record.",
        accessDate: "2026-09-01",
        reviewDate: "2026-09-01",
        caveat: "Not a real publication.",
      },
    ];
    course.labs = [
      {
        id: "photo-lab-metering",
        title: "Meter a backlit scene",
        summary: "A tabletop metering exercise.",
        outcome: "Choose an exposure and defend it.",
        executionClass: "tabletop",
        moduleIds: [moduleId],
        conceptIds: [conceptId],
        environment: "Any camera with manual mode.",
        evidence: "Your own written reasoning.",
        bodyFile: "labs/metering.md",
      },
    ];
    course.guides = [
      {
        id: "photo-guide-motion",
        title: "Freeze motion on demand",
        question: "How fast is fast enough?",
        summary: "A short decision guide.",
        moduleIds: [moduleId],
        lessonIds: [lessonId],
        bodyFile: "guides/motion.md",
      },
    ];
    course.cases = [
      {
        id: "photo-case-blur",
        title: "The blurred finish line",
        domain: "sports",
        summary: "A synthetic case study.",
        reporter: "Synthetic fixture author",
        sourceIds: ["photo-source-synthetic"],
        moduleIds: [moduleId],
        publishedAt: null,
        reviewedAt: "2026-09-01",
        bodyFile: "cases/blur.md",
      },
    ];
    await writeFile(coursePath, JSON.stringify(course, null, 2));
    for (const [file, text] of [
      ["labs/metering.md", "Meter the shadow side, then the highlight side."],
      [
        "guides/motion.md",
        "<!-- section:action -->\nUse a shutter speed faster than the subject.\n<!-- section:example -->\nA cyclist needs about 1/1000 s.\n<!-- section:template -->\nSubject, speed, distance, decision.\n<!-- section:limits -->\nPanning changes the rule.",
      ],
      ["cases/blur.md", "The finish-line photograph was blurred by motion."],
    ] as const) {
      await mkdir(join(courseDir, file, ".."), { recursive: true });
      await writeFile(join(courseDir, file), text);
    }
    const destination = join(temp, "out");
    const built = await buildContent(join(temp, "content"), destination);
    const photo = built.find((c) => c.id === "photo")!;
    assert.deepEqual(
      contentBodies(photo)
        .filter((b) => b.kind !== "lesson" && b.kind !== "scenario")
        .map((b) => [b.kind, b.id]),
      [
        ["lab", "photo-lab-metering"],
        ["guide", "photo-guide-motion"],
        ["case", "photo-case-blur"],
      ],
    );
    const stripped = (
      JSON.parse(
        await readFile(join(destination, "src/generated/catalog.json"), "utf8"),
      ) as CatalogCourse[]
    ).find((c) => c.id === "photo")!;
    for (const item of [
      ...stripped.labs!,
      ...stripped.guides!,
      ...stripped.cases!,
    ])
      assert.equal("body" in item, false, item.id);
    assert.equal(stripped.labs![0].executionClass, "tabletop");
    assert.equal(stripped.guides![0].question, "How fast is fast enough?");
    const expectations = bodyExpectations([stripped]);
    for (const [id, kind, check] of [
      [
        "photo-lab-metering",
        "lab",
        (b: ContentBody) =>
          b.kind === "lab" && b.body.startsWith("Meter the shadow side"),
      ],
      [
        "photo-guide-motion",
        "guide",
        (b: ContentBody) =>
          b.kind === "guide" && b.body.limits === "Panning changes the rule.",
      ],
      [
        "photo-case-blur",
        "case",
        (b: ContentBody) =>
          b.kind === "case" && b.body.startsWith("The finish-line"),
      ],
    ] as const) {
      const body = bodySchema.parse(
        JSON.parse(
          await readFile(
            join(destination, "public/teaching/bodies", `${id}.json`),
            "utf8",
          ),
        ),
      );
      assert.equal(body.kind, kind);
      assert.ok(check(body), id);
      assert.equal(checkBody(body, expectations.get(id)!), body);
    }
    const written = await readdir(join(destination, "public/teaching/bodies"));
    assert.equal(written.length, expectations.size);
  } finally {
    await rm(temp, { recursive: true, force: true });
  }
});

test("the body loader rejects a wrong id, kind, contentVersion, drifted revisions and malformed JSON, then retries after a failure", async () => {
  const expectations = bodyExpectations(catalog);
  const lesson = catalog[0].modules[0].lessons[0],
    scenario = catalog[0].scenarios[0];
  const good = (await readBody(lesson.id)) as LessonBody;
  const scenarioBody = await readBody(scenario.id);
  let calls = 0,
    responses: (() => Response | Promise<Response>)[] = [];
  const json =
    (value: unknown, status = 200) =>
    () =>
      new Response(JSON.stringify(value), {
        status,
        headers: { "content-type": "application/json" },
      });
  const loader = createBodyLoader({
    url: (id) => `/teaching/bodies/${id}.json`,
    expected: (id) => expectations.get(id),
    fetch: async () => {
      calls++;
      const next = responses.shift();
      if (!next) throw new TypeError("Failed to fetch");
      return next();
    },
  });
  const rejects = async (
    id: string,
    response: () => Response | Promise<Response>,
    message: RegExp,
  ) => {
    responses = [response];
    const before = calls;
    await assert.rejects(loader.load(id), message);
    assert.equal(calls, before + 1);
    assert.equal(loader.has(id), false, "a failed load is evicted");
  };
  const mismatch = /changed or are incomplete/;
  await rejects(lesson.id, json({ ...good, id: "other-lesson" }), mismatch);
  await rejects(
    lesson.id,
    json({ ...good, contentVersion: `${good.contentVersion}-next` }),
    mismatch,
  );
  await rejects(
    lesson.id,
    json({
      ...good,
      cards: good.cards.map((c, i) =>
        i ? c : { ...c, revision: `${c.revision}-drift` },
      ),
    }),
    mismatch,
  );
  await rejects(
    lesson.id,
    json({
      ...good,
      questions: good.questions.map((q, i) =>
        i ? q : { ...q, revision: `${q.revision}-drift` },
      ),
    }),
    mismatch,
  );
  await rejects(
    lesson.id,
    json({ ...good, sections: { ...good.sections, "extra-section": "More." } }),
    mismatch,
  );
  const [firstSection, secondSection] = Object.keys(good.sectionClaims);
  await rejects(
    lesson.id,
    json({
      ...good,
      sectionClaims: {
        ...good.sectionClaims,
        [secondSection]: ["claim-from-another-version"],
      },
    }),
    mismatch,
  );
  await rejects(
    lesson.id,
    json({
      ...good,
      sectionClaims: Object.fromEntries(
        Object.entries(good.sectionClaims).filter(
          ([id]) => id !== firstSection,
        ),
      ),
    }),
    mismatch,
  );
  await rejects(lesson.id, json(scenarioBody), mismatch);
  // A scenario body must carry the catalog's rubric (saved ratings are keyed
  // by its ids) and cite only the course's claims.
  if (scenarioBody.kind !== "scenario") throw Error("scenario body expected");
  await rejects(
    scenario.id,
    json({
      ...scenarioBody,
      rubric: scenarioBody.rubric.map((r, i) =>
        i ? r : { ...r, id: `${r.id}-renamed` },
      ),
    }),
    mismatch,
  );
  await rejects(
    scenario.id,
    json({
      ...scenarioBody,
      rubric: scenarioBody.rubric.map((r, i) =>
        i ? r : { ...r, criterion: `${r.criterion} (other version)` },
      ),
    }),
    mismatch,
  );
  await rejects(
    scenario.id,
    json({ ...scenarioBody, claimIds: ["claim-from-another-version"] }),
    mismatch,
  );
  await rejects(
    lesson.id,
    () => new Response("{not json", { status: 200 }),
    /incomplete or invalid/,
  );
  await rejects(
    lesson.id,
    json({ kind: "lesson", id: lesson.id }),
    /incomplete or invalid/,
  );
  await rejects(
    lesson.id,
    () => new Response("", { status: 503 }),
    /This lesson could not load[\s\S]*Your study data is safe/,
  );
  await rejects(
    lesson.id,
    () => Promise.reject(new TypeError("Failed to fetch")),
    /This lesson could not load[\s\S]*Your study data is safe/,
  );
  await rejects(
    scenario.id,
    () => new Response("", { status: 404 }),
    /This practice item could not load/,
  );
  const before = calls;
  await assert.rejects(loader.load("missing-lesson"), /unavailable/);
  assert.equal(calls, before, "an unknown id is refused without a request");
  // Retry after the failures fetches again, then the cache serves repeats.
  responses = [json(good)];
  const body = await loader.load(lesson.id);
  assert.deepEqual(body, good);
  assert.equal(calls, before + 1);
  assert.equal(loader.has(lesson.id), true);
  assert.equal(await loader.lesson(lesson.id), body);
  assert.equal(calls, before + 1);
  responses = [json(scenarioBody)];
  await assert.rejects(loader.lesson(scenario.id), mismatch);
  responses = [json(scenarioBody)];
  assert.equal((await loader.load(scenario.id)).kind, "scenario");
  assert.throws(
    () =>
      checkBody(
        { kind: "lab", id: "photo-lab", body: "x" },
        { kind: "case", id: "photo-lab" },
      ),
    new RegExp(bodyErrors.mismatch.slice(0, 20)),
  );
});

test("the reference loader refuses another course version, malformed or failed files, evicts failures, then caches one copy", async () => {
  const course = catalog[0];
  const good = await readReferences(course.id);
  assert.equal((await readdir(referencesDirectory)).length, catalog.length);
  let calls = 0,
    responses: (() => Response | Promise<Response>)[] = [];
  const json =
    (value: unknown, status = 200) =>
    () =>
      new Response(JSON.stringify(value), {
        status,
        headers: { "content-type": "application/json" },
      });
  const loader = createReferenceLoader({
    url: (id) => `/teaching/references/${id}.json`,
    course: (id) => catalog.find((c) => c.id === id),
    fetch: async () => {
      calls++;
      const next = responses.shift();
      if (!next) throw new TypeError("Failed to fetch");
      return next();
    },
  });
  const rejects = async (
    response: () => Response | Promise<Response>,
    message: RegExp,
  ) => {
    responses = [response];
    const before = calls;
    await assert.rejects(loader.load(course.id), message);
    assert.equal(calls, before + 1);
    assert.equal(loader.cached(course.id), undefined, "nothing is cached");
  };
  const mismatch = /changed or are incomplete/;
  await rejects(json({ ...good, courseId: "other-course" }), mismatch);
  await rejects(
    json({ ...good, sources: [...good.sources].reverse() }),
    mismatch,
  );
  await rejects(json({ ...good, claims: good.claims.slice(1) }), mismatch);
  await rejects(
    json({
      ...good,
      concepts: [
        ...good.concepts,
        { ...good.concepts[0], id: "extra-concept-from-elsewhere" },
      ],
    }),
    mismatch,
  );
  await rejects(
    () => new Response("{not json", { status: 200 }),
    new RegExp(referenceErrors.invalid.slice(0, 30)),
  );
  await rejects(
    json({ ...good, sources: [{ id: good.sources[0].id }] }),
    new RegExp(referenceErrors.invalid.slice(0, 30)),
  );
  await rejects(
    () => new Response("", { status: 503 }),
    /could not load[\s\S]*Your study data is safe/,
  );
  await rejects(
    () => Promise.reject(new TypeError("Failed to fetch")),
    /could not load[\s\S]*Your study data is safe/,
  );
  const before = calls;
  await assert.rejects(loader.load("missing-course"), /unavailable/);
  assert.equal(calls, before, "an unknown course is refused without a request");
  // Every waiting panel is told once the references arrive, never on failure.
  let notified = 0;
  const unsubscribe = loader.subscribe(() => notified++);
  responses = [() => new Response("", { status: 503 })];
  await assert.rejects(loader.load(course.id));
  assert.equal(notified, 0);
  responses = [json(good)];
  const loaded = await loader.load(course.id);
  assert.equal(notified, 1);
  unsubscribe();
  assert.deepEqual(loaded, good);
  assert.equal(loader.cached(course.id), loaded);
  assert.equal(await loader.load(course.id), loaded);
  assert.equal(calls, before + 2, "one request serves every later view");
  assert.equal(notified, 1, "an unsubscribed panel is not told again");
});
