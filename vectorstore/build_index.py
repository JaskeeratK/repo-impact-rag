import uuid
from ingest.repo_loader import RepoLoader
from ingest.commit_loader import CommitLoader
from process.diff_parser import DiffParser
from process.summarizer import Summarizer
from embeddings.embedder import Embedder
from vectorstore.store import VectorStore


def build_index(repo_url):
    repo_loader = RepoLoader(repo_url)
    repo_path = repo_loader.clone()

    commit_loader = CommitLoader(repo_path)
    commits = commit_loader.get_commits()

    parser = DiffParser()
    summarizer = Summarizer()
    embedder = Embedder()
    store = VectorStore()

    for commit in commits:
        parsed = parser.parse(commit["diff"])

        summary = summarizer.summarize_diff(commit["diff"])

        # Skip empty summaries
        if not summary or not summary.strip():
            continue

        embedding = embedder.embed(summary)[0]

        # Fix functions metadata
        functions = parsed.get("functions_modified", [])

        if isinstance(functions, list):
            functions = ", ".join(functions) if functions else "None"

        metadata = {
            "commit_id": commit.get("commit_id"),
            "functions": functions,
            "lines_added": parsed.get("lines_added", 0),
            "lines_removed": parsed.get("lines_removed", 0)
        }

        store.add(
            ids=[str(uuid.uuid4())],
            documents=[summary],
            embeddings=[embedding],
            metadatas=[metadata]
        )