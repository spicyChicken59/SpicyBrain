"""Independent derivation of the lab-l20 expected literals (standard library only).

    python expected/derive_expected.py            # print the derived values
    python expected/derive_expected.py --write    # rewrite expected/*.json from them

This script shares no code with solutions/ and does not import scikit-learn.
It re-implements the lab contract from DATA.md by hand: sentence packing into
chunks, the four admission rules, TF-IDF with the documented smooth-idf
formula written out term by term, cosine ranking, recall@k, reciprocal rank
and the 60-word context budget. The committed expected/*.json files were
written by this script once and then checked by hand for the cases DATA.md
works through; run_tests.py compares the scikit-learn solution against those
committed literals and never against this script's live output.
"""
from __future__ import annotations

import json
import math
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE.parent / "fixtures"
SIZES = {"small": 20, "large": 80}
BONUS = 0.05
BONUS_DAYS = 365
BONUS_TYPES = {"bulletin"}
TOP = 5
CONTEXT_WORDS = 60
TOKEN = re.compile(r"(?u)\b\w\w+\b")


def load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def pack(document, size):
    budget = SIZES[size]
    chunks = []
    for s_no, section in enumerate(document["sections"], start=1):
        groups, current = [], []
        for sentence in section["sentences"]:
            if current and len(" ".join(current + [sentence]).split()) > budget:
                groups.append(current)
                current = []
            current.append(sentence)
        if current:
            groups.append(current)
        for c_no, group in enumerate(groups, start=1):
            body = " ".join(group)
            chunks.append({
                "chunk_id": f"{document['doc_id']}:{size}:{s_no}.{c_no}",
                "doc": document, "heading": section["heading"], "body": body,
                "words": len(body.split()),
            })
    return chunks


def text_for(chunk, header):
    if header:
        return f"{chunk['doc']['title']}. {chunk['heading']}. {chunk['body']}"
    return chunk["body"]


def tokens(text):
    return TOKEN.findall(text.lower())


class Index:
    """Hand-written TF-IDF: raw counts, idf = ln((1 + n) / (1 + df)) + 1, unit length."""

    def __init__(self, chunks, header):
        self.chunks = chunks
        docs = [tokens(text_for(c, header)) for c in chunks]
        n = len(docs)
        df = {}
        for toks in docs:
            for term in set(toks):
                df[term] = df.get(term, 0) + 1
        self.idf = {term: math.log((1 + n) / (1 + count)) + 1 for term, count in df.items()}
        self.vectors = [self.vector(toks) for toks in docs]

    def vector(self, toks):
        weights = {}
        for term in toks:
            if term in self.idf:
                weights[term] = weights.get(term, 0.0) + self.idf[term]
        norm = math.sqrt(sum(w * w for w in weights.values()))
        return {t: w / norm for t, w in weights.items()} if norm else {}

    def cosine(self, query, i):
        q = self.vector(tokens(query))
        v = self.vectors[i]
        return sum(w * v.get(t, 0.0) for t, w in q.items())


def day(text):
    return date.fromisoformat(text)


def visible(user, document):
    region_ok = document["region"] == "all" or user["region"] == "all" or document["region"] == user["region"]
    return region_ok and bool(set(document["audience"]) & set(user["groups"]))


def current_versions(documents, as_of):
    best = {}
    for d in documents:
        if d["status"] == "approved" and day(d["effective_date"]) <= day(as_of):
            if d["family"] not in best or d["version"] > best[d["family"]]:
                best[d["family"]] = d["version"]
    return best


def admitted(chunk, user, as_of, current):
    d = chunk["doc"]
    return (d["status"] == "approved" and day(d["effective_date"]) <= day(as_of)
            and current.get(d["family"]) == d["version"] and visible(user, d))


def bonus(document, as_of, types=BONUS_TYPES):
    """Freshness preference: time-sensitive types only, effective within the last 365 days."""
    if types is not None and document["doc_type"] not in types:
        return 0.0
    age = (day(as_of) - day(document["effective_date"])).days
    return BONUS if 0 <= age <= BONUS_DAYS else 0.0


def order_key(item):
    score, chunk = item
    return (-score, -day(chunk["doc"]["effective_date"]).toordinal(), chunk["chunk_id"])


