from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.vectorstore.build_index import build_index
from backend.rag.retriever import Retriever
from backend.rag.generator import Generator
from backend.analysis.dependency_graph import DependencyGraph
from backend.ingest.commit_loader import CommitLoader

load_dotenv()

app = FastAPI(title="Repo Impact RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Request Models ----------
class RepoRequest(BaseModel):
    repo_url: str

class QuestionRequest(BaseModel):
    question: str

class CommitRequest(BaseModel):
    repo_path: str
    question: str


# ---------- Build Index ----------
@app.post("/build-index")
def build_repo_index(data: RepoRequest):
    try:
        build_index(data.repo_url)

        graph = DependencyGraph()
        graph.build("temp_repo")
        app.state.dependency_graph = graph

        return {
            "status": "success",
            "message": "Index built successfully",
            "files_indexed": len(graph.graph)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ---------- Analyze Impact ----------
@app.post("/analyze")
def analyze_impact(data: QuestionRequest):
    try:
        retriever = Retriever()
        generator = Generator()
        contexts = retriever.retrieve(data.question)

        if not contexts:
            return {"status": "error", "message": "No relevant context found"}

        dependents = []
        if hasattr(app.state, "dependency_graph"):
            graph = app.state.dependency_graph
            for file in graph.graph.keys():
                if any(keyword.lower() in file.lower()
                       for keyword in data.question.split() if len(keyword) > 4):
                    dependents.extend(graph.get_dependents(file))
        dependents = list(set(dependents))

        answer = generator.generate(data.question, contexts, dependents=dependents)
        return {
            "status": "success",
            "answer": answer,
            "contexts": contexts,
            "affected_files": dependents
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ---------- Analyze with Commit History ----------
@app.post("/analyze-with-history")
def analyze_with_history(data: CommitRequest):
    try:
        loader = CommitLoader(data.repo_path)
        commits = loader.get_commits(max_count=20)
        commit_context = "\n\n".join([
            f"Commit: {c['message'].strip()}\nDiff: {c['diff'][:500]}"
            for c in commits[:5]
        ])
        retriever = Retriever()
        generator = Generator()
        contexts = retriever.retrieve(data.question)
        contexts.append(commit_context)
        answer = generator.generate(data.question, contexts)
        return {"status": "success", "answer": answer}
    except Exception as e:
        return {"status": "error", "message": str(e)}