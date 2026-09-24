import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { loadCourses, loadTeaching } from "../scripts/content.ts";
import { validatePreservation } from "../src/content-schema.ts";
import {
  mediaSchema,
  validateTeaching,
  type TeachingMedia,
  type TeachingModule,
} from "../src/teaching-schema.ts";

const courses = await loadCourses();
const original = await loadTeaching(courses);
const course = courses.find((item) => item.id === "dbxfe")!;
const modules = original.modules.filter((item) => item.courseId === course.id);
const lessons = course.modules.flatMap((item) => item.lessons);
const expectedModules = [
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
];

test("the academy keeps the sixteen retained modules and every canonical study identity", async () => {
  const baseline = validatePreservation(
    JSON.parse(
      await readFile("content/preservation/dbxfe-study-hub.json", "utf8"),
    ),
    courses,
  );
  assert.equal(baseline.lessons.length, 43);
  assert.equal(baseline.lessons.flatMap((l) => l.cardIds).length, 144);
  assert.equal(baseline.lessons.flatMap((l) => l.questions).length, 96);
  // The retained sixteen modules stay registered; every registered course
  // module has exactly one teaching module and vice versa.
  const registered = new Set(course.modules.map((m) => m.id));
  for (const id of expectedModules)
    assert.ok(registered.has(id), `retained module ${id} is registered`);
  assert.deepEqual(new Set(modules.map((m) => m.moduleId)), registered);
  const taughtLessons = new Set(modules.flatMap((m) => m.lessonIds));
  for (const l of baseline.lessons)
    assert.ok(taughtLessons.has(l.id), `retained lesson ${l.id} is taught`);
  assert.deepEqual(taughtLessons, new Set(lessons.map((l) => l.id)));
  // Every preserved card keeps its mapping; the academy may add core cards
  // under new identities, and each of those must be mapped as well (the
  // validator refuses an unmapped lesson card).
  const mapped = new Set(
    modules.flatMap((m) => m.cardLinks.map((link) => link.cardId)),
  );
  const preservedCards = new Set(baseline.lessons.flatMap((l) => l.cardIds));
  for (const id of preservedCards)
    assert.ok(mapped.has(id), `Preserved card ${id} remains mapped to a beat`);
  const currentCards = lessons.flatMap((l) => l.cards.map((c) => c.id));
  assert.equal(new Set(currentCards).size, currentCards.length);
  for (const id of currentCards)
    assert.ok(mapped.has(id), `Current card ${id} is mapped to a beat`);
  assert.ok(
    currentCards.length >= preservedCards.size,
    "Card identities are added, never removed",
  );
  const extensionIds = modules.flatMap((m) =>
    m.extensionCards.map((c) => c.id),
  );
  assert.equal(extensionIds.length, modules.length * 4);
  assert.equal(new Set(extensionIds).size, extensionIds.length);
  for (const id of extensionIds)
    assert.ok(
      !lessons.some((l) => l.cards.some((c) => c.id === id)),
      `New extension must not replace canonical card ${id}`,
    );
});

