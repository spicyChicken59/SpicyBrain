import {
  useEffect,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import Markdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import type { CatalogCourse } from "./catalog-types";
import type {
  TeachingModule,
  TeachingConcept,
  TeachingVisual,
} from "./teaching-schema";

type TextNode = {
  type: string;
  value?: string;
  url?: string;
  children?: TextNode[];
};
// Only authored explicit concept tokens become controls. Code stays literal.
function conceptsRemark() {
  return (tree: TextNode) => {
    const walk = (node: TextNode) => {
      if (!node.children || ["code", "inlineCode", "link"].includes(node.type))
        return;
      node.children = node.children.flatMap((child) => {
        if (child.type !== "text") {
          walk(child);
          return [child];
        }
        const value = child.value ?? "",
          result: TextNode[] = [];
        let last = 0;
        for (const match of value.matchAll(
          /\[\[([a-z][a-z0-9-]+)\|([^\]]+)\]\]/g,
        )) {
          if (match.index! > last)
            result.push({
              type: "text",
              value: value.slice(last, match.index),
            });
          result.push({
            type: "link",
            url: `#concept/${match[1]}`,
            children: [{ type: "text", value: match[2] }],
          });
          last = match.index! + match[0].length;
        }
        if (last < value.length)
          result.push({ type: "text", value: value.slice(last) });
        return result.length ? result : [child];
      });
    };
    walk(tree);
  };
}
export function Concept({
  concept,
  label,
}: {
  concept: TeachingConcept;
  label: React.ReactNode;
}) {
  const [open, setOpen] = useState(false),
    [pos, setPos] = useState({ left: 12, top: 12 });
  const root = useRef<HTMLSpanElement>(null),
    trigger = useRef<HTMLButtonElement>(null),
    popup = useRef<HTMLSpanElement>(null),
    timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined),
    suppressed = useRef(false),
    id = useId();
  const show = () => {
    if (suppressed.current) return;
    clearTimeout(timer.current);
    const r = trigger.current?.getBoundingClientRect();
    if (r)
      setPos({
        left: Math.max(
          12,
          Math.min(
            r.left,
            window.innerWidth - Math.min(360, window.innerWidth - 24) - 12,
          ),
        ),
        top: Math.max(12, Math.min(r.bottom + 6, window.innerHeight - 280)),
      });
    setOpen(true);
  };
  const close = () => {
    suppressed.current = true;
    setOpen(false);
  };
  useLayoutEffect(() => {
    if (!open) return;
    const place = () => {
      const r = trigger.current?.getBoundingClientRect(),
        p = popup.current?.getBoundingClientRect();
      if (!r || !p) return;
      const available = innerHeight - 24,
        preferred =
          r.bottom + 8 + p.height <= innerHeight - 12
            ? r.bottom + 8
            : r.top - p.height - 8;
      setPos({
        left: Math.max(12, Math.min(r.left, innerWidth - p.width - 12)),
        top: Math.max(
          12,
          Math.min(preferred, innerHeight - Math.min(available, p.height) - 12),
        ),
      });
    };
    place();
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => {
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
    };
  }, [open]);
  useEffect(() => {
    if (!open) return;
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        close();
        trigger.current?.focus();
      }
    };
    const outside = (e: PointerEvent) => {
      if (!root.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("keydown", key);
    document.addEventListener("pointerdown", outside);
    return () => {
      document.removeEventListener("keydown", key);
      document.removeEventListener("pointerdown", outside);
    };
  }, [open]);
  useEffect(() => () => clearTimeout(timer.current), []);
  return (
    <span
      ref={root}
      className="concept-wrap"
      onMouseEnter={show}
      onMouseLeave={() => {
        suppressed.current = false;
        timer.current = setTimeout(() => {
          if (!root.current?.contains(document.activeElement)) setOpen(false);
        }, 180);
      }}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) {
          suppressed.current = false;
          setOpen(false);
        }
      }}
    >
      <button
        ref={trigger}
        type="button"
        className="concept-term"
        aria-expanded={open}
        aria-controls={open ? id : undefined}
        onFocus={show}
        onClick={() => {
          suppressed.current = false;
          show();
        }}
      >
        {label}
      </button>
      {open && (
        <span
          ref={popup}
          id={id}
          role="dialog"
          aria-label={`${concept.term} definition`}
          className="concept-popover"
          style={pos}
        >
          <strong>{concept.term}</strong>
          <span>{concept.definition}</span>
          <span className="concept-example">{concept.example}</span>
          <button
            className="sc-btn sc-btn--ghost"
            onClick={() => {
              close();
              trigger.current?.focus();
            }}
          >
            Close definition
          </button>
        </span>
      )}
    </span>
  );
}
/**
 * A focusable, labelled table region that shows a written "More columns"
 * hint whenever its table is wider than the region. Teaching tables and the
 * course crosswalk share it.
 */
