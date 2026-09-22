import "fake-indexeddb/auto";
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { openDB, deleteDB } from "idb";
import { z } from "zod";
import {
  ImportChangedError,
  StudyStore,
  emptyState,
  exportText,
  importPreview,
  mergeStates,
  migrateState,
  parseImport,
  parseImportFile,
  validateState,
  type BeatPosition,
  type StudyState,
} from "../src/study.ts";

const at = "2026-09-18T12:00:00.000Z";
const later = "2026-09-20T12:34:56.789Z";
const latest = "2026-09-20T12:35:00.000Z";
const lesson = "dbxfe-m04-l01";
const beat = "dbxfe-m09-beat-replay";
const question = "dbxfe-m09-check-replay";
const position: BeatPosition = {
  courseId: "dbxfe",
  moduleId: "dbxfe-m09",
  beatId: beat,
  version: "1.0.0",
  visualStateId: "change",
  view: "handbook",
  handbookOpen: true,
  handbookAnchor: beat,
  offset: 421.5,
  viewOffsets: { deck: 231.25, handbook: 421.5, cards: 92.75 },
  updatedAt: later,
};

async function predecessor(version: 1 | 2) {
  return JSON.parse(
    await readFile(
      new URL(`./fixtures/study-v${version}.json`, import.meta.url),
      "utf8",
    ),
  );
}

// This is a schema-3-shaped input built from the preserved schema-2 fixture,
// with the one real schema-3 addition (pathId), never from emptyState().
// Its predecessor data is synthetic; no user's study data is included.
async function schema3Fixture() {
  const old = await predecessor(2);
  old.schemaVersion = 3;
  old.positions[lesson] = {
    ...old.positions[lesson],
    pathId: "dbxfe-reliable-data",
    offset: 137.25,
    updatedAt: "2026-09-19T09:02:01.111Z",
  };
  old.resume = { ...old.positions[lesson] };
  old.settings = {
    theme: "dark",
    focus: true,
    sessionSize: 4,
    newLimit: 1,
    updatedAt: "2026-09-19T09:02:00.222Z",
  };
  return old;
}

async function teachingState() {
  const state = migrateState(await schema3Fixture());
  state.beatPositions[beat] = { ...position };
  state.beatResume = { ...position };
  state.beatChecks[question] = {
    id: question,
    courseId: "dbxfe",
    moduleId: "dbxfe-m09",
    beatId: beat,
    questionId: question,
    questionRevision: "1",
    opened: true,
    revealed: false,
    selectedOptionId: "dbxfe-m09-option-b",
    updatedAt: later,
  };
  state.drafts[question] = {
    id: question,
    courseId: "dbxfe",
    targetId: question,
    text: "The candidate is diagnostic; preserve the prior snapshot as stale.\nसमझ: no invented mastery.",
    createdAt: at,
    updatedAt: later,
  };
  state.settings.showSamajh = false;
  state.settings.updatedAt = later;
  return validateState(state);
}

async function seed(name: string, state: unknown) {
  const db = await openDB(name, 2, {
    upgrade(db) {
      db.createObjectStore("study");
    },
  });
  await db.put("study", state, "root");
  db.close();
}

async function savedRoot(name: string) {
  const db = await openDB(name, 2);
  try {
    assert.equal(
      db.version,
      2,
      "content-root migration must not bump native database version",
    );
    return await db.get("study", "root");
  } finally {
    db.close();
  }
}

test("genuine schema-3 shape retains every record family, timestamps and path context without manufacturing beat evidence", async () => {
  const old = await schema3Fixture();
  assert.equal("beatResume" in old, false);
  assert.equal("beatPositions" in old, false);
  assert.equal("beatChecks" in old, false);
  assert.equal("showSamajh" in old.settings, false);
  const before = structuredClone(old);
  const actual = migrateState(old);
  const expected = {
    ...before,
    schemaVersion: 4,
    beatPositions: {},
    beatResume: null,
    beatChecks: {},
    settings: { ...before.settings, showSamajh: true },
  };
  assert.deepEqual(actual, expected);
  assert.deepEqual(old, before, "migration must not mutate input");
  for (const key of [
    "notes",
    "drafts",
    "bookmarks",
    "completions",
    "attempts",
    "reviews",
    "schedules",
    "extraPractice",
    "assessments",
    "positions",
  ] as const) {
    assert.ok(
      Object.keys(before[key]).length > 0,
      `fixture must exercise ${key}`,
    );
    assert.deepEqual(actual[key], before[key], key);
  }
  assert.equal(actual.settings.updatedAt, old.settings.updatedAt);
  assert.deepEqual(actual.resume, old.resume);
  assert.equal(actual.resume?.pathId, "dbxfe-reliable-data");
});