test("every authored beat has a real visual, explained check, canonical anchor and handbook teaching", async () => {
  for (const m of modules) {
    const owned = course.modules.find(
      (item) => item.id === m.moduleId,
    )!.lessons;
    assert.deepEqual(new Set(m.lessonIds), new Set(owned.map((l) => l.id)));
    const checks = [
      ...lessons.flatMap((l) => l.questions),
      ...m.questions,
      ...m.selfQuestions,
    ];
    for (const beat of m.beats) {
      const label = `${m.moduleId}/${beat.id}`;
      const lesson = owned.find((l) => l.id === beat.lessonId);
      assert.ok(
        lesson?.sections.some((s) => s.id === beat.sectionId),
        `${label} belongs to its actual lesson`,
      );
      assert.ok(
        beat.explanation.trim() && beat.outcome.trim() && beat.recap.trim(),
        label,
      );
      assert.ok(
        beat.handbook.markdown.trim(),
        `${label} has handbook teaching`,
      );
      assert.ok(
        beat.handbook.sourceSectionIds.length,
        `${label} exposes canonical references`,
      );
      const visual = m.visuals.find((v) => v.id === beat.visualId)!;
      assert.ok(
        visual?.alt && visual.textEquivalent && visual.provenance,
        `${label} has accessible original visual evidence`,
      );
      const mechanisms = visual.states.map((s) =>
        JSON.stringify({
          nodes: s.nodes,
          connections: s.connections,
          table: s.table,
          equation: s.equation,
        }),
      );
      assert.equal(
        new Set(mechanisms).size,
        mechanisms.length,
        `${label} stages change the illustrated mechanism`,
      );
      assert.ok(beat.questionIds.length, `${label} has a check`);
      for (const id of beat.questionIds) {
        const check = checks.find((q) => q.id === id)!;
        assert.ok(check, `${label} check resolves`);
        // Reused canonical checks retain their original concept identities.
        // Their semantic fit to the new beat is assessed in EDITORIAL-REVIEW.md.
        assert.ok(check.conceptIds.length, `${id} has concept references`);
        if ("options" in check) {
          assert.equal(
            check.options.filter((o) => o.id === check.correctOptionId).length,
            1,
            `${id} has one intended answer`,
          );
          assert.equal(
            new Set(check.options.map((o) => o.text)).size,
            check.options.length,
            `${id} choices differ`,
          );
          assert.ok(
            check.options.every((o) => o.rationale.trim()),
            `${id} explains every option`,
          );
        } else
          assert.ok(
            check.modelAnswer.trim() && check.reasoning.trim(),
            `${id} has a self-check model and reasoning`,
          );
      }
    }
    assert.equal(
      m.extensionCards.length,
      4,
      `${m.moduleId} release extension contract`,
    );
    for (const card of m.extensionCards) {
      assert.ok(card.explanation.trim() && card.whyItMatters.trim(), card.id);
      const claims = [...course.claims, ...m.claims].filter((claim) =>
        card.claimIds.includes(claim.id),
      );
      assert.ok(
        claims.some(
          (claim) => claim.kind === "documented" && claim.sourceIds.length,
        ),
        `${card.id} has traceable primary evidence`,
      );
    }
    const media = original.media.filter(
      (v) => v.courseId === m.courseId && v.moduleId === m.moduleId,
    );
    // An access failure is unfinished review, not an editorial no-placement
    // conclusion. Both states leave media unplaced; only the latter carries
    // completed editorial evidence.
    if (!media.length) {
      const decisionPath = `docs/academy/media-decisions/${m.moduleId}.json`;
      const decision = JSON.parse(await readFile(decisionPath, "utf8")) as {
        moduleId: string;
        decision: string;
        reason: string;
        editorialEvidence?: string;
        remainingReview?: string;
        suggestedBeatId?: string;
        candidates: { url: string; reviewed: boolean }[];
      };
      assert.equal(decision.moduleId, m.moduleId, `${decisionPath} identity`);
      assert.ok(["no-placement", "blocked-review"].includes(decision.decision));
      if (decision.decision === "blocked-review")
        assert.ok(
          decision.remainingReview?.trim(),
          `${decisionPath} remaining work`,
        );
      else
        assert.ok(
          decision.editorialEvidence?.trim(),
          `${decisionPath} completed review`,
        );
      assert.ok(decision.reason.trim().length > 40, `${decisionPath} reason`);
      assert.ok(
        !decision.suggestedBeatId ||
          m.beats.some((b) => b.id === decision.suggestedBeatId),
        `${decisionPath} names a real beat`,
      );
      for (const candidate of decision.candidates)
        assert.ok(
          candidate.url.startsWith("https://") && candidate.reviewed === false,
          `${decisionPath} lists unreviewed leads only`,
        );
    }
    for (const item of media) {
      assert.ok(
        m.beats.some((b) => b.id === item.beatId),
        `${item.id} has an actual placement`,
      );
      assert.ok(
        m.visuals.some((v) => v.id === item.fallback.visualId),
        `${item.id} has an authored illustrated fallback`,
      );
      assert.ok(
        item.reviewedEvidence.trim() &&
          item.watchFor.trim() &&
          item.useNext.trim() &&
          item.playbackStatus.trim(),
        `${item.id} distinguishes actual evidence and usage`,
      );
      assert.ok(
        item.candidatesCompared.some((c) => c.decision.trim()),
        `${item.id} records candidate judgment`,
      );
    }
  }
});

