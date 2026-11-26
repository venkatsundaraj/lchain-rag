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
import math
import json
from datetime import datetime, timezone
from collections import defaultdict
from app.langchain.helpers.metrics import dedupe_keep_order, first_hit_rank, recall_at_k, ndcg_at_k, dcg

DATA = Path("data/vidore_hr")
REPO = "vidore/vidore_v3_hr"
REV = "main" 
RUNS = Path("vidore_runs")

PDF_DIR = Path("data/pdfs")

_rp = DATA / "page_remap.json"
REMAP = json.loads(_rp.read_text()) if _rp.exists() else {}



@dataclass
class Catalog:
    page_of: dict[str, tuple[str, int]]          # corpus_id -> (file_name, page_number_in_doc)
    id_of: dict[tuple[str, int], str]            # (file_name, page) -> corpus_id
    qrels: dict[str, dict[str, int]]             # query_id -> {corpus_id: rel}
    queries: dict[str, dict]                     # query_id -> {query, answer, content_type, query_types}
 
    def corpus_id_of(self, file_name: str, page: int) -> str | None:
        rm = REMAP.get(file_name)
        if rm is not None:
            page = rm.get(str(page))
            if page is None:
                return None           # a page the benchmark doesn't have -> counts as unmapped
        return self.id_of.get((file_name, page))
 
    @classmethod
    def load(cls) -> "Catalog":
        cache = DATA / "catalog.json"
        if cache.exists():
            raw = json.loads(cache.read_text())
            return cls(
                page_of={k: tuple(v) for k, v in raw["page_of"].items()},
                id_of={(f, p): cid for cid, (f, p) in ((k, tuple(v)) for k, v in raw["page_of"].items())},
                qrels={q: {c: int(r) for c, r in d.items()} for q, d in raw["qrels"].items()},
                queries=raw["queries"],
            )
        
        from datasets import load_dataset
 
        corpus = load_dataset(REPO, "corpus", split="test", revision=REV).remove_columns("image")
        docs = load_dataset(REPO, "documents_metadata", split="test", revision=REV)
        qrels = load_dataset(REPO, "qrels", split="test", revision=REV)
        queries = load_dataset(REPO, "queries", split="test", revision=REV)
 
        file_of = {d["doc_id"]: d["file_name"] for d in docs}
        page_of = {c["corpus_id"]: (file_of[c["doc_id"]], int(c["page_number_in_doc"])) for c in corpus}
        qd: dict[str, dict[str, int]] = defaultdict(dict)
        for r in qrels:
            if int(r["score"]) > 0:
                qd[str(r["query_id"])][r["corpus_id"]] = int(r["score"])
        qs = {str(q["query_id"]): {"query": q["query"], "answer": q.get("answer"),
                                   "content_type": q.get("content_type"), "query_types": q.get("query_types")}
              for q in queries}
        DATA.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"page_of": page_of, "qrels": qd, "queries": qs}, ensure_ascii=False))
        return cls.load()
 


def dump_page_images():
    from datasets import load_dataset

    out = DATA / "pages"
    out.mkdir(parents=True, exist_ok=True)
    corpus = load_dataset(REPO, "corpus", split="test", revision=REV)

    for c in corpus:
        img = out / f"{c['corpus_id']}.png"
        if not img.exists():
            c["image"].save(img)

    print(f"{len(corpus)} page images in {out}")



VISUAL = {"Chart", "Table", "Infographic", "Image"}


def score_run(rows: list[dict], cat: Catalog, ks=(5, 10), config: dict | None = None) -> dict:
    per_q, groups = [], defaultdict(list)
    for r in rows:
        qid = str(r["query_id"]); rels = cat.qrels.get(qid, {})
        if not rels:
            continue
        ranked = dedupe_keep_order(r["ranked"])
        m = {"query_id": qid, "n_gold": len(rels), "first_hit_rank": first_hit_rank(ranked, rels)}
        for k in ks:
            m[f"ndcg@{k}"] = ndcg_at_k(ranked, rels, k)
            m[f"recall@{k}"] = recall_at_k(ranked, rels, k)
        per_q.append(m)
        q = cat.queries[qid]
        types = set(q.get("content_type") or [])
        groups["text_only" if types <= {"Text", "Other"} else "has_visual"].append(m)
        for t in types & VISUAL:
            groups[f"has_{t.lower()}"].append(m)
        for qt in q.get("query_types") or []:
            groups[f"q_{qt}"].append(m)
        groups[f"n_gold_{min(len(rels), 4)}{'+' if len(rels) >= 4 else ''}"].append(m)
 
    def agg(ms):
        n = len(ms)
        out = {"n": n}
        for k in ks:
            out[f"ndcg@{k}"] = round(sum(x[f"ndcg@{k}"] for x in ms) / n, 4)
            out[f"recall@{k}"] = round(sum(x[f"recall@{k}"] for x in ms) / n, 4)
        out["mrr"] = round(sum(1 / x["first_hit_rank"] for x in ms if x["first_hit_rank"]) / n, 4)
        return out
 
    return {"config": config or {}, "aggregates": agg(per_q),
            "by_group": {g: agg(ms) for g, ms in sorted(groups.items())}, "rows": per_q}
 
 
