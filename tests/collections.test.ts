import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdir, mkdtemp, readFile, rm, writeFile, cp } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import {
  buildContent,
  collectionSearchEntries,
  diskTeachingLinkTargets,
  loadCourses,
  loadDownloads,
  loadTeaching,
  stripCourse,
} from "../scripts/content.ts";
import { validateCourses, type Course } from "../src/content-schema.ts";
import {
  teachingLinkTargets,
  validateTeaching,
  type TeachingIndexEntry,
  type TeachingModule,
} from "../src/teaching-schema.ts";
import {
  beatNeighbourhood,
  collectKnownIds,
  guideNoteId,
  guideNoteLesson,
  hasCollections,
  labClassOrder,
  labClassText,
  nextInTrack,
  relatedCollections,
  reporterText,
  routeResume,
} from "../src/collections-model.ts";
import { emptyState, importPreview } from "../src/study.ts";

// The synthetic course-collections fixture: three modules in two tracks (one
// module from a package file), two routes, two labs, two guides, a case, a
// crosswalk row and two capstones. The unrelated photography fixture has none
// of these fields.
const fixtureRoot = "tests/fixtures/collections/content";
const courses = await loadCourses(fixtureRoot);
const hearth = courses.find((c) => c.id === "hearth")!;
const teaching = await loadTeaching(courses, fixtureRoot);
const photoRoot = "tests/fixtures/photography/content";
const photo = (await loadCourses(photoRoot))[0];
const photoTeaching = await loadTeaching([photo], photoRoot);
const moduleById = (id: string) =>
  structuredClone(teaching.modules.find((m) => m.moduleId === id)!);
/** The runtime index entries the build would write for these modules. */
const indexEntries = (modules: TeachingModule[]) =>
  modules.map((m) => ({
    moduleId: m.moduleId,
    beats: m.beats.map((b) => ({ id: b.id })),
  }));

test("the collections fixture is a complete content-only package", async () => {
  assert.deepEqual(
    hearth.modules.map((m) => m.id),
    ["hearth-m01", "hearth-m02", "hearth-m03"],
  );
  assert.equal(hearth.tracks?.length, 2);
  assert.equal(hearth.routes?.filter((r) => r.essential).length, 1);
  assert.deepEqual(
    hearth.labs?.map((l) => l.executionClass),
    ["local-executed", "tabletop"],
  );
  assert.ok(hearth.labs?.some((l) => l.downloadId));
  for (const guide of hearth.guides ?? [])
    assert.deepEqual(Object.keys(guide.body).sort(), [
      "action",
      "example",
      "limits",
      "template",
    ]);
  assert.equal(hearth.cases?.[0].sourceIds.length, 1);
  assert.equal(hearth.crosswalk?.length, 1);
  const capstones = hearth.scenarios.filter((s) => s.isCapstone);
  assert.equal(capstones.length, 2);
  assert.equal(capstones.filter((s) => s.revisionNotice).length, 1);
  assert.equal(capstones.filter((s) => s.downloadIds?.length).length, 1);
  assert.equal(teaching.modules.length, 3);
  assert.equal((await loadDownloads(courses, fixtureRoot)).length, 2);
  assert.ok(!JSON.stringify(hearth).includes("dbxfe"));
});

const invalid = (mutate: (c: Course) => void, message: RegExp) => {
  const c = structuredClone(hearth);
  mutate(c);
  assert.throws(() => validateCourses([c]), message);
};

