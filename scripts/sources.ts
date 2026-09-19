import { writeFile, mkdir } from "node:fs/promises";
import { loadCourses } from "./content.ts";
const checkedAt = new Date().toISOString(),
  courses = await loadCourses();
const rows = [];
for (const c of courses)
  for (let i = 0; i < c.sources.length; i += 4) {
    const batch = await Promise.all(
      c.sources.slice(i, i + 4).map(async (s) => {
        let status: string,
          httpStatus: number | null = null,
          finalURL = s.url;
        try {
          const r = await fetch(s.url, {
            signal: AbortSignal.timeout(8000),
            redirect: "follow",
          });
          httpStatus = r.status;
          finalURL = r.url;
          status = r.ok ? "reachable" : "HTTP error";
          await r.body?.cancel();
        } catch (e) {
          status = e instanceof Error ? e.name : "fetch failed";
        }
        return {
          courseId: c.id,
          sourceId: s.id,
          title: s.title,
          url: s.url,
          finalURL,
          httpStatus,
          probeStatus: status,
          checkedAt,
          contentAccessDate: s.accessDate,
          editorialReviewDate: s.reviewDate,
          caveat: s.caveat,
          claimIds: c.claims
            .filter((cl) => cl.sourceIds.includes(s.id))
            .map((cl) => cl.id),
        };
      }),
    );
    rows.push(...batch);
  }
await mkdir("docs/evidence", { recursive: true });
await writeFile(
  "docs/evidence/source-availability.json",
  JSON.stringify(
    {
      checkedAt,
      note: "Availability is separate from factual review. A reachable page does not verify a claim; a failed probe is not a rendering failure. Builder primary-source reading is recorded in SOURCE-REVIEW.md.",
      sources: rows,
    },
    null,
    2,
  ) + "\n",
);
console.log(
  `${rows.length} sources probed; ${rows.filter((r) => r.probeStatus === "reachable").length} reachable. Report: docs/evidence/source-availability.json`,
);
