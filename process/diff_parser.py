import re


class DiffParser:
    def parse(self, diff_text):
        lines_added = len(re.findall(r'^\+', diff_text, re.MULTILINE))
        lines_removed = len(re.findall(r'^-', diff_text, re.MULTILINE))

        functions = re.findall(r'def (\w+)\(', diff_text)

        return {
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "functions_modified": list(set(functions))
        }
