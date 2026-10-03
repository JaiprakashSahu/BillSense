# BillSense: RAG-based Indian Bill Summarization & Query System

## Project Overview

Build a Retrieval-Augmented Generation (RAG) system that takes long Indian government bills (200-300+ pages), produces plain-language hierarchical summaries, and answers natural-language questions with grounded citations.

**Inspired by**: MiAI Law's legal case pipeline (30-40K pages → 20-25 page summaries + RAG Q&A)  
**Domain**: Indian government legislation (non-competing with MiAI Law's legal case domain)  
**Constraint**: Zero budget — free tiers only  
**Target**: Academic project deliverable + portfolio piece

## Why This Project Works

1. **Real-world value** — citizens/journalists rarely read full bills
2. **Demonstrates full RAG pipeline** — ingestion, chunking, summarization, embeddings, retrieval, Q&A
3. **Easy demo** — load a bill, ask a question, get cited answer
4. **Portfolio-friendly** — recruiter-recognizable tools (Gemini, Chroma, Streamlit)
5. **Academic-friendly** — clear architecture, measurable results

## Tech Stack (All Free)

| Component | Choice | Why |
|---|---|---|
| LLM | Google Gemini 1.5 Pro (free tier) | 1M-token context handles huge bills, free API |
| Embeddings | Gemini embedding-001 | Free, high quality, integrated with LLM |
| Vector DB | Chroma (local) | Free, no cloud needed, simple Python API |
| Web UI | Streamlit | Free, minimal setup, recruiter-recognizable |
| PDF parsing | PyMuPDF (fitz) | Free, fast, handles complex PDFs |
| Compute | Local laptop + Google Colab | Free, API-based inference |
| Version control | GitHub | Free, portfolio-visible |

**Fallback options**:
- Groq API (free, fast Llama/Mixtral) if Gemini rate-limits
- OpenRouter (free tier models) as backup
- Qdrant cloud free tier if Chroma isn't enough

## Data Sources

| Source | URL | What it offers |
|---|---|---|
| PRS Legislative Research | prsindia.org | Bills + expert explainer notes |
| Sansad (Parliament of India) | sansad.in | Official PDFs of introduced bills |
| India Code | indiacode.nic.in | Enacted laws repository |

**Recommended starting set (3 bills)**:
1. Personal Data Protection Bill 2019 — well-documented, sample size manageable
2. Digital Personal Data Protection Act 2023 — recent, high public interest
3. Bharatiya Nyaya Sanhita 2023 — massive replacement for IPC, high complexity

## System Architecture

┌─────────────────────┐
                │  Bill PDF (200p)    │
                └──────────┬──────────┘
                           ↓
          ┌────────────────────────────────┐
          │  1. Ingestion & Section        │
          │     Extraction (PyMuPDF)       │
          └────────────────┬───────────────┘
                           ↓
          ┌────────────────────────────────┐
          │  2. Hierarchical Chunking      │
          │     (Section-aware)             │
          └────────────────┬───────────────┘
                           ↓
                ┌──────────┴──────────┐
                ↓                     ↓
    ┌─────────────────────┐  ┌─────────────────────┐
    │ 3a. Section-Level   │  │ 3b. Chunk Embed →   │
    │     Summarization   │  │     Store in        │
    │     (Gemini)        │  │     Chroma          │
    └──────────┬──────────┘  └──────────┬──────────┘
               ↓                        ↓
    ┌─────────────────────┐  ┌─────────────────────┐
    │ 4. Bill-Level       │  │ 5. Retrieval        │
    │    Summary          │  │    on User Query    │
    │    (Meta-summary)   │  └──────────┬──────────┘
    └──────────┬──────────┘             ↓
               ↓             ┌─────────────────────┐
    ┌─────────────────────┐  │ 6. LLM Generates    │
    │ 7. Show Summary     │  │    Grounded Answer  │
    │    to User          │  │    with Citations   │
    └─────────────────────┘  └──────────┬──────────┘
                                        ↓
                             ┌─────────────────────┐
                             │ 8. Display to User  │
                             │    (Streamlit UI)   │
                             └─────────────────────┘


## Phase-by-Phase Implementation

### Phase 1: Setup & Data Collection (Week 1-2)

**Goal**: Environment ready, sample bills downloaded, project structure in place.

#### Tasks

1. Set up project repo on GitHub
2. Install dependencies:
```bash
   pip install google-generativeai chromadb streamlit pymupdf tiktoken tqdm python-dotenv
```
3. Get API keys:
   - Google AI Studio → Gemini API key (free)
   - Store in `.env` file
4. Download 3 sample bills as PDFs
5. Create directory structure:

billsense/
├── data/
│ ├── raw_pdfs/ # Downloaded bill PDFs
│ ├── extracted/ # Text extracted from PDFs
│ ├── chunks/ # Chunked sections
│ └── summaries/ # Generated summaries
├── src/
│ ├── ingestion.py # PDF → text
│ ├── chunking.py # Section-aware chunking
│ ├── summarize.py # Hierarchical summarization
│ ├── embed.py # Embedding + Chroma
│ ├── retrieve.py # RAG retrieval
│ └── generate.py # LLM answer generation
├── app/
│ └── streamlit_app.py # Web UI
├── tests/
├── .env
├── requirements.txt
└── README.md

#### Deliverables
- Working environment
- 3 bills downloaded
- Skeleton project on GitHub

### Phase 2: Ingestion & Chunking (Week 3-4)

**Goal**: Convert PDFs into structured, section-aware chunks.

#### Step 1: PDF text extraction

```python
# src/ingestion.py
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text = ""
    for page_num, page in enumerate(doc):
        text += f"\n=== PAGE {page_num + 1} ===\n"
        text += page.get_text()
    doc.close()
    return text
```

#### Step 2: Section-aware chunking

Bills have structure: Chapters, Sections, Sub-sections. Don't split randomly — respect the structure.

```python
# src/chunking.py
import re

def chunk_bill(text: str) -> list[dict]:
    # Match section headers like "1.", "2.", "Chapter 1", "Section 5"
    section_pattern = re.compile(
        r'^(?:Chapter\s+[IVX\d]+|Section\s+\d+|\d+\.\s+[A-Z])',
        re.MULTILINE
    )
    
    sections = section_pattern.split(text)
    chunks = []
    
    for i, section in enumerate(sections):
        if section.strip():
            chunks.append({
                'section_id': i,
                'content': section.strip(),
                'char_count': len(section),
                'word_count': len(section.split()),
            })
    
    return chunks
```

#### Step 3: Handle oversized sections

If a section is too big (> 4000 tokens), split further at paragraph boundaries.

```python
def split_oversized_chunk(chunk: dict, max_tokens: int = 4000) -> list[dict]:
    if chunk['word_count'] < max_tokens:
        return [chunk]
    
    # Split at paragraph breaks
    paragraphs = chunk['content'].split('\n\n')
    sub_chunks = []
    current = ""
    
    for para in paragraphs:
        if len(current) + len(para) > max_tokens * 4:  # rough char-to-token
            sub_chunks.append({**chunk, 'content': current})
            current = para
        else:
            current += "\n\n" + para
    
    if current:
        sub_chunks.append({**chunk, 'content': current})
    
    return sub_chunks
```

#### Deliverables
- Bills successfully parsed to text
- Section-aware chunks generated
- Chunk metadata saved to `data/chunks/`

### Phase 3: Hierarchical Summarization (Week 5-6)

**Goal**: Generate multi-level summaries — section-level, then bill-level meta-summary.

#### Step 1: Section-level summaries

```python
# src/summarize.py
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-pro')

SECTION_PROMPT = """
You are a legal analyst. Summarize this section of an Indian bill in plain 
language. Include:
- Purpose of this section
- Key obligations/rights created
- Any penalties or exceptions
- Preserve section numbers for citation

Section text:
{content}

Provide summary in Markdown format.
"""

def summarize_section(chunk: dict) -> str:
    response = model.generate_content(
        SECTION_PROMPT.format(content=chunk['content'])
    )
    return response.text
```

#### Step 2: Bill-level meta-summary

```python
BILL_PROMPT = """
You are a legal analyst. Below are section-level summaries of an Indian bill.
Create a hierarchical, plain-language document covering:

1. Executive Summary (2-3 paragraphs)
2. Key Provisions (bulleted list of major points)
3. Rights & Obligations (who gets what, who owes what)
4. Penalties & Enforcement
5. Notable Exceptions or Limitations

Section summaries:
{section_summaries}

Aim for ~15-20 pages of clear plain-language output.
"""

def summarize_bill(section_summaries: list[str]) -> str:
    combined = "\n\n---\n\n".join(section_summaries)
    response = model.generate_content(
        BILL_PROMPT.format(section_summaries=combined)
    )
    return response.text
```

#### Deliverables
- Section-level summaries per bill
- Bill-level meta-summaries
- Saved to `data/summaries/` as markdown

### Phase 4: Embeddings + Vector Store (Week 7)

**Goal**: Embed chunks, store in Chroma for retrieval.

```python
# src/embed.py
import chromadb
from chromadb.config import Settings
import google.generativeai as genai

def get_embedding(text: str) -> list[float]:
    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    return result['embedding']

def build_vector_store(chunks: list[dict], bill_name: str):
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(
        name=f"bill_{bill_name}",
        metadata={"hnsw:space": "cosine"}
    )
    
    for chunk in chunks:
        embedding = get_embedding(chunk['content'])
        collection.add(
            embeddings=[embedding],
            documents=[chunk['content']],
            metadatas=[{
                'section_id': chunk['section_id'],
                'bill_name': bill_name,
            }],
            ids=[f"{bill_name}_section_{chunk['section_id']}"]
        )
```

#### Deliverables
- Chroma vector store populated with all bill chunks
- Verify with a test similarity search

### Phase 5: RAG Retrieval + Q&A (Week 8-9)

**Goal**: Answer user queries with grounded citations.

```python
# src/retrieve.py + src/generate.py

def retrieve_relevant_chunks(query: str, bill_name: str, top_k: int = 5) -> list[dict]:
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(f"bill_{bill_name}")
    
    query_embedding = genai.embed_content(
        model="models/embedding-001",
        content=query,
        task_type="retrieval_query"
    )['embedding']
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    
    return [
        {
            'content': doc,
            'section_id': meta['section_id'],
            'distance': dist
        }
        for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )
    ]

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
```

#### Deliverables
- End-to-end query flow works
- Answers include section citations
- No hallucinated content

### Phase 6: Streamlit UI (Week 10)

**Goal**: Web app for bill browsing + Q&A.

```python
# app/streamlit_app.py
import streamlit as st

st.set_page_config(page_title="BillSense", layout="wide")
st.title("BillSense — Indian Bill Q&A")

# Sidebar: select bill
bill = st.sidebar.selectbox("Choose a bill:", [
    "Personal Data Protection Bill 2019",
    "Digital Personal Data Protection Act 2023",
    "Bharatiya Nyaya Sanhita 2023"
])

# Two tabs
tab1, tab2 = st.tabs(["📄 Summary", "❓ Ask a Question"])

with tab1:
    st.header(f"Summary: {bill}")
    with open(f"data/summaries/{bill}.md") as f:
        st.markdown(f.read())

with tab2:
    st.header("Ask about this bill")
    query = st.text_input("Your question:", placeholder="What are the penalties?")
    
    if query:
        with st.spinner("Searching..."):
            result = answer_query(query, bill)
        
        st.markdown("### Answer")
        st.markdown(result['answer'])
        
        st.markdown("### Sources")
        for src in result['sources']:
            with st.expander(f"Section {src['section_id']} (distance: {src['distance']:.3f})"):
                st.text(src['content'][:1000] + "...")
```

Run with:
```bash
streamlit run app/streamlit_app.py
```

#### Deliverables
- Working web app
- Summary view + Q&A view
- Deployable to Streamlit Cloud (free)

### Phase 7: Testing & Evaluation (Week 11)

**Goal**: Show the system works, measure quality.

#### Manual test set

Create 20-30 questions per bill with expected answers:|

Run through system, evaluate:
- Does it cite correct sections? (Precision)
- Does it retrieve all relevant sections? (Recall)
- Does it hallucinate? (Faithfulness)

#### Metrics to track

- **Citation accuracy**: % of answers with correct section citation
- **Recall**: % of relevant sections retrieved in top-5
- **Faithfulness**: % of answers grounded in retrieved context
- **User evaluation**: 5-point Likert on 10 test queries

Log results to a spreadsheet for defense presentation.

### Phase 8: Documentation & Defense (Week 12)

**Goal**: Ship documentation, prepare project defense.

#### README.md structure

```markdown
# BillSense — RAG-based Indian Bill Q&A System

Screenshot of app

## What it does
[2-sentence description]

## Demo
[Link to deployed app or video]

## Architecture
[Diagram]

## Setup
[Installation steps]

## Usage
[How to add new bills, run queries]

## Tech Stack
[Table of technologies used]

## Evaluation
[Metrics table]

## Author
[You]
```

#### Presentation slides

1. Problem statement (why bill comprehension matters)
2. Approach (RAG pipeline)
3. Architecture diagram
4. Live demo
5. Sample outputs (before/after: raw bill vs. summary)
6. Evaluation results
7. Challenges + lessons learned
8. Future work

#### Portfolio push

- Publish to GitHub with clean README
- Deploy demo to Streamlit Cloud (free)
- Write LinkedIn/Twitter post about it
- Add to resume with metrics

## Timeline Summary

| Phase | Week | Deliverable |
|---|---|---|
| 1: Setup | 1-2 | Environment + repo |
| 2: Ingestion | 3-4 | Chunks generated |
| 3: Summarization | 5-6 | Bill summaries |
| 4: Embeddings | 7 | Chroma populated |
| 5: RAG Q&A | 8-9 | Query system works |
| 6: UI | 10 | Streamlit app |
| 7: Testing | 11 | Evaluation results |
| 8: Docs | 12 | Ready to submit |

Total: **12 weeks (1 semester)**

## Cost Breakdown

| Item | Cost |
|---|---|
| Gemini API | $0 (free tier, 60 req/min) |
| Chroma | $0 (local) |
| Streamlit Cloud | $0 (free tier) |
| GitHub | $0 |
| Colab | $0 (free tier for testing) |
| Data (bills) | $0 (public) |
| **TOTAL** | **$0** |

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Gemini rate limits | Use Groq or OpenRouter as fallback |
| Chunks too large for embedding API | Split at paragraph level |
| Poor retrieval quality | Add re-ranking step, tune chunk size |
| Hallucinations | Strict system prompt, cite-only mode |
| PDF parsing failures | Manual review, fallback to text-based sources |

## Key Design Decisions

1. **Section-aware chunking > fixed-size**  
   Legal text has meaningful structure — respect it
   
2. **Hierarchical summarization > flat**  
   Section summaries → bill summary preserves granularity for citation
   
3. **Local Chroma > cloud vector DB**  
   Zero cost, easy setup, portable for demo
   
4. **Streamlit > custom web app**  
   Fast to build, recruiter-friendly, easy deployment
   
5. **Gemini > OpenAI**  
   Free tier, 1M-token context handles huge bills

## What to Emphasize in Your Project Defense

1. **Real-world problem** — millions of Indians affected by bills they never read
2. **Full RAG pipeline** — you've built end-to-end, not just a wrapper
3. **Zero-cost architecture** — you can build production-grade AI without money
4. **Measurable results** — evaluation metrics show it works
5. **Extensible design** — new bills can be added easily
6. **Production patterns** — hierarchical chunking, grounded citations, section-aware retrieval

## Comparison to MiAI Law (What Inspired This)

| Aspect | MiAI Law | BillSense |
|---|---|---|
| Domain | US legal cases | Indian bills |
| Scale | 3M+ documents | 3-10 documents |
| LLM | GPT-4 (paid) | Gemini (free) |
| Vector DB | Milvus | Chroma |
| Interface | Copilot plugin | Streamlit web app |
| Retrieval | Vector search | Vector search + citations |
| Summarization | Hierarchical (chunks → merge) | Same pattern |
| Cost | Enterprise-level | Free tier |

**Same fundamental architecture, different domain, scaled appropriately.**

## Next Steps

1. Lock in the 3 sample bills
2. Set up GitHub repo + environment
3. Follow Phase 1-2 tasks (Weeks 1-4)
4. Come back with questions when you hit specific implementation issues