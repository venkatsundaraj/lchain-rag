
from app.langchain.loader import Catalog, REPO, REV, score_run, print_report, save_run
import json
from pathlib import Path
from collections import Counter
from app.config import settings


 
CONFIG = "v0_pypdf_recursive_1000"
PDF_DIR = Path("data/pdfs")
RUNS = Path("vidore_runs")
N_CHUNKS = 20

def load_eval_queries(cat:Catalog) ->tuple[list[str], dict]:
    from datasets import load_dataset

    qs = load_dataset(REPO, "queries", split="test", revision=REV)
    cols = qs.column_names
    

    lang_col = next((i for i in cols if "lang" in i.lower()), None)
    fmt_col = next((i for i in cols if "format" in i.lower()), None)

    rows = list(qs)
    used = {}

    

    if lang_col:
        before = len(rows)
        rows = [r for r in rows if str(r[lang_col]).lower() in ("en", "eng", "english")]
        used[lang_col] = "en"
        print(f"  language filter {lang_col}=en: {before} -> {len(rows)}")
    # if fmt_col:
    #     before = len(rows)
    #     rows = [r for r in rows if str(r[fmt_col]).lower() == "question"]
    #     used[fmt_col] = "question"

    ids = [str(r["query_id"]) for r in rows if str(r["query_id"]) in cat.qrels]
    print("  !! not 318 -- inspect the columns above and adjust the filter before trusting numbers")
    print(len(set(ids)), len(rows))
    return ids, used



def build_store(reindex: bool):
    from langchain_openai import OpenAIEmbeddings
    from langchain_postgres import PGVector
 
    store = PGVector(
        embeddings=OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.OPENAI_API_KEY),
        collection_name=CONFIG,
        use_jsonb=True,
        connection=settings.DATABASE_URL,
        pre_delete_collection=reindex,
    )
    if reindex:
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
 
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = []
        for pdf in sorted(PDF_DIR.glob("*.pdf")):
            chunks += splitter.split_documents(PyPDFLoader(str(pdf)).load())
        store.add_documents(chunks)
        print(f"indexed {len(chunks)} chunks")
    return store
 
    
    # print({k: qs[0] for k in column_name if k != "query"})




if __name__ == "__main__":
    import argparse
    ar = argparse.ArgumentParser()
    ar.add_argument('--reindex', action="store_true")
    ar.add_argument('--k', type=int, default=N_CHUNKS)
    args = ar.parse_args()

    cat = Catalog.load()
    qids, qfilter = load_eval_queries(cat)
    
    store = build_store(args.reindex)
    retriever = store.as_retriever(search_kewargs = {"k": args.k})

    rows, unmapped = [], Counter()
    for i, id in enumerate(qids, 1):
        docs = retriever.invoke(input=cat.queries[id]["query"])

        ranked = []
        for d in docs:
            cid = cat.id_of[(Path(d.metadata["source"]).name, int(d.metadata["page"]))]
            if cid is None:
                unmapped[(Path(d.metadata["source"]), int(d.metadata["page"]))] += 1
            else:
                ranked.append(cid)

            rows.append({"query_id":id, "ranked":ranked})

            if i % 50 == 0:
                print(f"  {id}/{len(qids)}")


    print(f"\nunmapped chunks: {sum(unmapped.values())} "
          f"(should be 0; if many, your page index is off by one)")
    for (f, p), n in unmapped.most_common(5):
        print(f"   {f} p{p}: {n}")

    RUNS.mkdir(exist_ok=True)
    raw = RUNS / f"{CONFIG}.jsonl"
    raw.write_text("\n".join(json.dumps(r) for r in rows))
 
    result = score_run(rows, cat, config={
        "name": CONFIG, "retriever": "vector", "embedding": "text-embedding-3-small",
        "parser": "pypdf", "chunking": "recursive_1000_200", "k_chunks": args.k,
        "query_filter": qfilter, "n_queries": len(rows),
    })
    print_report(result)
    print("saved:", save_run(result, CONFIG))

   

    

    


