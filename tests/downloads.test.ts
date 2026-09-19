import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  loadCourses,
  loadDownloads,
  validateDownloadArchive,
} from "../scripts/content.ts";
import { safePath, validateCourses } from "../src/content-schema.ts";

// A stored ZIP member is enough to exercise the actual central-directory parser.
function archive(name = "README.md", attributes = 0) {
  const filename = Buffer.from(name),
    body = Buffer.from("A synthetic exercise.\n"),
    local = Buffer.alloc(30),
    central = Buffer.alloc(46),
    end = Buffer.alloc(22);
  local.writeUInt32LE(0x04034b50, 0);
  local.writeUInt16LE(20, 4);
  local.writeUInt32LE(body.length, 18);
  local.writeUInt32LE(body.length, 22);
  local.writeUInt16LE(filename.length, 26);
  central.writeUInt32LE(0x02014b50, 0);
  central.writeUInt16LE(20, 4);
  central.writeUInt16LE(20, 6);
  central.writeUInt32LE(body.length, 20);
  central.writeUInt32LE(body.length, 24);
  central.writeUInt16LE(filename.length, 28);
  central.writeUInt32LE(attributes, 38);
  const contents = Buffer.concat([local, filename, body]);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(1, 8);
  end.writeUInt16LE(1, 10);
  end.writeUInt32LE(central.length + filename.length, 12);
  end.writeUInt32LE(contents.length, 16);
  return Buffer.concat([contents, central, filename, end]);
}
test("download validation accepts a bounded text/Python/SQL bundle and rejects unsafe members", () => {
  for (const name of [
    "README.md",
    "data/events.csv",
    "solution.py",
    "queries.sql",
  ])
    assert.doesNotThrow(() => validateDownloadArchive(archive(name)));
  for (const name of [
    "../outside.py",
    "/absolute.py",
    "folder\\outside.py",
    "CON.txt",
    "page.html",
    "script.js",
    "program.exe",
  ])
    assert.throws(() => validateDownloadArchive(archive(name)));
  assert.throws(
    () => validateDownloadArchive(archive("linked.py", 0xa0000000)),
    /Unsupported/,
  );
  assert.throws(() => validateDownloadArchive(Buffer.from("not an archive")));
  const mismatched = archive();
  mismatched.write("OTHER.txt", 30);
  assert.throws(() => validateDownloadArchive(mismatched), /Mismatched/);
});
test("safe content paths reject traversal, encoding, reserved Windows names and trailing segments", () => {
  for (const path of [
    "../x.zip",
    "folder/../x.zip",
    "folder/./x.zip",
    "folder//x.zip",
    "folder\\x.zip",
    "%2e%2e/x.zip",
    "file.zip.",
    "nul.zip",
    "C:/x.zip",
  ])
    assert.equal(safePath(path), false, path);
});
test("disk download validation verifies the declared archive checksum before publishing", async () => {
  const directory = await mkdtemp(join(tmpdir(), "spicybrain-download-"));
  try {
    const courses = await loadCourses(),
      bytes = archive();
    courses[0].downloads = [
      {
        id: "test-download",
        title: "Synthetic exercise",
        description: "Local files only.",
        path: "exercise.zip",
        mediaType: "application/zip",
        sha256: createHash("sha256").update(bytes).digest("hex"),
      },
    ];
    await mkdir(join(directory, "downloads"));
    await writeFile(join(directory, "downloads/exercise.zip"), bytes);
    assert.equal((await loadDownloads(courses, directory)).length, 1);
    await writeFile(
      join(directory, "downloads/exercise.zip"),
      archive("changed.md"),
    );
    await assert.rejects(loadDownloads(courses, directory), /checksum/);
    courses[0].downloads[0].path = "exercise.html";
    assert.throws(() => validateCourses(courses), /Unsafe download/);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