def save_run(result: dict, name: str) -> Path:
    RUNS.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    p = RUNS / f"{stamp}_{name}.json"
    result["config"]["timestamp"] = datetime.now(timezone.utc).isoformat()
    p.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return p
 

def save_run(result: dict, name: str) -> Path:
    RUNS.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    p = RUNS / f"{stamp}_{name}.json"
    result["config"]["timestamp"] = datetime.now(timezone.utc).isoformat()
    p.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return p

def print_report(result: dict, k: int = 10) -> None:
    a = result["aggregates"]
    print(f"\nn={a['n']}  nDCG@{k}={a[f'ndcg@{k}']:.3f}  recall@{k}={a[f'recall@{k}']:.3f}  MRR={a['mrr']:.3f}")
    for g, s in result["by_group"].items():
        print(f"  {g:14s} n={s['n']:4d}  nDCG@{k}={s[f'ndcg@{k}']:.3f}  recall@{k}={s[f'recall@{k}']:.3f}")

def _tests() -> None:
    rels = {"A": 2, "B": 1, "C": 1}             # 3 relevant pages, one of them "fully"
    # perfect order: A, B, C -> nDCG 1
    assert abs(ndcg_at_k(["A", "B", "C"], rels, 10) - 1.0) < 1e-9
    # swap A and B: DCG = 1/log2(2) + 2/log2(3) + 1/log2(4); IDCG = 2 + 1/log2(3) + 1/2
    got = ndcg_at_k(["B", "A", "C"], rels, 10)
    exp = (1 + 2 / math.log2(3) + 0.5) / (2 + 1 / math.log2(3) + 0.5)
    assert abs(got - exp) < 1e-9, (got, exp)
    # nothing relevant in top-k
    assert ndcg_at_k(["X", "Y"], rels, 10) == 0.0
    # k cuts both the list and the ideal
    assert abs(ndcg_at_k(["A"], rels, 1) - 1.0) < 1e-9
    # recall
    assert abs(recall_at_k(["A", "X", "C"], rels, 3) - 2 / 3) < 1e-9
    assert recall_at_k(["X"], rels, 5) == 0.0
    # dedupe keeps first occurrence and order
    assert dedupe_keep_order(["A", "A", "B", "A", "C"]) == ["A", "B", "C"]
    # first hit
    assert first_hit_rank(["X", "B"], rels) == 2 and first_hit_rank(["X"], rels) is None
    print("metrics ok")

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "test"
    if cmd == "test":
        _tests()
    elif cmd == "dump":
        cat = Catalog.load()
        print(f"{len(cat.page_of)} pages, {len(cat.qrels)} queries with qrels, "
              f"{sum(len(v) for v in cat.qrels.values())} graded pairs")
        dump_page_images()
    elif cmd == "score":
        cat = Catalog.load()
        rows = [json.loads(l) for l in Path(sys.argv[2]).read_text().splitlines() if l.strip()]
        res = score_run(rows, cat, config={"source": sys.argv[2]})
        print_report(res)
        print("saved:", save_run(res, Path(sys.argv[2]).stem))

















# Day 0 — Instrument. Dump corpus text per page and page images to disk once (data/pages/{doc_id}/{page}.png, .txt). 
# Write ndcg_at_k(ranked_pages, graded_qrels) and recall_at_k; 
# unit-test them on a 3-query toy where you know the answer by hand. 
# Load the official qrels straight from HF, never a re-derived copy. 
# Metric: tests pass; 318 queries × gold loaded. P1 vs now: 
# in P1 you wrote the dataset; here the dataset is frozen for you and the risk moves to the metric code.