import "fake-indexeddb/auto";
import { test } from "node:test";
import assert from "node:assert/strict";
import { openDB } from "idb";
import {
  StudyStore,
  emptyState,
  mergeStates,
  applyReview,
  exportText,
  parseImport,
  parseImportFile,
  parseLegacyFile,
  validateState,
  studyBytes,
  utf8Bytes,
  STUDY_BUDGET_BYTES,
  JSON_FILE_BYTES,
  BACKUP_FRAME_BYTES,
  ImportChangedError,
} from "../src/study";
import {
  fixtureAt,
  fixtureLessons,
  fixtureNote,
  noteState,
  exactBytes,
} from "./study-fixtures";
const withNote = (index: number, text: string) => {
  const n = fixtureNote(index, text);
  return (s: ReturnType<typeof emptyState>) => ({
    ...s,
    notes: { ...s.notes, [n.id]: n },
  });
};
async function reader(name: string) {
  const s = new StudyStore(name);
  await s.init();
  const data = s.getSnapshot().data;
  s.close();
  return data;
}

test("P1 stale-tab and empty merge use latest persisted root and survive reopening", async () => {
  for (const incoming of [emptyState(), noteState(1, "Incoming")]) {
    const name = `merge-${crypto.randomUUID()}`,
      a = new StudyStore(name),
      b = new StudyStore(name);
    await a.init();
    await b.init();
    await b.change(withNote(1, "Saved after A initialized"));
    assert.equal(Object.keys((await reader(name)).notes).length, 1);
    await a.import(incoming, "merge");
    const after = await reader(name);
    assert.equal(
      after.notes[fixtureNote(1, "").id].text,
      "Saved after A initialized",
    );
    for (const note of Object.values(incoming.notes))
      assert.equal(after.notes[note.id].text, note.text);
    a.close();
    b.close();
  }
});
test("P1 queued edits across import barrier, failed edits, note/draft conflicts and immutable history survive", async () => {
  const name = `queue-import-${crypto.randomUUID()}`;
  let fail = true;
  const a = new StudyStore(name, () => {
      if (fail) throw Error("Synthetic failure");
    }),
    b = new StudyStore(name);
  await a.init();
  await b.init();
  await a.change(withNote(0, "Unsaved local text"));
  assert.equal(a.getSnapshot().status, "unsaved");
  const card = fixtureLessons[0].cards[0];
  await b.change((s) =>
    applyReview(
      withNote(1, "Other tab")(s),
      card,
      "dbxfe",
      "Good",
      "review-other",
      fixtureAt,
    ),
  );
  const d = {
    id: "draft-dbxfe-m02-scenario",
    courseId: "dbxfe",
    targetId: "dbxfe-m02-scenario",
    text: "Other draft",
    createdAt: fixtureAt,
    updatedAt: fixtureAt,
  };
  await b.change((s) => ({ ...s, drafts: { [d.id]: d } }));
  const incoming = noteState(1, "Imported conflicting text");
  incoming.drafts[d.id] = { ...d, text: "Imported draft" };
  fail = false;
  const imported = a.import(incoming, "merge");
  const edit = a.change(withNote(2, "Typed after import was queued"));
  await Promise.all([imported, edit]);
  const result = await reader(name);
  assert.deepEqual(
    new Set(Object.values(result.notes).map((n) => n.text)),
    new Set([
      "Unsaved local text",
      "Imported conflicting text",
      "Other tab",
      "Typed after import was queued",
    ]),
  );
  assert.deepEqual(
    new Set(Object.values(result.drafts).map((n) => n.text)),
    new Set(["Other draft", "Imported draft"]),
  );
  assert.equal(result.reviews["review-other"].rating, "Good");
  assert.equal(result.schedules[card.id].lastEventId, "review-other");
  const duplicate = await a.import(incoming, "merge");
  assert.equal(duplicate, undefined);
  assert.deepEqual(await reader(name), result);
  a.close();
  b.close();
});
test("P1 preview change blocks both modes, refreshed confirmation succeeds, post-enqueue edits are retained", async () => {
  for (const mode of ["merge", "replace"] as const) {
    const name = `preview-${crypto.randomUUID()}`,
      a = new StudyStore(name),
      b = new StudyStore(name);
    await a.init();
    await b.init();
    const expected = await a.readLatest();
    await b.change(withNote(1, "Written after preview"));
    await assert.rejects(
      a.import(emptyState(), mode, expected),
      ImportChangedError,
    );
    assert.equal(
      Object.values((await reader(name)).notes)[0].text,
      "Written after preview",
    );
    const basis = await a.readLatest();
    const imported = a.import(emptyState(), mode, basis);
    const pending = a.change(withNote(2, "Typed after confirmation"));
    await Promise.all([imported, pending]);
    assert.equal(
      (await reader(name)).notes[fixtureNote(2, "").id].text,
      "Typed after confirmation",
    );
    a.close();
    b.close();
  }
});
test("P1 injected merge transaction failure rolls back all records, pending work remains recoverable", async () => {
  const name = `rollback-${crypto.randomUUID()}`;
  let fail = false;
  const a = new StudyStore(name, () => {
    if (fail) throw Error("after put");
  });
  await a.init();
  await a.change(withNote(0, "Persisted"));
  const before = await reader(name);
  fail = true;
  await a.change(withNote(1, "Pending"));
  await assert.rejects(a.import(noteState(1, "Incoming"), "merge"));
  assert.deepEqual(await reader(name), before);
  assert.equal(
    parseImport(exportText(a.getSnapshot().data)).notes[fixtureNote(1, "").id]
      .text,
    "Pending",
  );
  const pendingPreview = await a.readLatest();
  fail = false;
  await a.import(emptyState(), "merge", pendingPreview);
  assert.equal(
    (await reader(name)).notes[fixtureNote(1, "").id].text,
    "Pending",
  );
  a.close();
});
test("P2 former 5 MB valid state exports and restores exactly, using file reader too", async () => {
  const state = noteState();
  validateState(state);
  const raw = exportText(state, fixtureAt);
  const {beatPositions:_positions,beatResume:_resume,beatChecks:_checks,...legacy}=state;
  const {showSamajh:_samajh,...oldSettings}=legacy.settings;
  const oldRaw=JSON.stringify({format:"SpicyBrain study data",exportedAt:fixtureAt,state:{...legacy,schemaVersion:3,settings:oldSettings}},null,2);
  assert.equal(utf8Bytes(oldRaw), 5118056);
  assert.deepEqual(parseImport(oldRaw),state);
  assert.equal(utf8Bytes(raw), 5118153);
  assert.deepEqual(parseImport(raw), state);
  assert.deepEqual(await parseImportFile(new Blob([raw])), state);
});
test("P2 exact UTF-8 active capacity, +1 byte unsaved, recovery remains restorable", async () => {
  const state = exactBytes(STUDY_BUDGET_BYTES);
  const name = `capacity-${crypto.randomUUID()}`,
    store = new StudyStore(name);
  await store.init();
  await store.change(() => state);
  assert.equal(store.getSnapshot().status, "saved");
  const key = Object.keys(state.notes)[0];
  const larger = structuredClone(state);
  larger.notes[key].text = "é" + larger.notes[key].text.slice(1);
  assert.equal(larger.notes[key].text.length, state.notes[key].text.length);
  assert.equal(studyBytes(larger), STUDY_BUDGET_BYTES + 1);
  await store.change(() => larger);
  assert.equal(store.getSnapshot().status, "unsaved");
  assert.match(store.getSnapshot().error!, /16 MB/);
  assert.deepEqual(await reader(name), state);
  assert.deepEqual(
    await parseImportFile(new Blob([exportText(store.getSnapshot().data)])),
    larger,
  );
  await store.change(() => state);
  assert.equal(store.getSnapshot().status, "saved");
  store.close();
});
test("P2 any larger legacy state remains intact, framed recovery restores, growth is paused", async () => {
  const legacy = noteState(210, "界".repeat(35000));
  const name = `legacy-${crypto.randomUUID()}`;
  const db = await openDB(name, 2, {
    upgrade(db) {
      db.createObjectStore("study");
    },
  });
  await db.put("study", legacy, "root");
  db.close();
  const store = new StudyStore(name);
  await store.init();
  assert.deepEqual(store.getSnapshot().data, legacy);
  const raw = exportText(legacy, fixtureAt);
  assert.ok(raw.startsWith('{"format":"SpicyBrain framed backup v1"'));
  assert.ok(utf8Bytes(raw) > JSON_FILE_BYTES);
  for (const line of raw.split("\n"))
    assert.ok(utf8Bytes(line) <= BACKUP_FRAME_BYTES);
  assert.deepEqual(parseImport(raw), legacy);
  const restored = await parseImportFile(new Blob([raw]));
  assert.deepEqual(restored, legacy);
  const oldRaw = JSON.stringify({
    format: "SpicyBrain study data",
    exportedAt: fixtureAt,
    state: legacy,
  });
  await assert.rejects(parseImportFile(new Blob([oldRaw])), /20 MB/);
  assert.deepEqual(await parseLegacyFile(new Blob([oldRaw])), legacy);
  const fresh = new StudyStore(`restored-${crypto.randomUUID()}`);
  await fresh.init();
  await fresh.import(restored, "merge");
  assert.deepEqual(await fresh.readLatest(), legacy);
  const key = Object.keys(legacy.notes)[0];
  await fresh.change((s) => ({
    ...s,
    notes: {
      ...s.notes,
      [key]: { ...s.notes[key], text: s.notes[key].text + "x" },
    },
  }));
  assert.equal(fresh.getSnapshot().status, "unsaved");
  await fresh.change((s) => ({
    ...s,
    notes: {
      ...s.notes,
      [key]: { ...s.notes[key], text: "Shorter, intentionally edited" },
    },
  }));
  assert.equal(fresh.getSnapshot().status, "saved");
  fresh.close();
  store.close();
});
test("P2 malformed, future, oversized plain/frame, missing and reordered frames fail without a write", async () => {
  const state = noteState(1, "Keep this");
  const name = `invalid-${crypto.randomUUID()}`,
    store = new StudyStore(name);
  await store.init();
  await store.replace(state);
  const header = JSON.stringify({
    format: "SpicyBrain framed backup v1",
    parts: 2,
    bytes: 2,
  });
  const bad = [
    "{",
    JSON.stringify({
      format: "SpicyBrain study data",
      exportedAt: fixtureAt,
      state: { ...state, schemaVersion: 99 },
    }),
    " ".repeat(JSON_FILE_BYTES + 1),
    header + "\n" + "x".repeat(BACKUP_FRAME_BYTES + 1),
    header + '\n{"part":1,"data":"x"}',
    header + '\n{"part":0,"data":"x"}',
  ];
  for (const raw of bad) {
    await assert.rejects(async () =>
      store.import(await parseImportFile(new Blob([raw])), "merge"),
    );
    assert.deepEqual(await reader(name), state);
  }
  assert.throws(() =>
    mergeStates(state, {
      ...state,
      notes: {
        ...state.notes,
        bad: {
          ...Object.values(state.notes)[0],
          id: "bad",
          text: "x".repeat(100001),
        },
      },
    }),
  );
  store.close();
});