test("routes: ids unique and global, modules must exist, at most one essential route", () => {
  assert.equal(validateCourses([structuredClone(hearth)]).length, 1);
  invalid((c) => {
    for (const route of c.routes!) route.essential = true;
  }, /More than one essential route/);
  invalid((c) => {
    c.routes![1].moduleIds.push("missing-module");
  }, /Unresolved route module: missing-module/);
  invalid((c) => {
    c.routes![1].moduleIds.push(c.routes![1].moduleIds[0]);
  }, /Duplicate module within route/);
  invalid((c) => {
    c.routes![1].id = c.routes![0].id;
  }, /Duplicate ID/);
  invalid((c) => {
    c.routes![0].id = c.modules[0].id;
  }, /Duplicate ID/);
  invalid((c) => {
    c.routes![0].moduleIds = [];
  }, /too_small|at least|>=1/i);
  invalid((c) => {
    (c.routes![0] as Record<string, unknown>).lessonIds = [];
  }, /Unrecognized key|unrecognized/i);
  invalid((c) => {
    c.routes![0].id = "Not An Id";
  }, /invalid|pattern|regex/i);
  // Global uniqueness reaches another course's identities too.
  const other = structuredClone(photo);
  other.id = "hearth-route-first-loaf";
  assert.throws(
    () => validateCourses([structuredClone(hearth), other]),
    /Duplicate ID: hearth-route-first-loaf/,
  );
  // No essential route is valid: routes are optional suggestions.
  const none = structuredClone(hearth);
  for (const route of none.routes!) delete route.essential;
  assert.equal(validateCourses([none]).length, 1);
  const without = structuredClone(hearth);
  delete without.routes;
  assert.equal(validateCourses([without]).length, 1);
});

test("scenario revisionNotice and downloadIds are validated and stay in the catalog tier", () => {
  invalid((c) => {
    c.scenarios.find((s) => s.revisionNotice)!.revisionNotice = "   ";
  }, /too_small|at least|>=1/i);
  invalid((c) => {
    (c.scenarios[0] as Record<string, unknown>).revisionNotice = 3;
  }, /string/i);
  invalid((c) => {
    c.scenarios[0].downloadIds = ["missing-download"];
  }, /Unresolved scenario download: missing-download/);
  invalid((c) => {
    c.scenarios[0].downloadIds = ["Not An Id"];
  }, /invalid|pattern|regex/i);
  const catalog = stripCourse(hearth);
  const revised = catalog.scenarios.find((s) => s.revisionNotice)!;
  assert.match(revised.revisionNotice!, /earlier version/);
  assert.deepEqual(revised.downloadIds, ["hearth-capstone-download"]);
  assert.equal("context" in revised, false);
});

test("scenario Markdown links are validated like lesson sections", () => {
  // The fixture capstone already links a lab, a guide, a case, a lesson, a
  // module, a practice item and the course; all resolve.
  const capstone = hearth.scenarios.find((s) => s.id === "hearth-capstone")!;
  for (const target of [
    "#/course/hearth/labs/hearth-lab-hydration",
    "#/course/hearth/guides/hearth-guide-bake-plan",
    "#/course/hearth/cases/hearth-case-village-bakery",
    "#/lesson/hearth-m01-l01",
    "#/module/hearth-m03",
    "#/practice/hearth-m01-scenario",
    "#/course/hearth",
  ])
    assert.ok(
      `${capstone.context} ${capstone.model}`.includes(`](${target})`),
      target,
    );
  const fields: ((s: Course["scenarios"][number], link: string) => void)[] = [
    (s, link) => (s.context += ` ${link}`),
    (s, link) => (s.task += ` ${link}`),
    (s, link) => (s.model += ` ${link}`),
    (s, link) => (s.reasoning += ` ${link}`),
    (s, link) => (s.disclosures[0].response += ` ${link}`),
  ];
  const broken: [string, RegExp][] = [
    ["[x](#/lesson/missing-lesson)", /Broken lesson\/section reference/],
    [
      "[x](#/lesson/hearth-m01-l01/missing-section)",
      /Broken lesson\/section reference/,
    ],
    ["[x](#/module/missing-module)", /Broken module link/],
    ["[x](#/module/hearth-m01/hearth-m01-starter)", /Broken module link/],
    ["[x](#/practice/missing-scenario)", /Broken practice link/],
    ["[x](#/course/missing-course)", /Broken course link/],
    ["[x](#/course/hearth/labs/missing-lab)", /Broken course collection link/],
    [
      "[x](#/course/hearth/crosswalk/hearth-crosswalk-open-course)",
      /Broken course collection link/,
    ],
    ["[x](#/course/hearth/labs)", /Broken internal link/],
    ["[x](http://example.com/plain)", /Unsafe Markdown link/],
    ["[x](#/search)", /Unsafe Markdown link/],
    ["[x](../private.md)", /Unsafe Markdown link/],
  ];
  broken.forEach(([link, message], i) =>
    invalid(
      (c) => fields[i % fields.length](c.scenarios[i % 4], link),
      message,
    ),
  );
  // Every field is checked, not only the context.
  for (const addLink of fields)
    invalid(
      (c) => addLink(c.scenarios[0], "[x](#/module/missing-module)"),
      /Broken module link/,
    );
  const valid = structuredClone(hearth);
  valid.scenarios[0].reasoning +=
    " See [the guide](#/course/hearth/guides/hearth-guide-dense-loaf) and [a source](https://example.com/notes).";
  assert.equal(validateCourses([valid]).length, 1);
});

