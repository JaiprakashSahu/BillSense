import os
from dotenv import load_dotenv
from src.retrieve import retrieve_relevant_chunks
from src.llm import get_client

load_dotenv()

RAG_PROMPT = """You are a legal expert on Indian legislation. Answer the user's question about this bill using the provided context. Be thorough and helpful.

Context from the bill:
{context}

User question: {query}

Instructions:
- Answer the question as completely as possible using the context
- Cite section/clause numbers where available like [Section X] or [Clause X]
- If the exact answer isn't in the context, use what IS available to give the most relevant and helpful response — explain related provisions, definitions, or framework from the context
- Use plain, simple language a non-lawyer can understand
- Structure your answer with bullet points or numbered lists where appropriate
- Do not include any thinking or reasoning tags - just provide the answer directly

Answer:"""


def answer_query(query: str, bill_name: str) -> dict:
    """Answer a query about a bill using RAG retrieval + LLM generation."""
    chunks = retrieve_relevant_chunks(query, bill_name, top_k=5)
    context = "\n\n---\n\n".join(
        f"[Section: {c['section_header']}]\n{c['content'][:1000]}"
        for c in chunks
    )

    # Trim context to stay under ~5000 tokens
    if len(context.split()) > 4000:
        context = " ".join(context.split()[:4000])

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
