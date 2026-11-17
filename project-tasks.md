# ViDoRe V3 (HR) — task list

**Project:** retrieval evals, then generation + verification, on `vidore/vidore_v3_hr` — 14 documents, 1,110 pages, 318 human-annotated queries with graded relevant pages (0/1/2), bounding boxes and reference answers.
**Yardstick (paper, nDCG@10 on HR):** BM25 12.8 · BGE-M3 42.4 · Jina-v4 text 52.8 · ColEmbed-3B-v2 visual 62.3 · Jina-v4 text + zerank-2 reranker **66.5** · visual + reranker 56.0 (hurt).
**Rules carried over:** measure first; one variable per run; every run saved as a stamped JSON with config + per-query rows; a number that doesn't move is a negative result, logged and reverted; scrutinize the instrument before the system.
**Rhythm:** 4–5 h/day, one task per day, one post per day — _what changed · number before/after · one sentence of why · next_.

---

## Milestone A — Retrieval evals (Days 0–8)

- [ ] **Day 0 — Instrument.** Dump corpus text per page and page images to disk once (`data/pages/{doc_id}/{page}.png`, `.txt`). Write `ndcg_at_k(ranked_pages, graded_qrels)` and `recall_at_k`; unit-test them on a 3-query toy where you know the answer by hand. Load the official qrels straight from HF, never a re-derived copy.
      _Metric:_ tests pass; 318 queries × gold loaded. _P1 vs now:_ in P1 you wrote the dataset; here the dataset is frozen for you and the risk moves to the metric code.

- [ ] **Day 1 — Honest baseline.** Fix the k problem (retrieve 20 chunks → first 10 distinct pages). Report nDCG@10 + recall@10, stratified by `content_type` and `query_type`, for `v0_pypdf_recursive_1000`.
      _Metric:_ nDCG@10 (expect roughly BGE-M3 territory, 35–45). _P1 vs now:_ P1's MRR assumed one binary gold; nDCG rewards ranking the "fully relevant" page above the "critically relevant" one.

- [ ] **Day 2 — Parse-quality audit, then parser swap.** Open the extracted text of 15 gold pages (5 table, 5 chart, 5 text). Score each: readable / garbled / empty. Then swap `PyPDFLoader` → Docling (or `pymupdf4llm`) producing one markdown doc **per page**; re-embed; rerun.
      _Metric:_ nDCG@10 on `has_table`; the audit table itself. _P1 vs now:_ ingestion was never a stage worth measuring in P1; here it may be the biggest lever.

- [ ] **Day 3 — Chunking within a page.** Whole page as one embedding vs 1000/200 chunks within the page (paper: no gain). One variable.
      _Metric:_ nDCG@10 delta. _P1 vs now:_ in P1 chunking decided the ladder (fixed > recursive). If it doesn't matter here, say why (page is already the unit the labels use).

- [ ] **Day 4 — Hybrid, and the BM25 = 12.8 question.** Add your Postgres FTS leg + RRF (your P1 code, not LangChain's). Before running, write down why keyword search gave +9 MRR in P1 and 12.8 nDCG here; then measure.
      _Metric:_ nDCG@10 on `q_numerical`, `has_table`. _P1 vs now:_ exact-identifier questions vs paraphrased analyst questions over tables — the hypothesis to confirm or kill.

- [ ] **Day 5 — Rerank.** `bge-reranker-base` over top-20 → nDCG@10. Record latency per query.
      _Metric:_ nDCG@10 delta vs the paper's +13.7 with zerank-2. _P1 vs now:_ P1's reranker gain was concentrated on contradicted claims; here, which content types does it lift?

- [ ] **Day 6 — Visual retriever (first local model).** A small ColPali-family model (1–3B) over page **images**; index 1,110 pages on Mac MPS or one rented GPU hour; MaxSim scoring. Save embeddings to disk — you won't want to redo this.
      _Metric:_ nDCG@10 vs the text ladder; indexing time and cost. _P1 vs now:_ first retriever that never reads text; first model you run yourself.

- [ ] **Day 7 — Fusion and the reranker-on-visual test.** RRF of text + visual rankings; then rerank the visual list (paper: it hurts).
      _Metric:_ nDCG@10 for both; the hurt/help answer. _P1 vs now:_ in P1 fusion was two text signals; here it's two modalities.

- [ ] **Day 8 — Milestone A write-up.** The ladder table against the paper's numbers, stratified, with the negative results. Post it.
      _Metric:_ every row traceable to a run file.

## Milestone B — Generation + verification (Days 9–15)

- [ ] **Day 9 — Answer generation with page citations.** Generate over the best retriever's top-5 pages; citations as `[file p.N]`; text context first. Save answers + retrieved pages per query. Record cost.
      _P1 vs now:_ citations are pages, not chunk ids; `cited ⊆ retrieved` invariant still applies.

- [ ] **Day 10 — Correctness judge.** Cross-family judge (Claude) scores each answer against the reference: correct / partial / incorrect. Run it 3× on a 50-query slice to report judge variance first.
      _Metric:_ % correct, by query_type; variance. _P1 vs now:_ P1 had no reference answers — faithfulness only; here correctness is measurable and the paper reports ~52–55% on hard queries.

- [ ] **Day 11 — Image context.** Same generation with page images (VLM) and with text+image. Three configs, one judge.
      _Metric:_ % correct delta (paper: image +2.5 on hard queries). _P1 vs now:_ the generator sees pictures for the first time.

- [ ] **Day 12 — Claims dataset (page-level evidence).** ~80 claims: extract from generated answers of 20 queries (mix of content types), label supported / contradicted / no_evidence with evidence = `(file, page)` and, where it's a figure, the bbox from the benchmark. Reuse `validate_claims.py` with a page-exists check instead of a quote check.
      _P1 vs now:_ evidence quotes don't exist for charts; the pointer replaces the quote.

- [ ] **Day 13 — Port `app/verify`, text judge.** Claims → claim-as-query over the best retriever → entailment with page text. Oracle vs retrieved.
      _Metric:_ false-supported rate; confusion matrix. _P1 vs now:_ same core, new evidence type; the boundary rule pays off here.

- [ ] **Day 14 — Multimodal judge.** Pass the page image alongside text. Measure on chart/table claims specifically, plus a new cell: claims about a figure that the text-only judge "supported" from caption alone.
      _Metric:_ false-supported, and caption-only-supported rate. _P1 vs now:_ the judge has eyes; the question is whether it uses them.

- [ ] **Day 15 — End to end + write-up.** Verdict per generated answer vs the correctness judge: where they disagree, read the claims. Cost/latency per verified answer. Full retrospective: P1/P2 vs ViDoRe, every distinction filled with a number.

## Milestone C — Optional stretch (if Days 0–15 land)

- [ ] Reproduce the paper's text baseline exactly (their extractor + a Jina/BGE embedding) to check your harness against a published row.
- [ ] Bounding-box grounding: does the cited page region overlap the annotated bbox? A fourth level of citation precision.
- [ ] Submit the text+rerank pipeline to the ViDoRe leaderboard.

---

## Decisions to record as you go

- Parser choice and why (audit table, not vibes).
- Whether chunking within pages matters on this corpus — and the reason.
- Why BM25 collapses here and worked in P1.
- Whether reranking helps text / hurts visual, replicated or not.
- The cost of the visual retriever (GPU minutes, storage per page) against its nDCG gain.
