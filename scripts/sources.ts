import { writeFile, mkdir } from "node:fs/promises";
import { loadCourses, loadTeaching } from "./content.ts";
const checkedAt = new Date().toISOString();
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
for (let i = 0; i < urls.length; i += 4) {
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
