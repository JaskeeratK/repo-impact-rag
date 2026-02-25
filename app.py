import streamlit as st
from vectorstore.build_index import build_index
from rag.retriever import Retriever
from rag.generator import Generator
from dotenv import load_dotenv

load_dotenv()

st.title("🔎 Code Change Impact Analyzer")

repo_url = st.text_input("Enter GitHub Repo URL")

if st.button("Build Index"):
    if repo_url:
        with st.spinner("Building index..."):
            build_index(repo_url)
        st.success("Index built successfully!")

question = st.text_input("Ask a question about code impact")

if st.button("Analyze Impact"):
    retriever = Retriever()
    generator = Generator()

    results = retriever.retrieve(question)
    documents = results["documents"][0]

    answer = generator.generate(documents, question)

    st.subheader("Impact Analysis")
    st.write(answer)
