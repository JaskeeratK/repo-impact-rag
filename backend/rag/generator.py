# import os
# import re
# from groq import Groq


# def clean_chunk(text: str) -> str:
#     """Strip Jupyter notebook JSON noise, keep only source content."""
#     # Remove notebook cell JSON scaffolding
#     text = re.sub(r'"cell_type"\s*:\s*"[^"]*".*?"source"\s*:\s*\[', '', text, flags=re.DOTALL)
#     text = re.sub(r'\\n["\']\s*[,\]]', '\n', text)
#     text = re.sub(r'["\'](\\n)+["\']', '\n', text)
#     text = re.sub(r'\\"', '"', text)
#     text = re.sub(r'\\t', '  ', text)
#     # Remove leftover JSON punctuation
#     text = re.sub(r'^\s*[{}\[\],]\s*$', '', text, flags=re.MULTILINE)
#     return text.strip()


# class Generator:

#     def __init__(self):
#         self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
#     def generate(self, question, chunks, dependents=None):
#         context_parts = []
#         for i, chunk in enumerate(chunks, 1):
#             clean = clean_chunk(chunk["text"])
#             if clean:
#                 context_parts.append(
#                     f"[Source {i}: {chunk['file']} | relevance {chunk['score']}]\n{clean}"
#                 )
#         context_text = "\n\n---\n\n".join(context_parts)

#         dependency_section = ""
#         if dependents:
#             dependency_section = f"\nFiles that import the affected module(s): {', '.join(dependents)}\n"

#         base_context = f"""RETRIEVED CODE:
# {context_text}

# {dependency_section}
# DEVELOPER QUESTION:
# {question}"""

#     # Call 1: prose analysis
#         prose_prompt = f"""{base_context}

# Provide a structured impact analysis with these sections:
# ## Affected Functions/Modules
# ## Code Changes Required
# ## Dependencies to Update
# ## Possible Risks or Bugs
# ## Mitigation Strategies

# Use ## markdown headers for each section. Be specific — reference actual function names, class names, and file paths from the retrieved code."""

#         prose_response = self.client.chat.completions.create(
#             model = "qwen/qwen3.6-27b",
#             messages=[{"role": "user", "content": prose_prompt}],
#             temperature=0.2,
#         )
#         prose = prose_response.choices[0].message.content

#     # Call 2: graph JSON
#         graph_prompt = f"""{base_context}

# Based on the code above, output ONLY a valid JSON object describing the impact graph. No prose, no markdown, just the JSON:
# {{
#   "change": {{"label": "short name of what changes", "detail": "e.g. 12 → 16"}},
#   "direct_changes": [
#     {{"file": "actual/file/path.py", "label": "ClassName or fn", "detail": "what changes"}}
#   ],
#   "dependencies": [
#     {{"file": "actual/file/path.py", "label": "ClassName or fn", "detail": "why affected"}}
#   ]
# }}

# Rules:
# - Maximum 3 items in direct_changes, 3 in dependencies
# - Labels must be under 4 words
# - Use actual file paths and class/function names from the retrieved code
# - Output ONLY the JSON, nothing else"""

#         graph_response = self.client.chat.completions.create(
#             model = "qwen/qwen3.6-27b",
#             messages=[{"role": "user", "content": graph_prompt}],
#             temperature=0.1,
#         )

#         graph_json = None
#         try:
#             raw = graph_response.choices[0].message.content.strip()
#             raw = raw.replace("```json", "").replace("```", "").strip()
#             graph_json = json.loads(raw)
#         except Exception:
#             pass

#         return prose, graph_json
import os
import re
import json
from groq import Groq

PROSE_MODEL = "openai/gpt-oss-20b"
GRAPH_MODEL = "llama-3.1-8b-instant"

def clean_chunk(text: str) -> str:
    """Strip Jupyter notebook JSON noise, keep only source content."""
    text = re.sub(r'"cell_type"\s*:\s*"[^"]*".*?"source"\s*:\s*\[', '', text, flags=re.DOTALL)
    text = re.sub(r'\\n["\']\s*[,\]]', '\n', text)
    text = re.sub(r'["\'](\\n)+["\']', '\n', text)
    text = re.sub(r'\\"', '"', text)
    text = re.sub(r'\\t', '  ', text)
    text = re.sub(r'^\s*[{}\[\],]\s*$', '', text, flags=re.MULTILINE)
    return text.strip()


class Generator:

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def generate(self, question, chunks, dependents=None):
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            clean = clean_chunk(chunk["text"])
            if clean:
                context_parts.append(
                    f"[Source {i}: {chunk['file']} | relevance {chunk['score']}]\n{clean}"
                )
        context_text = "\n\n---\n\n".join(context_parts)

        dependency_section = ""
        if dependents:
            dependency_section = f"\nFiles that import the affected module(s): {', '.join(dependents)}\n"

        base_context = f"""RETRIEVED CODE:
{context_text}

{dependency_section}
DEVELOPER QUESTION:
{question}"""

        # Call 1: prose analysis
        prose_prompt = f"""{base_context}

Provide a structured impact analysis with these sections:
## Affected Functions/Modules
## Code Changes Required
## Dependencies to Update
## Possible Risks or Bugs
## Mitigation Strategies

Use ## markdown headers for each section. Be specific — reference actual function names, class names, and file paths from the retrieved code."""

        prose_response = self.client.chat.completions.create(
            model=PROSE_MODEL,
            messages=[
                {"role": "system", "content": "You are a senior software engineer. Respond directly with the analysis only."},
                {"role": "user", "content": prose_prompt}
            ],
            temperature=0.2,
            
        )
        prose = prose_response.choices[0].message.content

        # Call 2: graph JSON
        graph_prompt = f"""{base_context}

Output ONLY a valid JSON object. No thinking, no prose, no markdown fences, just raw JSON:
{{
  "change": {{"label": "short name of what changes", "detail": "e.g. 12 → 16"}},
  "direct_changes": [
    {{"file": "actual/file/path.py", "label": "ClassName or fn", "detail": "what changes"}}
  ],
  "dependencies": [
    {{"file": "actual/file/path.py", "label": "ClassName or fn", "detail": "why affected"}}
  ]
}}

Rules:
- Maximum 3 items in direct_changes, 3 in dependencies
- Labels must be under 4 words
- Use actual file paths and class/function names from the retrieved code
- Output ONLY the JSON, nothing else"""

        graph_response = self.client.chat.completions.create(
            model=GRAPH_MODEL,
            messages=[
                {"role": "system", "content": "You output only raw JSON. No explanation. No markdown. Just the JSON object."},
                {"role": "user", "content": graph_prompt}
            ],
            temperature=0.1,
            
        )

        graph_json = None
        try:
            raw = graph_response.choices[0].message.content.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            # Strip thinking tags if model still outputs them
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            graph_json = json.loads(raw)
        except Exception as e:
            print(f"Graph JSON parse failed: {e}")
            print(f"Raw response: {graph_response.choices[0].message.content[:200]}")

        return prose, graph_json
