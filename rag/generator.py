from groq import Groq
import os


class Generator:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def generate(self, context_docs, question):
        context_text = "\n\n".join(context_docs)

        prompt = f"""
You are a senior software architect.

Context:
{context_text}

Question:
{question}

Explain the impact clearly and mention possible risks.
"""

        response = self.client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return response.choices[0].message.content
