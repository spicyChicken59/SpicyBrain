import { z } from "zod";

export const idSchema = z.string().regex(/^[a-z][a-z0-9-]{2,100}$/);
const text = z.string().trim().min(1).max(100000);
const ids = z.array(idSchema);
const date = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);
export const sectionKinds = [
  "why",
  "understand",
  "see",
  "deeper",
  "customer",
  "try",
  "revisit",
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
    sections: z.array(sectionSchema).length(7),
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

export function safePath(path: string) {
  return (
    /^[a-zA-Z0-9][a-zA-Z0-9/_ .-]*$/.test(path) &&
    !path.split("/").some((p) => p === ".." || p === ".") &&
    !path.includes("\\")
  );
}
export function validateCourses(input: unknown[]): Course[] {
  const courses = input.map((c) => courseSchema.parse(c));
  const allIds = new Set<string>();
  const navigation = new Set<string>();
  const prereqs = new Map<string, string[]>();
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
    for (const g of c.concepts) link(g.lessonId, g.sectionId);
    for (const l of lessons) {
      const kinds = new Set(l.sections.map((s) => s.kind));
      if (sectionKinds.some((k) => !kinds.has(k)))
        fail(`Missing required teaching section: ${l.id}`);
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
    if (new Set(c.modules.map((m) => m.scenarioId)).size !== c.modules.length)
      fail("Module scenarios must be distinct");
    if (
      c.capstoneId &&
      !c.scenarios.some((s) => s.id === c.capstoneId && s.isCapstone)
    )
      fail("Missing capstone");
    if (c.contract) {
      const d = c.contract;
      if (c.modules.length !== d.modules) fail("Incorrect module count");
      for (const m of c.modules) {
        if (m.lessons.length !== d.lessonsPerModule)
          fail(`Incorrect lesson count: ${m.id}`);
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
          if (parts[1] === "lesson" && parts[3]) link(id, parts[3]);
          if (
            !allIds.has(id) &&
            !navigation.has(id) &&
            !c.scenarios.some((x) => x.id === id)
          )
            fail(`Broken internal link: ${url}`);
        }
      }
  }
  const visit = (id: string, chain = new Set<string>()) => {
    if (chain.has(id)) fail(`Cyclic prerequisite: ${id}`);
    const next = new Set(chain).add(id);
    for (const p of prereqs.get(id) ?? []) {
      if (!navigation.has(p)) fail(`Invalid prerequisite: ${p}`);
      visit(p, next);
    }
  };
  for (const id of navigation) visit(id);
  return courses;
}
