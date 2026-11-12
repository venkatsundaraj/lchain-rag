

from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from app.config import settings
from collections import defaultdict
import json, time

CONFIG = "v0_pypdf_recursive_1000"
PDF_DIR = Path("data/pdfs")
GOLD = Path("data/eval/hr_gold.jsonl")

# Chunking

K=5
splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap=200)
chunks = []

for pdf in sorted(PDF_DIR.glob('*.pdf')):
    pages = PyPDFLoader(str(pdf)).load()
    chunks += splitter.split_documents(pages)




# Indexing

store = PGVector(
    embeddings=OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.OPENAI_API_KEY,),
    collection_name=CONFIG,
     use_jsonb=True,
     connection=settings.DATABASE_URL, 
     pre_delete_collection=True
)

store.add_documents(chunks)
retriever = store.as_retriever(search_kwargs = {"k":K})

rows, by_type = [], defaultdict(lambda :{"n":0, "rr":0.0, "hit":0})
for line in GOLD.open():
    q = json.loads(line)
    gold = [(i["file"], i['page'])for i in q["gold_pages"]]
    got = retriever.invoke(q['question'])
    got_pages = [(Path(d.metadata['source']).name, d.metadata["page"]) for d in got]
    rank = next((i + 1 for i, p in enumerate(got_pages) if p in gold), None)
    rows.append({**q, "retrieved_pages":got_pages, "first_hit_rank": rank})

    VISUAL = {"Chart", "Table", "Infographic", "Image"}
    types = set(q["content_type"])
    group = "text_only" if types <= {"Text", "Other"} else "has_visual"
    for t in [group] + [f"has_{x.lower()}" for x in sorted(types & VISUAL)]:
        s = by_type[t]
        s["n"] += 1
        s["hit"] += rank is not None
        s["rr"] += 1 / rank if rank else 0



# Save every intermediate, then report

run = Path("runs") / f"{CONFIG}_{int(time.time())}.jsonl"
run.parent.mkdir(exist_ok=True)
run.write_text("\n".join(json.dumps(r) for r in rows))

n = len(rows)
hits = sum(r["first_hit_rank"] is not None for r in rows)
mrr = sum(1 / r["first_hit_rank"] for r in rows if r["first_hit_rank"]) / n
print(f"\n{CONFIG}  queries={n}  hit@{K}={hits/n:.3f}  MRR={mrr:.3f}")
for t, s in sorted(by_type.items()):
    print(f"  {t:12s} n={s['n']:3d}  hit@{K}={s['hit']/s['n']:.3f}  MRR={s['rr']/s['n']:.3f}")