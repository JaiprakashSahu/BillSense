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


def extract_year(bill_name: str) -> str:
    """Extract year from bill name like 'Personal_Data_Protection_Bill_2019'."""
    import re
    match = re.search(r'(\d{4})', bill_name)
    return match.group(1) if match else "Unknown"


def get_available_bills() -> list[dict]:
    """Get list of bills from chunks dir (embedded = queryable), with summary status."""
    bills = []
    seen = set()

    # Scan chunks dir for all processed bills
    if os.path.exists(CHUNKS_DIR):
        for fname in sorted(os.listdir(CHUNKS_DIR)):
            if fname.endswith('_chunks.json'):
                bill_name = fname.replace('_chunks.json', '')
                if bill_name in seen:
                    continue
                seen.add(bill_name)
                display_name = bill_name.replace('_', ' ')
                year = extract_year(bill_name)
                summary_path = os.path.join(SUMMARIES_DIR, f"{bill_name}.md")
                bills.append({
                    'id': bill_name,
                    'name': display_name,
                    'year': year,
                    'has_summary': os.path.exists(summary_path),
                })

    return bills


def get_bills_by_year() -> dict:
    """Group available bills by year."""
    bills = get_available_bills()
    by_year = {}
    for bill in bills:
        year = bill['year']
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(bill)
    # Sort years descending (newest first)
    return dict(sorted(by_year.items(), reverse=True))


class QueryRequest(BaseModel):
    query: str
    bill_id: str
    top_k: int = 5


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "BillSense"}


@app.get("/api/bills")
def list_bills():
    """List all available bills grouped by year."""
    return {
        "bills": get_available_bills(),
        "by_year": get_bills_by_year(),
    }


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
            from src.llm import get_client

            context = "\n\n---\n\n".join(
                f"[Section: {c['section_header']}]\n{c['content'][:1000]}"
                for c in chunks
            )

            # Trim context to stay under ~5000 tokens
            if len(context.split()) > 4000:
                context = " ".join(context.split()[:4000])

            prompt = f"""You are a legal expert on Indian legislation. Answer the user's question about this bill using the provided context. Be thorough and helpful.

Context from the bill:
{context}

User question: {req.query}

Instructions:
- Answer the question as completely as possible using the context
- Cite section/clause numbers where available like [Section X] or [Clause X]
- If the exact answer isn't in the context, use what IS available to give the most relevant and helpful response — explain related provisions, definitions, or framework from the context
- Use plain, simple language a non-lawyer can understand
- Structure your answer with bullet points or numbered lists where appropriate
- Do not include any thinking or reasoning tags - just provide the answer directly

Answer:"""

            groq_client = get_client()
            stream = groq_client.chat(
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
