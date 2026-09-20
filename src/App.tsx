import { useEffect, useState } from "react";
import { beatHref, findLesson, lessonHref } from "./catalog";
import { Learn, Roadmap } from "./hub";
import {
  TeacherToday,
  TeacherCourses,
  ModuleWorkspace,
  CourseHandbook,
} from "./teaching";
import { Notebook, Search, Settings } from "./notebook-settings";
import { Practice, Review } from "./practice-review";
import { Reader } from "./reader";
import { PageTitle, StorageNotice, baseAsset, useStudy } from "./ui";

export default function App() {
  const [hash, setHash] = useState(location.hash || "#/"),
    { data, status } = useStudy();
  const [route, query] = hash.split("?"),
    params = new URLSearchParams(query),
    pathId = params.get("path") ?? undefined,
    fromValue = params.get("from"),
    from =
      fromValue &&
      /^#\/(?:lesson|module)\/[a-z0-9-]+(?:\/[a-z0-9-]+)?(?:\?(?:path|view)=[a-z0-9-]+(?:&detour=1)?)?$/.test(
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
    if (page !== "lesson" && page !== "module") {
      window.scrollTo(0, 0);
      document.querySelector<HTMLElement>("main h1")?.focus();
    }
    document.title = `${page === "lesson" ? (findLesson(id)?.lesson.title ?? "Lesson") : page[0].toUpperCase() + page.slice(1)} · SpicyBrain`;
  }, [page, id]);
  const nav = [
    ["start", "Today"],
    ["courses", "Courses"],
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
                  (p === "courses" &&
                    [
                      "courses",
                      "course",
                      "lesson",
                      "path",
                      "practice",
                      "module",
                      "handbook",
                      "learn",
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
            href={`#/search${from ? `?from=${encodeURIComponent(from)}` : page === "module" ? `?from=${encodeURIComponent(beatHref(id, section, params.get("view") ?? "deck"))}` : page === "lesson" ? `?from=${encodeURIComponent(lessonHref(id, data.positions[id]?.sectionId ?? section, pathId))}` : ""}`}
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
            <a href={from}>← Return to your saved learning context</a>
          </p>
        )}
        {status === "loading" ? (
          <p role="status">Opening your learning space…</p>
        ) : page === "start" ? (
          <TeacherToday />
        ) : page === "learn" ? (
          <Learn
            view={id}
            from={from}
            playbook={params.get("playbook") ?? undefined}
          />
        ) : page === "path" ? (
          <Roadmap id={id} />
        ) : page === "courses" || page === "course" ? (
          <TeacherCourses id={id} />
        ) : page === "module" ? (
          <ModuleWorkspace
            id={id}
            beatId={section}
            view={params.get("view") ?? undefined}
            extensionId={params.get("extension") ?? undefined}
            detour={params.get("detour") === "1" || !!from}
          />
        ) : page === "handbook" ? (
          <CourseHandbook id={id} />
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
