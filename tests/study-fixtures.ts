import { readFileSync } from "node:fs";
import type { CatalogCourse } from "../src/catalog-types";
import { emptyState, studyBytes, type StudyState } from "../src/study";
export const fixtureAt = "2026-09-19T10:00:00.000Z";
const catalog = JSON.parse(
  readFileSync(
    new URL("../src/generated/catalog.json", import.meta.url),
    "utf8",
  ),
) as CatalogCourse[];
// Keep the exact original regression fixture independent of new topic order.
export const fixtureLessons = catalog
  .flatMap((c) => c.modules.flatMap((m) => m.lessons))
  .filter((l) => /^dbxfe-m\d{2}-l\d{2}$/.test(l.id))
  .sort((a, b) => a.id.localeCompare(b.id));
const sections = fixtureLessons.flatMap((l) =>
  ["why", "understand", "see", "deeper", "customer", "try", "revisit"].map(
    (kind) => ({ lessonId: l.id, sectionId: `${l.id}-${kind}` }),
  ),
);
export function fixtureNote(index: number, text: string) {
  const ref = sections[index % sections.length];
  return {
    id: `note-${ref.sectionId}${index >= sections.length ? `-${index}` : ""}`,
    courseId: "dbxfe",
    ...ref,
    text,
    question: false,
    createdAt: fixtureAt,
    updatedAt: fixtureAt,
  };
}
export function noteState(count = 51, text = "x".repeat(100000)): StudyState {
  const state = emptyState();
  for (let index = 0; index < count; index++) {
    const note = fixtureNote(index, text);
    state.notes[note.id] = note;
  }
  return state;
}
export function exactBytes(bytes: number): StudyState {
  const s = emptyState();
  for (let i = 0; studyBytes(s) < bytes; i++) {
    const n = fixtureNote(i, "");
    s.notes[n.id] = n;
    const remaining = bytes - studyBytes(s);
    if (remaining < 0)
      throw Error("Fixture target is too close to record overhead");
    n.text = "x".repeat(Math.min(100000, remaining));
  }
  return s;
}
