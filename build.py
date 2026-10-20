import os
import json
import glob
import chromadb
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
llm = Anthropic()


def make_chunks(text, size=4):
    sentences = text.replace("\n", " ").split(". ")
    chunks = []
    for i in range(0, len(sentences), size):
        chunk = ". ".join(sentences[i:i + size]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def extract_triples(chunk, title):
    prompt = f"""Extract facts from the text as triples.
Return ONLY a JSON list, no other words.
Format: [["subject", "relation", "object"]]

Rules:
- relation must be lowercase snake_case, 1-3 words (examples: ceo_of, founded_by, based_in, acquired)
- use full entity names (Sam Altman, not "he"; OpenAI, not "the company")
- the text is from the Wikipedia page "{title}", so use that name when the text says "he", "she", or "it"
- only include clear facts, skip opinions

Text: {chunk}"""

    for attempt in range(2):
        reply = llm.messages.create(
            model="claude-haiku-5-5",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )

        answer = ""
        for block in reply.content:
            if block.type == "text":
                answer += block.text

        start = answer.find("[")
        end = answer.rfind("]")
        if start != -1 and end != -1:
            try:
                return json.loads(answer[start:end + 1])
            except json.JSONDecodeError:
                pass

        print("  attempt", attempt + 1, "failed. Raw reply starts with:", answer[:150])

    return []


all_chunks = []
all_ids = []
all_meta = []
all_triples = []

for path in sorted(glob.glob("docs/*.txt")):
    title = os.path.basename(path).replace(".txt", "")

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = make_chunks(text)
    print(title, "->", len(chunks), "chunks")

    for i, chunk in enumerate(chunks):
        all_chunks.append(chunk)
        all_ids.append(title + "_" + str(i))
        all_meta.append({"source": title})

        for t in extract_triples(chunk, title):
            if len(t) == 3:
                all_triples.append([str(x).strip() for x in t])

# remove duplicate triples
seen = set()
unique = []
for t in all_triples:
    key = tuple(t)
    if key not in seen:
        seen.add(key)
        unique.append(t)

with open("triples_all.json", "w", encoding="utf-8") as f:
    json.dump(unique, f, indent=2)
print("Saved", len(unique), "triples")

# build the vector index
client = chromadb.PersistentClient(path="chroma_db")
try:
    client.delete_collection("docs")
except Exception:
    pass

col = client.create_collection("docs")
col.add(documents=all_chunks, ids=all_ids, metadatas=all_meta)
print("Saved", len(all_chunks), "chunks to Chroma")