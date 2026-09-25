import raw from "./generated/catalog.json";
import { z } from "zod";
import teaching from "./generated/teaching-index.json";
import type {
  TeachingIndexEntry,
  TeachingModule,
  TeachingMedia,
} from "./teaching-schema";
import {
  validateTeaching,
  mediaSchema,
  teachingLinkTargets,
  type TeachingLinkTargets,
} from "./teaching-schema";
import rawPaths from "./generated/paths.json";
import type { Card, LearningPath } from "./content-schema";
import type {
  CardRef,
  CatalogCourse,
  ContentBody,
  CourseReferences,
  LessonBody,
  ScenarioBody,
} from "./catalog-types";
import {
  bodyErrors,
  bodyExpectations,
  createBodyLoader,
  createReferenceLoader,
} from "./bodies";
import { collectKnownIds } from "./collections-model";
export type { CatalogCourse, CatalogLesson } from "./catalog-types";
export type ExtensionCard = TeachingModule["extensionCards"][number];
/** The catalog tier: identities, titles, mappings and counts, never lesson prose or card text. */
export const courses = raw as CatalogCourse[];
export const paths = rawPaths as LearningPath[];
export const defaultPath = paths.find((path) => path.defaultStart);
export const playbooks = paths.flatMap((path) =>
  path.playbooks.map((playbook) => ({ ...playbook, path })),
);
export type SearchEntry = {
  id: string;
  type: string;
  courseId: string;
  title: string;
  text: string;
  href: string;
};
export const teachingIndex = teaching as TeachingIndexEntry[];
export async function loadSearch(): Promise<SearchEntry[]> {
  const response = await fetch(
    `${import.meta.env.BASE_URL}teaching/search.json`,
  );
  if (!response.ok)
    throw Error("Search could not load. Your study data is safe.");
  const result = z
    .array(
      z
        .object({
          id: z.string(),
          type: z.string(),
          courseId: z.string(),
          title: z.string(),
          text: z.string(),
          href: z.string().regex(/^#\//),
        })
        .strict(),
    )
    .safeParse(await response.json());
  if (!result.success)
    throw Error(
      "Search files are incomplete. Reload and try again. Your study data is safe.",
    );
  return result.data;
}
const moduleCache = new Map<string, Promise<TeachingModule>>();
let linkTargets: TeachingLinkTargets | undefined;
/**
 * A module is validated alone at runtime, so its links to other modules are
 * checked against the teaching index (the build already checked them against
 * the complete set of modules).
 */
const moduleLinkTargets = () =>
  (linkTargets ??= teachingLinkTargets(teachingIndex));
/**
 * The reference tier: one file per course with the full source, claim and
 * glossary records, validated and identity-checked against the catalog's
 * ids. A module workspace and a handbook wait for it beside their modules
 * (definitions and sources are part of the teaching); a lesson or practice
 * page fetches it only when a Sources panel is opened. Card text never needs
 * it, so a review session does not depend on it.
 */
const referenceLoader = createReferenceLoader({
  url: (courseId) =>
    `${import.meta.env.BASE_URL}teaching/references/${courseId}.json`,
  course: (courseId) => courses.find((c) => c.id === courseId),
});
export const loadReferences = (courseId: string): Promise<CourseReferences> =>
  referenceLoader.load(courseId);
export const cachedReferences = (courseId: string) =>
  referenceLoader.cached(courseId);
export const subscribeReferences = (listener: () => void) =>
  referenceLoader.subscribe(listener);
export function loadTeachingModule(moduleId: string) {
  const entry = teachingIndex.find((m) => m.moduleId === moduleId);
  if (!entry)
    return Promise.reject(Error("This teaching module is unavailable."));
  if (!moduleCache.has(moduleId))
    moduleCache.set(
      moduleId,
      fetch(`${import.meta.env.BASE_URL}${entry.url}`)
        .then(async (response) => {
          if (!response.ok)
            throw Error(
              "This module could not load. Check your connection and retry.",
            );
          let module: TeachingModule;
          try {
            module = validateTeaching(
              [await response.json()],
              courses,
              [],
              false,
              moduleLinkTargets(),
            ).modules[0];
          } catch {
            throw Error(
              "This module's files are incomplete or invalid. Retry, or reload to get the current course. Your study data is safe.",
            );
          }
          if (
            module.moduleId !== entry.moduleId ||
            module.courseId !== entry.courseId ||
            JSON.stringify(module.visuals.map((v) => v.id)) !==
              JSON.stringify(entry.visualIds) ||
            JSON.stringify(module.concepts.map((c) => c.id)) !==
              JSON.stringify(entry.conceptIds) ||
            JSON.stringify(
              module.beats.map((b) => ({ id: b.id, version: b.version })),
            ) !==
              JSON.stringify(
                entry.beats.map((b) => ({ id: b.id, version: b.version })),
              ) ||
            JSON.stringify(
              module.extensionCards.map((c) => ({
                id: c.id,
                revision: c.revision,
              })),
            ) !==
              JSON.stringify(
                entry.extensionCards.map((c) => ({
                  id: c.id,
                  revision: c.revision,
                })),
              )
          )
            throw Error(
              "Course files changed or are incomplete. Reload to get a consistent version. Your study data is safe.",
            );
          return module;
        })
        .catch((error) => {
          moduleCache.delete(moduleId);
          throw error;
        }),
    );
  return moduleCache.get(moduleId)!;
}
export async function loadTeachingMedia(): Promise<TeachingMedia[]> {
  const response = await fetch(
    `${import.meta.env.BASE_URL}teaching/media.json`,
  );
  if (!response.ok)
    throw Error(
      "Video references could not load. The illustrated lesson remains available.",
    );
  const media = mediaSchema.array().parse(await response.json());
  for (const item of media) {
    const entry = teachingIndex.find(
      (m) => m.moduleId === item.moduleId && m.courseId === item.courseId,
    );
    if (
      !entry?.beats.some((b) => b.id === item.beatId) ||
      !entry.visualIds.includes(item.fallback.visualId) ||
      item.conceptIds.some(
        (id) =>
          !entry.conceptIds.includes(id) &&
          !courses
            .find((c) => c.id === item.courseId)
            ?.concepts.some((c) => c.id === id),
      )
    )
      throw Error("Video references do not match this course version.");
    if (
      item.embedUrl &&
      !/^https:\/\/www\.youtube-nocookie\.com\/embed\/[A-Za-z0-9_-]{11}(?:\?start=\d+(?:&end=\d+)?)?$/.test(
        item.embedUrl,
      )
    )
      throw Error("Unsupported video player address.");
  }
  return media;
}
export const beatHref = (
  moduleId: string,
  beatId?: string,
  view = "deck",
  detour = false,
) =>
  `#/module/${moduleId}${beatId ? `/${beatId}` : ""}${view !== "deck" || detour ? `?view=${view}${detour ? "&detour=1" : ""}` : ""}`;
export const findBeat = (beatId: string) =>
  teachingIndex
    .flatMap((m) => m.beats.map((b) => ({ module: m, beat: b })))
    .find((x) => x.beat.id === beatId);
export const teachingTarget = (targetId: string) => {
  const module = teachingIndex.find(
    (m) =>
      m.moduleId === targetId ||
      m.beats.some(
        (b) => b.id === targetId || b.questionIds.includes(targetId),
      ),
  );
  if (!module) return undefined;
  const beat =
    module.beats.find(
      (b) => b.id === targetId || b.questionIds.includes(targetId),
    ) ?? module.beats.at(-1)!;
  return {
    title:
      module.moduleId === targetId
        ? `${module.title} · applied task`
        : beat.title,
    href: beatHref(module.moduleId, beat.id, "deck", true),
  };
};
export const cardTeaching = (cardId: string) => {
  const module = teachingIndex.find(
    (m) =>
      m.cardLinks.some((c) => c.cardId === cardId) ||
      m.extensionCards.some((c) => c.id === cardId),
  );
  const beatId =
    module?.cardLinks.find((c) => c.cardId === cardId)?.beatId ??
    module?.extensionCards.find((c) => c.id === cardId)?.beatId;
  return module && beatId
    ? {
        module,
        beatId,
        href:
          beatHref(module.moduleId, beatId, "handbook", true) +
          (module.extensionCards.some((c) => c.id === cardId)
            ? `&extension=${cardId}`
            : ""),
      }
    : undefined;
};
export const plainTeaching = (s: string) =>
  s.replace(/\[\[[a-z][a-z0-9-]+\|([^\]]+)\]\]/g, "$1");
