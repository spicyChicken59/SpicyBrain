// Prints raw and gzip sizes of the built initial assets and the lazy teaching
// files as JSON. Usage: node scripts/measure-bundle.mjs [dist-directory]
// gzip sizes use zlib level 9; hosts compress differently, so compare runs of
// this script with each other rather than with a server's transfer size.
import process from "node:process";
import console from "node:console";
import { readdir, readFile } from "node:fs/promises";
import { join } from "node:path";
import { gzipSync } from "node:zlib";

const dist = process.argv[2] ?? "dist";
const gzip = (bytes) => gzipSync(bytes, { level: 9 }).length;
async function files(directory, pattern) {
  let names = [];
  try {
    names = (await readdir(directory)).filter((name) => pattern.test(name));
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
  const out = [];
  for (const name of names.sort()) {
    const bytes = await readFile(join(directory, name));
    out.push({ file: name, raw: bytes.length, gzip: gzip(bytes) });
  }
  return out;
}
const total = (list) => ({
  files: list.length,
  raw: list.reduce((n, f) => n + f.raw, 0),
  gzip: list.reduce((n, f) => n + f.gzip, 0),
});
const assets = await files(join(dist, "assets"), /\.(?:js|css)$/);
const modules = await files(
  "public/teaching",
  /^(?!search\.json$|media\.json$).*\.json$/,
);
const bodies = await files("public/teaching/bodies", /\.json$/);
const search = await files("public/teaching", /^search\.json$/);
const media = await files("public/teaching", /^media\.json$/);
const generated = await files("src/generated", /\.json$/);
console.log(
  JSON.stringify(
    {
      dist,
      assets,
      initial: {
        js: total(assets.filter((f) => f.file.endsWith(".js"))),
        css: total(assets.filter((f) => f.file.endsWith(".css"))),
      },
      generated,
      publicTeaching: {
        modules: total(modules),
        bodies: total(bodies),
        search: total(search),
        media: total(media),
        total: total([...modules, ...bodies, ...search, ...media]),
      },
    },
    null,
    2,
  ),
);
