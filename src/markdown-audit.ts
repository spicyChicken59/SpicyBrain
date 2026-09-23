import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkGfm from "remark-gfm";

/**
 * Reads authored Markdown the way the app renders it: the same parser and
 * GFM extension as react-markdown in `MD` (`src/ui.tsx`), so a build check
 * sees exactly the links and elements a reader would. Used at build time by
 * `validateCourses`; nothing here runs while a page is shown.
 */

/** The mdast fields the audit reads. */
type MarkdownNode = {
  type: string;
  depth?: number;
  url?: string;
  value?: string;
  children?: MarkdownNode[];
  position?: { start: { line: number } };
};
export type MarkdownLink = {
  url: string;
  line?: number;
  /** A bare URL, address or `<autolink>`: its text is its destination. */
  literal: boolean;
};
export type MarkdownAudit = {
  /**
   * Every destination a reader could follow: inline links, reference-style
   * definitions, `<autolinks>` and GFM literals (bare `https://…`, `www.…`
   * and e-mail addresses). Links inside code are text, not links.
   */
  links: MarkdownLink[];
  /**
   * Constructs the renderer's element whitelist removes together with their
   * text: headings other than h3/h4, images and footnotes.
   */
  dropped: { what: string; reason: string; line?: number }[];
};

let parser: ReturnType<typeof createParser> | undefined;
function createParser() {
  return unified().use(remarkParse).use(remarkGfm);
}
const text = (node: MarkdownNode): string =>
  node.value ?? (node.children ?? []).map(text).join("");
/**
 * Parsing is the cost of a check (about 0.6 ms a body), and tests validate
 * clones of the same catalog many times, so results are kept per text.
 */
const cache = new Map<string, Readonly<MarkdownAudit>>();

export function auditMarkdown(markdown: string): Readonly<MarkdownAudit> {
  const cached = cache.get(markdown);
  if (cached) return cached;
  parser ??= createParser();
  const audit: MarkdownAudit = { links: [], dropped: [] };
  const visit = (node: MarkdownNode) => {
    const line = node.position?.start.line;
    if (node.type === "link" || node.type === "definition") {
      const url = node.url ?? "",
        shown = node.type === "link" ? text(node) : undefined;
      audit.links.push({
        url,
        line,
        literal:
          shown !== undefined &&
          [shown, `mailto:${shown}`, `http://${shown}`].includes(url),
      });
    } else if (node.type === "heading" && node.depth !== 3 && node.depth !== 4)
      audit.dropped.push({
        what: `heading (h${node.depth})`,
        reason:
          "only ### and #### headings are shown; the page supplies h1 and h2, so start at ###",
        line,
      });
    else if (node.type === "image" || node.type === "imageReference")
      audit.dropped.push({
        what: "image",
        reason: "Markdown images are not shown; declare an asset instead",
        line,
      });
    else if (
      node.type === "footnoteReference" ||
      node.type === "footnoteDefinition"
    )
      audit.dropped.push({
        what: "footnote",
        reason: "footnotes are not shown",
        line,
      });
    for (const child of node.children ?? []) visit(child);
  };
  visit(parser.parse(markdown) as unknown as MarkdownNode);
  if (cache.size >= 20000) cache.clear();
  cache.set(markdown, audit);
  return audit;
}
