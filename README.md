# RIA

<img width="1327" height="650" alt="ria5" src="https://github.com/user-attachments/assets/068cadea-256e-486b-a921-ccead3e6990f" />
<img width="1336" height="640" alt="ria6" src="https://github.com/user-attachments/assets/c01ae45a-6707-456f-9f6a-a03ac431b717" />
# Repo Impact RAG 🔍🚀

An advanced Retrieval-Augmented Generation (RAG) system engineered to map, trace, and evaluate the blast radius of code changes within a repository. By combining AST-aware code chunking, hybrid dense/sparse search, and static dependency graphs, this system answers natural-language questions about how changes to a function, module, or database schema ripple through an ecosystem.

---

## 🏗️ Architecture & Pipeline Flow

frontend/ (Static HTML/JS/CSS) ──HTTP──> backend/api.py (FastAPI)
│
┌─────────────────────────┴─────────────────────────┐
│                                                   │
POST /build-index                                    POST /analyze
│                                                   │
RepoLoader.clone()                                   Retriever.retrieve()
(git clone to disk)                                  ├── Dense Vector (Chroma)
│                                          └── Sparse BM25 (rank_bm25)
read_files() + chunk_file()                                   │
(Tree-Sitter AST / fallback)                         Reciprocal Rank Fusion (RRF)
│                                                   │
Embedder.embed()                                     DependencyGraph.get_dependents()
(sentence-transformers)                                       │
│                                          Generator.generate()
VectorStore.add()                                    (2 Groq calls: prose + JSON graph)
(Chroma, in-memory)


---

## 🛠️ Core Backend Mechanics

### 1. AST-Aware Semantic Chunking
Instead of slicing source code blindly by character limits, `vectorstore/build_index.py` utilizes **Tree-Sitter AST parsers** (`tree-sitter-languages`) for semantic boundaries.
* **Languages Supported:** Python, JS/TS, Go, Rust, Java, Ruby, C/C++.
* **Structural Isolation:** Code is isolated by structural blocks such as `function_definition` and `class_definition`. This retains full local code context (decorators, signatures, and docstrings).
* **Fallback Mode:** Files without syntax tree mappings default to a strict **800-character sliding window** chunker.

### 2. Dual-Engine Retrieval & Fusion
Queries pass through a hybrid retrieval pipeline designed to trap both high-level semantic intent and precise syntax tokens.

* **Dense Retrieval:** Handled via `sentence-transformers` matching against an in-memory Chroma instance. Captures conceptual matches (e.g., matching "token refresh" to `validate_session_timestamp`).
* **Sparse Retrieval:** Powered by `rank_bm25` (BM25Okapi), capturing exact variable names, function identifiers, or database parameters.
* **Reciprocal Rank Fusion (RRF):** Merges dense and sparse lists score-agnostically based on ranking order, eliminating manual alpha tuning.

The RRF score for a document $d \in D$ is evaluated as:

$$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$

> *Where $M$ represents the retrieval engines, $r_m(d)$ is the document rank inside engine $m$, and $k$ is a constant smoothing value set to **60**.*

### 3. Static Dependency Cross-Referencing
Before payload delivery to the LLM, source files extracted via RRF are looked up inside a pre-compiled `DependencyGraph`. The system resolves immediate downstream dependents—mapping files that actively import or depend on the flagged changes—and embeds them into the context as structural "high-risk zones."

---

## 🗂️ Project Layout

```text
backend/
  api.py                    FastAPI production entrypoint
  ingest/
    repo_loader.py          Target git clone utility using GitPython
  vectorstore/
    build_index.py          File tree walking, language validation, and AST chunking
    store.py                Chroma EphemeralClient instance wrapper
  embeddings/
    embedder.py              SentenceTransformer engine wrapper (fixed imports)
  rag/
    retriever.py             Dense + BM25 search engines and RRF rank merger
    generator.py              Groq LLM manager (Markdown analysis + structured JSON graph)
  analysis/
    dependency_graph.py      Regex and AST-based static import scanners per language
frontend/
  index.html / scripts.js    Single-page dashboard (Mermaid rendering + RRF telemetry panels)
requirements.txt
```
## 🔌 API Specification
All endpoints are hosted on backend/api.py and are CORS-open.

POST /build-index
Clones a target repository, fragments files via tree-sitter, maps imports, and primes the vector store.

Payload:

JSON


{ "repo_url": "[https://github.com/user/repo](https://github.com/user/repo)" }
Returns: Total count of indexed chunks.

POST /analyze
Generates a structured impact profile and dependency graph.

Payload:

JSON


{ "question": "What breaks if we change the user authentication payload schema?" }
Returns:

answer: Comprehensive impact, risk profile, and mitigation roadmap in Markdown.

graph: Structured JSON mapping used to render the live Mermaid canvas.

chunks: Exploded retrieval-quality panel displaying raw dense/BM25/RRF metrics.

⚡ Quickstart
1. Installation
Clone the repository and install system requirements:

Bash


pip install -r requirements.txt
2. Environment Variables
Create a .env configuration file in the project root:

Code snippet


GROQ_API_KEY=your_groq_api_key_here
3. Start the Backend Engine
Bash


python -m uvicorn backend.api:app --reload --port 8000
Open frontend/index.html inside a web browser or serve it via your static file host of choice to explore the interface.

⚙️ Core Technical Stack
API Framework: FastAPI + Uvicorn

Embeddings Model: sentence-transformers

Vector Vector Store: ChromaDB (EphemeralClient in-memory engine)

Keyword Matching: rank_bm25 (BM25Okapi implementation)

Inference Engine: Groq (llama-3.3-70b-versatile for deep structural context parsing)

Parser Engine: tree-sitter-languages for AST isolation
