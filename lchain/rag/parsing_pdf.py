import re
import pathlib
import requests
from datasets import load_dataset

REPO = "vidore/vidore_v3_hr"
docs = load_dataset(REPO, "documents_metadata", split="test")

out = pathlib.Path("data/pdfs")
out.mkdir(parents=True, exist_ok=True)

def candidate_urls(cellar_id):
    base = f"http://publications.europa.eu/resource/cellar/{cellar_id}"
    yield base                                  # content negotiation (headers below)
    for manif in ("01", "02", "03"):            # direct file paths: <id>.0001.<NN>/DOC_1
        yield f"{base}.0001.{manif}/DOC_1"

def fetch_pdf(cellar_id):
    for url in candidate_urls(cellar_id):
        try:
            r = requests.get(
                url,
                headers={"Accept": "application/pdf", "Accept-Language": "eng"},
                timeout=120,
                allow_redirects=True,
            )
        except requests.RequestException:
            continue
        if r.ok and r.content.startswith(b"%PDF"):
            return r.content, url
    return None, None

manual = []
for d in docs:
    path = out / d["file_name"]
    if path.exists():
        print("skip  ", path.name)
        continue
    cellar_id = re.search(r"publication/([0-9a-f-]{36})", d["url"]).group(1)
    content, src = fetch_pdf(cellar_id)
    if content:
        path.write_bytes(content)
        print("saved ", path.name, "<-", src)
    else:
        manual.append(d)
        print("MANUAL", path.name)

print(f"\n{len(manual)} need manual download:")
for d in manual:
    print(f"  {d['file_name']}\n    {d['url']}")