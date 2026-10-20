import json
from collections import Counter

with open("triples_all.json", "r", encoding="utf-8") as f:
    triples = json.load(f)

rel = Counter(t[1] for t in triples)
print("Unique relations:", len(rel))
for name, count in rel.most_common(25):
    print(" ", name, count)

ents = Counter()
for t in triples:
    ents[t[0]] += 1
    ents[t[2]] += 1
print("\nUnique entities:", len(ents))
for name, count in ents.most_common(25):
    print(" ", name, count)

print("\nSample triples:")
for t in triples[:20]:
    print(" ", t)