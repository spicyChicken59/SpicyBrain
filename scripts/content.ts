import {
  readdir,
  readFile,
  writeFile,
  mkdir,
  cp,
  rm,
  realpath,
} from "node:fs/promises";
import { resolve, join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import {
  validateTeaching,
  type TeachingIndexEntry,
} from "../src/teaching-schema.ts";
import {
  validateCourses,
  safePath,
  type Course,
  type Lesson,
  validatePaths,
  validatePreservation,
} from "../src/content-schema.ts";
import type {
  CatalogCourse,
  CatalogLesson,
  ContentBody,
} from "../src/catalog-types.ts";

export const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
type RawLesson = {
  bodyFile: string;
  sections: { id: string; kind: string; markdown?: string }[];
};
type RawModule = { lessonFiles: string[]; lessons?: RawLesson[] };
type RawModulePackage = {
  module: RawModule;
  scenarios?: unknown[];
  sources?: unknown[];
  claims?: unknown[];
  concepts?: unknown[];
};
type RawCourse = {
  id: string;
  modules: (RawModule | { file: string })[];
  scenarios?: unknown[];
  sources?: unknown[];
  claims?: unknown[];
  concepts?: unknown[];
  labs?: { bodyFile?: string; body?: string }[];
  guides?: { bodyFile?: string; body?: unknown }[];
  cases?: { bodyFile?: string; body?: string }[];
};
export type LoadOptions = {
  /** Module package files to load as if course.json listed them (course id → paths). */
  extraModuleFiles?: Record<string, string[]>;
};
const guideMarkers = ["action", "example", "template", "limits"] as const;
export function splitGuideBody(body: string) {
  const blocks = body.split(/^<!-- section:([a-z][a-z0-9-]*) -->\s*$/m);
  if (blocks[0].trim()) throw Error("Guide text before its first section");
  const map: Record<string, string> = {};
  for (let i = 1; i < blocks.length; i += 2) {
    if (map[blocks[i]] !== undefined) throw Error("Duplicate guide section");
    map[blocks[i]] = blocks[i + 1].trim();
  }
  for (const key of Object.keys(map))
    if (!guideMarkers.includes(key as (typeof guideMarkers)[number]))
      throw Error(`Unknown guide section: ${key}`);
  return map;
}
export async function loadCourses(
  contentRoot = join(root, "content"),
  options: LoadOptions = {},
) {
  const dirs = (
    await readdir(join(contentRoot, "courses"), { withFileTypes: true })
  )
    .filter((d) => d.isDirectory())
    .sort((a, b) => a.name.localeCompare(b.name));
  const raw: unknown[] = [];
  for (const dir of dirs) {
    const courseDir = join(contentRoot, "courses", dir.name);
    const c = JSON.parse(
      await readFile(await confinedFile(courseDir, "course.json"), "utf8"),
    ) as RawCourse;
    // A module package keeps one module's map entry, scenario, sources, claims
    // and course-level concepts together; it is merged before validation so
    // identities and references are checked exactly as inline modules are.
    const modules: RawModule[] = [];
    for (const entry of [
      ...c.modules,
      ...(options.extraModuleFiles?.[c.id] ?? []).map((file) => ({ file })),
    ]) {
      if (!("file" in entry)) {
        modules.push(entry);
        continue;
      }
      if (!safePath(entry.file) || !entry.file.endsWith(".json"))
        throw Error("Unsafe module package path");
      const pkg = JSON.parse(
        await readFile(await confinedFile(courseDir, entry.file), "utf8"),
      ) as RawModulePackage;
      if (!pkg.module || typeof pkg.module !== "object")
        throw Error(`Module package without a module: ${entry.file}`);
      for (const key of Object.keys(pkg))
        if (
          !["module", "scenarios", "sources", "claims", "concepts"].includes(
            key,
          )
        )
          throw Error(`Unknown module package field: ${key}`);
      modules.push(pkg.module);
      c.scenarios = [...(c.scenarios ?? []), ...(pkg.scenarios ?? [])];
      c.sources = [...(c.sources ?? []), ...(pkg.sources ?? [])];
      c.claims = [...(c.claims ?? []), ...(pkg.claims ?? [])];
      c.concepts = [...(c.concepts ?? []), ...(pkg.concepts ?? [])];
    }
    c.modules = modules;
    for (const item of c.labs ?? []) {
      if (
        !item.bodyFile ||
        !safePath(item.bodyFile) ||
        !item.bodyFile.endsWith(".md")
      )
        throw Error("Unsafe lab body path");
      item.body = (
        await readFile(await confinedFile(courseDir, item.bodyFile), "utf8")
      ).trim();
      delete item.bodyFile;
    }
    for (const item of c.guides ?? []) {
      if (
        !item.bodyFile ||
        !safePath(item.bodyFile) ||
        !item.bodyFile.endsWith(".md")
      )
        throw Error("Unsafe guide body path");
      item.body = splitGuideBody(
        await readFile(await confinedFile(courseDir, item.bodyFile), "utf8"),
      );
      delete item.bodyFile;
    }
    for (const item of c.cases ?? []) {
      if (
        !item.bodyFile ||
        !safePath(item.bodyFile) ||
        !item.bodyFile.endsWith(".md")
      )
        throw Error("Unsafe case body path");
      item.body = (
        await readFile(await confinedFile(courseDir, item.bodyFile), "utf8")
      ).trim();
      delete item.bodyFile;
    }
    for (const m of modules) {
      const lessons = [];
      for (const f of m.lessonFiles) {
        if (!safePath(f) || !f.endsWith(".json"))
          throw Error("Unsafe lesson path");
        const l = JSON.parse(
          await readFile(await confinedFile(courseDir, f), "utf8"),
        ) as RawLesson;
        if (!safePath(l.bodyFile) || !l.bodyFile.endsWith(".md"))
          throw Error("Unsafe body path");
        const body = await readFile(
          await confinedFile(courseDir, l.bodyFile),
          "utf8",
        );
        const blocks = body.split(/^<!-- section:([a-z][a-z0-9-]*) -->\s*$/m);
        if (blocks[0].trim())
          throw Error(`Unassigned Markdown before first section: ${f}`);
        const map = new Map<string, string>();
        for (let i = 1; i < blocks.length; i += 2) {
          if (map.has(blocks[i])) throw Error("Duplicate Markdown section");
          map.set(blocks[i], blocks[i + 1].trim());
        }
        const used = new Set<string>();
        for (const s of l.sections) {
          const marker = map.has(s.id) ? s.id : s.kind;
          if (used.has(marker))
            throw Error(
              `Ambiguous Markdown section: ${marker}; use stable section IDs`,
            );
          used.add(marker);
          s.markdown = map.get(marker) || "";
        }
        if ([...map.keys()].some((key) => !used.has(key)))
          throw Error(`Unassigned Markdown section: ${f}`);
        delete (l as Partial<RawLesson>).bodyFile;
        lessons.push(l);
      }
      delete (m as Partial<RawModule>).lessonFiles;
      m.lessons = lessons;
    }
    raw.push(c);
  }
  const courses = validateCourses(raw);
  for (const c of courses)
    for (const a of c.assets) {
      const svg = await readFile(
        await confinedFile(join(contentRoot, "assets"), a.path),
        "utf8",
      );
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
  let manifests: string[] = [];
  try {
    manifests = await readdir(join(contentRoot, "preservation"));
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
  }
  for (const name of manifests.filter((name) => name.endsWith(".json")))
    validatePreservation(
      JSON.parse(
        await readFile(
          await confinedFile(join(contentRoot, "preservation"), name),
          "utf8",
        ),
      ),
      courses,
    );
  return courses;
}
async function confinedFile(base: string, path: string) {
  if (!safePath(path)) throw Error(`Unsafe content path: ${path}`);
  const directory = await realpath(base),
    file = await realpath(join(base, path));
  if (!file.startsWith(directory + "/") && !file.startsWith(directory + "\\"))
    throw Error(`Content file escapes directory: ${path}`);
  return file;
}
export async function loadPaths(
  courses: Course[],
  contentRoot = join(root, "content"),
) {
  let names: string[];
  try {
    names = await readdir(join(contentRoot, "paths"));
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return [];
    throw error;
  }
  const raw = [];
  for (const name of names.filter((name) => name.endsWith(".json")).sort())
    raw.push(
      JSON.parse(
        await readFile(
          await confinedFile(join(contentRoot, "paths"), name),
          "utf8",
        ),
      ),
    );
  return validatePaths(raw, courses);
}
export function validateDownloadArchive(bytes: Buffer) {
  if (bytes.length > 20 * 1024 * 1024)
    throw Error("Download archive exceeds 20 MB");
  let end = -1;
  for (
    let offset = bytes.length - 22;
    offset >= Math.max(0, bytes.length - 65557);
    offset--
  )
    if (bytes.readUInt32LE(offset) === 0x06054b50) {
      end = offset;
      break;
    }
  if (end < 0 || bytes.readUInt16LE(end + 4) || bytes.readUInt16LE(end + 6))
    throw Error("Invalid or multipart download archive");
  const count = bytes.readUInt16LE(end + 10),
    centralSize = bytes.readUInt32LE(end + 12);
  let offset = bytes.readUInt32LE(end + 16),
    unpacked = 0;
  if (
    !count ||
    count > 200 ||
    offset + centralSize !== end ||
    bytes.readUInt16LE(end + 8) !== count
  )
    throw Error("Invalid download archive directory");
  const seen = new Set<string>();
  for (let index = 0; index < count; index++) {
    if (offset + 46 > end || bytes.readUInt32LE(offset) !== 0x02014b50)
      throw Error("Invalid download archive entry");
    const flags = bytes.readUInt16LE(offset + 8),
      compression = bytes.readUInt16LE(offset + 10);
    const size = bytes.readUInt32LE(offset + 24),
      nameSize = bytes.readUInt16LE(offset + 28),
      extraSize = bytes.readUInt16LE(offset + 30),
      commentSize = bytes.readUInt16LE(offset + 32);
    const attributes = bytes.readUInt32LE(offset + 38),
      localOffset = bytes.readUInt32LE(offset + 42);
    if (offset + 46 + nameSize + extraSize + commentSize > end)
      throw Error("Truncated download archive entry");
    const name = bytes
        .subarray(offset + 46, offset + 46 + nameSize)
        .toString("utf8"),
      directory = name.endsWith("/");
    if (
      !safePath(directory ? name.slice(0, -1) : name) ||
      (!directory && !/\.(?:md|txt|json|csv|py|sql|toml)$/.test(name))
    )
      throw Error(`Unsafe download member: ${name}`);
    if (seen.has(name.toLowerCase()))
      throw Error(`Duplicate download member: ${name}`);
    seen.add(name.toLowerCase());
    unpacked += size;
    if (
      unpacked > 50 * 1024 * 1024 ||
      flags & 1 ||
      ![0, 8].includes(compression) ||
      ((attributes >>> 16) & 0xf000) === 0xa000
    )
      throw Error(`Unsupported download member: ${name}`);
    if (
      localOffset + 30 > bytes.length ||
      bytes.readUInt32LE(localOffset) !== 0x04034b50
    )
      throw Error("Invalid download member location");
    const localNameSize = bytes.readUInt16LE(localOffset + 26);
    if (
      bytes
        .subarray(localOffset + 30, localOffset + 30 + localNameSize)
        .toString("utf8") !== name
    )
      throw Error("Mismatched download member name");
    offset += 46 + nameSize + extraSize + commentSize;
  }
  if (offset !== end) throw Error("Unexpected download archive directory data");
}
export async function loadDownloads(
  courses: Course[],
  contentRoot = join(root, "content"),
) {
  const downloads = [];
  const used = new Set<string>();
  for (const course of courses)
    for (const download of course.downloads ?? []) {
      if (used.has(download.path.toLowerCase()))
        throw Error(`Duplicate download path: ${download.path}`);
      used.add(download.path.toLowerCase());
      const source = await confinedFile(
          join(contentRoot, "downloads"),
          download.path,
        ),
        bytes = await readFile(source);
      if (createHash("sha256").update(bytes).digest("hex") !== download.sha256)
        throw Error(`Download checksum mismatch: ${download.id}`);
      validateDownloadArchive(bytes);
      downloads.push({ ...download, source });
    }
  return downloads;
}
export function counts(courses: Course[]) {
  return courses.map((c) => ({
    course: c.id,
    totals: {
      modules: c.modules.length,
      lessons: c.modules.flatMap((module) => module.lessons).length,
      cards: c.modules.flatMap((module) =>
        module.lessons.flatMap((lesson) => lesson.cards),
      ).length,
      checks: c.modules.flatMap((module) =>
        module.lessons.flatMap((lesson) => lesson.questions),
      ).length,
      scenarios: c.scenarios.filter((scenario) => !scenario.isCapstone).length,
      diagrams: c.assets.length,
    },
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
    tracks: c.tracks?.length ?? 0,
    labs: c.labs?.length ?? 0,
    guides: c.guides?.length ?? 0,
    cases: c.cases?.length ?? 0,
  }));
}
/** The catalog tier: every identity, mapping and number, no prose or assessment text. */
export function stripLesson(lesson: Lesson): CatalogLesson {
  return {
    ...lesson,
    sections: lesson.sections.map(
      ({ markdown: _markdown, ...section }) => section,
    ),
    cards: lesson.cards.map(({ id, revision, lessonId, sectionId }) => ({
      id,
      revision,
      lessonId,
      sectionId,
    })),
    questions: lesson.questions.map(({ id, revision, conceptIds }) => ({
      id,
      revision,
      conceptIds,
    })),
  };
}
export function stripCourse(course: Course): CatalogCourse {
  const withoutBody = <T extends { body: unknown }>({
    body: _body,
    ...rest
  }: T) => rest;
  return {
    ...course,
    modules: course.modules.map((module) => ({
      ...module,
      lessons: module.lessons.map(stripLesson),
    })),
    scenarios: course.scenarios.map(
      ({
        context: _context,
        task: _task,
        model: _model,
        reasoning: _reasoning,
        disclosures: _disclosures,
        ...scenario
      }) => scenario,
    ),
    ...(course.labs ? { labs: course.labs.map(withoutBody) } : {}),
    ...(course.guides ? { guides: course.guides.map(withoutBody) } : {}),
    ...(course.cases ? { cases: course.cases.map(withoutBody) } : {}),
  };
}
/** The body tier: one same-origin JSON file per lesson, scenario, lab, guide and case. */
export function contentBodies(course: Course): ContentBody[] {
  return [
    ...course.modules.flatMap((module) =>
      module.lessons.map((lesson): ContentBody => ({
        kind: "lesson",
        id: lesson.id,
        contentVersion: lesson.contentVersion,
        sections: Object.fromEntries(
          lesson.sections.map((section) => [section.id, section.markdown]),
        ),
        questions: lesson.questions,
        cards: lesson.cards,
      })),
    ),
    ...course.scenarios.map(
      ({ id, context, task, model, reasoning, disclosures }): ContentBody => ({
        kind: "scenario",
        id,
        context,
        task,
        model,
        reasoning,
        disclosures,
      }),
    ),
    ...(course.labs ?? []).map(({ id, body }): ContentBody => ({
      kind: "lab",
      id,
      body,
    })),
    ...(course.guides ?? []).map(({ id, body }): ContentBody => ({
      kind: "guide",
      id,
      body,
    })),
    ...(course.cases ?? []).map(({ id, body }): ContentBody => ({
      kind: "case",
      id,
      body,
    })),
  ];
}
export async function buildContent(
  contentRoot = join(root, "content"),
  destination = root,
) {
  const courses = await loadCourses(contentRoot);
  const paths = await loadPaths(courses, contentRoot);
  const downloads = await loadDownloads(courses, contentRoot);
  const teaching = await loadTeaching(courses, contentRoot);
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
    JSON.stringify(courses.map(stripCourse)),
  );
  await writeFile(
    join(destination, "src/generated/paths.json"),
    JSON.stringify(paths),
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
  const teachingIndex: TeachingIndexEntry[] = [];
  const teachingDirectory = join(destination, "public/teaching");
  await rm(teachingDirectory, { recursive: true, force: true });
  await mkdir(join(teachingDirectory, "bodies"), { recursive: true });
  for (const body of courses.flatMap(contentBodies))
    await writeFile(
      join(teachingDirectory, "bodies", `${body.id}.json`),
      JSON.stringify(body),
    );
  for (const module of teaching.modules) {
    const {
      courseId,
      moduleId,
      title,
      summary,
      lessonIds,
      optionalBridgeLessonIds,
      cardLinks,
      extensionCards,
    } = module;
    const filename = `${courseId}-${moduleId}.json`;
    const bytes = JSON.stringify(module);
    if (Buffer.byteLength(bytes) > 750000)
      throw Error(`Teaching module exceeds bounded payload: ${moduleId}`);
    await writeFile(join(teachingDirectory, filename), bytes);
    teachingIndex.push({
      courseId,
      moduleId,
      title,
      summary,
      lessonIds,
      optionalBridgeLessonIds,
      cardLinks,
      extensionCards: extensionCards.map(
        ({ id, revision, lessonId, sectionId, beatId }) => ({
          id,
          revision,
          lessonId,
          sectionId,
          beatId,
        }),
      ),
      visualIds: module.visuals.map((v) => v.id),
      conceptIds: module.concepts.map((c) => c.id),
      referenceIds: [...module.questions, ...module.selfQuestions].map(
        (x) => x.id,
      ),
      url: `teaching/${filename}`,
      beats: module.beats.map(
        ({ id, title, version, lessonId, sectionId, recap, questionIds }) => ({
          id,
          title,
          version,
          lessonId,
          sectionId,
          recap,
          questionIds,
        }),
      ),
    });
    for (const beat of module.beats)
      index.push({
        id: beat.id,
        type: "Teaching beat",
        courseId,
        title: `${module.title} · ${beat.title}`,
        text: [
          beat.title,
          beat.explanation,
          beat.handbook.markdown,
          beat.samajh?.text ?? "",
          ...beat.conceptIds,
        ].join(" "),
        href: `#/module/${moduleId}/${beat.id}`,
      });
    for (const card of module.extensionCards)
      index.push({
        id: card.id,
        type: "Extension card",
        courseId,
        title: card.prompt,
        text: [
          card.prompt,
          card.answer,
          card.explanation,
          card.whyItMatters,
          ...card.conceptIds,
        ].join(" "),
        href: `#/module/${moduleId}/${card.beatId}?view=handbook&detour=1&extension=${card.id}`,
      });
    for (const concept of module.concepts) {
      const beat = module.beats.find((b) => b.conceptIds.includes(concept.id)),
        card = module.extensionCards.find((c) =>
          c.conceptIds.includes(concept.id),
        );
      index.push({
        id: concept.id,
        type: "Glossary",
        courseId,
        title: concept.term,
        text: [
          concept.term,
          ...concept.aliases,
          concept.definition,
          concept.example,
        ].join(" "),
        href: beat
          ? `#/module/${moduleId}/${beat.id}`
          : card
            ? `#/module/${moduleId}/${card.beatId}?view=handbook&detour=1&extension=${card.id}`
            : `#/module/${moduleId}/${module.beats[0].id}`,
      });
    }
  }
  await writeFile(
    join(destination, "src/generated/teaching-index.json"),
    JSON.stringify(teachingIndex),
  );
  await writeFile(
    join(teachingDirectory, "media.json"),
    JSON.stringify(teaching.media),
  );
  for (const path of paths) {
    const firstId = path.groups[0].lessonIds[0];
    const courseId = courses.find((course) =>
      course.modules.some((module) =>
        module.lessons.some((lesson) => lesson.id === firstId),
      ),
    )!.id;
    index.push({
      id: path.id,
      type: "Roadmap",
      courseId,
      title: path.title,
      text: [path.summary, ...path.outcomes, ...path.startingAssumptions].join(
        " ",
      ),
      href: `#/path/${path.id}`,
    });
    for (const playbook of path.playbooks)
      index.push({
        id: playbook.id,
        type: "Playbook",
        courseId: playbook.targets[0].courseId,
        title: playbook.title,
        text: [
          playbook.summary,
          ...playbook.targets.map((target) => target.label),
        ].join(" "),
        href: `#/learn/playbooks?playbook=${playbook.id}`,
      });
  }
  await writeFile(
    join(destination, "src/generated/search.json"),
    JSON.stringify(index),
  );
  await writeFile(
    join(teachingDirectory, "search.json"),
    JSON.stringify(index),
  );
  await rm(join(destination, "public/content-assets"), {
    recursive: true,
    force: true,
  });
  for (const asset of courses.flatMap((course) => course.assets)) {
    const target = join(destination, "public/content-assets", asset.path);
    await mkdir(dirname(target), { recursive: true });
    await cp(
      await confinedFile(join(contentRoot, "assets"), asset.path),
      target,
    );
  }
  await rm(join(destination, "public/content-downloads"), {
    recursive: true,
    force: true,
  });
  for (const download of downloads) {
    const target = join(destination, "public/content-downloads", download.path);
    await mkdir(dirname(target), { recursive: true });
    await cp(download.source, target);
  }
  await mkdir(join(destination, "docs/evidence"), { recursive: true });
  await writeFile(
    join(destination, "docs/evidence/content-counts.json"),
    JSON.stringify(counts(courses), null, 2) + "\n",
  );
  return courses;
}
export async function loadTeaching(
  courses: Course[],
  contentRoot = join(root, "content"),
) {
  const raw: unknown[] = [],
    media: unknown[] = [];
  let dirs: import("node:fs").Dirent[] = [];
  try {
    dirs = await readdir(join(contentRoot, "teaching"), {
      withFileTypes: true,
    });
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
  }
  for (const dir of dirs.filter((d) => d.isDirectory()))
    for (const name of (await readdir(join(contentRoot, "teaching", dir.name)))
      .filter((n) => n.endsWith(".json"))
      .sort()) {
      const data = JSON.parse(
        await readFile(
          await confinedFile(join(contentRoot, "teaching", dir.name), name),
          "utf8",
        ),
      );
      if (name === "media.json" || /^media-[a-z0-9-]+\.json$/.test(name))
        media.push(...data);
      else raw.push(data);
    }
  return validateTeaching(raw, courses, media);
}
export async function verifyDesign() {
  const directory = join(root, "public/design-system");
  const p = JSON.parse(
    await readFile(join(directory, "provenance.json"), "utf8"),
  ) as { files: Record<string, string> };
  for (const [f, hash] of Object.entries(p.files)) {
    const bytes = await readFile(join(directory, f));
    const rawHash = createHash("sha256").update(bytes).digest("hex");
    // Git's Windows text checkout may use CRLF. Compare normalized text to
    // the same pinned digest; binary files and all other edits remain exact.
    const normalizedHash =
      /(?:\.(?:css|js|svg|json|md|txt)$|(?:^|\/)LICENSE$)/.test(f)
        ? createHash("sha256")
            .update(bytes.toString("utf8").replace(/\r\n/g, "\n"))
            .digest("hex")
        : rawHash;
    if (rawHash !== hash && normalizedHash !== hash)
      throw Error(`Design snapshot changed: ${f}`);
  }
}
if (
  process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  await verifyDesign();
  const c = process.argv.includes("--build")
    ? await buildContent()
    : await loadCourses();
  await loadPaths(c);
  await loadTeaching(c);
  await loadDownloads(c);
  console.log(JSON.stringify(counts(c), null, 2));
}
