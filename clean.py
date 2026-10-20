import json
from collections import Counter

with open("triples_all.json", "r", encoding="utf-8") as f:
    triples = json.load(f)

alias = {
    "Alphabet Inc.": "Alphabet",
    "Google DeepMind": "DeepMind",
    "Google LLC": "Google",
    "Meta": "Meta Platforms",
    "Meta Platforms, Inc.": "Meta Platforms",
    "Microsoft Corporation": "Microsoft",
}
drop_rel = {"is_a", "nationality"}
junk = {"American", "British", "Canadian"}
flip = {"founded", "co_founded"}

clean = []
seen = set()

for s, r, o in triples:
    s = alias.get(s, s)
    o = alias.get(o, o)

    if r in drop_rel or s in junk or o in junk or s == o:
        continue

    if r in flip:
        s, o = o, s
        r = "founded_by"

    key = (s, r, o)
    if key not in seen:
        seen.add(key)
        clean.append([s, r, o])

with open("triples_clean.json", "w", encoding="utf-8") as f:
    json.dump(clean, f, indent=2)

print("Before:", len(triples), "After:", len(clean))

rel = Counter(t[1] for t in clean)
print("Unique relations:", len(rel))
for name, count in rel.most_common(15):
    print(" ", name, count)