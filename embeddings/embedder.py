from langchain.embeddings import HuggingFaceEmbeddings
class Embedder:
    def __init__(self):
        self.model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    def embed(self, texts):
        return self.model.embed_documents(texts)

