import os
from dotenv import load_dotenv
from src.retrieve import retrieve_relevant_chunks
from src.llm import get_client

load_dotenv()

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

    client = get_client()
    response = client.chat(
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
