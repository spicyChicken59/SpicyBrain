import { useEffect, useRef, useState } from "react";
import {
  cardIndex,
  extensionCardIds,
  cardTeaching,
  plainTeaching,
  courses,
  findLesson,
  lessonHref,
  lessons,
  loadCards,
  loadScenarioBody,
  scenarios,
  type ExtensionCard,
} from "./catalog";
import type { Card } from "./content-schema";
import type { CardRef, ScenarioBody } from "./catalog-types";
import { applyReview, nowISO, reviewQueue, type Rating } from "./study";
import {
  ContentDownload,
  MD,
  PageTitle,
  SaveStatus,
  Sources,
  useStudy,
  uuid,
} from "./ui";

export function Practice({ id }: { id?: string }) {
  const { data, store } = useStudy(),
    [ratings, setRatings] = useState<
      Record<string, "weak" | "partial" | "strong">
    >({}),
    [message, setMessage] = useState("");
  const entry = scenarios.find((s) => s.scenario.id === id);
  // The list and the workspace frame come from the catalog tier; the
  // situation, task and model response arrive with the scenario body.
  const [body, setBody] = useState<ScenarioBody | null>(null),
    [bodyError, setBodyError] = useState(""),
    [retry, setRetry] = useState(0);
  const scenarioId = entry?.scenario.id;
  useEffect(() => {
    if (!scenarioId) return;
    let active = true;
    setBodyError("");
    void loadScenarioBody(scenarioId)
      .then((loaded) => {
        if (active) setBody(loaded);
      })
      .catch((error: Error) => {
        if (active) setBodyError(error.message);
      });
    return () => {
      active = false;
    };
  }, [scenarioId, retry]);
  if (!id)
    return (
      <>
        <PageTitle eyebrow="use it" title="Practice the work">
          <p>
            Make a decision, write your reasoning, then compare it with an
            authored example. Your response stays here.
          </p>
        </PageTitle>
        {courses.map((c) => (
          <section key={c.id}>
            <h2>{c.title}</h2>
            <div className="practice-list">
              {c.scenarios.map((s, i) => (
                <a
                  className={`practice-row ${s.isCapstone ? "capstone-row" : ""}`}
                  href={`#/practice/${s.id}`}
                  key={s.id}
                >
                  <span className="row-number">
                    {s.isCapstone ? "C" : String(i + 1).padStart(2, "0")}
                  </span>
                  <span>
                    <span className="sc-eyebrow">
                      {s.isCapstone
                        ? "end-to-end capstone"
                        : "applied scenario"}
                    </span>
                    <strong>{s.title}</strong>
                    <span>
                      {Object.values(data.drafts).some(
                        (d) => d.targetId === s.id && d.text,
                      )
                        ? "Draft in progress"
                        : "Not attempted"}
                    </span>
                  </span>
                  <span aria-hidden="true">→</span>
                </a>
              ))}
            </div>
          </section>
        ))}
      </>
    );
  if (!entry)
    return (
      <>
        <PageTitle
          eyebrow="practice unavailable"
          title="This practice item was removed."
        />
        <p>
          Existing responses are preserved in <a href="#/notebook">Notebook</a>.{" "}
          <a href="#/practice">Browse current practice</a>.
        </p>
      </>
    );
  const { course, scenario: s } = entry,
    key = `draft-${s.id}`;
  const prior = Object.values(data.assessments).filter(
    (a) => a.targetId === s.id,
  );
  return (
    <>
      <a className="sc-link--quiet" href="#/practice">
        ← All practice
      </a>
      <PageTitle
        eyebrow={
          s.isCapstone
            ? "capstone · fictional customer"
            : "applied practice · fictional context"
        }
        title={s.title}
      />
      {s.revisionNotice && (
        <p className="sc-notice academy-revision">
          <strong>Revised practice item.</strong> {s.revisionNotice}
        </p>
      )}
      <div className="practice-workspace">
        <article className="sc-doc sc-doc--flat">
          {bodyError ? (
            <div className="sc-notice practice-body-status" role="alert">
              <p>{bodyError}</p>
              <button
                className="sc-btn sc-btn--secondary"
                onClick={() => setRetry((n) => n + 1)}
              >
                Retry practice item
              </button>
            </div>
          ) : !body ? (
            <p className="practice-body-status" role="status">
              Opening the practice item…
            </p>
          ) : (
            <>
              <h2>The situation</h2>
              <MD>{body.context}</MD>
              {body.disclosures.length > 0 && (
                <section>
                  <h2>Ask the stakeholders</h2>
                  <p className="sc-hint">
                    These are authored teaching disclosures, not an AI
                    conversation. Open a question when you are ready to learn
                    more.
                  </p>
                  {body.disclosures.map((d) => (
                    <details
                      key={d.question}
                      className="sc-details stakeholder"
                    >
                      <summary>{d.question}</summary>
                      <MD>{d.response}</MD>
                    </details>
                  ))}
                </section>
              )}
              <h2>Your task</h2>
              <MD>{body.task}</MD>
            </>
          )}
          {body && (
            <ul>
              {body.requirements.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
          {!!s.downloadIds?.length && (
            <section className="academy-data-pack">
              <h2>Data pack</h2>
              <p>
                Optional files for working this item locally. Downloading does
                not execute anything or record completion.
              </p>
              <ul>
                {s.downloadIds.map((downloadId) =>
                  course.downloads?.some((d) => d.id === downloadId) ? (
                    <li key={downloadId}>
                      <ContentDownload
                        course={course}
                        downloadId={downloadId}
                      />
                    </li>
                  ) : null,
                )}
              </ul>
            </section>
          )}
          <label className="sc-field">
            Your response
            <textarea
              maxLength={100000}
              className="sc-input practice-response"
              rows={14}
              value={data.drafts[key]?.text ?? ""}
              onChange={(e) => {
                const text = e.target.value,
                  at = nowISO();
                void store.change((state) => ({
                  ...state,
                  drafts: {
                    ...state.drafts,
                    [key]: {
                      id: key,
                      courseId: course.id,
                      targetId: s.id,
                      text,
                      createdAt: state.drafts[key]?.createdAt ?? at,
                      updatedAt: at,
                    },
                  },
                }));
              }}
            />
          </label>
          <SaveStatus />
          {body && (
            <details className="sc-details model-response">
              <summary>Reveal model response and reasoning</summary>
              <h2>One defensible response</h2>
              <MD>{body.model}</MD>
              <h3>Why this works</h3>
              <MD>{body.reasoning}</MD>
            </details>
          )}
          <h2>Self-assessment</h2>
          <p>
            You choose the rating. This is educational feedback, not automated
            evaluation or an employer score.
          </p>
          {body?.rubric.map((r) => (
            <fieldset className="rubric" key={r.id}>
              <legend>{r.criterion}</legend>
              {(["weak", "partial", "strong"] as const).map((level) => (
                <label className="answer-option" key={level}>
                  <input
                    type="radio"
                    name={r.id}
                    checked={ratings[r.id] === level}
                    onChange={() => setRatings({ ...ratings, [r.id]: level })}
                  />
                  <span>
                    <strong>{level[0].toUpperCase() + level.slice(1)}</strong> ·{" "}
                    {r[level]}
                  </span>
                </label>
              ))}
            </fieldset>
          ))}
          <button
            className="sc-btn sc-btn--primary"
            onClick={() => {
              if (!body || body.rubric.some((r) => !ratings[r.id])) {
                setMessage(
                  "Choose a rating for each dimension before recording.",
                );
                return;
              }
              const id = uuid(),
                at = nowISO();
              void store.change((state) => ({
                ...state,
                assessments: {
                  ...state.assessments,
                  [id]: {
                    id,
                    courseId: course.id,
                    targetId: s.id,
                    at,
                    ratings,
                    kind: "self-assessment",
                  },
                },
              }));
              setRatings({});
              setMessage("Self-assessment recorded.");
            }}
          >
            Record self-assessment
          </button>
          <p role="status">{message}</p>
          {prior.length > 0 && (
            <details className="sc-details">
              <summary>{prior.length} self-assessments recorded</summary>
              {prior.map((a) => (
                <div key={a.id}>
                  <p>{new Date(a.at).toLocaleString()}</p>
                  <ul>
                    {Object.entries(a.ratings).map(([id, value]) => (
                      <li key={id}>
                        {body?.rubric.find((r) => r.id === id)?.criterion ?? id}
                        : {value}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </details>
          )}
          {body && <Sources course={course} claimIds={body.claimIds} />}
        </article>
        <aside className="practice-aside">
          <p className="sc-eyebrow">Return to the ideas</p>
          {s.lessonIds.map((id) => (
            <a key={id} href={lessonHref(id)}>
              {findLesson(id)?.lesson.title ?? id}
            </a>
          ))}
          <p className="sc-hint">
            Several designs can be defensible. Make assumptions, tradeoffs,
            evidence, and ownership visible.
          </p>
        </aside>
      </div>
    </>
  );
}

export function Review({
  lessonId,
  cardIds,
}: {
  lessonId?: string;
  cardIds?: string[];
}) {
  const { data, store } = useStudy();
  const [selectedLesson, setSelectedLesson] = useState(
    lessonId ?? (cardIds ? "all" : "studied"),
  );
  // Queues are computed from card identities; text is loaded for a session.
  const selection = cardIds
    ? cardIndex.filter((c) => cardIds.includes(c.id))
    : cardIndex;
  const [session, setSession] = useState<{
      mode: "due" | "new" | "extra";
      ids: string[];
      index: number;
    } | null>(null),
    [texts, setTexts] = useState<Map<string, Card | ExtensionCard> | null>(
      null,
    ),
    [textsError, setTextsError] = useState(""),
    [retry, setRetry] = useState(0),
    [revealed, setRevealed] = useState(false),
    [busy, setBusy] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false),
    [history, setHistory] = useState<Map<string, Card | ExtensionCard> | null>(
      null,
    ),
    [historyError, setHistoryError] = useState("");
  const eventId = useRef(uuid()),
    guard = useRef(false);
  const clock = nowISO();
  const due = reviewQueue(selection, data, clock, 100000);
  const openedCore = (c: CardRef) =>
    !extensionCardIds.has(c.id) &&
    (!!data.positions[c.lessonId] ||
      Object.values(data.beatPositions).some(
        (p) => cardTeaching(c.id)?.beatId === p.beatId,
      ));
  const inScope = (c: CardRef) =>
    selectedLesson === "all" ||
    (selectedLesson === "studied" && openedCore(c)) ||
    selectedLesson === c.lessonId;
  const newCards = selection.filter((c) => !data.schedules[c.id] && inScope(c));
  const sessionIds = session?.ids;
  useEffect(() => {
    if (!sessionIds) return;
    let active = true;
    setTexts(null);
    setTextsError("");
    void loadCards(sessionIds)
      .then((loaded) => {
        if (active) setTexts(loaded);
      })
      .catch((error: Error) => {
        if (active) setTextsError(error.message);
      });
    return () => {
      active = false;
    };
  }, [sessionIds, retry]);
  const scheduled = Object.values(data.schedules).sort(
    (a, b) => a.dueAt.localeCompare(b.dueAt) || a.id.localeCompare(b.id),
  );
  const scheduledKey = scheduled
    .map((s) => s.cardId)
    .filter((id) => cardIndex.some((c) => c.id === id))
    .join(" ");
  useEffect(() => {
    // Prompts for the history panel are fetched only once it is opened and
    // never block the page; lesson titles come from the catalog tier.
    if (!historyOpen) return;
    let active = true;
    setHistoryError("");
    void loadCards(scheduledKey ? scheduledKey.split(" ") : [])
      .then((loaded) => {
        if (active) setHistory(loaded);
      })
      .catch((error: Error) => {
        if (active) setHistoryError(error.message);
      });
    return () => {
      active = false;
    };
  }, [historyOpen, scheduledKey]);
  const start = (mode: "due" | "new" | "extra") => {
    const pool =
      mode === "due"
        ? due.slice(0, data.settings.sessionSize)
        : mode === "new"
          ? newCards.slice(0, data.settings.newLimit)
          : selection.filter(inScope).slice(0, data.settings.sessionSize);
    setSession({ mode, ids: pool.map((c) => c.id), index: 0 });
    setRevealed(false);
    guard.current = false;
    eventId.current = uuid();
  };
  const finished = !!session && session.index >= session.ids.length;
  const card =
    session && texts && !finished
      ? texts.get(session.ids[session.index])
      : undefined;
  const next = () => {
    setSession((s) => (s ? { ...s, index: s.index + 1 } : s));
    setRevealed(false);
    eventId.current = uuid();
    guard.current = false;
    setBusy(false);
  };
  const rate = async (rating: Rating) => {
    if (!card || !session || !revealed || guard.current) return;
    guard.current = true;
    setBusy(true);
    const course = findLesson(card.lessonId)!.course,
      id = eventId.current,
      at = nowISO();
    if (session.mode === "extra")
      await store.change((s) => ({
        ...s,
        extraPractice: {
          ...s.extraPractice,
          [id]: {
            id,
            courseId: course.id,
            lessonId: card.lessonId,
            cardId: card.id,
            revision: card.revision,
            at,
          },
        },
      }));
    else
      await store.change((s) =>
        applyReview(s, card, course.id, rating, id, at),
      );
    // Do not claim a committed review or advance on persistence failure.
    if (store.getSnapshot().status === "unsaved") {
      guard.current = false;
      setBusy(false);
      return;
    }
    next();
  };
  return (
    <>
      {!cardIds && (
        <PageTitle
          eyebrow="remember it"
          title="A little review goes a long way"
        >
          <p>
            Recall first. Reveal the answer. Choose how it felt. There is no
            streak to protect.
          </p>
        </PageTitle>
      )}
      {session ? (
        finished ? (
          <div className="sc-card session-done">
            <p className="sc-eyebrow">session complete</p>
            <h2>
              {session.ids.length
                ? "That is enough for this session."
                : "No cards in this session."}
            </h2>
            <p>
              {session.ids.length
                ? `${session.ids.length} ${session.mode === "extra" ? "extra-practice cards" : "card reviews"} recorded. Remaining cards keep their due dates.`
                : "Try another lesson selection or return after studying a lesson."}
            </p>
            <button
              className="sc-btn sc-btn--primary"
              onClick={() => setSession(null)}
            >
              Back to review
            </button>
          </div>
        ) : textsError || (texts && !card) ? (
          <div className="sc-notice review-status" role="alert">
            <p>
              {textsError ||
                "This card is unavailable in the current course files. Your review history is unchanged."}
            </p>
            <div className="actions">
              <button
                className="sc-btn sc-btn--secondary"
                onClick={() => setRetry((n) => n + 1)}
              >
                Retry cards
              </button>
              <button
                className="sc-btn sc-btn--ghost"
                onClick={() => setSession(null)}
              >
                End session
              </button>
            </div>
          </div>
        ) : !card ? (
          <p className="review-status" role="status">
            Preparing your cards…
          </p>
        ) : (
          <div className="review-workspace">
            <div className="review-meta">
              <span className="sc-eyebrow">
                {session.mode === "extra"
                  ? "extra practice · schedule unchanged"
                  : session.mode === "new"
                    ? "introduce new cards"
                    : "scheduled review"}
              </span>
              <span>
                {session.index + 1} of {session.ids.length}
              </span>
              <button
                className="sc-btn sc-btn--ghost"
                onClick={() => setSession(null)}
              >
                End session
              </button>
            </div>
            <div className="flashcard">
              <p className="sc-eyebrow">
                {findLesson(card.lessonId)?.module.title}
              </p>
              <h2>{plainTeaching(card.prompt)}</h2>
              {data.schedules[card.id]?.revision &&
                data.schedules[card.id].revision !== card.revision && (
                  <p className="sc-chip sc-chip--info">
                    Answer revised · review this version
                  </p>
                )}
              {!revealed ? (
                <button
                  className="sc-btn sc-btn--primary"
                  onClick={() => setRevealed(true)}
                >
                  Reveal answer
                </button>
              ) : (
                <div className="card-answer">
                  <MD>{plainTeaching(card.answer)}</MD>
                  <p>{plainTeaching(card.explanation)}</p>
                  <a
                    href={
                      cardTeaching(card.id)?.href ??
                      lessonHref(card.lessonId, card.sectionId)
                    }
                  >
                    Return to the explanation →
                  </a>
                  {extensionCardIds.has(card.id) ? (
                    <p className="sc-hint">
                      Optional extension · source claims and teaching context
                      are linked in the explanation.
                    </p>
                  ) : (
                    <Sources
                      course={findLesson(card.lessonId)!.course}
                      claimIds={card.claimIds}
                    />
                  )}
                </div>
              )}
            </div>
            {session.mode === "extra" ? (
              <button
                className="sc-btn sc-btn--primary"
                disabled={!revealed || busy}
                onClick={() => void rate("Good")}
              >
                Next practice card
              </button>
            ) : (
              <div className="rating-buttons" aria-label="Rate your recall">
                {(["Again", "Hard", "Good", "Easy"] as const).map((r) => (
                  <button
                    key={r}
                    className="sc-btn sc-btn--secondary"
                    disabled={!revealed || busy}
                    onClick={() => void rate(r)}
                  >
                    {r}
                  </button>
                ))}
              </div>
            )}
            <p className="sc-hint">
              {session.mode === "extra"
                ? "This session does not change due dates or scheduled review history."
                : "Ratings become available after you reveal the answer. They describe your recall, not a certified skill level."}
            </p>
            <SaveStatus />
          </div>
        )
      ) : (
        <div className="review-options">
          <section className="sc-card">
            <p className="sc-eyebrow">scheduled</p>
            <h2>
              {due.length
                ? `${due.length} cards to revisit`
                : "Nothing is due right now."}
            </h2>
            <p>
              {due.length
                ? `This session takes up to ${data.settings.sessionSize} cards, earliest due first. Revised answers are included.`
                : "New cards have not become overdue. You can introduce a few when you are ready."}
            </p>
            <button
              className="sc-btn sc-btn--primary"
              disabled={!due.length}
              onClick={() => start("due")}
            >
              Review due cards
            </button>
          </section>
          <section className="sc-card">
            <p className="sc-eyebrow">new & optional</p>
            <h2>Introduce one idea at a time.</h2>
            {!cardIds && (
              <label className="sc-field">
                Choose lessons
                <select
                  className="sc-select"
                  value={selectedLesson}
                  onChange={(e) => setSelectedLesson(e.target.value)}
                >
                  <option value="studied">Lessons I have opened</option>
                  <option value="all">All lessons · explicit selection</option>
                  {lessons.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.title}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <p>
              {newCards.length} new cards in this selection. Introduce up to{" "}
              {data.settings.newLimit}.
            </p>
            <div className="actions">
              <button
                className="sc-btn sc-btn--secondary"
                disabled={!newCards.length}
                onClick={() => start("new")}
              >
                Introduce new cards
              </button>
              <button
                className="sc-btn sc-btn--ghost"
                onClick={() => start("extra")}
              >
                Extra practice
              </button>
            </div>
          </section>
        </div>
      )}
      <details className="sc-details">
        <summary>How the review schedule works</summary>
        <p>
          SpicyBrain uses a simple product heuristic. Again returns in 10
          minutes. First Hard, Good, and Easy reviews return in 1, 3, and 7
          days. Later intervals grow by 1.2×, 2×, and 3×, rounded up and capped
          at 365 days. A day is exactly 24 hours. Extra practice never
          reschedules a card.
        </p>
        <p>
          Times are saved in UTC and shown in your local time. This is not a
          medical claim or a named validated memory algorithm.
        </p>
      </details>
      {scheduled.length > 0 && (
        <details
          className="sc-details review-history"
          onToggle={(e) => {
            if (e.currentTarget.open) setHistoryOpen(true);
          }}
        >
          <summary>Scheduled cards & review history</summary>
          {historyOpen && !history && !historyError && (
            <p role="status">Loading card prompts…</p>
          )}
          {historyError && (
            <p className="sc-hint">
              {historyError} Lesson titles remain listed below.
            </p>
          )}
          <ul>
            {scheduled.map((s) => {
              const ref = cardIndex.find((c) => c.id === s.cardId),
                prompt = history?.get(s.cardId)?.prompt;
              return (
                <li key={s.id}>
                  {ref
                    ? `${findLesson(ref.lessonId)?.lesson.title ?? ref.lessonId} · ${prompt ? plainTeaching(prompt) : `card ${s.cardId}`}`
                    : `Removed card ${s.cardId}`}{" "}
                  — due {new Date(s.dueAt).toLocaleString()} · {s.intervalDays}{" "}
                  interval days · revision {s.revision}
                </li>
              );
            })}
          </ul>
          <p>
            {Object.keys(data.reviews).length} immutable scheduled reviews;{" "}
            {Object.keys(data.extraPractice).length} extra-practice records.
          </p>
        </details>
      )}
    </>
  );
}
