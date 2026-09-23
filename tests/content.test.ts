import { test } from "node:test";
import assert from "node:assert/strict";
import { cp, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { loadCourses, verifyDesign } from "../scripts/content.ts";
import {
  validateCourses,
  validatePreservation,
  type Course,
} from "../src/content-schema.ts";
const original = await loadCourses();
const preservation = JSON.parse(
  await readFile("content/preservation/dbxfe-launch.json", "utf8"),
);
test("launch inventory and stable IDs are preserved while additional lessons are allowed", async () => {
  await verifyDesign();
  const baseline = validatePreservation(preservation, original);
  assert.equal(baseline.moduleIds.length, 12);
  assert.equal(baseline.lessons.length, 36);
  assert.equal(
    baseline.lessons.flatMap((lesson) => lesson.cardIds).length,
    108,
  );
  assert.equal(
    baseline.lessons.flatMap((lesson) => lesson.questions).length,
    72,
  );
  assert.equal(baseline.scenarioIds.length, 13);
  assert.equal(baseline.assetIds.length, 12);
  const c = original.find((course) => course.id === baseline.courseId)!;
  assert.equal(c.scenarios.filter((s) => s.isCapstone).length, 1);
  // Teaching modules may split an original module. Preserve every original
  // diagram identity rather than requiring each new partition to reuse an image.
  assert.ok(c.assets.length >= 18);
  // The academy grows the module list; the retained sixteen must remain.
  assert.ok(c.modules.length >= 16);
  for (const id of [
    "dbxfe-m01",
    "dbxfe-m02",
    "dbxfe-m03",
    "dbxfe-delta",
    "dbxfe-transformations",
    "dbxfe-m04",
    "dbxfe-orchestration",
    "dbxfe-m05",
    "dbxfe-m06",
    "dbxfe-m07",
    "dbxfe-genai",
    "dbxfe-m08",
    "dbxfe-m09",
    "dbxfe-m10",
    "dbxfe-m11",
    "dbxfe-m12",
  ])
    assert.ok(
      c.modules.some((m) => m.id === id),
      `retained module ${id}`,
    );
  const current = validatePreservation(
    JSON.parse(
      await readFile("content/preservation/dbxfe-study-hub.json", "utf8"),
    ),
    original,
  );
  assert.equal(current.lessons.length, 43);
  assert.equal(current.lessons.flatMap((l) => l.cardIds).length, 144);
  assert.equal(current.lessons.flatMap((l) => l.questions).length, 96);
  for (const m of c.modules) {
    for (const l of m.lessons) {
      assert.ok(l.cards.length >= 3);
      assert.ok(l.questions.length >= 2);
      assert.ok(
        l.sections.reduce((n, s) => n + s.markdown.split(/\s+/).length, 0) >
          300,
      );
    }
  }
});
test("preservation rejects an original lesson, section or assessment disappearing even if counts are replaced", () => {
  for (const kind of [
    "lesson",
    "section",
    "card",
    "question",
    "option",
    "asset",
    "scenario",
    "module",
  ] as const) {
    const changed = structuredClone(original);
    const course = changed[0],
      lesson = course.modules[0].lessons[0];
    const item =
      kind === "lesson"
        ? lesson
        : kind === "section"
          ? lesson.sections[0]
          : kind === "card"
            ? lesson.cards[0]
            : kind === "question"
              ? lesson.questions[0]
              : kind === "option"
                ? lesson.questions[0].options[0]
                : kind === "asset"
                  ? course.assets[0]
                  : kind === "scenario"
                    ? course.scenarios[0]
                    : course.modules[0];
    item.id = "replacement-new-id";
    assert.throws(
      () => validatePreservation(preservation, changed),
      /preserved/i,
    );
  }
});
test("flexible teaching order accepts distinct stable section IDs without a customer section", () => {
  const changed = structuredClone(original),
    lesson = changed[0].modules[0].lessons[0];
  lesson.teachingFormat = "flexible";
  lesson.sections[0].kind = "exercise";
  lesson.sections[1].kind = "solution";
  lesson.sections.find((section) => section.kind === "customer")!.kind =
    "reference";
  lesson.sections.reverse();
  assert.equal(validateCourses(changed).length, original.length);
});
test("flexible teaching separates an attempted exercise from a revealed solution", () => {
  const courses = structuredClone(original);
  const lesson = courses[0].modules
    .flatMap((module) => module.lessons)
    .find((lesson) => lesson.teachingFormat === "flexible")!;
  assert.ok(lesson, "The authored technical packages use flexible teaching");
  for (const kind of ["solution", "exercise"] as const) {
    const changed = structuredClone(courses);
    const target = changed[0].modules
      .flatMap((module) => module.lessons)
      .find((item) => item.id === lesson.id)!;
    for (const section of target.sections)
      if (
        section.kind === kind ||
        (kind === "exercise" && section.kind === "try")
      )
        section.kind = "reference";
    assert.throws(
      () => validateCourses(changed),
      /separate exercise and solution/,
    );
  }
});
// Explicit negative fixtures are named transformations of valid authored content. Each must fail.
const negatives: Record<string, (c: Course) => void> = {
  "missing metadata": (c) => {
    c.title = "";
  },
  "missing teaching section": (c) => {
    c.modules[0].lessons[0].sections.pop();
  },
  "duplicate ID": (c) => {
    c.modules[0].lessons[1].id = c.modules[0].lessons[0].id;
  },
  "prerequisite cycle": (c) => {
    c.modules[0].prerequisiteIds = [c.modules[1].id];
    c.modules[1].prerequisiteIds = [c.modules[0].id];
  },
  "invalid prerequisite": (c) => {
    c.prerequisiteIds = ["missing-lesson"];
  },
  "broken internal section": (c) => {
    c.modules[0].lessons[0].sections[0].markdown +=
      " [Bad](#/lesson/dbxfe-m01-l01/removed-section)";
  },
  "broken concept": (c) => {
    c.modules[0].lessons[0].cards[0].conceptIds = ["missing-concept"];
  },
  "missing asset reference": (c) => {
    c.modules[0].lessons[0].sections[0].assetIds = ["missing-asset"];
  },
  "missing text alternative": (c) => {
    c.assets[0].alt = "";
  },
  "malformed answer set": (c) => {
    c.modules[0].lessons[0].questions[0].options[1].id =
      c.modules[0].lessons[0].questions[0].options[0].id;
  },
  "invalid correct ID": (c) => {
    c.modules[0].lessons[0].questions[0].correctOptionId = "missing-option";
  },
  "missing rationale": (c) => {
    c.modules[0].lessons[0].questions[0].options[0].rationale = "";
  },
  "missing source": (c) => {
    c.claims[0].sourceIds = ["missing-source"];
  },
  "unsafe asset path": (c) => {
    c.assets[0].path = "../escape.svg";
  },
  "unsafe URL scheme": (c) => {
    c.modules[0].lessons[0].sections[0].markdown += " [Bad](javascript:alert)";
  },
  "raw executable HTML": (c) => {
    c.modules[0].lessons[0].sections[0].markdown += "<script>alert(1)</script>";
  },
  "unresolved marker": (c) => {
    c.modules[0].lessons[0].sections[0].markdown += " [AUTHOR_TODO]";
  },
  "per-lesson shortage": (c) => {
    c.modules[0].lessons[0].cards.pop();
  },
  "module distribution": (c) => {
    c.modules[0].lessons.pop();
  },
  "missing capstone": (c) => {
    c.scenarios = c.scenarios.filter((s) => !s.isCapstone);
  },
};
for (const [name, breakIt] of Object.entries(negatives))
  test(`reject ${name}`, () => {
    const c = structuredClone(original[0]);
    breakIt(c);
    assert.throws(() => validateCourses([c]));
  });
test("a legitimate explanation of placeholder terminology is not rejected", () => {
  const c = structuredClone(original[0]);
  c.modules[0].lessons[0].sections[0].markdown +=
    " A placeholder is a temporary value; replace it before deploying.";
  assert.equal(validateCourses([c]).length, 1);
});
test("missing actual asset and missing Markdown marker fail the disk loader", async () => {
  const temp = await mkdtemp(join(tmpdir(), "spicybrain-content-"));
  try {
    await cp("content", temp, { recursive: true });
    await rm(join(temp, "assets/dbxfe-m01-diagram.svg"));
    await assert.rejects(loadCourses(temp));
    await cp(
      "content/assets/dbxfe-m01-diagram.svg",
      join(temp, "assets/dbxfe-m01-diagram.svg"),
    );
    const path = join(temp, "courses/dbxfe/lessons/dbxfe-m01-l01.md");
    await writeFile(
      path,
      (await readFile(path, "utf8")).replace("<!-- section:why -->", ""),
    );
    await assert.rejects(loadCourses(temp));
  } finally {
    await rm(temp, { recursive: true, force: true });
  }
});
test("synthetic input deduplication/versioning/quarantine gives the published expected rows and aggregates", async () => {
  const csv = (
    await readFile("content/courses/dbxfe/data/inspection-events.csv", "utf8")
  )
    .trim()
    .split("\n")
    .slice(1)
    .map((l) => {
      const [event, inspection, version, plant, units, defects] = l.split(",");
      return {
        event,
        inspection,
        version: +version,
        plant,
        units: +units,
        defects: +defects,
      };
    });
  const unique = [...new Map(csv.map((r) => [r.event, r])).values()],
    latest = new Map<string, (typeof csv)[number]>(),
    quarantine = [];
  for (const r of unique) {
    if (r.units < 0) {
      quarantine.push({
        inspection_id: r.inspection,
        reason: "negative inspected_units",
      });
      continue;
    }
    if (
      !latest.has(r.inspection) ||
      latest.get(r.inspection)!.version < r.version
    )
      latest.set(r.inspection, r);
  }
  const accepted = [...latest.values()]
    .sort((a, b) => a.inspection.localeCompare(b.inspection))
    .map((r) => ({
      inspection_id: r.inspection,
      version: r.version,
      inspected_units: r.units,
      defective_units: r.defects,
    }));
  const units = accepted.reduce((n, r) => n + r.inspected_units, 0),
    defects = accepted.reduce((n, r) => n + r.defective_units, 0);
  assert.deepEqual(
    {
      accepted,
      quarantine,
      totals: {
        inspected_units: units,
        defective_units: defects,
        defect_rate: defects / units,
      },
    },
    JSON.parse(
      await readFile("content/courses/dbxfe/data/expected-output.json", "utf8"),
    ),
  );
});
test("hypothetical value sensitivity, break-even and published six-hour exercise", () => {
  const net = (h: number) => h * 48 * 60 - 12000 - 15000;
  assert.deepEqual([5, 10, 15].map(net), [-12600, 1800, 16200]);
  assert.equal(net(6), -9720);
  assert.equal(27000 / (48 * 60), 9.375);
});
