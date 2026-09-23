"""lab-l20-retrieval-quality test runner (local-executed, scikit-learn TF-IDF).

    python run_tests.py --evidence <path>     # the reference solution
    python run_tests.py --starter             # your completed starters/retrieval.py

Run from this directory with Python 3.12 and requirements.txt installed.
Offline; no network, no Databricks, no neural embeddings. Every expected
value is either a literal written into this file or a literal committed in
expected/*.json by the independent standard-library derivation described in
DATA.md; no test compares the solution with a value the solution computed.
The two shortcuts in starters/ are asserted to fail for their documented
reasons, and the starter's seven gaps are asserted to be marked. Fixture,
expected, solution, starter and produced-output SHA-256 hashes go into the
evidence JSON.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from functools import cache
from hashlib import sha256
from importlib import import_module, metadata
import json
from pathlib import Path
import platform
import sys
import time
import unittest

sys.dont_write_bytecode = True  # keep the package free of __pycache__
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

STARTER = "--starter" in sys.argv
R = import_module("starters.retrieval" if STARTER else "solutions.retrieval")
from starters import shortcuts  # noqa: E402

LAB = "lab-l20-retrieval-quality"
FIX = ROOT / "fixtures"
NAMES = ("chunks", "rankings", "metrics", "safety", "context", "comparison", "explain", "freshness", "threshold", "update")
EXPECTED = {name: json.loads((ROOT / "expected" / f"{name}.json").read_text(encoding="utf-8")) for name in NAMES}
DOCUMENTS = R.load_documents(FIX / "documents.json")
UPDATE = R.load_documents(FIX / "update.json")
USERS = R.load_users(FIX / "users.json")
K_VALUES, QUERIES = R.load_queries(FIX / "queries.json")
BY_ID = {q["query_id"]: q for q in QUERIES}
OUTPUTS: dict[str, object] = {}
TODAY = date(2026, 9, 20)


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def d(text: str) -> date:
    return date.fromisoformat(text)


def chunks(size: str, documents=DOCUMENTS):
    return R.chunk_corpus(documents, size)


@cache
def index(size: str, header: bool = True):
    return R.LexicalIndex(chunks(size), header=header)


def governed(size: str, query_id: str, **kwargs):
    q = BY_ID[query_id]
    return R.search(index(size), q["text"], USERS[q["user_id"]], d(q["as_of"]), **kwargs)


def naive(size: str, query_id: str):
    return R.naive_search(index(size, False), BY_ID[query_id]["text"])


def post(size: str, query_id: str):
    q = BY_ID[query_id]
    return shortcuts.post_filter_search(R, index(size), q["text"], USERS[q["user_id"]], d(q["as_of"]), k=3)


def listing(hits):
    return [[h.chunk_id, round(h.score, 4)] for h in hits]


def ids(hits):
    return [h.chunk_id for h in hits]


class ListingAssertions(unittest.TestCase):
    def assert_listing(self, produced, expected, label):
        self.assertEqual([row[0] for row in produced], [row[0] for row in expected], label)
        for (_, got), (_, want) in zip(produced, expected):
            self.assertAlmostEqual(got, want, delta=1e-4, msg=label)


class ChunkingTests(unittest.TestCase):
    def test_chunk_ids_counts_and_lengths_match_the_derivation(self):
        for size in R.SIZES:
            produced = chunks(size)
            self.assertEqual([c.chunk_id for c in produced], EXPECTED["chunks"][size]["ids"], size)
            self.assertEqual(len(produced), EXPECTED["chunks"][size]["count"])
            self.assertAlmostEqual(sum(c.words for c in produced) / len(produced), EXPECTED["chunks"][size]["mean_words"], places=2)
        self.assertEqual((len(chunks("small")), len(chunks("large"))), (48, 26))

    def test_small_chunks_are_single_sentences_and_large_chunks_are_whole_sections(self):
        sentences = {s for doc in DOCUMENTS for sec in doc["sections"] for s in sec["sentences"]}
        sections = {" ".join(sec["sentences"]) for doc in DOCUMENTS for sec in doc["sections"]}
        for c in chunks("small"):
            self.assertIn(c.body, sentences, "every sentence here is 11-20 words, so two never fit in 20")
            self.assertLessEqual(c.words, 20)
        for c in chunks("large"):
            self.assertIn(c.body, sections, "every section here is at most 80 words")

    def test_the_header_is_index_text_not_chunk_text(self):
        c = next(c for c in chunks("small") if c.chunk_id == "man-m7-r3:small:1.2")
        self.assertEqual(c.body, "Set the relief valve to 180 bar with the pump warm and the ram at top dead centre.")
        self.assertEqual(R.index_text(c, True), "M7 press service manual. Hydraulic unit. " + c.body)
        self.assertEqual(R.index_text(c, False), c.body)


class AdmissionTests(unittest.TestCase):
    def chunk(self, chunk_id, documents=DOCUMENTS):
        return next(c for c in R.chunk_corpus(documents, "small") if c.chunk_id == chunk_id)

    def test_permission_matrix_written_by_hand(self):
        cases = [
            ("tech-north", "proc-lockout-south:small:1.1", False),  # another plant's procedure
            ("tech-south", "proc-lockout-south:small:1.1", True),
            ("tech-north", "proc-lockout-north:small:1.1", True),
            ("contractor-north", "eng-m7-overpressure:small:1.1", False),  # audience is engineering only
            ("engineer", "eng-m7-overpressure:small:1.1", True),
            ("engineer", "proc-lockout-south:small:1.1", False),  # region 'all' does not add a group
            ("contractor-north", "note-press-hydraulics:small:1.1", True),
            ("contractor-north", "man-m7-r3:small:1.1", False),
            ("tech-south", "proc-daily-north:small:1.1", False),
        ]
        for user, chunk_id, allowed in cases:
            self.assertIs(R.visible(USERS[user], self.chunk(chunk_id)), allowed, f"{user} / {chunk_id}")

    def test_current_version_follows_effective_dates_not_arrival(self):
        corpus = chunks("small")
        self.assertEqual(R.current_versions(corpus, d("2026-05-01"))["man-m7"], 2)
        self.assertEqual(R.current_versions(corpus, d("2026-09-20"))["man-m7"], 3)
        self.assertEqual(R.current_versions(corpus, d("2026-09-20"))["man-l2"], 4)
        self.assertNotIn("draft-m7-relief", R.current_versions(corpus, d("2026-09-20")), "a draft is never current")
        updated = R.chunk_corpus(DOCUMENTS + UPDATE, "small")
        self.assertEqual([R.current_versions(updated, d(day))["man-m7"] for day in ("2026-09-14", "2026-09-15", "2026-10-31", "2026-11-01")],
                         [3, 4, 4, 5])

    def test_each_refusal_names_its_rule(self):
        corpus = chunks("small")
        current = R.current_versions(corpus, TODAY)
        tech = USERS["tech-north"]
        self.assertEqual(R.admission(self.chunk("draft-m7-relief:small:1.1"), tech, TODAY, current), "not approved")
        self.assertEqual(R.admission(self.chunk("man-m7-r2:small:1.1"), tech, TODAY, current), "superseded")
        self.assertEqual(R.admission(self.chunk("proc-lockout-south:small:1.1"), tech, TODAY, current), "not permitted")
        self.assertIsNone(R.admission(self.chunk("man-m7-r3:small:1.1"), tech, TODAY, current))
        early = d("2026-05-01")
        self.assertEqual(R.admission(self.chunk("man-m7-r3:small:1.1"), tech, early, R.current_versions(corpus, early)),
                         "not yet effective")


class RankingTests(ListingAssertions):
    def test_governed_rankings_match_the_derivation(self):
        for size in R.SIZES:
            key = f"governed/{size}"
            for q in QUERIES:
                produced = listing(governed(size, q["query_id"]))
                self.assert_listing(produced, EXPECTED["rankings"][key][q["query_id"]], f"{key} {q['query_id']}")
                OUTPUTS.setdefault(key, {})[q["query_id"]] = produced

    def test_naive_rankings_match_the_derivation(self):
        for size in R.SIZES:
            key = f"naive/{size}"
            for q in QUERIES:
                produced = listing(naive(size, q["query_id"]))
                self.assert_listing(produced, EXPECTED["rankings"][key][q["query_id"]], f"{key} {q['query_id']}")
                OUTPUTS.setdefault(key, {})[q["query_id"]] = produced

    def test_every_governed_result_passes_every_rule_checked_independently(self):
        # The test's own reading of the metadata, not R.admission.
        docs = {doc["doc_id"]: doc for doc in DOCUMENTS}
        for size in R.SIZES:
            for q in QUERIES:
                user, as_of = USERS[q["user_id"]], q["as_of"]
                for hit in governed(size, q["query_id"]):
                    doc = docs[hit.chunk.doc_id]
                    newest = max(o["version"] for o in DOCUMENTS if o["family"] == doc["family"]
                                 and o["status"] == "approved" and o["effective_date"] <= as_of)
                    self.assertEqual(doc["status"], "approved")
                    self.assertLessEqual(doc["effective_date"], as_of)
                    self.assertEqual(doc["version"], newest)
                    self.assertTrue(doc["region"] in ("all", user["region"]) or user["region"] == "all")
                    self.assertTrue(set(doc["audience"]) & set(user["groups"]))

    def test_safety_counts_naive_leaks_and_governed_does_not(self):
        self.assertEqual(EXPECTED["safety"]["naive/small"], {"unauthorized": 12, "draft": 1, "superseded": 7, "not_yet_effective": 1})
        for key, counts in EXPECTED["safety"].items():
            if key.startswith(("governed", "post_filter")):
                self.assertEqual(counts, {"unauthorized": 0, "draft": 0, "superseded": 0, "not_yet_effective": 0}, key)
        produced = {"unauthorized": 0, "draft": 0, "superseded": 0, "not_yet_effective": 0}
        corpus = chunks("small")
        for q in QUERIES:
            user, as_of = USERS[q["user_id"]], d(q["as_of"])
            current = R.current_versions(corpus, as_of)
            for hit in naive("small", q["query_id"]):
                reason = R.admission(hit.chunk, user, as_of, current)
                key = {"not approved": "draft", "not yet effective": "not_yet_effective", "superseded": "superseded",
                       "not permitted": "unauthorized", None: None}[reason]
                if key:
                    produced[key] += 1
        self.assertEqual(produced, EXPECTED["safety"]["naive/small"])
        OUTPUTS["naive_small_safety"] = produced


class FailureCaseTests(unittest.TestCase):
    def test_the_wrong_chunk_wins_q02(self):
        small = ids(governed("small", "q02"))
        self.assertEqual(small[:3], ["note-press-hydraulics:small:1.1", "man-m7-r3:small:1.3", "man-m7-r3:small:1.2"],
                         "a training note and the answer's own neighbour both outrank the answer")
        self.assertEqual(ids(governed("large", "q02"))[:2], ["note-press-hydraulics:large:1.1", "man-m7-r3:large:1.1"])
        self.assertEqual(ids(naive("small", "q02"))[1], "draft-m7-relief:small:1.1", "without rules an unapproved draft ranks second")
        small = index("small")
        explained = {cid: small.explain(BY_ID["q02"]["text"], cid) for cid in EXPECTED["explain"]["q02"]}
        for cid, want in EXPECTED["explain"]["q02"].items():
            self.assertAlmostEqual(explained[cid]["cosine"], want["cosine"], delta=1e-4)
            self.assertEqual([t for t, _ in explained[cid]["terms"]], [t for t, _ in want["terms"]], cid)
        self.assertEqual(explained["note-press-hydraulics:small:1.1"]["terms"][0][0], "setting")
        self.assertNotIn("setting", [t for t, _ in explained["man-m7-r3:small:1.2"]["terms"]], "the answer says 'Set'")
        OUTPUTS["explain_q02"] = explained

    def test_a_newer_authorized_revision_changes_the_answer_context(self):
        updated = R.LexicalIndex(R.chunk_corpus(DOCUMENTS + UPDATE, "small"), header=True)
        q = BY_ID["q03"]
        produced = {}
        for as_of, want in EXPECTED["update"].items():
            hits = R.search(updated, q["text"], USERS["tech-north"], d(as_of))
            ctx = R.assemble_context(hits)
            produced[as_of] = {"top": hits[0].chunk_id, "top_text": hits[0].chunk.body,
                               "context_chunk_ids": [e["chunk_id"] for e in ctx["entries"]]}
            self.assertEqual(produced[as_of], want, as_of)
        self.assertIn("150 operating hours", produced["2026-09-20"]["top_text"])
        self.assertIn("200 operating hours", produced["2026-09-10"]["top_text"], "rev 4 is not effective until 15 September")
        self.assertEqual(ids(governed("small", "q03"))[0], "man-m7-r3:small:1.1", "before the update arrives")
        OUTPUTS["update"] = produced

    def test_the_question_asked_before_rev_3_took_effect_q04(self):
        top = governed("small", "q04")[0]
        self.assertEqual(top.chunk_id, "man-m7-r2:small:1.1")
        self.assertIn("250 operating hours", top.chunk.body)
        self.assertEqual(ids(naive("small", "q04"))[:2], ["man-m7-r3:small:1.1", "man-m7-r2:small:1.1"],
                         "similarity alone puts a revision that was not yet in force first")

    def test_a_relevant_unauthorized_document_is_never_returned(self):
        self.assertEqual(ids(naive("small", "q05"))[:2], ["proc-lockout-south:small:1.1", "proc-lockout-south:small:1.2"])
        governed_q05 = ids(governed("small", "q05"))
        self.assertEqual(governed_q05[0], "proc-lockout-north:small:1.1")
        self.assertFalse([cid for cid in governed_q05 if cid.startswith("proc-lockout-south")])
        self.assertEqual(ids(naive("small", "q06"))[:2], ["eng-m7-overpressure:small:1.1", "eng-m7-overpressure:small:1.2"])
        for size in R.SIZES:
            self.assertFalse([cid for cid in ids(governed(size, "q06")) if cid.startswith("eng-")], size)
            self.assertEqual(ids(governed(size, "q13"))[0], f"eng-m7-overpressure:{size}:1.1", "the engineer may read it")

    def test_prompt_only_permission_leaks_the_restricted_text(self):
        q = BY_ID["q06"]
        leaked = shortcuts.prompt_only_permission(R, index("small"), q["text"], USERS["contractor-north"], d(q["as_of"]))
        texts = " ".join(e["text"] for e in leaked["entries"])
        self.assertIn("220 bar", texts, "the instruction sits beside a passage the contractor may not read")
        self.assertIn("contractor-north", leaked["instruction"])
        safe = R.assemble_context(governed("small", "q06"))
        self.assertNotIn("220 bar", " ".join(e["text"] for e in safe["entries"]))

    def test_post_filtering_scores_restricted_chunks_and_starves_the_list(self):
        for size in R.SIZES:
            for q in QUERIES:
                kept, _ = post(size, q["query_id"])
                self.assertEqual(listing(kept), EXPECTED["rankings"][f"post_filter/{size}"][q["query_id"]], f"{size} {q['query_id']}")
        kept, dropped = post("small", "q05")
        self.assertEqual(ids(kept), ["proc-lockout-north:small:1.1"])
        self.assertEqual(ids(dropped), ["proc-lockout-south:small:1.1", "proc-lockout-south:small:1.2"],
                         "restricted chunks were scored and ranked before anything removed them")
        kept, _ = post("small", "q11")
        self.assertNotIn("proc-daily-south:small:1.2", ids(kept))
        self.assertIn("proc-daily-south:small:1.2", ids(governed("small", "q11"))[:3], "filtering first keeps it")
        OUTPUTS["post_filter_q05"] = {"kept": ids(kept), "dropped": ids(dropped)}

    def test_freshness_bonus_is_scoped_to_bulletins(self):
        tech = USERS["tech-north"]
        produced = {}
        for size in R.SIZES:
            governed_index = index(size)
            q07, q05 = BY_ID["q07"], BY_ID["q05"]
            with_bonus = ids(R.search(governed_index, q07["text"], tech, d(q07["as_of"])))
            without = ids(R.search(governed_index, q07["text"], tech, d(q07["as_of"]), doc_types=()))
            everywhere = ids(R.search(governed_index, q05["text"], tech, d(q05["as_of"]), doc_types=None))
            target = f"bul-2026-004:{size}:1.1"
            produced[size] = {
                "q07_rank_of_bulletin_2026_with_bonus": with_bonus.index(target) + 1,
                "q07_rank_of_bulletin_2026_without_bonus": without.index(target) + 1,
                "q05_top_with_bonus_on_every_type": everywhere[0],
                "q05_rank_of_lockout_with_bonus_on_every_type": everywhere.index(f"proc-lockout-north:{size}:1.1") + 1,
            }
        self.assertEqual(produced, EXPECTED["freshness"])
        self.assertEqual(produced["small"]["q07_rank_of_bulletin_2026_with_bonus"], 1)
        self.assertEqual(produced["small"]["q05_top_with_bonus_on_every_type"], "notice-guarding:small:1.2",
                         "a bonus on every type lifts a newer safety notice above the lockout procedure")
        OUTPUTS["freshness"] = produced

    def test_no_single_score_threshold_separates_abstain_from_answer(self):
        q06_top = governed("small", "q06")[0]
        q05_top = governed("small", "q05")[0]
        produced = {"q06_contractor_top": [q06_top.chunk_id, round(q06_top.score, 4)],
                    "q05_first_relevant": [q05_top.chunk_id, round(q05_top.score, 4)]}
        self.assertEqual(produced["q06_contractor_top"][0], EXPECTED["threshold"]["q06_contractor_top"][0])
        self.assertAlmostEqual(produced["q06_contractor_top"][1], EXPECTED["threshold"]["q06_contractor_top"][1], delta=1e-4)
        self.assertAlmostEqual(produced["q05_first_relevant"][1], EXPECTED["threshold"]["q05_first_relevant"][1], delta=1e-4)
        self.assertIn(q05_top.chunk_id, BY_ID["q05"]["relevant"]["small"])
        self.assertGreater(q06_top.score, q05_top.score,
                           "a cut-off high enough to silence q06 would also drop q05's correct answer")
        OUTPUTS["threshold"] = produced

    def test_lexical_blind_spot_on_a_paraphrase_q08(self):
        ranked = ids(governed("small", "q08"))
        self.assertEqual(ranked[:2], ["man-c4-r2:small:1.2", "man-c4-r2:small:1.1"], "'belt' pulls in the tension section")
        self.assertEqual(ranked.index("man-c4-r2:small:2.1") + 1, 5)
        self.assertNotIn("man-c4-r2:small:2.2", ranked)
        self.assertEqual(R.recall_at_k(ranked, BY_ID["q08"]["relevant"]["small"], 5), 0.5)

    def test_an_exact_identifier_is_a_lexical_strength_q09(self):
        ranked = ids(governed("small", "q09"))
        self.assertEqual(ranked[0], "man-k1-r1:small:1.1")
        self.assertIn("man-m8-r1:small:2.2", ranked, "'417' also matches the M8 stroke length, 417 mm")


class MetricsTests(unittest.TestCase):
    def test_metric_functions_on_a_hand_example(self):
        ranked, relevant = ["a", "b", "c", "d", "e", "f"], ["c", "x"]
        self.assertEqual(R.recall_at_k(ranked, relevant, 1), 0.0)
        self.assertEqual(R.recall_at_k(ranked, relevant, 3), 0.5)
        self.assertEqual(R.recall_at_k(ranked, relevant, 5), 0.5)
        self.assertAlmostEqual(R.reciprocal_rank(ranked, relevant), 1 / 3)
        self.assertEqual(R.reciprocal_rank(["x", "y"], ["z"]), 0.0)
        self.assertEqual(R.reciprocal_rank(["a", "b", "c", "d", "e", "z"], ["z"]), 0.0, "rank 6 is outside MRR@5")

    def test_pipeline_metrics_match_the_derivation(self):
        produced = {}
        for size in R.SIZES:
            runs = {"naive": {q["query_id"]: ids(naive(size, q["query_id"])) for q in QUERIES},
                    "governed": {q["query_id"]: ids(governed(size, q["query_id"])) for q in QUERIES},
                    "post_filter": {q["query_id"]: ids(post(size, q["query_id"])[0]) for q in QUERIES}}
            for mode, results in runs.items():
                produced[f"{mode}/{size}"] = R.evaluate(results, QUERIES, size, K_VALUES)
        self.assertEqual(produced, EXPECTED["metrics"])
        self.assertEqual(produced["governed/small"]["graded_queries"], 12, "q06 has no relevant chunk and is scored separately")
        OUTPUTS["metrics"] = produced

    def test_chunk_size_comparison_matches_the_derivation(self):
        produced = {}
        for size, budget in R.SIZES.items():
            corpus = chunks(size)
            results = {q["query_id"]: governed(size, q["query_id"]) for q in QUERIES}
            metrics = R.evaluate({k: ids(v) for k, v in results.items()}, QUERIES, size, K_VALUES)
            produced[size] = {"budget_words": budget, "chunks": len(corpus),
                              "mean_chunk_words": round(sum(c.words for c in corpus) / len(corpus), 2),
                              **{m: v for m, v in metrics.items() if m.startswith(("recall", "mrr"))},
                              "mean_words_in_top3": round(sum(sum(h.chunk.words for h in hits[:3]) for hits in results.values())
                                                          / len(results), 2)}
        self.assertEqual(produced, EXPECTED["comparison"])
        OUTPUTS["comparison"] = produced


class ContextTests(unittest.TestCase):
    def test_contexts_match_the_derivation(self):
        for size in R.SIZES:
            for q in QUERIES:
                ctx = R.assemble_context(governed(size, q["query_id"]))
                produced = {"words": ctx["words"], "chunk_ids": [e["chunk_id"] for e in ctx["entries"]],
                            "citations": [e["citation"] for e in ctx["entries"]]}
                self.assertEqual(produced, EXPECTED["context"][size][q["query_id"]], f"{size} {q['query_id']}")
                OUTPUTS.setdefault(f"context/{size}", {})[q["query_id"]] = produced

    def test_budget_and_repeated_text_on_a_hand_example(self):
        base = chunks("small")
        pick = {c.chunk_id: c for c in base}
        first = pick["man-m7-r3:small:2.1"]        # 16 words
        duplicate = pick["man-m7-r2:small:2.1"]    # identical text from the superseded revision
        second = pick["man-m7-r3:small:2.2"]       # 17 words
        long_one = pick["note-press-hydraulics:small:1.1"]  # 20 words
        hits = [R.Hit(first, 0.9), R.Hit(duplicate, 0.8), R.Hit(second, 0.7), R.Hit(long_one, 0.6)]
        ctx = R.assemble_context(hits, budget=40)
        self.assertEqual([e["chunk_id"] for e in ctx["entries"]], ["man-m7-r3:small:2.1", "man-m7-r3:small:2.2"])
        self.assertEqual(ctx["words"], 33, "16 + 17; the 20-word chunk would make 53 and ends the context")
        self.assertEqual(ctx["entries"][1]["citation"], "[2] man-m7-r3 §Die change (v3, effective 2026-06-01)")

    def test_citations_outside_the_context_are_rejected(self):
        q03 = R.assemble_context(governed("small", "q03"))
        self.assertEqual(R.check_citations(["man-m7-r3:small:1.1"], q03), [])
        self.assertEqual(R.check_citations(["man-m7-r3:small:1.1", "man-m7-r2:small:1.1"], q03), ["man-m7-r2:small:1.1"])
        q06 = R.assemble_context(governed("small", "q06"))
        self.assertEqual(R.check_citations(["eng-m7-overpressure:small:1.1"], q06), ["eng-m7-overpressure:small:1.1"])

    def test_large_chunks_can_spend_the_budget_on_the_wrong_chunk(self):
        ctx = R.assemble_context(governed("large", "q02"))
        self.assertEqual([e["chunk_id"] for e in ctx["entries"]], ["note-press-hydraulics:large:1.1"])
        self.assertNotIn("180", " ".join(e["text"] for e in ctx["entries"]), "the value never reaches the context")
        small = R.assemble_context(governed("small", "q02"))
        self.assertIn("man-m7-r3:small:1.2", [e["chunk_id"] for e in small["entries"]])


class StarterTests(unittest.TestCase):
    def test_starter_marks_each_gap_and_keeps_the_rest(self):
        from starters import retrieval as S
        doc = DOCUMENTS[0]
        corpus = chunks("small")
        user = USERS["tech-north"]
        calls = {
            "GAP 1": lambda: S.chunk_document(doc, "small"),
            "GAP 2": lambda: S.visible(user, corpus[0]),
            "GAP 3": lambda: S.current_versions(corpus, TODAY),
            "GAP 4": lambda: S.search(None, "q", user, TODAY),
            "GAP 5": lambda: S.recall_at_k(["a"], ["a"], 1),
            "GAP 6": lambda: S.reciprocal_rank(["a"], ["a"]),
            "GAP 7": lambda: S.assemble_context([]),
        }
        for gap, call in calls.items():
            with self.assertRaises(NotImplementedError) as caught:
                call()
            self.assertTrue(str(caught.exception).startswith(gap), gap)
        self.assertEqual((S.SIZES, S.TOP_K, S.CONTEXT_WORDS, S.FRESH_TYPES), (R.SIZES, R.TOP_K, R.CONTEXT_WORDS, R.FRESH_TYPES))
        self.assertEqual(S.check_citations(["x"], {"entries": []}), ["x"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--starter", action="store_true",
                        help="test your completed starters/retrieval.py instead of the reference solution")
    args = parser.parse_args()
    if args.starter and args.evidence:
        parser.error("evidence records the reference solution only; drop --evidence when using --starter")
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    suite = unittest.TestSuite()
    cases = [ChunkingTests, AdmissionTests, RankingTests, FailureCaseTests, MetricsTests, ContextTests]
    if not args.starter:  # the gap check only makes sense on the untouched starter
        cases.append(StarterTests)
    for case in cases:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    exit_code = 0 if result.wasSuccessful() else 1

    def hashes(directory: str) -> dict[str, str]:
        return {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path.read_bytes()).hexdigest()
                for path in sorted((ROOT / directory).iterdir()) if path.is_file()}

    packages = ("scikit-learn", "numpy", "scipy", "joblib", "threadpoolctl")
    evidence = {
        "lab": LAB, "executionClass": "local-executed", "runtime": "ml",
        "python": platform.python_version(), "interpreter": sys.executable,
        "packages": {name: metadata.version(name) for name in packages},
        "java": "not used", "spark": "not used", "platform": platform.system() + " " + platform.release(),
        "startedAt": started_at.isoformat(), "finishedAt": datetime.now(timezone.utc).isoformat(),
        "durationSeconds": round(time.monotonic() - started, 3),
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "exit": exit_code,
        "fixtureHashes": hashes("fixtures"), "expectedHashes": hashes("expected"),
        "solutionHashes": {**hashes("solutions"), **hashes("starters"),
                           "run_tests.py": sha256((ROOT / "run_tests.py").read_bytes()).hexdigest()},
        "outputHashes": {name: sha256(canonical(value).encode("utf-8")).hexdigest() for name, value in sorted(OUTPUTS.items())},
        "commands": [f"{Path(sys.executable).name} run_tests.py --evidence <path>"],
        "notes": ("Local scikit-learn TfidfVectorizer on one machine: lexical TF-IDF retrieval, not neural embeddings, "
                  "not an approximate nearest-neighbour index and not Databricks AI Search (formerly Vector Search). "
                  "No Spark, no Databricks, no network, no model call. Expected values are literals in this runner or "
                  "in expected/*.json, written by the independent standard-library derivation in "
                  "expected/derive_expected.py (DATA.md). The post-filter and prompt-only shortcuts in starters/ are "
                  "asserted to fail for their documented reasons; the starter's seven gaps are asserted to be marked. "
                  "The maintenance library, users, queries and relevance labels are fictional."),
    }
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence[key] for key in ("lab", "python", "tests", "failures", "errors", "skipped", "exit")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
