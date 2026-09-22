import {
  createContext,
  useContext,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Asset, Course } from "./content-schema";
import { lessonHref, paths } from "./catalog";
import { pathForLesson } from "./paths";
import { StudyStore, exportText } from "./study";
export const store = new StudyStore();
const StoreContext = createContext(store);
export const StudyProvider = ({ children }: { children: ReactNode }) => (
  <StoreContext.Provider value={store}>{children}</StoreContext.Provider>
);
export function useStudy() {
  const s = useContext(StoreContext);
  return { ...useSyncExternalStore(s.subscribe, s.getSnapshot), store: s };
}
export const uuid = () => crypto.randomUUID();
export const baseAsset = (p: string) => `${import.meta.env.BASE_URL}${p}`;
export function download(name: string, text: string) {
  const url = URL.createObjectURL(
    new Blob([text], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function StudyDownload({
  name,
  children,
  className = "sc-btn sc-btn--secondary",
}: {
  name: string;
  children: ReactNode;
  className?: string;
}) {
  const { store } = useStudy();
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  return (
    <>
      <button
        className={className}
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          setError("");
          try {
            const data = await store
              .readLatest()
              .catch(() => store.getSnapshot().data);
            const raw = exportText(data);
            download(
              raw.startsWith('{"format":"SpicyBrain framed backup')
                ? name.replace(/\.json$/, ".jsonl")
                : name,
              raw,
            );
          } catch {
            setError(
              "The download could not be prepared. Keep this tab open and try again.",
            );
          } finally {
            setBusy(false);
          }
        }}
      >
        {children}
      </button>
      {error && <p role="alert">{error}</p>}
    </>
  );
}
export function MD({
  children,
  pathId,
  from,
}: {
  children: string;
  pathId?: string;
  from?: string;
}) {
  const contextualHref = (href: string | undefined) => {
    const target = /^#\/lesson\/([a-z0-9-]+)(?:\/([a-z0-9-]+))?$/.exec(
      href ?? "",
    );
    if (!target) return href;
    if (pathForLesson(paths, target[1], pathId))
      return lessonHref(target[1], target[2], pathId);
    if (
      from &&
      /^#\/(?:lesson|module)\/[a-z0-9-]+(?:\/[a-z0-9-]+)?(?:\?(?:path|view)=[a-z0-9-]+(?:&detour=1)?)?$/.test(
        from,
      )
    )
      return `${href}?from=${encodeURIComponent(from)}`;
    return href;
  };
  return (
    <Markdown
      remarkPlugins={[remarkGfm]}
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
      components={{
        a: ({ href, children }) => (
          <a
            href={contextualHref(href)}
            {...(href?.startsWith("https://")
              ? { target: "_blank", rel: "noopener noreferrer" }
              : {})}
          >
            {children}
          </a>
        ),
        table: ({ children }) => (
          <div
            className="sc-table-scroll"
            role="region"
            aria-label="Teaching table, scroll horizontally if needed"
            tabIndex={0}
          >
            <table className="sc-table">{children}</table>
          </div>
        ),
        pre: ({ children }) => (
          <pre
            tabIndex={0}
            aria-label="Illustrative code, scroll horizontally if needed"
          >
            {children}
          </pre>
        ),
      }}
    >
      {children}
    </Markdown>
  );
}
export function PageTitle({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <header className="sc-title">
      <p className="sc-eyebrow">{eyebrow}</p>
      <h1 tabIndex={-1}>{title}</h1>
      {children && <div className="sc-dek">{children}</div>}
    </header>
  );
}
export function SaveStatus() {
  const { status } = useStudy();
  return (
    <span className="save-status" role="status">
      {status === "saved"
        ? "Saved in this browser"
        : status === "saving"
          ? "Saving…"
          : status === "loading"
            ? "Opening study data…"
            : "Unsaved · keep this tab open"}
    </span>
  );
}
export function StorageNotice() {
  const { data, error, status, store } = useStudy();
  const [originalError, setOriginalError] = useState("");
  return (
    <>
      {error && (
        <aside className="sc-notice" role="alert">
          <p>{error}</p>
          <div className="actions">
            <StudyDownload name="SpicyBrain-recovery.json">
              Download recovery data
            </StudyDownload>
            {store.hasOriginalRecovery() && (
              <button
                className="sc-btn sc-btn--secondary"
                onClick={() => {
                  try {
                    const raw = store.exportOriginalRecovery();
                    if (raw)
                      download(
                        raw.startsWith('{"format":"SpicyBrain framed backup')
                          ? "SpicyBrain-original-saved.jsonl"
                          : "SpicyBrain-original-saved.json",
                        raw,
                      );
                  } catch {
                    setOriginalError(
                      "The original collection could not be encoded. Keep this tab and browser data intact for recovery.",
                    );
                  }
                }}
              >
                Download original saved collection
              </button>
            )}
            {originalError && <p role="alert">{originalError}</p>}
            <button
              className="sc-btn sc-btn--ghost"
              onClick={() => void store.change((s) => s)}
            >
              Retry saving
            </button>
          </div>
        </aside>
      )}
      {!data.disclosureAccepted && status !== "loading" && (
        <details
          className="sc-details storage-disclosure"
          open={[
            data.notes,
            data.drafts,
            data.attempts,
            data.completions,
            data.reviews,
            data.assessments,
          ].some((group) => Object.keys(group).length > 0)}
        >
          <summary>Your study data stays in this browser</summary>
          <p>
            No automatic cross-device sync. Clearing or evicting browser storage
            can erase notes and progress. Export/import is the manual backup and
            transfer path. This storage is not a secure vault; keep confidential
            material elsewhere.
          </p>
          <button
            className="sc-btn sc-btn--secondary"
            onClick={() =>
              void store.change((s) => ({ ...s, disclosureAccepted: true }))
            }
          >
            Got it
          </button>
        </details>
      )}
    </>
  );
}
export function Sources({
  course,
  claimIds,
}: {
  course: Course;
  claimIds: string[];
}) {
  const claims = course.claims.filter((c) => claimIds.includes(c.id));
  const ids = new Set(claims.flatMap((c) => c.sourceIds));
  return (
    <details className="sc-details section-sources">
      <summary>Sources & context</summary>
      {claims.map((c) => (
        <p key={c.id}>
          <strong>
            {c.kind === "documented"
              ? "Documented product fact"
              : c.kind === "fictional"
                ? "Fictional teaching example"
                : "SpicyBrain educational guidance"}
            .
          </strong>{" "}
          {c.description} <span className="sc-muted">{c.context}</span>
        </p>
      ))}
      {course.sources
        .filter((s) => ids.has(s.id))
        .map((s) => (
          <div className="source-record" key={s.id}>
            <a href={s.url} target="_blank" rel="noopener noreferrer">
              {s.title} ↗
            </a>
            <p>
              {s.publisher} · {s.type} · checked {s.accessDate}. Reviewed{" "}
              {s.reviewDate}.
            </p>
            <p>
              {s.context} {s.caveat}
            </p>
          </div>
        ))}
    </details>
  );
}
export function Diagram({ asset }: { asset: Asset }) {
  const dialog = useRef<HTMLDialogElement>(null),
    trigger = useRef<HTMLButtonElement>(null);
  const [zoom, setZoom] = useState(1),
    [failed, setFailed] = useState(false);
  const img = (modal = false) =>
    failed ? (
      <p className="sc-notice">
        The diagram could not load. Its complete text equivalent is below.
      </p>
    ) : (
      <img
        src={baseAsset(`content-assets/${asset.path}`)}
        alt={asset.alt}
        onError={() => setFailed(true)}
        style={
          modal ? { width: `${zoom * 100}%`, maxWidth: "none" } : undefined
        }
      />
    );
  return (
    <figure className="teaching-figure">
      <div className="diagram-frame">{img()}</div>
      <figcaption>{asset.caption}</figcaption>
      <button
        ref={trigger}
        className="sc-btn sc-btn--secondary"
        onClick={() => {
          setZoom(1);
          dialog.current?.showModal();
        }}
      >
        Open diagram
      </button>
      <details className="sc-details">
        <summary>Read the text equivalent</summary>
        <p>{asset.textEquivalent}</p>
        <p className="sc-muted">{asset.provenance}</p>
      </details>
      <dialog
        ref={dialog}
        aria-label={asset.caption}
        onClose={() => trigger.current?.focus()}
      >
        <div className="dialog-toolbar">
          <strong>Teaching diagram</strong>
          <div className="actions">
            <button
              className="sc-btn sc-btn--secondary"
              onClick={() => setZoom((v) => Math.min(3, v + 0.5))}
              disabled={zoom === 3}
            >
              Zoom in
            </button>
            <button
              className="sc-btn sc-btn--secondary"
              onClick={() => setZoom((v) => Math.max(1, v - 0.5))}
              disabled={zoom === 1}
            >
              Zoom out
            </button>
            <button
              className="sc-btn sc-btn--secondary"
              onClick={() => setZoom(1)}
            >
              Reset zoom
            </button>
            <button
              className="sc-btn sc-btn--primary"
              onClick={() => dialog.current?.close()}
            >
              Close diagram
            </button>
          </div>
        </div>
        <div
          className="diagram-scroll"
          role="region"
          aria-label="Zoomed diagram; scroll to pan"
          tabIndex={0}
        >
          {img(true)}
        </div>
        <p>{asset.textEquivalent}</p>
      </dialog>
    </figure>
  );
}
