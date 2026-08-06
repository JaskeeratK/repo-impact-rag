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
    def __init__(self):
        self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    def embed(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        embeddings = list(self.model.embed(texts))
        return [e.tolist() for e in embeddings]
