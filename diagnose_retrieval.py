import chromadb

col = chromadb.PersistentClient(path="chroma_db").get_collection("docs")
total = col.count()

# Each miss needs two hops. For each hop: which source doc, and a phrase that appears in the chunk holding that fact.
misses = [
    {
        "q": "Where is the company founded by Dario Amodei headquartered?",
        "hops": [
            ("Anthropic HQ", "Anthropic", "San Francisco"),
        ],
    },
    {
        "q": "Who is the CEO of the company that owns WhatsApp?",
        "hops": [
            ("WhatsApp owner", "WhatsApp", "Meta Platforms"),
            ("Meta CEO", "Mark Zuckerberg", "chief executive officer"),
        ],
    },
    {
        "q": "Who founded the company that acquired DeepMind?",
        "hops": [
            ("DeepMind acquired by Google", "DeepMind", "acquired by Google"),
            ("Google founders", "Google", "Larry Page and Sergey Brin"),
        ],
    },
    {
        "q": "Where is the headquarters of the company Mark Zuckerberg chairs?",
        "hops": [
            ("Zuckerberg chairs Meta", "Mark Zuckerberg", "chairman"),
            ("Meta HQ", "Meta Platforms", "Menlo Park"),
        ],
    },
]

# Pull the full ranking once so we can report each gold chunk's rank, not just whether it made the top 5.
everything = col.get(include=["documents", "metadatas"])
id_by_doc = {doc: cid for cid, doc in zip(everything["ids"], everything["documents"])}

for m in misses:
    print("=" * 100)
    print("Q:", m["q"])
    ranked = col.query(query_texts=[m["q"]], n_results=total, include=["documents", "metadatas"])
    docs = ranked["documents"][0]
    metas = ranked["metadatas"][0]

    print("Top 5 retrieved at k=5:")
    for i in range(5):
        print("  #%d [%s] %s..." % (i + 1, metas[i]["source"], docs[i][:90].replace("\n", " ")))

    for hop_name, source, phrase in m["hops"]:
        # Find the gold chunks for this hop by source + phrase
        gold = [
            (cid, doc)
            for cid, doc, meta in zip(everything["ids"], everything["documents"], everything["metadatas"])
            if meta["source"] == source and phrase in doc
        ]
        if not gold:
            print("  HOP [%s]: no chunk in '%s' contains '%s' -- check phrase" % (hop_name, source, phrase))
            continue
        for cid, doc in gold:
            rank = next((i + 1 for i, d in enumerate(docs) if d == doc), None)
            if rank is not None and rank <= 5:
                verdict = "IN top 5 (rank %d)" % rank
            else:
                verdict = "NOT in top 5 (rank %s of %d)" % (rank, total)
            print("  HOP [%s] chunk %s: %s" % (hop_name, cid, verdict))
