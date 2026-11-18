import math
def dcg(gains: list[int]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))
 
 
def ndcg_at_k(ranked: list[str], rels: dict[str, int], k: int) -> float:
    """ranked: corpus_ids, best first, duplicates already removed.
    rels: corpus_id -> graded relevance (>0). Linear gain, log2 discount."""
    if not rels:
        return 0.0
    gains = [rels.get(cid, 0) for cid in ranked[:k]]
    ideal = sorted(rels.values(), reverse=True)[:k]
    return dcg(gains) / dcg(ideal)
 
 
def recall_at_k(ranked: list[str], rels: dict[str, int], k: int) -> float:
    if not rels:
        return 0.0
    return len(set(ranked[:k]) & set(rels)) / len(rels)
 
 
def first_hit_rank(ranked: list[str], rels: dict[str, int]) -> int | None:
    return next((i + 1 for i, cid in enumerate(ranked) if cid in rels), None)
 
 
def dedupe_keep_order(ids: list[str]) -> list[str]:
    seen, out = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i); out.append(i)
    return out
 