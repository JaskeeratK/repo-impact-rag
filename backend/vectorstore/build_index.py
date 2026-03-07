import os
import uuid

from ingest.repo_loader import RepoLoader
from embeddings.embedder import Embedder
from vectorstore.store import VectorStore


ALLOWED_EXTENSIONS = [
    ".py",
    ".js",
    ".ts",
    ".html",
    ".css"
]


def read_files(repo_path):
    files = []

    for root, _, filenames in os.walk(repo_path):

        for file in filenames:

            if any(file.endswith(ext) for ext in ALLOWED_EXTENSIONS):

                path = os.path.join(root, file)

                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()

                        files.append({
                            "path": path,
                            "content": content
                        })

                except:
                    continue

    return files


def chunk_text(text, chunk_size=800):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


def build_index(repo_url):

    repo_loader = RepoLoader(repo_url)
    repo_path = repo_loader.clone()

    embedder = Embedder()
    store = VectorStore()

    files = read_files(repo_path)

    print("Files found:", len(files))

    total_chunks = 0

    for file in files:

        chunks = chunk_text(file["content"])

        for chunk in chunks:

            embedding = embedder.embed(chunk)[0]

            store.add(
                ids=[str(uuid.uuid4())],
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[{
                    "file": file["path"]
                }]
            )

            total_chunks += 1

    print("Chunks indexed:", total_chunks)