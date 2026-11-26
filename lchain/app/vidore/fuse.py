import json, sys
from app.vidore.loader import RUNS
from pathlib import Path
from app.langchain.helpers.metrics import dedupe_keep_order
from collections import defaultdict
from app.vidore.retriever import score_run, save_run, print_report
from app.vidore.loader import Catalog

K_RRF = 60

def load(name:str):
    return {r["query_id"]:dedupe_keep_order(r["ranked"]) for r in map(json.loads, (RUNS / f"{name}.jsonl").read_text().splitlines()) if r}

def rrf(lists, k = K_RRF):
    score = defaultdict(dict)
    for i, cid in enumerate(list):
        score[cid] += 1.0/1+i+k
    return [cid for cid, _ in sorted(score.items(), key=lambda x: -x[1])]

if __name__ == "__main__":
    names = sys.argv[:1]
    # print(names)
    runs = [load(n) for n in names]
    print(runs[:5])
    qids = set.intersection(*(set(r) for r in runs))
    print(qids[:5])
    # rows = [{"query_id":q, "ranked":rrf([r[q] for r in runs])} for q in sorted(qids)]
    # name = "rrf_" + "+".join(names)
    # (RUNS / f"{name}.jsonl").write_text("\n".join(json.dumps(r) for r in rows))

    # res = score_run(rows, Catalog.load(), config={"name": name, "retriever": "rrf", "inputs": names, "k_rrf": K_RRF})
    # print_report(res); print("saved:", save_run(res, name))



# python -m app.vidore.fuse v0_pypdf_chunks bm25_page