export function ScrollableTable({
  children,
  label,
  className = "teaching-table",
}: {
  children: React.ReactNode;
  label: string;
  className?: string;
}) {
  const region = useRef<HTMLDivElement>(null),
    [overflow, setOverflow] = useState(false);
  useLayoutEffect(() => {
    const node = region.current;
    if (!node) return;
    const measure = () => setOverflow(node.scrollWidth > node.clientWidth + 1);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(node);
    if (node.firstElementChild) observer.observe(node.firstElementChild);
    return () => observer.disconnect();
  }, [children]);
  return (
    <div className="teaching-table-wrap">
      {overflow && (
        <p className="table-scroll-hint">
          More columns → Scroll sideways, or focus the table and use arrow keys.
        </p>
      )}
      <div
        ref={region}
        className={className}
        role="region"
        aria-label={label}
        tabIndex={0}
      >
        {children}
      </div>
    </div>
  );
}
export function TeachingText({
  children,
  module,
  course,
}: {
  children: string;
  module: TeachingModule;
  course: CatalogCourse;
}) {
  const concepts = useMemo(
    () => [
      ...module.concepts,
      ...course.concepts.map((c) => ({
        ...c,
        example: "Use the linked concept in its lesson context.",
        sourceIds: [],
      })),
    ],
    [module, course],
  );
  const components = useMemo<Components>(
    () => ({
      a: ({ href, children }) => {
        const id = href?.startsWith("#concept/") ? href.slice(9) : undefined,
          c = concepts.find((c) => c.id === id);
        return c ? (
          <Concept concept={c} label={children} />
        ) : (
          <a
            href={href}
            {...(href?.startsWith("https://")
              ? { target: "_blank", rel: "noopener noreferrer" }
              : {})}
          >
            {children}
          </a>
        );
      },
      table: ({ children }) => (
        <ScrollableTable label="Teaching table">
          <table>{children}</table>
        </ScrollableTable>
      ),
      pre: ({ children }) => (
        <pre
          tabIndex={0}
          aria-label="Illustrative code; scroll horizontally if needed"
        >
          {children}
        </pre>
      ),
    }),
    [concepts],
  );
  return (
    <Markdown
      remarkPlugins={[remarkGfm, conceptsRemark]}
      skipHtml
      allowedElements={[
        "p",
        "strong",
        "em",
        "del",
        "blockquote",
        "ul",
        "ol",
        "li",
        "code",
        "pre",
        "a",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "h3",
        "h4",
        "hr",
        "br",
      ]}
      components={components}
    >
      {children}
    </Markdown>
  );
}
export function Visual({
  visual,
  stateId,
  onState,
}: {
  visual: TeachingVisual;
  stateId?: string;
  onState?: (id: string) => void;
}) {
  const [local, setLocal] = useState(visual.states[0].id),
    dialog = useRef<HTMLDialogElement>(null),
    zoomButton = useRef<HTMLButtonElement>(null);
  const selected =
      visual.states.find((s) => s.id === (stateId ?? local)) ??
      visual.states[0],
    uid = useId();
  const choose = (id: string) => {
    setLocal(id);
    onState?.(id);
  };
  const scene = (zoom = false) => (
    <>
      {visual.states.length > 1 && (
        <div
          className="visual-stages"
          role="group"
          aria-label={`${visual.title} stages`}
        >
          {visual.states.map((s, i) => (
            <button
              key={s.id}
              className="stage-button"
              aria-pressed={s.id === selected.id}
              onClick={() => choose(s.id)}
            >
              <span>{i + 1}</span>
              {s.title}
            </button>
          ))}
        </div>
      )}
      <div
        className={`visual-scene visual-kind-${visual.kind}`}
        role="group"
        aria-label={visual.alt}
      >
        <div
          className="visual-stage-description"
          aria-live={zoom ? "off" : "polite"}
        >
          <strong>{selected.title}</strong>
          <p>{selected.explanation}</p>
        </div>
        {selected.equation && (
          <div className="visual-equation" role="math">
            {selected.equation}
          </div>
        )}
        {!!selected.nodes.length && (
          <ul className="visual-nodes">
            {selected.nodes.map((n) => (
              <li key={n.id} className={`visual-node node-${n.status}`}>
                <span className="node-status">
                  {n.status === "excluded"
                    ? "Excluded from this result"
                    : n.status === "selected"
                      ? "In this result"
                      : n.status === "pending"
                        ? "Pending"
                        : n.status === "warning"
                          ? "Check this"
                          : "Context"}
                </span>
                <strong>{n.label}</strong>
                {n.value && <span className="node-value">{n.value}</span>}
                <p>{n.detail}</p>
              </li>
            ))}
          </ul>
        )}
        {!!selected.connections.length && (
          <ol className="visual-connections" aria-label="Relationships">
            {selected.connections.map((e, i) => (
              <li key={i}>
                <strong>
                  {selected.nodes.find((n) => n.id === e.from)?.label}
                </strong>
                <span aria-hidden="true"> → </span>
                <span className="sc-sr-only"> leads to </span>
                <strong>
                  {selected.nodes.find((n) => n.id === e.to)?.label}
                </strong>
                <span>{e.label}</span>
              </li>
            ))}
          </ol>
        )}
        {selected.table && (
          <ScrollableTable label={`${visual.title} data table`}>
            <table>
              <thead>
                <tr>
                  {selected.table.columns.map((c, i) => (
                    <th scope="col" key={i}>
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {selected.table.rows.map((r, i) => (
                  <tr key={i}>
                    {r.map((v, j) => (
                      <td key={j}>{v}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </ScrollableTable>
        )}
      </div>
    </>
  );
  return (
    <figure className="teaching-visual">
      <div className="visual-heading">
        <figcaption id={uid}>{visual.title}</figcaption>
        <button
          ref={zoomButton}
          className="sc-btn sc-btn--ghost visual-zoom"
          onClick={() => dialog.current?.showModal()}
        >
          Enlarge visual
        </button>
      </div>
      {scene()}
      <p className="visual-caption">{visual.caption}</p>
      <details className="visual-equivalent">
        <summary>Text equivalent and credit</summary>
        <p>{visual.textEquivalent}</p>
        <p>{visual.provenance}</p>
      </details>
      <dialog
        className="visual-dialog"
        ref={dialog}
        aria-label={`${visual.title}, enlarged`}
        onClose={() => zoomButton.current?.focus()}
      >
        <div className="visual-heading">
          <h2>{visual.title}</h2>
          <button
            className="sc-btn sc-btn--secondary"
            onClick={() => dialog.current?.close()}
          >
            Close enlarged visual
          </button>
        </div>
        {scene(true)}
        <p>{visual.caption}</p>
      </dialog>
    </figure>
  );
}
export function TeachingSources({
  module,
  course,
  claimIds,
}: {
  module: TeachingModule;
  course: CatalogCourse;
  claimIds: string[];
}) {
  const claims = [...module.claims, ...course.claims].filter((c) =>
    claimIds.includes(c.id),
  );
  return (
    <details className="teaching-sources">
      <summary>Sources, context and limits</summary>
      {claims.map((c) => (
        <div key={c.id}>
          <p>
            <strong>{"kind" in c ? c.kind : "documented"}</strong> ·{" "}
            {c.description}
          </p>
          {"context" in c && <p>{c.context}</p>}
          <ul>
            {c.sourceIds.map((id) => {
              const s = [...module.sources, ...course.sources].find(
                (s) => s.id === id,
              );
              return s ? (
                <li key={id}>
                  <a href={s.url} target="_blank" rel="noopener noreferrer">
                    {s.title}
                  </a>{" "}
                  · {s.publisher} · reviewed{" "}
                  {"reviewedAt" in s ? s.reviewedAt : s.reviewDate}
                  <p>
                    {s.context} {s.caveat}
                  </p>
                </li>
              ) : null;
            })}
          </ul>
        </div>
      ))}
    </details>
  );
}
