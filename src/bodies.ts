import { z } from "zod";
import {
  cardSchema,
  claimSchema,
  courseConceptSchema,
  idSchema,
  questionSchema,
  rubricSchema,
  sourceSchema,
} from "./content-schema";
import type {
  BodyKind,
  CatalogCourse,
  ContentBody,
  CourseReferences,
  LessonBody,
} from "./catalog-types";

const text = z.string().trim().min(1).max(100000);
export const bodySchema = z.discriminatedUnion("kind", [
  z
    .object({
      kind: z.literal("lesson"),
      id: idSchema,
      contentVersion: text,
      sections: z.record(idSchema, text),
      sectionClaims: z.record(idSchema, z.array(idSchema)),
      questions: z.array(questionSchema),
      cards: z.array(cardSchema),
    })
    .strict(),
  z
    .object({
      kind: z.literal("scenario"),
      id: idSchema,
      context: text,
      task: text,
      model: text,
      reasoning: text,
      disclosures: z.array(
        z.object({ question: text, response: text }).strict(),
      ),
      requirements: z.array(text).min(1),
      rubric: z.array(rubricSchema).min(1),
      claimIds: z.array(idSchema),
    })
    .strict(),
  z.object({ kind: z.literal("lab"), id: idSchema, body: text }).strict(),
  z
    .object({
      kind: z.literal("guide"),
      id: idSchema,
      body: z
        .object({ action: text, example: text, template: text, limits: text })
        .strict(),
    })
    .strict(),
  z.object({ kind: z.literal("case"), id: idSchema, body: text }).strict(),
]);

type Revision = { id: string; revision: string };
/** What the catalog tier promises about one body file before it is fetched. */
export type BodyExpectation =
  | {
      kind: "lesson";
      id: string;
      contentVersion: string;
      sectionIds: string[];
      cards: Revision[];
      questions: Revision[];
    }
  | { kind: Exclude<BodyKind, "lesson">; id: string };

export function bodyExpectations(courses: CatalogCourse[]) {
  const map = new Map<string, BodyExpectation>();
  const plain = (kind: Exclude<BodyKind, "lesson">, id: string) =>
    map.set(id, { kind, id });
  for (const course of courses) {
    for (const module of course.modules)
      for (const lesson of module.lessons)
        map.set(lesson.id, {
          kind: "lesson",
          id: lesson.id,
          contentVersion: lesson.contentVersion,
          sectionIds: lesson.sections.map((s) => s.id),
          cards: lesson.cards.map(({ id, revision }) => ({ id, revision })),
          questions: lesson.questions.map(({ id, revision }) => ({
            id,
            revision,
          })),
        });
    for (const scenario of course.scenarios) plain("scenario", scenario.id);
    for (const lab of course.labs ?? []) plain("lab", lab.id);
    for (const guide of course.guides ?? []) plain("guide", guide.id);
    for (const item of course.cases ?? []) plain("case", item.id);
  }
  return map;
}

const labels: Record<BodyKind, string> = {
  lesson: "This lesson",
  scenario: "This practice item",
  lab: "This lab",
  guide: "This guide",
  case: "This case analysis",
};
export const bodyErrors = {
  unavailable: "This content is unavailable.",
  network: (kind: BodyKind) =>
    `${labels[kind]} could not load. Check your connection and retry. Your study data is safe.`,
  invalid: (kind: BodyKind) =>
    `${labels[kind]}'s files are incomplete or invalid. Retry, or reload to get the current course. Your study data is safe.`,
  mismatch:
    "Course files changed or are incomplete. Reload to get a consistent version. Your study data is safe.",
};
const same = (a: unknown, b: unknown) =>
  JSON.stringify(a) === JSON.stringify(b);
/** Validates a fetched body's identity against the catalog reference it was requested for. */
export function checkBody(
  body: ContentBody,
  expected: BodyExpectation,
): ContentBody {
  if (body.kind !== expected.kind || body.id !== expected.id)
    throw Error(bodyErrors.mismatch);
  if (body.kind === "lesson" && expected.kind === "lesson") {
    const sections = Object.keys(body.sections),
      claimed = Object.keys(body.sectionClaims);
    if (
      body.contentVersion !== expected.contentVersion ||
      sections.length !== expected.sectionIds.length ||
      expected.sectionIds.some((id) => !(id in body.sections)) ||
      claimed.length !== expected.sectionIds.length ||
      expected.sectionIds.some((id) => !(id in body.sectionClaims)) ||
      !same(
        body.cards.map(({ id, revision }) => ({ id, revision })),
        expected.cards,
      ) ||
      !same(
        body.questions.map(({ id, revision }) => ({ id, revision })),
        expected.questions,
      )
    )
      throw Error(bodyErrors.mismatch);
  }
  return body;
}

