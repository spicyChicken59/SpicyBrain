import type {
  Card,
  CaseAnalysis,
  Course,
  Guide,
  Lab,
  Lesson,
  Question,
  Scenario,
  Section,
} from "./content-schema";

/**
 * The initial bundle carries the catalog tier: every identity, title, mapping
 * and number the interface needs to navigate, count and schedule. Prose,
 * card text, question text and scenario bodies live in the body tier under
 * `public/teaching/bodies/<id>.json`, fetched on demand and validated
 * against these references before use. A full `Course` is assignable to a
 * `CatalogCourse`, so build-time validators accept either.
 */
export type CatalogSection = Omit<Section, "markdown">;
/** What scheduling and navigation read; concept and claim ids travel with the card text. */
export type CardRef = Pick<Card, "id" | "revision" | "lessonId" | "sectionId">;
export type QuestionRef = Pick<Question, "id" | "revision" | "conceptIds">;
export type CatalogLesson = Omit<Lesson, "sections" | "cards" | "questions"> & {
  sections: CatalogSection[];
  cards: CardRef[];
  questions: QuestionRef[];
};
export type CatalogModule = Omit<Course["modules"][number], "lessons"> & {
  lessons: CatalogLesson[];
};
export type CatalogScenario = Omit<
  Scenario,
  "context" | "task" | "model" | "reasoning" | "disclosures"
>;
export type CatalogLab = Omit<Lab, "body">;
export type CatalogGuide = Omit<Guide, "body">;
export type CatalogCase = Omit<CaseAnalysis, "body">;
export type CatalogCourse = Omit<
  Course,
  "modules" | "scenarios" | "labs" | "guides" | "cases"
> & {
  modules: CatalogModule[];
  scenarios: CatalogScenario[];
  labs?: CatalogLab[];
  guides?: CatalogGuide[];
  cases?: CatalogCase[];
};
/** Runtime index entry for a researched extension card; its text stays in the module JSON. */
export type ExtensionCardRef = CardRef & { beatId: string };

export type LessonBody = {
  kind: "lesson";
  id: string;
  contentVersion: string;
  /** Section ID → Markdown, one entry per catalog section. */
  sections: Record<string, string>;
  questions: Question[];
  cards: Card[];
};
export type ScenarioBody = Pick<
  Scenario,
  "id" | "context" | "task" | "model" | "reasoning" | "disclosures"
> & { kind: "scenario" };
export type LabBody = { kind: "lab"; id: string; body: Lab["body"] };
export type GuideBody = { kind: "guide"; id: string; body: Guide["body"] };
export type CaseBody = { kind: "case"; id: string; body: CaseAnalysis["body"] };
export type ContentBody =
  LessonBody | ScenarioBody | LabBody | GuideBody | CaseBody;
export type BodyKind = ContentBody["kind"];