def search(index, query, user, as_of, documents, mode, k=TOP, types=BONUS_TYPES):
    current = current_versions(documents, as_of)
    scored = []
    for i, chunk in enumerate(index.chunks):
        if mode == "governed" and not admitted(chunk, user, as_of, current):
            continue
        cos = index.cosine(query, i)
        if cos <= 0:
            continue
        extra = 0.0 if mode == "naive" else bonus(chunk["doc"], as_of, types)
        scored.append((round(cos + extra, 6), chunk))
    scored.sort(key=order_key)
    top = scored[:k]
    if mode == "post_filter":
        top = [item for item in top if admitted(item[1], user, as_of, current)]
    return top


def metrics(rows, k_values):
    graded = [r for r in rows if r["relevant"]]
    out = {"graded_queries": len(graded),
           "mean_results": round(sum(len(r["ranked"]) for r in rows) / len(rows), 4)}
    for k in k_values:
        out[f"recall@{k}"] = round(sum(len(set(r["ranked"][:k]) & set(r["relevant"])) / len(r["relevant"])
                                       for r in graded) / len(graded), 4)
    rr = []
    for r in graded:
        rank = next((i for i, cid in enumerate(r["ranked"][:TOP], start=1) if cid in r["relevant"]), None)
        rr.append(1 / rank if rank else 0.0)
    out[f"mrr@{TOP}"] = round(sum(rr) / len(rr), 4)
    return out


def context(ranked):
    included, seen, used = [], set(), 0
    for score, chunk in ranked:
        if chunk["body"] in seen:
            continue
        if used + chunk["words"] > CONTEXT_WORDS:
            break
        seen.add(chunk["body"])
        used += chunk["words"]
        d = chunk["doc"]
        included.append({
            "n": len(included) + 1, "chunk_id": chunk["chunk_id"],
            "citation": f"[{len(included) + 1}] {d['doc_id']} §{chunk['heading']} (v{d['version']}, effective {d['effective_date']})",
            "text": chunk["body"],
        })
    return {"words": used, "entries": included}


def explain(index, query, chunk_id):
    """Per-term contributions (query weight x chunk weight) that sum to the cosine."""
    i = next(n for n, c in enumerate(index.chunks) if c["chunk_id"] == chunk_id)
    q = index.vector(tokens(query))
    v = index.vectors[i]
    parts = sorted(((t, w * v[t]) for t, w in q.items() if t in v), key=lambda p: (-p[1], p[0]))
    return {"cosine": round(sum(x for _, x in parts), 4), "terms": [[t, round(x, 4)] for t, x in parts]}


def rank_of(ranked, chunk_id):
    ids = [c["chunk_id"] for _, c in ranked]
    return ids.index(chunk_id) + 1 if chunk_id in ids else None


