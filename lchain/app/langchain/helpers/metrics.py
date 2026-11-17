import math

def dcg(gains:list[int]) ->float:
    return sum(g/math.log2(i+2) for i, g in enumerate(gains))

def nccg_at_k(ranks:list[str], rels:dict[str, int], k:int) -> float:
    gains = [rels.get(cid, 0) for cid in ranks[:k]]
    ideals = sorted(rels.values(), reverse=True)[:k]

    return dcg(gains)/dcg(ideals)

def recall_at_k(ranks:list[str], rels:dict[str, int], k:int) -> float:
    if not ranks:
        return 0.0
    return (len(set(ranks[:k]) & set(rels))) / len(rels)



def first_hit_at_k(ranks:list[str], rels:dict[str, int], k:int) -> float:
    return next((i+1 for i, cid in enumerate(ranks) if cid in rels), None)

def dedupe_keep_order(ids:list[int]) ->list[int]:
    seen, out = set(), []

    for i in ids:
        if i not in seen:
            seen.add(i); out.append(i)

    return out