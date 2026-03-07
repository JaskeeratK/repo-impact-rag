import streamlit as st
from vectorstore.build_index import build_index
from rag.retriever import Retriever
from rag.generator import Generator
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Code Impact Analyzer", layout="wide")

st.title("🔎 Code Change Impact Analyzer")

repo_url = st.text_input("Enter GitHub Repo URL")

# ---------- BUILD INDEX ----------

if st.button("Build Index"):

    if not repo_url:
        st.warning("Please enter a repository URL.")
    else:
        with st.spinner("Cloning repo and building embeddings..."):
            build_index(repo_url)

        st.success("✅ Index built successfully!")


# ---------- QUESTION ----------

question = st.text_input("Ask a question about code impact")


if st.button("Analyze Impact"):

    if not question:
        st.warning("Please enter a question.")
        st.stop()

    retriever = Retriever()
    generator = Generator()

    with st.spinner("Retrieving relevant code context..."):
        contexts = retriever.retrieve(question)

    if not contexts:
        st.error("❌ No relevant context found in the index.")
        st.info("Try rebuilding the index.")
        st.stop()

    with st.spinner("Analyzing potential impact..."):
        answer = generator.generate(question, contexts)

    st.subheader("📊 Impact Analysis")
    st.write(answer)


    # ---------- DEBUG VIEW ----------

    with st.expander("🔍 Retrieved Context (Debug)"):
        for i, doc in enumerate(contexts):
            st.markdown(f"**Context {i+1}**")
            st.code(doc)