type Mutation = (m: TeachingModule) => void;
const negatives: Record<string, Mutation> = {
  "unknown source": (m) => {
    m.claims[0].sourceIds = ["missing-source"];
  },
  "documented claim without evidence": (m) => {
    m.claims[0].kind = "documented";
    m.claims[0].sourceIds = [];
  },
  "unknown concept": (m) => {
    m.beats[0].conceptIds = ["missing-concept"];
  },
  "unknown visual": (m) => {
    m.beats[0].visualId = "missing-visual";
  },
  "unknown check": (m) => {
    m.beats[0].questionIds = ["missing-check"];
  },
  "wrong lesson section": (m) => {
    m.beats[0].sectionId = "missing-section";
  },
  "unknown handbook reference": (m) => {
    m.beats[0].handbook.sourceSectionIds = ["missing-section"];
  },
  "unknown optional bridge": (m) => {
    m.optionalBridgeLessonIds = ["missing-bridge"];
  },
  "unknown scenario": (m) => {
    m.scenarioIds = ["missing-scenario"];
  },
  "incomplete lesson ownership": (m) => {
    m.lessonIds.pop();
  },
  "duplicate lesson ownership": (m) => {
    m.lessonIds.push(m.lessonIds[0]);
  },
  "missing core-card mapping": (m) => {
    m.cardLinks.pop();
  },
  "duplicated core-card mapping": (m) => {
    m.cardLinks.push(m.cardLinks[0]);
  },
  "extension detached from beat": (m) => {
    m.extensionCards[0].beatId = "missing-beat";
  },
  "empty accessible visual": (m) => {
    m.visuals[0].textEquivalent = "";
  },
  "duplicate visual state": (m) => {
    m.visuals[0].states.push(structuredClone(m.visuals[0].states[0]));
  },
  "broken visual connection": (m) => {
    m.visuals[0].states[0].connections.push({
      from: "missing-node",
      to: "missing-node",
      label: "Broken",
    });
  },
  "unequal table cells": (m) => {
    m.visuals[0].states[0].table = { columns: ["A"], rows: [["One", "Two"]] };
  },
  "invalid correct option": (m) => {
    m.questions[0].correctOptionId = "missing-option";
  },
  "duplicate answer identity": (m) => {
    m.questions[0].options[1].id = m.questions[0].options[0].id;
  },
  "missing answer rationale": (m) => {
    m.questions[0].options[0].rationale = "";
  },
  "unresolved inline concept": (m) => {
    m.beats[0].explanation += " [[missing-concept|Term]]";
  },
  "missing beat media": (m) => {
    m.beats[0].mediaIds = ["missing-media"];
  },
  "missing applied-task beat": (m) => {
    m.appliedTask.beatIds = ["missing-beat"];
  },
};
const subject = original.modules.findIndex((m) => m.moduleId === "dbxfe-delta");
for (const [name, mutate] of Object.entries(negatives))
  test(`teaching rejects ${name}`, () => {
    const changed = structuredClone(original.modules);
    mutate(changed[subject]);
    assert.throws(() => validateTeaching(changed, courses, original.media));
  });

test("teaching identities cannot collide with preserved cards, scenarios, rubric rows, assets or downloads", () => {
  const ids = [
    lessons[0].cards[0].id,
    course.scenarios[0].id,
    course.scenarios[0].rubric[0].id,
    course.assets[0].id,
    course.downloads![0].id,
  ];
  for (const id of ids) {
    const changed = structuredClone(original.modules);
    changed[subject].extensionCards[0].id = id;
    assert.throws(
      () => validateTeaching(changed, courses, original.media),
      /Duplicate teaching identity/,
    );
  }
  assert.throws(
    () =>
      validateTeaching(
        [...original.modules, original.modules[0]],
        courses,
        original.media,
      ),
    /Duplicate teaching module/,
  );
  assert.throws(() =>
    validateTeaching(
      [{ schemaVersion: 1, courseId: course.id, moduleId: "dbxfe-delta" }],
      courses,
    ),
  );
});

for (const link of [
  "[Run](javascript:alert)",
  "[Run](vbscript:alert)",
  "[Open](data:text/html,hello)",
  "[File](file:///private.txt)",
  "[Relative](../../private.txt)",
  "[Credentials](https://name:secret@example.com/)",
  "![Tracking image](https://example.com/pixel.png)",
  '<iframe src="https://example.com"></iframe>',
  "[Absent lesson](#/lesson/missing-lesson)",
  "[Wrong section](#/lesson/dbxfe-m03-l02/missing-section)",
  "[Absent course](#/course/missing-course)",
  "[Absent scenario](#/practice/missing-scenario)",
  "[Absent beat](#/module/dbxfe-delta/missing-beat)",
  "[Absent module](#/module/missing-module)",
])
  test(`teaching rejects unsafe or unresolved authored link: ${link}`, () => {
    const changed = structuredClone(original.modules);
    changed[subject].beats[0].handbook.markdown += `\n${link}`;
    assert.throws(() => validateTeaching(changed, courses, original.media));
  });