test("schema-3 persisted root upgrades atomically while native database stays version2", async () => {
  const name = `teaching-migration-${crypto.randomUUID()}`;
  const old = await schema3Fixture();
  await seed(name, old);
  const store = new StudyStore(name);
  try {
    await store.init();
    assert.equal(store.getSnapshot().status, "saved");
    assert.deepEqual(store.getSnapshot().data, migrateState(old));
    assert.deepEqual(await savedRoot(name), migrateState(old));
  } finally {
    store.close();
    await deleteDB(name);
  }
});

test("preserved schema1 and schema2 fixtures migrate all existing families with only declared defaults", async () => {
  for (const version of [1, 2] as const) {
    const old = await predecessor(version);
    const actual = migrateState(old);
    assert.deepEqual(actual, {
      ...old,
      schemaVersion: 4,
      extraPractice: old.extraPractice ?? {},
      beatPositions: {},
      beatResume: null,
      beatChecks: {},
      settings: { ...old.settings, showSamajh: true },
    });
    assert.deepEqual(parseImport(exportText(actual)), actual);
    assert.equal(actual.settings.updatedAt, old.settings.updatedAt);
    assert.throws(() => migrateState({ ...old, beatResume: null }));
    assert.throws(() =>
      migrateState({
        ...old,
        settings: { ...old.settings, showSamajh: false },
      }),
    );
  }
});

test("deck stage, view, exact offset, handbook anchor, unrevealed check, draft and Samajh round-trip without scoring", async () => {
  const state = await teachingState();
  const serialized = exportText(state, latest);
  assert.deepEqual(parseImport(serialized), state);
  assert.deepEqual(await parseImportFile(new Blob([serialized])), state);
  assert.equal(state.beatResume?.offset, 421.5);
  assert.equal(state.beatChecks[question].revealed, false);
  assert.equal(state.beatChecks[question].questionRevision, "1");
  assert.equal(state.settings.showSamajh, false);
  assert.deepEqual(state.attempts, (await schema3Fixture()).attempts);
  assert.deepEqual(state.completions, (await schema3Fixture()).completions);
  for (const view of ["deck", "handbook", "cards"] as const) {
    const next = structuredClone(state);
    next.beatPositions[beat] = {
      ...position,
      view,
      handbookOpen: false,
      offset: 0,
    };
    next.beatResume = next.beatPositions[beat];
    assert.deepEqual(parseImport(exportText(next)), next);
  }
  const earlierSchema4 = structuredClone(state);
  delete earlierSchema4.beatChecks[question].questionRevision;
  delete earlierSchema4.beatPositions[beat].viewOffsets;
  delete earlierSchema4.beatResume!.viewOffsets;
  assert.deepEqual(parseImport(exportText(earlierSchema4)), earlierSchema4);
});

test("unknown teaching references are retained and reported by import preview", async () => {
  const state = await teachingState();
  const restored = parseImport(exportText(state));
  const preview = importPreview(emptyState(), restored, new Set());
  assert.equal(preview.counts.beatPositions, 1);
  assert.equal(preview.counts.beatChecks, 1);
  for (const id of [
    "dbxfe",
    "dbxfe-m09",
    beat,
    question,
    "dbxfe-reliable-data",
  ])
    assert.ok(preview.unknown.includes(id), id);
  assert.deepEqual(restored, state);
});

