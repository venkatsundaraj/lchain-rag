"""Align a PDF whose page count differs from the benchmark's by matching page images.
Writes data/vidore_hr/page_remap.json: {file_name: {pypdf_index: benchmark_page}}.

    pip install pymupdf imagehash
    python -m app.vidore.align
"""
import json
import fitz, imagehash
from PIL import Image
from app.vidore.loader import Catalog, DATA, PDF_DIR   # PDF_DIR = Path("data/pdfs")

FILES = ["employment_and_social_developments_in_europe_2024-KEBD24002ENN.pdf"]
WEAK = 12          # hamming distance above this = suspicious match, printed for eyeballing

def phash_pdf(path):
    out = []
    for page in fitz.open(path):
        pix = page.get_pixmap(dpi=40)
        out.append(imagehash.phash(Image.frombytes("RGB", (pix.width, pix.height), pix.samples)))
    return out

if __name__ == "__main__":
    cat = Catalog.load()
    remap_all = {}
    for f in FILES:
        mine = phash_pdf(PDF_DIR / f)
        bench = {bp: cid for cid, (ff, bp) in cat.page_of.items() if ff == f}
        remap, used = {}, set()
        for bp in sorted(bench):
            h = imagehash.phash(Image.open(DATA / "pages" / f"{bench[bp]}.png"))
            best = min((i for i in range(len(mine)) if i not in used), key=lambda i: h - mine[i])
            d = h - mine[best]
            if d > WEAK:
                print(f"  weak: bench p{bp} -> pypdf {best} (dist {d})")
            remap[best] = bp; used.add(best)
        shifts = sorted({i - bp for i, bp in remap.items()})
        print(f"{f}: {len(remap)} benchmark pages matched; offsets seen: {shifts}; "
              f"unmatched pypdf pages: {sorted(set(range(len(mine))) - used)}")
        remap_all[f] = {str(i): bp for i, bp in remap.items()}
    (DATA / "page_remap.json").write_text(json.dumps(remap_all, indent=1))
    print("saved", DATA / "page_remap.json")