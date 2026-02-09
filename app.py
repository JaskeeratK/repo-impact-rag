import streamlit as st
from ingest.commit_loader import load_commits
from process.diff_parser import get_diff_summary
from vectorstore.store import build_store
from embeddings.embedder import get_embedder
from rag.retriever import retrieve
from rag.generator import generate_answer

st.title("🔍 Code Change Impact Analyzer (RAG)")

repo_url = st.text_input("GitHub Repository URL")
since = st.date_input("Analyze commits since")

if st.button("Index Repository"):
    commits = load_commits(since=str(since))
    docs = []

    for c in commits:
        diff = get_diff_summary(c["hash"])
        docs.append(
            f"{c['message']}\n{diff}"
        )

    store = build_store(docs, get_embedder())
    st.success("Repository indexed successfully!")

query = st.text_input("Ask about a code change")

if st.button("Analyze Impact"):
    contexts = retrieve(query, store)
    answer = generate_answer(query, contexts)
    st.write(answer)

