import process from "node:process";
import { readFile, readdir, mkdir } from "node:fs/promises";
import { chromium } from "playwright";
const browser = await chromium.launch({
  executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});
const page = await browser.newPage({ viewport: { width: 1680, height: 3300 } });
const names = (await readdir("content/assets"))
  .filter((n) => n.endsWith(".svg"))
  .sort();
let html =
  "<style>body{margin:20px;background:#eee;display:grid;grid-template-columns:800px 800px;gap:24px;font:16px sans-serif}figure{margin:0}svg{width:800px;max-height:480px}figcaption{height:25px}</style>";
for (const n of names)
  html += `<figure><figcaption>${n}</figcaption>${await readFile("content/assets/" + n, "utf8")}</figure>`;
await page.setContent(html);
await mkdir("docs/evidence", { recursive: true });
await page.screenshot({
  path: "docs/evidence/diagram-contact-sheet.png",
  fullPage: true,
});
await browser.close();
