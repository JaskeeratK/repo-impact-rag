from embeddings.embedder import Embedder
from vectorstore.store import VectorStore


class Retriever:
    def __init__(self):
        self.embedder = Embedder()
        self.store = VectorStore()

    def retrieve(self, query):
        query_embedding = self.embedder.embed(query)[0]
        results = self.store.query(query_embedding)

        return results
