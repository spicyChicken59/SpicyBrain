import { readdir, readFile, writeFile, mkdir, cp, rm } from "node:fs/promises";
import { resolve, join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import {
  validateCourses,
  safePath,
  type Course,
} from "../src/content-schema.ts";

export const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
type RawLesson = {
  bodyFile: string;
  sections: { kind: string; markdown?: string }[];
};
type RawCourse = {
  modules: { lessonFiles: string[]; lessons?: RawLesson[] }[];
};
export async function loadCourses(contentRoot = join(root, "content")) {
  const dirs = (
    await readdir(join(contentRoot, "courses"), { withFileTypes: true })
  )
    .filter((d) => d.isDirectory())
    .sort((a, b) => a.name.localeCompare(b.name));
  const raw: unknown[] = [];
  for (const dir of dirs) {
    const courseDir = join(contentRoot, "courses", dir.name);
    const c = JSON.parse(
      await readFile(join(courseDir, "course.json"), "utf8"),
    ) as RawCourse;
    for (const m of c.modules) {
      const lessons = [];
      for (const f of m.lessonFiles) {
        if (!safePath(f)) throw Error("Unsafe lesson path");
        const l = JSON.parse(
          await readFile(join(courseDir, f), "utf8"),
        ) as RawLesson;
        if (!safePath(l.bodyFile)) throw Error("Unsafe body path");
        const body = await readFile(join(courseDir, l.bodyFile), "utf8");
        const blocks = body.split(/^<!-- section:([a-z]+) -->\s*$/m);
        const map = new Map<string, string>();
        for (let i = 1; i < blocks.length; i += 2) {
          if (map.has(blocks[i])) throw Error("Duplicate Markdown section");
          map.set(blocks[i], blocks[i + 1].trim());
        }
        for (const s of l.sections) s.markdown = map.get(s.kind) || "";
        delete (l as Partial<RawLesson>).bodyFile;
        lessons.push(l);
      }
      delete (m as Partial<typeof m>).lessonFiles;
      m.lessons = lessons;
    }
    raw.push(c);
  }
  const courses = validateCourses(raw);
  for (const c of courses)
    for (const a of c.assets) {
      const svg = await readFile(join(contentRoot, "assets", a.path), "utf8");
      if (
        !svg.includes("<svg") ||
        !svg.includes("<title") ||
        !svg.includes("<desc") ||
        /<script|<foreignObject|on\w+=|(?:href|src)=["'](?:https?:|data:)/i.test(
          svg,
        )
      )
        throw Error(`Unsafe or inaccessible SVG: ${a.id}`);
    }
  return courses;
}
export function counts(courses: Course[]) {
  return courses.map((c) => ({
    course: c.id,
    modules: c.modules.map((m) => ({
      id: m.id,
      lessons: m.lessons.length,
      cards: m.lessons.reduce((n, l) => n + l.cards.length, 0),
      checks: m.lessons.reduce((n, l) => n + l.questions.length, 0),
      diagrams: new Set(
        m.lessons.flatMap((l) => l.sections.flatMap((s) => s.assetIds)),
      ).size,
      scenarios: 1,
    })),
    capstones: c.scenarios.filter((s) => s.isCapstone).length,
  }));
}
export async function buildContent(
  contentRoot = join(root, "content"),
  destination = root,
) {
  const courses = await loadCourses(contentRoot);
  await mkdir(join(destination, "src/generated"), { recursive: true });
  const design = await readFile(
    join(root, "public/design-system/sc.css"),
    "utf8",
  );
  await writeFile(
    join(destination, "src/generated/design.css"),
    design.replace(/^@import[^\n]*(?:\n|$)/gm, ""),
  );
  await writeFile(
    join(destination, "src/generated/catalog.json"),
    JSON.stringify(courses),
  );
  const index = courses.flatMap((c) => [
    {
      id: c.id,
      type: "Course",
      courseId: c.id,
      title: c.title,
      text: [c.title, c.subtitle, c.summary, ...c.tags].join(" "),
      href: `#/course/${c.id}`,
    },
    ...c.modules.flatMap((m) =>
      m.lessons.flatMap((l) =>
        l.sections.map((s) => ({
          id: s.id,
          type: "Lesson",
          courseId: c.id,
          title: `${l.title} · ${s.title}`,
          text: [l.title, ...l.tags, s.markdown].join(" "),
          href: `#/lesson/${l.id}/${s.id}`,
        })),
      ),
    ),
    ...c.concepts.map((g) => ({
      id: g.id,
      type: "Glossary",
      courseId: c.id,
      title: g.term,
      text: [g.term, ...g.aliases, g.definition].join(" "),
      href: `#/lesson/${g.lessonId}/${g.sectionId}`,
    })),
  ]);
  await writeFile(
    join(destination, "src/generated/search.json"),
    JSON.stringify(index),
  );
  await rm(join(destination, "public/content-assets"), {
    recursive: true,
    force: true,
  });
  await cp(
    join(contentRoot, "assets"),
    join(destination, "public/content-assets"),
    { recursive: true },
  );
  await mkdir(join(destination, "docs/evidence"), { recursive: true });
  await writeFile(
    join(destination, "docs/evidence/content-counts.json"),
    JSON.stringify(counts(courses), null, 2) + "\n",
  );
  return courses;
}
export async function verifyDesign() {
  const directory = join(root, "public/design-system");
  const p = JSON.parse(
    await readFile(join(directory, "provenance.json"), "utf8"),
  ) as { files: Record<string, string> };
  for (const [f, hash] of Object.entries(p.files))
    if (
      createHash("sha256")
        .update(await readFile(join(directory, f)))
        .digest("hex") !== hash
    )
      throw Error(`Design snapshot changed: ${f}`);
}
if (
  process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  await verifyDesign();
  const c = process.argv.includes("--build")
    ? await buildContent()
    : await loadCourses();
  console.log(JSON.stringify(counts(c), null, 2));
}