test("empty and stale merge preserve current beat resume, visual stage, checks and optional-language setting", async () => {
  const current = await teachingState();
  for (const incoming of [emptyState(), migrateState(await schema3Fixture())]) {
    const result = mergeStates(current, incoming);
    assert.deepEqual(result.beatResume, current.beatResume);
    assert.deepEqual(result.beatPositions, current.beatPositions);
    assert.deepEqual(result.beatChecks, current.beatChecks);
    assert.deepEqual(result.settings, current.settings);
    assert.deepEqual(mergeStates(incoming, current), result);
  }
  const stale = structuredClone(current);
  stale.beatResume = {
    ...position,
    visualStateId: "start",
    view: "deck",
    offset: 0,
    updatedAt: at,
  };
  stale.beatPositions[beat] = stale.beatResume;
  stale.beatChecks[question] = {
    ...stale.beatChecks[question],
    opened: false,
    revealed: false,
    updatedAt: at,
  };
  stale.settings = { ...stale.settings, showSamajh: true, updatedAt: at };
  const result = mergeStates(current, stale);
  assert.deepEqual(result.beatResume, current.beatResume);
  assert.deepEqual(result.beatPositions, current.beatPositions);
  assert.deepEqual(result.beatChecks, current.beatChecks);
  assert.deepEqual(result.settings, current.settings);
});

test("divergent self-explanation drafts preserve both texts and timestamps through repeat merge", async () => {
  const local = await teachingState();
  const incoming = structuredClone(local);
  incoming.drafts[question] = {
    ...incoming.drafts[question],
    text: "Different reasoning from another device",
    updatedAt: latest,
  };
  const merged = mergeStates(local, incoming);
  const variants = Object.values(merged.drafts).filter(
    (d) => d.targetId === question,
  );
  assert.equal(variants.length, 2);
  assert.deepEqual(
    variants.map((d) => [d.text, d.createdAt, d.updatedAt]).sort(),
    [
      [local.drafts[question].text, at, later],
      [incoming.drafts[question].text, at, latest],
    ].sort(),
  );
  assert.deepEqual(mergeStates(merged, incoming), merged);
  assert.deepEqual(mergeStates(incoming, local), merged);
  assert.deepEqual(
    merged.attempts,
    local.attempts,
    "drafts must not fabricate objective attempts",
  );
  assert.deepEqual(parseImport(exportText(merged)), merged);
});

test("latest-state transactions retain simultaneous legacy note and teaching navigation writes", async () => {
  const name = `teaching-concurrent-${crypto.randomUUID()}`;
  const initial = await teachingState();
  await seed(name, initial);
  const one = new StudyStore(name),
    two = new StudyStore(name);
  try {
    await one.init();
    await two.init();
    await Promise.all([
      one.change((s) => ({
        ...s,
        beatResume: { ...position, view: "cards", updatedAt: latest },
        beatPositions: {
          ...s.beatPositions,
          [beat]: { ...position, view: "cards", updatedAt: latest },
        },
      })),
      two.change((s) => ({
        ...s,
        notes: {
          ...s.notes,
          "synthetic-v2-note": {
            ...s.notes["synthetic-v2-note"],
            text: "Latest note from another tab",
            updatedAt: latest,
          },
        },
      })),
    ]);
    const durable = await savedRoot(name);
    assert.equal(
      durable.notes["synthetic-v2-note"].text,
      "Latest note from another tab",
    );
    assert.equal(durable.beatResume.view, "cards");
    assert.deepEqual(durable.reviews, initial.reviews);
    assert.deepEqual(await one.readLatest(), durable);
    assert.deepEqual(await two.readLatest(), durable);
  } finally {
    one.close();
    two.close();
    await deleteDB(name);
  }
});

test("aborted teaching write keeps durable root, recovery draft and exact stage; retry incorporates another tab", async () => {
  const name = `teaching-abort-${crypto.randomUUID()}`;
  const initial = await teachingState();
  await seed(name, initial);
  let fail = true;
  const one = new StudyStore(name, () => {
    if (fail) throw new DOMException("Synthetic quota", "QuotaExceededError");
  });
  const two = new StudyStore(name);
  try {
    await one.init();
    await two.init();
    await one.change((s) => ({
      ...s,
      beatResume: {
        ...position,
        visualStateId: "decision",
        offset: 812.75,
        updatedAt: latest,
      },
      beatPositions: {
        ...s.beatPositions,
        [beat]: {
          ...position,
          visualStateId: "decision",
          offset: 812.75,
          updatedAt: latest,
        },
      },
      drafts: {
        ...s.drafts,
        [question]: {
          ...s.drafts[question],
          text: "Final unsaved reasoning!",
          updatedAt: latest,
        },
      },
    }));
    assert.equal(one.getSnapshot().status, "unsaved");
    assert.deepEqual(await savedRoot(name), initial);
    const recovery = parseImport(exportText(one.getSnapshot().data));
    assert.equal(recovery.drafts[question].text, "Final unsaved reasoning!");
    assert.equal(recovery.beatResume?.visualStateId, "decision");
    assert.equal(recovery.beatResume?.offset, 812.75);
    await two.change((s) => ({
      ...s,
      settings: { ...s.settings, sessionSize: 2, updatedAt: latest },
    }));
    const combined = await one.readLatest();
    assert.equal(combined.settings.sessionSize, 2);
    assert.equal(combined.drafts[question].text, "Final unsaved reasoning!");
    assert.equal(one.getSnapshot().status, "unsaved");
    fail = false;
    await one.change((s) => s);
    assert.equal(one.getSnapshot().status, "saved");
    assert.deepEqual(await savedRoot(name), combined);
  } finally {
    one.close();
    two.close();
    await deleteDB(name);
  }
});

