# BillSense — RAG-based Indian Bill Q&A System

A Retrieval-Augmented Generation (RAG) system that takes long Indian government bills (200-300+ pages), produces plain-language hierarchical summaries, and answers natural-language questions with grounded citations.

## What it does

BillSense ingests Indian legislative bills as PDFs, breaks them into section-aware chunks, generates multi-level summaries, and enables users to ask questions about the bills — getting cited answers grounded in the actual text.

## Architecture

```
PDF Bill → PyMuPDF Extraction → Section-Aware Chunking
                                       ↓
                          ┌────────────┴────────────┐
                          ↓                         ↓
                 Hierarchical              Embed chunks →
                 Summarization             Store in Chroma
                 (Groq LLM)                      ↓
                          ↓              RAG Retrieval on
                 Bill-Level              User Query
                 Summary                        ↓
                          ↓              LLM Answer with
                 Display in              Citations
                 Next.js UI                    ↓
                                        Display in
                                        Next.js UI
```

## Tech Stack

| Component | Choice |
|---|---|
| LLM | Groq (Qwen 3.8 27B) — free tier |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) — local |
| Vector DB | Chroma (local) |
| Backend | FastAPI |
| Frontend | Next.js + Tailwind CSS |
| PDF Parsing | PyMuPDF |

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/JaiprakashSahu/BillSense.git
cd BillSense
chmod +x setup.sh && ./setup.sh

# 2. Add your API key
echo "GROQ_API_KEY=your_key_here" > .env

# 3. Place PDFs in data/raw_pdfs/ and run full pipeline
make pipeline

# 4. Start the app
make dev
# Open http://localhost:3000
```

## Commands

```bash
make help          # Show all commands
make setup         # Install all dependencies
make pipeline      # Run full pipeline (extract → chunk → embed → summarize)
make extract       # Stage 1 only: PDF → text
make chunk         # Stage 2 only: text → sections
make embed         # Stage 3 only: sections → Chroma
make summarize     # Stage 4 only: sections → summaries
make serve         # Start backend API (port 8000)
make frontend      # Start frontend (port 3000)
make dev           # Start both backend + frontend
make clean         # Remove generated data (keeps PDFs)
```

## Project Structure

```
BillSense/
├── backend/api.py           # FastAPI backend
├── frontend/                # Next.js frontend
├── src/
│   ├── ingestion.py         # PDF → text extraction
│   ├── chunking.py          # Section-aware chunking
│   ├── summarize.py         # Hierarchical summarization
│   ├── embed.py             # Local embeddings + Chroma
│   ├── retrieve.py          # RAG retrieval
│   └── generate.py          # LLM answer generation
├── data/
│   ├── raw_pdfs/            # Input PDFs
│   ├── extracted/           # Extracted text
│   ├── chunks/              # Chunked sections
│   └── summaries/           # Generated summaries
├── run_pipeline.py          # Full pipeline script
├── Makefile                 # All commands
└── setup.sh                 # First-time setup
```

## Sample Bills

- Personal Data Protection Bill 2019
- Digital Personal Data Protection Act 2023
- Bharatiya Nyaya Sanhita 2023

## Author

Jaiprakash Sahu
