# RIA

<img width="1327" height="650" alt="ria5" src="https://github.com/user-attachments/assets/068cadea-256e-486b-a921-ccead3e6990f" />
<img width="1336" height="640" alt="ria6" src="https://github.com/user-attachments/assets/c01ae45a-6707-456f-9f6a-a03ac431b717" />
# Repo Impact Analyzer (RIA)

> Point it at any GitHub repo. Ask what breaks. Get a real answer.

RIA is a RAG-powered developer tool that clones a repository, indexes every file into a vector database, builds a cross-language dependency graph, and uses an LLM to answer natural language questions about code impact.

**"What breaks if I change the auth middleware?"** → RIA retrieves the relevant code, finds all files that import it, and gives you a structured technical answer.

---

## How It Works

```
User question
     │
     ▼
Embed question (all-MiniLM-L6-v2)
     │
     ▼
ChromaDB vector search → top 5 relevant code chunks + source file paths
     │
     ▼
DependencyGraph.get_dependents() → files that import the affected modules
     │
     ▼
LLaMA 3.1 8B (via Groq) → structured impact analysis
```

Two phases:

1. **Index** — clone repo → read files → AST chunk by function → embed → store in ChromaDB + build dependency graph
2. **Query** — embed question → vector search → dependency lookup → LLM generation

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Vector DB | ChromaDB (local, persisted to disk) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| AST Chunking | `tree-sitter-languages` |
| Language detection | `pygments` |
| Encoding detection | `chardet` |
| LLM | LLaMA 3.1 8B via Groq API |
| Repo ingestion | `gitpython` |
| Frontend | Vanilla HTML / CSS / JS |

---

## Project Structure

```
repo-impact-rag/
├── backend/
│   ├── analysis/
│   │   └── dependency_graph.py     # Import graph (Python, JS, TS, Go, Rust, Java, Ruby, CSS, HTML)
│   ├── embeddings/
│   │   └── embedder.py             # sentence-transformers wrapper
│   ├── ingest/
│   │   ├── repo_loader.py          # git clone via gitpython
│   │   ├── commit_loader.py        # git history loader
│   │   └── pr_loader.py            # GitHub PR loader
│   ├── process/
│   │   ├── diff_parser.py          # Parse git diffs
│   │   └── summarizer.py           # Groq-based diff summarizer
│   ├── rag/
│   │   ├── generator.py            # LLaMA prompt + generation
│   │   └── retriever.py            # ChromaDB semantic search
│   ├── vectorstore/
│   │   ├── build_index.py          # Main indexing pipeline
│   │   └── store.py                # ChromaDB client wrapper
│   └── api.py                      # FastAPI routes
├── frontend/
│   ├── index.html
│   ├── scripts.js                  # API calls + UI logic
│   ├── network.js                  # Animated canvas hero
│   └── style.css
├── .env                            # API keys (not committed)
└── requirements.txt
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create `.env` in the project root

```
GROQ_API_KEY=your_groq_api_key_here
gh_token=your_github_personal_access_token_here
```

- Groq key → [console.groq.com](https://console.groq.com)
- GitHub PAT → Settings → Developer Settings → Personal Access Tokens (needs `repo` scope)

### 3. Start the backend

```bash
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

> `--host 0.0.0.0` is required in Codespaces so the server is reachable from the frontend.

### 4. Start the frontend

Click **Go Live** in VS Code (Live Server extension), or:

```bash
cd frontend && npx serve .
```

### 5. (Codespaces only) Expose port 8000

Ports tab → port `8000` → right-click → **Port Visibility → Public**. Copy the forwarded URL and update `scripts.js`:

```js
const API_BASE = "https://your-codespace-8000.app.github.dev";
```

---

## API

### `POST /build-index`

Clones the repo, indexes all files, builds the dependency graph.

```json
// Request
{ "repo_url": "https://github.com/owner/repo" }

// Response
{
  "status": "success",
  "message": "Index built successfully",
  "files_indexed": 342
}
```

### `POST /analyze`

Retrieves relevant code, runs dependency lookup, generates impact analysis.

```json
// Request
{ "question": "What breaks if I change the auth middleware?" }

// Response
{
  "status": "success",
  "answer": "...",
  "contexts": ["..."],
  "affected_files": ["temp_repo/routes/login.py", "temp_repo/middleware/session.py"]
}
```

### `POST /analyze-with-history`

Same as `/analyze` but injects the last 5 commit diffs as additional context.

```json
// Request
{ "repo_path": "temp_repo", "question": "What changed recently in auth?" }
```

---

## Indexing Pipeline (deep dive)

### File filtering

Three layers before anything gets indexed:

- **Directory pruning** — `node_modules`, `.git`, `__pycache__`, `dist`, `.venv`, `.next`, `target` etc. are skipped entirely at the `os.walk()` level
- **Extension blocklist** — binaries, images, compiled files, lock files all skipped
- **Binary sniffing** — for unknown/extensionless files, `chardet` reads the first 4KB. Null bytes → binary. Detectable encoding → text.

### Chunking strategy

Chunk quality is the most important factor in RAG retrieval. Fixed-size character splits frequently cut functions in half, destroying the semantic unit. RIA uses `tree-sitter` to parse files into an AST and extract individual functions and classes as chunks — **one chunk = one function or class**.

| Language | Chunking |
|---|---|
| Python, JS, TS, TSX, Go, Rust, Java, Ruby, C, C++ | tree-sitter AST (exact function/class boundaries) |
| HTML, CSS, JSON, YAML, Markdown, SQL, Shell, etc. | 800-char fixed-size fallback |

### Dependency graph

A second pass over the repo builds a structural import map for every file:

| Language | Method | Patterns |
|---|---|---|
| Python | `ast` module | `import X`, `from X import Y` |
| JS / TS / JSX / TSX | regex | `import X from '...'`, `require('...')`, `import('...')` |
| Go | regex | `import "pkg"`, block imports |
| Rust | regex | `use std::x`, `extern crate x` |
| Java / Kotlin / Scala | regex | `import com.example.X` |
| Ruby | regex | `require '...'`, `require_relative '...'` |
| CSS / SCSS / LESS | regex | `@import`, `@use` |
| HTML | regex | `<script src=...>`, `<link href=...>` |

`get_dependents(file)` returns every file in the graph whose import list contains the target module name.

---

## Why RAG instead of sending the whole repo?

Most repos are hundreds of thousands of tokens. LLMs have context limits and degrade significantly with too much irrelevant content. RAG retrieves only the 5 most semantically relevant code chunks (~500–1000 tokens) so the LLM can focus precisely on what matters.

The dependency graph complements the vector search: semantic search answers *"what code is relevant?"* — the graph answers *"what else imports this and could break?"* Neither alone gives the full picture.

---

## Known Limitations

| Limitation | Detail |
|---|---|
| Single repo at a time | ChromaDB uses one collection — indexing a new repo overwrites the previous one. Fix: namespace by repo URL hash. |
| Dependency graph lost on restart | `app.state` is in-memory. ChromaDB persists but the graph doesn't. Fix: serialize graph to JSON on disk. |
| Non-code embeddings | `all-MiniLM-L6-v2` is trained on natural language. A code-specific model (CodeBERT, `code-search-net`) would improve retrieval. |
| Hardcoded `API_BASE` | Codespaces forwarded URL changes on rebuild. Fix: use an env variable or auto-detect at runtime. |
| No auth | `allow_origins=["*"]` with no API key. Fine for local use, not for public deployment. |
