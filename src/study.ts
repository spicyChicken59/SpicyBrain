import { z } from "zod";
import { openDB, type IDBPDatabase } from "idb";
import { idSchema, type Card } from "./content-schema";

export const DAY = 86_400_000;
export const ALGORITHM = "spicybrain-simple-v1";
export type Rating = "Again" | "Hard" | "Good" | "Easy";
export const nowISO = () => new Date().toISOString();
const iso = z.iso.datetime();
const text = z.string().max(100000);
const uid = z
  .string()
  .min(1)
  .max(200)
  .regex(/^[a-zA-Z0-9-]+$/);
const record = <T extends z.ZodType>(v: T) => z.record(uid, v);
const ref = { courseId: idSchema, lessonId: idSchema };
const base = { id: uid, createdAt: iso, updatedAt: iso };
const note = z
  .object({ ...base, ...ref, sectionId: idSchema, text, question: z.boolean() })
  .strict();
const draft = z
  .object({ ...base, courseId: idSchema, targetId: idSchema, text })
  .strict();
const bookmark = z
  .object({
    id: uid,
    ...ref,
    sectionId: idSchema,
    active: z.boolean(),
    updatedAt: iso,
  })
  .strict();
const completion = z
  .object({
    id: uid,
    ...ref,
    sectionId: idSchema.optional(),
    completed: z.boolean(),
    contentVersion: text.min(1),
    updatedAt: iso,
  })
  .strict();
const attempt = z
  .object({
    id: uid,
    ...ref,
    questionId: idSchema,
    questionRevision: text.min(1),
    contentVersion: text.min(1),
    at: iso,
    optionId: idSchema,
    correctOptionId: idSchema,
    correct: z.boolean(),
    conceptIds: z.array(idSchema),
    snapshot: z
      .object({
        prompt: text,
        options: z.array(
          z.object({ id: idSchema, text, rationale: text }).strict(),
        ),
      })
      .strict(),
  })
  .strict();
const review = z
  .object({
    id: uid,
    ...ref,
    cardId: idSchema,
    revision: text.min(1),
    at: iso,
    rating: z.enum(["Again", "Hard", "Good", "Easy"]),
    beforeInterval: z.number().int().min(0).max(365),
    intervalDays: z.number().int().min(0).max(365),
    dueAt: iso,
    algorithmVersion: z.literal(ALGORITHM),
  })
  .strict();
const schedule = z
  .object({
    id: uid,
    ...ref,
    cardId: idSchema,
    revision: text.min(1),
    intervalDays: z.number().int().min(0).max(365),
    dueAt: iso,
    lastEventId: uid,
    updatedAt: iso,
  })
  .strict();
const practice = z
  .object({ id: uid, ...ref, cardId: idSchema, revision: text.min(1), at: iso })
  .strict();
const assessment = z
  .object({
    id: uid,
    courseId: idSchema,
    targetId: idSchema,
    at: iso,
    ratings: z.record(idSchema, z.enum(["weak", "partial", "strong"])),
    kind: z.literal("self-assessment"),
  })
  .strict();
const settings = z
  .object({
    theme: z.enum(["auto", "dark", "light"]),
    focus: z.boolean(),
    sessionSize: z.number().int().min(1).max(30),
    newLimit: z.number().int().min(1).max(10),
    updatedAt: iso,
  })
  .strict();
const position = z
  .object({
    ...ref,
    sectionId: idSchema,
    offset: z.number().min(-5000).max(100000),
    updatedAt: iso,
  })
  .strict();
export const stateSchema = z
  .object({
    schemaVersion: z.literal(2),
    notes: record(note),
    drafts: record(draft),
    bookmarks: record(bookmark),
    completions: record(completion),
    attempts: record(attempt),
    reviews: record(review),
    schedules: record(schedule),
    extraPractice: record(practice),
    assessments: record(assessment),
    positions: record(position),
    resume: position.nullable(),
    settings,
    disclosureAccepted: z.boolean(),
  })
  .strict();
