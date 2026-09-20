import { z } from "zod";

export const idSchema = z.string().regex(/^[a-z][a-z0-9-]{2,100}$/);
const text = z.string().trim().min(1).max(100000);
const ids = z.array(idSchema);
const date = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);
export const legacySectionKinds = [
  "why",
  "understand",
  "see",
  "deeper",
  "customer",
  "try",
  "revisit",
] as const;
export const sectionKinds = [
  ...legacySectionKinds,
  "outcome",
  "prerequisites",
  "mechanism",
  "example",
  "exercise",
  "solution",
  "mistakes",
  "sources",
  "related",
  "reference",
] as const;
export const sourceSchema = z
  .object({
    id: idSchema,
    title: text,
    url: z.url().refine((v) => v.startsWith("https://")),
    publisher: text,
    type: z.enum(["official documentation", "primary reference"]),
    context: text,
    accessDate: date,
    reviewDate: date,
    caveat: text,
  })
  .strict();
export const claimSchema = z
  .object({
    id: idSchema,
    description: text,
    kind: z.enum(["documented", "guidance", "fictional"]),
    sourceIds: ids,
    context: text,
  })
  .strict();
export const sectionSchema = z
  .object({
    id: idSchema,
    kind: z.enum(sectionKinds),
    title: text,
    markdown: text,
    conceptIds: ids,
    claimIds: ids,
    assetIds: ids,
  })
  .strict();
export const questionSchema = z
  .object({
    id: idSchema,
    revision: text,
    prompt: text,
    options: z
      .array(z.object({ id: idSchema, text, rationale: text }).strict())
      .min(2)
      .max(6),
    correctOptionId: idSchema,
    conceptIds: ids.min(1),
    claimIds: ids,
  })
  .strict();
export const cardSchema = z
  .object({
    id: idSchema,
    revision: text,
    prompt: text,
    answer: text,
    explanation: text,
    lessonId: idSchema,
    sectionId: idSchema,
    conceptIds: ids.min(1),
    claimIds: ids,
  })
  .strict();
export const lessonSchema = z
  .object({
    id: idSchema,
    title: text,
    summary: text,
    contentVersion: text,
    estimatedMinutes: z.number().int().min(1).max(120),
    objectives: z.array(text).min(1),
    prerequisiteIds: ids,
    tags: z.array(text),
    teachingFormat: z.literal("flexible").optional(),
    downloadIds: ids.optional(),
    sections: z.array(sectionSchema).min(1),
    questions: z.array(questionSchema).min(2),
    cards: z.array(cardSchema).min(3),
  })
  .strict();
export const rubricSchema = z
  .object({
    id: idSchema,
    criterion: text,
    weak: text,
    partial: text,
    strong: text,
  })
  .strict();
export const scenarioSchema = z
  .object({
    id: idSchema,
    title: text,
    context: text,
    task: text,
    requirements: z.array(text).min(2),
    model: text,
    reasoning: text,
    rubric: z.array(rubricSchema).min(3),
    disclosures: z.array(z.object({ question: text, response: text }).strict()),
    lessonIds: ids.min(1),
    claimIds: ids,
    isCapstone: z.boolean(),
  })
  .strict();
export const assetSchema = z
  .object({
    id: idSchema,
    path: text,
    caption: text,
    alt: text,
    textEquivalent: text,
    provenance: text,
    claimIds: ids,
  })
  .strict();
export const moduleSchema = z
  .object({
    id: idSchema,
    title: text,
    summary: text,
    objectives: z.array(text).min(1),
    prerequisiteIds: ids,
    lessons: z.array(lessonSchema).min(1),
    scenarioId: idSchema,
  })
  .strict();
export const courseSchema = z
  .object({
    schemaVersion: z.literal(1),
    id: idSchema,
    title: text,
    subtitle: text,
    summary: text,
    contentVersion: text,
    objectives: z.array(text).min(1),
    prerequisiteIds: ids,
    tags: z.array(text),
    reviewDate: date,
    changeNotes: z.array(text).min(1),
    refreshers: z.array(z.object({ title: text, markdown: text }).strict()),
    modules: z.array(moduleSchema).min(1),
    sources: z.array(sourceSchema),
    claims: z.array(claimSchema),
    concepts: z.array(
      z
        .object({
          id: idSchema,
          term: text,
          aliases: z.array(text),
          definition: text,
          lessonId: idSchema,
          sectionId: idSchema,
        })
        .strict(),
    ),
    assets: z.array(assetSchema),
    downloads: z
      .array(
        z
          .object({
            id: idSchema,
            title: text,
            description: text,
            path: text,
            mediaType: z.literal("application/zip"),
            sha256: z.string().regex(/^[a-f0-9]{64}$/),
          })
          .strict(),
      )
      .optional(),
    scenarios: z.array(scenarioSchema),
    capstoneId: idSchema.optional(),
    contract: z
      .object({
        modules: z.number().int().positive(),
        lessonsPerModule: z.number().int().positive(),
        cardsPerLesson: z.number().int().min(3),
        checksPerLesson: z.number().int().min(2),
        diagramsPerModule: z.number().int().positive(),
      })
      .strict()
      .optional(),
  })
  .strict();
