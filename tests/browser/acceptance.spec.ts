import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile, readdir } from "node:fs/promises";
import { emptyState, exportText } from "../../src/study";
import { ready, nav, stored, noOverflow, shot } from "./helpers";
const lesson = "dbxfe-m01-l01",
  section = `${lesson}-understand`;
const marker = "SYNTHETIC-ONLY-COPPER-KITE-48291";
for (const base of ["/", "/SpicyBrain/"])
  test(`A B F root/base navigation and persistence ${base}`, async ({
    page,
    browserName,
  }) => {
    test.skip(browserName !== "chromium");
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    const requests: string[] = [];
    page.on("request", (r) =>
      requests.push(r.url() + " " + (r.postData() ?? "")),
    );
    await ready(page, base);
    await expect(
      page.getByRole("heading", { name:"One idea. A little clearer." }),
    ).toBeVisible();
    await shot(page, base === "/" ? "01-start-desktop" : "01-start-nested");
    await page
      .getByRole("navigation", { name: "Main navigation" })
      .getByRole("link", { name: "Courses", exact: true })
      .click();
    await expect(page.getByText("16 modules",{exact:true})).toBeVisible();
    await page.locator(".teacher-course-card").click();
    await expect(page.locator(".teacher-module-map>li")).toHaveCount(16);
    await shot(page, "02-course-map");
    await nav(page, `#/lesson/${lesson}/${section}`);
    await expect(page.locator(`#${section}`)).toBeVisible();
    await page
      .locator(`#${section}`)
      .getByText("Notes for this section", { exact: true })
      .click();
    await page
      .locator(`#${section}`)
      .getByLabel("Your lesson note")
      .fill(marker + "\nA long note " + "with a useful question. ".repeat(35));
    await page
      .locator(`#${section}`)
      .getByLabel("Unresolved question", { exact: true })
      .check();
    await page
      .locator(`#${section}`)
      .getByRole("button", { name: "Bookmark section", exact: true })
      .click();
    await expect
      .poll(async () =>
        (await stored(page))?.notes[`note-${section}`]?.text.startsWith(marker),
      )
      .toBe(true);
    await expect
      .poll(async () => (await stored(page))?.resume?.sectionId)
      .toBe(section);
    expect(Object.keys((await stored(page)).completions)).toHaveLength(0);
    await page.reload();
    await expect(
      page.locator(`#${section}`).getByLabel("Your lesson note"),
    ).toHaveValue(new RegExp(marker));
    await page.getByRole("button", { name: "Focus mode", exact: true }).click();
    await expect(
      page.getByRole("button", { name: "Exit focus mode" }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Exit focus mode" }).click();
    await nav(page, `#/lesson/${lesson}/${lesson}-deeper`);
    await page.getByText("Expand technical detail", { exact: true }).click();
    await expect(page.locator(".depth")).toHaveAttribute("open", "");
    await nav(page, `#/lesson/${lesson}/${lesson}-see`);
    const opener = page.getByRole("button", {
      name: "Open diagram",
      exact: true,
    });
    await opener.click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.getByRole("button", { name: "Zoom in" }).click();
    await page.getByRole("button", { name: "Reset zoom" }).click();
    await shot(page, "03-diagram");
    await page.keyboard.press("Escape");
    await expect(opener).toBeFocused();
    await page.getByText("Read the text equivalent", { exact: true }).click();
    await nav(page, `#/lesson/${lesson}/${section}`);
    await page
      .locator(`#${section}`)
      .getByRole("button", { name: "Mark section complete", exact: true })
      .click();
    await expect
      .poll(
        async () =>
          (await stored(page))?.completions[`complete-${section}`]?.completed,
      )
      .toBe(true);
    await shot(page, "04-reader");
    await nav(page, "#/");
    await page.getByRole("link", { name: "Resume saved lesson" }).click();
    await expect(page).toHaveURL(new RegExp(lesson));
    await page.goBack();
    await expect(
      page.getByRole("link", { name: "Resume saved lesson" }),
    ).toBeVisible();
    await page.goForward();
    await expect(page.locator(".reader")).toBeVisible();
    await nav(page, "#/search");
    for (const query of ["CDC", "customer", "decision"]) {
      await page.getByLabel("Search courses, concepts, or notes").fill(query);
      await expect(page.locator(".search-result").first()).toBeVisible();
    }
    await page.getByLabel("Search courses, concepts, or notes").fill(marker);
    await expect(page.locator(".search-result")).toHaveCount(1);
    await expect(page.locator(".search-result")).toContainText("Personal note");
    await shot(page, "05-search");
    await page.locator(".search-result").click();
    await page
      .getByLabel("Your lesson note")
      .fill(marker + " final navigation edit");
    await nav(page, "#/courses");
    await nav(page, `#/notebook/note-${section}`);
    await expect(page.getByLabel("Your lesson note")).toHaveValue(
      marker + " final navigation edit",
    );
    await shot(page, "06-notebook");
    expect(requests.every((r) => !r.includes(marker))).toBe(true);
    expect(requests.every((r) => r.startsWith("http://127.0.0.1:4183/"))).toBe(
      true,
    );
    expect(page.url()).not.toContain(marker);
    expect(errors).toEqual([]);
  });
test("C objective attempts, unanswered and double submission; old evidence retained", async ({
  page,
}) => {
  await ready(page, `/#/lesson/${lesson}/${lesson}-revisit`);
  const check = page.locator(".knowledge-check").first();
  await check
    .getByRole("button", { name: "Check answer", exact: true })
    .click();
  await expect(check.getByRole("alert")).toHaveText(
    "Choose an answer before checking.",
  );
  await check.locator('input[value$="-b"]').check();
  await check
    .getByRole("button", { name: "Check answer", exact: true })
    .evaluate((b: HTMLButtonElement) => {
      b.click();
      b.click();
    });
  await expect(
    check.getByText("Revisit the reasoning.", { exact: true }),
  ).toBeVisible();
  await expect(check.locator(".answer-feedback p")).toHaveCount(4);
  await expect
    .poll(async () => Object.keys((await stored(page)).attempts).length)
    .toBe(1);
  await check.getByRole("button", { name: "Try again", exact: true }).click();
  await check.locator('input[value$="-a"]').check();
  await check
    .getByRole("button", { name: "Check answer", exact: true })
    .click();
  await expect(check.getByText("2 saved attempts · 1 correct")).toBeVisible();
  const attempts = Object.values((await stored(page)).attempts);
  expect(attempts.map((a) => a.correct)).toEqual([false, true]);
  expect(
    attempts.every(
      (a) => a.contentVersion === "1.0.0" && a.questionRevision === "1",
    ),
  ).toBe(true);
});
test("D real clock, reveal before rating, interruption, four due dates and extra practice", async ({
  page,
}) => {
  const at = new Date("2026-03-08T06:59:59.000Z");
  await page.clock.setFixedTime(at);
  await ready(page, "/#/settings");
  await page.getByLabel("New cards per introduction").selectOption("5");
  await page.getByLabel("Cards per review session").selectOption("1");
  await nav(page, "#/review");
  await expect(
    page.getByRole("button", { name: "Review due cards" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Introduce new cards" }),
  ).toBeDisabled();
  await page.getByLabel("Choose lessons").selectOption("all");
  await page.getByRole("button", { name: "Introduce new cards" }).click();
  for (const rating of ["Again", "Hard", "Good", "Easy"]) {
    await expect(
      page.getByRole("button", { name: rating, exact: true }),
    ).toBeDisabled();
    await page
      .getByRole("button", { name: "Reveal answer", exact: true })
      .click();
    await page
      .getByRole("button", { name: rating, exact: true })
      .evaluate((b: HTMLButtonElement) => {
        b.click();
        b.click();
      });
    await expect(
      page.getByRole("button", { name: "Reveal answer", exact: true }),
    ).toBeVisible();
  }
  const before = await stored(page);
  expect(Object.keys(before.reviews)).toHaveLength(4);
  expect(Object.values(before.reviews).map((r) => r.dueAt)).toEqual([
    "2026-03-08T07:09:59.000Z",
    "2026-03-09T06:59:59.000Z",
    "2026-03-11T06:59:59.000Z",
    "2026-03-15T06:59:59.000Z",
  ]);
  await page.reload();
  expect((await stored(page)).reviews).toEqual(before.reviews);
  await page.clock.setFixedTime(new Date("2026-03-08T07:09:58.999Z"));
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Review due cards" }),
  ).toBeDisabled();
  await page.clock.setFixedTime(new Date("2026-03-08T07:09:59.000Z"));
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Review due cards" }),
  ).toBeEnabled();
  await page.getByLabel("Choose lessons").selectOption("all");
  await page
    .getByRole("button", { name: "Extra practice", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Reveal answer", exact: true })
    .click();
  await shot(page, "07-review");
  await page.getByRole("button", { name: "Next practice card" }).click();
  await expect(
    page.getByText("That is enough for this session.", { exact: true }),
  ).toBeVisible();
  const after = await stored(page);
  expect(after.schedules).toEqual(before.schedules);
  expect(after.reviews).toEqual(before.reviews);
  expect(Object.keys(after.extraPractice)).toHaveLength(1);
});
test("E scenario and complete capstone draft/model/rubric journey", async ({
  page,
}) => {
  await ready(page, "/#/practice");
  await expect(page.locator(".practice-row")).toHaveCount(13);
  for (const id of ["dbxfe-m02-scenario", "dbxfe-capstone"]) {
    await nav(page, `#/practice/${id}`);
    await page
      .getByRole("textbox", { name: "Your response", exact: true })
      .fill(
        "Synthetic engagement submission: " +
          "owner, evidence, reversible decision; ".repeat(45),
      );
    const disclosures = page.locator(".stakeholder summary");
    for (let i = 0; i < (await disclosures.count()); i++)
      await disclosures.nth(i).click();
    await page
      .getByText("Reveal model response and reasoning", { exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "One defensible response" }),
    ).toBeVisible();
    if (id === "dbxfe-capstone") {
      expect(await page.locator(".model-response").innerText()).toMatch(
        /rollback/i,
      );
      expect(await page.locator(".model-response").innerText()).toMatch(
        /sensitivity/i,
      );
    }
    const rubrics = page.locator(".rubric");
    for (let i = 0; i < (await rubrics.count()); i++)
      await rubrics.nth(i).getByRole("radio").nth(1).check();
    await page.getByRole("button", { name: "Record self-assessment" }).click();
    await expect(
      page.getByText("1 self-assessments recorded", { exact: true }),
    ).toBeVisible();
    await page.reload();
    await expect(
      page.getByRole("textbox", { name: "Your response", exact: true }),
    ).toHaveValue(/Synthetic engagement/);
    await shot(page, id === "dbxfe-capstone" ? "09-capstone" : "08-practice");
  }
  expect(Object.keys((await stored(page)).assessments)).toHaveLength(2);
});
test("G export clean-context import, duplicate/conflict/unknown previews, replace cancel/confirm/reset", async ({
  page,
  browser,
}) => {
  await ready(page, `/#/lesson/${lesson}/${section}`);
  await page
    .locator(`#${section}`)
    .getByText("Notes for this section", { exact: true })
    .click();
  await page
    .locator(`#${section}`)
    .getByLabel("Your lesson note")
    .fill("Synthetic transfer original");
  await nav(page, "#/settings");
  const downloadPromise = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export all study data", exact: true })
    .click();
  const download = await downloadPromise;
  const raw = await readFile((await download.path())!, "utf8");
  const exported = JSON.parse(raw).state;
  const context = await browser.newContext(),
    other = await context.newPage();
  await ready(other, "http://127.0.0.1:4183/#/settings");
  const upload = async (text: string) =>
    other.getByLabel("Study data file").setInputFiles({
      name: "synthetic.json",
      mimeType: "application/json",
      buffer: Buffer.from(text),
    });
  await upload(raw);
  await expect(
    other.getByRole("heading", { name: "Import preview" }),
  ).toBeVisible();
  await shot(other, "10-import-preview");
  await other
    .getByRole("button", { name: "Merge import", exact: true })
    .click();
  await expect(
    other.getByText("Import committed.", { exact: false }),
  ).toBeVisible();
  expect(await stored(other)).toEqual(exported);
  await upload(raw);
  await other
    .getByRole("button", { name: "Merge import", exact: true })
    .click();
  expect(await stored(other)).toEqual(exported);
  const conflict = structuredClone(exported);
  conflict.notes[`note-${section}`].text =
    "Synthetic transfer conflicting text";
  conflict.notes[`note-${section}`].updatedAt = "2099-01-01T00:00:00.000Z";
  conflict.notes["removed-note"] = {
    ...conflict.notes[`note-${section}`],
    id: "removed-note",
    lessonId: "removed-lesson",
    sectionId: "removed-section",
    text: "<script>window.badImport=true</script>",
  };
  await upload(exportText(conflict));
  await expect(
    other.getByText("1 conflicting note/draft texts.", { exact: false }),
  ).toBeVisible();
  await expect(
    other.getByText("2 unknown content references.", { exact: false }),
  ).toBeVisible();
  await other
    .getByRole("button", { name: "Merge import", exact: true })
    .click();
  await expect
    .poll(async () => Object.keys((await stored(other)).notes).length)
    .toBe(3);
  await upload(exportText(emptyState()));
  await other.getByLabel("Import method").selectOption("replace");
  await expect(
    other.getByRole("button", { name: "Confirm replacement" }),
  ).toBeDisabled();
  await other.getByRole("button", { name: "Cancel import" }).click();
  expect(Object.keys((await stored(other)).notes)).toHaveLength(3);
  await upload("{");
  await expect(
    other.getByText(
      "This file is invalid, too large, or from an unsupported future version. No data changed.",
    ),
  ).toBeVisible();
  await upload(
    JSON.stringify({
      format: "SpicyBrain study data",
      exportedAt: "2026-09-19T00:00:00.000Z",
      state: { ...emptyState(), schemaVersion: 99 },
    }),
  );
  expect(Object.keys((await stored(other)).notes)).toHaveLength(3);
  await nav(other, "#/notebook/removed-note");
  await expect(other.getByLabel("Your lesson note")).toHaveValue(
    "<script>window.badImport=true</script>",
  );
  expect(await other.evaluate(() => Object.hasOwn(window, "badImport"))).toBe(
    false,
  );
  await other.getByRole("link", { name: "Return to source" }).click();
  await expect(
    other.getByRole("heading", {
      name: "This lesson is no longer in the catalog.",
    }),
  ).toBeVisible();
  await nav(other, "#/settings");
  await upload(raw);
  await other.getByLabel("Import method").selectOption("replace");
  await other
    .getByLabel("I understand that replacement removes my current study data.")
    .check();
  await other.getByRole("button", { name: "Confirm replacement" }).click();
  await expect(
    other.getByText("Import committed.", { exact: false }),
  ).toBeVisible();
  expect(await stored(other)).toEqual(exported);
  await other.getByText("Reset study data", { exact: true }).click();
  await expect(
    other.getByRole("button", { name: "Permanently reset local study data" }),
  ).toBeDisabled();
  await other.getByLabel("Type RESET to confirm").fill("RESET");
  await other
    .getByRole("button", { name: "Permanently reset local study data" })
    .click();
  await expect
    .poll(async () => Object.keys((await stored(other)).notes).length)
    .toBe(0);
  await context.close();
});
test("H browser denied/quota storage, recoverable text and missing asset/route", async ({
  browser,
}) => {
  for (const mode of ["denied", "quota"]) {
    const context = await browser.newContext();
    await context.addInitScript((mode) => {
      if (mode === "denied")
        Object.defineProperty(window, "indexedDB", {
          get() {
            throw new DOMException("Synthetic denial", "SecurityError");
          },
        });
      else
        IDBObjectStore.prototype.put = function () {
          throw new DOMException(
            "Synthetic full storage",
            "QuotaExceededError",
          );
        };
    }, mode);
    const page = await context.newPage();
    await ready(page, `http://127.0.0.1:4183/#/lesson/${lesson}/${section}`);
    await page
      .locator(`#${section}`)
      .getByText("Notes for this section", { exact: true })
      .click();
    await page
      .locator(`#${section}`)
      .getByLabel("Your lesson note")
      .fill("Synthetic unsaved recovery final text");
    await expect(page.getByRole("alert")).toContainText(/storage|Not saved/i);
    await expect(
      page
        .locator(`#${section}`)
        .getByText("Unsaved · keep this tab open", { exact: true }),
    ).toBeVisible();
    await nav(page, "#/notebook");
    await expect(page.getByLabel("Your lesson note")).toHaveValue(
      "Synthetic unsaved recovery final text",
    );
    const promise = page.waitForEvent("download");
    await page.getByRole("button", { name: "Download recovery data" }).click();
    const download = await promise;
    expect(await readFile((await download.path())!, "utf8")).toContain(
      "Synthetic unsaved recovery final text",
    );
    await shot(page, `11-storage-${mode}`);
    await context.close();
  }
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.route("**/content-assets/*.svg", (r) => r.abort());
  await ready(page, `http://127.0.0.1:4183/#/lesson/${lesson}/${lesson}-see`);
  await expect(
    page.getByText("The diagram could not load.", { exact: false }).first(),
  ).toBeVisible();
  await page.getByText("Read the text equivalent", { exact: true }).click();
  await nav(page, "#/not-a-page");
  await expect(
    page.getByRole("heading", { name: "Let’s find your way back." }),
  ).toBeVisible();
  await context.close();
});
test("H actual blocked IndexedDB upgrade recovers edits after old connection closes", async ({
  page,
}) => {
  await page.addInitScript(async () => {
    const request = indexedDB.open("spicybrain-study-v2", 1);
    request.onupgradeneeded = () => request.result.createObjectStore("study");
    await new Promise<void>((resolve) => {
      request.onsuccess = () => resolve();
    });
    Object.assign(window, { syntheticOldDB: request.result });
  });
  await ready(page, `/#/lesson/${lesson}/${section}`);
  await expect(page.getByRole("alert")).toContainText("blocked");
  await page
    .locator(`#${section}`)
    .getByText("Notes for this section", { exact: true })
    .click();
  await page
    .locator(`#${section}`)
    .getByLabel("Your lesson note")
    .fill("Synthetic edit while blocked");
  await page.evaluate(() => {
    (
      window as unknown as { syntheticOldDB: IDBDatabase }
    ).syntheticOldDB.close();
  });
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect
    .poll(async () => (await stored(page))?.notes[`note-${section}`]?.text)
    .toBe("Synthetic edit while blocked");
});
test("L keyboard, light/dark, axe, mobile 390 and 320 at 200% text; no overflow", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await ready(page);
  await page.keyboard.press("Tab");
  await expect(page.locator(":focus")).toBeVisible();
  await nav(page, "#/settings");
  for (const theme of ["light", "dark"]) {
    await page.getByLabel("Theme").selectOption(theme);
    await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(
      results.violations.map((v) => ({
        id: v.id,
        nodes: v.nodes.map((n) => n.target),
      })),
    ).toEqual([]);
    await shot(page, `12-settings-${theme}`);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  for (const hash of [
    "#/",
    "#/courses",
    `#/lesson/${lesson}/${lesson}-see`,
    "#/practice/dbxfe-m04-scenario",
    "#/review",
    "#/search",
    "#/notebook",
    "#/settings",
  ]) {
    await nav(page, hash);
    await noOverflow(page);
    await shot(page, "mobile-" + hash.split("/")[1]);
  }
  await page.setViewportSize({ width: 320, height: 800 });
  await page.evaluate(() => {
    const scale = (rules: CSSRuleList) => {
      for (const rule of rules) {
        if (rule instanceof CSSStyleRule && rule.style.fontSize)
          rule.style.fontSize = `calc((${rule.style.fontSize}) * 2)`;
        if ("cssRules" in rule) scale((rule as CSSGroupingRule).cssRules);
      }
    };
    for (const sheet of document.styleSheets) scale(sheet.cssRules);
  });
  for (const hash of [
    "#/courses",
    `#/lesson/${lesson}/${section}`,
    "#/practice/dbxfe-capstone",
    "#/settings",
  ]) {
    await nav(page, hash);
    await noOverflow(page);
  }
  await shot(page, "13-narrow-text-zoom");
});
test("H synthetic private marker absent from production artifacts", async () => {
  for (const folder of ["dist/assets", "dist-nested/assets"])
    for (const file of await readdir(folder)) {
      if (/\.(js|css|json)$/.test(file))
        expect(await readFile(`${folder}/${file}`, "utf8")).not.toContain(
          marker,
        );
    }
});
test("L keyboard-only note entry and touch mobile diagram/review", async ({
  page,
  browser,
}) => {
  await ready(page, `/#/lesson/${lesson}/${lesson}-why`);
  let reached = false;
  for (let i = 0; i < 100; i++) {
    await page.keyboard.press("Tab");
    if (
      await page
        .locator(":focus")
        .evaluate(
          (e) =>
            e.tagName === "SUMMARY" &&
            e.textContent === "Notes for this section",
        )
    ) {
      reached = true;
      break;
    }
  }
  expect(reached).toBe(true);
  expect(
    await page
      .locator(":focus")
      .evaluate((e) => getComputedStyle(e).outlineStyle),
  ).not.toBe("none");
  await page.keyboard.press("Enter");
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("Your lesson note").first()).toBeFocused();
  await page.keyboard.type("Synthetic keyboard-only note");
  await expect
    .poll(async () => (await stored(page))?.notes[`note-${lesson}-why`]?.text)
    .toBe("Synthetic keyboard-only note");
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    hasTouch: true,
    isMobile: true,
  });
  const mobile = await context.newPage();
  await ready(mobile, `http://127.0.0.1:4183/#/lesson/${lesson}/${lesson}-see`);
  await mobile.getByRole("button", { name: "Open diagram", exact: true }).tap();
  await mobile.getByRole("button", { name: "Zoom in" }).tap();
  await mobile.getByRole("button", { name: "Reset zoom" }).tap();
  await mobile.getByRole("button", { name: "Close diagram" }).tap();
  await noOverflow(mobile);
  await nav(mobile, `#/review/${lesson}`);
  await mobile.getByRole("button", { name: "Introduce new cards" }).tap();
  await mobile
    .getByRole("button", { name: "Reveal answer", exact: true })
    .tap();
  await mobile.getByRole("button", { name: "Good", exact: true }).tap();
  await expect
    .poll(async () => Object.keys((await stored(mobile)).reviews).length)
    .toBe(1);
  await context.close();
});
test("H native transaction abort during replacement retains the old snapshot", async ({
  page,
}) => {
  await ready(page, "/#/settings");
  await page.getByLabel("Theme").selectOption("dark");
  const before = await stored(page);
  await page.getByLabel("Study data file").setInputFiles({
    name: "synthetic-replace.json",
    mimeType: "application/json",
    buffer: Buffer.from(exportText(emptyState())),
  });
  await page.getByLabel("Import method").selectOption("replace");
  await page
    .getByLabel("I understand that replacement removes my current study data.")
    .check();
  await page.evaluate(() => {
    const original = IDBObjectStore.prototype.put;
    IDBObjectStore.prototype.put = function (value, key) {
      original.call(this, value, key);
      throw new DOMException(
        "Synthetic fault after enqueueing replacement",
        "QuotaExceededError",
      );
    };
  });
  await page.getByRole("button", { name: "Confirm replacement" }).click();
  await expect(
    page.getByText(
      "Import could not be committed, or immutable events conflict.",
      { exact: false },
    ),
  ).toBeVisible();
  expect(await stored(page)).toEqual(before);
  await page.reload();
  expect(await stored(page)).toEqual(before);
});
