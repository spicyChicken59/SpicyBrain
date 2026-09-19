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
import { join, resolve, extname } from "node:path";
import { tmpdir } from "node:os";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createServer } from "node:http";
import { chromium, expect } from "@playwright/test";
import { buildContent, root } from "./content.ts";
import { stored } from "../tests/browser/helpers.ts";
import type { Course, Lesson } from "../src/content-schema.ts";
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
    if (!file.startsWith(base + "/")) throw Error();
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
  await symlink(join(root, "node_modules"), join(temp, "node_modules"), "dir");
  const before = await manifest(temp);
  await cp(
    join(root, "tests/fixtures/photography/content"),
    join(temp, "content"),
    { recursive: true },
  );
  const added = await manifest(temp);
  const addition = diff(before, added);
  expect(addition.every((f) => f.path.startsWith("content/"))).toBe(true);
  let catalog = await build();
  expect(catalog.map((c) => c.id)).toEqual(["dbxfe", "photo"]);
  expect(catalog[1].modules).toHaveLength(2);
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
  // Every fixture lesson, asset, check and scenario renders through existing components.
  for (const m of catalog[1].modules) {
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
  await rm(join(temp, "content/courses/photo"), { recursive: true });
  for (const n of ["photo-m01-diagram.svg", "photo-m02-diagram.svg"])
    await rm(join(temp, "content/assets", n));
  const release = await build();
  expect(release.map((c) => c.id)).toEqual(["dbxfe"]);
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
  ).toBeVisible();
  await expect(page.getByLabel("Your lesson note")).toHaveValue(
    "Synthetic photography identity note",
  );
  const after = await manifest(temp),
    runtimeChanges = diff(before, after).filter(
      (f) =>
        !f.path.startsWith("src/generated/") &&
        !f.path.startsWith("public/content-assets/") &&
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
        },
        additionDiff: addition,
        renameReorderDiff: renamedDiff,
        runtimeSourceChanges: runtimeChanges,
        assertions: [
          "Catalog discovery",
          "Every lesson, asset, check and scenario rendered",
          "Public and local note search",
          "Notes/bookmarks/completion/attempt/review persisted",
          "Module/lesson title, order, option order and filenames changed; IDs/history survived",
          "Cosmetic changes did not reset schedules",
          "Material question/card revision signaled; old immutable evidence retained",
          "Fixture removed; release catalog only dbxfe; orphan note recoverable",
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
  await rm(temp, { recursive: true, force: true });
}
