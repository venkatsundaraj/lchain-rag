
from app.vidore.loader import Catalog, REPO, REV, score_run, print_report, save_run
import json
from pathlib import Path
from collections import Counter
from app.config import settings


 
COLLECTION = "v0_pypdf_recursive_1000"
RUN_NAME   = "v0_pypdf_chunks"
CHUNKING   = "recursive_1000_200"      # "page" | "recursive_1000_200"

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
        collection_name=COLLECTION,
        use_jsonb=True,
        connection=settings.DATABASE_URL,
        pre_delete_collection=reindex,
    )
    if reindex:
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        docs = []
        for pdf in sorted(PDF_DIR.glob("*.pdf")):
            docs += PyPDFLoader(str(pdf)).load()                 # one Document per page

        if CHUNKING == "page":
            chunks = [d for d in docs if d.page_content.strip()]
        else:
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = splitter.split_documents(docs)

        store.add_documents(chunks)
        print(f"indexed {len(chunks)} units ({CHUNKING})")
    return store
 
    
    # print({k: qs[0] for k in column_name if k != "query"})




if __name__ == "__main__":
    import argparse
    ar = argparse.ArgumentParser()
    ar.add_argument('--reindex', action="store_true")
    ar.add_argument('--k', type=int, default=N_CHUNKS)
    ar.add_argument('--collection', default=COLLECTION)
    ar.add_argument('--run', default=RUN_NAME)
    ar.add_argument('--chunking', default=CHUNKING, choices=["page", "recursive_1000_200"])

    args = ar.parse_args()
    COLLECTION, RUN_NAME, CHUNKING = args.collection, args.run, args.chunking

    cat = Catalog.load()
    qids, qfilter = load_eval_queries(cat)
    
    store = build_store(args.reindex)
    retriever = store.as_retriever(search_kwargs={"k": args.k})

    rows, unmapped = [], Counter()
    for i, id in enumerate(qids, 1):
        docs = retriever.invoke(input=cat.queries[id]["query"])

        ranked = []
        for d in docs:
            cid = cat.corpus_id_of(Path(d.metadata["source"]).name, int(d.metadata["page"]))
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

    n_ranked = sum(len(r["ranked"]) for r in rows)
    assert n_ranked > 0, "retriever returned nothing — wrong collection name or empty index?"
    print(f"ranked ids: {n_ranked} across {len(rows)} queries")

    RUNS.mkdir(exist_ok=True)
    raw = RUNS / f"{RUN_NAME}.jsonl"
    raw.write_text("\n".join(json.dumps(r) for r in rows))
 
    result = score_run(rows, cat, config={
        "name": RUN_NAME, "collection": COLLECTION, "retriever": "vector",
        "embedding": "text-embedding-3-small", "parser": "pypdf",
        "chunking": CHUNKING, "k_chunks": args.k,
        "query_filter": qfilter, "n_queries": len(rows),
    })
    print_report(result)
    print("saved:", save_run(result, RUN_NAME))

   

    

    



# python -m app.vidore.retriever --collection v0_pypdf_recursive_1000 --run v0_pypdf_chunks --chunking recursive_1000_200
# python -m app.vidore.retriever --collection v1_pypdf_page            --run v1_pypdf_page  --chunking page