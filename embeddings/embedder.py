from langchain.embeddings import OpenAIEmbeddings

def get_embedder():
    return OpenAIEmbeddings(model="text-embedding-3-small")