test("every Markdown link form is checked, not only inline links", () => {
  // Reference definitions, <autolinks> and GFM literals all render as links
  // (react-markdown with remark-gfm), so each is held to the same rule.
  const forms: [string, RegExp][] = [
    [
      "See [the module][m].\n\n[m]: #/module/missing-module",
      /Broken module link: #\/module\/missing-module in scenario hearth-m01-scenario, reasoning$/,
    ],
    [
      "See [the notes][n].\n\n[n]: http://example.com/plain",
      /Unsafe Markdown link: http:\/\/example\.com\/plain in scenario hearth-m01-scenario, reasoning$/,
    ],
    [
      "Read <http://example.com/plain>.",
      /Unsafe Markdown link: http:\/\/example\.com\/plain in .+ A bare URL or address becomes a link/,
    ],
    [
      "Read http://example.com/plain today.",
      /Unsafe Markdown link: http:\/\/example\.com\/plain in /,
    ],
    [
      "Read www.example.com/plain today.",
      /Unsafe Markdown link: http:\/\/www\.example\.com\/plain in /,
    ],
    [
      "Write to baker@example.com today.",
      /Unsafe Markdown link: mailto:baker@example\.com in /,
    ],
    // A path segment that names an inherited object key is a broken link,
    // not a crash in the check.
    [
      "[x](#/course/hearth/constructor/hearth-lab-hydration)",
      /Broken course collection link: #\/course\/hearth\/constructor\//,
    ],
  ];
  for (const [markdown, message] of forms)
    invalid((c) => {
      c.scenarios[0].reasoning += `\n\n${markdown}\n`;
    }, message);
  // The same forms resolve when their targets do, and link syntax inside
  // code is text, not a link.
  const valid = structuredClone(hearth);
  valid.scenarios[0].reasoning +=
    "\n\nSee [the guide][g], <https://example.com/notes> and https://example.com/more. The text `[x](http://example.com)` is code.\n\n[g]: #/course/hearth/guides/hearth-guide-dense-loaf\n";
  assert.equal(validateCourses([valid]).length, 1);
});