test("stale replace preview cannot erase newer teaching state, and aborted replacement preserves all families", async () => {
  const name = `teaching-preview-${crypto.randomUUID()}`;
  const initial = await teachingState();
  await seed(name, initial);
  let fail = false;
  const one = new StudyStore(name, () => {
    if (fail) throw Error("Synthetic abort");
  });
  const two = new StudyStore(name);
  try {
    await one.init();
    await two.init();
    const preview = await one.readLatest();
    await two.change((s) => ({
      ...s,
      beatChecks: {
        ...s.beatChecks,
        [question]: {
          ...s.beatChecks[question],
          revealed: true,
          updatedAt: latest,
        },
      },
    }));
    const before = await savedRoot(name);
    await assert.rejects(
      one.import(emptyState(), "replace", preview),
      ImportChangedError,
    );
    assert.deepEqual(await savedRoot(name), before);
    fail = true;
    await assert.rejects(one.replace(emptyState()), /Synthetic abort/);
    assert.deepEqual(await savedRoot(name), before);
    assert.equal((await one.readLatest()).beatChecks[question].revealed, true);
  } finally {
    one.close();
    two.close();
    await deleteDB(name);
  }
});

test("future schema root refuses current-client writes without overwriting stored evidence", async () => {
  const name = `teaching-future-${crypto.randomUUID()}`;
  const future = { ...(await teachingState()), schemaVersion: 5 };
  await seed(name, future);
  const store = new StudyStore(name);
  try {
    await store.init();
    assert.equal(store.getSnapshot().status, "unsaved");
    await store.change((s) => ({
      ...s,
      settings: { ...s.settings, showSamajh: false, updatedAt: later },
    }));
    assert.equal(store.getSnapshot().status, "unsaved");
    assert.deepEqual(await savedRoot(name), future);
    await assert.rejects(store.replace(emptyState()));
    assert.deepEqual(await savedRoot(name), future);
  } finally {
    store.close();
    await deleteDB(name);
  }
});

test("schema-3 version guard rejects schema4 before an old tab can put a stale root", async () => {
  // Frozen guard from e3bfb974's strict stateSchema discriminator. This is a
  // focused compatibility simulation, not an execution of an entire old UI.
  const oldGuard = z.object({ schemaVersion: z.literal(3) }).passthrough();
  const name = `teaching-old-guard-${crypto.randomUUID()}`;
  const current = await teachingState();
  await seed(name, current);
  const db = await openDB(name, 2);
  try {
    const stale = await schema3Fixture();
    assert.equal(oldGuard.parse(stale).schemaVersion, 3);
    const tx = db.transaction("study", "readwrite");
    const persisted = await tx.store.get("root");
    assert.throws(() => oldGuard.parse(persisted));
    tx.abort();
    await assert.rejects(tx.done);
    assert.deepEqual(await db.get("study", "root"), current);
  } finally {
    db.close();
    await deleteDB(name);
  }
});

test("malformed teaching position/check keys fail before any import mutation", async () => {
  const current = await teachingState();
  const badPosition = structuredClone(current);
  badPosition.beatPositions["different-beat"] = badPosition.beatPositions[beat];
  assert.throws(() => validateState(badPosition), /Beat position key mismatch/);
  const badCheck = structuredClone(current);
  badCheck.beatChecks[question].id = "different-question";
  assert.throws(() => validateState(badCheck), /Record key mismatch/);
  const badStage = structuredClone(current) as StudyState;
  badStage.beatResume!.offset = Number.NaN;
  assert.throws(() => validateState(badStage));
  assert.deepEqual(parseImport(exportText(current)), current);
});

