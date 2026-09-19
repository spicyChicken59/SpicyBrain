import process from "node:process";
import { URL } from "node:url";
// Loopback-only production static server. No SPA rewrite or deployment.
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { resolve, extname } from "node:path";
const mime = {
  ".html": "text/html",
  ".js": "application/javascript",
  ".css": "text/css",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
  ".json": "application/json",
};
createServer(async (req, res) => {
  try {
    const path = decodeURIComponent(new URL(req.url, "http://local").pathname),
      nested = path.startsWith("/SpicyBrain/");
    const root = resolve(nested ? "dist-nested" : "dist"),
      file = resolve(
        root,
        "." +
          (nested ? path.slice("/SpicyBrain".length) : path) +
          (path.endsWith("/") ? "index.html" : ""),
      );
    if (!file.startsWith(root + "/")) throw Error("Outside root");
    res.setHeader(
      "Content-Type",
      mime[extname(file)] || "application/octet-stream",
    );
    res.setHeader("Cache-Control", "no-store");
    res.end(await readFile(file));
  } catch {
    res.statusCode = 404;
    res.end("Not found");
  }
}).listen(Number(process.env.PORT || 4183), "127.0.0.1");
