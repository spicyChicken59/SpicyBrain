import { useEffect, useState } from "react";
import {
  cards,
  courses,
  defaultPath,
  findLesson,
  lessonHref,
  paths,
} from "./catalog";
import { pathLessonHref, pathForLesson } from "./paths";
import type { Lesson } from "./content-schema";
import type { StudyState } from "./study";
import { reviewQueue } from "./study";
import { PageTitle, useStudy } from "./ui";

export function completionLabel(lesson: Lesson, data: StudyState) {
  const record = data.completions[`complete-${lesson.id}`];
  if (!record?.completed) return "Ready to explore";
  return record.contentVersion === lesson.contentVersion
    ? "Marked complete"
    : "Revised since completion";
}
export function Today() {
  const { data } = useStudy();
  const resume = data.resume,
    entry = resume && findLesson(resume.lessonId);
  const path = paths.find((p) => p.id === resume?.pathId);
  const due = reviewQueue(cards, data, new Date().toISOString(), 100000);
  return (
    <>
      <div className="start-hero">
        <p className="sc-eyebrow">a little understanding, carried forward</p>
        <h1>
          {entry ? "Pick up the thread." : "Make complicated\nthings click."}
        </h1>
        <p className="hero-dek">
          {entry
            ? "Your saved place. One useful next step."
            : "Understand a subject. Work through an example. Put the idea to use."}
        </p>
        <div className="continue-panel">
          <p className="sc-eyebrow">
            {entry ? "where you left off" : "a path to begin with"}
          </p>
          <h2>
            {entry?.lesson.title ??
              defaultPath?.title ??
              "Explore your learning library"}
          </h2>
          <p>
            {entry
              ? (entry.lesson.sections.find((s) => s.id === resume?.sectionId)
                  ?.title ?? "Topic beginning")
              : (defaultPath?.summary ?? "Choose a topic and start anywhere.")}
          </p>
          {path && (
            <p className="sc-hint">
              In <a href={`#/path/${path.id}`}>{path.title}</a>
            </p>
          )}
          {resume?.pathId && !path && (
            <p className="sc-notice">
              Your saved roadmap is unavailable. The topic and your history
              remain accessible.
            </p>
          )}
          <a
            className="sc-btn sc-btn--primary"
            href={
              entry
                ? lessonHref(entry.lesson.id, resume?.sectionId, resume?.pathId)
                : defaultPath
                  ? `#/path/${defaultPath.id}`
                  : "#/learn/topics"
            }
          >
            {entry
              ? "Resume learning"
              : defaultPath
                ? "Explore this path"
                : "Browse topics"}{" "}
            <span aria-hidden="true">→</span>
          </a>
          {!resume && (
            <p className="sc-hint">
              No study activity yet. Start anywhere; nothing is locked.
            </p>
          )}
          {resume && !entry && (
            <p>
              Your saved topic is unavailable. Its notes and history remain in
              Notebook; choose a new topic when you are ready.
            </p>
          )}
        </div>
      </div>
      <div className="start-secondary">
        <a href="#/learn/topics">
          <span className="sc-eyebrow">follow your curiosity</span>
          <h2>Browse topics</h2>
          <p>Go directly to an explanation you need.</p>
          <span aria-hidden="true">→</span>
        </a>
        <a href="#/review">
          <span className="sc-eyebrow">bring an idea back</span>
          <h2>
            {due.length ? `${due.length} cards to revisit` : "A small review"}
          </h2>
          <p>
            {due.length
              ? "Your scheduled and revised cards, in a bounded session."
              : "Introduce cards from a topic when you choose."}
          </p>
          <span aria-hidden="true">→</span>
        </a>
        <a href="#/learn/playbooks">
          <span className="sc-eyebrow">find a useful reference</span>
          <h2>Work through a task</h2>
          <p>Quick routes into the reasoning behind a decision.</p>
          <span aria-hidden="true">→</span>
        </a>
      </div>
      <div className="start-footnote">
        <p>
          Independent learning, practical examples, and room to think.
          Completion, answers, and review history are separate records of your
          work.
        </p>
        <p className="sc-muted">
          Study data stays in this browser. There is no automatic cross-device
          sync; export a backup in Settings.
        </p>
      </div>
    </>
  );
}

