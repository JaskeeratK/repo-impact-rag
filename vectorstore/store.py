from langchain.vectorstores import FAISS

def build_store(docs, embedder):
    return FAISS.from_documents(docs, embedder)
