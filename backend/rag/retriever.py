from backend.embeddings.embedder import Embedder
from backend.vectorstore.store import VectorStore


class Retriever:

    def __init__(self):
        self.embedder = Embedder()
        self.store = VectorStore()

    def retrieve(self, question):
        query_embedding = self.embedder.embed(question)[0]

        results = self.store.query(query_embedding)

        print("DEBUG RESULTS:", results)  

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        source_files = list(set(
            m["file"] for m in metadatas if "file" in m
        ))

        return documents, source_files