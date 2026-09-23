import {
  Fragment,
  useEffect,
  useId,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  beatHref,
  courses,
  findLesson,
  lessonHref,
  loadCollectionBody,
  teachingIndex,
} from "./catalog";
import type {
  CatalogCase,
  CatalogCourse,
  CatalogGuide,
  CatalogLab,
  ContentBody,
} from "./catalog-types";
import {
  guideNoteId,
  guideNoteLesson,
  hasCollections,
  labClassOrder,
  labClassText,
  nextInTrack,
  relatedCollections,
  reporterText,
  routeResume,
} from "./collections-model";
import { NoteEditor } from "./reader";
import { nowISO } from "./study";
import { ContentDownload, MD, PageTitle, useStudy } from "./ui";
import { ScrollableTable } from "./teaching-text";

/*
 * Views for the optional course collections: named routes, the lab shelf,
 * field guides, case analyses and the learning crosswalk. Everything listed
 * comes from the catalog tier; lab, guide and case bodies load on demand.
 * A course without these fields never reaches this file's views, so its
 * course map and card render exactly as before.
 */

const plural = (n: number, one: string, many: string) =>
  `${n} ${n === 1 ? one : many}`;
/** Phones collapse secondary lists; wider screens open them. Read once at mount. */
const wideQuery = "(min-width: 761px)";
function useWide() {
  const [wide] = useState(
    () =>
      typeof window !== "undefined" &&
      typeof window.matchMedia === "function" &&
      window.matchMedia(wideQuery).matches,
  );
  return wide;
}
const findModule = (id: string) => {
  for (const course of courses) {
    const module = course.modules.find((m) => m.id === id);
    if (module) return { course, module };
  }
  return undefined;
};
/** A module's canonical entry: its teaching deck, or its first lesson when it has none. */
export function moduleHref(id: string) {
  if (teachingIndex.some((t) => t.moduleId === id)) return beatHref(id);
  const found = findModule(id);
  return found ? lessonHref(found.module.lessons[0].id) : `#/courses`;
}
export const moduleTitle = (id: string) =>
  teachingIndex.find((t) => t.moduleId === id)?.title ??
  findModule(id)?.module.title ??
  id;
const navigationTarget = (id: string) => {
  if (findModule(id)) return { href: moduleHref(id), title: moduleTitle(id) };
  const lesson = findLesson(id);
  if (lesson) return { href: lessonHref(id), title: lesson.lesson.title };
  const course = courses.find((c) => c.id === id);
  return course ? { href: `#/course/${id}`, title: course.title } : undefined;
};

function ModuleLinks({ ids }: { ids: string[] }) {
  return (
    <ul className="academy-links">
      {ids.map((id) => (
        <li key={id}>
          <a href={moduleHref(id)}>{moduleTitle(id)}</a>
        </li>
      ))}
    </ul>
  );
}
function External({ href, children }: { href: string; children: string }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children} ↗<span className="sc-sr-only"> (opens in a new tab)</span>
    </a>
  );
}

/** Module prerequisites as links: guidance for the order, never a lock. */
export function BuildsOn({ ids }: { ids: string[] }) {
  const targets = ids.flatMap((id) => {
    const target = navigationTarget(id);
    return target ? [{ id, ...target }] : [];
  });
  if (!targets.length) return null;
  return (
    <p className="academy-builds-on">
      Builds on:{" "}
      {targets.map((t, i) => (
        <Fragment key={t.id}>
          {i ? ", " : ""}
          <a href={t.href}>{t.title}</a>
        </Fragment>
      ))}
      <span className="academy-muted">
        {" "}
        · a suggested order; every module stays open
      </span>
    </p>
  );
}

/** Tracks, labs and field guides on a course card, when the course has them. */
export function CourseCounts({ course }: { course: CatalogCourse }) {
  const parts = [
    course.tracks?.length
      ? plural(course.tracks.length, "track", "tracks")
      : "",
    course.labs?.length ? plural(course.labs.length, "lab", "labs") : "",
    course.guides?.length
      ? plural(course.guides.length, "field guide", "field guides")
      : "",
  ].filter(Boolean);
  return parts.length ? (
    <p className="academy-course-counts">{parts.join(" · ")}</p>
  ) : null;
}

