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
        embedding = embedder.embed(summary)[0]

        store.add(
            ids=[str(uuid.uuid4())],
            documents=[summary],
            embeddings=[embedding],
            metadatas=[{
                "commit_id": commit["commit_id"],
                "functions": parsed["functions_modified"],
                "lines_added": parsed["lines_added"],
                "lines_removed": parsed["lines_removed"]
            }]
        )
