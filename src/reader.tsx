import { useEffect, useRef, useState } from "react";
import { cards, findLesson, lessonEntries, lessonHref } from "./catalog";
import type { Course, Lesson, Question, Section } from "./content-schema";
import { nowISO } from "./study";
import {
  Diagram,
  MD,
  PageTitle,
  SaveStatus,
  Sources,
  useStudy,
  uuid,
} from "./ui";

export function NoteEditor({
  courseId,
  lessonId,
  sectionId,
  noteId,
}: {
  courseId: string;
  lessonId: string;
  sectionId: string;
  noteId?: string;
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
        Your lesson note
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
  course: Course;
  lesson: Lesson;
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
  course: Course;
  lesson: Lesson;
  section: Section;
}) {
  const { data, store } = useStudy();
  const b = `bookmark-${section.id}`,
    completion = `complete-${section.id}`;
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
          aria-pressed={data.completions[completion]?.completed ?? false}
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
                  completed: !s.completions[completion]?.completed,
                  contentVersion: lesson.contentVersion,
                  updatedAt,
                },
              },
            }));
          }}
        >
          {data.completions[completion]?.completed
            ? "Section complete"
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
export function Reader({ id, sectionId }: { id: string; sectionId?: string }) {
  const entry = findLesson(id),
    { data, store } = useStudy();
  const entryRef = useRef(entry);
  entryRef.current = entry;
  useEffect(() => {
    if (!entry) return;
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
        if (node) {
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
      const selected =
        nodes
          .filter((v) => v.node!.getBoundingClientRect().top <= 180)
          .at(-1) ?? nodes[0];
      if (!selected) return;
      const position = {
        courseId: course.id,
        lessonId: id,
        sectionId: selected.s.id,
        offset: Math.max(0, -selected.node!.getBoundingClientRect().top),
        updatedAt: nowISO(),
      };
      void store.change((s) => ({
        ...s,
        resume: position,
        positions: { ...s.positions, [id]: position },
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
  }, [id, sectionId, store]);
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
  const index = lessonEntries.findIndex((e) => e.lesson.id === id),
    previous = lessonEntries[index - 1],
    next = lessonEntries[index + 1];
  const completed =
    data.completions[`complete-${lesson.id}`]?.completed ?? false;
  const changeFocus = () => {
    const updatedAt = nowISO();
    void store.change((s) => ({
      ...s,
      settings: { ...s.settings, focus: !s.settings.focus, updatedAt },
    }));
  };
  return (
    <div className={`reader ${data.settings.focus ? "focus-mode" : ""}`}>
      <div className="reader-top">
        <a className="sc-link--quiet" href={`#/course/${course.id}`}>
          ← Course map
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
      <div className="sc-reading">
        <nav
          className="sc-chapter-nav sc-chapter-nav--rail"
          aria-label="Lesson sections"
        >
          {lesson.sections.map((s, i) => (
            <a
              key={s.id}
              href={lessonHref(id, s.id)}
              aria-current={
                data.resume?.lessonId === id && data.resume.sectionId === s.id
                  ? "location"
                  : undefined
              }
              onClick={() => {
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
                    },
                  },
                }));
              }}
            >
              <span className="chapter-number">0{i + 1}</span>
              {s.title}
            </a>
          ))}
        </nav>
        <article className="sc-reading__body sc-doc sc-doc--flat">
          <div className="lesson-outcomes">
            <p className="sc-eyebrow">After this lesson</p>
            <ul>
              {lesson.objectives.map((o) => (
                <li key={o}>{o}</li>
              ))}
            </ul>
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
                0{i + 1} / {s.kind === "customer" ? "explain it" : s.kind}
              </p>
              <h2>{s.title}</h2>
              {s.kind === "deeper" ? (
                <details className="sc-details depth">
                  <summary>Expand technical detail</summary>
                  <MD>{s.markdown}</MD>
                </details>
              ) : (
                <MD>{s.markdown}</MD>
              )}
              {s.assetIds.map((a) => {
                const asset = course.assets.find((v) => v.id === a);
                return asset ? <Diagram key={a} asset={asset} /> : null;
              })}
              {s.kind === "try" && (
                <TryDraft course={course} lesson={lesson} section={s} />
              )}{" "}
              {s.kind === "revisit" && (
                <>
                  <h3>Check your understanding</h3>
                  {lesson.questions.map((q) => (
                    <KnowledgeCheck
                      key={q.id}
                      question={q}
                      course={course}
                      lesson={lesson}
                    />
                  ))}
                  <p>
                    {cards.filter((c) => c.lessonId === id).length} flashcards
                    connect this lesson to later review.
                  </p>
                  <a href={`#/review/${id}`}>Review this lesson’s cards →</a>
                </>
              )}
              <Sources course={course} claimIds={s.claimIds} />
              <SectionTools course={course} lesson={lesson} section={s} />
            </section>
          ))}
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
                      completed: !s.completions[key]?.completed,
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
              <a href={lessonHref(previous.lesson.id)}>
                ← {previous.lesson.title}
              </a>
            )}
            {next && (
              <a href={lessonHref(next.lesson.id)}>{next.lesson.title} →</a>
            )}
          </nav>
        </article>
      </div>
    </div>
  );
}
function TryDraft({
  course,
  section,
}: {
  course: Course;
  lesson: Lesson;
  section: Section;
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
        Compare your reasoning with the answer in Check and revisit. This
        response is not automatically graded.
      </p>
    </div>
  );
}
