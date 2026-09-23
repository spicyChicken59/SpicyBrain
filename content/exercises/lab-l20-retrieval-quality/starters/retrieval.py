"""Starter for lab-l20: complete the seven marked gaps (see TASKS.md).

Everything that is not a gap already works: loading, the Chunk and Hit
records, the contextual header, the TF-IDF index (scikit-learn's
TfidfVectorizer with its defaults), admission reasons, the freshness bonus,
the ranking order, naive search, evaluation, citations and the citation
check. Run the tests from the lab directory; the starter gaps are expected to
raise NotImplementedError until you fill them.

This is lexical retrieval on one machine: no neural embeddings and no call to
Databricks AI Search (formerly Vector Search) or any other service.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

SIZES = {"small": 20, "large": 80}          # maximum body words per chunk
TOP_K = 5
FRESH_TYPES = ("bulletin",)                  # time-sensitive document types
FRESH_BONUS = 0.05
FRESH_WINDOW_DAYS = 365
CONTEXT_WORDS = 60


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    family: str
    version: int
    effective_date: date
    region: str
    audience: tuple[str, ...]
    status: str
    doc_type: str
    title: str
    heading: str
    size: str
    body: str
    words: int


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float

    @property
    def chunk_id(self) -> str:
        return self.chunk.chunk_id


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_documents(path: Path) -> list[dict]:
    return load_json(path)["documents"]


def load_users(path: Path) -> dict[str, dict]:
    return {u["user_id"]: u for u in load_json(path)["users"]}


def load_queries(path: Path) -> tuple[list[int], list[dict]]:
    data = load_json(path)
    return data["k_values"], data["queries"]


# --- chunking ---------------------------------------------------------------

def chunk_document(document: dict, size: str) -> list[Chunk]:
    """Pack whole sentences into chunks of at most SIZES[size] words; never cross a section."""
    raise NotImplementedError("GAP 1: pack whole sentences into chunks of at most SIZES[size] words inside one section; ids are <doc_id>:<size>:<section>.<chunk>, both counted from 1")


def chunk_corpus(documents: list[dict], size: str) -> list[Chunk]:
    return [chunk for document in documents for chunk in chunk_document(document, size)]


def index_text(chunk: Chunk, header: bool) -> str:
    """The text the index sees: a contextual header (title and heading) plus the body, or the body alone."""
    return f"{chunk.title}. {chunk.heading}. {chunk.body}" if header else chunk.body


# --- the lexical index --------------------------------------------------------

class LexicalIndex:
    """TF-IDF over every chunk of one chunking; filters decide which rows are ever scored."""

    def __init__(self, chunks: list[Chunk], header: bool = True):
        self.chunks = list(chunks)
        self.header = header
        self.vectorizer = TfidfVectorizer()
        self.matrix = self.vectorizer.fit_transform([index_text(c, header) for c in self.chunks])
        self.position = {c.chunk_id: i for i, c in enumerate(self.chunks)}

    def cosine(self, query: str, rows: list[int] | None = None) -> np.ndarray:
        q = self.vectorizer.transform([query])
        matrix = self.matrix if rows is None else self.matrix[rows]
        return (matrix @ q.T).toarray().ravel()

    def explain(self, query: str, chunk_id: str) -> dict:
        """Per-term contributions (query weight x chunk weight); they sum to the cosine."""
        q = self.vectorizer.transform([query]).toarray().ravel()
        v = self.matrix[self.position[chunk_id]].toarray().ravel()
        terms = self.vectorizer.get_feature_names_out()
        parts = [(str(terms[i]), float(q[i] * v[i])) for i in np.nonzero(q * v)[0]]
        parts.sort(key=lambda p: (-p[1], p[0]))
        return {"cosine": round(sum(x for _, x in parts), 4), "terms": [[t, round(x, 4)] for t, x in parts]}


# --- admission: every rule runs before ranking --------------------------------

def visible(user: dict, chunk: Chunk) -> bool:
    """Permission: the caller's region matches (or either side is 'all') AND a group is in the audience."""
    raise NotImplementedError("GAP 2: admit a chunk when the regions match (or either is 'all') AND one of the caller's groups is in the audience")


