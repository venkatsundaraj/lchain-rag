import math

def precision_at_k(ranks:list[bool], k = 4):
    top = ranks[:k]
    if top is None:
        return 0.0
    return sum(top) / len(top)


def recalling(ranks:list[str], evidences:list[str], k=5):
    items = [i in ranks[:5] for i in evidences]
    # top = items[:5]
    if not items:
        return 0.0
    return sum(items) / len(evidences)

def first_hit(ranked):
    for i, r in enumerate(ranked):
        if r:
            return i + 1
    return 0.0

def mrr(ranked):
    val = []
    for i, r in enumerate(ranked):
        if r:
            val.append(1/(1+i))
    return sum(val) / len(val)




def dcg_at_k(ranked, relevant, k):
    score = 0.0

    for rank, chunk in enumerate(ranked[:k], start=1):
        rel = int(chunk in relevant)
        score += rel / math.log2(rank + 1)
    
    return score


if __name__ == "__main__":
    ranked = ["67", "110", "22", "48", "88", "100"]
    g_evidences = ["48", "96", "110", "85", "100"]
    k = 4

    is_chunk_relevant = [i in g_evidences for i in ranked]
    print("relevancy", is_chunk_relevant)

    precision = precision_at_k(is_chunk_relevant, k)
    print("precision", precision)

    recall_at_k = recalling(ranked, g_evidences, k)
    print("recall",recall_at_k)

    first_hit_value = first_hit(is_chunk_relevant)
    print("first hit", first_hit_value)
   
   
    mrr_value = mrr(is_chunk_relevant)
    print("mrr", mrr_value)

    relevant = set(g_evidences)
    dcg_vlaue = dcg_at_k(ranked, relevant, 6)
    ideal_relevances = [1] * min(len(relevant), 6)

    idcg = sum(
        rel / math.log2(rank + 1)
        for rank, rel in enumerate(ideal_relevances, start=1)
    )

    print("dcg values", dcg_vlaue/idcg)



    