export type StudyState = z.infer<typeof stateSchema>;
export type Note = z.infer<typeof note>;
export function emptyState(at = "1970-01-01T00:00:00.000Z"): StudyState {
  return {
    schemaVersion: 2,
    notes: {},
    drafts: {},
    bookmarks: {},
    completions: {},
    attempts: {},
    reviews: {},
    schedules: {},
    extraPractice: {},
    assessments: {},
    positions: {},
    resume: null,
    settings: {
      theme: "auto",
      focus: false,
      sessionSize: 10,
      newLimit: 3,
      updatedAt: at,
    },
    disclosureAccepted: false,
  };
}
export function scheduleRating(previous: number, rating: Rating, at: string) {
  if (
    !Number.isInteger(previous) ||
    previous < 0 ||
    previous > 365 ||
    !Number.isFinite(Date.parse(at))
  )
    throw Error("Invalid review basis");
  let intervalDays = 0,
    delay = 600000;
  if (rating === "Hard")
    intervalDays = Math.min(365, Math.max(1, Math.ceil(previous * 1.2)));
  if (rating === "Good")
    intervalDays = previous === 0 ? 3 : Math.min(365, Math.ceil(previous * 2));
  if (rating === "Easy")
    intervalDays = previous === 0 ? 7 : Math.min(365, Math.ceil(previous * 3));
  if (rating !== "Again") delay = intervalDays * DAY;
  return {
    intervalDays,
    dueAt: new Date(Date.parse(at) + delay).toISOString(),
  };
}
export function applyReview(
  state: StudyState,
  card: Card,
  courseId: string,
  rating: Rating,
  eventId: string,
  at: string,
): StudyState {
  if (state.reviews[eventId]) return state;
  const beforeInterval = state.schedules[card.id]?.intervalDays ?? 0;
  const next = scheduleRating(beforeInterval, rating, at);
  return {
    ...state,
    reviews: {
      ...state.reviews,
      [eventId]: {
        id: eventId,
        courseId,
        lessonId: card.lessonId,
        cardId: card.id,
        revision: card.revision,
        at,
        rating,
        beforeInterval,
        ...next,
        algorithmVersion: ALGORITHM,
      },
    },
    schedules: {
      ...state.schedules,
      [card.id]: {
        id: card.id,
        courseId,
        lessonId: card.lessonId,
        cardId: card.id,
        revision: card.revision,
        ...next,
        lastEventId: eventId,
        updatedAt: at,
      },
    },
  };
}
export function reviewQueue(
  cards: Card[],
  state: StudyState,
  at: string,
  limit = state.settings.sessionSize,
) {
  return cards
    .filter((c) => {
      const s = state.schedules[c.id];
      return (
        s &&
        (Date.parse(s.dueAt) <= Date.parse(at) || s.revision !== c.revision)
      );
    })
    .sort(
      (a, b) =>
        Date.parse(state.schedules[a.id].dueAt) -
          Date.parse(state.schedules[b.id].dueAt) || a.id.localeCompare(b.id),
    )
    .slice(0, limit);
}
export function migrateState(value: unknown): StudyState {
  if (
    value &&
    typeof value === "object" &&
    "schemaVersion" in value &&
    value.schemaVersion === 1
  ) {
    // Synthetic predecessor: v1 had all records except extra practice, which was not recorded.
    const old = stateSchema
      .omit({ schemaVersion: true, extraPractice: true })
      .extend({ schemaVersion: z.literal(1) })
      .strict()
      .parse(value);
    return validateState({ ...old, schemaVersion: 2, extraPractice: {} });
  }
  return validateState(value);
}
export function validateState(value: unknown): StudyState {
  const s = stateSchema.parse(value);
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
  ] as const) {
    for (const [k, v] of Object.entries(s[key]))
      if (k !== v.id) throw Error(`Record key mismatch: ${key}`);
  }
  for (const [key, v] of Object.entries(s.positions))
    if (key !== v.lessonId) throw Error("Position key mismatch");
  for (const a of Object.values(s.attempts)) {
    if (
      !a.snapshot.options.some((o) => o.id === a.optionId) ||
      !a.snapshot.options.some((o) => o.id === a.correctOptionId) ||
      a.correct !== (a.optionId === a.correctOptionId)
    )
      throw Error("Invalid attempt evidence");
  }
  for (const r of Object.values(s.reviews)) {
    const n = scheduleRating(r.beforeInterval, r.rating, r.at);
    if (n.dueAt !== r.dueAt || n.intervalDays !== r.intervalDays)
      throw Error("Invalid review evidence");
  }
  for (const v of Object.values(s.schedules)) {
    const r = s.reviews[v.lastEventId];
    if (
      !r ||
      r.cardId !== v.cardId ||
      r.dueAt !== v.dueAt ||
      r.intervalDays !== v.intervalDays ||
      r.revision !== v.revision
    )
      throw Error("Schedule has no matching immutable event");
  }
  return s;
}
export function exportText(s: StudyState, at = nowISO()) {
  return JSON.stringify(
    { format: "SpicyBrain study data", exportedAt: at, state: s },
    null,
    2,
  );
}
export function parseImport(raw: string): StudyState {
  if (new TextEncoder().encode(raw).byteLength > 5_000_000)
    throw Error("Import exceeds the 5 MB limit. No data changed.");
  const envelope = z
    .object({
      format: z.literal("SpicyBrain study data"),
      exportedAt: iso,
      state: z.unknown(),
    })
    .strict()
    .parse(JSON.parse(raw));
  return migrateState(envelope.state);
}
function stableHash(value: string) {
  let h = 2166136261;
  for (const ch of value) {
    h ^= ch.charCodeAt(0);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0).toString(16);
}
function newest<T extends { updatedAt: string }>(a: T, b: T): T {
  return Date.parse(a.updatedAt) > Date.parse(b.updatedAt)
    ? a
    : Date.parse(a.updatedAt) < Date.parse(b.updatedAt)
      ? b
      : JSON.stringify(a) >= JSON.stringify(b)
        ? a
        : b;
}
const immutableKeys = [
  "attempts",
  "reviews",
  "extraPractice",
  "assessments",
] as const;
export function mergeStates(
  local: StudyState,
  incoming: StudyState,
): StudyState {
  const result = structuredClone(local);
  for (const key of immutableKeys) {
    const target = result[key] as Record<string, unknown>;
    for (const [id, item] of Object.entries(incoming[key])) {
      if (target[id] && JSON.stringify(target[id]) !== JSON.stringify(item))
        throw Error(`Conflicting immutable event: ${id}. No data changed.`);
      target[id] = item;
    }
  }
  for (const key of ["notes", "drafts"] as const) {
    for (const [id, item] of Object.entries(incoming[key])) {
      const target = result[key] as Record<
        string,
        Note | z.infer<typeof draft>
      >;
      const old = target[id];
      if (!old) {
        target[id] = item;
        continue;
      }
      if (old.text !== item.text) {
        const winner = newest(old, item),
          other = winner === old ? item : old;
        // Content-derived conflict IDs make repeated imports idempotent. Collision-safe suffix search.
        const stem = `${id}-conflict-${stableHash(JSON.stringify(other))}`;
        let conflictId = stem,
          i = 0;
        while (
          target[conflictId] &&
          JSON.stringify({ ...target[conflictId], id: other.id }) !==
            JSON.stringify(other)
        )
          conflictId = `${stem}-${++i}`;
        target[conflictId] = { ...other, id: conflictId };
        target[id] = winner;
      } else target[id] = newest(old, item);
    }
  }
  for (const key of ["bookmarks", "completions", "positions"] as const) {
    const target = result[key] as Record<string, { updatedAt: string }>;
    for (const [id, item] of Object.entries(incoming[key]))
      target[id] = target[id] ? newest(target[id], item) : item;
  }
  result.settings = newest(local.settings, incoming.settings);
  result.resume =
    local.resume && incoming.resume
      ? newest(local.resume, incoming.resume)
      : local.resume || incoming.resume;
  result.disclosureAccepted =
    local.disclosureAccepted || incoming.disclosureAccepted;
  // Reconstruct schedules from the latest immutable review; event ID breaks timestamp ties.
  result.schedules = {};
  for (const r of Object.values(result.reviews).sort(
    (a, b) => Date.parse(a.at) - Date.parse(b.at) || a.id.localeCompare(b.id),
  )) {
    result.schedules[r.cardId] = {
      id: r.cardId,
      cardId: r.cardId,
      courseId: r.courseId,
      lessonId: r.lessonId,
      revision: r.revision,
      intervalDays: r.intervalDays,
      dueAt: r.dueAt,
      lastEventId: r.id,
      updatedAt: r.at,
    };
  }
  return validateState(result);
}
export function importPreview(
  local: StudyState,
  incoming: StudyState,
  known: Set<string>,
) {
  const counts = Object.fromEntries(
    [
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
    ].map((k) => [
      k,
      Object.keys(incoming[k as keyof StudyState] as object).length,
    ]),
  );
  const conflicts =
    Object.values(incoming.notes).filter(
      (n) => local.notes[n.id] && local.notes[n.id].text !== n.text,
    ).length +
    Object.values(incoming.drafts).filter(
      (n) => local.drafts[n.id] && local.drafts[n.id].text !== n.text,
    ).length;
  const unknown = new Set<string>();
  for (const group of [
    incoming.notes,
    incoming.drafts,
    incoming.bookmarks,
    incoming.completions,
    incoming.attempts,
    incoming.reviews,
    incoming.assessments,
    incoming.positions,
  ])
    for (const value of Object.values(group)) {
      for (const key of [
        "courseId",
        "lessonId",
        "sectionId",
        "targetId",
        "cardId",
        "questionId",
      ] as const)
        if (key in value) {
          const id = (value as Record<string, unknown>)[key] as string;
          if (!known.has(id)) unknown.add(id);
        }
    }
  return { counts, conflicts, unknown: [...unknown].sort() };
}
export type StoreSnapshot = {
  data: StudyState;
  status: "loading" | "saving" | "saved" | "unsaved";
  error: string | null;
};
export class StudyStore {
  private db: IDBPDatabase | undefined;
  private listeners = new Set<() => void>();
  private queue = Promise.resolve();
  private pending: ((s: StudyState) => StudyState)[] = [];
  private snap: StoreSnapshot = {
    data: emptyState(),
    status: "loading",
    error: null,
  };
  constructor(
    private name = "spicybrain-study-v2",
    private fault?: () => void,
  ) {}
  getSnapshot = () => this.snap;
  subscribe = (fn: () => void) => {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  };
  private emit(s: StoreSnapshot) {
    this.snap = s;
    for (const fn of this.listeners) fn();
  }
  async init() {
    try {
      this.db = await openDB(this.name, 2, {
        upgrade(db) {
          if (!db.objectStoreNames.contains("study"))
            db.createObjectStore("study");
        },
        blocked: () =>
          this.emit({
            ...this.snap,
            status: "unsaved",
            error:
              "Storage upgrade is blocked. Close other SpicyBrain tabs, then retry. Keep or download your draft.",
          }),
        blocking: () => {
          this.db?.close();
          this.db = undefined;
          this.emit({
            ...this.snap,
            status: "unsaved",
            error:
              "Another tab needs a storage upgrade. Download unsaved work and reload.",
          });
        },
        terminated: () => {
          this.db = undefined;
          this.emit({
            ...this.snap,
            status: "unsaved",
            error:
              "Browser storage disconnected. Download your unsaved work before reloading.",
          });
        },
      });
      const tx = this.db.transaction("study", "readwrite");
      const saved = await tx.store.get("root");
      const data = saved ? migrateState(saved) : emptyState();
      if (saved?.schemaVersion === 1) await tx.store.put(data, "root");
      await tx.done;
      // A blocked upgrade may have allowed edits in memory. Replay, never erase them.
      this.emit({
        data: this.pending.reduce((s, op) => op(s), data),
        status: this.pending.length ? "saving" : "saved",
        error: null,
      });
      if (this.pending.length) await this.change((s) => s);
    } catch {
      this.emit({
        ...this.snap,
        status: "unsaved",
        error:
          "Browser storage is unavailable or unreadable. Your changes stay in this tab only. Download recovery data before leaving.",
      });
    }
  }
  change(fn: (s: StudyState) => StudyState) {
    const data = fn(this.snap.data);
    this.pending.push(fn);
    this.emit({ data, status: "saving", error: null });
    this.queue = this.queue.then(async () => {
      if (!this.pending.length) return;
      const batch = [...this.pending];
      try {
        if (!this.db) throw Error("Storage unavailable");
        this.fault?.();
        const tx = this.db.transaction("study", "readwrite");
        const stored = await tx.store.get("root");
        const combined = validateState(
          batch.reduce(
            (s, op) => op(s),
            stored ? migrateState(stored) : emptyState(),
          ),
        );
        await tx.store.put(combined, "root");
        await tx.done;
        this.pending.splice(0, batch.length);
        this.emit({
          data: this.pending.reduce((s, op) => op(s), combined),
          status: this.pending.length ? "saving" : "saved",
          error: null,
        });
      } catch {
        this.emit({
          ...this.snap,
          status: "unsaved",
          error:
            "Not saved in this browser. Your draft is still here. Download recovery data, or retry saving.",
        });
      }
    });
    return this.queue;
  }
  async replace(next: StudyState) {
    validateState(next);
    await this.queue;
    if (!this.db)
      throw Error("Storage unavailable. Existing data was not replaced.");
    const tx = this.db.transaction("study", "readwrite");
    try {
      await tx.store.put(next, "root");
      this.fault?.();
      await tx.done;
      this.pending = [];
      this.emit({ data: next, status: "saved", error: null });
    } catch (e) {
      try {
        tx.abort();
      } catch {
        /* Already aborted. */
      }
      await tx.done.catch(() => {});
      throw e;
    }
  }
  async import(next: StudyState, mode: "merge" | "replace") {
    await this.queue;
    await this.replace(
      mode === "merge" ? mergeStates(this.snap.data, next) : next,
    );
  }
  flush = () => this.queue;
  close() {
    this.db?.close();
  }
}
