import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import type { TeachingModule } from "../src/teaching-schema";
import type { Lesson } from "../src/content-schema";

const modulePath = "content/teaching/dbxfe/dbxfe-lakebase.json";
const lessonPath = "content/courses/dbxfe/lessons/dbxfe-lakebase-l01.json";
const teaching = JSON.parse(
  await readFile(modulePath, "utf8"),
) as TeachingModule;
const lesson = JSON.parse(await readFile(lessonPath, "utf8")) as Lesson;

test("Lakebase restore correction keeps every teaching route consistent and moves assessed revisions", async () => {
  const beat = teaching.beats.find((b) => b.id === "dbxfe-lakebase-branches")!;
  const visual = teaching.visuals.find((v) => v.id === beat.visualId)!;
  const check = teaching.selfQuestions.find(
    (q) => q.id === "dbxfe-lakebase-branches-self",
  )!;
  const card = lesson.cards.find((c) => c.id === "dbxfe-lakebase-l01-card12")!;
  assert.equal(beat.version, "1.1.0");
  assert.equal(check.revision, "2");
  assert.equal(card.revision, "2");
  assert.equal(lesson.contentVersion, "1.1.0");
  assert.deepEqual(
    visual.states.map((s) => s.id),
    ["incident", "branch", "restore"],
  );
  assert.match(visual.states[2].explanation, /original still has later work/i);
  assert.match(beat.handbook.markdown, /existing connections keep running/i);
  assert.match(check.modelAnswer, /cutover separately/i);
  assert.match(
    card.explanation,
    /original and its connections remain unchanged/i,
  );
  const surfaces = await Promise.all(
    [
      modulePath,
      lessonPath,
      "content/courses/dbxfe/modules/dbxfe-lakebase.json",
      "content/courses/dbxfe/lessons/dbxfe-lakebase-l01.md",
      "content/exercises/lab-l23-transactional-state/ADAPTATION.md",
    ].map((p) => readFile(p, "utf8")),
  );
  for (const text of surfaces) {
    assert.doesNotMatch(
      text,
      /restore rewinds everything|restore returns the whole branch|restore brings the 40 rows back and erases|NOTIFY \| LISTEN|rewinding a branch/i,
    );
  }
});

test("managed-pooler teaching and blocked research are not promoted by generic behavior or counts", async () => {
  const connections = teaching.beats.find(
    (b) => b.id === "dbxfe-lakebase-connections",
  )!;
  assert.equal(connections.version, "1.1.0");
  assert.match(
    connections.handbook.markdown,
    /LISTEN and NOTIFY are both unsupported/,
  );
  const media = JSON.parse(
    await readFile("docs/academy/MEDIA-DECISIONS.json", "utf8"),
  );
  assert.equal(media.totals.placements, 16);
  assert.equal(media.totals.blockedReview, 32);
  assert.equal(media.totals.noPlacement, 0);
  const labs = JSON.parse(await readFile("docs/academy/LABS.json", "utf8"));
  assert.deepEqual(labs.totals.checksByClass, {
    "local-executed": 532,
    tabletop: 53,
    "platform-guide": 34,
  });
  const ledger = JSON.parse(
    await readFile("docs/academy/CLAIM-REVIEW.json", "utf8"),
  );
  assert.equal(
    new Set(ledger.claims.map((c: { id: string }) => c.id)).size,
    ledger.claims.length,
  );
  assert.ok(ledger.totals.byStatus["pending-claim-review"] > 0);
  const acceptance = await readFile("docs/academy/ACCEPTANCE.md", "utf8");
  assert.match(acceptance, /G10 Media evidence and privacy \| BLOCKED/);
  assert.match(acceptance, /G14 Source and capability review \| BLOCKED/);
});