export type Course = z.infer<typeof courseSchema>;
export type Lesson = z.infer<typeof lessonSchema>;
export type Section = z.infer<typeof sectionSchema>;
export type Card = z.infer<typeof cardSchema>;
export type Question = z.infer<typeof questionSchema>;
export type Scenario = z.infer<typeof scenarioSchema>;
export type Asset = z.infer<typeof assetSchema>;
export type Download = NonNullable<Course["downloads"]>[number];

export function safePath(path: string) {
  return (
    /^[a-zA-Z0-9][a-zA-Z0-9/_ .-]*$/.test(path) &&
    !path.split("/").some((p) => p === ".." || p === ".") &&
    !path.includes("\\") &&
    !path
      .split("/")
      .some(
        (p) =>
          !p ||
          /[ .]$/.test(p) ||
          /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(p),
      )
  );
}
export function validateCourses(input: unknown[]): Course[] {
  const courses = input.map((c) => courseSchema.parse(c));
  const allIds = new Set<string>();
  const navigation = new Set<string>();
  const prereqs = new Map<string, string[]>();
  const catalogLessons = courses.flatMap((c) =>
    c.modules.flatMap((m) => m.lessons),
  );
  const catalogScenarios = courses.flatMap((c) => c.scenarios);
  const fail = (message: string): never => {
    throw new Error(message);
  };
  for (const c of courses) {
    for (const item of [
      c,
      ...c.modules,
      ...c.modules.flatMap((m) => m.lessons),
    ]) {
      navigation.add(item.id);
      prereqs.set(item.id, item.prerequisiteIds);
    }
  }
  for (const c of courses) {
    const lessons = c.modules.flatMap((m) => m.lessons);
    const sections = lessons.flatMap((l) => l.sections);
    const items = [
      c,
      ...c.modules,
      ...lessons,
      ...sections,
      ...lessons.flatMap((l) => [
        ...l.cards,
        ...l.questions,
        ...l.questions.flatMap((q) => q.options),
      ]),
      ...c.scenarios,
      ...c.scenarios.flatMap((s) => s.rubric),
      ...c.concepts,
      ...c.sources,
      ...c.claims,
      ...c.assets,
      ...(c.downloads ?? []),
    ];
    for (const item of items) {
      if (allIds.has(item.id)) fail(`Duplicate ID: ${item.id}`);
      allIds.add(item.id);
    }
    const concepts = new Set(c.concepts.map((x) => x.id)),
      claims = new Set(c.claims.map((x) => x.id)),
      sources = new Set(c.sources.map((x) => x.id)),
      assets = new Set(c.assets.map((x) => x.id));
    const refs = (values: string[], set: Set<string>, label: string) => {
      for (const v of values)
        if (!set.has(v)) fail(`Unresolved ${label}: ${v}`);
    };
    const link = (lessonId: string, sectionId: string) => {
      if (
        !lessons
          .find((l) => l.id === lessonId)
          ?.sections.some((s) => s.id === sectionId)
      )
        fail(`Broken lesson/section reference: ${lessonId}/${sectionId}`);
    };
    for (const cl of c.claims) {
      refs(cl.sourceIds, sources, "source");
      if (cl.kind === "documented" && !cl.sourceIds.length)
        fail(`Documented claim missing source: ${cl.id}`);
    }
    for (const a of c.assets) {
      if (!safePath(a.path) || !a.path.endsWith(".svg"))
        fail(`Unsafe asset path: ${a.path}`);
      refs(a.claimIds, claims, "asset claim");
    }
    for (const d of c.downloads ?? [])
      if (!safePath(d.path) || !d.path.endsWith(".zip"))
        fail(`Unsafe download path: ${d.path}`);
    for (const g of c.concepts) link(g.lessonId, g.sectionId);
    for (const l of lessons) {
      const kinds = new Set(l.sections.map((s) => s.kind));
      if (
        !l.teachingFormat &&
        (l.sections.length !== 7 ||
          legacySectionKinds.some((k) => !kinds.has(k)))
      )
        fail(`Missing required teaching section: ${l.id}`);
      if (
        l.teachingFormat === "flexible" &&
        (!kinds.has("solution") ||
          (!kinds.has("exercise") && !kinds.has("try")))
      )
        fail(
          `Flexible lesson requires a separate exercise and solution: ${l.id}`,
        );
      refs(
        l.downloadIds ?? [],
        new Set((c.downloads ?? []).map((d) => d.id)),
        "download",
      );
      for (const s of l.sections) {
        refs(s.conceptIds, concepts, "concept");
        refs(s.claimIds, claims, "claim");
        refs(s.assetIds, assets, "asset");
      }
      for (const q of l.questions) {
        const options = new Set(q.options.map((o) => o.id));
        if (
          options.size !== q.options.length ||
          !options.has(q.correctOptionId)
        )
          fail(`Malformed answer set: ${q.id}`);
        refs(q.conceptIds, concepts, "question concept");
        refs(q.claimIds, claims, "question claim");
      }
      for (const card of l.cards) {
        link(card.lessonId, card.sectionId);
        refs(card.conceptIds, concepts, "card concept");
        refs(card.claimIds, claims, "card claim");
      }
    }
    for (const s of c.scenarios) {
      refs(s.lessonIds, new Set(lessons.map((l) => l.id)), "scenario lesson");
      refs(s.claimIds, claims, "scenario claim");
    }
    for (const m of c.modules) {
      if (!c.scenarios.some((s) => s.id === m.scenarioId && !s.isCapstone))
        fail(`Missing module scenario: ${m.id}`);
    }
    // A canonical applied scenario may support several instructional modules.
    // Its ID and learner draft stay singular; references must still resolve above.
    if (
      c.capstoneId &&
      !c.scenarios.some((s) => s.id === c.capstoneId && s.isCapstone)
    )
      fail("Missing capstone");
    if (c.contract) {
      const d = c.contract;
      if (c.modules.length < d.modules) fail("Insufficient module count");
      for (const m of c.modules) {
        if (m.lessons.length < d.lessonsPerModule)
          fail(`Insufficient lesson count: ${m.id}`);
        if (
          new Set(
            m.lessons.flatMap((l) => l.sections.flatMap((s) => s.assetIds)),
          ).size < d.diagramsPerModule
        )
          fail(`Missing module diagram: ${m.id}`);
        for (const l of m.lessons)
          if (
            l.cards.length < d.cardsPerLesson ||
            l.questions.length < d.checksPerLesson
          )
            fail(`Insufficient lesson coverage: ${l.id}`);
      }
    }
    const serialized = JSON.stringify(c);
    if (
      /\[AUTHOR_TODO\]|\[REPLACE_ME\]|\[UNRESOLVED_SOURCE\]|coming soon/i.test(
        serialized,
      )
    )
      fail("Unresolved production authoring marker");
    if (
      /(?:javascript|vbscript|data):|<\s*(?:script|iframe|object|embed)\b|onerror\s*=/i.test(
        serialized,
      )
    )
      fail("Unsafe content URL or markup");
    for (const s of sections)
      for (const match of s.markdown.matchAll(/\]\(([^)]+)\)/g)) {
        const url = match[1];
        if (
          !url.startsWith("https://") &&
          !/^#\/(course|lesson|practice)\/[a-z0-9-/]+$/.test(url)
        )
          fail(`Unsafe Markdown link: ${url}`);
        if (url.startsWith("#/")) {
          const parts = url.split("/"),
            id = parts[2];
          if (parts.length > (parts[1] === "lesson" ? 4 : 3))
            fail(`Broken internal link: ${url}`);
          if (
            parts[1] === "lesson" &&
            !catalogLessons.some(
              (l) =>
                l.id === id &&
                (!parts[3] || l.sections.some((s) => s.id === parts[3])),
            )
          )
            fail(`Broken lesson/section reference: ${url}`);
          if (
            parts[1] === "course" &&
            !courses.some((course) => course.id === id)
          )
            fail(`Broken course link: ${url}`);
          if (
            parts[1] === "practice" &&
            !catalogScenarios.some((scenario) => scenario.id === id)
          )
            fail(`Broken practice link: ${url}`);
        }
      }
  }
  const complete = new Set<string>();
  const visit = (id: string, chain = new Set<string>()) => {
    if (chain.has(id)) fail(`Cyclic prerequisite: ${id}`);
    if (complete.has(id)) return;
    const next = new Set(chain).add(id);
    for (const p of prereqs.get(id) ?? []) {
      if (!navigation.has(p)) fail(`Invalid prerequisite: ${p}`);
      visit(p, next);
    }
    complete.add(id);
  };
  for (const id of navigation) visit(id);
  return courses;
}

