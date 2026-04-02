import chromadb


class VectorStore:

    def __init__(self, collection_name="repo_index"):

        self.client = chromadb.Client(
            chromadb.config.Settings(
                persist_directory="./chroma_db",
                is_persistent=True   # ✅ this is enough
            )
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

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