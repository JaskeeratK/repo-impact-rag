# from sentence_transformers import SentenceTransformer


# # class Embedder:
# #     def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
# #         self.model = SentenceTransformer(model_name)
# from fastapi import Request

# class Embedder:
#     def __init__(self):
#         self.model = SentenceTransformer("paraphrase-MiniLM-L3-v2")

#     def embed(self, texts):
#         if isinstance(texts, str):
#             texts = [texts]
#         return self.model.encode(texts).tolist()
from fastembed import TextEmbedding


class Embedder:
    _model = None  # shared across every Embedder() instance in this process

    def __init__(self):
        if Embedder._model is None:
            Embedder._model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self.model = Embedder._model

    def embed(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        embeddings = list(self.model.embed(texts))
        return [e.tolist() for e in embeddings]
            texts = [texts]
        embeddings = list(self.model.embed(texts))
        return [e.tolist() for e in embeddings]