export const referenceSchema = z
  .object({
    courseId: idSchema,
    lessonId: idSchema.optional(),
    sectionId: idSchema.optional(),
    scenarioId: idSchema.optional(),
    label: text,
  })
  .strict();
export const pathSchema = z
  .object({
    schemaVersion: z.literal(1),
    id: idSchema,
    title: text,
    summary: text,
    outcomes: z.array(text).min(1),
    startingAssumptions: z.array(text).min(1),
    defaultStart: z.boolean().optional(),
    groups: z
      .array(
        z
          .object({
            id: idSchema,
            title: text,
            purpose: text,
            lessonIds: ids.min(1),
          })
          .strict(),
      )
      .min(1),
    prerequisites: z.array(
      z
        .object({
          lessonId: idSchema,
          requiredLessonId: idSchema,
          explanation: text,
        })
        .strict(),
    ),
    optionalBridges: z.array(
      z
        .object({
          lessonId: idSchema,
          beforeLessonIds: ids.min(1),
          explanation: text,
        })
        .strict(),
    ),
    playbooks: z.array(
      z
        .object({
          id: idSchema,
          title: text,
          summary: text,
          targets: z.array(referenceSchema).min(1),
        })
        .strict(),
    ),
  })
  .strict();
export type LearningPath = z.infer<typeof pathSchema>;
export type ContentReference = z.infer<typeof referenceSchema>;
export type Playbook = LearningPath["playbooks"][number];

