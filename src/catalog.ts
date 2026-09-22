import raw from "./generated/catalog.json";
import { z } from "zod";
import teaching from "./generated/teaching-index.json";
import type {
  TeachingIndexEntry,
  TeachingModule,
  TeachingMedia,
} from "./teaching-schema";
import { validateTeaching, mediaSchema } from "./teaching-schema";
import rawPaths from "./generated/paths.json";
import type { Course, LearningPath } from "./content-schema";
export const courses = raw as Course[];
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
export const cards = [
  ...lessons.flatMap((l) => l.cards),
  ...teachingIndex.flatMap((m) => m.extensionCards),
];
export const scenarios = courses.flatMap((course) =>
  course.scenarios.map((scenario) => ({ course, scenario })),
);
export const knownIds = new Set([
  ...paths.map((path) => path.id),
  ...teachingIndex.flatMap((m) => [
    ...m.beats.map((b) => b.id),
    ...m.extensionCards.map((c) => c.id),
    ...(m.referenceIds ?? []),
  ]),
  ...courses.flatMap((c) => [
    c.id,
    ...c.modules.flatMap((m) => [
      m.id,
      ...m.lessons.flatMap((l) => [
        l.id,
        ...l.sections.map((s) => s.id),
        ...l.cards.map((v) => v.id),
        ...l.questions.map((v) => v.id),
      ]),
    ]),
    ...c.scenarios.map((s) => s.id),
  ]),
]);
export const lessonHref = (id: string, section?: string, pathId?: string) =>
  `#/lesson/${id}${section ? `/${section}` : ""}${pathId ? `?path=${encodeURIComponent(pathId)}` : ""}`;
export const findLesson = (id: string) =>
  lessonEntries.find((e) => e.lesson.id === id);