export const lessonEntries = courses.flatMap((course) =>
  course.modules.flatMap((module) =>
    module.lessons.map((lesson) => ({ course, module, lesson })),
  ),
);
export const lessons = lessonEntries.map((x) => x.lesson);
export const extensionCardIds = new Set(
  teachingIndex.flatMap((m) => m.extensionCards.map((c) => c.id)),
);
/** Every reviewable card's identity, core lessons first, then extension cards. Text is loaded through `loadCards`. */
export const cardIndex: CardRef[] = [
  ...lessons.flatMap((l) => l.cards),
  ...teachingIndex.flatMap((m) => m.extensionCards),
];
const cardOwner = new Map(
  lessons.flatMap((l) => l.cards.map((c) => [c.id, l.id] as const)),
);
const questionOwner = new Map(
  lessons.flatMap((l) => l.questions.map((q) => [q.id, l.id] as const)),
);
export const scenarios = courses.flatMap((course) =>
  course.scenarios.map((scenario) => ({ course, scenario })),
);
export const knownIds = collectKnownIds(courses, teachingIndex, paths);
/** Field guides by identity; a guide draft note cites its guide as its section. */
export const guideEntries = courses.flatMap((course) =>
  (course.guides ?? []).map((guide) => ({ course, guide })),
);
export const findGuide = (id: string) =>
  guideEntries.find((entry) => entry.guide.id === id);
