import { z } from "zod";
import {
  idSchema,
  questionSchema,
  cardSchema,
  type Course,
} from "./content-schema";
const text = z.string().trim().min(1).max(100000);
const ids = z.array(idSchema);
const date = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);
const httpsUrl = z.url().refine((value) => {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && !url.username && !url.password;
  } catch {
    return false;
  }
}, "Use an HTTPS URL without credentials");
const playerUrl =
  /^https:\/\/(?:www\.)?youtube-nocookie\.com\/embed\/[A-Za-z0-9_-]{11}(?:\?start=\d+(?:&end=\d+)?)?$/;
const authoredStrings = (value: unknown): string[] =>
  typeof value === "string"
    ? [value]
    : Array.isArray(value)
      ? value.flatMap(authoredStrings)
      : value && typeof value === "object"
        ? Object.values(value).flatMap(authoredStrings)
        : [];

function checkAuthoredText(
  value: unknown,
  fail: (message: string) => never,
  internalLink?: (
    kind: string,
    id: string,
    section: string | undefined,
    url: string,
  ) => void,
) {
  if (
    /(?:javascript|vbscript):|\bdata:(?:text|image|application|audio|video|font)\/|<\s*(?:script|iframe|object|embed)\b|onerror\s*=|\[AUTHOR_TODO\]|coming soon/i.test(
      JSON.stringify(value),
    )
  )
    fail("Unsafe or unfinished teaching content");
  for (const leaf of authoredStrings(value)) {
    const prose = leaf
      .replace(/(?:```|~~~)[\s\S]*?(?:```|~~~)/g, "")
      .replace(/`[^`]*`/g, "");
    if (/!\[[^\]]*\]\(/.test(prose))
      fail("Use a local validated teaching visual instead of Markdown images");
    for (const match of prose.matchAll(/\]\(([^)]+)\)/g)) {
      const url = match[1];
      if (url.startsWith("https://")) {
        if (!httpsUrl.safeParse(url).success)
          fail(`Invalid teaching link ${url}`);
        continue;
      }
      const target =
        /^#\/(course|lesson|practice|module)\/([a-z][a-z0-9-]+)(?:\/([a-z][a-z0-9-]+))?$/.exec(
          url,
        );
      if (!target) fail(`Unsafe teaching Markdown link: ${url}`);
      const [, kind, id, section] = target!;
      internalLink?.(kind, id, section, url);
    }
  }
}
export const teachingSourceSchema = z
  .object({
    id: idSchema,
    title: text,
    url: httpsUrl,
    publisher: text,
    reviewedAt: date,
    publishedAt: text.nullable(),
    context: text,
    caveat: text,
    reviewedEvidence: text,
  })
  .strict();
const node = z
  .object({
    id: idSchema,
    label: text,
    value: text.optional(),
    detail: text,
    status: z.enum(["selected", "context", "excluded", "pending", "warning"]),
  })
  .strict();
export const visualSchema = z
  .object({
    id: idSchema,
    kind: z.enum(["nodes", "comparison", "timeline", "table", "equation"]),
    title: text,
    alt: text,
    caption: text,
    textEquivalent: text,
    provenance: text,
    claimIds: ids,
    states: z
      .array(
        z
          .object({
            id: idSchema,
            title: text,
            explanation: text,
            nodes: z.array(node),
            connections: z.array(
              z.object({ from: idSchema, to: idSchema, label: text }).strict(),
            ),
            table: z
              .object({
                columns: z.array(text).min(1),
                rows: z.array(z.array(text)).min(1),
              })
              .strict()
              .optional(),
            equation: text.optional(),
          })
          .strict(),
      )
      .min(1)
      .max(12),
  })
  .strict();
export const beatSchema = z
  .object({
    id: idSchema,
    version: text,
    title: text,
    outcome: text,
    explanation: text,
    lessonId: idSchema,
    sectionId: idSchema,
    conceptIds: ids.min(1),
    claimIds: ids,
    visualId: idSchema,
    samajh: z
      .object({ text, mapping: text, boundary: text })
      .strict()
      .optional(),
    questionIds: ids.min(1),
    hint: text.optional(),
    handbook: z.object({ markdown: text, sourceSectionIds: ids }).strict(),
    recap: text,
    changeNote: text,
    mediaIds: ids,
  })
  .strict();
export const teachingModuleSchema = z
  .object({
    schemaVersion: z.literal(1),
    courseId: idSchema,
    moduleId: idSchema,
    title: text,
    summary: text,
    outcomes: z.array(text).min(1),
    startingAssumptions: z.array(text).min(1),
    lessonIds: ids.min(1),
    optionalBridgeLessonIds: ids,
    editorialRationale: text,
    sources: z.array(teachingSourceSchema),
    claims: z.array(
      z
        .object({
          id: idSchema,
          description: text,
          kind: z.enum(["documented", "guidance", "fictional"]),
          sourceIds: ids,
          context: text,
        })
        .strict(),
    ),
    concepts: z.array(
      z
        .object({
          id: idSchema,
          term: text,
          aliases: z.array(text),
          definition: text,
          example: text,
          sourceIds: ids,
        })
        .strict(),
    ),
    visuals: z.array(visualSchema).min(1),
    questions: z.array(questionSchema),
    selfQuestions: z.array(
      z
        .object({
          id: idSchema,
          revision: text,
          prompt: text,
          modelAnswer: text,
          reasoning: text,
          conceptIds: ids.min(1),
          claimIds: ids,
        })
        .strict(),
    ),
    beats: z.array(beatSchema).min(1),
    cardLinks: z.array(
      z.object({ cardId: idSchema, beatId: idSchema }).strict(),
    ),
    extensionCards: z.array(
      cardSchema.extend({ beatId: idSchema, whyItMatters: text }).strict(),
    ),
    recap: z
      .object({ title: text, markdown: text, visualId: idSchema })
      .strict(),
    appliedTask: z
      .object({
        title: text,
        prompt: text,
        modelAnswer: text,
        reasoning: text,
        beatIds: ids.min(1),
      })
      .strict(),
    scenarioIds: ids,
  })
  .strict();
export type TeachingModule = z.infer<typeof teachingModuleSchema>;
export type Beat = z.infer<typeof beatSchema>;
export type TeachingVisual = z.infer<typeof visualSchema>;
export type TeachingConcept = TeachingModule["concepts"][number];
export type TeachingIndexEntry = Pick<
  TeachingModule,
  | "courseId"
  | "moduleId"
  | "title"
  | "summary"
  | "outcomes"
  | "startingAssumptions"
  | "lessonIds"
  | "optionalBridgeLessonIds"
  | "cardLinks"
  | "extensionCards"
> & {
  url: string;
  referenceIds: string[];
  visualIds: string[];
  conceptIds: string[];
  beats: Pick<
    Beat,
    | "id"
    | "title"
    | "version"
    | "lessonId"
    | "sectionId"
    | "recap"
    | "questionIds"
  >[];
};

export const mediaSchema = z
  .object({
    id: idSchema,
    moduleId: idSchema,
    courseId: idSchema,
    beatId: idSchema,
    title: text,
    publisher: text,
    url: httpsUrl,
    publishedAt: text.nullable(),
    reviewedAt: date,
    conceptIds: ids.min(1),
    placement: text,
    watchFor: text,
    useNext: text,
    language: text,
    captions: text,
    durationSeconds: z.number().positive().nullable(),
    startSeconds: z.number().nonnegative().nullable(),
    endSeconds: z.number().positive().nullable(),
    reviewMethod: z.enum([
      "video and transcript",
      "transcript",
      "video and written companion",
    ]),
    reviewedEvidence: text,
    playbackStatus: text,
    embeddingStatus: z.enum(["verified", "unavailable", "unverified"]),
    embedUrl: z
      .string()
      .regex(playerUrl, "Unsupported media player")
      .optional(),
    context: text,
    limits: text,
    candidatesCompared: z
      .array(
        z
          .object({
            title: text,
            url: httpsUrl,
            decision: text,
          })
          .strict(),
      )
      .min(1),
    fallback: z
      .object({ title: text, markdown: text, visualId: idSchema })
      .strict(),
  })
  .strict()
  .superRefine((media, context) => {
    if (
      (media.startSeconds !== null &&
        media.durationSeconds !== null &&
        media.startSeconds >= media.durationSeconds) ||
      (media.endSeconds !== null &&
        (media.startSeconds === null ||
          media.endSeconds <= media.startSeconds ||
          (media.durationSeconds !== null &&
            media.endSeconds > media.durationSeconds)))
    )
      context.addIssue({ code: "custom", message: "Invalid media segment" });
    if (media.embeddingStatus === "verified" && !media.embedUrl)
      context.addIssue({ code: "custom", message: "Missing verified player" });
    try {
      checkAuthoredText(media, (message) => {
        throw Error(message);
      });
    } catch (error) {
      context.addIssue({
        code: "custom",
        message:
          error instanceof Error ? error.message : "Unsafe media content",
      });
    }
  });
export type TeachingMedia = z.infer<typeof mediaSchema>;

export function validateTeaching(
  raw: unknown[],
  courses: Course[],
  mediaRaw: unknown[] = [],
  validateMediaReferences = true,
) {
  const modules = raw.map((m) => teachingModuleSchema.parse(m)),
    media = mediaRaw.map((m) => mediaSchema.parse(m));
  const all = new Set<string>(
    courses.flatMap((c) => [
      c.id,
      ...c.modules.map((m) => m.id),
      ...c.sources.map((s) => s.id),
      ...c.claims.map((s) => s.id),
      ...c.concepts.map((s) => s.id),
      ...c.assets.map((s) => s.id),
      ...(c.downloads ?? []).map((s) => s.id),
      ...c.scenarios.flatMap((s) => [s.id, ...s.rubric.map((r) => r.id)]),
      ...c.modules.flatMap((m) =>
        m.lessons.flatMap((l) => [
          l.id,
          ...l.sections.map((s) => s.id),
          ...l.cards.map((c) => c.id),
          ...l.questions.flatMap((q) => [q.id, ...q.options.map((o) => o.id)]),
        ]),
      ),
    ]),
  );
  const fail = (s: string): never => {
    throw Error(s);
  };
  const refs = (a: string[], set: Set<string>, label: string) => {
    for (const id of a)
      if (!set.has(id)) fail(`Unresolved teaching ${label}: ${id}`);
  };
  const internalLink = (
    kind: string,
    id: string,
    section: string | undefined,
    url: string,
  ) => {
    if (kind === "course" && (!courses.some((c) => c.id === id) || section))
      fail(`Broken teaching course link ${url}`);
    if (
      kind === "practice" &&
      (!courses.some((c) => c.scenarios.some((s) => s.id === id)) || section)
    )
      fail(`Broken teaching practice link ${url}`);
    if (
      kind === "lesson" &&
      !courses.some((c) =>
        c.modules.some((m) =>
          m.lessons.some(
            (l) =>
              l.id === id &&
              (!section || l.sections.some((s) => s.id === section)),
          ),
        ),
      )
    )
      fail(`Broken teaching lesson link ${url}`);
    if (
      kind === "module" &&
      !modules.some(
        (m) =>
          m.moduleId === id &&
          (!section || m.beats.some((b) => b.id === section)),
      )
    )
      fail(`Broken teaching module link ${url}`);
  };
  const pair = new Set<string>();
  for (const m of modules) {
    const key = `${m.courseId}/${m.moduleId}`;
    if (pair.has(key)) fail(`Duplicate teaching module ${key}`);
    pair.add(key);
    const c = courses.find((c) => c.id === m.courseId);
    if (!c?.modules.some((x) => x.id === m.moduleId))
      fail(`Unknown teaching module ${key}`);
    const course = c!;
    const lessons = course.modules.flatMap((m) => m.lessons),
      sections = lessons.flatMap((l) => l.sections);
    for (const item of [
      ...m.sources,
      ...m.claims,
      ...m.concepts,
      ...m.visuals,
      ...m.questions,
      ...m.questions.flatMap((q) => q.options),
      ...m.selfQuestions,
      ...m.beats,
      ...m.extensionCards,
    ]) {
      if (all.has(item.id)) fail(`Duplicate teaching identity ${item.id}`);
      all.add(item.id);
    }
    const sources = new Set([...course.sources, ...m.sources].map((s) => s.id)),
      claims = new Set([...course.claims, ...m.claims].map((s) => s.id)),
      concepts = new Set([...course.concepts, ...m.concepts].map((s) => s.id)),
      questions = new Set(
        [
          ...lessons.flatMap((l) => l.questions),
          ...m.questions,
          ...m.selfQuestions,
        ].map((q) => q.id),
      ),
      visuals = new Set(m.visuals.map((v) => v.id)),
      beats = new Set(m.beats.map((b) => b.id));
    const lessonIds = new Set(lessons.map((l) => l.id));
    refs(m.lessonIds, lessonIds, "lesson");
    refs(m.optionalBridgeLessonIds, lessonIds, "bridge");
    refs(m.scenarioIds, new Set(course.scenarios.map((s) => s.id)), "scenario");
    const owned = course.modules
      .find((x) => x.id === m.moduleId)!
      .lessons.map((l) => l.id);
    if (
      new Set(m.lessonIds).size !== m.lessonIds.length ||
      owned.length !== m.lessonIds.length ||
      owned.some((id) => !m.lessonIds.includes(id))
    )
      fail(`Teaching lesson ownership differs from course map: ${m.moduleId}`);
    for (const claim of m.claims) {
      refs(claim.sourceIds, sources, "claim source");
      if (claim.kind === "documented" && !claim.sourceIds.length)
        fail(`Missing evidence ${claim.id}`);
    }
    for (const g of m.concepts) refs(g.sourceIds, sources, "concept source");
    for (const v of m.visuals) {
      refs(v.claimIds, claims, "visual claim");
      const stateIds = new Set<string>();
      for (const s of v.states) {
        if (stateIds.has(s.id)) fail(`Duplicate visual stage ${s.id}`);
        stateIds.add(s.id);
        const nodes = new Set(s.nodes.map((n) => n.id));
        if (nodes.size !== s.nodes.length)
          fail(`Duplicate visual node ${v.id}`);
        for (const e of s.connections)
          refs([e.from, e.to], nodes, "connection");
        if (!s.nodes.length && !s.table && !s.equation)
          fail(`Empty visual ${v.id}`);
        if (s.table?.rows.some((r) => r.length !== s.table!.columns.length))
          fail(`Unequal table cells ${v.id}`);
      }
    }
    for (const q of [...m.questions, ...m.selfQuestions]) {
      refs(q.conceptIds, concepts, "question concept");
      refs(q.claimIds, claims, "question claim");
      if ("options" in q && !q.options.some((o) => o.id === q.correctOptionId))
        fail(`Unknown correct answer ${q.id}`);
    }
    for (const b of m.beats) {
      if (
        !lessons
          .find((l) => l.id === b.lessonId)
          ?.sections.some((s) => s.id === b.sectionId)
      )
        fail(`Broken beat legacy anchor ${b.id}`);
      refs(b.conceptIds, concepts, "beat concept");
      refs(b.claimIds, claims, "beat claim");
      refs(b.questionIds, questions, "beat question");
      refs([b.visualId], visuals, "beat visual");
      refs(
        b.handbook.sourceSectionIds,
        new Set(sections.map((s) => s.id)),
        "handbook section",
      );
      if (validateMediaReferences)
        refs(
          b.mediaIds,
          new Set(
            media
              .filter(
                (v) => v.moduleId === m.moduleId && v.courseId === m.courseId,
              )
              .map((v) => v.id),
          ),
          "media",
        );
    }
    for (const card of m.extensionCards) {
      refs(card.conceptIds, concepts, "card concept");
      refs(card.claimIds, claims, "card claim");
      refs([card.beatId], beats, "card beat");
      if (
        !lessons
          .find((l) => l.id === card.lessonId)
          ?.sections.some((s) => s.id === card.sectionId)
      )
        fail(`Broken extension anchor ${card.id}`);
    }
    const legacyCards = new Set(
      lessons
        .filter((l) => m.lessonIds.includes(l.id))
        .flatMap((l) => l.cards.map((c) => c.id)),
    );
    for (const link of m.cardLinks) {
      refs([link.cardId], legacyCards, "core card");
      refs([link.beatId], beats, "core card beat");
    }
    if (new Set(m.cardLinks.map((l) => l.cardId)).size !== m.cardLinks.length)
      fail(`Duplicate core card mapping ${m.moduleId}`);
    if (
      [...legacyCards].some((id) => !m.cardLinks.some((l) => l.cardId === id))
    )
      fail(`Unmapped canonical card ${m.moduleId}`);
    refs([m.recap.visualId], visuals, "recap visual");
    refs(m.appliedTask.beatIds, beats, "task beat");
    for (const match of JSON.stringify(m).matchAll(
      /\[\[([a-z][a-z0-9-]+)\|[^\]]+\]\]/g,
    ))
      refs([match[1]], concepts, "inline concept");
    checkAuthoredText(m, fail, internalLink);
  }
  for (const v of media) {
    if (all.has(v.id)) fail(`Duplicate media ${v.id}`);
    all.add(v.id);
    const m = modules.find(
      (m) => m.moduleId === v.moduleId && m.courseId === v.courseId,
    );
    if (!m || !m.beats.some((b) => b.id === v.beatId))
      fail(`Unknown media placement ${v.id}`);
    refs(
      [v.fallback.visualId],
      new Set(m!.visuals.map((v) => v.id)),
      "media fallback",
    );
    refs(
      v.conceptIds,
      new Set(
        [
          ...m!.concepts,
          ...courses.find((c) => c.id === v.courseId)!.concepts,
        ].map((g) => g.id),
      ),
      "media concept",
    );
    checkAuthoredText(v, fail, internalLink);
    for (const match of JSON.stringify(v).matchAll(
      /\[\[([a-z][a-z0-9-]+)\|[^\]]+\]\]/g,
    ))
      refs(
        [match[1]],
        new Set(
          [
            ...m!.concepts,
            ...courses.find((c) => c.id === v.courseId)!.concepts,
          ].map((g) => g.id),
        ),
        "media inline concept",
      );
  }
  return { modules, media };
}