test("Markdown the renderer would drop fails the build and names the item", () => {
  // MD shows only h3/h4 headings and no images or footnotes; anything else
  // would vanish from the page together with its text.
  const dropped: [(c: Course) => void, RegExp][] = [
    [
      (c) => (c.labs![0].body = `# ${c.labs![0].title}\n\n${c.labs![0].body}`),
      /Unsupported Markdown heading \(h1\) in lab hearth-lab-hydration, line 1: only ### and #### headings are shown/,
    ],
    [
      (c) => (c.labs![1].body += "\n\n## Purpose\n\nWhy the plan matters."),
      /Unsupported Markdown heading \(h2\) in lab hearth-lab-schedule, line \d+/,
    ],
    [
      (c) =>
        (c.guides![0].body.template = `## Your draft\n\n${c.guides![0].body.template}`),
      /Unsupported Markdown heading \(h2\) in guide hearth-guide-dense-loaf, template, line 1/,
    ],
    [
      // A setext underline makes the line above it a heading.
      (c) =>
        (c.cases![0].body = `What was reported\n=================\n\n${c.cases![0].body}`),
      /Unsupported Markdown heading \(h1\) in case hearth-case-village-bakery, line 1/,
    ],
    [
      (c) => (c.cases![0].body += "\n\nA closing thought\n---\n"),
      /Unsupported Markdown heading \(h2\) in case hearth-case-village-bakery/,
    ],
    [
      (c) => (c.labs![0].body += "\n\n> ## Quoted heading\n"),
      /Unsupported Markdown heading \(h2\) in lab hearth-lab-hydration/,
    ],
    [
      (c) => (c.labs![0].body += "\n\n##### Too deep\n"),
      /Unsupported Markdown heading \(h5\) in lab hearth-lab-hydration/,
    ],
    [
      (c) =>
        (c.modules[0].lessons[0].sections[0].markdown += "\n\n## An aside\n"),
      /Unsupported Markdown heading \(h2\) in lesson hearth-m01-l01, section /,
    ],
    [
      (c) =>
        (c.scenarios[0].context = `# The situation\n\n${c.scenarios[0].context}`),
      /Unsupported Markdown heading \(h1\) in scenario hearth-m01-scenario, context, line 1/,
    ],
    [
      (c) => (c.labs![0].body += "\n\n![A loaf](https://example.com/loaf.png)"),
      /Unsupported Markdown image in lab hearth-lab-hydration/,
    ],
    [
      (c) => (c.cases![0].body += "\n\nA claim.[^1]\n\n[^1]: Its note."),
      /Unsupported Markdown footnote in case hearth-case-village-bakery/,
    ],
  ];
  for (const [mutate, message] of dropped) invalid(mutate, message);
  // Headings of the supported depths, and lines inside code that only look
  // like headings, are kept.
  const valid = structuredClone(hearth);
  valid.labs![0].body +=
    "\n\n```sh\n# a shell comment, not a heading\n## nor this\n```\n\n    # indented code\n\n### A third-level heading\n\n#### A fourth-level heading\n\nText.\n\n---\n\nMore text.\n";
  assert.equal(validateCourses([valid]).length, 1);
});

test("teaching identities may not reuse a track, route, lab, guide, case or crosswalk identity", () => {
  const targets = teachingLinkTargets(indexEntries(teaching.modules));
  // Control: the fixture validates as written, at build and at runtime.
  assert.equal(
    validateTeaching(structuredClone(teaching.modules), [hearth]).modules
      .length,
    3,
  );
  const beat = "hearth-m01-proof";
  for (const kind of [
    "tracks",
    "routes",
    "labs",
    "guides",
    "cases",
    "crosswalk",
  ] as const) {
    const c = structuredClone(hearth);
    (c[kind] as { id: string }[])[0].id = beat;
    const duplicate = new RegExp(`Duplicate teaching identity ${beat}$`);
    assert.throws(
      () => validateTeaching(structuredClone(teaching.modules), [c]),
      duplicate,
      kind,
    );
    // The runtime validates one module against the catalog tier.
    assert.throws(
      () =>
        validateTeaching(
          [moduleById("hearth-m01")],
          [stripCourse(c)],
          [],
          false,
          targets,
        ),
      duplicate,
      `${kind} at runtime`,
    );
  }
  // A beat renamed to a guide's or a route's identity, with every reference
  // to it renamed too, is refused: its note would be the guide draft's note.
  for (const taken of ["hearth-guide-bake-plan", "hearth-route-first-loaf"]) {
    const renamed = JSON.parse(
      JSON.stringify(teaching.modules).replaceAll(`"${beat}"`, `"${taken}"`),
    ) as TeachingModule[];
    assert.ok(renamed[0].beats.some((b) => b.id === taken));
    assert.throws(
      () => validateTeaching(renamed, [hearth]),
      new RegExp(`Duplicate teaching identity ${taken}$`),
    );
  }
});

