import type { ContentReference, LearningPath } from "./content-schema";

/** Returns canonical IDs; paths never create a second copy of lesson state. */
export const orderedPathLessons = (path: LearningPath) =>
  path.groups.flatMap((group) => group.lessonIds);
export const pathLessonHref = (
  pathId: string,
  lessonId: string,
  sectionId?: string,
) =>
  `#/lesson/${lessonId}${sectionId ? `/${sectionId}` : ""}?path=${encodeURIComponent(pathId)}`;
export const referenceHref = (target: ContentReference, pathId?: string) =>
  target.lessonId
    ? `#/lesson/${target.lessonId}${target.sectionId ? `/${target.sectionId}` : ""}${pathId ? `?path=${encodeURIComponent(pathId)}` : ""}`
    : target.scenarioId
      ? `#/practice/${target.scenarioId}`
      : `#/course/${target.courseId}`;

/** Explicit path lookup only. A direct topic visit must use its course fallback. */
export function pathForLesson(
  paths: LearningPath[],
  lessonId: string,
  preferredPathId?: string,
) {
  if (!preferredPathId) return undefined;
  return paths.find(
    (path) =>
      path.id === preferredPathId &&
      (orderedPathLessons(path).includes(lessonId) ||
        path.optionalBridges.some((bridge) => bridge.lessonId === lessonId)),
  );
}

export function pathNeighbors(path: LearningPath, lessonId: string) {
  const ids = orderedPathLessons(path),
    index = ids.indexOf(lessonId);
  if (index >= 0) return { previous: ids[index - 1], next: ids[index + 1] };
  const bridge = path.optionalBridges.find(
    (item) => item.lessonId === lessonId,
  );
  return { previous: undefined, next: bridge?.beforeLessonIds[0] };
}