const badMedia: Record<string, (m: TeachingMedia) => void> = {
  "credentials in canonical source": (m) => {
    m.url = "https://name:secret@example.com/video";
  },
  "credentials in candidate source": (m) => {
    m.candidatesCompared[0].url = "https://name:secret@example.com/video";
  },
  "untrusted player": (m) => {
    m.embedUrl = "https://example.com/embed/dQw4w9WgXcQ";
  },
  "player hostname suffix": (m) => {
    m.embedUrl = "https://www.youtube-nocookie.com.evil.test/embed/dQw4w9WgXcQ";
  },
  "verified player omitted": (m) => {
    m.embeddingStatus = "verified";
    delete m.embedUrl;
  },
  "segment starts after duration": (m) => {
    m.startSeconds = 11;
    m.durationSeconds = 10;
    m.endSeconds = null;
  },
  "segment ends before start": (m) => {
    m.startSeconds = 10;
    m.endSeconds = 5;
  },
  "segment ends after duration": (m) => {
    m.startSeconds = 0;
    m.endSeconds = 11;
    m.durationSeconds = 10;
  },
  "segment has end without start": (m) => {
    m.startSeconds = null;
    m.endSeconds = 1;
  },
  "unsafe fallback link": (m) => {
    m.fallback.markdown = "[Run](javascript:alert)";
  },
  "unsafe fallback frame": (m) => {
    m.fallback.markdown = '<iframe src="https://example.com"></iframe>';
  },
  "tracking image fallback": (m) => {
    m.fallback.markdown = "![Remote](https://example.com/pixel)";
  },
};
for (const [name, mutate] of Object.entries(badMedia))
  test(`media schema rejects ${name} before runtime caching`, () => {
    const changed = structuredClone(original.media[0]);
    mutate(changed);
    assert.equal(mediaSchema.safeParse(changed).success, false);
  });

test("media references resolve within the real placement and share authored-link validation", () => {
  for (const mutate of [
    (m: TeachingMedia) => {
      m.beatId = "missing-beat";
    },
    (m: TeachingMedia) => {
      m.fallback.visualId = "missing-visual";
    },
    (m: TeachingMedia) => {
      m.conceptIds = ["missing-concept"];
    },
    (m: TeachingMedia) => {
      m.fallback.markdown = "[Missing](#/lesson/missing-lesson)";
    },
    (m: TeachingMedia) => {
      m.fallback.markdown = "[[missing-concept|Missing]]";
    },
  ]) {
    const media = structuredClone(original.media);
    mutate(media[0]);
    assert.throws(() => validateTeaching(original.modules, courses, media));
  }
});

test("the shuffle illustration carries both plants from both input partitions", () => {
  const m = modules.find((m) => m.moduleId === "dbxfe-transformations")!;
  const visual = m.visuals.find(
    (v) => v.id === "dbxfe-transformations-plan-visual",
  )!;
  const after = visual.states.find((s) => s.id === "after")!;
  // Original fixture: partition one has North=12, South=5; partition two
  // has North=8, South=7. Both grouped results need both contributions.
  assert.deepEqual(
    new Set(after.connections.map((e) => `${e.from}/${e.to}`)),
    new Set(["p-one/north", "p-one/south", "p-two/north", "p-two/south"]),
  );
  assert.match(visual.textEquivalent, /South contribution: 5/);
  assert.match(visual.textEquivalent, /North contribution: 8/);
});

test("the cutover illustration sends rollback toward the retained path", () => {
  const m = modules.find((m) => m.moduleId === "dbxfe-m08")!;
  const visual = m.visuals.find((v) => v.id === "dbxfe-m08-visual-cutover")!;
  const switched = visual.states.find((s) => s.id === "change")!;
  const rollback = switched.connections.find((e) => /rollback/i.test(e.label))!;
  assert.equal(rollback.from, "node-new");
  assert.equal(rollback.to, "node-old");
});

test("an unrelated content-only fixture supports arbitrary beat and extension counts without Databricks IDs", async () => {
  const root = "tests/fixtures/photography/content";
  const photoCourses = await loadCourses(root);
  const photo = await loadTeaching(photoCourses, root);
  assert.equal(photo.modules.length, 2);
  assert.ok(!JSON.stringify(photo).includes("dbxfe"));
  for (const count of [0, 1, 5]) {
    const module = structuredClone(photo.modules[0]);
    module.beats = [module.beats[0]];
    module.beats[0].mediaIds = [];
    module.cardLinks = module.cardLinks.map((link) => ({
      ...link,
      beatId: module.beats[0].id,
    }));
    module.appliedTask.beatIds = [module.beats[0].id];
    module.recap.visualId = module.beats[0].visualId;
    const example = module.extensionCards[0];
    module.extensionCards = Array.from({ length: count }, (_, i) => ({
      ...example,
      id: `photo-arbitrary-extension-${i}`,
    }));
    assert.equal(
      validateTeaching([module], photoCourses).modules[0].extensionCards.length,
      count,
    );
    module.beats.push({
      ...structuredClone(module.beats[0]),
      id: "photo-additional-teaching-beat",
      version: "2.0.0",
    });
    assert.equal(
      validateTeaching([module], photoCourses).modules[0].beats.length,
      2,
    );
  }
});
