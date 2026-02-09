from langchain.embeddings import HuggingFaceEmbeddings

def get_embedder():
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        encode_kwargs={"normalize_embeddings": True}
    )

