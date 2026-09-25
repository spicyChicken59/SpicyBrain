import { test } from "node:test";
import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import { extname, join } from "node:path";

// Published content, downloads and evidence must not carry the build
// machine's layout or environment: virtual-environment and scratch paths,
// JVM proxy options or proxy host lists. Lab evidence names its interpreter
// and scratch locations with placeholders (scripts/public-evidence.py).
const forbidden =
  /\/home\/user\/|\/tmp\/claude-|scratchpad|JAVA_TOOL_OPTIONS|proxyHost|nonProxyHosts/;
const textTypes = new Set([
  ".json",
  ".md",
  ".py",
  ".sql",
  ".csv",
  ".txt",
  ".yml",
  ".yaml",
  ".svg",
]);

async function files(dir: string): Promise<string[]> {
  const out: string[] = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...(await files(path)));
    else if (textTypes.has(extname(entry.name))) out.push(path);
  }
  return out;
}

test("content, the academy's documents and evidence, and the README carry no build-machine paths or proxy settings", async () => {
  const scanned = [
    ...(await files("content")),
    // Every academy document: briefs, reviews, lab evidence, media
    // decisions, the release record and its evidence.
    ...(await files("docs/academy")),
    ...(await files("docs/evidence")),
    "README.md",
  ];
  assert.ok(scanned.length > 100);
  const leaks = [];
  for (const path of scanned) {
    const text = await readFile(path, "utf8");
    const match = forbidden.exec(text);
    if (match) leaks.push(`${path}: ${match[0]}`);
  }
  assert.deepEqual(leaks, []);
});
