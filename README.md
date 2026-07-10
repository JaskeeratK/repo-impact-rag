# RIA

<img width="1327" height="650" alt="ria5" src="https://github.com/user-attachments/assets/068cadea-256e-486b-a921-ccead3e6990f" />
<img width="1336" height="640" alt="ria6" src="https://github.com/user-attachments/assets/c01ae45a-6707-456f-9f6a-a03ac431b717" />
## Repo Impact RAG 🔍🚀

An advanced Retrieval-Augmented Generation (RAG) system engineered to map, trace, and evaluate the blast radius of code changes within a repository. By combining AST-aware code chunking, hybrid dense/sparse search, and static dependency graphs, this system answers natural-language questions about how changes to a function, module, or database schema ripple through an ecosystem.

---

## 🏗️ Architecture & Pipeline Flow


```text
                          frontend/ (Static HTML / JS / CSS)
                                      │
                                   HTTP API
                                      │
                                      ▼
                     backend/api.py (FastAPI Application)
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            │                                                   │
            ▼                                                   ▼
      POST /build-index                                  POST /analyze
            │                                                   │
            ▼                                                   ▼
     RepoLoader.clone()                               Retriever.retrieve()
      (Clone Git repository)                          │
            │                                         ├── Dense Retrieval (ChromaDB)
            ▼                                         └── Sparse Retrieval (BM25)
  read_files() + chunk_file()                                   │
(Tree-Sitter AST parsing / fallback)                            ▼
            │                                  Reciprocal Rank Fusion (RRF)
            ▼                                                   │
   Embedder.embed()                                             ▼
(sentence-transformers)                     DependencyGraph.get_dependents()
            │                                                   │
            ▼                                                   ▼
     VectorStore.add()                              Generator.generate()
 (ChromaDB in-memory store)           (Groq LLM: Markdown analysis + JSON graph)
```
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
# 🔌 API Specification

All endpoints are hosted on `backend/api.py` and are CORS-enabled.

---

## POST `/build-index`

Clones a target repository, fragments source files using **Tree-sitter**, maps imports, and initializes the vector store.

### Request Body

```json
{
  "repo_url": "https://github.com/user/repo"
}
```

### Response

Returns the total number of indexed code chunks.

---

## POST `/analyze`

Generates a structured impact analysis and dependency graph for a codebase query.

### Request Body

```json
{
  "question": "What breaks if we change the user authentication payload schema?"
}
```

### Response

| Field | Description |
|--------|-------------|
| `answer` | Comprehensive impact analysis, risk profile, and mitigation roadmap in Markdown format. |
| `graph` | Structured JSON used to render the live Mermaid dependency graph. |
| `chunks` | Retrieval diagnostics showing raw Dense Retrieval, BM25, and RRF ranking metrics. |

---

# ⚡ Quickstart

## 1. Installation

Clone the repository and install the required dependencies:

```bash
pip install -r requirements.txt
```

---

## 2. Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## 3. Start the Backend

Launch the FastAPI server:

```bash
python -m uvicorn backend.api:app --reload --port 8000
```

Then open `frontend/index.html` in your browser (or serve it using any static file server) to access the interface.

---

# ⚙️ Core Technical Stack

| Component | Technology |
|-----------|------------|
| **API Framework** | FastAPI + Uvicorn |
| **Embeddings Model** | sentence-transformers |
| **Vector Store** | ChromaDB (EphemeralClient, in-memory) |
| **Keyword Retrieval** | rank_bm25 (BM25Okapi) |
| **Inference Engine** | Groq (`llama-3.1-8b-instant`) and (`openai/gpt-oss-20b`) |
| **Parser Engine** | tree-sitter-languages (AST-based code parsing) |