/** The suggested essential route with Start/Resume, and the other routes as links. */
export function RoutesPanel({ course }: { course: CatalogCourse }) {
  const { data } = useStudy(),
    titleId = useId();
  const routes = course.routes ?? [];
  if (!routes.length) return null;
  const essential = routes.find((route) => route.essential),
    others = routes.filter((route) => route !== essential),
    // Without an essential route the others are the panel's top headings.
    RouteHeading = essential ? "h3" : "h2";
  const resume = essential
    ? routeResume(essential.moduleIds, data.beatPositions, teachingIndex)
    : undefined;
  const steps = (ids: string[]) => (
    <ol className="academy-route-steps" role="list">
      {ids.map((id) => (
        <li key={id}>
          <a href={moduleHref(id)}>{moduleTitle(id)}</a>
        </li>
      ))}
    </ol>
  );
  return (
    <section
      className="academy-routes"
      aria-labelledby={essential ? titleId : undefined}
      aria-label={essential ? undefined : "Learning routes"}
    >
      {essential && (
        <div className="academy-route academy-route--essential">
          <p className="sc-eyebrow">Essential route · a suggested order</p>
          <h2 id={titleId}>{essential.title}</h2>
          <p>{essential.summary}</p>
          {steps(essential.moduleIds)}
          <div className="actions">
            <a
              className="sc-btn sc-btn--secondary"
              href={
                resume
                  ? beatHref(resume.moduleId, resume.beatId, resume.view)
                  : moduleHref(essential.moduleIds[0])
              }
            >
              {resume ? "Resume this route →" : "Start this route →"}
            </a>
            {resume && (
              <span className="academy-muted">
                Saved place: {moduleTitle(resume.moduleId)} ·{" "}
                {
                  teachingIndex
                    .find((t) => t.moduleId === resume.moduleId)
                    ?.beats.find((b) => b.id === resume.beatId)?.title
                }
              </span>
            )}
          </div>
          <p className="sc-hint">
            A route links the course’s own modules in a suggested order. Nothing
            is locked, and progress belongs to each module.
          </p>
        </div>
      )}
      {others.length > 0 && (
        <details className="sc-details academy-other-routes">
          <summary>
            {essential ? "Deeper routes" : "Learning routes"} ({others.length})
          </summary>
          {others.map((route) => (
            <div className="academy-route" key={route.id}>
              <RouteHeading>{route.title}</RouteHeading>
              <p>{route.summary}</p>
              {steps(route.moduleIds)}
            </div>
          ))}
        </details>
      )}
    </section>
  );
}

/** A compact strip of the course's other collections. */
export function AlsoInCourse({ course }: { course: CatalogCourse }) {
  if (!hasCollections(course)) return null;
  const capstones = course.scenarios.filter((s) => s.isCapstone).length;
  const links = [
    course.labs?.length
      ? {
          href: `#/course/${course.id}/labs`,
          text: plural(course.labs.length, "lab", "labs"),
        }
      : undefined,
    course.guides?.length
      ? {
          href: `#/course/${course.id}/guides`,
          text: plural(course.guides.length, "field guide", "field guides"),
        }
      : undefined,
    course.cases?.length
      ? {
          href: `#/course/${course.id}/cases`,
          text: plural(course.cases.length, "case analysis", "case analyses"),
        }
      : undefined,
    capstones
      ? {
          href: "#/practice",
          text: plural(capstones, "capstone", "capstones"),
        }
      : undefined,
    course.crosswalk?.length
      ? { href: `#/course/${course.id}/crosswalk`, text: "Learning crosswalk" }
      : undefined,
    { href: `#/handbook/${course.id}`, text: "Course handbook" },
  ].filter((link) => !!link);
  return (
    <nav className="academy-also" aria-label="Also in this course">
      <p className="sc-eyebrow">Also in this course</p>
      <ul>
        {links.map((link) => (
          <li key={link.href}>
            <a href={link.href}>{link.text}</a>
          </li>
        ))}
      </ul>
    </nav>
  );
}

