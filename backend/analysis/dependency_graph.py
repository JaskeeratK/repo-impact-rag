import ast
import os

class DependencyGraph:
    def __init__(self):
        self.graph = {}

    def build(self, repo_path):
        for root, _, files in os.walk(repo_path):
            for f in files:
                if f.endswith(".py"):
                    filepath = os.path.join(root, f)
                    self.graph[filepath] = self._extract_imports(filepath)
        return self.graph

    def _extract_imports(self, filepath):
        imports = []
        try:
            with open(filepath, "r") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except:
            pass
        return imports

    def get_dependents(self, target_file):
        target_module = os.path.basename(target_file).replace(".py", "")
        return [
            file for file, imports in self.graph.items()
            if any(target_module in imp for imp in imports)
        ]