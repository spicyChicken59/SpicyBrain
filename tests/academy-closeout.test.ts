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

test("Genie access teaching distinguishes standalone queries, dashboard companions and private conversations", async () => {
  const module = JSON.parse(await readFile("content/teaching/dbxfe/dbxfe-genie.json", "utf8")) as TeachingModule;
  const access = module.beats.find((b) => b.id === "dbxfe-genie-access")!;
  const review = module.beats.find((b) => b.id === "dbxfe-genie-review")!;
  const dashboard = module.extensionCards.find((c) => c.id === "dbxfe-genie-extension-dashboard")!;
  assert.match(access.handbook.markdown, /standalone Genie Agent/);
  assert.match(access.handbook.markdown, /publisher's data grants/);
  assert.match(access.handbook.markdown, /shared as agent context/);
  assert.match(review.handbook.markdown, /not their full exchange or results/);
  assert.equal(dashboard.revision, "2");
  assert.match(dashboard.explanation, /cannot edit companion instructions/);
});

test("Genie Code closeout replaces stale mode and administrator instructions with versioned teaching", async () => {
  const module = JSON.parse(await readFile("content/teaching/dbxfe/dbxfe-ai-assist.json", "utf8")) as TeachingModule;
  const cards = module.extensionCards;
  const admin = cards.find((c) => c.id === "dbxfe-ai-assist-extension-admin")!;
  const agent = cards.find((c) => c.id === "dbxfe-ai-assist-extension-agent")!;
  assert.equal(admin.revision, "2");
  assert.equal(agent.revision, "2");
  assert.match(admin.answer, /API changes remain available until November 1, 2026/);
  assert.match(agent.explanation, /Auto-approve is the first-use default/);
  assert.match(agent.explanation, /not a security boundary/);
  assert.doesNotMatch(JSON.stringify(module), /Agent mode marked Preview|three modes|can disable it for every workspace/);
  const canonical = JSON.parse(await readFile("content/courses/dbxfe/lessons/dbxfe-ai-assist-l01.json", "utf8")) as Lesson;
  assert.equal(canonical.contentVersion, "1.2.0");
  assert.equal(canonical.cards[0].revision, "2");
});

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
  assert.equal(lesson.contentVersion, "1.2.0");
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
  const auth = teaching.beats.find((b) => b.id === "dbxfe-lakebase-auth")!;
  const sync = teaching.beats.find((b) => b.id === "dbxfe-lakebase-sync")!;
  assert.match(auth.handbook.markdown, /disable password connections by default/);
  assert.match(auth.handbook.markdown, /existing app service principal/);
  assert.match(sync.handbook.markdown, /Lakebase CDF/);
  assert.match(sync.handbook.markdown, /automatic Change Data Feed/);
  const moduleRecord = JSON.parse(
    await readFile("content/courses/dbxfe/modules/dbxfe-lakebase.json", "utf8"),
  );
  assert.match(moduleRecord.scenarios[0].model, /does not prove the queue is empty/);

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
