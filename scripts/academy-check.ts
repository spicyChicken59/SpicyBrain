/**
 * Academy content check.
 *
 * `--module <id>` validates one not-yet-registered module package in
 * isolation (its course package, lessons, teaching module and media file)
 * and runs the editorial quality audit on it. Without `--module`, the whole
 * registered course is validated, audited and compared against the academy
 * contract manifest; `--write` records docs/academy/COVERAGE.json.
 *
 * The audit is a floor, not a judgement: it rejects label-only content,
 * missing checks, thin handbooks and duplicated prompts. Editorial review
 * still decides whether a beat teaches.
 */
import { readFile, writeFile, mkdir, access, readdir } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { loadCourses, loadTeaching, root } from "./content.ts";
import type { Course } from "../src/content-schema.ts";
import {
  validateTeaching,
  type TeachingModule,
  type TeachingMedia,
} from "../src/teaching-schema.ts";

export type Finding = {
  level: "fail" | "warn";
  where: string;
  message: string;
};
const words = (s: string) => s.trim().split(/\s+/).filter(Boolean).length;
const genericTitle =
  /^(overview|introduction|summary|key concepts?|deep dive|recap|conclusion|next steps?|wrap[- ]?up|background)$/i;
const placeholder =
  /\bTODO\b|\bTBD\b|lorem ipsum|\[placeholder\]|placeholder text|coming soon|\[AUTHOR/i;

export type ContractModule = {
  label: string;
  moduleId: string;
  disposition: "retained" | "new";
  checkStyle: "objective-heavy" | "judgement";
  topics: string[];
  labIds: string[];
  guideIds: string[];
};
export type Contract = {
  schemaVersion: 1;
  courseId: string;
  title: string;
  tracks: {
    key: string;
    id: string;
    title: string;
    modules: ContractModule[];
  }[];
  capstoneIds: string[];
  labIds: string[];
  guideIds: string[];
  caseCount: number;
};

export function auditModule(
  course: Course,
  m: TeachingModule,
  media: TeachingMedia[],
  options: {
    checkStyle?: ContractModule["checkStyle"];
    mediaDecision?: unknown;
    disposition?: ContractModule["disposition"];
  } = {},
): { findings: Finding[]; stats: Record<string, number | string> } {
  const f: Finding[] = [];
  const fail = (where: string, message: string) =>
    f.push({ level: "fail", where, message });
  const warn = (where: string, message: string) =>
    f.push({ level: "warn", where, message });
  const owned = course.modules.find((x) => x.id === m.moduleId)!.lessons;
  // Retained modules keep their immutable legacy cards, checks and lesson
  // bodies; their floors are the accepted release's, not the new authoring
  // standard. New modules must meet the stricter floors.
  const legacy = options.disposition === "retained";
  const floor = {
    selfModel: legacy ? 12 : 25,
    selfReasoning: legacy ? 6 : 12,
    cardAnswer: legacy ? 4 : 8,
    cardExplanation: legacy ? 8 : 25,
    lessonWords: legacy ? 300 : 600,
    scenarioModel: legacy ? 80 : 120,
    rationale: legacy ? 3 : 6,
    appliedModel: legacy ? 30 : 60,
    cardPrompt: legacy ? 3 : 5,
    sourceEvidence: legacy ? 5 : 10,
  };
  const serialized = JSON.stringify(m);
  if (placeholder.test(serialized))
    fail(m.moduleId, "placeholder text present");
  if (m.outcomes.length < 2) warn(m.moduleId, "fewer than two outcomes");
  if (words(m.editorialRationale) < 15)
    warn(m.moduleId, "editorial rationale is thin");
  if (words(m.recap.markdown) < 30) fail(m.moduleId, "recap under 30 words");
  if (words(m.appliedTask.modelAnswer) < floor.appliedModel)
    fail(
      m.moduleId,
      `applied task model answer under ${floor.appliedModel} words`,
    );
  if (words(m.appliedTask.reasoning) < 15)
    fail(m.moduleId, "applied task reasoning under 15 words");
  if (m.appliedTask.beatIds.length < 2)
    warn(m.moduleId, "applied task draws on fewer than two beats");
  // Beats
  if (m.beats.length < 8)
    fail(m.moduleId, `only ${m.beats.length} beats (minimum 8)`);
  if (m.beats.length > 16)
    warn(m.moduleId, `${m.beats.length} beats (more than 16 needs a reason)`);
  const titles = new Set<string>();
  let objective = 0,
    samajh = 0;
  const samajhKeywords = new Map<string, number>();
  const checks = [
    ...owned.flatMap((l) => l.questions),
    ...m.questions,
    ...m.selfQuestions,
  ];
  for (const b of m.beats) {
    const w = `${m.moduleId}/${b.id}`;
    const n = words(b.explanation);
    if (n < 35) fail(w, `explanation ${n} words (minimum 35)`);
    if (n > 120) fail(w, `explanation ${n} words (maximum 120)`);
    if (genericTitle.test(b.title.trim()))
      fail(w, `generic beat title "${b.title}"`);
    const key = b.title.trim().toLowerCase();
    if (titles.has(key)) fail(w, `duplicate beat title "${b.title}"`);
    titles.add(key);
    if (words(b.handbook.markdown) < 100)
      fail(w, `handbook ${words(b.handbook.markdown)} words (minimum 100)`);
    if (words(b.outcome) < 4) warn(w, "outcome is very short");
    const v = m.visuals.find((x) => x.id === b.visualId)!;
    for (const s of v.states) {
      const rich =
        s.nodes.length >= 2 ||
        (s.table &&
          (s.table.rows.length >= 2 || s.table.columns.length >= 2)) ||
        !!s.equation;
      if (!rich)
        fail(
          `${w}/${v.id}/${s.id}`,
          "visual state carries no mechanism (need ≥2 nodes, a table or an equation)",
        );
      const te = v.textEquivalent.toLowerCase();
      if (!te.includes(s.title.toLowerCase()))
        fail(`${w}/${v.id}`, `text equivalent omits state "${s.title}"`);
      for (const node of s.nodes)
        if (!te.includes(node.label.toLowerCase()))
          fail(`${w}/${v.id}`, `text equivalent omits node "${node.label}"`);
    }
    if (words(v.caption) < 5) warn(`${w}/${v.id}`, "caption is very short");
    for (const qid of b.questionIds) {
      const q = checks.find((x) => x.id === qid)!;
      if ("options" in q) {
        objective++;
        if (q.options.length < 3)
          fail(qid, "objective check needs at least three choices");
        for (const o of q.options)
          if (words(o.rationale) < floor.rationale)
            fail(
              qid,
              `rationale for "${o.text}" under ${floor.rationale} words`,
            );
        if (words(q.prompt) < 6) warn(qid, "prompt is very short");
      } else {
        if (words(q.modelAnswer) < floor.selfModel)
          fail(qid, `self-check model answer under ${floor.selfModel} words`);
        if (words(q.reasoning) < floor.selfReasoning)
          fail(qid, `self-check reasoning under ${floor.selfReasoning} words`);
      }
    }
    if (b.samajh) {
      samajh++;
      const sw = words(b.samajh.text);
      if (sw < 25 || sw > 120) fail(w, `Samajh ${sw} words (expected 25–120)`);
      if (words(b.samajh.mapping) < 5) fail(w, "Samajh mapping under 5 words");
      if (words(b.samajh.boundary) < 5)
        fail(w, "Samajh boundary under 5 words");
      for (const kw of [
        "godown",
        "warehouse",
        "restaurant",
        "kitchen",
        "register",
        "dabba",
        "chai",
        "cricket",
        "shaadi",
        "train",
      ])
        if (b.samajh.text.toLowerCase().includes(kw))
          samajhKeywords.set(kw, (samajhKeywords.get(kw) ?? 0) + 1);
    }
  }
  for (const [kw, n] of samajhKeywords)
    if (n > 2)
      warn(m.moduleId, `Samajh reuses the "${kw}" metaphor ${n} times`);
  if (samajh < 2)
    fail(m.moduleId, `only ${samajh} Samajh explanations (minimum 2)`);
  const ratio = m.beats.length
    ? objective /
      m.beats.map((b) => b.questionIds.length).reduce((a, b) => a + b, 0)
    : 0;
  if (options.checkStyle === "objective-heavy" && ratio < 0.5)
    fail(
      m.moduleId,
      `objective checks are ${Math.round(ratio * 100)}% (mechanism modules need at least 50%)`,
    );
  // Cards
  const core = owned.flatMap((l) => l.cards);
  if (core.length < 10)
    fail(m.moduleId, `${core.length} core cards (minimum 10)`);
  if (m.extensionCards.length !== 4)
    fail(m.moduleId, `${m.extensionCards.length} extension cards (exactly 4)`);
  const prompts = new Set<string>();
  for (const c of [...core, ...m.extensionCards]) {
    const key = c.prompt.trim().toLowerCase();
    if (prompts.has(key)) fail(c.id, "duplicate card prompt within module");
    prompts.add(key);
    if (words(c.prompt) < floor.cardPrompt)
      fail(c.id, `card prompt under ${floor.cardPrompt} words`);
    if (words(c.answer) < floor.cardAnswer)
      fail(c.id, `card answer under ${floor.cardAnswer} words`);
    if (words(c.explanation) < floor.cardExplanation)
      fail(c.id, `card explanation under ${floor.cardExplanation} words`);
    if ("whyItMatters" in c && words(String(c.whyItMatters)) < 8)
      fail(c.id, "whyItMatters under 8 words");
    if (m.beats.some((b) => b.title.trim().toLowerCase() === key))
      fail(c.id, "card prompt repeats a beat title");
  }
  // Sources, claims, concepts
  for (const s of m.sources) {
    if (words(s.reviewedEvidence) < floor.sourceEvidence)
      fail(s.id, `source reviewedEvidence under ${floor.sourceEvidence} words`);
    if (words(s.caveat) < 5) warn(s.id, "source caveat is very short");
  }
  const referenced = new Set([
    ...m.beats.flatMap((b) => b.conceptIds),
    ...m.extensionCards.flatMap((c) => c.conceptIds),
    ...[...m.questions, ...m.selfQuestions].flatMap((q) => q.conceptIds),
  ]);
  for (const g of m.concepts) {
    if (!referenced.has(g.id))
      warn(g.id, "concept is never referenced by a beat, card or check");
    if (words(g.definition) < 6) fail(g.id, "concept definition under 6 words");
    if (words(g.example) < 4) fail(g.id, "concept example under 4 words");
  }
  // Lessons owned
  for (const l of owned) {
    const kinds = new Set(l.sections.map((s) => s.kind));
    const total = l.sections.reduce((n, s) => n + words(s.markdown), 0);
    if (total < floor.lessonWords)
      fail(l.id, `lesson body ${total} words (minimum ${floor.lessonWords})`);
    for (const kind of ["exercise", "solution", "mistakes", "sources"])
      if (
        !kinds.has(kind as never) &&
        !(kind === "exercise" && kinds.has("try"))
      )
        warn(l.id, `lesson lacks a ${kind} section`);
    if (l.questions.length < 2) fail(l.id, "lesson needs at least two checks");
  }
  // Scenario
  const scenario = course.scenarios.find(
    (s) => s.id === course.modules.find((x) => x.id === m.moduleId)!.scenarioId,
  )!;
  if (words(scenario.model) < floor.scenarioModel)
    fail(
      scenario.id,
      `scenario model response under ${floor.scenarioModel} words`,
    );
  if (scenario.requirements.length < 3)
    warn(scenario.id, "scenario has fewer than three requirements");
  if (!scenario.disclosures.length)
    warn(scenario.id, "scenario has no stakeholder disclosures");
  // Media or documented decision
  if (!media.length && !options.mediaDecision)
    fail(
      m.moduleId,
      "no reviewed media placement and no documented editorial no-video decision",
    );
  return {
    findings: f,
    stats: {
      beats: m.beats.length,
      objectiveChecks: objective,
      samajh,
      coreCards: core.length,
      extensionCards: m.extensionCards.length,
      visuals: m.visuals.length,
      states: m.visuals.reduce((n, v) => n + v.states.length, 0),
      concepts: m.concepts.length,
      sources: m.sources.length,
      media: media.length,
      lessonWords: owned.reduce(
        (n, l) => n + l.sections.reduce((k, s) => k + words(s.markdown), 0),
        0,
      ),
      handbookWords: m.beats.reduce(
        (n, b) => n + words(b.handbook.markdown),
        0,
      ),
    },
  };
}

const exists = (p: string) =>
  access(p).then(
    () => true,
    () => false,
  );
async function readJson<T>(p: string): Promise<T> {
  return JSON.parse(await readFile(p, "utf8")) as T;
}
/** Editorial no-video decisions: the shared register plus one file per module. */
async function mediaDecisions(): Promise<Record<string, unknown>> {
  const shared = join(root, "docs/academy/MEDIA-DECISIONS.json");
  const decisions: Record<string, unknown> = (await exists(shared))
    ? await readJson<Record<string, unknown>>(shared)
    : {};
  const directory = join(root, "docs/academy/media-decisions");
  if (await exists(directory))
    for (const name of (await readdir(directory)).filter((n) =>
      n.endsWith(".json"),
    )) {
      const record = await readJson<{ moduleId?: string }>(
        join(directory, name),
      );
      if (record.moduleId) decisions[record.moduleId] = record;
    }
  return decisions;
}

export async function checkModules(moduleIds: string[]) {
  const courseDir = join(root, "content/courses/dbxfe");
  const raw = await readJson<{ modules: { file?: string; id?: string }[] }>(
    join(courseDir, "course.json"),
  );
  const registered = (id: string) =>
    raw.modules.some((m) => m.id === id || m.file === `modules/${id}.json`);
  const extra = moduleIds
    .filter((id) => !registered(id))
    .map((id) => `modules/${id}.json`);
  const courses = await loadCourses(join(root, "content"), {
    extraModuleFiles: { dbxfe: extra },
  });
  const course = courses.find((c) => c.id === "dbxfe")!;
  const decisions = await mediaDecisions();
  const contract = (await exists(join(courseDir, "academy.json")))
    ? await readJson<Contract>(join(courseDir, "academy.json"))
    : undefined;
  const results: Record<string, ReturnType<typeof auditModule>> = {};
  let failed = false;
  for (const id of moduleIds) {
    const teachingPath = join(root, "content/teaching/dbxfe", `${id}.json`);
    const mediaPath = join(root, "content/teaching/dbxfe", `media-${id}.json`);
    const moduleRaw = await readJson<unknown>(teachingPath);
    const shared = join(root, "content/teaching/dbxfe/media.json");
    const mediaRaw = [
      ...((await exists(mediaPath))
        ? await readJson<unknown[]>(mediaPath)
        : []),
      ...((await exists(shared))
        ? (await readJson<{ moduleId: string }[]>(shared)).filter(
            (v) => v.moduleId === id,
          )
        : []),
    ];
    const { modules, media } = validateTeaching(
      [moduleRaw],
      courses,
      mediaRaw,
      true,
    );
    const contractModule = contract?.tracks
      .flatMap((t) => t.modules)
      .find((x) => x.moduleId === id);
    const result = auditModule(course, modules[0], media, {
      checkStyle: contractModule?.checkStyle,
      mediaDecision: decisions[id],
      disposition: contractModule?.disposition,
    });
    if (contractModule) {
      const text = JSON.stringify(modules[0]).toLowerCase();
      for (const topic of contractModule.topics)
        if (!text.includes(topic.toLowerCase()))
          result.findings.push({
            level: "fail",
            where: id,
            message: `contract topic "${topic}" does not appear in the module text`,
          });
    }
    results[id] = result;
    if (result.findings.some((x) => x.level === "fail")) failed = true;
  }
  return { results, failed };
}

export async function checkCourse(write = false) {
  const courses = await loadCourses();
  const course = courses.find((c) => c.id === "dbxfe")!;
  const teaching = await loadTeaching(courses);
  const courseDir = join(root, "content/courses/dbxfe");
  const contract = await readJson<Contract>(join(courseDir, "academy.json"));
  const decisions = await mediaDecisions();
  const findings: Finding[] = [];
  const modules: Record<string, Record<string, number | string>> = {};
  const contractModules = contract.tracks.flatMap((t) => t.modules);
  const prompts = new Map<string, string>();
  for (const cm of contractModules) {
    const m = teaching.modules.find((x) => x.moduleId === cm.moduleId);
    if (!m) {
      findings.push({
        level: "fail",
        where: cm.label,
        message: `contract module ${cm.moduleId} has no teaching module`,
      });
      continue;
    }
    const media = teaching.media.filter((v) => v.moduleId === m.moduleId);
    const r = auditModule(course, m, media, {
      checkStyle: cm.checkStyle,
      mediaDecision: decisions[m.moduleId],
      disposition: cm.disposition,
    });
    const text = JSON.stringify(m).toLowerCase();
    for (const topic of cm.topics)
      if (!text.includes(topic.toLowerCase()))
        r.findings.push({
          level: "fail",
          where: cm.moduleId,
          message: `contract topic "${topic}" does not appear in the module text`,
        });
    for (const labId of cm.labIds)
      if (!course.labs?.some((l) => l.id === labId))
        r.findings.push({
          level: "fail",
          where: cm.moduleId,
          message: `contract lab ${labId} is missing from the course`,
        });
    for (const guideId of cm.guideIds)
      if (!course.guides?.some((g) => g.id === guideId))
        r.findings.push({
          level: "fail",
          where: cm.moduleId,
          message: `contract guide ${guideId} is missing from the course`,
        });
    const track = course.tracks?.find((t) => t.moduleIds.includes(m.moduleId));
    const contractTrack = contract.tracks.find((t) => t.modules.includes(cm));
    if (!track || track.id !== contractTrack!.id)
      r.findings.push({
        level: "fail",
        where: cm.moduleId,
        message: `module is not in track ${contractTrack!.id}`,
      });
    findings.push(...r.findings);
    modules[cm.label] = {
      moduleId: cm.moduleId,
      disposition: cm.disposition,
      ...r.stats,
    };
    const owned = course.modules.find((x) => x.id === m.moduleId)!.lessons;
    for (const c of [...owned.flatMap((l) => l.cards), ...m.extensionCards]) {
      const key = c.prompt.trim().toLowerCase();
      if (prompts.has(key) && prompts.get(key) !== m.moduleId)
        findings.push({
          level: "fail",
          where: c.id,
          message: `card prompt duplicates a card in ${prompts.get(key)}`,
        });
      prompts.set(key, m.moduleId);
    }
  }
  for (const m of teaching.modules)
    if (
      m.courseId === "dbxfe" &&
      !contractModules.some((cm) => cm.moduleId === m.moduleId)
    )
      findings.push({
        level: "fail",
        where: m.moduleId,
        message: "teaching module is not in the academy contract",
      });
  if (contractModules.length !== 48)
    findings.push({
      level: "fail",
      where: "contract",
      message: `${contractModules.length} contract modules (expected 48)`,
    });
  for (const id of contract.capstoneIds)
    if (!course.scenarios.some((s) => s.id === id && s.isCapstone))
      findings.push({
        level: "fail",
        where: id,
        message: "contract capstone missing",
      });
  for (const id of contract.labIds)
    if (!course.labs?.some((l) => l.id === id))
      findings.push({
        level: "fail",
        where: id,
        message: "contract lab missing",
      });
  for (const id of contract.guideIds)
    if (!course.guides?.some((g) => g.id === id))
      findings.push({
        level: "fail",
        where: id,
        message: "contract guide missing",
      });
  if ((course.cases?.length ?? 0) < contract.caseCount)
    findings.push({
      level: "fail",
      where: "cases",
      message: `${course.cases?.length ?? 0} case analyses (contract ${contract.caseCount})`,
    });
  const totals = {
    modules: contractModules.length,
    beats: teaching.modules.reduce((n, m) => n + m.beats.length, 0),
    visualStates: teaching.modules.reduce(
      (n, m) => n + m.visuals.reduce((k, v) => k + v.states.length, 0),
      0,
    ),
    coreCards: course.modules.reduce(
      (n, m) => n + m.lessons.reduce((k, l) => k + l.cards.length, 0),
      0,
    ),
    extensionCards: teaching.modules.reduce(
      (n, m) => n + m.extensionCards.length,
      0,
    ),
    samajh: teaching.modules.reduce(
      (n, m) => n + m.beats.filter((b) => b.samajh).length,
      0,
    ),
    lessons: course.modules.reduce((n, m) => n + m.lessons.length, 0),
    scenarios: course.scenarios.filter((s) => !s.isCapstone).length,
    capstones: course.scenarios.filter((s) => s.isCapstone).length,
    labs: course.labs?.length ?? 0,
    labsByClass: Object.fromEntries(
      ["local-executed", "tabletop", "platform-guide"].map((k) => [
        k,
        course.labs?.filter((l) => l.executionClass === k).length ?? 0,
      ]),
    ),
    guides: course.guides?.length ?? 0,
    cases: course.cases?.length ?? 0,
    crosswalk: course.crosswalk?.length ?? 0,
    media: teaching.media.length,
    mediaDecisions: Object.keys(decisions).length,
    tracks: course.tracks?.length ?? 0,
  };
  const floors: [string, number, number][] = [
    ["modules", totals.modules, 48],
    ["beats", totals.beats, 480],
    ["cards", totals.coreCards + totals.extensionCards, 672],
    ["labs", totals.labs, 24],
    ["guides", totals.guides, 32],
    ["capstones", totals.capstones, 3],
    ["cases", totals.cases, 8],
  ];
  for (const [name, value, floor] of floors)
    if (value < floor)
      findings.push({
        level: "fail",
        where: "totals",
        message: `${name}: ${value} below contract floor ${floor}`,
      });
  const report = {
    date: new Date().toISOString().slice(0, 10),
    totals,
    modules,
    findings,
  };
  if (write) {
    await mkdir(join(root, "docs/academy"), { recursive: true });
    await writeFile(
      join(root, "docs/academy/COVERAGE.json"),
      JSON.stringify(report, null, 2) + "\n",
    );
  }
  return report;
}

if (
  process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const args = process.argv.slice(2);
  const moduleIds = args.flatMap((a, i) =>
    a === "--module" ? [args[i + 1]] : [],
  );
  if (moduleIds.length) {
    const { results, failed } = await checkModules(moduleIds);
    for (const [id, r] of Object.entries(results)) {
      console.log(`\n== ${id} ==`);
      console.log(JSON.stringify(r.stats));
      for (const x of r.findings)
        console.log(`${x.level.toUpperCase()} ${x.where}: ${x.message}`);
      if (!r.findings.some((x) => x.level === "fail"))
        console.log("PASS (no failing findings)");
    }
    process.exit(failed ? 1 : 0);
  } else {
    const report = await checkCourse(args.includes("--write"));
    console.log(JSON.stringify(report.totals, null, 2));
    for (const x of report.findings)
      console.log(`${x.level.toUpperCase()} ${x.where}: ${x.message}`);
    const fails = report.findings.filter((x) => x.level === "fail").length;
    console.log(
      fails
        ? `FAIL: ${fails} failing findings`
        : "PASS: academy contract satisfied",
    );
    process.exit(fails ? 1 : 0);
  }
}
