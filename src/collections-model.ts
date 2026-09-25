import type { CatalogCourse, CatalogGuide } from "./catalog-types";
import type { LearningPath, Track } from "./content-schema";
import type { TeachingIndexEntry } from "./teaching-schema";

/**
 * Pure helpers behind the optional course collections (tracks, routes, labs,
 * guides, cases, crosswalk). They read only the catalog tier, so every view
 * that uses them works without loading a body, and they are unit-tested
 * without a browser. Nothing here is specific to one course.
 */

export type LabExecutionClass = NonNullable<
  CatalogCourse["labs"]
>[number]["executionClass"];
/** Plain-language names for how a lab runs. A class describes where work happens, never that a lab was verified. */
export const labClassText: Record<
  LabExecutionClass,
  { label: string; legend: string }
> = {
  "local-executed": {
    label: "Locally executed",
    legend:
      "You run the provided files on your own computer with the tools the lab names. The lab’s evidence describes a local run, not a run on a hosted platform.",
  },
  tabletop: {
    label: "Tabletop",
    legend:
      "You work through the materials on paper or in a text editor. Nothing is executed; the result is your written reasoning.",
  },
  "platform-guide": {
    label: "Platform guide",
    legend:
      "A walkthrough to follow on the platform itself if you have access. The course did not run it for you and claims no result from it.",
  },
};
export const labClassOrder: LabExecutionClass[] = [
  "local-executed",
  "tabletop",
  "platform-guide",
];

/**
 * Every content identity a study record can cite. A field-guide draft is an
 * ordinary note whose section is the guide, so collection identities count as
 * known content in an import preview.
 */
export function collectKnownIds(
  courses: CatalogCourse[],
  teaching: Pick<
    TeachingIndexEntry,
    "beats" | "extensionCards" | "referenceIds"
  >[],
  paths: Pick<LearningPath, "id">[],
) {
  return new Set([
    ...paths.map((path) => path.id),
    ...teaching.flatMap((m) => [
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
      ...(c.tracks ?? []).map((t) => t.id),
      ...(c.routes ?? []).map((r) => r.id),
      ...(c.labs ?? []).map((l) => l.id),
      ...(c.guides ?? []).map((g) => g.id),
      ...(c.cases ?? []).map((x) => x.id),
      ...(c.crosswalk ?? []).map((x) => x.id),
    ]),
  ]);
}

/** True when a course declares any lab, guide, case or crosswalk entry. */
export const hasCollections = (course: CatalogCourse) =>
  !!(
    course.labs?.length ||
    course.guides?.length ||
    course.cases?.length ||
    course.crosswalk?.length
  );

export const trackOf = (
  course: CatalogCourse,
  moduleId: string,
): Track | undefined =>
  course.tracks?.find((track) => track.moduleIds.includes(moduleId));

/** The module after this one in its track's order, if the course has tracks. */
export function nextInTrack(course: CatalogCourse, moduleId: string) {
  const track = trackOf(course, moduleId);
  if (!track) return undefined;
  return {
    track,
    next: track.moduleIds[track.moduleIds.indexOf(moduleId) + 1] as
      string | undefined,
  };
}

/** Labs and field guides that name this module. */
export function relatedCollections(course: CatalogCourse, moduleId: string) {
  return {
    labs: (course.labs ?? []).filter((lab) => lab.moduleIds.includes(moduleId)),
    guides: (course.guides ?? []).filter((guide) =>
      guide.moduleIds.includes(moduleId),
    ),
  };
}

type Position = {
  moduleId: string;
  beatId: string;
  updatedAt: string;
  view: "deck" | "handbook" | "cards";
};
/**
 * The most recently saved beat inside a route's modules, if its beat still
 * exists; otherwise undefined, and the route offers Start instead of Resume.
 */
export function routeResume(
  moduleIds: string[],
  positions: Record<string, Position>,
  teaching: { moduleId: string; beats: { id: string }[] }[],
) {
  return Object.values(positions)
    .filter(
      (p) =>
        moduleIds.includes(p.moduleId) &&
        teaching.some(
          (m) =>
            m.moduleId === p.moduleId && m.beats.some((b) => b.id === p.beatId),
        ),
    )
    .sort(
      (a, b) =>
        b.updatedAt.localeCompare(a.updatedAt) ||
        a.beatId.localeCompare(b.beatId),
    )[0];
}

/** Who reported a case: common reporter kinds read as a phrase; anything else is shown as written. */
export function reporterText(reporter: string) {
  const known: Record<string, string> = {
    "customer-authored": "The customer (customer-authored)",
    "vendor case study": "The vendor (vendor case study)",
    joint: "The customer and the vendor jointly",
    "conference talk": "A conference talk",
  };
  // Own keys only: an authored reporter such as "constructor" is shown as written.
  return Object.hasOwn(known, reporter) ? known[reporter] : reporter;
}

/** A field-guide draft is an ordinary note keyed by the guide. */
export const guideNoteId = (guideId: string) => `note-${guideId}`;
/** The lesson a guide draft is filed under: the guide's first linked lesson, else the course's first lesson. */
export const guideNoteLesson = (course: CatalogCourse, guide: CatalogGuide) =>
  guide.lessonIds[0] ?? course.modules[0].lessons[0].id;

/** The previous beat in the saved beat's module, from the teaching index. */
export function beatNeighbourhood<B extends { id: string }>(
  entry: { beats: B[] },
  beatId: string,
) {
  const index = entry.beats.findIndex((b) => b.id === beatId);
  return {
    index,
    total: entry.beats.length,
    previous: index > 0 ? entry.beats[index - 1] : undefined,
  };
}
