# import os
# import uuid

# from backend.ingest.repo_loader import RepoLoader
# from backend.embeddings.embedder import Embedder
# from backend.vectorstore.store import VectorStore


# ALLOWED_EXTENSIONS = [
#     ".py",
#     ".js",
#     ".ts",
#     ".html",
#     ".css"
# ]


# def read_files(repo_path):
#     files = []

#     for root, _, filenames in os.walk(repo_path):

#         for file in filenames:

#             if any(file.endswith(ext) for ext in ALLOWED_EXTENSIONS):

#                 path = os.path.join(root, file)

#                 try:
#                     with open(path, "r", encoding="utf-8") as f:
#                         content = f.read()

#                         files.append({
#                             "path": path,
#                             "content": content
#                         })

#                 except:
#                     continue

#     return files


# import ast as ast_module

# def chunk_by_functions(file_path, content):
#     chunks = []
#     if file_path.endswith(".py"):
#         try:
#             tree = ast_module.parse(content)
#             for node in ast_module.walk(tree):
#                 if isinstance(node, (ast_module.FunctionDef, ast_module.ClassDef)):
#                     start = node.lineno - 1
#                     end = node.end_lineno
#                     lines = content.splitlines()[start:end]
#                     chunks.append({
#                         "content": "\n".join(lines),
#                         "name": node.name,
#                         "type": "function" if isinstance(node, ast_module.FunctionDef) else "class"
#                     })
#         except SyntaxError:
#             pass
#     # fallback for non-Python or failed parse
#     if not chunks:
#         for i in range(0, len(content), 800):
#             chunks.append({
#                 "content": content[i:i+800],
#                 "name": "chunk",
#                 "type": "raw"
#             })
#     return chunks


# def build_index(repo_url):

#     repo_loader = RepoLoader(repo_url)
#     repo_path = repo_loader.clone()

#     embedder = Embedder()
#     store = VectorStore()

#     files = read_files(repo_path)

#     print("Files found:", len(files))

#     total_chunks = 0

#     # for file in files:
#     #     chunks = chunk_by_functions(file["path"], file["content"])
#     #     for chunk in chunks:
#     #         embedding = embedder.embed(chunk["content"])[0]
#     #         store.add(
#     #             ids=[str(uuid.uuid4())],
#     #             documents=[chunk["content"]],
#     #             embeddings=[embedding],
#     #             metadatas=[{
#     #                 "file": file["path"],
#     #                 "name": chunk["name"],
#     #                 "type": chunk["type"]
#     #             }]
#     #         )
#     files = read_files(repo_path)
#     print("Files found:", len(files))

#     total_chunks = 0

#     for file in files:
#         chunks = chunk_by_functions(file["path"], file["content"])
#         for chunk in chunks:
#             embedding = embedder.embed(chunk["content"])[0]
#             store.add(
#                 ids=[str(uuid.uuid4())],
#                 documents=[chunk["content"]],
#                 embeddings=[embedding],
#                 metadatas=[{
#                     "file": file["path"],
#                     "name": chunk["name"],
#                     "type": chunk["type"]
#                 }]
#             )
#             total_chunks += 1

#     print("Chunks indexed:", total_chunks)
#     return repo_path  # critical — api.py needs this
import os
import re
import uuid
import chardet

from pygments.lexers import get_lexer_for_filename, guess_lexer
from pygments.util import ClassNotFound

from backend.ingest.repo_loader import RepoLoader
from backend.embeddings.embedder import Embedder
from backend.vectorstore.store import VectorStore


# ---------------------------------------------------------------------------
# Files / directories to always skip
# ---------------------------------------------------------------------------
SKIP_DIRS = {
    ".git", ".github", "node_modules", "__pycache__", ".venv", "venv",
    "env", ".env", "dist", "build", ".next", ".nuxt", "coverage",
    ".pytest_cache", ".mypy_cache", "target", "out", ".idea", ".vscode",
}

SKIP_EXTENSIONS = {
    # binaries & media
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".bmp",
    ".mp4", ".mp3", ".wav", ".pdf", ".zip", ".tar", ".gz", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".wasm", ".bin", ".obj",
    # compiled / lock
    ".pyc", ".pyo", ".class", ".o",
    "package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock",
}

# Extensions we know are text — pygments will handle the rest
TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".go", ".rs", ".rb", ".php",
    ".c", ".cpp", ".cc", ".h", ".hpp",
    ".cs", ".swift", ".kt", ".scala",
    ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".md", ".mdx", ".rst", ".txt",
    ".sh", ".bash", ".zsh", ".fish",
    ".sql", ".graphql", ".proto",
    ".xml", ".env.example", ".gitignore", ".dockerignore",
    "Dockerfile", "Makefile", ".tf", ".hcl",
}


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def is_text_file(filepath: str) -> bool:
    """Return True if the file is likely a readable text file."""
    _, ext = os.path.splitext(filepath)
    basename = os.path.basename(filepath)

    if ext.lower() in SKIP_EXTENSIONS or basename in SKIP_EXTENSIONS:
        return False
    if ext.lower() in TEXT_EXTENSIONS or basename in TEXT_EXTENSIONS:
        return True

    # For files with no extension or unknown extension, sniff with chardet
    try:
        with open(filepath, "rb") as f:
            raw = f.read(4096)
        if b"\x00" in raw:   # null bytes → binary
            return False
        result = chardet.detect(raw)
        return result["encoding"] is not None
    except Exception:
        return False