export const lessonHref = (id: string, section?: string, pathId?: string) =>
  `#/lesson/${id}${section ? `/${section}` : ""}${pathId ? `?path=${encodeURIComponent(pathId)}` : ""}`;
export const findLesson = (id: string) =>
  lessonEntries.find((e) => e.lesson.id === id);

/**
 * The body tier. Each lesson, scenario, lab, guide and case has one
 * same-origin JSON file, validated and identity-checked against the catalog
 * before it is cached; a failed load is evicted so Retry fetches again.
 */
const expectations = bodyExpectations(courses);
const bodyLoader = createBodyLoader({
  url: (id) => `${import.meta.env.BASE_URL}teaching/bodies/${id}.json`,
  expected: (id) => expectations.get(id),
});
export const loadBody = (id: string): Promise<ContentBody> =>
  bodyLoader.load(id);
export const loadLessonBody = (id: string): Promise<LessonBody> =>
  bodyLoader.lesson(id);
export async function loadScenarioBody(id: string): Promise<ScenarioBody> {
  const body = await loadBody(id);
  if (body.kind !== "scenario") throw Error(bodyErrors.mismatch);
  return body;
}
/** A lab, guide or case body, refused when the file is another kind. */
export async function loadCollectionBody<K extends "lab" | "guide" | "case">(
  kind: K,
  id: string,
): Promise<Extract<ContentBody, { kind: K }>> {
  const body = await loadBody(id);
  if (body.kind !== kind) throw Error(bodyErrors.mismatch);
  return body as Extract<ContentBody, { kind: K }>;
}
/** Lessons a module workspace needs: the owned lessons plus any lesson whose check a beat reuses. */
export function moduleLessonIds(entry: TeachingIndexEntry) {
  return [
    ...new Set([
      ...entry.lessonIds,
      ...entry.beats.flatMap((b) =>
        b.questionIds.flatMap((q) => {
          const owner = questionOwner.get(q);
          return owner ? [owner] : [];
        }),
      ),
    ]),
  ];
}
/** Resolves card text: core cards through their lesson bodies, extension cards through their module. */
export async function loadCards(
  ids: string[],
): Promise<Map<string, Card | ExtensionCard>> {
  const wanted = new Set(ids),
    lessonIds = new Set<string>(),
    moduleIds = new Set<string>();
  for (const id of wanted) {
    const owner = cardOwner.get(id);
    if (owner) lessonIds.add(owner);
    else if (extensionCardIds.has(id)) {
      const teaching = cardTeaching(id);
      if (teaching) moduleIds.add(teaching.module.moduleId);
    }
  }
  const result = new Map<string, Card | ExtensionCard>();
  await Promise.all([
    ...[...lessonIds].map(async (lessonId) => {
      for (const card of (await loadLessonBody(lessonId)).cards)
        if (wanted.has(card.id)) result.set(card.id, card);
    }),
    ...[...moduleIds].map(async (moduleId) => {
      for (const card of (await loadTeachingModule(moduleId)).extensionCards)
        if (wanted.has(card.id)) result.set(card.id, card);
    }),
  ]);
  return result;
}
