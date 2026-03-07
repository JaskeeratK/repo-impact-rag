from backend.embeddings.embedder import Embedder
from backend.vectorstore.store import VectorStore


class Retriever:

    def __init__(self):

        self.embedder = Embedder()
        self.store = VectorStore()

    def retrieve(self, question):

        query_embedding = self.embedder.embed(question)[0]

        results = self.store.query(query_embedding)

        documents = results.get("documents", [[]])[0]

        return documents