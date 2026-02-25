
from groq import Groq
import os


class Summarizer:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def summarize_diff(self, diff_text):
        prompt = f"""
You are a senior software architect.

Analyze this git diff and explain:
1. What changed
2. Which components are affected
3. Possible architectural impact

Diff:
{diff_text[:4000]}
"""

        response = self.client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        return response.choices[0].message.content
