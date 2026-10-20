import json
import random

with open("triples_clean.json", "r", encoding="utf-8") as f:
    triples = json.load(f)

chains = []
for s1, r1, o1 in triples:
    for s2, r2, o2 in triples:
        if o1 == s2 and s1 != o2:
            chains.append((s1, r1, o1, r2, o2))

print("Total 2-hop chains:", len(chains))
random.seed(1)
for c in random.sample(chains, min(40, len(chains))):
    print(c[0], "--", c[1], "->", c[2], "--", c[3], "->", c[4])