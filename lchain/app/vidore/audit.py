"""Day 2 — parse-quality audit. Dump pypdf text for 15 gold pages (5 table / 5 chart / 5 text)
next to their page images so you can grade each: readable / garbled / empty.

    python -m vidore.day2_audit            # writes data/vidore_hr/audit/
"""
import json, random
from pathlib import Path
from app.vidore.loader import Catalog, DATA

PDF_DIR = Path("data/pdfs")
OUT = DATA / "audit"
PER_TYPE = 5
SEED = 7

def gold_pages_by_type(cat: Catalog) -> dict[str, list[str]]:
    by = {"Table": set(), "Chart": set(), "Text": set()}
    for qid, q in cat.queries.items():
        types = set(q.get("content_type") or [])
        for t in by:
            if t in types:
                by[t] |= set(cat.qrels.get(qid, {}))
    pools = {t: sorted(s) for t, s in by.items()}
    print({t: len(v) for t, v in pools.items()})      # pool sizes
    return pools

def page_text(file_name: str, page: int) -> str:
    from pypdf import PdfReader
    return PdfReader(str(PDF_DIR / file_name)).pages[page].extract_text() or ""

if __name__ == "__main__":
    cat = Catalog.load()
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    sheet = []
    for t, cids in gold_pages_by_type(cat).items():
        for cid in rng.sample(cids, min(PER_TYPE, len(cids))):
            file, page = cat.page_of[cid]
            txt = page_text(file, page)
            (OUT / f"{t.lower()}_{cid}.txt").write_text(txt)
            sheet.append({"type": t, "corpus_id": cid, "file": file, "page": page,
                          "chars": len(txt), "image": str(DATA / "pages" / f"{cid}.png"),
                          "grade": ""})          # <- you fill: readable | garbled | empty
    (OUT / "audit_sheet.json").write_text(json.dumps(sheet, indent=2))
    for r in sheet:
        print(f"{r['type']:5s} {r['corpus_id']:>6} {r['file'][:40]:40s} p{r['page']:<4} {r['chars']:5d} chars")
    print(f"\n{len(sheet)} pages -> {OUT}/  open each .txt beside its .png and fill 'grade' in audit_sheet.json")