def derive():
    documents = load("documents.json")["documents"]
    update = load("update.json")["documents"]
    users = {u["user_id"]: u for u in load("users.json")["users"]}
    qfile = load("queries.json")
    queries, k_values = qfile["queries"], qfile["k_values"]
    by_id = {q["query_id"]: q for q in queries}
    out = {"chunks": {}, "rankings": {}, "metrics": {}, "safety": {}, "context": {}, "comparison": {},
           "explain": {}, "freshness": {}, "threshold": {}, "update": {}}
    governed_indexes = {}
    for size in SIZES:
        chunks = [c for d in documents for c in pack(d, size)]
        out["chunks"][size] = {"count": len(chunks),
                               "mean_words": round(sum(c["words"] for c in chunks) / len(chunks), 2),
                               "ids": [c["chunk_id"] for c in chunks]}
        indexes = {"naive": Index(chunks, header=False), "governed": Index(chunks, header=True)}
        governed_indexes[size] = indexes["governed"]
        for mode in ("naive", "governed", "post_filter"):
            index = indexes["naive" if mode == "naive" else "governed"]
            rows, unsafe = [], {"unauthorized": 0, "draft": 0, "superseded": 0, "not_yet_effective": 0}
            key = f"{mode}/{size}"
            out["rankings"][key] = {}
            top3_words = []
            for q in queries:
                user = users[q["user_id"]]
                k = 3 if mode == "post_filter" else TOP
                ranked = search(index, q["text"], user, q["as_of"], documents, mode, k=k)
                ids = [c["chunk_id"] for _, c in ranked]
                out["rankings"][key][q["query_id"]] = [[c["chunk_id"], round(sc, 4)] for sc, c in ranked]
                rows.append({"ranked": ids, "relevant": q["relevant"][size]})
                top3_words.append(sum(c["words"] for _, c in ranked[:3]))
                current = current_versions(documents, q["as_of"])
                for _, c in ranked:
                    d = c["doc"]
                    unsafe["unauthorized"] += not visible(user, d)
                    unsafe["draft"] += d["status"] != "approved"
                    unsafe["not_yet_effective"] += day(d["effective_date"]) > day(q["as_of"])
                    unsafe["superseded"] += (d["status"] == "approved" and day(d["effective_date"]) <= day(q["as_of"])
                                             and current.get(d["family"]) != d["version"])
            out["metrics"][key] = metrics(rows, k_values)
            out["safety"][key] = unsafe
            if mode == "governed":
                out["comparison"][size] = {"budget_words": SIZES[size], "chunks": len(chunks),
                                           "mean_chunk_words": out["chunks"][size]["mean_words"],
                                           **{m: v for m, v in out["metrics"][key].items() if m.startswith(("recall", "mrr"))},
                                           "mean_words_in_top3": round(sum(top3_words) / len(top3_words), 2)}
        index = indexes["governed"]
        out["context"][size] = {}
        for q in queries:
            ranked = search(index, q["text"], users[q["user_id"]], q["as_of"], documents, "governed")
            ctx = context(ranked)
            out["context"][size][q["query_id"]] = {"words": ctx["words"], "chunk_ids": [e["chunk_id"] for e in ctx["entries"]],
                                                   "citations": [e["citation"] for e in ctx["entries"]]}
    small = governed_indexes["small"]
    q02 = by_id["q02"]["text"]
    out["explain"]["q02"] = {cid: explain(small, q02, cid) for cid in
                             ("note-press-hydraulics:small:1.1", "man-m7-r3:small:1.3", "man-m7-r3:small:1.2")}
    tech = users["tech-north"]
    q07, q05 = by_id["q07"], by_id["q05"]
    for size, index in governed_indexes.items():
        with_bonus = search(index, q07["text"], tech, q07["as_of"], documents, "governed")
        without = search(index, q07["text"], tech, q07["as_of"], documents, "governed", types=set())
        universal = search(index, q05["text"], tech, q05["as_of"], documents, "governed", types=None)
        out["freshness"][size] = {
            "q07_rank_of_bulletin_2026_with_bonus": rank_of(with_bonus, f"bul-2026-004:{size}:1.1"),
            "q07_rank_of_bulletin_2026_without_bonus": rank_of(without, f"bul-2026-004:{size}:1.1"),
            "q05_top_with_bonus_on_every_type": universal[0][1]["chunk_id"],
            "q05_rank_of_lockout_with_bonus_on_every_type": rank_of(universal, f"proc-lockout-north:{size}:1.1"),
        }
    q06 = search(small, by_id["q06"]["text"], users["contractor-north"], by_id["q06"]["as_of"], documents, "governed")
    q05_ranked = search(small, q05["text"], tech, q05["as_of"], documents, "governed")
    out["threshold"] = {"q06_contractor_top": [q06[0][1]["chunk_id"], round(q06[0][0], 4)],
                        "q05_first_relevant": [q05_ranked[0][1]["chunk_id"], round(q05_ranked[0][0], 4)]}
    # Altered input: a newer revision arrives and the index is rebuilt.
    both = documents + update
    chunks = [c for d in both for c in pack(d, "small")]
    index = Index(chunks, header=True)
    q03 = by_id["q03"]
    for as_of in ("2026-09-10", "2026-09-20", "2026-11-05"):
        ranked = search(index, q03["text"], tech, as_of, both, "governed")
        ctx = context(ranked)
        out["update"][as_of] = {"top": ranked[0][1]["chunk_id"], "top_text": ranked[0][1]["body"],
                                "context_chunk_ids": [e["chunk_id"] for e in ctx["entries"]]}
    return out


NAMES = ("chunks", "rankings", "metrics", "safety", "context", "comparison", "explain", "freshness", "threshold", "update")


def main():
    out = derive()
    if "--write" in sys.argv:
        for name in NAMES:
            (HERE / f"{name}.json").write_text(json.dumps(out[name], indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("comparison", "safety", "explain", "freshness", "threshold", "update")}, indent=1))


if __name__ == "__main__":
    main()
