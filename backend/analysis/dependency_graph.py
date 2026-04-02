import ast
import os
import re


class DependencyGraph:
    def __init__(self):
        self.graph = {}

    def build(self, repo_path):
        for root, dirs, files in os.walk(repo_path):
            # Skip non-source directories
            dirs[:] = [d for d in dirs if d not in {
                ".git", "node_modules", "__pycache__", ".venv",
                "venv", "dist", "build", ".next", "target",
            }]
            for f in files:
                filepath = os.path.join(root, f)
                imports = self._extract_imports(filepath)
                if imports is not None:
                    self.graph[filepath] = imports
        return self.graph

    def _extract_imports(self, filepath: str):
        """
        Dispatch to the right extractor based on file extension.
        Returns a list of import strings, or None if unsupported.
        """
        ext = os.path.splitext(filepath)[1].lower()
        basename = os.path.basename(filepath)

        if ext == ".py":
            return self._python_imports(filepath)
        elif ext in (".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"):
            return self._js_imports(filepath)
        elif ext == ".go":
            return self._go_imports(filepath)
        elif ext == ".rs":
            return self._rust_imports(filepath)
        elif ext in (".java", ".kt", ".scala"):
            return self._java_imports(filepath)
        elif ext == ".rb":
            return self._ruby_imports(filepath)
        elif ext in (".css", ".scss", ".sass", ".less"):
            return self._css_imports(filepath)
        elif ext in (".html", ".htm"):
            return self._html_imports(filepath)
        elif basename in ("Dockerfile",) or ext in (".sh", ".bash"):
            return []   # tracked but no imports to extract
        else:
            return None  # unsupported — don't add to graph

    # ------------------------------------------------------------------ #
    #  Language-specific extractors                                        #
    # ------------------------------------------------------------------ #

    def _python_imports(self, filepath):
        imports = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except Exception:
            pass
        return imports

    def _js_imports(self, filepath):
        imports = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            # ES6: import X from './foo'  /  import './foo'
            imports += re.findall(
                r'import\s+(?:.*?\s+from\s+)?[\'"](.+?)[\'"]', content)
            # CommonJS: require('./foo')
            imports += re.findall(r'require\s*\(\s*[\'"](.+?)[\'"]\s*\)', content)
            # Dynamic: import('./foo')
            imports += re.findall(r'import\s*\(\s*[\'"](.+?)[\'"]\s*\)', content)
        except Exception:
            pass
        return imports

    def _go_imports(self, filepath):
        imports = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            # Single: import "fmt"
            imports += re.findall(r'import\s+"([^"]+)"', content)
            # Block: import ( "fmt"\n "os" )
            blocks = re.findall(r'import\s*\(([^)]+)\)', content, re.DOTALL)
            for block in blocks:
                imports += re.findall(r'"([^"]+)"', block)
        except Exception:
            pass
        return imports

    def _rust_imports(self, filepath):
        imports = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            # use std::collections::HashMap;
            imports += re.findall(r'use\s+([\w:]+)', content)
            # extern crate foo;
            imports += re.findall(r'extern\s+crate\s+(\w+)', content)
        except Exception:
            pass
        return imports

    def _java_imports(self, filepath):
        imports = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            imports += re.findall(r'import\s+([\w.]+);', content)
        except Exception:
            pass
        return imports

    def _ruby_imports(self, filepath):
        imports = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            imports += re.findall(r"require\s+['\"](.+?)['\"]", content)
            imports += re.findall(r"require_relative\s+['\"](.+?)['\"]", content)
        except Exception:
            pass
        return imports

    def _css_imports(self, filepath):
        imports = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            imports += re.findall(r'@import\s+[\'"](.+?)[\'"]', content)
            imports += re.findall(r'@use\s+[\'"](.+?)[\'"]', content)
        except Exception:
            pass
        return imports

    def _html_imports(self, filepath):
        imports = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            # <script src="..."> and <link href="...">
            imports += re.findall(r'<script[^>]+src=[\'"]([^\'"]+)[\'"]', content)
            imports += re.findall(r'<link[^>]+href=[\'"]([^\'"]+)[\'"]', content)
        except Exception:
            pass
        return imports

    # ------------------------------------------------------------------ #
    #  Dependency lookup                                                   #
    # ------------------------------------------------------------------ #

    def get_dependents(self, target_file: str) -> list:
        """Return all files that import the given target file."""
        # Strip extension to get the module/base name
        base = os.path.splitext(os.path.basename(target_file))[0]
        return [
            file for file, imports in self.graph.items()
            if file != target_file and any(base in imp for imp in imports)
        ]