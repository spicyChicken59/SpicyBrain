// Probes every cited URL and writes docs/evidence/source-availability.json.
//
// With --from-log <file> --run <url> --head <sha> nothing is fetched: the
// report is rebuilt from a CI job log of this same script, which prints the
// URL count and every URL that did not answer. It is used where the CI
// artifact cannot be downloaded. The rebuild refuses a log whose URL count
// differs from the content being reported, so a log of other content cannot
// be passed off as this content's probe.
import { writeFile, mkdir, readFile } from "node:fs/promises";
import { loadCourses, loadTeaching } from "./content.ts";
const arg = (name: string) => {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : undefined;
};
const fromLog = arg("--from-log");
let checkedAt = new Date().toISOString();
const courses = await loadCourses();
const teaching = await loadTeaching(courses);
const sources = [
  ...courses.flatMap((c) =>
    c.sources.map((s) => ({
      courseId: c.id,
      moduleId: null,
      sourceId: s.id,
      title: s.title,
      url: s.url,
      editorialReviewDate: s.reviewDate,
      reviewedEvidence: null,
      caveat: s.caveat,
      claimIds: c.claims
        .filter((cl) => cl.sourceIds.includes(s.id))
        .map((cl) => cl.id),
    })),
  ),
  ...teaching.modules.flatMap((m) =>
    m.sources.map((s) => ({
      courseId: m.courseId,
      moduleId: m.moduleId,
      sourceId: s.id,
      title: s.title,
      url: s.url,
      editorialReviewDate: s.reviewedAt,
      reviewedEvidence: s.reviewedEvidence,
      caveat: s.caveat,
      claimIds: m.claims
        .filter((cl) => cl.sourceIds.includes(s.id))
        .map((cl) => cl.id),
    })),
  ),
  ...teaching.media.map((s) => ({
    courseId: s.courseId,
    moduleId: s.moduleId,
    sourceId: s.id,
    title: s.title,
    url: s.url,
    editorialReviewDate: s.reviewedAt,
    reviewedEvidence: s.reviewedEvidence,
    caveat: s.limits,
    claimIds: [],
  })),
];
const urls = [...new Set(sources.map((s) => s.url))];
const results = new Map<
  string,
  { httpStatus: number | null; finalURL: string; probeStatus: string }
>();
let provenance: Record<string, string> | undefined;
if (fromLog) {
  const log = await readFile(fromLog, "utf8");
  const summary = log.match(
    /(\d+) source\/media records across (\d+) URLs; (\d+) URLs reachable/,
  );
  if (!summary) throw Error(`${fromLog}: no availability summary line`);
  if (Number(summary[2]) !== urls.length)
    throw Error(
      `${fromLog} probed ${summary[2]} URLs; this content cites ${urls.length}`,
    );
  const stamp = log.match(
    /(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)[^\n]*source\/media records/,
  );
  if (stamp) checkedAt = stamp[1];
  for (const m of log.matchAll(/not reachable: (\S+) (\S+)/g)) {
    if (!urls.includes(m[2])) throw Error(`${fromLog}: unknown URL ${m[2]}`);
    const status = Number(m[1]);
    results.set(m[2], {
      httpStatus: Number.isNaN(status) ? null : status,
      finalURL: m[2],
      probeStatus: Number.isNaN(status) ? m[1] : "HTTP error",
    });
  }
  for (const url of urls)
    if (!results.has(url))
      results.set(url, {
        httpStatus: null,
        finalURL: url,
        probeStatus: "reachable",
      });
  const reachable = [...results.values()].filter(
    (r) => r.probeStatus === "reachable",
  ).length;
  if (reachable !== Number(summary[3]))
    throw Error(
      `${fromLog}: ${urls.length - reachable} URLs listed unreachable, but the summary counts ${urls.length - Number(summary[3])}`,
    );
  provenance = {
    method:
      "Rebuilt from the CI job log of npm run report:sources: every URL the log lists as not reachable keeps its logged status; every other URL counted reachable by the log's own summary. HTTP status and final URL of reachable pages are not in the log and are left null/unchanged.",
    run: arg("--run") ?? "unstated",
    head: arg("--head") ?? "unstated",
  };
}
for (let i = 0; fromLog === undefined && i < urls.length; i += 4) {
  await Promise.all(
    urls.slice(i, i + 4).map(async (url) => {
      try {
        const response = await fetch(url, {
          signal: AbortSignal.timeout(8000),
          redirect: "follow",
        });
        results.set(url, {
          httpStatus: response.status,
          finalURL: response.url,
          probeStatus: response.ok ? "reachable" : "HTTP error",
        });
        await response.body?.cancel();
      } catch (error) {
        results.set(url, {
          httpStatus: null,
          finalURL: url,
          probeStatus: error instanceof Error ? error.name : "fetch failed",
        });
      }
    }),
  );
}
const rows = sources.map((s) => ({ ...s, ...results.get(s.url), checkedAt }));
await mkdir("docs/evidence", { recursive: true });
await writeFile(
  "docs/evidence/source-availability.json",
  JSON.stringify(
    {
      checkedAt,
      ...(provenance ? { reconstructedFrom: provenance } : {}),
      note: "Availability only: a reachable page does not verify a claim, captions or playback. Actual primary-source reading is recorded per source/claim and in teacher-first editorial/media reviews. Failed probes can reflect access restrictions; inspect rather than silently relabel them.",
      uniqueURLs: urls.length,
      sources: rows,
    },
    null,
    2,
  ) + "\n",
);
console.log(
  `${rows.length} source/media records across ${urls.length} URLs; ${[...results.values()].filter((r) => r.probeStatus === "reachable").length} URLs reachable. Report: docs/evidence/source-availability.json`,
);
// Unreachable URLs are listed in the log too, so they can be inspected where
// the artifact cannot be downloaded. A failed probe is not a finding by itself.
for (const [url, r] of results)
  if (r.probeStatus !== "reachable")
    console.log(`not reachable: ${r.httpStatus ?? r.probeStatus} ${url}`);
