import { test, expect } from "@playwright/test";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { createHash } from "node:crypto";
import type { Card, Question } from "../../src/content-schema";
import type { CatalogCourse } from "../../src/catalog-types";
import { applyReview, emptyState, stateSchema } from "../../src/study";
import { ready, nav, stored, noOverflow, shot } from "./helpers";

const id = "dbxfe-record-resolution";
const prior = JSON.parse(
  await readFile("tests/fixtures/record-resolution-v1.json", "utf8"),
) as {
  sourceCommit: string;
  contentVersion: string;
  question: Question;
  card: Card;
};
const courses = JSON.parse(
  await readFile("src/generated/catalog.json", "utf8"),
) as CatalogCourse[];
const course = courses.find((c) => c.id === "dbxfe")!;
const lesson = course.modules
  .flatMap((m) => m.lessons)
  .find((l) => l.id === id)!;
const checksum = (data: Buffer) =>
  createHash("sha256").update(data).digest("hex");

for (const [width, base] of [
  [1440, "/"],
  [390, "/SpicyBrain/"],
] as const) {
  test(`Corrected publication policy: reader, source, download and prior evidence at ${width}px`, async ({
    page,
    browserName,
  }) => {
    const at = "2026-09-19T12:00:00.000Z";
    await page.clock.setFixedTime(new Date("2026-09-19T21:00:00.000Z"));
    const sectionId = `${id}-stages`;
    const noteId = `note-${sectionId}`;
    const initial = emptyState(at);
    initial.disclosureAccepted = true;
    initial.notes[noteId] = {
      id: noteId,
      courseId: course.id,
      lessonId: id,
      sectionId,
      text: "SYNTHETIC earlier-version note: preserve provenance evidence.",
      question: true,
      createdAt: at,
      updatedAt: at,
    };
    initial.completions[`complete-${id}`] = {
      id: `complete-${id}`,
      courseId: course.id,
      lessonId: id,
      contentVersion: prior.contentVersion,
      completed: true,
      updatedAt: at,
    };
    initial.completions[`complete-${sectionId}`] = {
      id: `complete-${sectionId}`,
      courseId: course.id,
      lessonId: id,
      sectionId,
      contentVersion: prior.contentVersion,
      completed: true,
      updatedAt: at,
    };
    initial.attempts["prior-resolution-attempt"] = {
      id: "prior-resolution-attempt",
      courseId: course.id,
      lessonId: id,
      questionId: prior.question.id,
      questionRevision: prior.question.revision,
      contentVersion: prior.contentVersion,
      at,
      optionId: prior.question.correctOptionId,
      correctOptionId: prior.question.correctOptionId,
      correct: true,
      conceptIds: prior.question.conceptIds,
      snapshot: {
        prompt: prior.question.prompt,
        options: prior.question.options,
      },
    };
    const seeded = applyReview(
      initial,
      prior.card,
      course.id,
      "Good",
      "prior-resolution-review",
      at,
    );
    expect(Date.parse(seeded.schedules[prior.card.id].dueAt)).toBeGreaterThan(
      Date.parse("2026-09-19T21:00:00.000Z"),
    );
    stateSchema.parse(seeded);
    await page.setViewportSize({ width, height: width === 1440 ? 1000 : 844 });
    await ready(page, base);
    await page.evaluate(async (state) => {
      await new Promise<void>((resolve, reject) => {
        const request = indexedDB.open("spicybrain-study-v2", 2);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
          const db = request.result;
          const tx = db.transaction("study", "readwrite");
          tx.objectStore("study").put(state, "root");
          tx.oncomplete = () => {
            db.close();
            resolve();
          };
          tx.onerror = () => reject(tx.error);
        };
      });
    }, seeded);
    await page.reload();
    await nav(page, `#/lesson/${id}?path=reliable-data-foundations`);
    await expect(
      page.getByText(
        `You completed version ${prior.contentVersion}. This is version ${lesson.contentVersion}`,
        { exact: false },
      ),
    ).toBeVisible();
    await page.evaluate(() => scrollTo(0, 0));
    await shot(page, `publication-gate-revision-${width}`);
    await expect(
      page.locator(`#${sectionId}`).getByLabel("Your lesson note"),
    ).toHaveValue(seeded.notes[noteId].text);
    await expect(
      page
        .locator(`#${sectionId}`)
        .getByRole("button", { name: "Mark revised section complete" }),
    ).toBeVisible();
    const worked = page.locator(`#${id}-worked`);
    await expect(worked).toContainText("unkeyed");
    await worked
      .getByRole("heading", {
        name: "A conflict without an identifiable inspection",
      })
      .evaluate((element) => element.scrollIntoView({ block: "start" }));
    await noOverflow(page);
    await shot(page, `publication-gate-example-${width}`);
    const solution = page.locator(`#${id}-solution`);
    await expect(solution.locator("details.depth")).not.toHaveAttribute(
      "open",
      "",
    );
    await solution
      .getByText("Reveal explained solution", { exact: true })
      .click();
    await expect(solution).toContainText("blocked_no_snapshot");
    await expect(solution).toContainText("stale_previous");
    await solution
      .getByText("For the unkeyed first run,", { exact: false })
      .evaluate((element) => element.scrollIntoView({ block: "start" }));
    await shot(page, `publication-gate-solution-${width}`);
    const sourceHashes: Record<string, string> = {};
    for (const [section, filename] of [
      ["reference-code", "reference.py"],
      ["spark-code", "spark_transform.py"],
    ]) {
      const source = await readFile(
        `content/exercises/reliable-data/solutions/${filename}`,
        "utf8",
      );
      const area = page.locator(`#${id}-${section}`);
      await area.getByText("Expand technical detail", { exact: true }).click();
      // Verify the complete rendered source, not a checksum label or excerpt.
      expect(
        (await area.locator("pre code").textContent())
          ?.replace(/\r\n/g, "\n")
          .trimEnd(),
      ).toBe(source.replace(/\r\n/g, "\n").trimEnd());
      sourceHashes[filename] = checksum(
        Buffer.from(source.replace(/\r\n/g, "\n")),
      );
      await area.scrollIntoViewIfNeeded();
      await noOverflow(page);
      await shot(page, `publication-gate-${section}-${width}`);
      await area.locator("pre code").evaluate((element) => {
        const node = element.firstChild!;
        const offset = node.textContent!.indexOf('"publication_allowed"');
        if (offset < 0)
          throw new Error("Missing publication decision in rendered source");
        const range = document.createRange();
        range.setStart(node, offset);
        range.setEnd(node, offset + 21);
        scrollBy(0, range.getBoundingClientRect().top - 180);
        const pre = element.closest("pre")!;
        pre.scrollLeft = Math.max(
          0,
          range.getBoundingClientRect().left -
            pre.getBoundingClientRect().left -
            24,
        );
      });
      await shot(page, `publication-gate-decision-${section}-${width}`);
    }
    await expect(
      page.getByText("This question has been revised.", { exact: false }),
    ).toBeVisible();
    const downloadEvent = page.waitForEvent("download");
    await page.locator(".lesson-downloads a").first().click();
    const download = await downloadEvent;
    expect(await download.failure()).toBeNull();
    const bytes = await readFile((await download.path())!);
    const declared = course.downloads!.find((d) =>
      lesson.downloadIds!.includes(d.id),
    )!;
    expect(checksum(bytes)).toBe(declared.sha256);
    expect(bytes).toEqual(await readFile(`content/downloads/${declared.path}`));
    await nav(page, "#/review");
    await page.getByRole("button", { name: /Review due/ }).click();
    await expect(
      page.getByText("Answer revised · review this version", { exact: true }),
    ).toBeVisible();
    await shot(page, `publication-gate-review-${width}`);
    await page.reload();
    const after = await stored(page);
    for (const family of [
      "notes",
      "completions",
      "attempts",
      "reviews",
      "schedules",
    ] as const) {
      expect(after[family]).toEqual(seeded[family]);
    }
    await mkdir("test-results/evidence", { recursive: true });
    await writeFile(
      `test-results/evidence/publication-gate-reader-${width}.json`,
      JSON.stringify(
        {
          browser: browserName,
          browserVersion: page.context().browser()?.version(),
          viewport: { width },
          base,
          baselineSource: prior.sourceCommit,
          earlierVersion: prior.contentVersion,
          currentVersion: lesson.contentVersion,
          oldQuestionRevision: prior.question.revision,
          currentQuestionRevision: lesson.questions.find(
            (q) => q.id === prior.question.id,
          )!.revision,
          oldCardRevision: prior.card.revision,
          currentCardRevision: lesson.cards.find((c) => c.id === prior.card.id)!
            .revision,
          preservedFamilies: [
            "notes",
            "completions",
            "attempts",
            "reviews",
            "schedules",
          ],
          originalTimestampsPreserved: true,
          renderedSourceSha256NormalizedLF: sourceHashes,
          actualDownloadedSha256: checksum(bytes),
          result: "pass",
        },
        null,
        2,
      ) + "\n",
    );
  });
}