test("failed schema3 migration and future root export original content separately from new unsaved drafts", async () => {
  const malformed = await schema3Fixture();
  malformed.notes["synthetic-v2-note"].createdAt =
    "unreadable original timestamp";
  const future = {
    ...(await teachingState()),
    schemaVersion: 42,
    futureRecord: {
      text: 'Original 漢字 🧠\nquoted "evidence" remains intact',
      count: 0,
    },
  };
  for (const original of [malformed, future]) {
    const name = `teaching-original-${crypto.randomUUID()}`;
    await seed(name, original);
    const store = new StudyStore(name);
    try {
      await store.init();
      assert.equal(store.getSnapshot().status, "unsaved");
      assert.equal(store.hasOriginalRecovery(), true);
      assert.match(
        store.getSnapshot().error ?? "",
        /original saved collection/,
      );
      const originalText = store.exportOriginalRecovery();
      assert.ok(originalText);
      const exportedOriginal = JSON.parse(originalText).state;
      assert.deepEqual(exportedOriginal, original);
      assert.deepEqual(
        Buffer.from(JSON.stringify(exportedOriginal), "utf8"),
        Buffer.from(JSON.stringify(original), "utf8"),
      );
      assert.throws(
        () => parseImport(originalText),
        "original recovery must not pretend the invalid/future root became valid",
      );
      await store.change((s) => ({
        ...s,
        drafts: {
          ...s.drafts,
          "recovery-draft": {
            id: "recovery-draft",
            courseId: "dbxfe",
            targetId: question,
            text: "New work after the migration failed",
            createdAt: latest,
            updatedAt: latest,
          },
        },
      }));
      assert.equal(store.getSnapshot().status, "unsaved");
      const newRecovery = parseImport(exportText(store.getSnapshot().data));
      assert.equal(
        newRecovery.drafts["recovery-draft"].text,
        "New work after the migration failed",
      );
      assert.equal(newRecovery.schemaVersion, 4);
      assert.deepEqual(
        JSON.parse(store.exportOriginalRecovery()!).state,
        original,
      );
      assert.deepEqual(await savedRoot(name), original);
    } finally {
      store.close();
      await deleteDB(name);
    }
  }
});

test("oversized original future-root recovery uses frames without losing a byte or requiring validation", async () => {
  const name = `teaching-original-framed-${crypto.randomUUID()}`;
  const original = {
    schemaVersion: 99,
    futurePayload:
      "Original 漢字 🧠\n" + "x".repeat(20_050_000) + "\nlast-byte!",
  };
  await seed(name, original);
  const store = new StudyStore(name);
  try {
    await store.init();
    assert.equal(store.hasOriginalRecovery(), true);
    const backup = store.exportOriginalRecovery()!;
    const lines = backup.split("\n");
    const header = JSON.parse(lines.shift()!);
    assert.equal(header.format, "SpicyBrain framed backup v1");
    assert.equal(lines.length, header.parts);
    const raw = lines
      .map((line, index) => {
        const frame = JSON.parse(line);
        assert.equal(frame.part, index);
        assert.ok(Buffer.byteLength(line, "utf8") <= 1_000_000);
        return frame.data as string;
      })
      .join("");
    assert.equal(Buffer.byteLength(raw, "utf8"), header.bytes);
    assert.deepEqual(JSON.parse(raw).state, original);
    assert.deepEqual(await savedRoot(name), original);
    assert.equal(store.getSnapshot().status, "unsaved");
  } finally {
    store.close();
    await deleteDB(name);
  }
});

test("readable saved root offers no spurious original-recovery collection", async () => {
  const name = `teaching-no-recovery-${crypto.randomUUID()}`;
  await seed(name, await schema3Fixture());
  const store = new StudyStore(name);
  try {
    await store.init();
    assert.equal(store.getSnapshot().status, "saved");
    assert.equal(store.hasOriginalRecovery(), false);
    assert.equal(store.exportOriginalRecovery(), null);
  } finally {
    store.close();
    await deleteDB(name);
  }
});
