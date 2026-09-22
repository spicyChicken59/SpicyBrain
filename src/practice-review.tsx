import { useRef, useState } from "react";
import {
  cards,
  extensionCardIds,
  cardTeaching,
  plainTeaching,
  courses,
  findLesson,
  lessonHref,
  lessons,
  scenarios,
} from "./catalog";
import { applyReview, nowISO, reviewQueue, type Rating } from "./study";
import { MD, PageTitle, SaveStatus, Sources, useStudy, uuid } from "./ui";

export function Practice({ id }: { id?: string }) {
  const { data, store } = useStudy(),
    [ratings, setRatings] = useState<
      Record<string, "weak" | "partial" | "strong">
    >({}),
    [message, setMessage] = useState("");
  const entry = scenarios.find((s) => s.scenario.id === id);
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
      <div className="practice-workspace">
        <article className="sc-doc sc-doc--flat">
          <h2>The situation</h2>
          <MD>{s.context}</MD>
          {s.disclosures.length > 0 && (
            <section>
              <h2>Ask the stakeholders</h2>
              <p className="sc-hint">
                These are authored teaching disclosures, not an AI conversation.
                Open a question when you are ready to learn more.
              </p>
              {s.disclosures.map((d) => (
                <details key={d.question} className="sc-details stakeholder">
                  <summary>{d.question}</summary>
                  <MD>{d.response}</MD>
                </details>
              ))}
            </section>
          )}
          <h2>Your task</h2>
          <MD>{s.task}</MD>
          <ul>
            {s.requirements.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
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
          <details className="sc-details model-response">
            <summary>Reveal model response and reasoning</summary>
            <h2>One defensible response</h2>
            <MD>{s.model}</MD>
            <h3>Why this works</h3>
            <MD>{s.reasoning}</MD>
          </details>
          <h2>Self-assessment</h2>
          <p>
            You choose the rating. This is educational feedback, not automated
            evaluation or an employer score.
          </p>
          {s.rubric.map((r) => (
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
              if (s.rubric.some((r) => !ratings[r.id])) {
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
                        {s.rubric.find((r) => r.id === id)?.criterion ?? id}:{" "}
                        {value}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </details>
          )}
          <Sources course={course} claimIds={s.claimIds} />
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
  const selection = cardIds
    ? cards.filter((c) => cardIds.includes(c.id))
    : cards;
  const [session, setSession] = useState<{
      mode: "due" | "new" | "extra";
      ids: string[];
      index: number;
    } | null>(null),
    [revealed, setRevealed] = useState(false),
    [busy, setBusy] = useState(false);
  const eventId = useRef(uuid()),
    guard = useRef(false);
  const clock = nowISO();
  const due = reviewQueue(selection, data, clock, 100000);
  const openedCore = (c: (typeof cards)[number]) =>
    !extensionCardIds.has(c.id) &&
    (!!data.positions[c.lessonId] ||
      Object.values(data.beatPositions).some(
        (p) => cardTeaching(c.id)?.beatId === p.beatId,
      ));
  const newCards = selection.filter(
    (c) =>
      !data.schedules[c.id] &&
      (selectedLesson === "all" ||
        (selectedLesson === "studied" && openedCore(c)) ||
        selectedLesson === c.lessonId),
  );
  const start = (mode: "due" | "new" | "extra") => {
    const pool =
      mode === "due"
        ? due.slice(0, data.settings.sessionSize)
        : mode === "new"
          ? newCards.slice(0, data.settings.newLimit)
          : selection
              .filter(
                (c) =>
                  selectedLesson === "all" ||
                  (selectedLesson === "studied" && openedCore(c)) ||
                  selectedLesson === c.lessonId,
              )
              .slice(0, data.settings.sessionSize);
    setSession({ mode, ids: pool.map((c) => c.id), index: 0 });
    setRevealed(false);
    guard.current = false;
    eventId.current = uuid();
  };
  const card = session
    ? cards.find((c) => c.id === session.ids[session.index])
    : null;
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
        card ? (
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
        ) : (
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
      {Object.keys(data.schedules).length > 0 && (
        <details className="sc-details">
          <summary>Scheduled cards & review history</summary>
          <ul>
            {Object.values(data.schedules)
              .sort(
                (a, b) =>
                  a.dueAt.localeCompare(b.dueAt) || a.id.localeCompare(b.id),
              )
              .map((s) => (
                <li key={s.id}>
                  {cards.find((c) => c.id === s.cardId)?.prompt ??
                    `Removed card ${s.cardId}`}{" "}
                  — due {new Date(s.dueAt).toLocaleString()} · {s.intervalDays}{" "}
                  interval days · revision {s.revision}
                </li>
              ))}
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
