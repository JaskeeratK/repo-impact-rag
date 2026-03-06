import chromadb
from chromadb.config import Settings


class VectorStore:
    def __init__(self, collection_name="repo_index"):
        self.client = chromadb.Client(
            Settings(
                persist_directory="./chroma_db",
                anonymized_telemetry=False
            )
        )
        self.collection = self.client.get_or_create_collection(collection_name)

    def add(self, ids, documents, embeddings, metadatas):
        # Safety check to ensure all lists match length
        if not (len(ids) == len(documents) == len(embeddings) == len(metadatas)):
            raise ValueError("ids, documents, embeddings, and metadatas must have same length")

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