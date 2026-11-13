from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
from langchain_community.document_loaders import PyPDFLoader
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from app.config import settings
import json
from collections import defaultdict


pdf_rep = Path('data/pdfs')
CONFIG = "v0_pypdf_recursive_1000"
K = 5
splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 200)

# chunking
chunks = []
for p in sorted(pdf_rep.glob("*.pdf")):
    page = PyPDFLoader(str(p)).load()
    chunks += splitter.split_documents(page)


# indexing

store = PGVector(
            embeddings=OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.OPENAI_API_KEY),
            connection=settings.DATABASE_URL,
            use_jsonb=True, 
            collection_name=CONFIG,
            pre_delete_collection=True, 
                 )

store.add_documents(chunks)
retriever = store.as_retriever(search_kwargs = {"k":K})

rows, by_type = [], defaultdict(lambda: {"n":0, "rr":0.0, "hit":0})
for line in Path('data/eval/hr_gold.jsonl').open():
    g = json.loads(line)
    gold = [(i["file"], i["page"]) for i in g["gold_pages"]]
    got = retriever.invoke(g["question"])
    got_pages = [(Path(i.metadata["source"]).name, i.metadata["page"]) for i in got]

    rank = next((i+1 for i, p in enumerate(got_pages) if p in gold), None)

    rows.append({**g, "retrieved_pages":got_pages, "first_hit_rank":rank})

    VISUAL = {"Chart", "Table", "Infographic", "Image"}
    types = set(g["content_type"])
    group = "text_only" if types <= {"Text", "Other"} else "has_visual"
    for t in [group] + [f"has_{x.lower()}" for x in sorted(types & VISUAL)]:
        s = by_type[t]
        s["n"] += 1
        s["hit"] += rank is not None
        s["rr"] += 1 / rank if rank else 0

    
print(by_type)