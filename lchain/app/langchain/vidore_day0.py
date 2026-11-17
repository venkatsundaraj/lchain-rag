"""Day 0 — instrument for ViDoRe V3 (HR): dataset access, metrics, run-file writer.
 
    python -m vidore.day0 dump      # page images + catalog to data/vidore_hr/
    python -m vidore.day0 test      # metric unit tests on a hand-checked toy
    python -m vidore.day0 score runs/v0.jsonl   # score a run of ranked corpus_ids
 
Everything is keyed by the benchmark's own `corpus_id` (one id per page).
Your retriever returns chunks with (file, page) metadata; map them to
corpus_id ONCE with `catalog.corpus_id_of(file, page)` and never compare
page numbers again.
 
Metrics follow trec_eval / MTEB, which the ViDoRe paper reports:
  nDCG@k  : DCG = sum(rel_i / log2(i + 1)) over the top-k ranked pages,
            linear gain (rel in {0,1,2}), divided by the ideal DCG.
  recall@k: |relevant pages in top-k| / |relevant pages|, relevant = rel > 0.
"""

from dataclasses import dataclass
from pathlib import Path
import json
from collections import defaultdict

DATA = Path("data/vidore_hr")
REPO = "vidore/vidore_v3_hr"
REV = "main" 
RUNS = Path("vidore_runs")

@dataclass
class Catelog:
    page_of:dict[str, tuple[str, int]]
    id_of:dict[tuple[str, int], str]
    qrels:dict[str, tuple[str, int]]
    quries:dict[str, dict]

    def corpus_id_of(self, file_name:str, page:int):
        return self.id_of.get(file_name, page)

    @classmethod
    def load(cls) -> "Catelog":
        cache = DATA / "catelog.json"
        if cache.exists():
            raw = json.loads(cache.read_text())
            return cls(
                page_of={k:tuple(v) for k, v in raw["page_of"]}.items(),
                int_of={(f, p):cid for cid, (f,p) in ((k, tuple(v)) for k, v in raw["page_of"].items())},
                qrels={q: {c:int(r) for c, r in d.items()} for q,d in raw["qrels"].items()},
                queries=raw["queries"]
            )

        from datasets import load_dataset

        corpus  = load_dataset(REPO, "corpus", split="test", revision=REV).remove_columns(["image"])
        queries = load_dataset(REPO, "queries", split="test", revision=REV)
        qrels   = load_dataset(REPO, "qrels", split="test", revision=REV)
        docs    = load_dataset(REPO, "documents_metadata", split="test", revision=REV)

        file_of = {d["doc_id"]: d["file_name"] for d in docs}
        page_of = {c["corpus_id"]:(file_of[c["doc_id"]], c["page_number_in_doc"]) for c in corpus}
        qd = defaultdict(dict)

        for q in qrels:
            qd[str(q["query_id"])[q["corpus_id"]]] = q[int["score"]]

        qr = {str(q["query_id"]): {"query":q["query"], "answer":q.get('answer'), "content_type":q.get('content_type'), "query_types": q.get("query_types")} for q in queries}

        DATA.mkdir(parents=True, exist_ok=True)
        cache.write_text({"page_of":page_of, "qrels":qd, "queries":qr}, ensure_ascii=False)
        return cls.load()


def dump_page_images():
    from datasets import load_dataset

    out = DATA / "pages"
    out.mkdir(parents=True, exist_ok=True)
    corpus = load_dataset(REPO, "corpus", split="test", revision=REV)

    for c in corpus:
        img = out / f"{c["image"]}.png"

        if img.exists():
            c["image"].save(img)

    print(f"{len(corpus)} page images in {out}")


if __name__ == "__main__":
    cat = Catelog.load()
    

















# Day 0 — Instrument. Dump corpus text per page and page images to disk once (data/pages/{doc_id}/{page}.png, .txt). 
# Write ndcg_at_k(ranked_pages, graded_qrels) and recall_at_k; 
# unit-test them on a 3-query toy where you know the answer by hand. 
# Load the official qrels straight from HF, never a re-derived copy. 
# Metric: tests pass; 318 queries × gold loaded. P1 vs now: 
# in P1 you wrote the dataset; here the dataset is frozen for you and the risk moves to the metric code.