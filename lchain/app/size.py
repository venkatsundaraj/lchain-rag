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

gold = defaultdict(list)
for r in qrels:
    gold[r["query_id"]].append(page_of[r["corpus_id"]])

pdf_dir = pathlib.Path("data/pdfs")
n_pages = {f: len(PdfReader(pdf_dir / f).pages) for f in file_of.values()}

out = pathlib.Path("data/eval"); out.mkdir(parents=True, exist_ok=True)
rows = 0
with open(out / "hr_gold.jsonl", "w") as fh:
    for q in queries:
        if q["language"] != "english":
            continue
        pages = sorted(set(gold[q["query_id"]]))
        for f, p in pages:
            assert 0 <= p < n_pages[f] or 1 <= p <= n_pages[f], (f, p)
        fh.write(json.dumps({
            "query_id": q["query_id"],
            "question": q["query"],
            "answer": q["answer"],
            "content_type": q["content_type"],
            "query_types": q["query_types"],
            "gold_pages": [{"file": f, "page": p} for f, p in pages],
        }) + "\n")
        rows += 1
print(rows, "queries written")   # expect 318