test("labs, field guides and case analyses become search entries linking to their routes", async () => {
  const entries = collectionSearchEntries(hearth);
  assert.deepEqual(
    entries.map((e) => [e.type, e.id, e.href]),
    [
      [
        "Lab",
        "hearth-lab-hydration",
        "#/course/hearth/labs/hearth-lab-hydration",
      ],
      [
        "Lab",
        "hearth-lab-schedule",
        "#/course/hearth/labs/hearth-lab-schedule",
      ],
      [
        "Field guide",
        "hearth-guide-dense-loaf",
        "#/course/hearth/guides/hearth-guide-dense-loaf",
      ],
      [
        "Field guide",
        "hearth-guide-bake-plan",
        "#/course/hearth/guides/hearth-guide-bake-plan",
      ],
      [
        "Case analysis",
        "hearth-case-village-bakery",
        "#/course/hearth/cases/hearth-case-village-bakery",
      ],
    ],
  );
  // Body text is searchable, not only titles: a template line and a lab step.
  assert.match(entries[2].text, /The one change I will test/);
  assert.match(entries[0].text, /python hydration\.py recipe\.json/);
  assert.match(entries[4].text, /customer-authored/);
  assert.deepEqual(collectionSearchEntries(photo), []);
  const out = await mkdtemp(join(tmpdir(), "spicybrain-collections-search-"));
  try {
    await buildContent(fixtureRoot, out);
    const search = JSON.parse(
      await readFile(join(out, "public/teaching/search.json"), "utf8"),
    ) as { type: string; href: string }[];
    for (const entry of entries)
      assert.ok(
        search.some((s) => s.type === entry.type && s.href === entry.href),
        entry.href,
      );
    for (const s of search) assert.match(s.href, /^#\//);
  } finally {
    await rm(out, { recursive: true, force: true });
  }
});

test("knownIds include collection identities, so a guide draft note imports as known content", () => {
  const catalog = [stripCourse(hearth)];
  const index = teaching.modules.map((m) => ({
    beats: m.beats.map((b) => ({ ...b })),
    extensionCards: [],
    referenceIds: [],
  })) as unknown as TeachingIndexEntry[];
  const known = collectKnownIds(catalog, index, [{ id: "hearth-path" }]);
  for (const id of [
    "hearth",
    "hearth-m01",
    "hearth-m01-l01",
    "hearth-m01-l01-understand",
    "hearth-m01-l01-card1",
    "hearth-m01-l01-q1",
    "hearth-capstone",
    "hearth-m01-starter",
    "hearth-path",
    ...hearth.tracks!.map((t) => t.id),
    ...hearth.routes!.map((r) => r.id),
    ...hearth.labs!.map((l) => l.id),
    ...hearth.guides!.map((g) => g.id),
    ...hearth.cases!.map((x) => x.id),
    ...hearth.crosswalk!.map((x) => x.id),
  ])
    assert.ok(known.has(id), id);
  assert.equal(known.has("missing-id"), false);
  const guide = catalog[0].guides![1];
  const id = guideNoteId(guide.id),
    at = "2026-09-23T00:00:00.000Z";
  const incoming = emptyState(at);
  incoming.notes[id] = {
    id,
    courseId: "hearth",
    lessonId: guideNoteLesson(catalog[0], guide),
    sectionId: guide.id,
    text: "Synthetic draft",
    question: false,
    createdAt: at,
    updatedAt: at,
  };
  assert.deepEqual(importPreview(emptyState(at), incoming, known).unknown, []);
  const withoutGuides = collectKnownIds(
    [{ ...catalog[0], guides: undefined }],
    index,
    [],
  );
  assert.deepEqual(
    importPreview(emptyState(at), incoming, withoutGuides).unknown,
    [guide.id],
  );
});

test("linkTargets: a module linking to another module loads alone; unknown modules and beats still fail", async () => {
  const m02 = moduleById("hearth-m02");
  assert.match(
    JSON.stringify(m02),
    /\]\(#\/module\/hearth-m01\/hearth-m01-starter\)/,
  );
  // Alone, without targets, the link to another module cannot resolve.
  assert.throws(
    () => validateTeaching([m02], courses, [], false),
    /Broken teaching module link #\/module\/hearth-m01\/hearth-m01-starter/,
  );
  // The runtime passes targets built from the teaching index.
  const targets = teachingLinkTargets(indexEntries(teaching.modules));
  assert.deepEqual(
    [...targets.keys()],
    ["hearth-m01", "hearth-m02", "hearth-m03"],
  );
  assert.equal(
    validateTeaching([m02], courses, [], false, targets).modules[0].moduleId,
    "hearth-m02",
  );
  const withoutBeat = teachingLinkTargets(
    indexEntries(teaching.modules).map((m) =>
      m.moduleId === "hearth-m01"
        ? { ...m, beats: m.beats.filter((b) => b.id !== "hearth-m01-starter") }
        : m,
    ),
  );
  assert.throws(
    () => validateTeaching([m02], courses, [], false, withoutBeat),
    /Broken teaching module link/,
  );
  const withoutModule = teachingLinkTargets(
    indexEntries(teaching.modules).filter((m) => m.moduleId !== "hearth-m01"),
  );
  assert.throws(
    () => validateTeaching([m02], courses, [], false, withoutModule),
    /Broken teaching module link/,
  );
  // The full build checks against every module in the call.
  assert.equal(validateTeaching(teaching.modules, courses).modules.length, 3);
  for (const link of [
    "[x](#/module/hearth-m01/missing-beat)",
    "[x](#/module/missing-module)",
  ]) {
    const all = structuredClone(teaching.modules);
    all[1].beats[0].handbook.markdown += ` ${link}`;
    assert.throws(
      () => validateTeaching(all, courses),
      /Broken teaching module link/,
    );
    const alone = structuredClone(all[1]);
    assert.throws(
      () => validateTeaching([alone], courses, [], false, targets),
      /Broken teaching module link/,
    );
  }
});

test("academy-check link targets come from every teaching file on disk, skipping unreadable ones", async () => {
  const targets = await diskTeachingLinkTargets(fixtureRoot);
  assert.deepEqual([...(targets.get("hearth-m02") ?? [])].sort(), [
    "hearth-m02-ratio",
    "hearth-m02-strength",
  ]);
  assert.equal(targets.size, 3);
  const temp = await mkdtemp(join(tmpdir(), "spicybrain-link-targets-"));
  try {
    await cp(fixtureRoot, temp, { recursive: true });
    const dir = join(temp, "teaching/hearth");
    await writeFile(join(dir, "hearth-m04.json"), '{"moduleId": "hearth-m0');
    await writeFile(
      join(dir, "media-hearth-m01.json"),
      // Named as media, so never a module, whatever its shape.
      JSON.stringify({ moduleId: "not-a-module", beats: [{ id: "x" }] }),
    );
    await mkdir(join(temp, "teaching/other"), { recursive: true });
    await writeFile(
      join(temp, "teaching/other/other-m01.json"),
      JSON.stringify({ moduleId: "other-m01", beats: [{ id: "other-b1" }] }),
    );
    const onDisk = await diskTeachingLinkTargets(temp);
    assert.deepEqual([...onDisk.keys()].sort(), [
      "hearth-m01",
      "hearth-m02",
      "hearth-m03",
      "other-m01",
    ]);
    assert.deepEqual([...onDisk.get("other-m01")!], ["other-b1"]);
  } finally {
    await rm(temp, { recursive: true, force: true });
  }
  assert.equal(
    (await diskTeachingLinkTargets(join(tmpdir(), "missing"))).size,
    0,
  );
});

test("collection helpers: next in track, related labs and guides, route resume, guide notes and reporters", () => {
  const catalog = stripCourse(hearth);
  assert.deepEqual(nextInTrack(catalog, "hearth-m01"), {
    track: catalog.tracks![0],
    next: "hearth-m02",
  });
  assert.equal(nextInTrack(catalog, "hearth-m02")!.next, undefined);
  assert.equal(
    nextInTrack(catalog, "hearth-m03")!.track.id,
    "hearth-track-oven",
  );
  assert.equal(nextInTrack(stripCourse(photo), "photo-m01"), undefined);
  const related = relatedCollections(catalog, "hearth-m01");
  assert.deepEqual(
    [related.labs.map((l) => l.id), related.guides.map((g) => g.id)],
    [["hearth-lab-schedule"], ["hearth-guide-dense-loaf"]],
  );
  assert.equal(hasCollections(catalog), true);
  assert.equal(hasCollections(stripCourse(photo)), false);
  assert.equal(photo.tracks, undefined);
  assert.equal(photo.routes, undefined);
  const index = indexEntries(teaching.modules);
  const position = (moduleId: string, beatId: string, updatedAt: string) => ({
    moduleId,
    beatId,
    updatedAt,
    view: "deck" as const,
  });
  const positions = {
    a: position("hearth-m01", "hearth-m01-proof", "2026-09-23T10:00:00.000Z"),
    b: position("hearth-m03", "hearth-m03-steam", "2026-09-23T11:00:00.000Z"),
    c: position("hearth-m02", "removed-beat", "2026-09-23T12:00:00.000Z"),
    d: position("photo-m01", "photo-m01-motion", "2026-09-23T13:00:00.000Z"),
  };
  const essential = catalog.routes!.find((r) => r.essential)!;
  assert.equal(
    routeResume(essential.moduleIds, positions, index)?.beatId,
    "hearth-m03-steam",
  );
  assert.equal(
    routeResume(["hearth-m01"], positions, index)?.beatId,
    "hearth-m01-proof",
  );
  assert.equal(routeResume(["hearth-m02"], positions, index), undefined);
  const [dense, plan] = catalog.guides!;
  assert.equal(guideNoteId(dense.id), "note-hearth-guide-dense-loaf");
  assert.equal(guideNoteLesson(catalog, dense), "hearth-m01-l01");
  assert.equal(
    guideNoteLesson(catalog, plan),
    catalog.modules[0].lessons[0].id,
  );
  assert.equal(reporterText("joint"), "The customer and the vendor jointly");
  assert.equal(reporterText("a trade magazine"), "a trade magazine");
  // An inherited object key is shown as written, never as a function.
  assert.equal(reporterText("constructor"), "constructor");
  assert.equal(reporterText("toString"), "toString");
  assert.deepEqual(labClassOrder, [
    "local-executed",
    "tabletop",
    "platform-guide",
  ]);
  for (const k of labClassOrder)
    assert.doesNotMatch(labClassText[k].legend, /verified/i);
  const beats = index[0];
  assert.deepEqual(beatNeighbourhood(beats, "hearth-m01-proof"), {
    index: 1,
    total: 2,
    previous: { id: "hearth-m01-starter" },
  });
  assert.equal(
    beatNeighbourhood(beats, "hearth-m01-starter").previous,
    undefined,
  );
});

test("photography remains a course without collections after the schema additions", () => {
  assert.equal(validateCourses([structuredClone(photo)]).length, 1);
  assert.equal(photoTeaching.modules.length, 2);
  for (const key of [
    "tracks",
    "routes",
    "labs",
    "guides",
    "cases",
    "crosswalk",
  ])
    assert.equal(key in photo, false, key);
  for (const s of photo.scenarios) {
    assert.equal("revisionNotice" in s, false);
    assert.equal("downloadIds" in s, false);
  }
});
