from datasets import load_dataset
from app.langchain.retriever import build_store
from app.langchain.loader import Catalog
from pathlib import Path
from collections import Counter
from app.langchain.helpers.metrics import dedupe_keep_order, first_hit_rank, recall_at_k, ndcg_at_k, dcg
import json
from collections import defaultdict

CONFIG = "vidore/vidore_v3_hr"
REV = "main"

RUNS = Path('test') 


qrels = load_dataset(CONFIG, "qrels", split="test", revision=REV)
queries = load_dataset(CONFIG, "queries", split="test", revision=REV)

res = set([id["query_id"] for id in queries])

# let's take the analogy of left join table. here the qrels is the left table
# we want to be added with queries on query_id

def dedup_rank(items:list[str])->list[str]:
    seen, out = set(), []
    for r in items:
        if r not in seen:
            out.append(r);seen.add(i)
    return out

VISUAL = {"Chart", "Table", "Infographic", "Image"}

def score_run_v1(rows:list[dict], cat:Catalog, ks=(5, 10)):
    per_q, groups = [], defaultdict(list)
    for i, r in enumerate(rows, 1):
        if i > 2:
             break
        rels = cat.qrels.get(str(r["query_id"]), {})
        if not rels:
                    continue
        ranked = dedup_rank(r["ranked"])
        m = {"query_id":qid, "n_gold":len(rels), "first_hit_rank":first_hit_rank(ranked, qrels)}
        # print(rels, r["ranked"])
        for k in ks:
             m[f"ndcg@{k}"] = ndcg_at_k(ranked, rels, k)
             m[f"recall@{k}"] = recall_at_k(ranked, rels, k)
        # print(m, "mmmm")
        per_q.append(m)
        query = cat.queries[(str(r["query_id"]))]
        types = set(query.get('content_type',[]))
        groups["text_only" if types <= {"Text", "Other"} else "has_visual"].append(m)
        for q in types & VISUAL:
             groups[f"has_{q.lower()}"].append(m)
        for t in query.get("query_types") or []:
             groups[f"q_{t.lower()}"].append(m)
        groups[f"n_gold_{min(len(rels), 4)}{'+' if len(rels) >= 4 else ''}"].append(m)
        RUNS.mkdir(parents=True, exist_ok=True)
        FILE = RUNS /  "test.json"
        output = {
            "groups": {
                key: list(value)
                for key, value in groups.items()
            }
}

        FILE.write_text(json.dumps(output, indent=2), encoding="utf-8")
       
        # FILE.write_text(json.dumps({"groups": groups}, default=list, indent=2), encoding="utf-8")

             


if __name__ == "__main__":
    from argparse import ArgumentParser
    ap = ArgumentParser()
    ap.add_argument('--k', type=int)
    print(list(res)[:10])
    args = ap.parse_args()

    cat = Catalog.load()
    
    lang_col = next((i for i in queries.column_names if "lang" in i.lower()), None)
    qids = {id["query_id"] for id in qrels}
    rows = []
    if lang_col:
        print(True)
        rows = [r for r in queries if r["query_id"]]

    store = build_store(False)
    retrieved = store.as_retriever(search_kewargs = {"k":args.k})
    queries_data = [str(i["query_id"]) for i in rows]

    items, unmapped = [], Counter()
    for i, qid in enumerate(queries_data[:100], 1):
        # print(len(cat.queries))
        docs = retrieved.invoke(input=cat.queries[qid]["query"])
        ranked = []
        for d in docs:
            cid = cat.id_of[(Path(d.metadata["source"]).name, int(d.metadata["page"]))]
            if cid is None:
                unmapped[(Path(d.metadata["source"]), int(d.metadata["page"]))] += 1
            else:
                ranked.append(cid)

            items.append({"query_id":qid, "ranked":ranked})

            if i % 50 == 0:
                print(f"  {qid}/{len(qids)}")
    print(items,"items")
    resule = score_run_v1(items, cat)


        



    