def detect_language(filepath: str) -> str:
    """Return a human-readable language name using pygments."""
    try:
        lexer = get_lexer_for_filename(filepath)
        return lexer.name
    except ClassNotFound:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(2048)
            lexer = guess_lexer(content)
            return lexer.name
        except ClassNotFound:
            return "Text"


# ---------------------------------------------------------------------------
# Reading files
# ---------------------------------------------------------------------------

def read_file_content(filepath: str):
    """Read a file, auto-detecting encoding."""
    try:
        with open(filepath, "rb") as f:
            raw = f.read()
        detected = chardet.detect(raw)
        encoding = detected.get("encoding") or "utf-8"
        return raw.decode(encoding, errors="replace")
    except Exception:
        return None


def read_files(repo_path: str) -> list:
    files = []
    for root, dirs, filenames in os.walk(repo_path):
        # Prune skipped directories in-place so os.walk doesn't descend into them
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in filenames:
            filepath = os.path.join(root, filename)
            if not is_text_file(filepath):
                continue
            content = read_file_content(filepath)
            if content and content.strip():
                files.append({
                    "path": filepath,
                    "content": content,
                    "language": detect_language(filepath),
                })
    return files


# ---------------------------------------------------------------------------
# Chunking  (tree-sitter for supported languages, fallback for everything else)
# ---------------------------------------------------------------------------

# Map pygments language names -> tree-sitter language names
TREESITTER_LANG_MAP = {
    "Python":     "python",
    "JavaScript": "javascript",
    "TypeScript": "typescript",
    "TSX":        "tsx",
    "Go":         "go",
    "Rust":       "rust",
    "Java":       "java",
    "Ruby":       "ruby",
    "C":          "c",
    "C++":        "cpp",
}

# tree-sitter node types that represent top-level callable/class blocks
FUNCTION_NODE_TYPES = {
    "function_definition",    # Python
    "class_definition",       # Python
    "function_declaration",   # JS / TS / Go / Java
    "method_definition",      # JS / TS
    "arrow_function",         # JS / TS
    "method_declaration",     # Java
    "class_declaration",      # Java / JS / TS
    "function_item",          # Rust
    "impl_item",              # Rust
    "func_declaration",       # Go
}


def _try_treesitter_chunks(language_name: str, content: str):
    """
    Try to chunk content using tree-sitter-languages (the convenience wrapper).
    Returns a list of chunk dicts, or None if unavailable for this language.
    """
    ts_lang = TREESITTER_LANG_MAP.get(language_name)
    if not ts_lang:
        return None

    try:
        from tree_sitter_languages import get_language, get_parser
        parser = get_parser(ts_lang)
        tree = parser.parse(bytes(content, "utf-8"))
    except Exception:
        return None

    lines = content.splitlines()
    chunks = []

    def walk(node):
        if node.type in FUNCTION_NODE_TYPES:
            start = node.start_point[0]
            end   = node.end_point[0] + 1
            name  = "unknown"
            for child in node.children:
                if child.type in ("identifier", "name", "property_identifier"):
                    name = content[child.start_byte:child.end_byte]
                    break
            chunks.append({
                "content": "\n".join(lines[start:end]),
                "name": name,
                "type": node.type,
            })
            return   # don't recurse — avoids nested duplicates
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return chunks if chunks else None


def _fallback_chunks(content: str, chunk_size: int = 800) -> list:
    """Split content into fixed-size chunks (used for config, markup, etc.)."""
    return [
        {
            "content": content[i:i + chunk_size],
            "name": f"chunk_{i // chunk_size}",
            "type": "raw",
        }
        for i in range(0, len(content), chunk_size)
    ]


def chunk_file(filepath: str, content: str, language: str) -> list:
    """
    1. Try tree-sitter AST chunking (best quality, proper function boundaries).
    2. Fall back to fixed-size raw chunks.
    """
    chunks = _try_treesitter_chunks(language, content)
    if chunks:
        return chunks
    return _fallback_chunks(content)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def build_index(repo_url: str):
    repo_loader = RepoLoader(repo_url)
    repo_path = repo_loader.clone()

    embedder = Embedder()
    store = VectorStore()

    files = read_files(repo_path)
    print(f"Files found: {len(files)}")

    total_chunks = 0

    for file in files:
        chunks = chunk_file(file["path"], file["content"], file["language"])
        for chunk in chunks:
            if not chunk["content"].strip():
                continue
            embedding = embedder.embed(chunk["content"])[0]
            store.add(
                ids=[str(uuid.uuid4())],
                documents=[chunk["content"]],
                embeddings=[embedding],
                metadatas=[{
                    "file":     file["path"],
                    "name":     chunk["name"],
                    "type":     chunk["type"],
                    "language": file["language"],
                }]
            )
            total_chunks += 1

    print(f"Chunks indexed: {total_chunks}")
    return repo_path, total_chunks