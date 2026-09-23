import { useEffect, useRef, useState } from "react";
import {
  beatHref,
  cardIndex,
  courses,
  findBeat,
  findLesson,
  lessonHref,
  loadLessonBody,
  loadTeachingMedia,
  loadTeachingModule,
  moduleLessonIds,
  paths,
  plainTeaching,
  teachingIndex,
} from "./catalog";
import type { CatalogCourse, LessonBody } from "./catalog-types";
import type { Beat, TeachingMedia, TeachingModule } from "./teaching-schema";
import { nowISO, reviewQueue, type BeatPosition } from "./study";
import { MD, SaveStatus, useStudy, uuid } from "./ui";
import { NoteEditor } from "./reader";
import { Review } from "./practice-review";
import { TeachingSources, TeachingText, Visual } from "./teaching-text";

export function TeacherToday() {
  const { data } = useStudy(),
    resume = data.beatResume,
    entry = resume ? findBeat(resume.beatId) : undefined;
  const due = reviewQueue(cardIndex, data, nowISO(), 100000).length;
  return (
    <div className="teacher-home">
      <p className="sc-eyebrow">Your learning space</p>
      <h1 tabIndex={-1}>One idea. A little clearer.</h1>
      <p className="home-intro">
        Pick up where you left off, or choose a course. A small session is
        welcome.
      </p>
      <div className="today-primary">
        {entry && resume ? (
          <>
            <span className="sc-eyebrow">Continue · {entry.module.title}</span>
            <h2>{entry.beat.title}</h2>
            <p>{entry.beat.recap}</p>
            <a
              className="sc-btn sc-btn--primary"
              href={beatHref(entry.module.moduleId, entry.beat.id, resume.view)}
            >
              Resume learning →
            </a>
            {entry.beat.version !== resume.version && (
              <p>
                This beat has changed since your last visit. Your earlier work
                is retained.
              </p>
            )}
          </>
        ) : data.resume && findLesson(data.resume.lessonId) ? (
          <>
            <p className="sc-eyebrow">Your saved reference</p>
            <h2>{findLesson(data.resume.lessonId)?.lesson.title}</h2>
            <p>
              Your saved place remains in the original lesson. The course now
              also has visual teaching beats.
            </p>
            <a
              className="sc-btn sc-btn--primary"
              href={lessonHref(
                data.resume.lessonId,
                data.resume.sectionId,
                data.resume.pathId,
              )}
            >
              Resume saved lesson →
            </a>
          </>
        ) : (
          <>
            <p className="sc-eyebrow">Start with understanding</p>
            <h2>{courses[0]?.title ?? "Choose your first course"}</h2>
            <p>
              See how an idea works, try it yourself, then return when you need
              it.
            </p>
            <a
              className="sc-btn sc-btn--primary"
              href={courses[0] ? `#/course/${courses[0].id}` : "#/courses"}
            >
              Open the course →
            </a>
          </>
        )}
      </div>
      {data.resume?.pathId &&
        !paths.some((p) => p.id === data.resume?.pathId) && (
          <p className="sc-notice">
            Your saved roadmap is unavailable. Your original lesson, notes and
            saved place remain available.
          </p>
        )}
      <div className="today-secondary">
        <a href="#/courses">
          <strong>Courses</strong>
          <span>Choose a topic and your own pace.</span>
        </a>
        <a href="#/review">
          <strong>
            {due ? `${due} cards to revisit` : "A little recall practice"}
          </strong>
          <span>Due cards keep their own schedule.</span>
        </a>
        <a href="#/notebook">
          <strong>Your notebook</strong>
          <span>Keep the explanations that clicked.</span>
        </a>
      </div>
      <details className="secondary-library">
        <summary>Other ways to find material</summary>
        <a href="#/learn">Learning paths, topics and playbooks</a> ·{" "}
        <a href="#/search">Search lessons, concepts and your notes</a>
      </details>
    </div>
  );
}
export function TeacherCourses({ id }: { id?: string }) {
  const { data } = useStudy(),
    course = courses.find((c) => c.id === id);
  if (id && !course)
    return (
      <div>
        <h1>Course unavailable</h1>
        <a href="#/courses">Browse courses</a>
      </div>
    );
  if (!course)
    return (
      <div className="teacher-courses">
        <h1 tabIndex={-1}>Your courses</h1>
        <p>Explore one subject at a time. Everything stays open to you.</p>
        {courses.map((c) => (
          <a
            className="teacher-course-card"
            href={`#/course/${c.id}`}
            key={c.id}
          >
            <span className="sc-eyebrow">{c.modules.length} modules</span>
            <h2>{c.title}</h2>
            <p>{c.subtitle}</p>
            <strong>See the course →</strong>
          </a>
        ))}
      </div>
    );
  const savedCoursePosition =
    data.beatResume?.courseId === course.id && findBeat(data.beatResume.beatId)
      ? data.beatResume
      : undefined;
  const startHref = savedCoursePosition
    ? beatHref(
        savedCoursePosition.moduleId,
        savedCoursePosition.beatId,
        savedCoursePosition.view,
      )
    : teachingIndex.some((m) => m.moduleId === course.modules[0].id)
      ? beatHref(course.modules[0].id)
      : lessonHref(course.modules[0].lessons[0].id);
  return (
    <div className="teacher-course">
      <a href="#/courses" className="sc-link--quiet">
        ← Courses
      </a>
      <header className="course-heading">
        <p className="sc-eyebrow">
          Your course map · {course.modules.length} modules
        </p>
        <h1 tabIndex={-1}>{course.title}</h1>
        <p>{course.subtitle}</p>
        <div className="actions">
          <a className="sc-btn sc-btn--primary" href={startHref}>
            {savedCoursePosition ? "Resume the course →" : "Start the course →"}
          </a>
          <a href={`#/handbook/${course.id}`}>Open course handbook</a>
        </div>
      </header>
      <details className="sc-details">
        <summary>Outcomes, starting point and optional bridges</summary>
        <MD>{course.summary}</MD>
        <ul>
          {course.objectives.map((o) => (
            <li key={o}>{o}</li>
          ))}
        </ul>
        <p>
          No cloud workspace is needed. Optional refreshers are linked where
          they help.
        </p>
        {course.refreshers.map((r) => (
          <details key={r.title}>
            <summary>{r.title}</summary>
            <MD>{r.markdown}</MD>
          </details>
        ))}
      </details>
      <ol className="teacher-module-map">
        {course.modules.map((m, i) => {
          const t = teachingIndex.find((t) => t.moduleId === m.id),
            completed =
              t?.beats.filter(
                (b) =>
                  data.completions[`beat-${b.id}`]?.completed &&
                  data.completions[`beat-${b.id}`]?.contentVersion ===
                    b.version,
              ).length ?? 0,
            saved = Object.values(data.beatPositions)
              .filter(
                (p) =>
                  p.moduleId === m.id &&
                  t?.beats.some((b) => b.id === p.beatId),
              )
              .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))[0];
          return (
            <li key={m.id}>
              <span className="module-index">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div>
                <h2>
                  <a href={t ? beatHref(m.id) : lessonHref(m.lessons[0].id)}>
                    {t?.title ?? m.title}
                  </a>
                </h2>
                <p>{t?.summary ?? m.summary}</p>
                {saved && (
                  <p className="sc-hint">
                    Saved place:{" "}
                    {t?.beats.find((b) => b.id === saved.beatId)?.title}
                  </p>
                )}
                <div className="module-map-meta">
                  <span>
                    {t
                      ? `${t.beats.length} teaching beats · ${completed} marked complete`
                      : `${m.lessons.length} lessons`}
                  </span>
                  {t && (
                    <a href={beatHref(m.id, undefined, "handbook", true)}>
                      Handbook
                    </a>
                  )}
                </div>
              </div>
              <a
                className="module-open"
                href={t ? beatHref(m.id) : lessonHref(m.lessons[0].id)}
                aria-label={`Open ${t?.title ?? m.title}`}
              >
                →
              </a>
            </li>
          );
        })}
      </ol>
      <details className="secondary-library">
        <summary>Original references and alternative paths</summary>
        <p>
          All original lessons and their notes remain available in search and
          the learning library.
        </p>
        <a href="#/learn">Open learning library</a>
      </details>
      <p className="sc-hint">
        Completion is your explicit choice, separate from check evidence and
        card recall. This independent course is not an official credential or
        leveling rubric.
      </p>
    </div>
  );
}
function Draft({
  id,
  targetId,
  courseId,
  label,
}: {
  id: string;
  targetId: string;
  courseId: string;
  label: string;
}) {
  const { data, store } = useStudy();
  return (
    <label className="sc-field">
      {label}
      <textarea
        className="sc-input"
        rows={4}
        maxLength={100000}
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
                targetId,
                courseId,
                text,
                createdAt: s.drafts[id]?.createdAt ?? at,
                updatedAt: at,
              },
            },
          }));
        }}
      />
    </label>
  );
}
function BeatCheck({
  module,
  course,
  beat,
  questionId,
  lessons,
}: {
  module: TeachingModule;
  course: CatalogCourse;
  beat: Beat;
  questionId: string;
  lessons: LessonBody[];
}) {
  const { data, store } = useStudy(),
    q = [
      ...module.questions,
      ...module.selfQuestions,
      ...lessons.flatMap((l) => l.questions),
    ].find((q) => q.id === questionId);
  if (!q)
    return (
      <p className="sc-hint">
        This check is unavailable in the current course files. Your earlier
        answers are retained.
      </p>
    );
  const id = `check-${q.id}`,
    raw = data.beatChecks[id],
    saved = raw?.questionRevision === q.revision ? raw : undefined,
    objective = "options" in q,
    validChoice =
      objective && q.options.some((o) => o.id === saved?.selectedOptionId),
    revealed = saved?.revealed && (!objective || validChoice);
  const update = (patch: Partial<NonNullable<typeof saved>>) => {
    const at = nowISO();
    void store.change((s) => ({
      ...s,
      beatChecks: {
        ...s.beatChecks,
        [id]: {
          ...(s.beatChecks[id]?.questionRevision === q.revision
            ? s.beatChecks[id]
            : {
                id,
                courseId: course.id,
                moduleId: module.moduleId,
                beatId: beat.id,
                questionId: q.id,
                questionRevision: q.revision,
                opened: false,
                revealed: false,
              }),
          ...patch,
          updatedAt: at,
        },
      },
    }));
  };
  const grade = () => {
    if (!objective || !saved?.selectedOptionId || !validChoice || revealed)
      return;
    const optionId = saved.selectedOptionId,
      at = nowISO(),
      event = uuid();
    void store.change((s) => ({
      ...s,
      beatChecks: {
        ...s.beatChecks,
        [id]: { ...s.beatChecks[id], revealed: true, updatedAt: at },
      },
      attempts: {
        ...s.attempts,
        [event]: {
          id: event,
          courseId: course.id,
          lessonId: beat.lessonId,
          questionId: q.id,
          questionRevision: q.revision,
          contentVersion: findLesson(beat.lessonId)!.lesson.contentVersion,
          beatId: beat.id,
          beatVersion: beat.version,
          at,
          optionId,
          correctOptionId: q.correctOptionId,
          correct: optionId === q.correctOptionId,
          conceptIds: q.conceptIds,
          snapshot: { prompt: q.prompt, options: q.options },
        },
      },
    }));
  };
  return (
    <details
      className="beat-check"
      open={saved?.opened ?? false}
      onToggle={(e) => {
        if (e.currentTarget.open !== (saved?.opened ?? false))
          update({ opened: e.currentTarget.open });
      }}
    >
      <summary>Check yourself</summary>
      <div className="check-body">
        <TeachingText module={module} course={course}>
          {q.prompt}
        </TeachingText>
        {objective ? (
          <fieldset>
            <legend className="sc-sr-only">Choose an answer</legend>
            {q.options.map((o) => (
              <label key={o.id} className="check-option">
                <input
                  type="radio"
                  name={id}
                  disabled={revealed}
                  checked={saved?.selectedOptionId === o.id}
                  onChange={() =>
                    update({ selectedOptionId: o.id, revealed: false })
                  }
                />
                <span>{plainTeaching(o.text)}</span>
              </label>
            ))}
          </fieldset>
        ) : (
          <Draft
            id={`draft-${q.id}`}
            targetId={q.id}
            courseId={course.id}
            label="Your reasoning (saved locally)"
          />
        )}
        {!revealed ? (
          <button
            className="sc-btn sc-btn--secondary"
            disabled={objective && !validChoice}
            onClick={() => (objective ? grade() : update({ revealed: true }))}
          >
            {objective ? "Check my answer" : "Reveal model reasoning"}
          </button>
        ) : (
          <div className="check-answer" role="status">
            {objective ? (
              <>
                <strong>
                  {saved.selectedOptionId === q.correctOptionId
                    ? "That choice is correct."
                    : "Compare the reasoning."}
                </strong>
                {q.options.map((o) => (
                  <div key={o.id}>
                    <p>
                      <strong>
                        {o.id === q.correctOptionId
                          ? "Correct choice: "
                          : "Alternative: "}
                        {plainTeaching(o.text)}
                      </strong>
                    </p>
                    <TeachingText module={module} course={course}>
                      {o.rationale}
                    </TeachingText>
                  </div>
                ))}
              </>
            ) : (
              <>
                <p className="sc-eyebrow">Model reasoning · self-comparison</p>
                <TeachingText module={module} course={course}>
                  {q.modelAnswer}
                </TeachingText>
                <TeachingText module={module} course={course}>
                  {q.reasoning}
                </TeachingText>
                <p>No automatic score is assigned to your writing.</p>
              </>
            )}
            <button
              className="sc-btn sc-btn--ghost"
              onClick={() =>
                update({ revealed: false, selectedOptionId: undefined })
              }
            >
              Try again
            </button>
          </div>
        )}
        <p className="sc-hint">
          Trying or revealing this check does not mark the beat complete.
        </p>
        <SaveStatus />
      </div>
    </details>
  );
}
function MediaReference({
  item,
  module,
  course,
}: {
  item: TeachingMedia;
  module: TeachingModule;
  course: CatalogCourse;
}) {
  const [loaded, setLoaded] = useState(false),
    [failed, setFailed] = useState(false);
  return (
    <details className="beat-media">
      <summary>Another explanation · {item.title}</summary>
      <p>
        {item.publisher} · {item.language}
        {item.durationSeconds
          ? ` · ${Math.round(item.durationSeconds / 60)} min total`
          : ""}
      </p>
      <p>
        <strong>Watch for:</strong> {item.watchFor}
      </p>
      {item.startSeconds !== null && (
        <p>
          Reviewed segment starts at {Math.floor(item.startSeconds / 60)}:
          {String(Math.floor(item.startSeconds % 60)).padStart(2, "0")}
          {item.endSeconds !== null
            ? ` and ends at ${Math.floor(item.endSeconds / 60)}:${String(Math.floor(item.endSeconds % 60)).padStart(2, "0")}`
            : ""}
          .
        </p>
      )}
      {item.embeddingStatus === "verified" &&
        item.embedUrl &&
        (!loaded ? (
          <div className="media-consent">
            <p>
              Loading the player connects to YouTube and shares this site’s
              origin. Your study notes are not sent. Nothing is loaded until you
              choose.
            </p>
            <button
              className="sc-btn sc-btn--secondary"
              onClick={() => setLoaded(true)}
            >
              Load video player
            </button>
          </div>
        ) : (
          <>
            <iframe
              className="teaching-player"
              title={item.title}
              src={item.embedUrl}
              sandbox="allow-scripts allow-same-origin allow-presentation"
              allow="fullscreen; picture-in-picture"
              referrerPolicy="strict-origin-when-cross-origin"
              onError={() => setFailed(true)}
              allowFullScreen
            />
            <button
              className="sc-btn sc-btn--ghost"
              onClick={() => setLoaded(false)}
            >
              Unload player
            </button>
            <button
              className="sc-btn sc-btn--ghost"
              onClick={() => setFailed(true)}
            >
              Player unavailable? Use the illustrated explanation
            </button>
          </>
        ))}
      {(failed || item.embeddingStatus !== "verified") && (
        <p role="status">
          The original link and illustrated explanation remain available.
        </p>
      )}
      <a href={item.url} target="_blank" rel="noopener noreferrer">
        Open original video in a new tab ↗
      </a>
      <p>
        <strong>Use it next:</strong> {item.useNext}
      </p>
      <details open={failed}>
        <summary>{item.fallback.title} · illustrated equivalent</summary>
        <TeachingText module={module} course={course}>
          {item.fallback.markdown}
        </TeachingText>
        <Visual
          visual={module.visuals.find((v) => v.id === item.fallback.visualId)!}
        />
      </details>
      <details>
        <summary>Review notes, captions and limits</summary>
        <p>
          Reviewed {item.reviewedAt} using {item.reviewMethod}. Published:{" "}
          {item.publishedAt ?? "date not verified"}.
        </p>
        <p>{item.reviewedEvidence}</p>
        <p>Captions: {item.captions}</p>
        <p>Playback: {item.playbackStatus}</p>
        <p>
          {item.context} {item.limits}
        </p>
        <ul>
          {item.candidatesCompared.map((c, i) => (
            <li key={i}>
              <a href={c.url} target="_blank" rel="noopener noreferrer">
                {c.title}
              </a>
              : {c.decision}
            </li>
          ))}
        </ul>
      </details>
      <p className="sc-hint">
        Opening or playing a video does not record learning completion.
      </p>
    </details>
  );
}
function HandbookArticle({
  module,
  course,
  beat,
  withVisual = true,
}: {
  module: TeachingModule;
  course: CatalogCourse;
  beat: Beat;
  withVisual?: boolean;
}) {
  return (
    <article className="handbook-article" id={`handbook-${beat.id}`}>
      <p className="sc-eyebrow">{module.title}</p>
      <h2>{beat.title}</h2>
      <p className="beat-outcome">{beat.outcome}</p>
      <TeachingText module={module} course={course}>
        {beat.explanation}
      </TeachingText>
      {withVisual && (
        <Visual visual={module.visuals.find((v) => v.id === beat.visualId)!} />
      )}
      <TeachingText module={module} course={course}>
        {beat.handbook.markdown}
      </TeachingText>
      <TeachingSources
        module={module}
        course={course}
        claimIds={beat.claimIds}
      />
      {module.extensionCards
        .filter((c) => c.beatId === beat.id)
        .map((c) => (
          <section
            className="handbook-extension"
            id={`extension-${c.id}`}
            key={c.id}
          >
            <p className="sc-eyebrow">
              Beyond this module · optional extension
            </p>
            <h3>{plainTeaching(c.prompt)}</h3>
            <TeachingText module={module} course={course}>
              {c.answer}
            </TeachingText>
            <TeachingText module={module} course={course}>
              {c.explanation}
            </TeachingText>
            <p>
              <strong>Why it matters:</strong> {c.whyItMatters}
            </p>
            <TeachingSources
              module={module}
              course={course}
              claimIds={c.claimIds}
            />
          </section>
        ))}
      <details>
        <summary>Original worked references</summary>
        <ul>
          {beat.handbook.sourceSectionIds.map((id) => {
            const l = course.modules
              .flatMap((m) => m.lessons)
              .find((l) => l.sections.some((s) => s.id === id));
            return l ? (
              <li key={id}>
                <a
                  href={`${lessonHref(l.id, id)}?from=${encodeURIComponent(beatHref(module.moduleId, beat.id))}`}
                >
                  {l.title} · {l.sections.find((s) => s.id === id)?.title}
                </a>
              </li>
            ) : null;
          })}
        </ul>
      </details>
      <a className="handbook-back" href={beatHref(module.moduleId, beat.id)}>
        Study this beat in the deck →
      </a>
    </article>
  );
}
function ModuleCards({
  module,
  course,
  lessons,
}: {
  module: TeachingModule;
  course: CatalogCourse;
  lessons: LessonBody[];
}) {
  const [scope, setScope] = useState("core"),
    [topic, setTopic] = useState("all"),
    [reviewing, setReviewing] = useState(false);
  const lessonCards = lessons.flatMap((l) => l.cards);
  const core = module.cardLinks.flatMap((l) => {
      const card = lessonCards.find((c) => c.id === l.cardId);
      return card ? [{ ...card, beatId: l.beatId }] : [];
    }),
    all = [...core, ...module.extensionCards];
  const filtered = (
    scope === "core"
      ? core
      : scope === "extension"
        ? module.extensionCards
        : all
  ).filter((c) => topic === "all" || c.conceptIds.includes(topic));
  const concepts = [...module.concepts, ...course.concepts].filter((g) =>
    all.some((c) => c.conceptIds.includes(g.id)),
  );
  return (
    <section className="module-cards">
      <h2>Keep the useful ideas</h2>
      <p>
        Core cards return to this module’s explanations. Beyond cards add
        optional related ideas, with their own teaching and sources.
      </p>
      <div className="card-filters">
        <label className="sc-field">
          Card set
          <select
            className="sc-select"
            value={scope}
            onChange={(e) => {
              setScope(e.target.value);
              setReviewing(false);
            }}
          >
            <option value="core">From this module</option>
            <option value="extension">Beyond this module</option>
            <option value="all">All</option>
          </select>
        </label>
        <label className="sc-field">
          Topic
          <select
            className="sc-select"
            value={topic}
            onChange={(e) => {
              setTopic(e.target.value);
              setReviewing(false);
            }}
          >
            <option value="all">All topics</option>
            {concepts.map((c) => (
              <option key={c.id} value={c.id}>
                {c.term}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p>{filtered.length} cards in this selection.</p>
      {scope !== "core" && (
        <p className="sc-notice">
          Beyond cards are optional. They enter your schedule only when you
          explicitly introduce and rate them.
        </p>
      )}
      <button
        className="sc-btn sc-btn--primary"
        disabled={!filtered.length}
        onClick={() => setReviewing(!reviewing)}
      >
        {reviewing ? "Browse explanations" : "Review this selection"}
      </button>
      {reviewing ? (
        <Review key={`${scope}-${topic}`} cardIds={filtered.map((c) => c.id)} />
      ) : (
        <div className="card-library">
          {filtered.map((c) => (
            <details key={c.id}>
              <summary>{plainTeaching(c.prompt)}</summary>
              <TeachingText module={module} course={course}>
                {c.answer}
              </TeachingText>
              <TeachingText module={module} course={course}>
                {c.explanation}
              </TeachingText>
              {"whyItMatters" in c && (
                <p>
                  <strong>Why it matters:</strong> {String(c.whyItMatters)}
                </p>
              )}
              <TeachingSources
                module={module}
                course={course}
                claimIds={c.claimIds}
              />
              <a
                href={`${beatHref(module.moduleId, c.beatId, "handbook", true)}${"whyItMatters" in c ? `&extension=${c.id}` : ""}`}
              >
                Return to the exact explanation →
              </a>
            </details>
          ))}
        </div>
      )}
    </section>
  );
}
export function ModuleWorkspace({
  id,
  beatId,
  view,
  extensionId,
  detour = false,
}: {
  id: string;
  beatId?: string;
  view?: string;
  extensionId?: string;
  detour?: boolean;
}) {
  const [loaded, setLoaded] = useState<{
      module: TeachingModule;
      lessons: LessonBody[];
    } | null>(null),
    [error, setError] = useState(""),
    [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setError("");
    // The module and the lesson bodies its beats and cards draw on load in
    // parallel; either failure is retried through the same control.
    const entry = teachingIndex.find((m) => m.moduleId === id);
    void Promise.all([
      loadTeachingModule(id),
      Promise.all((entry ? moduleLessonIds(entry) : []).map(loadLessonBody)),
    ])
      .then(([module, lessons]) => {
        if (active) setLoaded({ module, lessons });
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [id, retry]);
  if (error)
    return (
      <div role="alert">
        <h1>That module could not open</h1>
        <p>{error}</p>
        <button
          className="sc-btn sc-btn--secondary"
          onClick={() => setRetry((n) => n + 1)}
        >
          Retry module
        </button>
        <a href="#/courses">Browse courses</a>
      </div>
    );
  if (!loaded || loaded.module.moduleId !== id)
    return <p role="status">Opening the teaching module…</p>;
  return (
    <ModuleView
      key={id}
      module={loaded.module}
      lessons={loaded.lessons}
      beatId={beatId}
      view={view}
      extensionId={extensionId}
      detour={detour}
    />
  );
}
function ModuleView({
  module,
  lessons,
  beatId,
  view: requestedView,
  extensionId,
  detour,
}: {
  module: TeachingModule;
  lessons: LessonBody[];
  beatId?: string;
  view?: string;
  extensionId?: string;
  detour: boolean;
}) {
  const { data, store } = useStudy(),
    course = courses.find((c) => c.id === module.courseId)!;
  const recent = Object.values(data.beatPositions)
    .filter(
      (p) =>
        p.moduleId === module.moduleId &&
        module.beats.some((b) => b.id === p.beatId),
    )
    .sort(
      (a, b) =>
        b.updatedAt.localeCompare(a.updatedAt) ||
        a.beatId.localeCompare(b.beatId),
    )[0];
  const fallback =
    data.beatResume?.moduleId === module.moduleId &&
    module.beats.some((b) => b.id === data.beatResume?.beatId)
      ? data.beatResume.beatId
      : (recent?.beatId ?? module.beats[0].id);
  const beat = module.beats.find((b) => b.id === (beatId ?? fallback)),
    view = (
      ["deck", "handbook", "cards"].includes(requestedView ?? "")
        ? requestedView
        : "deck"
    ) as BeatPosition["view"];
  const [media, setMedia] = useState<TeachingMedia[]>([]),
    [mediaError, setMediaError] = useState("");
  const stateRef = useRef({ beat, view, detour });
  stateRef.current = { beat, view, detour };
  const position = beat ? data.beatPositions[beat.id] : undefined,
    visual = module.visuals.find((v) => v.id === beat?.visualId),
    index = module.beats.findIndex((b) => b.id === beat?.id);
  const save = (patch: Partial<BeatPosition>) => {
    const current = stateRef.current;
    if (!current.beat) return;
    const b = current.beat,
      at = nowISO();
    void store.change((s) => {
      const p: BeatPosition = {
        ...(s.beatPositions[b.id] ?? {
          courseId: course.id,
          moduleId: module.moduleId,
          beatId: b.id,
          version: b.version,
          visualStateId: module.visuals.find((v) => v.id === b.visualId)!
            .states[0].id,
          view: current.view,
          handbookOpen: false,
          handbookAnchor: b.id,
          offset: 0,
        }),
        ...patch,
        view: current.view,
        version: b.version,
        viewOffsets: {
          deck: 0,
          handbook: 0,
          cards: 0,
          ...s.beatPositions[b.id]?.viewOffsets,
          ...(patch.offset !== undefined
            ? { [current.view]: patch.offset }
            : {}),
        },
        updatedAt: at,
      };
      return {
        ...s,
        beatPositions: { ...s.beatPositions, [b.id]: p },
        beatResume: current.detour ? s.beatResume : p,
      };
    });
  };
  const saveRef = useRef(save);
  saveRef.current = save;
  useEffect(() => {
    let active = true;
    void loadTeachingMedia()
      .then((m) => {
        if (active) setMedia(m.filter((v) => v.moduleId === module.moduleId));
      })
      .catch(() => {
        if (active)
          setMediaError(
            "Video references could not load. The illustrated lesson remains available; reload to retry.",
          );
      });
    return () => {
      active = false;
    };
  }, [module.moduleId]);
  useEffect(() => {
    if (!beat) return;
    const old = store.getSnapshot().data.beatPositions[beat.id];
    saveRef.current({ view, version: beat.version });
    let timer: ReturnType<typeof setTimeout> | undefined,
      ready = false;
    const raf = requestAnimationFrame(() => {
      if (view === "handbook" && (!old?.viewOffsets || detour))
        document
          .getElementById(
            extensionId &&
              module.extensionCards.some(
                (c) => c.id === extensionId && c.beatId === beat.id,
              )
              ? `extension-${extensionId}`
              : `handbook-${beat.id}`,
          )
          ?.scrollIntoView();
      else
        window.scrollTo(
          0,
          old?.viewOffsets?.[view] ?? (old?.view === view ? old.offset : 0),
        );
      ready = true;
    });
    const scroll = () => {
      if (!ready) return;
      clearTimeout(timer);
      timer = setTimeout(
        () => saveRef.current({ offset: Math.min(100000, window.scrollY) }),
        250,
      );
    };
    window.addEventListener("scroll", scroll, { passive: true });
    return () => {
      cancelAnimationFrame(raf);
      clearTimeout(timer);
      window.removeEventListener("scroll", scroll);
    };
  }, [beat?.id, view, store, extensionId]);
  if (!beat || !visual)
    return (
      <div>
        <h1>That teaching beat is unavailable</h1>
        <p>Your notes and history are retained.</p>
        <a href={beatHref(module.moduleId, module.beats[0].id)}>
          Open the module’s first beat
        </a>
      </div>
    );
  const completed = data.completions[`beat-${beat.id}`],
    revised = completed?.completed && completed.contentVersion !== beat.version,
    anchor =
      module.beats.find((b) => b.id === position?.handbookAnchor) ?? beat;
  const currentHref = beatHref(module.moduleId, beat.id, view, detour),
    activeMedia = media.filter((v) => v.beatId === beat.id);
  return (
    <div
      className={`teacher-workspace ${data.settings.focus ? "teacher-focus" : ""}`}
    >
      <header className="module-top">
        <a href={`#/course/${course.id}`}>← Course map</a>
        <p className="sc-eyebrow">
          Module {course.modules.findIndex((m) => m.id === module.moduleId) + 1}{" "}
          of {course.modules.length}
        </p>
        <h1 tabIndex={-1}>{module.title}</h1>
        <nav className="teaching-tabs" aria-label="Module views">
          {(["deck", "handbook", "cards"] as const).map((v) => (
            <a
              key={v}
              aria-current={view === v ? "page" : undefined}
              href={beatHref(module.moduleId, beat.id, v, detour)}
            >
              {v[0].toUpperCase() + v.slice(1)}
            </a>
          ))}
        </nav>
      </header>
      <div className="module-tools">
        <span>
          {view === "deck"
            ? `Beat ${index + 1} of ${module.beats.length}`
            : view === "handbook"
              ? "Your complete module reference"
              : "Recall and explanation"}
        </span>
        <button
          className="sc-btn sc-btn--ghost"
          onClick={() => {
            const updatedAt = nowISO();
            void store.change((s) => ({
              ...s,
              settings: { ...s.settings, focus: !s.settings.focus, updatedAt },
            }));
          }}
        >
          {data.settings.focus ? "Exit focus mode" : "Focus mode"}
        </button>
        <details className="module-options">
          <summary>Reading options</summary>
          <label className="sc-check">
            <input
              type="checkbox"
              checked={data.settings.showSamajh}
              onChange={(e) => {
                const showSamajh = e.target.checked,
                  updatedAt = nowISO();
                void store.change((s) => ({
                  ...s,
                  settings: { ...s.settings, showSamajh, updatedAt },
                }));
              }}
            />
            Show Samajh analogies
          </label>
          <a href="#/settings">Theme and session preferences</a>
        </details>
      </div>
      {view === "deck" ? (
        <div
          className={`deck-layout ${position?.handbookOpen ? "with-handbook" : ""}`}
        >
          <nav className="beat-rail" aria-label="Teaching beats">
            <label className="mobile-beat-picker sc-field">
              Jump to a beat
              <select
                className="sc-select"
                value={beat.id}
                onChange={(e) => {
                  location.hash = beatHref(
                    module.moduleId,
                    e.target.value,
                    "deck",
                    detour,
                  );
                }}
              >
                {module.beats.map((b, i) => (
                  <option key={b.id} value={b.id}>
                    {i + 1}. {b.title}
                  </option>
                ))}
              </select>
            </label>
            <ol>
              {module.beats.map((b, i) => (
                <li key={b.id}>
                  <a
                    aria-current={b.id === beat.id ? "step" : undefined}
                    href={beatHref(module.moduleId, b.id, "deck", detour)}
                  >
                    <span>{i + 1}</span>
                    {b.title}
                    {data.completions[`beat-${b.id}`]?.completed && (
                      <span className="sc-sr-only"> · marked complete</span>
                    )}
                  </a>
                </li>
              ))}
            </ol>
          </nav>
          <div className="deck-body">
            <article className="teaching-beat">
              <p className="beat-outcome">{beat.outcome}</p>
              <h2 tabIndex={-1}>{beat.title}</h2>
              <div className="beat-explanation">
                <TeachingText module={module} course={course}>
                  {beat.explanation}
                </TeachingText>
              </div>
              <Visual
                key={beat.visualId}
                visual={visual}
                stateId={position?.visualStateId}
                onState={(visualStateId) => save({ visualStateId })}
              />
              {data.settings.showSamajh && beat.samajh && (
                <details className="samajh">
                  <summary>Samajh · another way to picture it</summary>
                  <p lang="hi-Latn">{beat.samajh.text}</p>
                  <p>
                    <strong>The connection:</strong> {beat.samajh.mapping}
                  </p>
                  <p>
                    <strong>Where the analogy stops:</strong>{" "}
                    {beat.samajh.boundary}
                  </p>
                </details>
              )}
              {activeMedia.map((item) => (
                <MediaReference
                  key={item.id}
                  item={item}
                  module={module}
                  course={course}
                />
              ))}
              {beat.questionIds.map((q) => (
                <BeatCheck
                  key={q}
                  module={module}
                  course={course}
                  beat={beat}
                  questionId={q}
                  lessons={lessons}
                />
              ))}
              {mediaError && <p className="sc-hint">{mediaError}</p>}
              <div className="beat-context-tools">
                <button
                  className="sc-btn sc-btn--ghost"
                  onClick={() =>
                    save({
                      handbookOpen: !position?.handbookOpen,
                      handbookAnchor: beat.id,
                    })
                  }
                >
                  {position?.handbookOpen
                    ? "Close handbook beside this beat"
                    : "Open handbook beside this beat"}
                </button>
                <a
                  href={beatHref(module.moduleId, beat.id, "handbook", true)}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Handbook in a new tab ↗
                </a>
              </div>
              <details className="beat-notes">
                <summary>Keep a note or question</summary>
                <NoteEditor
                  courseId={course.id}
                  lessonId={beat.lessonId}
                  sectionId={beat.sectionId}
                  noteId={`note-${beat.id}`}
                />
              </details>
              <TeachingSources
                module={module}
                course={course}
                claimIds={beat.claimIds}
              />
              {revised && (
                <p className="sc-notice">
                  Material revised since your earlier completion.{" "}
                  {beat.changeNote} Your previous work is retained.
                </p>
              )}
              <div className="beat-completion">
                <button
                  className="sc-btn sc-btn--secondary"
                  onClick={() => {
                    const id = `beat-${beat.id}`,
                      updatedAt = nowISO();
                    void store.change((s) => ({
                      ...s,
                      completions: {
                        ...s.completions,
                        [id]: {
                          id,
                          courseId: course.id,
                          lessonId: beat.lessonId,
                          sectionId: beat.id,
                          completed: revised || !s.completions[id]?.completed,
                          contentVersion: beat.version,
                          updatedAt,
                        },
                      },
                    }));
                  }}
                >
                  {completed?.completed && !revised
                    ? "Marked complete · undo"
                    : "Mark this beat complete"}
                </button>
                <span>Only your choice records completion.</span>
              </div>
            </article>
            <nav className="beat-pagination" aria-label="Continue learning">
              {index > 0 ? (
                <a
                  className="sc-btn sc-btn--secondary"
                  href={beatHref(
                    module.moduleId,
                    module.beats[index - 1].id,
                    "deck",
                    detour,
                  )}
                >
                  ← Previous beat
                </a>
              ) : (
                <span />
              )}
              {index < module.beats.length - 1 ? (
                <a
                  className="sc-btn sc-btn--primary"
                  href={beatHref(
                    module.moduleId,
                    module.beats[index + 1].id,
                    "deck",
                    detour,
                  )}
                >
                  Next beat →
                </a>
              ) : (
                <a
                  className="sc-btn sc-btn--primary"
                  href={beatHref(module.moduleId, beat.id, "cards", detour)}
                >
                  Review this module’s cards →
                </a>
              )}
            </nav>
            {index === module.beats.length - 1 && (
              <ModuleRecap module={module} course={course} />
            )}
          </div>
          {position?.handbookOpen && (
            <aside
              className="handbook-pane"
              aria-label="Handbook beside the deck"
            >
              <div className="pane-toolbar">
                <label className="sc-field">
                  Handbook section
                  <select
                    className="sc-select"
                    value={anchor.id}
                    onChange={(e) => save({ handbookAnchor: e.target.value })}
                  >
                    {module.beats.map((b) => (
                      <option value={b.id} key={b.id}>
                        {b.title}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  className="sc-btn sc-btn--ghost"
                  onClick={() => save({ handbookOpen: false })}
                >
                  Close handbook
                </button>
              </div>
              <HandbookArticle module={module} course={course} beat={anchor} />
            </aside>
          )}
        </div>
      ) : view === "handbook" ? (
        <div className="module-handbook">
          <div className="handbook-tools">
            <button
              className="sc-btn sc-btn--secondary"
              onClick={() => window.print()}
            >
              Print handbook
            </button>
            <a href={beatHref(module.moduleId, beat.id)}>Return to the deck</a>
          </div>
          <nav aria-label="Module handbook contents">
            <ol>
              {module.beats.map((b) => (
                <li key={b.id}>
                  <a
                    href={`#handbook-${b.id}`}
                    onClick={(e) => {
                      e.preventDefault();
                      document
                        .getElementById(`handbook-${b.id}`)
                        ?.scrollIntoView();
                      save({ handbookAnchor: b.id });
                    }}
                  >
                    {b.title}
                  </a>
                </li>
              ))}
            </ol>
          </nav>
          {module.beats.map((b) => (
            <HandbookArticle
              key={b.id}
              module={module}
              course={course}
              beat={b}
            />
          ))}
          <ModuleRecap module={module} course={course} />
        </div>
      ) : (
        <ModuleCards module={module} course={course} lessons={lessons} />
      )}
      <details className="module-foundations">
        <summary>Module outcomes, starting assumptions and bridges</summary>
        <ul>
          {module.outcomes.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
        <ul>
          {module.startingAssumptions.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
        {module.optionalBridgeLessonIds.map((id) => (
          <p key={id}>
            <a
              href={`${lessonHref(id)}?from=${encodeURIComponent(currentHref)}`}
            >
              Optional bridge: {findLesson(id)?.lesson.title}
            </a>
          </p>
        ))}
      </details>
      <SaveStatus />
    </div>
  );
}
function ModuleRecap({
  module,
  course,
}: {
  module: TeachingModule;
  course: CatalogCourse;
}) {
  return (
    <section className="module-recap">
      <h2>{module.recap.title}</h2>
      <TeachingText module={module} course={course}>
        {module.recap.markdown}
      </TeachingText>
      <Visual
        visual={module.visuals.find((v) => v.id === module.recap.visualId)!}
      />
      <h3>{module.appliedTask.title}</h3>
      <TeachingText module={module} course={course}>
        {module.appliedTask.prompt}
      </TeachingText>
      <Draft
        id={`task-${module.moduleId}`}
        targetId={module.moduleId}
        courseId={course.id}
        label="Your applied-task reasoning"
      />
      <details>
        <summary>Compare with the worked solution</summary>
        <TeachingText module={module} course={course}>
          {module.appliedTask.modelAnswer}
        </TeachingText>
        <TeachingText module={module} course={course}>
          {module.appliedTask.reasoning}
        </TeachingText>
      </details>
      <p>For more practice:</p>
      <ul>
        {module.scenarioIds.map((id) => (
          <li key={id}>
            <a
              href={`#/practice/${id}?from=${encodeURIComponent(beatHref(module.moduleId, module.beats.at(-1)!.id))}`}
            >
              {course.scenarios.find((s) => s.id === id)?.title}
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}
export function CourseHandbook({ id }: { id: string }) {
  const course = courses.find((c) => c.id === id),
    [modules, setModules] = useState<TeachingModule[]>([]),
    [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    void Promise.all(
      teachingIndex
        .filter((m) => m.courseId === id)
        .map((m) => loadTeachingModule(m.moduleId)),
    )
      .then((m) => {
        if (active) setModules(m);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [id]);
  if (!course) return <h1>Course unavailable</h1>;
  return (
    <div className="course-handbook">
      <a href={`#/course/${id}`}>← Course map</a>
      <h1 tabIndex={-1}>{course.title}: handbook</h1>
      <p>
        The full written course reference, with the same concepts, visuals and
        sources as the deck.
      </p>
      <div className="handbook-tools">
        <button
          className="sc-btn sc-btn--secondary"
          disabled={!modules.length}
          onClick={() => window.print()}
        >
          Print course handbook
        </button>
      </div>
      <nav aria-label="Course handbook contents">
        <ol>
          {course.modules.map((m) => (
            <li key={m.id}>
              <a
                href={`#chapter-${m.id}`}
                onClick={(e) => {
                  e.preventDefault();
                  document.getElementById(`chapter-${m.id}`)?.scrollIntoView();
                }}
              >
                {m.title}
              </a>
            </li>
          ))}
        </ol>
      </nav>
      {error && <p role="alert">{error}</p>}
      {!modules.length && !error && (
        <p role="status">Assembling the course handbook…</p>
      )}
      {course.modules.map((m) => {
        const t = modules.find((t) => t.moduleId === m.id);
        return t ? (
          <section
            className="handbook-chapter"
            id={`chapter-${m.id}`}
            key={m.id}
          >
            <h2>{t.title}</h2>
            {t.beats.map((b) => (
              <HandbookArticle key={b.id} module={t} course={course} beat={b} />
            ))}
            <ModuleRecap module={t} course={course} />
          </section>
        ) : null;
      })}
    </div>
  );
}
