import { useState } from "react";
import {
  courses,
  findLesson,
  knownIds,
  lessonHref,
  publicIndex,
  scenarios,
} from "./catalog";
import { NoteEditor } from "./reader";
import {
  emptyState,
  exportText,
  importPreview,
  nowISO,
  parseImport,
  type StudyState,
} from "./study";
import { PageTitle, SaveStatus, download, useStudy } from "./ui";

export function Search() {
  const { data } = useStudy(),
    [query, setQuery] = useState("");
  const q = query.trim().toLocaleLowerCase();
  const index = [
    ...publicIndex,
    ...Object.values(data.notes).map((n) => ({
      id: n.id,
      type: "Personal note",
      courseId: n.courseId,
      title: findLesson(n.lessonId)?.lesson.title ?? "Note for removed content",
      text: n.text,
      href: `#/notebook/${n.id}`,
    })),
  ];
  const results = q
    ? index.filter((x) => x.text.toLocaleLowerCase().includes(q)).slice(0, 80)
    : [];
  return (
    <>
      <PageTitle eyebrow="find the connection" title="Search your learning">
        <p>
          Lessons, glossary aliases, and your local notes. Your search stays on
          this device.
        </p>
      </PageTitle>
      <label className="sc-field search-field">
        Search courses, concepts, or notes
        <input
          className="sc-input"
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Try CDC, rollback, or a phrase from your notes"
        />
      </label>
      {q ? (
        <>
          <p role="status">
            {results.length === 80
              ? "Showing up to 80 matching results. Narrow your search for more."
              : `${results.length} results`}
          </p>
          {!results.length && (
            <p className="sc-empty">
              No results for that phrase. Try a shorter term or a glossary
              alias.
            </p>
          )}
          <div className="search-results">
            {results.map((r) => (
              <a
                key={`${r.type}-${r.id}`}
                href={r.href}
                className="search-result"
              >
                <span className="sc-eyebrow">
                  {r.type} ·{" "}
                  {courses.find((c) => c.id === r.courseId)?.title ??
                    "Unavailable course"}
                </span>
                <h2>{r.title}</h2>
                <p>
                  {r.text
                    .replace(/[#*`]/g, "")
                    .slice(
                      Math.max(0, r.text.toLocaleLowerCase().indexOf(q) - 55),
                      Math.max(0, r.text.toLocaleLowerCase().indexOf(q) - 55) +
                        200,
                    )}
                  …
                </p>
              </a>
            ))}
          </div>
        </>
      ) : (
        <div className="sc-empty">
          Start with a concept, question, or phrase you want to find.
        </div>
      )}
    </>
  );
}
export function Notebook({ id }: { id?: string }) {
  const { data, store } = useStudy(),
    [query, setQuery] = useState(""),
    [unresolved, setUnresolved] = useState(false);
  const notes = Object.values(data.notes)
    .filter(
      (n) =>
        (!id || n.id === id) &&
        (!unresolved || n.question) &&
        n.text.toLowerCase().includes(query.toLowerCase()),
    )
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  const bookmarks = Object.values(data.bookmarks).filter((b) => b.active);
  const drafts = Object.values(data.drafts).filter(
    (d) => d.text && d.text.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <>
      <PageTitle eyebrow="keep what clicks" title="Your notebook">
        <p>
          Notes, open questions, saved sections, and practice drafts. All linked
          to where you learned them.
        </p>
      </PageTitle>
      {id && (
        <p>
          <a href="#/notebook">Show all notes</a>
        </p>
      )}
      <div className="notebook-filters">
        <label className="sc-field">
          Search this notebook
          <input
            className="sc-input"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <label className="sc-check">
          <input
            type="checkbox"
            checked={unresolved}
            onChange={(e) => setUnresolved(e.target.checked)}
          />
          Unresolved questions only
        </label>
      </div>
      <h2>Lesson notes</h2>
      {!notes.length && (
        <p className="sc-empty">
          {query || unresolved || id
            ? "No matching notes."
            : "No notes yet. Open a lesson and capture one idea or question."}
        </p>
      )}
      <div className="notes-list">
        {notes.map((n) => {
          const entry = findLesson(n.lessonId),
            section = entry?.lesson.sections.find((s) => s.id === n.sectionId);
          return (
            <section className="sc-card" id={n.id} key={n.id}>
              <p className="sc-eyebrow">
                {courses.find((c) => c.id === n.courseId)?.title ??
                  "Removed course"}
                {n.id.includes("-conflict-")
                  ? " · preserved import conflict"
                  : ""}
              </p>
              <h3>
                {entry?.lesson.title ?? "Removed lesson · note preserved"}
              </h3>
              <p>{section?.title ?? "The original section is unavailable."}</p>
              <NoteEditor
                courseId={n.courseId}
                lessonId={n.lessonId}
                sectionId={n.sectionId}
                noteId={n.id}
              />
              <a href={lessonHref(n.lessonId, n.sectionId)}>
                Return to source →
              </a>
            </section>
          );
        })}
      </div>
      {!id && (
        <>
          <h2>Bookmarked sections</h2>
          {!bookmarks.length ? (
            <p className="sc-empty">No bookmarks yet.</p>
          ) : (
            <ul className="bookmark-list">
              {bookmarks.map((b) => (
                <li key={b.id}>
                  <a href={lessonHref(b.lessonId, b.sectionId)}>
                    {findLesson(b.lessonId)?.lesson.title ??
                      "Removed lesson · bookmark preserved"}{" "}
                    ·{" "}
                    {findLesson(b.lessonId)?.lesson.sections.find(
                      (s) => s.id === b.sectionId,
                    )?.title ?? b.sectionId}
                  </a>
                </li>
              ))}
            </ul>
          )}
          <h2>Practice drafts</h2>
          {!drafts.length ? (
            <p className="sc-empty">No practice drafts yet.</p>
          ) : (
            drafts.map((d) => {
              const s = scenarios.find((s) => s.scenario.id === d.targetId),
                entry = courses
                  .flatMap((c) => c.modules.flatMap((m) => m.lessons))
                  .find((l) => l.sections.some((s) => s.id === d.targetId));
              return (
                <details key={d.id} className="sc-details draft-details">
                  <summary>
                    {s?.scenario.title ??
                      entry?.title ??
                      "Removed content · draft preserved"}
                    {d.id.includes("-conflict-") ? " · import conflict" : ""}
                  </summary>
                  <label className="sc-field">
                    Practice draft
                    <textarea
                      maxLength={100000}
                      className="sc-input"
                      rows={8}
                      value={d.text}
                      onChange={(e) => {
                        const text = e.target.value,
                          updatedAt = nowISO();
                        void store.change((state) => ({
                          ...state,
                          drafts: {
                            ...state.drafts,
                            [d.id]: { ...d, text, updatedAt },
                          },
                        }));
                      }}
                    />
                  </label>
                  <SaveStatus />
                  {s ? (
                    <a href={`#/practice/${d.targetId}`}>
                      Return to practice →
                    </a>
                  ) : entry ? (
                    <a href={lessonHref(entry.id, d.targetId)}>
                      Return to lesson →
                    </a>
                  ) : (
                    <p>
                      Original content is unavailable. Your text remains
                      editable and exportable.
                    </p>
                  )}
                </details>
              );
            })
          )}
        </>
      )}
    </>
  );
}
export function Settings() {
  const { data, store } = useStudy();
  const [incoming, setIncoming] = useState<StudyState | null>(null),
    [mode, setMode] = useState<"merge" | "replace">("merge"),
    [confirm, setConfirm] = useState(false),
    [reset, setReset] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  const preview = incoming ? importPreview(data, incoming, knownIds) : null;
  const pref = (patch: Partial<StudyState["settings"]>) => {
    const updatedAt = nowISO();
    void store.change((s) => ({
      ...s,
      settings: { ...s.settings, ...patch, updatedAt },
    }));
  };
  const loadFile = async (file?: File) => {
    setIncoming(null);
    setConfirm(false);
    if (!file) return;
    try {
      if (file.size > 5_000_000) throw Error("Import exceeds the 5 MB limit.");
      setIncoming(parseImport(await file.text()));
      setMessage("Import validated. Review the preview before applying.");
    } catch {
      setMessage(
        "This file is invalid, too large, or from an unsupported future version. No data changed.",
      );
    }
  };
  return (
    <>
      <PageTitle eyebrow="make it yours" title="Settings & study data" />
      <div className="settings-grid">
        <section className="sc-card">
          <h2>Reading preferences</h2>
          <label className="sc-field">
            Theme
            <select
              className="sc-select"
              value={data.settings.theme}
              onChange={(e) =>
                pref({ theme: e.target.value as "auto" | "dark" | "light" })
              }
            >
              <option value="auto">Auto · follow device</option>
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </select>
          </label>
          <label className="sc-check">
            <input
              type="checkbox"
              checked={data.settings.focus}
              onChange={(e) => pref({ focus: e.target.checked })}
            />
            Start lessons in focus mode
          </label>
          <label className="sc-field">
            Cards per review session
            <select
              className="sc-select"
              value={data.settings.sessionSize}
              onChange={(e) => pref({ sessionSize: Number(e.target.value) })}
            >
              {[1, 5, 10, 15, 20, 30].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
          <label className="sc-field">
            New cards per introduction
            <select
              className="sc-select"
              value={data.settings.newLimit}
              onChange={(e) => pref({ newLimit: Number(e.target.value) })}
            >
              {[1, 2, 3, 5, 10].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
          <SaveStatus />
        </section>
        <section className="sc-card">
          <h2>Only in this browser</h2>
          <p>
            Notes, drafts, completions, quiz attempts, reviews, bookmarks, and
            preferences stay in this browser and site origin. They do not
            automatically sync across devices.
          </p>
          <p>
            Clearing or evicting browser storage can erase them. IndexedDB is
            not a secure vault. Do not save confidential customer or employer
            material here.
          </p>
          <p>
            Export is a manual download; it is not cloud sync. Moving to another
            domain or browser requires export/import.
          </p>
          <button
            className="sc-btn sc-btn--primary"
            onClick={() => {
              download("SpicyBrain-study-data.json", exportText(data));
              setMessage(
                "Export download requested. Keep the file somewhere you can find it. Browser save status is separate.",
              );
            }}
          >
            Export all study data
          </button>
          <p className="sc-hint">
            The file contains personal study text. Share it only when you intend
            to.
          </p>
        </section>
      </div>
      <section className="sc-card import-panel">
        <h2>Import a backup</h2>
        <p>
          All records are checked before anything is written. Unknown content
          stays recoverable.
        </p>
        <label className="sc-field">
          Study data file (.json, up to 5 MB)
          <input
            className="sc-input"
            type="file"
            accept=".json,application/json"
            onChange={(e) => void loadFile(e.target.files?.[0])}
          />
        </label>
        {preview && incoming && (
          <div className="import-preview">
            <h3>Import preview</h3>
            <div className="sc-table-scroll">
              <table className="sc-table">
                <thead>
                  <tr>
                    <th>Record type</th>
                    <th>Incoming</th>
                    <th>Current</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(preview.counts).map(([k, n]) => (
                    <tr key={k}>
                      <th>{k}</th>
                      <td>{n}</td>
                      <td>
                        {
                          Object.keys(data[k as keyof StudyState] as object)
                            .length
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p>
              {preview.conflicts} conflicting note/draft texts. Merge preserves
              both texts.
            </p>
            <p>
              {preview.unknown.length} unknown content references. These records
              remain available in Notebook and exports.
            </p>
            {preview.unknown.length > 0 && (
              <details>
                <summary>Unknown references</summary>
                <ul>
                  {preview.unknown.map((id) => (
                    <li key={id}>{id}</li>
                  ))}
                </ul>
              </details>
            )}
            <label className="sc-field">
              Import method
              <select
                className="sc-select"
                value={mode}
                onChange={(e) => {
                  setMode(e.target.value as "merge" | "replace");
                  setConfirm(false);
                }}
              >
                <option value="merge">Merge · keep and combine</option>
                <option value="replace">
                  Replace · overwrite current study data
                </option>
              </select>
            </label>
            <p>
              Merge deduplicates identical events. The later timestamp wins for
              settings and mutable records; an exact tie uses stable serialized
              order. Conflicting note and draft text is preserved as another
              entry. Schedules follow the most recent immutable review.
            </p>
            {mode === "replace" && (
              <div className="sc-notice">
                <p>
                  Replace removes all current study records and preferences, and
                  uses this file instead. Export your current data first if you
                  want to retain it.
                </p>
                <button
                  className="sc-btn sc-btn--secondary"
                  onClick={() =>
                    download("SpicyBrain-before-replace.json", exportText(data))
                  }
                >
                  Export current data first
                </button>
                <label className="sc-check">
                  <input
                    type="checkbox"
                    checked={confirm}
                    onChange={(e) => setConfirm(e.target.checked)}
                  />
                  I understand that replacement removes my current study data.
                </label>
              </div>
            )}
            <div className="actions">
              <button
                className="sc-btn sc-btn--primary"
                disabled={busy || (mode === "replace" && !confirm)}
                onClick={async () => {
                  setBusy(true);
                  try {
                    await store.import(incoming, mode);
                    setIncoming(null);
                    setConfirm(false);
                    setMessage(
                      "Import committed. All study records were saved in one transaction.",
                    );
                  } catch {
                    setMessage(
                      "Import could not be committed, or immutable events conflict. Existing data was not changed. Export both copies before resolving conflicting events.",
                    );
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                {mode === "merge" ? "Merge import" : "Confirm replacement"}
              </button>
              <button
                className="sc-btn sc-btn--secondary"
                onClick={() => {
                  setIncoming(null);
                  setMessage("Import cancelled. No data changed.");
                }}
              >
                Cancel import
              </button>
            </div>
          </div>
        )}
        <p role="status">{message}</p>
      </section>
      <details className="sc-details reset-panel">
        <summary>Reset study data</summary>
        <p>
          Reset removes all local notes, attempts, reviews, drafts, and
          preferences. Export before continuing if you want a backup.
        </p>
        <button
          className="sc-btn sc-btn--secondary"
          onClick={() =>
            download("SpicyBrain-before-reset.json", exportText(data))
          }
        >
          Export before reset
        </button>
        <label className="sc-field">
          Type RESET to confirm
          <input
            className="sc-input"
            value={reset}
            onChange={(e) => setReset(e.target.value)}
            autoComplete="off"
          />
        </label>
        <button
          className="sc-btn sc-btn--secondary"
          disabled={reset !== "RESET" || busy}
          onClick={async () => {
            setBusy(true);
            try {
              await store.replace(emptyState(nowISO()));
              setReset("");
              setMessage("Study data reset in this browser.");
            } catch {
              setMessage("Reset failed. Existing data was preserved.");
            } finally {
              setBusy(false);
            }
          }}
        >
          Permanently reset local study data
        </button>
      </details>
    </>
  );
}
