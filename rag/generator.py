from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

def generate_answer(query, contexts):
    context_text = "\n\n".join([c.page_content for c in contexts])

    prompt = f"""
    You are analyzing code changes.
    Based ONLY on the following history:
    {context_text}

    Question: {query}
    """
    return llm.predict(prompt)
