import json
import chromadb
import networkx as nx
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
llm = Anthropic()

col = chromadb.PersistentClient(path="chroma_db").get_collection("docs")

with open("triples_clean.json", "r", encoding="utf-8") as f:
    triples = json.load(f)

G = nx.MultiDiGraph()
for s, r, o in triples:
    G.add_edge(s, o, relation=r)


def ask_llm(context, question):
    prompt = f"""Answer using only the context below.
If the context is not enough, reply exactly: NOT_ENOUGH_INFO
Answer directly. Do not mention the context or the documents in your answer.

Context:
{context}

Question: {question}"""

    reply = llm.messages.create(
        model="claude-haiku-5-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = ""
    for block in reply.content:
        if block.type == "text":
            answer += block.text
    return answer.strip()


def get_chunks(question, k):
    res = col.query(query_texts=[question], n_results=k)
    return res["documents"][0]


def get_graph_facts(question, chunks, hops=2):
    text = question + " " + " ".join(chunks)
    frontier = set(n for n in G.nodes if len(n) > 3 and n in text)

    facts = set()
    for hop in range(hops):
        next_frontier = set()
        for node in frontier:
            for u, v, data in G.out_edges(node, data=True):
                facts.add(u + " " + data["relation"] + " " + v)
                next_frontier.add(v)
            for u, v, data in G.in_edges(node, data=True):
                facts.add(u + " " + data["relation"] + " " + v)
                next_frontier.add(u)
        frontier = next_frontier
    return list(facts)


def plain_rag(question, k=2):
    chunks = get_chunks(question, k)
    return ask_llm("\n".join(chunks), question)


def graph_rag(question, k=2):
    chunks = get_chunks(question, k)
    facts = get_graph_facts(question, chunks)
    context = "\n".join(chunks) + "\n" + "\n".join(facts)
    return ask_llm(context, question), len(facts)


questions = [
    "Who is the CEO of the company that acquired Instagram?",
    "Where is the company founded by Dario Amodei headquartered?",
    "Who founded the company that owns YouTube?",
]

if __name__ == "__main__":
    for q in questions:
        print("Q:", q)
        print("Plain RAG:", plain_rag(q))
        answer, n = graph_rag(q)
        print("GraphRAG :", answer, "(" + str(n) + " graph facts used)")
        print()