import os
from groq import Groq
from dotenv import load_dotenv
from src.retrieve import retrieve_relevant_chunks

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "qwen/qwen3.8-27b"

RAG_PROMPT = """You are a legal research assistant. Answer the user's question using ONLY the
provided context from an Indian bill. Cite the section number for each claim.

Context:
{context}

User question: {query}

Instructions:
- Only use information from the context above
- Cite section numbers like [Section X]
- If context doesn't answer the question, say "The provided sections don't
  address this specifically."
- Use plain language
- Do not include any thinking or reasoning tags - just provide the answer directly

Answer:"""


def answer_query(query: str, bill_name: str) -> dict:
    """Answer a query about a bill using RAG retrieval + LLM generation."""
    chunks = retrieve_relevant_chunks(query, bill_name)
    context = "\n\n---\n\n".join(
        f"[Section: {c['section_header']}]\n{c['content']}"
        for c in chunks
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": RAG_PROMPT.format(context=context, query=query)
        }],
        max_tokens=2048,
    )

    return {
        'answer': response.choices[0].message.content,
        'sources': chunks,
    }