function LearnNav({ view, from }: { view: string; from?: string }) {
  const suffix = from ? `?from=${encodeURIComponent(from)}` : "";
  return (
    <nav className="learn-nav" aria-label="Learn views">
      {[
        ["roadmaps", "Roadmaps"],
        ["topics", "Browse topics"],
        ["playbooks", "Playbooks"],
      ].map(([id, title]) => (
        <a
          key={id}
          href={`#/learn/${id}${suffix}`}
          aria-current={view === id ? "page" : undefined}
        >
          {title}
        </a>
      ))}
      <a href={`#/practice${suffix}`}>Practice & capstone</a>
      <a href={`#/courses${suffix}`}>Course library</a>
    </nav>
  );
}
export function Learn({
  view = "roadmaps",
  from,
  playbook,
}: {
  view?: string;
  from?: string;
  playbook?: string;
}) {
  const { data } = useStudy();
  const [query, setQuery] = useState("");
  const q = query.trim().toLowerCase();
  useEffect(() => {
    if (playbook && view === "playbooks")
      document.getElementById(playbook)?.scrollIntoView();
  }, [playbook, view]);
  const detour = (href: string) =>
    from
      ? `${href}${href.includes("?") ? "&" : "?"}from=${encodeURIComponent(from)}`
      : href;
  return (
    <>
      <PageTitle
        eyebrow="learn"
        title={
          view === "topics"
            ? "Follow the subject."
            : view === "playbooks"
              ? "Useful when you need it."
              : "A clear way through."
        }
      >
        <p>
          {view === "topics"
            ? "Enter a topic directly, or follow a roadmap for a connected sequence."
            : view === "playbooks"
              ? "Task references lead back to the full explanation and practice."
              : "Connected topics, explicit assumptions, and optional foundations. Nothing is locked."}
        </p>
      </PageTitle>
      <LearnNav view={view} from={from} />
      {view === "topics" ? (
        <>
          <label className="sc-field search-field">
            Filter topics
            <input
              className="sc-input"
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="A title, subject, or question"
            />
          </label>
          <p className="sc-hint">
            For lesson text, glossary aliases, and your own notes, use{" "}
            <a href={detour("#/search")}>Search</a>.
          </p>
          {courses.map((course) => (
            <section key={course.id} className="topic-course">
              <h2>{course.title}</h2>
              {course.modules.map((module) => {
                const found = module.lessons.filter((l) =>
                  `${l.title} ${l.summary} ${l.tags.join(" ")}`
                    .toLowerCase()
                    .includes(q),
                );
                return found.length ? (
                  <section className="topic-group" key={module.id}>
                    <h3>{module.title}</h3>
                    <div className="topic-grid">
                      {found.map((l) => (
                        <a
                          className="topic-card"
                          key={l.id}
                          href={detour(lessonHref(l.id))}
                        >
                          <p className="sc-eyebrow">
                            {l.teachingFormat === "flexible"
                              ? "Worked technical topic"
                              : "Introductory / applied overview"}
                          </p>
                          <h4>{l.title}</h4>
                          <p>{l.summary}</p>
                          <span className="sc-hint">
                            {completionLabel(l, data)} →
                          </span>
                        </a>
                      ))}
                    </div>
                  </section>
                ) : null;
              })}
            </section>
          ))}
          {q &&
            !courses.some((c) =>
              c.modules.some((m) =>
                m.lessons.some((l) =>
                  `${l.title} ${l.summary} ${l.tags.join(" ")}`
                    .toLowerCase()
                    .includes(q),
                ),
              ),
            ) && (
              <p role="status">
                No topics match that phrase. Try a shorter term or Search.
              </p>
            )}
        </>
      ) : view === "playbooks" ? (
        <div className="playbook-list">
          {paths.flatMap((path) =>
            path.playbooks.map((book) => (
              <section className="playbook" id={book.id} key={book.id}>
                <p className="sc-eyebrow">{path.title}</p>
                <h2>{book.title}</h2>
                <p>{book.summary}</p>
                <ul>
                  {book.targets.map((target, i) => (
                    <li key={i}>
                      <a
                        href={detour(
                          target.scenarioId
                            ? `#/practice/${target.scenarioId}`
                            : target.lessonId
                              ? lessonHref(target.lessonId, target.sectionId)
                              : `#/course/${target.courseId}`,
                        )}
                      >
                        {target.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </section>
            )),
          )}
        </div>
      ) : (
        <div className="roadmap-list">
          {paths.map((path) => (
            <a
              className="roadmap-card"
              href={detour(`#/path/${path.id}`)}
              key={path.id}
            >
              <p className="sc-eyebrow">
                {path.groups.length} groups ·{" "}
                {path.groups.reduce((n, g) => n + g.lessonIds.length, 0)} topics
              </p>
              <h2>{path.title}</h2>
              <p>{path.summary}</p>
              <span className="course-link">Explore the roadmap →</span>
            </a>
          ))}
          {!paths.length && (
            <p>
              No roadmaps are available.{" "}
              <a href="#/learn/topics">Browse the current topics.</a>
            </p>
          )}
        </div>
      )}
    </>
  );
}

export function Roadmap({ id }: { id: string }) {
  const { data } = useStudy();
  const path = paths.find((p) => p.id === id);
  if (!path)
    return (
      <>
        <PageTitle
          eyebrow="roadmap unavailable"
          title="This roadmap is no longer available."
        />
        <p>
          Your topic notes, completion choices, and review history are retained.{" "}
          <a href="#/learn">Browse current roadmaps</a>.
        </p>
      </>
    );
  const ordered = path.groups
    .flatMap((g) => g.lessonIds)
    .map(findLesson)
    .filter((e) => !!e);
  const next = ordered.find(
    (e) => completionLabel(e.lesson, data) !== "Marked complete",
  );
  const saved =
    data.resume?.pathId === id
      ? ordered.find((e) => e.lesson.id === data.resume?.lessonId)
      : undefined;
  const primary = saved ?? next;
  return (
    <>
      <a className="sc-link--quiet" href="#/learn">
        ← All roadmaps
      </a>
      <PageTitle eyebrow="your roadmap" title={path.title}>
        <p>{path.summary}</p>
      </PageTitle>
      <div className="roadmap-intro">
        <section>
          <h2>What you will be able to do</h2>
          <ul>
            {path.outcomes.map((o) => (
              <li key={o}>{o}</li>
            ))}
          </ul>
        </section>
        <section>
          <h2>Starting assumptions</h2>
          <ul>
            {path.startingAssumptions.map((o) => (
              <li key={o}>{o}</li>
            ))}
          </ul>
          <p>Prerequisites guide your choices. You can open every topic.</p>
        </section>
      </div>
      {next ? (
        <div className="sc-actionbar">
          <p>
            {saved
              ? "Continue from your saved place in this path."
              : completionLabel(next.lesson, data) ===
                  "Revised since completion"
                ? "A topic has changed since you marked it complete."
                : "Take the next topic, or choose anywhere below."}
          </p>
          <a
            className="sc-btn sc-btn--primary"
            href={pathLessonHref(
              id,
              primary!.lesson.id,
              saved ? data.resume?.sectionId : undefined,
            )}
          >
            {saved ? "Resume this path" : "Open next topic"} →
          </a>
        </div>
      ) : (
        <p className="sc-notice">
          You marked every current topic complete. That records completion, not
          mastery. Revisit any topic or <a href="#/review">review its cards</a>.
        </p>
      )}
      {path.optionalBridges.length > 0 && (
        <section className="bridge-list">
          <p className="sc-eyebrow">optional foundations</p>
          <h2>Fill a gap when it helps.</h2>
          {path.optionalBridges.map((bridge) => {
            const entry = findLesson(bridge.lessonId);
            return (
              <div className="bridge" key={bridge.lessonId}>
                <h3>
                  <a href={pathLessonHref(id, bridge.lessonId)}>
                    {entry?.lesson.title ?? "Unavailable bridge"}
                  </a>
                </h3>
                <p>{bridge.explanation}</p>
                <p className="sc-hint">
                  Optional. Choosing a core topic leaves this bridge
                  uncompleted.
                </p>
              </div>
            );
          })}
        </section>
      )}
      <div className="course-map">
        {path.groups.map((group, index) => (
          <section className="module-block" key={group.id}>
            <div className="module-heading">
              <span className="module-number">
                {String(index + 1).padStart(2, "0")}
              </span>
              <div>
                <h2>{group.title}</h2>
                <p>{group.purpose}</p>
              </div>
            </div>
            <ol>
              {group.lessonIds.map((lessonId) => {
                const entry = findLesson(lessonId);
                if (!entry)
                  return (
                    <li key={lessonId}>
                      This topic is unavailable; your history is retained.
                    </li>
                  );
                const prereqs = path.prerequisites.filter(
                  (p) => p.lessonId === lessonId,
                );
                return (
                  <li key={lessonId}>
                    <a href={pathLessonHref(id, lessonId)}>
                      <span>
                        <strong>{entry.lesson.title}</strong>
                        <span>{entry.lesson.summary}</span>
                      </span>
                      <span className="lesson-state">
                        {completionLabel(entry.lesson, data)} →
                      </span>
                    </a>
                    {prereqs.length > 0 && (
                      <details className="roadmap-prerequisites">
                        <summary>Helpful first</summary>
                        <ul>
                          {prereqs.map((p) => (
                            <li key={p.requiredLessonId}>
                              <a
                                href={
                                  pathForLesson(paths, p.requiredLessonId, id)
                                    ? pathLessonHref(id, p.requiredLessonId)
                                    : lessonHref(p.requiredLessonId)
                                }
                              >
                                {findLesson(p.requiredLessonId)?.lesson.title ??
                                  p.requiredLessonId}
                              </a>{" "}
                              — {p.explanation}
                            </li>
                          ))}
                        </ul>
                      </details>
                    )}
                  </li>
                );
              })}
            </ol>
          </section>
        ))}
      </div>
      <p>
        <a href="#/learn/playbooks">Use the playbooks</a> ·{" "}
        <a href="#/practice">Applied practice and capstone</a>
      </p>
    </>
  );
}