export function validatePaths(
  input: unknown[],
  courses: Course[],
): LearningPath[] {
  const paths = input.map((value) => pathSchema.parse(value));
  const allIds = new Set<string>();
  const collect = (value: unknown) => {
    if (Array.isArray(value)) for (const item of value) collect(item);
    else if (value && typeof value === "object") {
      const record = value as Record<string, unknown>;
      if (typeof record.id === "string") allIds.add(record.id);
      for (const [key, item] of Object.entries(record))
        if (key !== "id") collect(item);
    }
  };
  collect(courses);
  const lessons = new Map(
    courses.flatMap((c) =>
      c.modules.flatMap((m) => m.lessons.map((l) => [l.id, l] as const)),
    ),
  );
  const graph = new Map<string, Set<string>>(
    courses
      .flatMap((course) => [
        course,
        ...course.modules,
        ...course.modules.flatMap((module) => module.lessons),
      ])
      .map((item) => [item.id, new Set(item.prerequisiteIds)]),
  );
  const fail = (message: string): never => {
    throw new Error(message);
  };
  const requireLesson = (id: string) => {
    if (!lessons.has(id)) fail(`Missing path lesson: ${id}`);
  };
  if (paths.filter((path) => path.defaultStart).length > 1)
    fail("Multiple default-start paths");
  for (const path of paths) {
    for (const item of [path, ...path.groups, ...path.playbooks]) {
      if (allIds.has(item.id)) fail(`Duplicate ID: ${item.id}`);
      allIds.add(item.id);
    }
    const ordered = path.groups.flatMap((group) => group.lessonIds);
    if (new Set(ordered).size !== ordered.length)
      fail(`Duplicate lesson within path: ${path.id}`);
    for (const id of ordered) requireLesson(id);
    const bridges = path.optionalBridges.map((bridge) => bridge.lessonId);
    if (new Set(bridges).size !== bridges.length)
      fail(`Duplicate optional bridge: ${path.id}`);
    if (bridges.some((id) => ordered.includes(id)))
      fail(`Optional bridge is also a required topic: ${path.id}`);
    for (const bridge of path.optionalBridges) {
      requireLesson(bridge.lessonId);
      for (const id of bridge.beforeLessonIds) {
        if (!ordered.includes(id)) fail(`Bridge target outside path: ${id}`);
        graph.get(id)!.add(bridge.lessonId);
      }
    }
    const dependencyKeys = new Set<string>();
    for (const dependency of path.prerequisites) {
      if (
        !ordered.includes(dependency.lessonId) &&
        !bridges.includes(dependency.lessonId)
      )
        fail(`Prerequisite target outside path: ${dependency.lessonId}`);
      requireLesson(dependency.requiredLessonId);
      const key = `${dependency.lessonId}/${dependency.requiredLessonId}`;
      if (dependencyKeys.has(key)) fail(`Duplicate path prerequisite: ${key}`);
      dependencyKeys.add(key);
      graph.get(dependency.lessonId)!.add(dependency.requiredLessonId);
    }
    for (const playbook of path.playbooks)
      for (const target of playbook.targets) {
        const course = courses.find((course) => course.id === target.courseId);
        if (!course)
          throw new Error(`Missing playbook course: ${target.courseId}`);
        if (target.scenarioId && (target.lessonId || target.sectionId))
          fail(`Ambiguous playbook target: ${playbook.id}`);
        if (target.sectionId && !target.lessonId)
          fail(`Section requires playbook lesson: ${playbook.id}`);
        if (
          target.scenarioId &&
          !course.scenarios.some(
            (scenario) => scenario.id === target.scenarioId,
          )
        )
          fail(`Missing playbook scenario: ${target.scenarioId}`);
        if (target.lessonId) {
          const lesson = course.modules
            .flatMap((module) => module.lessons)
            .find((lesson) => lesson.id === target.lessonId);
          if (
            !lesson ||
            (target.sectionId &&
              !lesson.sections.some(
                (section) => section.id === target.sectionId,
              ))
          )
            fail(
              `Missing playbook lesson/section: ${target.lessonId}/${target.sectionId ?? ""}`,
            );
        }
      }
  }
  const complete = new Set<string>();
  const visit = (id: string, chain = new Set<string>()) => {
    if (chain.has(id)) fail(`Cyclic path prerequisite: ${id}`);
    if (complete.has(id)) return;
    const next = new Set(chain).add(id);
    for (const required of graph.get(id) ?? []) visit(required, next);
    complete.add(id);
  };
  for (const id of graph.keys()) visit(id);
  return paths;
}