export type BodyLoader = {
  load: (id: string) => Promise<ContentBody>;
  lesson: (id: string) => Promise<LessonBody>;
  has: (id: string) => boolean;
};
/**
 * Promise-cached loader. A failed load is evicted so Retry fetches again; a
 * body that does not match its catalog reference is never cached.
 */
export function createBodyLoader(options: {
  url: (id: string) => string;
  expected: (id: string) => BodyExpectation | undefined;
  fetch?: typeof fetch;
}): BodyLoader {
  const cache = new Map<string, Promise<ContentBody>>();
  const request = options.fetch ?? ((input) => fetch(input));
  const load = (id: string) => {
    const expected = options.expected(id);
    if (!expected) return Promise.reject(Error(bodyErrors.unavailable));
    if (!cache.has(id))
      cache.set(
        id,
        request(options.url(id))
          .catch(() => {
            // A rejected fetch (offline, aborted) is a network failure, not a
            // content fault; surface the retryable message, never a raw TypeError.
            throw Error(bodyErrors.network(expected.kind));
          })
          .then(async (response) => {
            if (!response.ok) throw Error(bodyErrors.network(expected.kind));
            let body: ContentBody;
            try {
              body = bodySchema.parse(await response.json());
            } catch {
              throw Error(bodyErrors.invalid(expected.kind));
            }
            return checkBody(body, expected);
          })
          .catch((error: unknown) => {
            cache.delete(id);
            throw error;
          }),
      );
    return cache.get(id)!;
  };
  return {
    load,
    lesson: async (id) => {
      const body = await load(id);
      if (body.kind !== "lesson") throw Error(bodyErrors.mismatch);
      return body;
    },
    has: (id) => cache.has(id),
  };
}

export const referencesSchema = z
  .object({
    kind: z.literal("references"),
    courseId: idSchema,
    sources: z.array(sourceSchema),
    claims: z.array(claimSchema),
    concepts: z.array(courseConceptSchema),
  })
  .strict();
const referenceLabel = "Sources and definitions";
export const referenceErrors = {
  network: `${referenceLabel} could not load. Check your connection and retry. Your study data is safe.`,
  invalid: `${referenceLabel} are incomplete or invalid. Retry, or reload to get the current course. Your study data is safe.`,
};
/**
 * The reference file must carry exactly the catalog's source, claim and
 * concept identities, in the catalog's order: a file from another version of
 * the course is refused rather than shown against this catalog.
 */
export function checkReferences(
  references: CourseReferences,
  course: CatalogCourse,
): CourseReferences {
  const ids = (items: { id: string }[]) => items.map((item) => item.id);
  if (
    references.courseId !== course.id ||
    !same(ids(references.sources), ids(course.sources)) ||
    !same(ids(references.claims), ids(course.claims)) ||
    !same(ids(references.concepts), ids(course.concepts))
  )
    throw Error(bodyErrors.mismatch);
  return references;
}
export type ReferenceLoader = {
  load: (courseId: string) => Promise<CourseReferences>;
  /** The references once loaded, so a view that preloaded them renders them at once. */
  cached: (courseId: string) => CourseReferences | undefined;
};
/** Promise-cached per course; a failed or mismatched load is evicted so Retry fetches again. */
export function createReferenceLoader(options: {
  url: (courseId: string) => string;
  course: (courseId: string) => CatalogCourse | undefined;
  fetch?: typeof fetch;
}): ReferenceLoader {
  const cache = new Map<string, Promise<CourseReferences>>(),
    resolved = new Map<string, CourseReferences>();
  const request = options.fetch ?? ((input) => fetch(input));
  const load = (courseId: string) => {
    const course = options.course(courseId);
    if (!course) return Promise.reject(Error(bodyErrors.unavailable));
    if (!cache.has(courseId))
      cache.set(
        courseId,
        request(options.url(courseId))
          .catch(() => {
            throw Error(referenceErrors.network);
          })
          .then(async (response) => {
            if (!response.ok) throw Error(referenceErrors.network);
            let references: CourseReferences;
            try {
              references = referencesSchema.parse(await response.json());
            } catch {
              throw Error(referenceErrors.invalid);
            }
            checkReferences(references, course);
            resolved.set(courseId, references);
            return references;
          })
          .catch((error: unknown) => {
            cache.delete(courseId);
            throw error;
          }),
      );
    return cache.get(courseId)!;
  };
  return { load, cached: (courseId) => resolved.get(courseId) };
}
