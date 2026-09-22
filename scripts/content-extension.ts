import {
  cp,
  mkdtemp,
  readdir,
  readFile,
  writeFile,
  rm,
  symlink,
  rename,
} from "node:fs/promises";
import { join, resolve, extname, sep } from "node:path";
import { tmpdir } from "node:os";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createServer } from "node:http";
import { chromium, expect } from "@playwright/test";
import { buildContent, loadCourses, loadPaths, root } from "./content.ts";
import { stored } from "../tests/browser/helpers.ts";
import type { Course, Lesson } from "../src/content-schema.ts";
import type { TeachingModule } from "../src/teaching-schema.ts";
type RawCourse = Omit<Course, "modules"> & {
  modules: (Omit<Course["modules"][number], "lessons"> & {
    lessonFiles: string[];
  })[];
};
type RawLesson = Omit<Lesson, "sections"> & {
  bodyFile: string;
  sections: Omit<Lesson["sections"][number], "markdown">[];
};
const temp = await mkdtemp(join(tmpdir(), "spicybrain-extension-"));
const tempBase = resolve(tmpdir());
if (!resolve(temp).startsWith(tempBase + sep + "spicybrain-extension-"))
  throw Error("Unsafe extension-test directory");
async function removeTemporaryTree(target: string) {
  const absolute = resolve(target);
  if (absolute !== resolve(temp) && !absolute.startsWith(resolve(temp) + sep))
    throw Error("Cleanup escaped extension-test directory");
  await rm(absolute, { recursive: true, force: true });
}
async function manifest(
  folder: string,
  prefix = "",
): Promise<Record<string, string>> {
  const out: Record<string, string> = {};
  for (const f of await readdir(folder, { withFileTypes: true })) {
    const relative = prefix + f.name;
    if (
      [
        "node_modules",
        ".git",
        "dist",
        "dist-nested",
        "test-results",
        "playwright-report",
      ].includes(f.name)
    )
      continue;
    if (f.isDirectory())
      Object.assign(out, await manifest(join(folder, f.name), relative + "/"));
    else
      out[relative] = createHash("sha256")
        .update(await readFile(join(folder, f.name)))
        .digest("hex");
  }
  return out;
}
const diff = (a: Record<string, string>, b: Record<string, string>) =>
  [...new Set([...Object.keys(a), ...Object.keys(b)])]
    .sort()
    .filter((k) => a[k] !== b[k])
    .map((path) => ({ path, before: a[path] ?? null, after: b[path] ?? null }));
