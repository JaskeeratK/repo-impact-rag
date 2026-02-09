from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL_NAME = "llama3-8b-8192"

def generate_answer(query, contexts):
    context_text = "\n\n".join(
        [c.page_content for c in contexts]
    )

    prompt = f"""
You are a senior software engineer.

Based ONLY on the following git history and code changes:
{context_text}

Answer the question clearly and mention potential impact areas.

Question:
{query}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content