export const preservationSchema = z
  .object({
    schemaVersion: z.literal(1),
    courseId: idSchema,
    baselineCommit: z.string().regex(/^[a-f0-9]{40}$/),
    moduleIds: ids.min(1),
    lessons: z
      .array(
        z
          .object({
            id: idSchema,
            sectionIds: ids.min(1),
            cardIds: ids.min(3),
            questions: z
              .array(z.object({ id: idSchema, optionIds: ids.min(2) }).strict())
              .min(2),
          })
          .strict(),
      )
      .min(1),
    scenarioIds: ids.min(1),
    assetIds: ids.min(1),
    capstoneId: idSchema,
  })
  .strict();
export function validatePreservation(input: unknown, courses: Course[]) {
  const baseline = preservationSchema.parse(input);
  const course = courses.find((course) => course.id === baseline.courseId);
  if (!course) throw Error(`Missing preserved course: ${baseline.courseId}`);
  const check = (expected: string[], actual: string[]) => {
    const present = new Set(actual);
    for (const id of expected)
      if (!present.has(id)) throw Error(`Missing preserved ID: ${id}`);
  };
  check(
    baseline.moduleIds,
    course.modules.map((module) => module.id),
  );
  check(
    baseline.scenarioIds,
    course.scenarios.map((scenario) => scenario.id),
  );
  check(
    baseline.assetIds,
    course.assets.map((asset) => asset.id),
  );
  if (course.capstoneId !== baseline.capstoneId)
    throw Error("Preserved capstone identity changed");
  const lessons = course.modules.flatMap((module) => module.lessons);
  for (const original of baseline.lessons) {
    const lesson = lessons.find((lesson) => lesson.id === original.id);
    if (!lesson) throw Error(`Missing preserved lesson: ${original.id}`);
    check(
      original.sectionIds,
      lesson.sections.map((section) => section.id),
    );
    check(
      original.cardIds,
      lesson.cards.map((card) => card.id),
    );
    check(
      original.questions.map((question) => question.id),
      lesson.questions.map((question) => question.id),
    );
    for (const question of original.questions)
      check(
        question.optionIds,
        lesson.questions
          .find((item) => item.id === question.id)!
          .options.map((option) => option.id),
      );
  }
  return baseline;
}