const build = async () => {
  const courses = await buildContent(join(temp, "content"), temp);
  execFileSync(
    process.execPath,
    [join(root, "node_modules/vite/bin/vite.js"), "build"],
    {
      cwd: temp,
      env: { ...process.env, APP_BASE: "./", APP_OUT: "dist" },
      stdio: "pipe",
    },
  );
  return courses;
};
const mime: Record<string, string> = {
  ".html": "text/html",
  ".js": "application/javascript",
  ".css": "text/css",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
};
const server = createServer(async (req, res) => {
  try {
    const path = decodeURIComponent(new URL(req.url!, "http://local").pathname),
      base = resolve(temp, "dist"),
      file = resolve(
        base,
        "." + path + (path.endsWith("/") ? "index.html" : ""),
      );
    if (!file.startsWith(base + sep)) throw Error();
    res.setHeader(
      "Content-Type",
      mime[extname(file)] || "application/octet-stream",
    );
    res.setHeader("Cache-Control", "no-store");
    res.end(await readFile(file));
  } catch {
    res.statusCode = 404;
    res.end("Not found");
  }
});
let browser: Awaited<ReturnType<typeof chromium.launch>> | undefined;
try {
  for (const path of [
    "src",
    "content",
    "public",
    "index.html",
    "vite.config.ts",
    "package.json",
    "tsconfig.json",
  ])
    await cp(join(root, path), join(temp, path), { recursive: true });
  await symlink(
    join(root, "node_modules"),
    join(temp, "node_modules"),
    process.platform === "win32" ? "junction" : "dir",
  );
  const before = await manifest(temp);
  const baselineCourseIds = (await loadCourses(join(temp, "content"))).map(
    (c) => c.id,
  );
  await cp(
    join(root, "tests/fixtures/photography/content"),
    join(temp, "content"),
    { recursive: true },
  );
  const added = await manifest(temp);
  const addition = diff(before, added);
  expect(addition.every((f) => f.path.startsWith("content/"))).toBe(true);
  let catalog = await build();
  expect(catalog.map((c) => c.id)).toEqual(
    [...baselineCourseIds, "photo"].sort(),
  );
  const photoCourse = catalog.find((c) => c.id === "photo")!;
  expect(photoCourse.modules).toHaveLength(2);
  const extensionPaths = await loadPaths(catalog, join(temp, "content"));
  expect(extensionPaths.some((path) => path.id === "photo-path")).toBe(true);
  await new Promise<void>((r) => server.listen(0, "127.0.0.1", r));
  const address = server.address();
  if (!address || typeof address === "string") throw Error("No port");
  const url = `http://127.0.0.1:${address.port}`;
  browser = await chromium.launch({
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
  });
  const go = async (hash: string) => {
    await page.goto(url + "/" + hash);
    await expect(page.locator("main h1")).toBeVisible();
  };
  await go("#/courses");
  await expect(
    page.getByRole("heading", {
      name: "Exposure and composition in photography",
    }),
  ).toBeVisible();
  await go("#/learn/roadmaps");
  await page
    .getByRole("link")
    .filter({ hasText: "Intentional photographs" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Intentional photographs", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Open next topic", exact: false })
    .click();
  await expect(page).toHaveURL(/#\/lesson\/photo-m01-l02\?path=photo-path$/);
  await go("#/learn/playbooks");
  await expect(
    page.getByRole("heading", {
      name: "A moving subject looks blurred",
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("link", {
      name: "Reason through motion and shutter duration",
      exact: true,
    })
    .click();
  await expect(page).toHaveURL(
    /#\/lesson\/photo-m01-l01\/photo-m01-l01-understand/,
  );
  // Every fixture lesson, asset, check and scenario renders through existing components.
  for (const m of photoCourse.modules) {
    for (const l of m.lessons) {
      await go(`#/lesson/${l.id}`);
      await expect(
        page.getByRole("heading", { name: l.title, exact: true }),
      ).toBeVisible();
      await expect(page.locator(".knowledge-check")).toHaveCount(2);
    }
    await go(`#/practice/${m.scenarioId}`);
    await page
      .getByText("Reveal model response and reasoning", { exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "One defensible response" }),
    ).toBeVisible();
  }
  const lid = "photo-m01-l01",
    sid = lid + "-understand";
  await go(`#/lesson/${lid}/${sid}`);
  await page
    .locator("#" + sid)
    .getByText("Notes for this section", { exact: true })
    .click();
  await page
    .locator("#" + sid)
    .getByLabel("Your lesson note")
    .fill("Synthetic photography identity note");
  await page
    .locator("#" + sid)
    .getByRole("button", { name: "Bookmark section", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Mark lesson complete", exact: true })
    .click();
  const check = page.locator(".knowledge-check").first();
  await check.locator('input[value$="-a"]').check();
  await check
    .getByRole("button", { name: "Check answer", exact: true })
    .click();
  await go(`#/lesson/${lid}/${lid}-see`);
  await page.getByRole("button", { name: "Open diagram", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  expect(
    await page
      .getByRole("dialog")
      .locator("img")
      .evaluate((e: HTMLImageElement) => e.naturalWidth),
  ).toBeGreaterThan(0);
  await page.getByRole("button", { name: "Close diagram" }).click();
  await go("#/search");
  await page.getByLabel("Search courses, concepts, or notes").fill("capture");
  await expect(
    page.locator(".search-result").filter({ hasText: "photography" }).first(),
  ).toBeVisible();
  await go(`#/review/${lid}`);
  await page.getByRole("button", { name: "Introduce new cards" }).click();
  await page
    .getByRole("button", { name: "Reveal answer", exact: true })
    .click();
  await page.getByRole("button", { name: "Good", exact: true }).click();
  await expect
    .poll(async () => Object.keys((await stored(page)).reviews).length)
    .toBe(1);
  const teachingFiles = ["photo-m01.json", "photo-m02.json"];
  const photoTeaching = await Promise.all(
    teachingFiles.map(
      async (file) =>
        JSON.parse(
          await readFile(join(temp, "content/teaching/photo", file), "utf8"),
        ) as TeachingModule,
    ),
  );
  const externalRequests: string[] = [];
  page.on("request", (request) => {
    if (/youtube|vimeo/.test(request.url()))
      externalRequests.push(request.url());
  });
  for (const module of photoTeaching) {
    const beat = module.beats[0],
      visual = module.visuals.find((v) => v.id === beat.visualId)!;
    await go(`#/module/${module.moduleId}/${beat.id}`);
    await expect(
      page.getByRole("heading", { name: module.title, exact: true }),
    ).toBeVisible();
    await page
      .getByRole("button", {
        name: new RegExp(`^${module.concepts[0].term}$`, "i"),
      })
      .first()
      .click();
    await expect(
      page.getByRole("dialog", {
        name: module.concepts[0].term + " definition",
      }),
    ).toContainText(module.concepts[0].definition);
    await page
      .getByRole("button", { name: "Close definition", exact: true })
      .click();
    await page
      .locator(".teaching-beat .teaching-visual")
      .getByRole("button", { name: visual.states[1].title, exact: false })
      .first()
      .click();
    await expect(
      page.locator(".teaching-beat .visual-stage-description:visible"),
    ).toContainText(visual.states[1].explanation);
    await page.locator(".samajh summary").click();
    await expect(page.locator(".samajh")).toContainText(beat.samajh!.boundary);
    const question = module.questions.find(
      (q) => q.id === beat.questionIds[0],
    )!;
    await page.locator(".beat-check summary").click();
    await page
      .getByRole("radio", {
        name: question.options.find((o) => o.id === question.correctOptionId)!
          .text,
        exact: true,
      })
      .check();
    await page
      .getByRole("button", { name: "Check my answer", exact: true })
      .click();
    await expect(
      page.getByText("That choice is correct.", { exact: true }),
    ).toBeVisible();
    expect((await stored(page)).completions[`beat-${beat.id}`]).toBeUndefined();
    if (module.moduleId === "photo-m01") {
      await page
        .getByRole("button", { name: "Mark this beat complete", exact: true })
        .click();
      await expect(
        page.getByRole("button", {
          name: "Marked complete · undo",
          exact: true,
        }),
      ).toBeVisible();
    }
    if (module.moduleId === "photo-m02") {
      await page.locator(".beat-media > summary").click();
      await expect(
        page
          .locator(".beat-media")
          .getByRole("link", { name: "Open original video in a new tab ↗" }),
      ).toHaveAttribute("href", "https://www.youtube.com/watch?v=hr0OprJm5ow");
      await page
        .getByText("Choose the intended story · illustrated equivalent", {
          exact: true,
        })
        .click();
      await expect(page.locator(".beat-media .teaching-visual")).toBeVisible();
      await expect(page.locator("iframe")).toHaveCount(0);
    }
    await page
      .getByRole("navigation", { name: "Module views" })
      .getByRole("link", { name: "Handbook", exact: true })
      .click();
    for (const b of module.beats)
      await expect(
        page
          .locator(".module-handbook")
          .getByRole("heading", { name: b.title, exact: true }),
      ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Print handbook", exact: true }),
    ).toBeEnabled();
    await page
      .getByRole("navigation", { name: "Module views" })
      .getByRole("link", { name: "Cards", exact: true })
      .click();
    await expect(
      page.getByText("6 cards in this selection.", { exact: true }),
    ).toBeVisible();
    await page.getByLabel("Card set").selectOption("extension");
    await expect(
      page.getByText("4 cards in this selection.", { exact: true }),
    ).toBeVisible();
    const schedulesBefore = (await stored(page)).schedules;
    await page
      .locator(".card-library > details")
      .first()
      .locator(":scope > summary")
      .click();
    const cardReturn = page
      .locator(".card-library > details")
      .first()
      .getByRole("link", { name: "Return to the exact explanation →" });
    await expect(cardReturn).toHaveAttribute(
      "href",
      `#/module/${module.moduleId}/${beat.id}?view=handbook&detour=1&extension=${module.extensionCards[0].id}`,
    );
    const cardsResume = (await stored(page)).beatResume;
    await cardReturn.click();
    await expect(page.locator(".module-handbook")).toBeVisible();
    await expect(
      page.locator(`#extension-${module.extensionCards[0].id}`),
    ).toBeVisible();
    expect((await stored(page)).beatResume).toEqual(cardsResume);
    expect((await stored(page)).schedules).toEqual(schedulesBefore);
  }
  expect(externalRequests).toEqual([]);
  await go("#/handbook/photo");
  await expect(page.locator(".handbook-chapter")).toHaveCount(2);
  await expect(
    page.getByRole("button", { name: "Print course handbook", exact: true }),
  ).toBeEnabled();
  // Save a non-first visual stage, a different handbook anchor, and a beat note.
  const beatId = "photo-m01-motion",
    beatPositionKey = beatId;
  await go(`#/module/photo-m01/${beatId}`);
  await page
    .getByRole("button", {
      name: "Open handbook beside this beat",
      exact: true,
    })
    .click();
  await page.getByLabel("Handbook section").selectOption("photo-m01-light");
  await page.locator(".beat-notes > summary").click();
  await page
    .locator(".beat-notes")
    .getByLabel("Your lesson note")
    .fill("Synthetic teaching-beat identity note");
  await expect
    .poll(async () => (await stored(page)).notes[`note-${beatId}`]?.text)
    .toBe("Synthetic teaching-beat identity note");
  await page.evaluate(() => window.scrollTo(0, 180));
  await expect
    .poll(async () => (await stored(page)).beatPositions[beatId]?.offset)
    .toBeGreaterThan(0);
  await go("#/");
  await expect(
    page.getByRole("link", { name: "Resume learning →", exact: true }),
  ).toHaveAttribute("href", `#/module/photo-m01/${beatId}`);
  const stateBefore = await stored(page);
  await page.screenshot({
    path: join(root, "docs/evidence/extension-review.png"),
  });
  const coursePath = join(temp, "content/courses/photo/course.json"),
    raw = JSON.parse(await readFile(coursePath, "utf8")) as RawCourse;
  raw.modules.reverse();
  for (const [mi, m] of raw.modules.entries()) {
    m.title = "Renamed module " + (mi + 1);
    m.lessonFiles.reverse();
    for (let i = 0; i < m.lessonFiles.length; i++) {
      const old = m.lessonFiles[i],
        l = JSON.parse(
          await readFile(join(temp, "content/courses/photo", old), "utf8"),
        ) as RawLesson;
      l.title = "Renamed: " + l.title;
      l.questions.forEach((q) => q.options.reverse());
      const body = `lessons/reordered-${mi}-${i}.md`;
      await rename(
        join(temp, "content/courses/photo", l.bodyFile),
        join(temp, "content/courses/photo", body),
      );
      l.bodyFile = body;
      const next = `lessons/reordered-${mi}-${i}.json`;
      await writeFile(
        join(temp, "content/courses/photo", next),
        JSON.stringify(l, null, 2) + "\n",
      );
      await rm(join(temp, "content/courses/photo", old));
      m.lessonFiles[i] = next;
    }
  }
  await writeFile(coursePath, JSON.stringify(raw, null, 2) + "\n");
  for (const [index, module] of photoTeaching.entries()) {
    module.title = "Renamed teaching: " + module.title;
    module.beats.reverse();
    module.beats.forEach((b) => (b.title = "Renamed beat: " + b.title));
    module.visuals.forEach((v) => v.states.reverse());
    module.questions.forEach((q) => q.options.reverse());
    await writeFile(
      join(temp, "content/teaching/photo", `renamed-teaching-${index}.json`),
      JSON.stringify(module, null, 2) + "\n",
    );
    await rm(join(temp, "content/teaching/photo", teachingFiles[index]));
  }
  const reordered = await manifest(join(temp, "content"));
  const renamedDiff = diff(
    Object.fromEntries(
      Object.entries(added)
        .filter(([k]) => k.startsWith("content/"))
        .map(([k, v]) => [k.slice(8), v]),
    ),
    reordered,
  ).map((f) => ({ ...f, path: "content/" + f.path }));
  catalog = await build();
  await page.reload();
  await page
    .getByRole("link", { name: "Resume learning →", exact: true })
    .click();
  await expect(page).toHaveURL(new RegExp(`#/module/photo-m01/${beatId}$`));
  await expect(page.locator(".teaching-beat > h2")).toHaveText(
    "Renamed beat: Separate subject motion from camera motion",
  );
  await expect(
    page
      .locator(".teaching-beat .visual-stages")
      .getByRole("button", { name: "Short interval", exact: false }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("Handbook section")).toHaveValue(
    "photo-m01-light",
  );
  await expect(
    page.getByText("That choice is correct.", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Marked complete · undo", exact: true }),
  ).toBeVisible();
  await page.locator(".beat-notes > summary").click();
  await expect(
    page.locator(".beat-notes").getByLabel("Your lesson note"),
  ).toHaveValue("Synthetic teaching-beat identity note");
  const resumed = (await stored(page)).beatPositions[beatPositionKey];
  for (const key of [
    "beatId",
    "visualStateId",
    "view",
    "handbookOpen",
    "handbookAnchor",
  ] as const)
    expect(resumed[key]).toEqual(
      stateBefore.beatPositions[beatPositionKey][key],
    );
  await go(`#/lesson/${lid}/${sid}`);
  await expect(
    page.getByRole("heading", {
      name: "Renamed: Freeze or blur a moving subject",
    }),
  ).toBeVisible();
  await expect(
    page.locator("#" + sid).getByLabel("Your lesson note"),
  ).toHaveValue("Synthetic photography identity note");
  await expect(
    page.getByRole("button", { name: "Mark incomplete", exact: true }),
  ).toBeVisible();
  await expect(
    page
      .locator(".knowledge-check")
      .first()
      .getByText("1 saved attempt · 1 correct"),
  ).toBeVisible();
  let current = await stored(page);
  for (const k of [
    "notes",
    "bookmarks",
    "completions",
    "attempts",
    "reviews",
    "schedules",
  ] as const)
    expect(current[k]).toEqual(stateBefore[k]);
  // Material revision flag is exercised in a rebuilt browser bundle, preserving history.
  const targetFile = raw.modules
    .flatMap((m) => m.lessonFiles)
    .find((f) => f === "lessons/reordered-1-1.json")!;
  const revised = JSON.parse(
    await readFile(join(temp, "content/courses/photo", targetFile), "utf8"),
  ) as RawLesson;
  expect(revised.id).toBe(lid);
  revised.cards[0].revision = "2";
  revised.cards[0].answer +=
    " Also consider subject distance when comparing blur.";
  revised.questions[0].revision = "2";
  await writeFile(
    join(temp, "content/courses/photo", targetFile),
    JSON.stringify(revised, null, 2) + "\n",
  );
  await build();
  await page.reload();
  await go(`#/lesson/${lid}/${lid}-revisit`);
  await expect(
    page.getByText("This question has been revised.", { exact: false }),
  ).toBeVisible();
  await go("#/review");
  await page.getByRole("button", { name: "Review due cards" }).click();
  await expect(
    page.getByText("Answer revised · review this version"),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Reveal answer", exact: true })
    .click();
  await page.getByRole("button", { name: "Hard", exact: true }).click();
  await expect
    .poll(async () => Object.keys((await stored(page)).reviews).length)
    .toBe(2);
  current = await stored(page);
  expect(Object.values(current.reviews).map((r) => r.revision)).toEqual([
    "1",
    "2",
  ]);
  expect(current.schedules["photo-m01-l01-card1"].revision).toBe("2");
  // A changed teaching beat keeps the previous completion as evidence and asks for review.
  const revisedModuleFile = join(
    temp,
    "content/teaching/photo/renamed-teaching-0.json",
  );
  const revisedModule = JSON.parse(
    await readFile(revisedModuleFile, "utf8"),
  ) as TeachingModule;
  const revisedBeat = revisedModule.beats.find((b) => b.id === beatId)!;
  revisedBeat.version = "2.0.0";
  revisedBeat.explanation +=
    " Compare motion at the intended viewing size; magnification changes what blur is visible.";
  revisedBeat.changeNote =
    "Added the viewing-size condition to the motion comparison.";
  await writeFile(
    revisedModuleFile,
    JSON.stringify(revisedModule, null, 2) + "\n",
  );
  const priorBeatCompletion = (await stored(page)).completions[
    `beat-${beatId}`
  ];
  await build();
  await go(`#/module/photo-m01/${beatId}`);
  await page.reload();
  await expect(
    page.getByText("Material revised since your earlier completion.", {
      exact: false,
    }),
  ).toBeVisible();
  expect((await stored(page)).completions[`beat-${beatId}`]).toEqual(
    priorBeatCompletion,
  );
  await expect(
    page.getByRole("button", { name: "Mark this beat complete", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Mark this beat complete", exact: true })
    .click();
  await expect
    .poll(
      async () =>
        (await stored(page)).completions[`beat-${beatId}`]?.contentVersion,
    )
    .toBe("2.0.0");
  await removeTemporaryTree(join(temp, "content/teaching/photo"));
  await removeTemporaryTree(join(temp, "content/courses/photo"));
  await rm(join(temp, "content/paths/photography.json"));
  for (const n of ["photo-m01-diagram.svg", "photo-m02-diagram.svg"])
    await rm(join(temp, "content/assets", n));
  const release = await build();
  expect(release.map((c) => c.id)).toEqual(baselineCourseIds);
  await page.reload();
  await go("#/courses");
  await expect(
    page.getByRole("heading", {
      name: "Exposure and composition in photography",
    }),
  ).toHaveCount(0);
  await go("#/notebook");
  await expect(
    page.getByText("Removed lesson · note preserved", { exact: true }),
  ).toHaveCount(2);
  expect(
    await page
      .getByLabel("Your lesson note")
      .evaluateAll((nodes) =>
        nodes.map((n) => (n as HTMLTextAreaElement).value),
      ),
  ).toEqual(
    expect.arrayContaining([
      "Synthetic photography identity note",
      "Synthetic teaching-beat identity note",
    ]),
  );
  const after = await manifest(temp),
    runtimeChanges = diff(before, after).filter(
      (f) =>
        !f.path.startsWith("src/generated/") &&
        !f.path.startsWith("public/content-assets/") &&
        !f.path.startsWith("public/content-downloads/") &&
        !f.path.startsWith("public/teaching/") &&
        !f.path.startsWith("docs/evidence/"),
    );
  expect(runtimeChanges).toEqual([]);
  await writeFile(
    join(root, "docs/evidence/content-extension.json"),
    JSON.stringify(
      {
        date: new Date().toISOString(),
        browser: browser.version(),
        fixture: "tests/fixtures/photography/content",
        course: {
          id: "photo",
          modules: 2,
          lessons: 4,
          cards: 12,
          checks: 8,
          scenarios: 2,
          diagrams: 2,
          teachingModules: 2,
          beats: 4,
          extensionCards: 8,
          curatedMediaFixtures: 1,
        },
        additionDiff: addition,
        renameReorderDiff: renamedDiff,
        runtimeSourceChanges: runtimeChanges,
        assertions: [
          "Catalog discovery",
          "Content-only unrelated roadmap and playbook discovery; canonical topic targets and explicit path context",
          "Every lesson, asset, check and scenario rendered",
          "Public and local note search",
          "Notes/bookmarks/completion/attempt/review persisted",
          "Module/lesson title, order, option order and filenames changed; IDs/history survived",
          "Cosmetic changes did not reset schedules",
          "Both unrelated modules support Deck, Handbook and Cards; course handbook includes both chapters",
          "Concept definitions, Samajh boundaries, staged comparisons and explained checks rendered",
          "Four optional extension cards per module; browsing and explanation detours do not schedule cards",
          "Media fallback rendered with original link and no external player request",
          "Beat completion, note, revealed check, visual state and handbook anchor survived content rename/reorder",
          "Home resume returned to the exact stable beat; a revised beat retained prior completion and asked for explicit review",
          "Material question/card revision signaled; old immutable evidence retained",
          "Fixture removed; original release catalog restored; orphan lesson and beat notes recoverable",
        ],
        result: "pass",
      },
      null,
      2,
    ) + "\n",
  );
  console.log(
    "PASS: content-only photography extension, stable identity, revision and cleanup. Manifest: docs/evidence/content-extension.json",
  );
} finally {
  await browser?.close();
  server.close();
  await removeTemporaryTree(temp);
}
