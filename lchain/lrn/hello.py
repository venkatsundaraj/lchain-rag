
from dataclasses import dataclass
from app.config import settings
from collections import defaultdict

@dataclass(frozen=True, slots=True)
class Doc:
    no:str
    name:str

if __name__ == "__main__":
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

    print(hit_at_k)

    item = next((i+1 for i, p in enumerate(x) if p in y), None)

    
    # print(item)
    # print(any([i for i in rows if i == 10] or [bool(j) for j in rows_v1]))

    