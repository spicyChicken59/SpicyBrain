import { test } from "node:test";
import assert from "node:assert/strict";
import { loadCourses } from "../scripts/content.ts";
import { validatePaths, type LearningPath } from "../src/content-schema.ts";
import {
  orderedPathLessons,
  pathForLesson,
  pathLessonHref,
  pathNeighbors,
  referenceHref,
} from "../src/paths.ts";

const courses = await loadCourses();
const first = courses[0].modules[0].lessons[0],
  second = courses[0].modules[0].lessons[1],
  bridge = courses[0].modules[0].lessons[2];
const fixture: LearningPath = {
  schemaVersion: 1,
  id: "test-path",
  title: "A deliberate path",
  summary: "A content-only sequence.",
  outcomes: ["Explain a useful concept."],
  startingAssumptions: ["No previous activity is inferred."],
  defaultStart: true,
  groups: [
    {
      id: "test-path-group",
      title: "Start here",
      purpose: "Build a mental model.",
      lessonIds: [first.id, second.id],
    },
  ],
  prerequisites: [],
  optionalBridges: [],
  playbooks: [
    {
      id: "test-path-playbook",
      title: "A task reference",
      summary: "Open the canonical explanation.",
      targets: [
        {
          courseId: courses[0].id,
          lessonId: first.id,
          sectionId: first.sections[0].id,
          label: "The explanation",
        },
      ],
    },
  ],
};
test("content-defined path resolves canonical lessons and section/scenario references", () => {
  const path = validatePaths([fixture], courses)[0];
  assert.deepEqual(orderedPathLessons(path), [first.id, second.id]);
  assert.deepEqual(pathNeighbors(path, first.id), {
    previous: undefined,
    next: second.id,
  });
  assert.deepEqual(pathNeighbors(path, second.id), {
    previous: first.id,
    next: undefined,
  });
  assert.equal(pathForLesson([path], first.id), undefined);
  assert.equal(pathForLesson([path], first.id, "removed-path"), undefined);
  assert.equal(pathForLesson([path], first.id, path.id), path);
  assert.equal(
    pathLessonHref(path.id, first.id, first.sections[0].id),
    `#/lesson/${first.id}/${first.sections[0].id}?path=${path.id}`,
  );
  assert.equal(
    referenceHref(path.playbooks[0].targets[0], path.id),
    pathLessonHref(path.id, first.id, first.sections[0].id),
  );
  assert.equal(
    referenceHref({
      courseId: courses[0].id,
      scenarioId: courses[0].scenarios[0].id,
      label: "Practice",
    }),
    `#/practice/${courses[0].scenarios[0].id}`,
  );
});
test("an optional bridge returns to its explicitly supported topic", () => {
  const path = structuredClone(fixture);
  path.optionalBridges = [
    {
      lessonId: bridge.id,
      beforeLessonIds: [second.id],
      explanation: "Optional support.",
    },
  ];
  // Path navigation itself does not write a completion or infer mastery.
  assert.deepEqual(pathNeighbors(path, bridge.id), {
    previous: undefined,
    next: second.id,
  });
  assert.equal(pathForLesson([path], bridge.id, path.id), path);
});
const negatives: Record<string, (path: LearningPath) => void> = {
  "duplicate path ID": (path) => {
    path.id = first.id;
  },
  "duplicate group ID": (path) => {
    path.groups[0].id = path.id;
  },
  "missing canonical lesson": (path) => {
    path.groups[0].lessonIds[0] = "removed-lesson";
  },
  "duplicate canonical lesson": (path) => {
    path.groups[0].lessonIds.push(first.id);
  },
  cycle: (path) => {
    path.prerequisites = [
      { lessonId: first.id, requiredLessonId: second.id, explanation: "One" },
      { lessonId: second.id, requiredLessonId: first.id, explanation: "Two" },
    ];
  },
  "bridge self-cycle": (path) => {
    path.optionalBridges = [
      {
        lessonId: first.id,
        beforeLessonIds: [first.id],
        explanation: "Invalid",
      },
    ];
  },
  "missing prerequisite": (path) => {
    path.prerequisites = [
      {
        lessonId: first.id,
        requiredLessonId: "removed-lesson",
        explanation: "Missing",
      },
    ];
  },
  "missing bridge target": (path) => {
    path.optionalBridges = [
      {
        lessonId: bridge.id,
        beforeLessonIds: ["removed-lesson"],
        explanation: "Missing",
      },
    ];
  },
  "missing playbook section": (path) => {
    path.playbooks[0].targets[0].sectionId = "removed-section";
  },
  "missing playbook course": (path) => {
    path.playbooks[0].targets[0].courseId = "removed-course";
  },
  "ambiguous playbook reference": (path) => {
    path.playbooks[0].targets[0].scenarioId = courses[0].scenarios[0].id;
  },
  "orphan section": (path) => {
    delete path.playbooks[0].targets[0].lessonId;
  },
};
for (const [name, mutate] of Object.entries(negatives))
  test(`path validator rejects ${name}`, () => {
    const path = structuredClone(fixture);
    mutate(path);
    assert.throws(() => validatePaths([path], courses));
  });
test("only one content-defined default-start path is allowed", () => {
  const next = structuredClone(fixture);
  next.id = "other-path";
  next.groups[0].id = "other-path-group";
  next.playbooks[0].id = "other-path-playbook";
  assert.throws(() => validatePaths([fixture, next], courses), /default-start/);
});
test("paths can reference an unrelated course without engine registration", async () => {
  const photography = await loadCourses("tests/fixtures/photography/content");
  const path = structuredClone(fixture),
    photo = photography[0].modules[0].lessons[0];
  path.groups[0].lessonIds.push(photo.id);
  path.playbooks[0].targets.push({
    courseId: photography[0].id,
    lessonId: photo.id,
    sectionId: photo.sections[0].id,
    label: "An unrelated subject",
  });
  assert.equal(
    validatePaths(
      [path],
      [...courses, ...photography],
    )[0].groups[0].lessonIds.at(-1),
    photo.id,
  );
});
test("path prerequisites cannot introduce a cycle through an existing module", () => {
  const changed = structuredClone(courses),
    path = structuredClone(fixture);
  changed[0].modules[0].prerequisiteIds = [first.id];
  changed[0].modules[0].lessons[1].prerequisiteIds = [changed[0].modules[0].id];
  path.prerequisites = [
    {
      lessonId: first.id,
      requiredLessonId: second.id,
      explanation: "This would close a cycle through a module.",
    },
  ];
  assert.throws(() => validatePaths([path], changed), /Cyclic/);
});
