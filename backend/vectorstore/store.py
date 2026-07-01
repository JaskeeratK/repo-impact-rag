import chromadb

class VectorStore:
    COLLECTION_NAME = "repo_chunks"

    def __init__(self):
        self.client = chromadb.EphemeralClient()
        self.collection = self.client.get_or_create_collection(self.COLLECTION_NAME)

    def reset(self):
        try:
            self.client.delete_collection(self.COLLECTION_NAME)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(self.COLLECTION_NAME)

    def add(self, ids, documents, embeddings, metadatas):
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def query(self, query_embedding, n_results=5):
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )