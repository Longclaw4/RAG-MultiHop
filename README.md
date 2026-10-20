# Plain RAG vs GraphRAG on multi-hop questions

Plain retrieval-augmented generation (RAG) answers a question from the chunks most similar to it. That works when the answer sits in one chunk. It fails when the question needs two facts that live in different documents, such as "Who is the CEO of the company that owns WhatsApp?" The WhatsApp page says Meta owns it, and the Mark Zuckerberg page says he runs Meta. Plain RAG can retrieve one of those pages but not both.

This project compares plain RAG against a GraphRAG variant on the same Wikipedia corpus. GraphRAG adds facts from a knowledge graph, so the model can follow a chain across documents.

## Why plain RAG misses

Retrieval ranks chunks by similarity to the question. The bridge fact in a two-hop question is often not similar to the question text. In the failure cases below, the chunk holding the bridge fact was in the index but ranked 8th or 9th of 52, just outside the top 5 that plain RAG passes to the model.

## Pipeline

1. **Fetch** (`fetch.py`): download the Wikipedia intro for 16 entities (companies, people, and products).
2. **Chunk and extract** (`build.py`): split each page into 4-sentence chunks. Claude Haiku extracts `[subject, relation, object]` triples from each chunk. The chunks go into a Chroma vector index.
3. **Clean** (`clean.py`): merge aliases (e.g. "Meta" and "Meta Platforms, Inc." become one entity), drop noisy relations, and normalise `founded` / `co_founded` to `founded_by`. This leaves 530 triples from 555 raw.
4. **Retrieve**:
   - *Plain RAG* (`plain_rag` in `ask.py`): the top-k chunks go to the model.
   - *GraphRAG* (`graph_rag` in `ask.py`): the top-2 chunks, plus every graph fact within 2 hops of any entity named in the question or those chunks.
5. **Answer**: Claude Haiku answers using only the context. It replies `NOT_ENOUGH_INFO` when the context does not contain the answer.

## Results

Correct answers out of each group, given as the min-max across 3 full runs (`eval.py`). Scoring is keyword-based with a refusal check; see Limitations.

| System | All (34) | Multi-hop (14) | Two-file docs (8) | Single fact (4) | Unanswerable (4) | Hard unanswerable (4) |
|---|---|---|---|---|---|---|
| Plain RAG, k=2 | 18-19 | 5-6 | 1 | 4 | 4 | 4 |
| Plain RAG, k=5 | 26 | 9 | 5 | 4 | 4 | 4 |
| Plain RAG, k=10 | 29-30 | 12-13 | 5 | 4 | 4 | 4 |
| GraphRAG (top-2 chunks + 2-hop facts) | 34 | 14 | 8 | 4 | 4 | 4 |

- On this corpus, GraphRAG beats plain RAG at k=10 by 4-5 questions. Most of the gap at k=5 closes at k=10.
- Both systems correctly abstained on all four hard unanswerable questions, in all three runs. GraphRAG received 279-384 graph facts for those questions and did not guess.

## Failure analysis

**Why plain k=5 misses two-hop questions.** Plain RAG at k=5 failed 5 of the 14 multi-hop questions and 3 of the 8 two-file questions, in every run. Every miss was `NOT_ENOUGH_INFO`, not a wrong answer. For four of the multi-hop misses (Dario Amodei's company HQ, WhatsApp's owner's CEO, the founders of DeepMind's acquirer, and Mark Zuckerberg's company HQ) I checked the index directly with `diagnose_retrieval.py`. In each case the chunk holding the second fact was in the collection but ranked 8th or 9th of 52, just outside the top 5. Example: the Anthropic chunk that says "headquartered in San Francisco" ranked 9th for "Where is the company founded by Dario Amodei headquartered?" I haven't run the same check on the other misses, including the Daniela Amodei question.

**What k=10 still misses.** Plain k=10 failed 1-2 multi-hop questions and 3 two-file questions per run, again all `NOT_ENOUGH_INFO`. The two-file misses are the net-worth, previous-employer HQ, and "president of the company Dario co-founded" questions. I haven't checked where their bridge chunks rank, so I can't say whether they sit just outside the top 10 or further down.

**Unanswerable questions do not separate the systems.** Neither system made up an answer on any of the eight unanswerable questions, including the four hard ones about related entities. That's one result, on eight questions; it does not show GraphRAG is safe from hallucination in general.

## Limitations

- **Small corpus.** 16 pages and 52 chunks. Plain RAG with a larger k can compete with the graph here. The graph is expected to matter more as the corpus grows, but this project does not test that.
- **Questions favour the graph.** The multi-hop questions were written around the same entities the graph was built from. The docs-only questions were written from the source text but may still be answerable from graph triples. A fairer test needs questions written before the graph is built.
- **Keyword scoring.** Answers are marked correct when they contain an expected keyword and no refusal phrase. This catches the Q7 false positive from an earlier run, but it can still reject a correct answer that happens to contain a phrase such as "doesn't mention." Answers were spot-checked by hand, not by a second judge.
- **Noisy extraction.** The triples come from an LLM reading each chunk. Some are wrong or duplicated, and cleaning removes only the obvious cases.
- **High token cost per GraphRAG query.** GraphRAG sends the graph facts with the chunks, so the context is larger on every query. Building the graph also makes one LLM call per chunk. Token counts were not measured in this project.
- **Unanswerable questions do not separate the systems.** On the first unanswerable set, every system abstained correctly. The harder set is meant to test this; see the results.

## How to run

`chroma_db/` and the `.env` file are not in the repo, so build the index first.

```bash
pip install -r requirements.txt

# put your key in .env:  ANTHROPIC_API_KEY=...

python fetch.py   # downloads docs/*.txt
python build.py   # chunks, extracts triples, builds chroma_db/
python clean.py   # writes triples_clean.json

python eval.py    # 3 runs, writes eval_results.json
streamlit run app.py
```

`build.py` makes one LLM call per chunk, so it costs some tokens to run.
