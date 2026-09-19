import "fake-indexeddb/auto";
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { openDB, deleteDB } from "idb";
import {
  ALGORITHM,
  DAY,
  StudyStore,
  applyReview,
  emptyState,
  exportText,
  importPreview,
  mergeStates,
  migrateState,
  parseImport,
  reviewQueue,
  scheduleRating,
  validateState,
} from "../src/study.ts";
import type { Card } from "../src/content-schema.ts";
const at = "2026-03-08T06:59:59.000Z";
const card: Card = {
  id: "test-card",
  lessonId: "test-lesson",
  sectionId: "test-section",
  revision: "1",
  prompt: "Recall?",
  answer: "Answer",
  explanation: "Why",
  conceptIds: ["test-concept"],
  claimIds: [],
};
const note = (text = "Original", updatedAt = at) => ({
  id: "test-note",
  courseId: "test-course",
  lessonId: "test-lesson",
  sectionId: "test-section",
  text,
  question: true,
  createdAt: at,
  updatedAt,
});
function completeState() {
  const s = applyReview(
    emptyState(at),
    card,
    "test-course",
    "Again",
    "review-one",
    at,
  );
  s.notes["test-note"] = note();
  s.drafts["test-draft"] = {
    id: "test-draft",
    courseId: "test-course",
    targetId: "test-scenario",
    text: "Scenario draft",
    createdAt: at,
    updatedAt: at,
  };
  s.bookmarks["test-bookmark"] = {
    id: "test-bookmark",
    courseId: "test-course",
    lessonId: "test-lesson",
    sectionId: "test-section",
    active: true,
    updatedAt: at,
  };
  s.completions["test-complete"] = {
    id: "test-complete",
    courseId: "test-course",
    lessonId: "test-lesson",
    completed: true,
    contentVersion: "1.0",
    updatedAt: at,
  };
  s.attempts["test-attempt"] = {
    id: "test-attempt",
    courseId: "test-course",
    lessonId: "test-lesson",
    questionId: "test-question",
    questionRevision: "1",
    contentVersion: "1.0",
    at,
    optionId: "option-b",
    correctOptionId: "option-a",
    correct: false,
    conceptIds: ["test-concept"],
    snapshot: {
      prompt: "What?",
      options: [
        { id: "option-b", text: "No", rationale: "Incorrect because…" },
        { id: "option-a", text: "Yes", rationale: "Correct because…" },
      ],
    },
  };
  s.extraPractice["test-extra"] = {
    id: "test-extra",
    courseId: "test-course",
    lessonId: "test-lesson",
    cardId: card.id,
    revision: "1",
    at,
  };
  s.assessments["test-assess"] = {
    id: "test-assess",
    courseId: "test-course",
    targetId: "test-scenario",
    at,
    ratings: { "test-dimension": "partial" },
    kind: "self-assessment",
  };
  s.resume = {
    courseId: "test-course",
    lessonId: "test-lesson",
    sectionId: "test-section",
    offset: 124,
    updatedAt: at,
  };
  s.positions["test-lesson"] = s.resume;
  s.disclosureAccepted = true;
  return validateState(s);
}
test("baseline schema 2 migrates every record unchanged, persists schema 3, and round-trips path context", async () => {
  const current = completeState();
  const old = { ...current, schemaVersion: 2 };
  const migrated = migrateState(old);
  assert.deepEqual(migrated, current);
  const name = `baseline-v2-${crypto.randomUUID()}`;
  const db = await openDB(name, 2, {
    upgrade(db) {
      db.createObjectStore("study");
    },
  });
  await db.put("study", old, "root");
  db.close();
  const store = new StudyStore(name);
  await store.init();
  assert.deepEqual(store.getSnapshot().data, current);
  await store.change((s) => ({
    ...s,
    resume: {
      ...s.resume!,
      pathId: "synthetic-path",
      updatedAt: "2026-03-09T06:59:59.000Z",
    },
    positions: {
      ...s.positions,
      "test-lesson": {
        ...s.positions["test-lesson"],
        pathId: "synthetic-path",
        updatedAt: "2026-03-09T06:59:59.000Z",
      },
    },
  }));
  const withPath = store.getSnapshot().data;
  assert.deepEqual(parseImport(exportText(withPath)), withPath);
  assert(
    importPreview(emptyState(), withPath, new Set()).unknown.includes(
      "synthetic-path",
    ),
  );
  assert.deepEqual(mergeStates(withPath, migrated).resume, withPath.resume);
  store.close();
  const reopened = new StudyStore(name);
  await reopened.init();
  assert.deepEqual(reopened.getSnapshot().data, withPath);
  reopened.close();
  await deleteDB(name);
  const illegalLegacy = {
    ...old,
    resume: { ...old.resume!, pathId: "not-a-v2-field" },
  };
  assert.throws(() => migrateState(illegalLegacy));
});
test("all schedule ratings, rounding, ceiling and exact 24-hour DST boundaries", () => {
  for (const [rating, first, next] of [
    ["Again", 0, 0],
    ["Hard", 1, 5],
    ["Good", 3, 8],
    ["Easy", 7, 12],
  ] as const) {
    for (const [previous, days] of [
      [0, first],
      [4, next],
    ]) {
      const result = scheduleRating(previous, rating, at);
      assert.equal(result.intervalDays, days);
      assert.equal(
        Date.parse(result.dueAt) - Date.parse(at),
        rating === "Again" ? 600000 : days * DAY,
      );
    }
    assert.ok(scheduleRating(365, rating, at).intervalDays <= 365);
  }
  assert.equal(scheduleRating(1, "Hard", at).intervalDays, 2);
  assert.equal(scheduleRating(364, "Hard", at).intervalDays, 365);
  assert.equal(scheduleRating(200, "Easy", at).intervalDays, 365);
  assert.equal(scheduleRating(0, "Good", at).dueAt, "2026-03-11T06:59:59.000Z");
  assert.throws(() => scheduleRating(-1, "Good", at));
});
test("due before/at/after, order by due and stable ID, session cap leaves remainder; new separate", () => {
  let s = emptyState();
  const cards = ["test-c", "test-a", "test-b"].map((id) => ({ ...card, id }));
  for (const c of cards)
    s = applyReview(s, c, "test-course", "Again", `review-${c.id}`, at);
  assert.equal(reviewQueue(cards, s, "2026-03-08T07:09:58.999Z").length, 0);
  assert.deepEqual(
    reviewQueue(cards, s, "2026-03-08T07:09:59.000Z", 2).map((c) => c.id),
    ["test-a", "test-b"],
  );
  assert.equal(reviewQueue(cards, s, "2026-03-08T07:10:00.000Z", 30).length, 3);
  assert.equal(
    reviewQueue([{ ...card, id: "unseen-card" }], s, "2099-01-01T00:00:00.000Z")
      .length,
    0,
  );
  assert.equal(Object.keys(s.reviews).length, 3);
});
test("immutable event deduplication, material revision flagged until reviewed, cosmetic edit retains schedule", () => {
  const s = applyReview(
    emptyState(),
    card,
    "test-course",
    "Good",
    "event-one",
    at,
  );
  assert.deepEqual(
    applyReview(s, card, "test-course", "Easy", "event-one", at),
    s,
  );
  assert.equal(s.reviews["event-one"].algorithmVersion, ALGORITHM);
  assert.equal(
    reviewQueue([{ ...card, prompt: "Typo corrected" }], s, at).length,
    0,
  );
  assert.equal(reviewQueue([{ ...card, revision: "2" }], s, at).length, 1);
  const next = applyReview(
    s,
    { ...card, revision: "2" },
    "test-course",
    "Hard",
    "event-two",
    at,
  );
  assert.equal(reviewQueue([{ ...card, revision: "2" }], next, at).length, 0);
  assert.equal(next.reviews["event-one"].revision, "1");
  assert.equal(Object.keys(next.reviews).length, 2);
});
test("complete versioned round trip preserves every record; stable option IDs survive reorder", () => {
  const s = completeState();
  assert.deepEqual(parseImport(exportText(s, at)), s);
  const a = s.attempts["test-attempt"];
  a.snapshot.options.reverse();
  assert.equal(validateState(s).attempts["test-attempt"].correct, false);
  assert.equal(
    a.snapshot.options.find((o) => o.id === a.correctOptionId)?.text,
    "Yes",
  );
});
test("merge preserves conflicting note and draft text, deterministic mutable state and immutable IDs; repeat idempotent", () => {
  const local = completeState(),
    incoming = completeState();
  incoming.notes["test-note"] = note("Other text", "2026-03-09T00:00:00.000Z");
  incoming.drafts["test-draft"].text = "Other draft";
  incoming.settings = {
    ...incoming.settings,
    theme: "dark",
    updatedAt: "2026-03-10T00:00:00.000Z",
  };
  const merged = mergeStates(local, incoming);
  assert.deepEqual(
    new Set(Object.values(merged.notes).map((n) => n.text)),
    new Set(["Original", "Other text"]),
  );
  assert.equal(Object.keys(merged.drafts).length, 2);
  assert.equal(merged.settings.theme, "dark");
  assert.equal(Object.keys(merged.reviews).length, 1);
  assert.deepEqual(mergeStates(merged, incoming), merged);
  assert.equal(importPreview(local, incoming, new Set()).conflicts, 2);
  assert.ok(
    importPreview(local, incoming, new Set()).unknown.includes("test-lesson"),
  );
  const bad = completeState();
  bad.attempts["test-attempt"].snapshot.prompt = "Different immutable evidence";
  assert.throws(() => mergeStates(local, bad), /Conflicting immutable/);
  assert.equal(local.notes["test-note"].text, "Original");
});
test("invalid/future/oversize/schedule corruption rejected without mutating state; unknown references retained as plain text", () => {
  const s = completeState();
  s.notes["test-note"].text = "<script>alert(1)</script>";
  assert.equal(
    parseImport(exportText(s)).notes["test-note"].text,
    s.notes["test-note"].text,
  );
  for (const raw of [
    "{",
    JSON.stringify({
      format: "SpicyBrain study data",
      exportedAt: at,
      state: { ...s, schemaVersion: 99 },
    }),
    "x".repeat(5_000_001),
  ])
    assert.throws(() => parseImport(raw));
  const bad = structuredClone(s);
  bad.schedules[card.id].intervalDays = 100;
  assert.throws(() => validateState(bad));
  assert.equal(s.schemaVersion, 3);
});
test("synthetic v1 fixture migrates both export and actual IndexedDB version and survives reopen", async () => {
  const old = JSON.parse(
    await readFile(
      new URL("./fixtures/study-v1.json", import.meta.url),
      "utf8",
    ),
  );
  const name = `migration-${crypto.randomUUID()}`;
  const db = await openDB(name, 1, {
    upgrade(db) {
      db.createObjectStore("study");
    },
  });
  await db.put("study", old, "root");
  db.close();
  const store = new StudyStore(name);
  await store.init();
  const migrated = migrateState(old);
  assert.deepEqual(store.getSnapshot().data, migrated);
  assert.deepEqual(
    parseImport(
      JSON.stringify({
        format: "SpicyBrain study data",
        exportedAt: at,
        state: old,
      }),
    ),
    migrated,
  );
  store.close();
  const check = await openDB(name, 2);
  assert.equal((await check.get("study", "root")).schemaVersion, 3);
  assert.equal(
    (await check.get("study", "root")).notes["synthetic-note"].text,
    old.notes["synthetic-note"].text,
  );
  assert.deepEqual((await check.get("study", "root")).reviews, old.reviews);
  check.close();
  await deleteDB(name);
});
test("quota failure preserves pending final edit; recovery/retry saves; replacement abort leaves all old records", async () => {
  const name = `failure-${crypto.randomUUID()}`;
  let fail = false;
  const store = new StudyStore(name, () => {
    if (fail) throw new DOMException("Quota", "QuotaExceededError");
  });
  await store.init();
  await store.replace(completeState());
  fail = true;
  await store.change((s) => ({
    ...s,
    notes: { ...s.notes, "test-note": note("Last typed character!") },
  }));
  assert.equal(store.getSnapshot().status, "unsaved");
  assert.equal(
    parseImport(exportText(store.getSnapshot().data)).notes["test-note"].text,
    "Last typed character!",
  );
  fail = false;
  await store.change((s) => s);
  assert.equal(store.getSnapshot().status, "saved");
  fail = true;
  await assert.rejects(store.replace(emptyState()));
  assert.equal(
    store.getSnapshot().data.notes["test-note"].text,
    "Last typed character!",
  );
  store.close();
  const reopened = new StudyStore(name);
  await reopened.init();
  assert.equal(
    reopened.getSnapshot().data.notes["test-note"].text,
    "Last typed character!",
  );
  assert.equal(Object.keys(reopened.getSnapshot().data.reviews).length, 1);
  reopened.close();
  await deleteDB(name);
});
test("concurrent writers retain distinct notes and atomic review records; rapid edits keep final text", async () => {
  const name = `writers-${crypto.randomUUID()}`,
    one = new StudyStore(name),
    two = new StudyStore(name);
  await one.init();
  await two.init();
  await Promise.all([
    one.change((s) => ({ ...s, notes: { ...s.notes, "test-note": note() } })),
    two.change((s) =>
      applyReview(s, card, "test-course", "Easy", "event-two", at),
    ),
  ]);
  for (let i = 0; i < 30; i++)
    void one.change((s) => ({
      ...s,
      notes: { ...s.notes, "test-note": note(`Text ${i}`) },
    }));
  await one.flush();
  one.close();
  two.close();
  const check = new StudyStore(name);
  await check.init();
  assert.equal(check.getSnapshot().data.notes["test-note"].text, "Text 29");
  assert.equal(
    check.getSnapshot().data.schedules[card.id].lastEventId,
    "event-two",
  );
  assert.equal(check.getSnapshot().data.reviews["event-two"].intervalDays, 7);
  check.close();
  await deleteDB(name);
});
test("blocked upgrade preserves text entered while blocked then commits when released", async () => {
  const name = `blocked-${crypto.randomUUID()}`;
  const old = await openDB(name, 1, {
    upgrade(db) {
      db.createObjectStore("study");
    },
  });
  const store = new StudyStore(name);
  const blocked = new Promise<void>((resolve) => {
    store.subscribe(() => {
      if (store.getSnapshot().error?.includes("blocked")) resolve();
    });
  });
  const initialization = store.init();
  await blocked;
  await store.change((s) => ({
    ...s,
    notes: { ...s.notes, "test-note": note("Typed while upgrade blocked") },
  }));
  old.close();
  await initialization;
  assert.equal(
    store.getSnapshot().data.notes["test-note"].text,
    "Typed while upgrade blocked",
  );
  assert.equal(store.getSnapshot().status, "saved");
  store.close();
  await deleteDB(name);
});
test("UTC instants compare correctly even when input clock omits fractional seconds", () => {
  const s = applyReview(
    emptyState(),
    card,
    "test-course",
    "Again",
    "event-one",
    at,
  );
  assert.equal(reviewQueue([card], s, "2026-03-08T07:09:59Z").length, 1);
  assert.equal(reviewQueue([card], s, "2026-03-08T07:09:58Z").length, 0);
});