/** The end of a module: the next module in its track and the labs and guides that name it. */
export function ModuleNext({
  course,
  moduleId,
}: {
  course: CatalogCourse;
  moduleId: string;
}) {
  const wide = useWide(),
    titleId = useId();
  const position = nextInTrack(course, moduleId),
    { labs, guides } = relatedCollections(course, moduleId);
  if (!position && !labs.length && !guides.length) return null;
  return (
    <section className="academy-next" aria-labelledby={titleId}>
      <h2 id={titleId}>Where to go next</h2>
      {position &&
        (position.next ? (
          <p className="academy-next-module">
            Next in this track:{" "}
            <a href={moduleHref(position.next)}>{moduleTitle(position.next)}</a>{" "}
            <span className="academy-muted">· {position.track.title}</span>
          </p>
        ) : (
          <p className="academy-next-module">
            This is the last module in {position.track.title}.{" "}
            <a href={`#/course/${course.id}`}>
              Choose another track on the course map
            </a>
          </p>
        ))}
      {(labs.length > 0 || guides.length > 0) && (
        <details className="academy-related" open={wide}>
          <summary>
            Related labs and field guides ({labs.length + guides.length})
          </summary>
          <ul>
            {labs.map((lab) => (
              <li key={lab.id}>
                <a href={`#/course/${course.id}/labs/${lab.id}`}>
                  Lab · {lab.title}
                </a>
              </li>
            ))}
            {guides.map((guide) => (
              <li key={guide.id}>
                <a href={`#/course/${course.id}/guides/${guide.id}`}>
                  Field guide · {guide.title}
                </a>
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

type CollectionKind = "lab" | "guide" | "case";
const bodyLabel: Record<CollectionKind, string> = {
  lab: "lab",
  guide: "field guide",
  case: "case analysis",
};
function useCollectionBody<K extends CollectionKind>(kind: K, id: string) {
  const [state, setState] = useState<{
      id: string;
      body?: Extract<ContentBody, { kind: K }>;
      error?: string;
    }>({ id }),
    [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setState({ id });
    void loadCollectionBody(kind, id)
      .then((body) => {
        if (active) setState({ id, body });
      })
      .catch((error: Error) => {
        if (active) setState({ id, error: error.message });
      });
    return () => {
      active = false;
    };
  }, [kind, id, retry]);
  return {
    ...(state.id === id ? state : { id }),
    retry: () => setRetry((n) => n + 1),
  };
}
function BodyStatus({
  kind,
  loaded,
  error,
  retry,
}: {
  kind: CollectionKind;
  loaded: boolean;
  error?: string;
  retry: () => void;
}) {
  if (error)
    return (
      <div className="sc-notice academy-body-status" role="alert">
        <p>{error}</p>
        <button className="sc-btn sc-btn--secondary" onClick={retry}>
          Retry {bodyLabel[kind]}
        </button>
      </div>
    );
  return loaded ? null : (
    <p className="academy-body-status" role="status">
      Opening the {bodyLabel[kind]}…
    </p>
  );
}

const back = (href: string, text: string) => (
  <a className="sc-link--quiet academy-back" href={href}>
    ← {text}
  </a>
);
function Unavailable({
  eyebrow,
  title,
  href,
  text,
  course,
}: {
  eyebrow: string;
  title: string;
  href: string;
  text: string;
  course: CatalogCourse;
}) {
  return (
    <div className="academy-page">
      {back(`#/course/${course.id}`, "Course map")}
      <PageTitle eyebrow={eyebrow} title={title} />
      <p>
        Links and notes that pointed here are kept, and your study data is safe.{" "}
        <a href={href}>{text}</a> or return to the{" "}
        <a href={`#/course/${course.id}`}>{course.title}</a> course map.
      </p>
    </div>
  );
}

function LabFacts({ course, lab }: { course: CatalogCourse; lab: CatalogLab }) {
  return (
    <>
      <dl className="academy-facts">
        <div>
          <dt>Outcome</dt>
          <dd>{lab.outcome}</dd>
        </div>
        <div>
          <dt>Environment</dt>
          <dd>{lab.environment}</dd>
        </div>
        <div>
          <dt>Evidence</dt>
          <dd>{lab.evidence}</dd>
        </div>
        <div>
          <dt>Modules</dt>
          <dd>
            <ModuleLinks ids={lab.moduleIds} />
          </dd>
        </div>
      </dl>
      {lab.downloadId &&
        course.downloads?.some((d) => d.id === lab.downloadId) && (
          <div className="academy-download">
            <p className="academy-download-label">Lab files</p>
            <ContentDownload course={course} downloadId={lab.downloadId} />
          </div>
        )}
    </>
  );
}
function LabShelf({ course }: { course: CatalogCourse }) {
  const labs = course.labs ?? [];
  const classes = labClassOrder.filter((k) =>
    labs.some((lab) => lab.executionClass === k),
  );
  return (
    <div className="academy-page">
      {back(`#/course/${course.id}`, "Course map")}
      <PageTitle eyebrow={`${course.title} · lab shelf`} title="Labs">
        <p>
          Hands-on exercises grouped by how they run. Each lab links back to the
          modules that teach its ideas, and its evidence line says exactly what
          was, or was not, executed.
        </p>
      </PageTitle>
      <section className="academy-legend" aria-labelledby="academy-lab-legend">
        <h2 id="academy-lab-legend">How the labs run</h2>
        <dl>
          {classes.map((k) => (
            <div key={k}>
              <dt>{labClassText[k].label}</dt>
              <dd>{labClassText[k].legend}</dd>
            </div>
          ))}
        </dl>
      </section>
      {classes.map((k) => {
        const group = labs.filter((lab) => lab.executionClass === k);
        return (
          <section
            className="academy-group"
            key={k}
            aria-labelledby={`academy-labs-${k}`}
          >
            <h2 id={`academy-labs-${k}`}>
              {labClassText[k].label} · {plural(group.length, "lab", "labs")}
            </h2>
            <ul className="academy-items">
              {group.map((lab) => (
                <li key={lab.id}>
                  <article className="academy-card">
                    <p className="academy-kind">
                      <span className="sc-chip sc-chip--neutral">
                        {labClassText[lab.executionClass].label}
                      </span>
                    </p>
                    <h3>
                      <a href={`#/course/${course.id}/labs/${lab.id}`}>
                        {lab.title}
                      </a>
                    </h3>
                    <p>{lab.summary}</p>
                    <LabFacts course={course} lab={lab} />
                  </article>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}
function LabPage({ course, lab }: { course: CatalogCourse; lab: CatalogLab }) {
  const { body, error, retry } = useCollectionBody("lab", lab.id);
  const cls = labClassText[lab.executionClass];
  return (
    <div className="academy-page">
      {back(`#/course/${course.id}/labs`, "Lab shelf")}
      <PageTitle eyebrow={`${cls.label} lab`} title={lab.title}>
        <p>{lab.summary}</p>
      </PageTitle>
      <p className="academy-class-note">
        <span className="sc-chip sc-chip--neutral">{cls.label}</span>{" "}
        {cls.legend}
      </p>
      <LabFacts course={course} lab={lab} />
      <section className="academy-body" aria-labelledby="academy-lab-body">
        <h2 id="academy-lab-body">Lab instructions</h2>
        <BodyStatus kind="lab" loaded={!!body} error={error} retry={retry} />
        {body && <MD>{body.body}</MD>}
      </section>
      <section aria-labelledby="academy-lab-modules">
        <h2 id="academy-lab-modules">Related modules</h2>
        <ModuleLinks ids={lab.moduleIds} />
      </section>
    </div>
  );
}

function GuideList({ course }: { course: CatalogCourse }) {
  return (
    <div className="academy-page">
      {back(`#/course/${course.id}`, "Course map")}
      <PageTitle
        eyebrow={`${course.title} · field guides`}
        title="Field guides"
      >
        <p>
          Practical guides for a recurring question: what to do, a completed
          fictional example, a blank template you can draft in your notebook,
          and where the approach stops working.
        </p>
      </PageTitle>
      <ul className="academy-items">
        {(course.guides ?? []).map((guide) => (
          <li key={guide.id}>
            <article className="academy-card">
              <h2>
                <a href={`#/course/${course.id}/guides/${guide.id}`}>
                  {guide.title}
                </a>
              </h2>
              <p className="academy-question">{guide.question}</p>
              <p>{guide.summary}</p>
              <dl className="academy-facts">
                <div>
                  <dt>Modules</dt>
                  <dd>
                    <ModuleLinks ids={guide.moduleIds} />
                  </dd>
                </div>
              </dl>
            </article>
          </li>
        ))}
      </ul>
    </div>
  );
}
function GuideDraft({
  course,
  guide,
  template,
}: {
  course: CatalogCourse;
  guide: CatalogGuide;
  template: string;
}) {
  const { data, store } = useStudy();
  const id = guideNoteId(guide.id),
    lessonId = guideNoteLesson(course, guide),
    existing = !!data.notes[id];
  const [open, setOpen] = useState(false),
    editor = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (open) editor.current?.querySelector("textarea")?.focus();
  }, [open]);
  return open ? (
    <div className="academy-draft" ref={editor}>
      <NoteEditor
        courseId={course.id}
        lessonId={lessonId}
        sectionId={guide.id}
        noteId={id}
        label="Your draft from this template"
      />
      <a href={`#/notebook/${id}`}>Open this draft in Notebook →</a>
    </div>
  ) : (
    <div className="academy-draft">
      <button
        className="sc-btn sc-btn--secondary"
        onClick={() => {
          // Only the first use copies the template; an existing draft is
          // reopened as it is. The draft is an ordinary exported note.
          const at = nowISO();
          void store.change((s) =>
            s.notes[id]
              ? s
              : {
                  ...s,
                  notes: {
                    ...s.notes,
                    [id]: {
                      id,
                      courseId: course.id,
                      lessonId,
                      sectionId: guide.id,
                      text: template.slice(0, 100000),
                      question: false,
                      createdAt: at,
                      updatedAt: at,
                    },
                  },
                },
          );
          setOpen(true);
        }}
      >
        Draft in Notebook
      </button>
      <p className="sc-hint">
        {existing
          ? "You already have a draft from this template. It opens as you left it."
          : "Copies this template into a note you can edit. It stays in this browser, appears in Notebook and is included in exports."}
      </p>
    </div>
  );
}
/**
 * One part of a field guide: its own h2, so the h3/h4 headings in its body
 * nest under it (a worked example and a template often repeat heading
 * names), over a disclosure that holds the body.
 */
function GuidePart({
  title,
  toggle,
  open,
  children,
}: {
  title: string;
  toggle: string;
  open?: boolean;
  children: ReactNode;
}) {
  const titleId = useId();
  return (
    <section className="academy-guide-part" aria-labelledby={titleId}>
      <h2 id={titleId}>{title}</h2>
      <details className="sc-details" open={open}>
        <summary>{toggle}</summary>
        {children}
      </details>
    </section>
  );
}
function GuidePage({
  course,
  guide,
}: {
  course: CatalogCourse;
  guide: CatalogGuide;
}) {
  const { body, error, retry } = useCollectionBody("guide", guide.id);
  const wide = useWide();
  return (
    <div className="academy-page academy-guide">
      {back(`#/course/${course.id}/guides`, "Field guides")}
      <PageTitle eyebrow="field guide" title={guide.title}>
        <p className="academy-question">{guide.question}</p>
        <p>{guide.summary}</p>
      </PageTitle>
      <BodyStatus kind="guide" loaded={!!body} error={error} retry={retry} />
      {body && (
        <>
          <section
            className="academy-guide-action"
            aria-labelledby="academy-guide-action"
          >
            <h2 id="academy-guide-action">Action</h2>
            <MD>{body.body.action}</MD>
          </section>
          <GuidePart
            title="Worked example"
            toggle="Show the worked example"
            open={wide}
          >
            <MD>{body.body.example}</MD>
          </GuidePart>
          <GuidePart title="Template" toggle="Show the template">
            <MD>{body.body.template}</MD>
            <GuideDraft
              course={course}
              guide={guide}
              template={body.body.template}
            />
          </GuidePart>
          <GuidePart title="Limits" toggle="Show the limits">
            <MD>{body.body.limits}</MD>
          </GuidePart>
        </>
      )}
      <section aria-labelledby="academy-guide-related">
        <h2 id="academy-guide-related">Related modules</h2>
        <ModuleLinks ids={guide.moduleIds} />
        {guide.lessonIds.length > 0 && (
          <>
            <p className="academy-muted">Original lessons it draws on:</p>
            <ul className="academy-links">
              {guide.lessonIds.map((id) => (
                <li key={id}>
                  <a href={lessonHref(id)}>
                    {findLesson(id)?.lesson.title ?? id}
                  </a>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
    </div>
  );
}

function CaseFacts({ item }: { item: CatalogCase }) {
  return (
    <dl className="academy-facts">
      <div>
        <dt>Reported by</dt>
        <dd>{reporterText(item.reporter)}</dd>
      </div>
      <div>
        <dt>Published</dt>
        <dd>{item.publishedAt ?? "Date not verified"}</dd>
      </div>
      <div>
        <dt>Reviewed</dt>
        <dd>{item.reviewedAt}</dd>
      </div>
    </dl>
  );
}
function CaseList({ course }: { course: CatalogCourse }) {
  return (
    <div className="academy-page">
      {back(`#/course/${course.id}`, "Course map")}
      <PageTitle
        eyebrow={`${course.title} · case analyses`}
        title="Case analyses"
      >
        <p>
          Public accounts of real work, read critically: what was reported, who
          reported it, and which modules explain the mechanisms involved.
        </p>
      </PageTitle>
      <ul className="academy-items">
        {(course.cases ?? []).map((item) => (
          <li key={item.id}>
            <article className="academy-card">
              <p className="academy-kind">
                <span className="sc-chip sc-chip--neutral">{item.domain}</span>
              </p>
              <h2>
                <a href={`#/course/${course.id}/cases/${item.id}`}>
                  {item.title}
                </a>
              </h2>
              <p>{item.summary}</p>
              <CaseFacts item={item} />
            </article>
          </li>
        ))}
      </ul>
    </div>
  );
}
function CasePage({
  course,
  item,
}: {
  course: CatalogCourse;
  item: CatalogCase;
}) {
  const { body, error, retry } = useCollectionBody("case", item.id);
  const sources = course.sources.filter((s) => item.sourceIds.includes(s.id));
  return (
    <div className="academy-page">
      {back(`#/course/${course.id}/cases`, "Case analyses")}
      <PageTitle eyebrow={`case analysis · ${item.domain}`} title={item.title}>
        <p>{item.summary}</p>
      </PageTitle>
      <CaseFacts item={item} />
      <section
        className="academy-sources"
        aria-labelledby="academy-case-source"
      >
        <h2 id="academy-case-source">
          {sources.length === 1 ? "Source" : "Sources"}
        </h2>
        <p className="sc-hint">
          Outcomes are as the source reports them. This course has not
          reproduced them.
        </p>
        {sources.map((s) => (
          <div className="source-record" key={s.id}>
            <External href={s.url}>{s.title}</External>
            <p>
              {s.publisher} · {s.type} · accessed {s.accessDate} · reviewed{" "}
              {s.reviewDate}
            </p>
            <p>{s.context}</p>
            <p>
              <strong>Caveat:</strong> {s.caveat}
            </p>
          </div>
        ))}
      </section>
      <section className="academy-body" aria-labelledby="academy-case-body">
        <h2 id="academy-case-body">The analysis</h2>
        <BodyStatus kind="case" loaded={!!body} error={error} retry={retry} />
        {body && <MD>{body.body}</MD>}
      </section>
      <section aria-labelledby="academy-case-modules">
        <h2 id="academy-case-modules">Related modules</h2>
        <ModuleLinks ids={item.moduleIds} />
      </section>
    </div>
  );
}

function Crosswalk({ course }: { course: CatalogCourse }) {
  return (
    <div className="academy-page">
      {back(`#/course/${course.id}`, "Course map")}
      <PageTitle
        eyebrow={`${course.title} · crosswalk`}
        title="Learning crosswalk"
      >
        <p>
          Other learning resources that cover related ground, mapped to this
          course’s modules. Studying here is independent; it earns no credit
          with these publishers, and each row says what its review could see.
        </p>
      </PageTitle>
      <ScrollableTable
        className="sc-table-scroll academy-crosswalk"
        label="Learning crosswalk, scroll horizontally if needed"
      >
        <table className="sc-table">
          <thead>
            <tr>
              <th scope="col">Resource</th>
              <th scope="col">Publisher</th>
              <th scope="col">Access</th>
              <th scope="col">Prerequisites</th>
              <th scope="col">Related modules</th>
              <th scope="col">Note</th>
            </tr>
          </thead>
          <tbody>
            {(course.crosswalk ?? []).map((row) => (
              <tr key={row.id}>
                <th scope="row">
                  <External href={row.url}>{row.title}</External>
                  <span className="academy-reviewed">
                    Reviewed {row.reviewedAt}
                  </span>
                </th>
                <td>{row.publisher}</td>
                <td>{row.access}</td>
                <td>{row.prerequisites}</td>
                <td>
                  <ModuleLinks ids={row.moduleIds} />
                </td>
                <td>{row.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </ScrollableTable>
    </div>
  );
}

const sectionNames = {
  labs: { list: "lab shelf", item: "lab", back: "Browse the lab shelf" },
  guides: {
    list: "field guides",
    item: "field guide",
    back: "Browse the field guides",
  },
  cases: {
    list: "case analyses",
    item: "case analysis",
    back: "Browse the case analyses",
  },
  crosswalk: {
    list: "learning crosswalk",
    item: "crosswalk entry",
    back: "Open the learning crosswalk",
  },
} as const;
type SectionName = keyof typeof sectionNames;
const isSection = (value: string): value is SectionName =>
  Object.hasOwn(sectionNames, value);

/** `#/course/<id>/(labs|guides|cases)[/<item>]` and `#/course/<id>/crosswalk`. */
export function CourseSection({
  course,
  section,
  item,
}: {
  course: CatalogCourse;
  section: string;
  item?: string;
}) {
  const map = `#/course/${course.id}`;
  if (!isSection(section))
    return (
      <Unavailable
        course={course}
        eyebrow="page unavailable"
        title="That part of the course is not available."
        href={map}
        text="Open the course map"
      />
    );
  const names = sectionNames[section],
    list = course[section];
  if (!list?.length)
    return (
      <Unavailable
        course={course}
        eyebrow={`${names.list} unavailable`}
        title={`This course has no ${names.list}.`}
        href={map}
        text="Open the course map"
      />
    );
  const missing = () => (
    <Unavailable
      course={course}
      eyebrow={`${names.item} unavailable`}
      title={`This ${names.item} is not in the current course.`}
      href={`${map}/${section}`}
      text={names.back}
    />
  );
  if (section === "crosswalk")
    return item ? missing() : <Crosswalk course={course} />;
  if (!item)
    return section === "labs" ? (
      <LabShelf course={course} />
    ) : section === "guides" ? (
      <GuideList course={course} />
    ) : (
      <CaseList course={course} />
    );
  if (section === "labs") {
    const lab = course.labs?.find((x) => x.id === item);
    return lab ? <LabPage key={lab.id} course={course} lab={lab} /> : missing();
  }
  if (section === "guides") {
    const guide = course.guides?.find((x) => x.id === item);
    return guide ? (
      <GuidePage key={guide.id} course={course} guide={guide} />
    ) : (
      missing()
    );
  }
  const found = course.cases?.find((x) => x.id === item);
  return found ? (
    <CasePage key={found.id} course={course} item={found} />
  ) : (
    missing()
  );
}
