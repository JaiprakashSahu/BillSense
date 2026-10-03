"""BillSense FastAPI Backend — serves RAG Q&A and summaries."""

import os
import sys
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="BillSense API", description="RAG-based Indian Bill Q&A")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
SUMMARIES_DIR = os.path.join(BASE_DIR, "data", "summaries")
CHUNKS_DIR = os.path.join(BASE_DIR, "data", "chunks")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")


def get_available_bills() -> list[dict]:
    """Get list of bills that have been processed."""
    bills = []
    if not os.path.exists(SUMMARIES_DIR):
        return bills

    for fname in sorted(os.listdir(SUMMARIES_DIR)):
        if fname.endswith('.md'):
            bill_name = fname.replace('.md', '')
            display_name = bill_name.replace('_', ' ')
            bills.append({
                'id': bill_name,
                'name': display_name,
                'has_summary': True,
            })
    return bills


class QueryRequest(BaseModel):
    query: str
    bill_id: str
    top_k: int = 5


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "BillSense"}


@app.get("/api/bills")
def list_bills():
    """List all available bills."""
    return {"bills": get_available_bills()}


@app.get("/api/bills/{bill_id}/summary")
def get_summary(bill_id: str):
    """Get the summary for a specific bill."""
    summary_path = os.path.join(SUMMARIES_DIR, f"{bill_id}.md")
    if not os.path.exists(summary_path):
        raise HTTPException(status_code=404, detail="Summary not found for this bill")

    with open(summary_path, 'r') as f:
        content = f.read()

    return {"bill_id": bill_id, "summary": content}


@app.post("/api/query")
def query_bill(req: QueryRequest):
    """Answer a question about a bill using RAG."""
    import time
    start = time.time()

    try:
        from src.generate import answer_query
        result = answer_query(req.query, req.bill_id)
        processing_time = round(time.time() - start, 2)

        return {
            "answer": result['answer'],
            "sources": [
                {
                    "section_header": s.get('section_header', ''),
                    "chunk_id": s.get('chunk_id', ''),
                    "content": s['content'][:500],
                    "distance": round(s['distance'], 4),
                }
                for s in result['sources']
            ],
            "processing_time": processing_time,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stream")
async def stream_query(req: QueryRequest):
    """Stream answer for a question about a bill (SSE)."""
    import time

    async def event_stream():
        start = time.time()

        # Stage 1: Searching
        yield f"data: {json.dumps({'type': 'progress', 'stage': 'searching', 'message': 'Searching relevant sections...'})}\n\n"

        try:
            from src.retrieve import retrieve_relevant_chunks
            chunks = retrieve_relevant_chunks(req.query, req.bill_id, top_k=req.top_k)
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

        # Stage 2: Generating
        yield f"data: {json.dumps({'type': 'progress', 'stage': 'generating', 'message': 'Generating answer...'})}\n\n"

        try:
            from groq import Groq
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))

            context = "\n\n---\n\n".join(
                f"[Section: {c['section_header']}]\n{c['content']}"
                for c in chunks
            )

            prompt = f"""You are a legal research assistant. Answer the user's question using ONLY the
provided context from an Indian bill. Cite the section number for each claim.

Context:
{context}

User question: {req.query}

Instructions:
- Only use information from the context above
- Cite section numbers like [Section X]
- If context doesn't answer the question, say "The provided sections don't address this specifically."
- Use plain language
- Do not include any thinking or reasoning tags - just provide the answer directly

Answer:"""

            stream = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                stream=True,
            )

            for chunk_resp in stream:
                if chunk_resp.choices[0].delta.content:
                    token = chunk_resp.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'chunk', 'content': token})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

        processing_time = round(time.time() - start, 2)

        # Send sources and completion
        sources_data = [
            {
                "section_header": s.get('section_header', ''),
                "chunk_id": s.get('chunk_id', ''),
                "content": s['content'][:500],
                "distance": round(s['distance'], 4),
            }
            for s in chunks
        ]

        yield f"data: {json.dumps({'type': 'complete', 'sources': sources_data, 'processing_time': processing_time})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
