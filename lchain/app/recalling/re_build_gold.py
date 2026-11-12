
from datasets import load_dataset
from pathlib import Path
import json
from collections import defaultdict

REPO = "vidore/vidore_v3_hr"
REV = 'main'

corpus = load_dataset(REPO, "corpus", split="test", revision=REV).remove_columns("image")
docs = load_dataset(REPO, "documents_metadata", split="test", revision=REV)
qrels = load_dataset(REPO, "qrels", split="test", revision=REV)
queries = load_dataset(REPO, "queries", split="test", revision=REV)

PAGE = "page_number_in_doc"

file_of = {f["doc_id"]: f["file_name"] for f in docs}
page_of = {c["corpus_id"]: (file_of[c["doc_id"]], c[PAGE]) for c in corpus}

# qrid = {r["query_id"]: page_of[r["corpus_id"]] for r in qrels}

gold = defaultdict(list)

for q in qrels:
    if q["score"] <= 0:
        continue
    f, p = page_of[q["corpus_id"]]
    gold[q["query_id"]].append({"file":f, "page":p, "score":q["score"]})
print(len(gold))
if __name__ == "__main__":
    import argparse
    par = argparse.ArgumentParser()
    res = par.add_argument('--hello', default='hello world')
    result = par.parse_args()
    # print(result.hello)

    # output_path = Path('data/result') / "result.jsonl"
    # output_path.parent.mkdir(parents=True, exist_ok=True)
    # with output_path.open("w", encoding="utf-8") as f:
    #     for row in corpus:
    #         f.write(json.dumps(row, ensure_ascii=True, default=str) + "\n")

    # print(f"{len(corpus)} recorded at {output_path}")

    out = Path('data')
    out.mkdir(parents=True, exist_ok=True)
    rows = 0
    with open(out / 'result.jsonl', 'w') as fh:
        for q in queries:
            pages = gold[q["query_id"]]
            print(len(pages))
            fh.write(json.dumps({"query_id": q["query_id"], 
                                 "answer":q["answer"], 
                                 "content_type":q["content_type"], 
                                 "query_types":q["query_types"],
                                  "gold_pages":[{"file_name":f["file"], "page":f["page"], "score":f["score"]} for f in pages]}) + "\n")


    # print(corpus.features,"\n\n", docs.features, "\n\n", qrels.features, "\n\n", queries.features)