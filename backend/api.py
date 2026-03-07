from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.vectorstore.build_index import build_index
from backend.rag.retriever import Retriever
from backend.rag.generator import Generator

load_dotenv()

app = FastAPI(title="Repo Impact RAG API")

# ---------- CORS (important for frontend) ----------

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


# ---------- Build Index Endpoint ----------

@app.post("/build-index")
def build_repo_index(data: RepoRequest):

    try:
        build_index(data.repo_url)

        return {
            "status": "success",
            "message": "Index built successfully"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ---------- Analyze Impact Endpoint ----------

@app.post("/analyze")
def analyze_impact(data: QuestionRequest):

    try:
        retriever = Retriever()
        generator = Generator()

        contexts = retriever.retrieve(data.question)

        if not contexts:
            return {
                "status": "error",
                "message": "No relevant context found in the index"
            }

        answer = generator.generate(data.question, contexts)

        return {
            "status": "success",
            "answer": answer,
            "contexts": contexts
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }