import os
import google.generativeai as genai
from dotenv import load_dotenv
from src.retrieve import retrieve_relevant_chunks

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-pro')

RAG_PROMPT = """
You are a legal research assistant. Answer the user's question using ONLY the
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

Answer:
"""


def answer_query(query: str, bill_name: str) -> dict:
    """Answer a query about a bill using RAG retrieval + LLM generation."""
    chunks = retrieve_relevant_chunks(query, bill_name)
    context = "\n\n---\n\n".join(
        f"[Section {c['section_id']}]\n{c['content']}"
        for c in chunks
    )

    response = model.generate_content(
        RAG_PROMPT.format(context=context, query=query)
    )

    return {
        'answer': response.text,
        'sources': chunks,
    }
