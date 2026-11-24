from app.vidore.loader import Catalog, DATA
import json, random
from pathlib import Path


PDF_DIR = Path("data/pdfs")
OUT = DATA / "audit"
PER_TYPE = 5

SEED = 7

def gold_pages_by_type(cat:Catalog) -> dict[str, list[str]]:
    by = {"Graph":set(), "Tables":set(), "Images":set()}
    for qid, q in cat.queries.items():
        types = set(q.get('content_type'),[])
        if len(types) == 1 and (t := next(iter(types))) in by:
            by[t] = set(cat.qrels.get(qid, {}))
        return {t:sorted(s) for t, s in by.items()}



if __name__ == "__main__":
    cat = Catalog.load()
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    sheet = []
    for t, cids in gold_pages_by_type(cat).items():
         True
