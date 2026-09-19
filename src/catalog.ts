import raw from "./generated/catalog.json";
import search from "./generated/search.json";
import type { Course } from "./content-schema";
export const courses = raw as Course[];
export const publicIndex = search as {
  id: string;
  type: string;
  courseId: string;
  title: string;
  text: string;
  href: string;
}[];
export const lessonEntries = courses.flatMap((course) =>
  course.modules.flatMap((module) =>
    module.lessons.map((lesson) => ({ course, module, lesson })),
  ),
);
export const lessons = lessonEntries.map((x) => x.lesson);
export const cards = lessons.flatMap((l) => l.cards);
export const scenarios = courses.flatMap((course) =>
  course.scenarios.map((scenario) => ({ course, scenario })),
);
export const knownIds = new Set(
  courses.flatMap((c) => [
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
);
export const lessonHref = (id: string, section?: string) =>
  `#/lesson/${id}${section ? `/${section}` : ""}`;
export const findLesson = (id: string) =>
  lessonEntries.find((e) => e.lesson.id === id);
