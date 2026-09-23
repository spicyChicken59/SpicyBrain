import { useEffect, useRef, useState } from "react";
import {
  cardIndex,
  courses,
  findLesson,
  lessonEntries,
  lessonHref,
  loadLessonBody,
  paths,
  teachingIndex,
  beatHref,
} from "./catalog";
import { pathForLesson, pathNeighbors } from "./paths";
import type { Question } from "./content-schema";
import type {
  CatalogCourse,
  CatalogLesson,
  CatalogSection,
  LessonBody,
} from "./catalog-types";
import { nowISO } from "./study";
import {
  Diagram,
  MD,
  PageTitle,
  SaveStatus,
  Sources,
  useStudy,
  uuid,
  baseAsset,
} from "./ui";

export function NoteEditor({
  courseId,
  lessonId,
  sectionId,
  noteId,
  label = "Your lesson note",
}: {
  courseId: string;
  lessonId: string;
  sectionId: string;
  noteId?: string;
  label?: string;
}) {
  const { data, store } = useStudy();
  const id = noteId ?? `note-${sectionId}`;
  const saved = data.notes[id];
  const update = (text: string, question = saved?.question ?? false) => {
    const at = nowISO();
    void store.change((s) => ({
      ...s,
      notes: {
        ...s.notes,
        [id]: {
          id,
          courseId,
          lessonId,
          sectionId,
          text,
          question,
          createdAt: s.notes[id]?.createdAt ?? at,
          updatedAt: at,
        },
      },
    }));
  };
  return (
    <div className="note-editor">
      <label className="sc-field">
        {label}
        <textarea
          maxLength={100000}
          className="sc-input"
          rows={4}
          value={saved?.text ?? ""}
          onChange={(e) => update(e.target.value)}
          placeholder="Explain it in your own words, or keep a question for later."
        />
      </label>
      <label className="sc-check">
        <input
          type="checkbox"
          checked={saved?.question ?? false}
          onChange={(e) => update(saved?.text ?? "", e.target.checked)}
        />{" "}
        Unresolved question
      </label>
      <SaveStatus />
    </div>
  );
}
function KnowledgeCheck({
  question: q,
  course,
  lesson,
}: {
  question: Question;
  course: CatalogCourse;
  lesson: CatalogLesson;
}) {
  const { data, store, status } = useStudy(),
    [selected, setSelected] = useState(""),
    [submitted, setSubmitted] = useState(false),
    [error, setError] = useState("");
  const event = useRef(uuid()),
    guard = useRef(false);
  const attempts = Object.values(data.attempts)
    .filter((a) => a.questionId === q.id)
    .sort((a, b) => a.at.localeCompare(b.at));
  const submit = () => {
    if (!selected) {
      setError("Choose an answer before checking.");
      return;
    }
    if (guard.current) return;
    guard.current = true;
    const id = event.current,
      at = nowISO();
    void store.change((s) =>
      s.attempts[id]
        ? s
        : {
            ...s,
            attempts: {
              ...s.attempts,
              [id]: {
                id,
                courseId: course.id,
                lessonId: lesson.id,
                questionId: q.id,
                questionRevision: q.revision,
                contentVersion: lesson.contentVersion,
                at,
                optionId: selected,
                correctOptionId: q.correctOptionId,
                correct: selected === q.correctOptionId,
                conceptIds: q.conceptIds,
                snapshot: { prompt: q.prompt, options: q.options },
              },
            },
          },
    );
    setSubmitted(true);
    setError("");
  };
  return (
    <div className="knowledge-check">
      {attempts.length > 0 &&
        attempts.at(-1)?.questionRevision !== q.revision && (
          <p className="sc-notice">
            This question has been revised. Try this version; your previous
            attempts remain unchanged.
          </p>
        )}
      <fieldset>
        <legend>{q.prompt}</legend>
        {q.options.map((o) => (
          <label
            key={o.id}
            className={`answer-option ${submitted && o.id === q.correctOptionId ? "correct-option" : ""}`}
          >
            <input
              type="radio"
              name={q.id}
              value={o.id}
              disabled={submitted}
              checked={selected === o.id}
              onChange={() => setSelected(o.id)}
            />
            <span>{o.text}</span>
          </label>
        ))}
      </fieldset>
      {error && <p role="alert">{error}</p>}
      <button
        className="sc-btn sc-btn--secondary"
        onClick={submit}
        disabled={submitted}
      >
        Check answer
      </button>
      {submitted && (
        <div className="answer-feedback" role="status">
          <p>
            <strong>
              {selected === q.correctOptionId
                ? "Correct for this question."
                : "Revisit the reasoning."}
            </strong>
          </p>
          {q.options.map((o) => (
            <p key={o.id}>
              <strong>
                {o.id === q.correctOptionId ? "Correct choice" : "Other choice"}
                : {o.text}
              </strong>
              <br />
              {o.rationale}
            </p>
          ))}
          <button
            className="sc-btn sc-btn--ghost"
            onClick={() => {
              setSelected("");
              setSubmitted(false);
              event.current = uuid();
              guard.current = false;
            }}
          >
            Try again
          </button>
        </div>
      )}
      {attempts.length > 0 && (
        <details className="sc-details">
          <summary>
            {attempts.length} {status === "saved" ? "saved" : "in-tab"}{" "}
            {attempts.length === 1 ? "attempt" : "attempts"} ·{" "}
            {attempts.filter((a) => a.correct).length} correct
          </summary>
          <ul>
            {attempts.map((a) => (
              <li key={a.id}>
                {a.correct ? "Correct" : "Incorrect"} ·{" "}
                {new Date(a.at).toLocaleString()} · question revision{" "}
                {a.questionRevision}
                <details>
                  <summary>What was assessed</summary>
                  <p>{a.snapshot.prompt}</p>
                  <p>
                    Your choice:{" "}
                    {a.snapshot.options.find((o) => o.id === a.optionId)?.text}.
                    Correct choice:{" "}
                    {
                      a.snapshot.options.find((o) => o.id === a.correctOptionId)
                        ?.text
                    }
                    .
                  </p>
                </details>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
function SectionTools({
  course,
  lesson,
  section,
}: {
  course: CatalogCourse;
  lesson: CatalogLesson;
  section: CatalogSection;
}) {
  const { data, store } = useStudy();
  const b = `bookmark-${section.id}`,
    completion = `complete-${section.id}`;
  const record = data.completions[completion];
  const completeCurrent =
    !!record?.completed && record.contentVersion === lesson.contentVersion;
  return (
    <div className="section-tools">
      <div className="actions">
        <button
          className="sc-btn sc-btn--ghost"
          aria-pressed={data.bookmarks[b]?.active ?? false}
          onClick={() => {
            const updatedAt = nowISO();
            void store.change((s) => ({
              ...s,
              bookmarks: {
                ...s.bookmarks,
                [b]: {
                  id: b,
                  courseId: course.id,
                  lessonId: lesson.id,
                  sectionId: section.id,
                  active: !s.bookmarks[b]?.active,
                  updatedAt,
                },
              },
            }));
          }}
        >
          {data.bookmarks[b]?.active ? "Bookmarked" : "Bookmark section"}
        </button>
        <button
          className="sc-btn sc-btn--ghost"
          aria-pressed={completeCurrent}
          onClick={() => {
            const updatedAt = nowISO();
            void store.change((s) => ({
              ...s,
              completions: {
                ...s.completions,
                [completion]: {
                  id: completion,
                  courseId: course.id,
                  lessonId: lesson.id,
                  sectionId: section.id,
                  completed: !completeCurrent,
                  contentVersion: lesson.contentVersion,
                  updatedAt,
                },
              },
            }));
          }}
        >
          {completeCurrent
            ? "Section complete"
            : record?.completed
              ? "Mark revised section complete"
              : "Mark section complete"}
        </button>
      </div>
      <details
        className="sc-details"
        open={!!data.notes[`note-${section.id}`]?.text}
      >
        <summary>Notes for this section</summary>
        <NoteEditor
          courseId={course.id}
          lessonId={lesson.id}
          sectionId={section.id}
        />
      </details>
    </div>
  );
}
export function Reader({
  id,
  sectionId,
  pathId,
  from,
}: {
  id: string;
  sectionId?: string;
  pathId?: string;
  from?: string;
}) {
  const entry = findLesson(id),
    { data, store } = useStudy();
  const originDetour = /^#\/lesson\/([^/?]+)/.exec(from ?? "")?.[1] === id;
  const entryRef = useRef(entry);
  entryRef.current = entry;
  // Navigation, notes, bookmarks and positions come from the catalog tier;
  // the prose and checks arrive with the lesson body.
  const [body, setBody] = useState<LessonBody | null>(null),
    [bodyError, setBodyError] = useState(""),
    [retry, setRetry] = useState(0);
  const known = !!entry;
  useEffect(() => {
    if (!known) return;
    let active = true;
    setBodyError("");
    void loadLessonBody(id)
      .then((loaded) => {
        if (active) setBody(loaded);
      })
      .catch((error: Error) => {
        if (active) setBodyError(error.message);
      });
    return () => {
      active = false;
    };
  }, [id, known, retry]);
  const bodyReady = !!body;
  useEffect(() => {
    // Restore and capture positions once the sections have their text, so a
    // saved offset lands on the same content it was measured against.
    if (!entry || !bodyReady) return;
    const { lesson, course } = entry;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let restoring = true;
    const saved = store.getSnapshot().data.positions[id];
    const target = sectionId ?? saved?.sectionId ?? lesson.sections[0].id;
    const frame = requestAnimationFrame(() =>
      requestAnimationFrame(() => {
        const node =
          document.getElementById(target) ??
          document.getElementById(lesson.sections[0].id);
        if (!sectionId && !saved) window.scrollTo(0, 0);
        else if (node) {
          node.scrollIntoView();
          if (saved?.sectionId === target)
            window.scrollBy(0, Math.max(0, saved.offset));
        }
        restoring = false;
      }),
    );
    const capture = () => {
      if (restoring) return;
      const nodes = lesson.sections
        .map((s) => ({ s, node: document.getElementById(s.id) }))
        .filter((v) => v.node);
      const reached = nodes.filter(
        (v) => v.node!.getBoundingClientRect().top <= 180,
      );
      // Above the first section (title, outcomes, context) no section is being
      // read, so an existing saved place is kept: scrolling up to the masthead
      // to search or to reread the outcomes must not move it back to the start.
      // A first visit still records the first section.
      if (!reached.length && store.getSnapshot().data.positions[id]) return;
      const selected = reached.at(-1) ?? nodes[0];
      if (!selected) return;
      const position = {
        courseId: course.id,
        lessonId: id,
        sectionId: selected.s.id,
        offset: Math.max(0, -selected.node!.getBoundingClientRect().top),
        updatedAt: nowISO(),
        ...(pathId ? { pathId } : {}),
      };
      void store.change((s) => ({
        ...s,
        resume: from ? s.resume : position,
        positions: originDetour
          ? s.positions
          : { ...s.positions, [id]: position },
      }));
    };
    const scroll = () => {
      clearTimeout(timer);
      timer = setTimeout(capture, 300);
    };
    const initial = setTimeout(capture, 150);
    window.addEventListener("scroll", scroll, { passive: true });
    window.addEventListener("pagehide", capture);
    return () => {
      clearTimeout(timer);
      clearTimeout(initial);
      cancelAnimationFrame(frame);
      capture();
      window.removeEventListener("scroll", scroll);
      window.removeEventListener("pagehide", capture);
    };
  }, [id, sectionId, pathId, from, originDetour, store, bodyReady]);
  if (!entry)
    return (
      <>
        <PageTitle
          eyebrow="lesson unavailable"
          title="This lesson is no longer in the catalog."
        />
        <p>
          Your notes and history are preserved. Find them in{" "}
          <a href="#/notebook">Notebook</a>, or return to{" "}
          <a href="#/courses">Courses</a>.
        </p>
      </>
    );
  const { course, module, lesson } = entry;
  const href = (lessonId: string, section?: string, context?: string) => {
    const target = lessonHref(lessonId, section, context);
    return from
      ? `${target}${target.includes("?") ? "&" : "?"}from=${encodeURIComponent(from)}`
      : target;
  };
  const path = pathForLesson(paths, id, pathId);
  const prerequisites = [
    ...new Set([
      ...lesson.prerequisiteIds,
      ...(path?.prerequisites
        .filter((p) => p.lessonId === id)
        .map((p) => p.requiredLessonId) ?? []),
    ]),
  ];
  const bridges =
    path?.optionalBridges.filter((b) => b.beforeLessonIds.includes(id)) ?? [];
  const checkSection = lesson.sections.find((s) => s.kind === "revisit");
  const checks = (
    <>
      <h3>Check your understanding</h3>
      {body?.questions.map((q) => (
        <KnowledgeCheck
          key={q.id}
          question={q}
          course={course}
          lesson={lesson}
        />
      ))}
      <p>
        {cardIndex.filter((c) => c.lessonId === id).length} flashcards connect
        this lesson to later review.
      </p>
      <a href={`#/review/${id}`}>Review this lesson’s cards →</a>
    </>
  );
  const courseEntries = lessonEntries.filter((e) => e.course.id === course.id);
  const index = courseEntries.findIndex((e) => e.lesson.id === id);
  const neighbors = path ? pathNeighbors(path, id) : undefined;
  const previous = neighbors
    ? neighbors.previous
      ? findLesson(neighbors.previous)
      : undefined
    : courseEntries[index - 1];
  const next = neighbors
    ? neighbors.next
      ? findLesson(neighbors.next)
      : undefined
    : courseEntries[index + 1];
  const history = data.completions[`complete-${lesson.id}`];
  const revised =
    history?.completed && history.contentVersion !== lesson.contentVersion;
  const completed = !!history?.completed && !revised;
  const changeFocus = () => {
    const updatedAt = nowISO();
    void store.change((s) => ({
      ...s,
      settings: { ...s.settings, focus: !s.settings.focus, updatedAt },
    }));
  };
  return (
    <div className={`reader ${data.settings.focus ? "focus-mode" : ""}`}>
      {teachingIndex.some((m) => m.lessonIds.includes(id)) && (
        <p className="legacy-reference-note">
          Original lesson reference · your earlier notes and history stay here.{" "}
          <a
            href={beatHref(
              teachingIndex.find((m) => m.lessonIds.includes(id))!.moduleId,
              teachingIndex
                .find((m) => m.lessonIds.includes(id))!
                .beats.find(
                  (b) =>
                    b.lessonId === id &&
                    (b.sectionId === sectionId || !sectionId),
                )?.id,
            )}
          >
            Open the linked visual teaching module →
          </a>
        </p>
      )}
      <div className="reader-top">
        <a
          className="sc-link--quiet"
          href={path ? `#/path/${path.id}` : `#/course/${course.id}`}
        >
          {path ? `← ${path.title}` : "← Course map"}
        </a>
        <button className="sc-btn sc-btn--secondary" onClick={changeFocus}>
          {data.settings.focus ? "Exit focus mode" : "Focus mode"}
        </button>
      </div>
      <PageTitle
        eyebrow={`${module.title} · lesson ${module.lessons.findIndex((l) => l.id === id) + 1} of ${module.lessons.length}`}
        title={lesson.title}
      >
        <p>{lesson.summary}</p>
        <p className="sc-meta">
          About {lesson.estimatedMinutes} minutes to read · estimate · practice
          at your own pace
        </p>
      </PageTitle>
      <p className="reader-context">
        {path ? (
          <>
            Following <a href={`#/path/${path.id}`}>{path.title}</a>. Previous
            and next stay in this roadmap.
          </>
        ) : pathId ? (
          <>
            The requested roadmap is unavailable or does not contain this topic.
            Previous and next use{" "}
            <a href={`#/course/${course.id}`}>{course.title}</a>.
          </>
        ) : (
          <>
            Direct topic visit. Previous and next use{" "}
            <a href={`#/course/${course.id}`}>{course.title}</a>.
          </>
        )}
      </p>
      <p className="reader-utilities">
        <a
          href={`#/learn/playbooks?from=${encodeURIComponent(from ?? lessonHref(id, data.positions[id]?.sectionId ?? sectionId, pathId))}`}
        >
          Related task references
        </a>{" "}
        · <a href={`#/notebook`}>Notebook</a>
      </p>
      {revised && (
        <p className="sc-notice">
          You completed version {history.contentVersion}. This is version{" "}
          {lesson.contentVersion}; your earlier completion is preserved, and
          does not mean you studied this revision.
        </p>
      )}
      <div className="sc-reading">
        <nav
          className="sc-chapter-nav sc-chapter-nav--rail"
          aria-label="Lesson sections"
        >
          {lesson.sections.map((s, i) => (
            <a
              key={s.id}
              href={href(id, s.id, pathId)}
              aria-current={
                data.resume?.lessonId === id && data.resume.sectionId === s.id
                  ? "location"
                  : undefined
              }
              onClick={() => {
                if (originDetour) return;
                const updatedAt = nowISO();
                void store.change((state) => ({
                  ...state,
                  positions: {
                    ...state.positions,
                    [id]: {
                      courseId: course.id,
                      lessonId: id,
                      sectionId: s.id,
                      offset: 0,
                      updatedAt,
                      ...(pathId ? { pathId } : {}),
                    },
                  },
                }));
              }}
            >
              <span className="chapter-number">
                {String(i + 1).padStart(2, "0")}
              </span>
              {s.title}
            </a>
          ))}
        </nav>
        <article className="sc-reading__body sc-doc sc-doc--flat">
          {bodyError ? (
            <div className="sc-notice lesson-body-status" role="alert">
              <p>{bodyError}</p>
              <button
                className="sc-btn sc-btn--secondary"
                onClick={() => setRetry((n) => n + 1)}
              >
                Retry lesson
              </button>
            </div>
          ) : (
            !body && (
              <p className="lesson-body-status" role="status">
                Opening the lesson…
              </p>
            )
          )}
          <div className="lesson-outcomes">
            <p className="sc-eyebrow">After this lesson</p>
            <ul>
              {lesson.objectives.map((o) => (
                <li key={o}>{o}</li>
              ))}
            </ul>
            <p className="sc-eyebrow">Helpful first</p>
            {prerequisites.length ? (
              <ul>
                {prerequisites.map((prerequisite) => (
                  <li key={prerequisite}>
                    <a
                      href={
                        findLesson(prerequisite)
                          ? lessonHref(
                              prerequisite,
                              undefined,
                              path &&
                                pathForLesson(paths, prerequisite, path.id)
                                ? path.id
                                : undefined,
                            )
                          : `#/course/${courses.find((c) => c.id === prerequisite || c.modules.some((m) => m.id === prerequisite))?.id ?? prerequisite}`
                      }
                    >
                      {findLesson(prerequisite)?.lesson.title ??
                        courses.find((c) => c.id === prerequisite)?.title ??
                        courses
                          .flatMap((c) => c.modules)
                          .find((m) => m.id === prerequisite)?.title ??
                        prerequisite}
                    </a>
                    {path?.prerequisites.find(
                      (p) =>
                        p.lessonId === id &&
                        p.requiredLessonId === prerequisite,
                    )?.explanation
                      ? ` — ${path.prerequisites.find((p) => p.lessonId === id && p.requiredLessonId === prerequisite)!.explanation}`
                      : ""}
                  </li>
                ))}
              </ul>
            ) : (
              <p>
                No required earlier topic. Use the optional foundations when
                helpful.
              </p>
            )}
            {bridges.length > 0 && (
              <div>
                <p>Optional foundations for this topic:</p>
                <ul>
                  {bridges.map((b) => (
                    <li key={b.lessonId}>
                      <a href={href(b.lessonId, undefined, path?.id)}>
                        {findLesson(b.lessonId)?.lesson.title}
                      </a>{" "}
                      — {b.explanation}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <p className="sc-hint">
              Prerequisites are guidance; every topic is open.
            </p>
          </div>
          {sectionId && !lesson.sections.some((s) => s.id === sectionId) && (
            <p className="sc-notice">
              That section was removed. Your linked notes remain in Notebook.
              Showing the beginning of this lesson.
            </p>
          )}
          {lesson.sections.map((s, i) => (
            <section
              id={s.id}
              key={s.id}
              className="lesson-section"
              tabIndex={-1}
            >
              <p className="sc-eyebrow">
                {String(i + 1).padStart(2, "0")} /{" "}
                {s.kind === "customer" ? "explain it" : s.kind}
              </p>
              <h2>{s.title}</h2>
              {s.kind === "deeper" || s.kind === "solution" ? (
                <details className="sc-details depth">
                  <summary>
                    {s.kind === "solution"
                      ? "Reveal explained solution"
                      : "Expand technical detail"}
                  </summary>
                  <MD
                    pathId={path?.id}
                    from={
                      from ??
                      lessonHref(
                        id,
                        data.positions[id]?.sectionId ?? sectionId,
                        path?.id,
                      )
                    }
                  >
                    {body?.sections[s.id] ?? ""}
                  </MD>
                </details>
              ) : (
                <MD
                  pathId={path?.id}
                  from={
                    from ??
                    lessonHref(
                      id,
                      data.positions[id]?.sectionId ?? sectionId,
                      path?.id,
                    )
                  }
                >
                  {body?.sections[s.id] ?? ""}
                </MD>
              )}
              {s.assetIds.map((a) => {
                const asset = course.assets.find((v) => v.id === a);
                return asset ? <Diagram key={a} asset={asset} /> : null;
              })}
              {(s.kind === "try" || s.kind === "exercise") && (
                <TryDraft course={course} lesson={lesson} section={s} />
              )}{" "}
              {s.id === checkSection?.id && checks}
              <Sources course={course} claimIds={s.claimIds} />
              <SectionTools course={course} lesson={lesson} section={s} />
            </section>
          ))}
          {!checkSection && (
            <section className="lesson-checks">{checks}</section>
          )}
          {!!lesson.downloadIds?.length && (
            <section className="lesson-downloads">
              <h2>Optional local exercises</h2>
              <p>
                Read and solve the tasks here, or download the authored files to
                run locally. Downloading does not execute code or record
                completion.
              </p>
              <ul>
                {lesson.downloadIds.map((downloadId) => {
                  const file = course.downloads?.find(
                    (d) => d.id === downloadId,
                  );
                  return file ? (
                    <li key={file.id}>
                      <a
                        href={baseAsset(
                          `content-downloads/${file.path.replace(/^downloads\//, "")}`,
                        )}
                        download
                      >
                        {file.title}
                      </a>
                      <p>{file.description}</p>
                    </li>
                  ) : null;
                })}
              </ul>
            </section>
          )}
          <div className="sc-actionbar">
            <p>
              {completed
                ? "You marked this lesson complete. Quiz and review evidence remain separate."
                : "Finished this lesson? Mark completion when you choose."}
            </p>
            <button
              className="sc-btn sc-btn--primary"
              aria-pressed={completed}
              onClick={() => {
                const updatedAt = nowISO(),
                  key = `complete-${id}`;
                void store.change((s) => ({
                  ...s,
                  completions: {
                    ...s.completions,
                    [key]: {
                      id: key,
                      courseId: course.id,
                      lessonId: id,
                      completed: !completed,
                      contentVersion: lesson.contentVersion,
                      updatedAt,
                    },
                  },
                }));
              }}
            >
              {completed ? "Mark incomplete" : "Mark lesson complete"}
            </button>
          </div>
          <nav
            className="lesson-pagination"
            aria-label="Previous and next lessons"
          >
            {previous && (
              <a href={href(previous.lesson.id, undefined, path?.id)}>
                ← {previous.lesson.title}
              </a>
            )}
            {next && (
              <a href={href(next.lesson.id, undefined, path?.id)}>
                {next.lesson.title} →
              </a>
            )}
          </nav>
          {!next && (
            <p className="sc-hint">
              End of this {path ? "roadmap" : "course"}. Choose a topic to
              revisit or open <a href="#/review">Review</a>.
            </p>
          )}
        </article>
      </div>
    </div>
  );
}
function TryDraft({
  course,
  section,
}: {
  course: CatalogCourse;
  lesson: CatalogLesson;
  section: CatalogSection;
}) {
  const { data, store } = useStudy();
  const id = `draft-${section.id}`;
  return (
    <div className="note-editor">
      <label className="sc-field">
        Your practice response
        <textarea
          maxLength={100000}
          className="sc-input"
          rows={5}
          value={data.drafts[id]?.text ?? ""}
          onChange={(e) => {
            const text = e.target.value,
              at = nowISO();
            void store.change((s) => ({
              ...s,
              drafts: {
                ...s.drafts,
                [id]: {
                  id,
                  courseId: course.id,
                  targetId: section.id,
                  text,
                  createdAt: s.drafts[id]?.createdAt ?? at,
                  updatedAt: at,
                },
              },
            }));
          }}
        />
      </label>
      <SaveStatus />
      <p className="sc-hint">
        Compare your reasoning with the explained solution or Check and revisit.
        Your draft is not automatically graded; revealing an answer does not
        complete the task.
      </p>
    </div>
  );
}
