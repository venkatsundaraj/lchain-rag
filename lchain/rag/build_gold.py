# scripts/build_gold.py
import json, pathlib
from collections import defaultdict
from datasets import load_dataset
from pypdf import PdfReader

REPO = "vidore/vidore_v3_hr"
REV = "main"   # replace with the commit hash from "Files and versions", to freeze it

corpus  = load_dataset(REPO, "corpus", split="test", revision=REV).remove_columns(["image"])
queries = load_dataset(REPO, "queries", split="test", revision=REV)
qrels   = load_dataset(REPO, "qrels", split="test", revision=REV)
docs    = load_dataset(REPO, "documents_metadata", split="test", revision=REV)

print(corpus.features)   # look for the page-index field; set PAGE_FIELD below to its name
PAGE_FIELD = "page_number_in_doc"
assert PAGE_FIELD in corpus.features, f"pick the page field from: {list(corpus.features)}"

file_of = {d["doc_id"]: d["file_name"] for d in docs}
page_of = {c["corpus_id"]: (file_of[c["doc_id"]], c[PAGE_FIELD]) for c in corpus}

print(page_of)

gold = defaultdict(list)
for r in qrels:
    if r["score"] <= 0:                      # 0 = annotated as NOT relevant
        continue
    f, p = page_of[r["corpus_id"]]
    gold[r["query_id"]].append((f, p, r["score"]))

pdf_dir = pathlib.Path("data/pdfs")
n_pages = {f: len(PdfReader(pdf_dir / f).pages) for f in file_of.values()}

out = pathlib.Path("data/eval"); out.mkdir(parents=True, exist_ok=True)
rows = 0
with open(out / "hr_gold.jsonl", "w") as fh:
    for q in queries:
        if q["language"] != "english":
            continue
        pages = sorted(set(gold[q["query_id"]]))
        assert pages, f"query {q['query_id']} has no relevant pages"
        fh.write(json.dumps({
            "query_id": q["query_id"],
            "question": q["query"],
            "answer": q["answer"],
            "content_type": [t for t in q["content_type"] if not t.startswith("N/A")],
            "query_types": q["query_types"],
            "gold_pages": [{"file": f, "page": p, "score": s} for f, p, s in pages],
        }) + "\n")
        rows += 1
print(rows, "queries written")   # expect 318