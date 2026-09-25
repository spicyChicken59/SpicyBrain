import { readdir, readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { test, expect } from "@playwright/test";

type Download = { id: string; path: string; sha256: string };
const sha256 = (bytes: Buffer) =>
  createHash("sha256").update(bytes).digest("hex");

// The ZIP a learner receives must be the committed, hash-manifested file, from
// the root build and from the nested-path build alike. Extraction and
// execution of each lab download is the labs job (run-labs.py --from-zip).
test("Every registered download is served byte-identical to its committed, hash-manifested file from root and nested builds", async ({
  request,
}) => {
  const downloads: Download[] = [];
  for (const entry of await readdir("content/courses", {
    withFileTypes: true,
  })) {
    if (!entry.isDirectory()) continue;
    const course = JSON.parse(
      await readFile(`content/courses/${entry.name}/course.json`, "utf8"),
    ) as { downloads?: Download[] };
    downloads.push(...(course.downloads ?? []));
  }
  expect(downloads.length).toBeGreaterThan(0);
  for (const download of downloads) {
    const path = download.path.replace(/^downloads\//, "");
    const committed = await readFile(`content/downloads/${path}`);
    expect(sha256(committed), `${download.id}: committed file`).toBe(
      download.sha256,
    );
    for (const prefix of ["/", "/SpicyBrain/"]) {
      const response = await request.get(`${prefix}content-downloads/${path}`);
      expect(response.status(), `${prefix} ${download.id}`).toBe(200);
      const served = await response.body();
      expect(sha256(served), `${prefix} ${download.id}: served file`).toBe(
        download.sha256,
      );
      expect(served.equals(committed)).toBe(true);
    }
  }
});
