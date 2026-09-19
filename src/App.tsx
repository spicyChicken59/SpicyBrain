import { useEffect, useState } from "react";
import { courses, findLesson, lessonHref, cards } from "./catalog";
import { Notebook, Search, Settings } from "./notebook-settings";
import { Practice, Review } from "./practice-review";
import { Reader } from "./reader";
import { reviewQueue } from "./study";
import { MD, PageTitle, StorageNotice, baseAsset, useStudy } from "./ui";

function Start() {
  const { data } = useStudy();
  const first = courses[0]?.modules[0]?.lessons[0],
    resume = data.resume,
    entry = resume ? findLesson(resume.lessonId) : null,
    due = reviewQueue(cards, data, new Date().toISOString(), 100000);
  return (
    <>
      <div className="start-hero">
        <p className="sc-eyebrow">your space to make things click</p>
        <h1>
          {entry
            ? "Pick up the thread."
            : "Learn it. See it.\nUse it. Remember it."}
        </h1>
        <p className="hero-dek">
          {entry
            ? "One idea at a time. Your place is right here."
            : "Clear explanations. Useful practice. Ideas that stay with you."}
        </p>
        <div className="continue-panel">
          <p className="sc-eyebrow">
            {entry ? "where you left off" : "start here"}
          </p>
          <h2>{entry?.lesson.title ?? courses[0]?.title}</h2>
          <p>
            {entry
              ? `${entry.module.title} · ${entry.lesson.sections.find((s) => s.id === resume?.sectionId)?.title ?? "Lesson beginning"}`
              : courses[0]?.subtitle}
          </p>
          {first && (
            <a
              className="sc-btn sc-btn--primary"
              href={
                entry
                  ? lessonHref(entry.lesson.id, resume?.sectionId)
                  : lessonHref(first.id)
              }
            >
              {entry ? "Resume learning" : "Start learning"}{" "}
              <span aria-hidden="true">→</span>
            </a>
          )}
          {!entry && (
            <p className="sc-hint">
              No study activity yet. Start anywhere; nothing is locked.
            </p>
          )}
          {resume && !entry && (
            <p>
              Your previous lesson was removed. Your notes and history remain in
              Notebook.
            </p>
          )}
        </div>
      </div>
      <div className="start-secondary">
        <a href="#/courses">
          <span className="sc-eyebrow">choose your path</span>
          <h2>Explore the course</h2>
          <p>See the map. Skip what you know.</p>
          <span aria-hidden="true">→</span>
        </a>
        <a href="#/review">
          <span className="sc-eyebrow">a small review</span>
          <h2>
            {due.length
              ? `${due.length} cards to revisit`
              : "Bring an idea back"}
          </h2>
          <p>
            {due.length
              ? "A manageable session, on your terms."
              : "Introduce a few cards after a lesson."}
          </p>
          <span aria-hidden="true">→</span>
        </a>
        <a href="#/practice">
          <span className="sc-eyebrow">try the work</span>
          <h2>Make one decision</h2>
          <p>A fictional customer. A practical task.</p>
          <span aria-hidden="true">→</span>
        </a>
      </div>
      <div className="start-footnote">
        <p className="sc-eyebrow">a practical role ramp</p>
        <p>
          Independent learning material for someone new to Databricks pre-sales
          field engineering. Learn the platform, ask better questions, and build
          useful customer-facing judgment.
        </p>
        <p className="sc-muted">
          Not official Databricks onboarding, a credential, or an employer
          assessment.
        </p>
      </div>
    </>
  );
}
function Courses({ id }: { id?: string }) {
  const { data } = useStudy(),
    course = courses.find((c) => c.id === id);
  if (id && !course)
    return (
      <>
        <PageTitle
          eyebrow="course unavailable"
          title="That course is not in this catalog."
        />
        <a href="#/courses">Browse current courses</a>
      </>
    );
  if (!course)
    return (
      <>
        <PageTitle eyebrow="learn something useful" title="Your courses">
          <p>
            Complete learning paths, built around understanding and practical
            work.
          </p>
        </PageTitle>
        {courses.map((c) => (
          <a className="course-card" key={c.id} href={`#/course/${c.id}`}>
            <div>
              <p className="sc-eyebrow">
                {c.modules.length} modules ·{" "}
                {c.modules.reduce((n, m) => n + m.lessons.length, 0)} lessons
              </p>
              <h2>{c.title}</h2>
              <p>{c.subtitle}</p>
              <p>{c.summary}</p>
              <span className="course-link">Explore this course →</span>
            </div>
            <div className="course-cover sc-on-ink" aria-hidden="true">
              <span>
                Learn.
                <br />
                See.
                <br />
                Use.
                <br />
                Remember.
              </span>
              <span className="cover-rule" />
            </div>
          </a>
        ))}
      </>
    );
  return (
    <>
      <a className="sc-link--quiet" href="#/courses">
        ← All courses
      </a>
      <PageTitle eyebrow="your course map" title={course.title}>
        <p>{course.subtitle}</p>
      </PageTitle>
      <div className="course-intro">
        <p>{course.summary}</p>
        <details className="sc-details">
          <summary>Outcomes, prerequisites & optional refreshers</summary>
          <h2>What you will practice</h2>
          <ul>
            {course.objectives.map((o) => (
              <li key={o}>{o}</li>
            ))}
          </ul>
          <p>
            Prerequisites:{" "}
            {course.prerequisiteIds.length
              ? course.prerequisiteIds
                  .map(
                    (id) =>
                      findLesson(id)?.lesson.title ??
                      courses.find((c) => c.id === id)?.title ??
                      id,
                  )
                  .join(", ")
              : "Curiosity and basic familiarity with data. Use the optional refreshers whenever useful."}{" "}
            Nothing is locked.
          </p>
          {course.refreshers.map((r) => (
            <details className="sc-details" key={r.title}>
              <summary>{r.title}</summary>
              <MD>{r.markdown}</MD>
            </details>
          ))}
        </details>
      </div>
      <div className="course-map">
        {course.modules.map((m, i) => (
          <section className="module-block" key={m.id}>
            <div className="module-heading">
              <span className="module-number">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div>
                <h2>{m.title}</h2>
                <p>{m.summary}</p>
              </div>
            </div>
            <ol>
              {m.lessons.map((l) => (
                <li key={l.id}>
                  <a href={lessonHref(l.id)}>
                    <span>
                      <strong>{l.title}</strong>
                      <span>{l.summary}</span>
                    </span>
                    <span className="lesson-state">
                      {data.completions[`complete-${l.id}`]?.completed
                        ? "Complete"
                        : `~${l.estimatedMinutes} min`}{" "}
                      <span aria-hidden="true">→</span>
                    </span>
                  </a>
                </li>
              ))}
            </ol>
            <a className="module-practice" href={`#/practice/${m.scenarioId}`}>
              Apply this module →
            </a>
          </section>
        ))}
      </div>
      {course.capstoneId && (
        <div className="sc-actionbar">
          <p>Bring the course ideas together in the capstone.</p>
          <a
            className="sc-btn sc-btn--primary"
            href={`#/practice/${course.capstoneId}`}
          >
            Open the capstone →
          </a>
        </div>
      )}
      <p className="sc-hint">
        Reading times are estimates. Completion is your explicit choice; it does
        not establish mastery. Sources checked{" "}
        {course.sources[0]?.accessDate ?? course.reviewDate}.
      </p>
    </>
  );
}
export default function App() {
  const [hash, setHash] = useState(location.hash || "#/"),
    { data, status } = useStudy();
  const parts = hash.slice(2).split("/"),
    page = parts[0] || "start",
    id = parts[1],
    section = parts[2];
  useEffect(() => {
    const handler = () => setHash(location.hash || "#/");
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);
  useEffect(() => {
    if (data.settings.theme === "auto")
      delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = data.settings.theme;
  }, [data.settings.theme]);
  useEffect(() => {
    if (page !== "lesson") {
      window.scrollTo(0, 0);
      document.querySelector<HTMLElement>("main h1")?.focus();
    }
    document.title = `${page === "lesson" ? (findLesson(id)?.lesson.title ?? "Lesson") : page[0].toUpperCase() + page.slice(1)} · SpicyBrain`;
  }, [page, id]);
  const nav = [
    ["start", "Start"],
    ["courses", "Courses"],
    ["practice", "Practice"],
    ["review", "Review"],
    ["search", "Search"],
    ["notebook", "Notebook"],
  ];
  return (
    <>
      <a
        className="sc-skip"
        href="#main"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("main")?.focus();
        }}
      >
        Skip to content
      </a>
      <header className="sc-masthead">
        <div className="masthead-inner">
          <a className="sc-brand" href="#/">
            <img
              className="sc-mark"
              src={baseAsset("design-system/assets/sc-mark-color-dark.svg")}
              alt=""
            />
            <span className="sc-brand__name">SpicyBrain</span>
          </a>
          <nav className="sc-nav" aria-label="Main navigation">
            {nav.map(([p, title]) => (
              <a
                key={p}
                href={p === "start" ? "#/" : `#/${p}`}
                aria-current={
                  page === p ||
                  (p === "courses" && (page === "course" || page === "lesson"))
                    ? "page"
                    : undefined
                }
              >
                {title}
              </a>
            ))}
          </nav>
          <a
            className="settings-link"
            href="#/settings"
            aria-current={page === "settings" ? "page" : undefined}
          >
            Settings
          </a>
        </div>
      </header>
      <main
        className={`sc-wrap main-wrap ${page === "lesson" ? "reader-wrap" : ""}`}
        id="main"
        tabIndex={-1}
      >
        <StorageNotice />
        {status === "loading" ? (
          <p role="status">Opening your learning space…</p>
        ) : page === "start" ? (
          <Start />
        ) : page === "courses" || page === "course" ? (
          <Courses id={id} />
        ) : page === "lesson" ? (
          <Reader id={id} sectionId={section} />
        ) : page === "practice" ? (
          <Practice key={id ?? "all"} id={id} />
        ) : page === "review" ? (
          <Review key={id ?? "all"} lessonId={id} />
        ) : page === "search" ? (
          <Search />
        ) : page === "notebook" ? (
          <Notebook id={id} />
        ) : page === "settings" ? (
          <Settings />
        ) : (
          <>
            <PageTitle
              eyebrow="page unavailable"
              title="Let’s find your way back."
            />
            <p>
              Your study data is safe. <a href="#/">Return to Start</a> or{" "}
              <a href="#/notebook">open Notebook</a>.
            </p>
          </>
        )}
      </main>
      <footer className="sc-foot">
        <div className="footer-inner">
          <p>
            Learn it. See it. Use it. Remember it.
            <br />
            <span>Independent learning · study data stays in your browser</span>
          </p>
          <a
            className="sc-watermark"
            href="https://github.com/spicyChicken59"
            target="_blank"
            rel="noopener noreferrer"
          >
            <img
              className="sc-mark"
              src={baseAsset("design-system/assets/sc-mark-mono-cream.svg")}
              alt=""
            />
            <span className="sc-watermark__name">SpicyChicken</span>
          </a>
        </div>
      </footer>
    </>
  );
}
