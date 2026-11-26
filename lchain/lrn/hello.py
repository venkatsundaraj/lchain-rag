
from dataclasses import dataclass
from app.config import settings
from app.vidore.loader import Catalog
from collections import defaultdict
from app.vidore.loader import REPO, REV

@dataclass(frozen=True, slots=True)
class Doc:
    no:str
    name:str

if __name__ == "__main__":
    from pypdf import PdfReader
    cat = Catalog.load()
    a = {"1": "hello", "2":"world", "3":"venkat"}
    m = {"1": "hello", "2":"world", "3":"venkat", "1":"world"}
    b = [
            {"doc_id":"1", "corpus_id":13}, 
            {"doc_id":"2", "corpus_id":14}, 
            {"doc_id":"3", "corpus_id":15}
         ]

    d = {c["corpus_id"]: a[c["doc_id"]] for c in b}
    # print(settings.OPENAI_API_KEY)
    chunks = []
    chunk_one = []
    for i in a:
        chunks += {i:i, a[i]:a[i]}

        # chunk_one.append(i)
        chunk_one.extend([i, a[i]])


    print(chunks)
    print(chunk_one)

    # m["1"] = "world"
    # print(m)
    gold = defaultdict(list)
    gold = {"one":[1, 2, 3], "two":[4, 6, 7]}
    # for i in a:
    #     print(i, a[i], len(a))

    x = {"world", "hello"}
    y = {"world", "hello", "hello"}
    # print(sorted(x & y))
    # if y <= x:
    #     print(True)

    rows = [1, 2, 3, 1, 2, 4]
    rows_v1 = [0, "", None, " ", 5]
    hit_at_k = sum(rows)/len(rows)

    # print(hit_at_k)
    print("one" in gold, True)

    item = next((i+1 for i, p in enumerate(x) if p in y), None)

    from pypdf import PdfReader
    r = PdfReader("data/pdfs/employment_and_social_developments_in_europe_2024-KEBD24002ENN.pdf")

    from datasets import load_dataset
    # docs = load_dataset(REPO, "documents_metadata", split="test", revision=REV)
    # print(docs.column_names)
    # print([d for d in docs if "2024" in d["file_name"]][0])

    from pathlib import Path
    print(len(PdfReader(Path("~/Downloads/hello.pdf").expanduser()).pages))


    cat = Catalog.load()
    print(cat.corpus_id_of("posting_of_workers-KE0224850ENN.pdf", 3))              # expect a corpus_id string like "812"
    print(cat.corpus_id_of("employment_and_social_developments_in_europe_2024-KEBD24002ENN.pdf", 75))  # expect the id for bench p70 → "126"
    qid = "6"; print(cat.qrels[qid])                                                # gold ids for a query you scored 1.0 before

    
    # 1. where is page 126's text in YOUR pdf?
    # for i, p in enumerate(r.pages):
    #     if "quality employment, access to quality education and training" in (p.extract_text() or ""):
    #         print("found at index", i)

    # # 2. page counts: your PDFs vs the benchmark, per file
    # from collections import Counter
    # bench = Counter(f for f, _ in cat.page_of.values())
    # for f, n in sorted(bench.items()):
    #     mine = len(PdfReader(f"data/pdfs/{f}").pages)
    #     print(f"{'OK ' if mine == n else 'XX '}{f[:50]:50s} benchmark={n:4d} yours={mine:4d}")

    
    # print(item)
    # print(any([i for i in rows if i == 10] or [bool(j) for j in rows_v1]))

    