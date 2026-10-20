import streamlit as st
from ask import plain_rag, graph_rag

st.set_page_config(page_title="Plain RAG vs GraphRAG", layout="wide")
st.title("Plain RAG vs GraphRAG")
st.caption(
    "Both answer from the same Wikipedia docs. Plain RAG uses the top 5 chunks. "
    "GraphRAG uses the top 2 chunks plus 2-hop facts from a knowledge graph."
)

question = st.text_input(
    "Ask a question",
    placeholder="Who is the CEO of the company that owns WhatsApp?",
)

if question:
    with st.spinner("Asking both systems..."):
        plain = plain_rag(question, k=5)
        graph, n_facts = graph_rag(question)

    left, right = st.columns(2)
    with left:
        st.subheader("Plain RAG (k=5)")
        st.write(plain)
    with right:
        st.subheader("GraphRAG")
        st.write(graph)
        st.caption(str(n_facts) + " graph facts used")
