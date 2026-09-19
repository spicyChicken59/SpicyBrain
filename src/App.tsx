import { useEffect, useState } from "react";
import { courses, findLesson, lessonHref } from "./catalog";
import { Today, Learn, Roadmap, completionLabel } from "./hub";
import { Notebook, Search, Settings } from "./notebook-settings";
import { Practice, Review } from "./practice-review";
import { Reader } from "./reader";
import { MD, PageTitle, StorageNotice, baseAsset, useStudy } from "./ui";

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
                      {completionLabel(l, data)}{" "}
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
  const [route, query] = hash.split("?"),
    params = new URLSearchParams(query),
    pathId = params.get("path") ?? undefined,
    fromValue = params.get("from"),
    from =
      fromValue &&
      /^#\/lesson\/[a-z0-9-]+(?:\/[a-z0-9-]+)?(?:\?path=[a-z0-9-]+)?$/.test(
        fromValue,
      )
        ? fromValue
        : undefined,
    parts = route.slice(2).split("/"),
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
    ["start", "Today"],
    ["learn", "Learn"],
    ["review", "Review"],
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
                  (p === "learn" &&
                    [
                      "courses",
                      "course",
                      "lesson",
                      "path",
                      "practice",
                    ].includes(page))
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
            href={`#/search${from ? `?from=${encodeURIComponent(from)}` : page === "lesson" ? `?from=${encodeURIComponent(lessonHref(id, data.positions[id]?.sectionId ?? section, pathId))}` : ""}`}
            aria-current={page === "search" ? "page" : undefined}
          >
            Search
          </a>
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
        {from && (
          <p className="detour-return">
            <a href={from}>← Return to your learning path and saved topic</a>
          </p>
        )}
        {status === "loading" ? (
          <p role="status">Opening your learning space…</p>
        ) : page === "start" ? (
          <Today />
        ) : page === "learn" ? (
          <Learn
            view={id}
            from={from}
            playbook={params.get("playbook") ?? undefined}
          />
        ) : page === "path" ? (
          <Roadmap id={id} />
        ) : page === "courses" || page === "course" ? (
          <Courses id={id} />
        ) : page === "lesson" ? (
          <Reader
            key={`${id}-${pathId ?? "direct"}`}
            id={id}
            sectionId={section}
            pathId={pathId}
            from={from}
          />
        ) : page === "practice" ? (
          <Practice key={id ?? "all"} id={id} />
        ) : page === "review" ? (
          <Review key={id ?? "all"} lessonId={id} />
        ) : page === "search" ? (
          <Search from={from} />
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
              Your study data is safe. <a href="#/">Return to Today</a> or{" "}
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
