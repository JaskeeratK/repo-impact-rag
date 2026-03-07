import os
from groq import Groq


class Generator:

    def __init__(self):

        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

    def generate(self, question, contexts):

        context_text = "\n\n".join(contexts)

        prompt = f"""
You are a senior backend engineer performing code impact analysis.

Repository code snippets:
{context_text}

Developer question:
{question}

Explain:
1. Which functions/modules will be affected
2. What code changes are required
3. What dependencies must be replaced
4. Possible risks or bugs introduced

Give a structured technical answer.
"""

        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content