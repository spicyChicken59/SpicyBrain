"""Two tempting shortcuts, kept so the tests can show exactly how they fail.

Each takes the retrieval module R (the reference solution, or your completed
starter) so the shortcut differs from the governed pipeline in one decision
only. Do not copy either into a real system.
"""
from __future__ import annotations


def post_filter_search(R, index, query, user, as_of, k=3):
    """WRONG: rank every chunk, cut the list to k, THEN drop what the caller may not read.

    Returns (kept, dropped). Two failures follow: unauthorized chunks were
    scored and ranked (they reached the retrieval output and any log of it),
    and they used up slots, so fewer than k results survive and authorized
    relevant chunks that ranked below them are never seen.
    """
    current = R.current_versions(index.chunks, as_of)
    scores = index.cosine(query)
    hits = [R.Hit(c, round(float(s) + R.freshness_bonus(c, as_of), 6))
            for c, s in zip(index.chunks, scores) if s > 0]
    top = sorted(hits, key=R.order_key)[:k]
    kept = [h for h in top if R.admission(h.chunk, user, as_of, current) is None]
    dropped = [h for h in top if R.admission(h.chunk, user, as_of, current) is not None]
    return kept, dropped


def prompt_only_permission(R, index, query, user, as_of, k=5):
    """WRONG: retrieve by similarity alone and ask the model to ignore what the user may not see.

    The instruction is text beside the passages; the restricted passage is
    already in the context the model receives, so nothing was enforced.
    """
    context = R.assemble_context(R.naive_search(index, query, k))
    context["instruction"] = f"Do not use any passage that {user['user_id']} is not allowed to read."
    return context