def current_versions(chunks: list[Chunk], as_of: date) -> dict[str, int]:
    """Highest approved version of each family that is effective on as_of (independent of the caller)."""
    raise NotImplementedError("GAP 3: return {family: highest approved version effective on as_of}; the caller does not change the answer")


def admission(chunk: Chunk, user: dict, as_of: date, current: dict[str, int]) -> str | None:
    """None when admitted, otherwise the first rule that refuses the chunk."""
    if chunk.status != "approved":
        return "not approved"
    if chunk.effective_date > as_of:
        return "not yet effective"
    if current.get(chunk.family) != chunk.version:
        return "superseded"
    if not visible(user, chunk):
        return "not permitted"
    return None


def freshness_bonus(chunk: Chunk, as_of: date, doc_types: tuple[str, ...] | None = FRESH_TYPES) -> float:
    """A small preference for recent time-sensitive documents; None applies it to every type."""
    if doc_types is not None and chunk.doc_type not in doc_types:
        return 0.0
    age = (as_of - chunk.effective_date).days
    return FRESH_BONUS if 0 <= age <= FRESH_WINDOW_DAYS else 0.0


def order_key(hit: Hit):
    return (-hit.score, -hit.chunk.effective_date.toordinal(), hit.chunk_id)


def search(index: LexicalIndex, query: str, user: dict, as_of: date, k: int = TOP_K,
           doc_types: tuple[str, ...] | None = FRESH_TYPES) -> list[Hit]:
    """Governed retrieval: admit first, score only the admitted rows, then rank."""
    raise NotImplementedError("GAP 4: admit first (admission() is None), score only the admitted rows, add freshness_bonus, drop zero scores, sort by order_key, keep k")


def naive_search(index: LexicalIndex, query: str, k: int = TOP_K) -> list[Hit]:
    """Similarity alone: no admission rules, no freshness preference."""
    scores = index.cosine(query)
    hits = [Hit(c, round(float(s), 6)) for c, s in zip(index.chunks, scores) if s > 0]
    return sorted(hits, key=order_key)[:k]


# --- evaluation ---------------------------------------------------------------

def recall_at_k(ranked: list[str], relevant: list[str], k: int) -> float:
    raise NotImplementedError("GAP 5: the share of the relevant chunks that appear in the first k results")


def reciprocal_rank(ranked: list[str], relevant: list[str], k: int = TOP_K) -> float:
    raise NotImplementedError("GAP 6: 1 / rank of the first relevant chunk within the first k results, 0.0 when none")


def evaluate(results: dict[str, list[str]], queries: list[dict], size: str, k_values: list[int]) -> dict:
    """Mean recall@k and MRR@5 over the queries that have at least one relevant chunk."""
    graded = [q for q in queries if q["relevant"][size]]
    out = {"graded_queries": len(graded),
           "mean_results": round(sum(len(results[q["query_id"]]) for q in queries) / len(queries), 4)}
    for k in k_values:
        out[f"recall@{k}"] = round(sum(recall_at_k(results[q["query_id"]], q["relevant"][size], k)
                                       for q in graded) / len(graded), 4)
    out[f"mrr@{TOP_K}"] = round(sum(reciprocal_rank(results[q["query_id"]], q["relevant"][size])
                                    for q in graded) / len(graded), 4)
    return out


# --- context assembly and citations -------------------------------------------

def citation(chunk: Chunk, n: int) -> str:
    return f"[{n}] {chunk.doc_id} §{chunk.heading} (v{chunk.version}, effective {chunk.effective_date.isoformat()})"


def assemble_context(hits: list[Hit], budget: int = CONTEXT_WORDS) -> dict:
    """Spend the word budget in rank order; skip repeated text; stop at the first chunk that does not fit."""
    raise NotImplementedError("GAP 7: spend the budget in rank order, skip repeated text, stop at the first chunk that does not fit, number the citations from 1")


def check_citations(cited_chunk_ids: list[str], context: dict) -> list[str]:
    """Return every cited chunk that is not in the assembled context (a deterministic check, not a judge)."""
    present = {e["chunk_id"] for e in context["entries"]}
    return [cid for cid in cited_chunk_ids if cid not in present]
