# BillSense — Developer Handover Guide

> **For:** Nitish (second developer)
> **Project:** BillSense — RAG-based Indian Bill Summarization & Q&A System
> **Repo:** https://github.com/JaiprakashSahu/BillSense

---

## What is BillSense?

BillSense takes Indian government bills (PDFs, 10–600+ pages), extracts their text, chunks them into sections, generates plain-language summaries using an LLM, embeds the chunks into a shared vector database, and lets users ask questions about any bill with cited answers.

**Architecture:**

```
PDF Bill
  → PyMuPDF (text extraction)
  → Section-aware chunking (regex-based splitting + merging)
  → Embedding (sentence-transformers, local) → Qdrant Cloud (shared vector DB)
  → Summarization (Groq LLM) → Markdown files
  → FastAPI backend (serves Q&A + summaries)
  → Next.js + Tailwind frontend (sidebar with years → bills, Q&A tab, Summary tab)
```

**Tech stack:**

| Component | Technology |
|---|---|
| LLM | Groq API (qwen/qwen3.8-27b) — free tier |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) — runs locally |
| Vector DB | Qdrant Cloud — shared, free 1GB tier |
| Backend | FastAPI (Python) |
| Frontend | Next.js 15 + Tailwind CSS |
| PDF parsing | PyMuPDF |

---

## Prerequisites (install on your machine)

### 1. Python 3.9+
```bash
python3 --version  # Should be 3.9 or higher
```

### 2. Node.js 18+
```bash
node --version  # Should be 18 or higher
npm --version
```

### 3. Git
```bash
git --version
```

### 4. GitHub CLI
```bash
brew install gh  # macOS
# or: https://cli.github.com for other OS
gh auth login    # Login with your GitHub account
```

---

## Setup Steps

### Step 1: Clone the repo

```bash
git clone https://github.com/JaiprakashSahu/BillSense.git
cd BillSense
```

### Step 2: Switch to your branch

```bash
git checkout dev-nitish
git pull origin main  # Get latest from main
```

### Step 3: Install dependencies

```bash
# Python dependencies
pip3 install -r requirements.txt

# Frontend dependencies
cd frontend && npm install && cd ..
```

### Step 4: Create your `.env` file

Copy the example and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env` with these values:

```env
# Get free API key from https://console.groq.com/keys
# You can add multiple keys (different accounts) for rate limit rotation
GROQ_API_KEY=your_groq_key_here
GROQ_API_KEY_2=optional_second_key
GROQ_API_KEY_3=optional_third_key

# Shared Qdrant Cloud — SAME credentials for both developers
# Ask Jaiprakash for these values (they are shared)
QDRANT_URL=https://a35665e3-7ae8-4499-90cb-43539130e76b.sa-east-1-0.aws.cloud.qdrant.io
QDRANT_API_KEY=<ask Jaiprakash for this key>
```

**Important:**
- `GROQ_API_KEY` — create your OWN key(s) at https://console.groq.com (free, 200K tokens/day per key)
- `QDRANT_URL` and `QDRANT_API_KEY` — use the SAME values as Jaiprakash (shared DB)

### Step 5: Verify setup

```bash
# Test Groq
python3 -c "
from src.llm import get_client
c = get_client()
r = c.chat(messages=[{'role':'user','content':'Hi'}], max_tokens=5)
print('Groq OK:', r.choices[0].message.content)
"

# Test Qdrant
python3 -c "
from src.db import get_qdrant_client
client = get_qdrant_client()
collections = client.get_collections()
print(f'Qdrant OK: {len(collections.collections)} collections')
"
```

---

## Project Structure

```
BillSense/
├── data/
│   ├── raw_pdfs/            # Input bill PDFs (download from PRS India)
│   ├── extracted/           # Extracted text (generated)
│   ├── chunks/              # Chunked sections (generated)
│   └── summaries/           # Generated summaries (.md + _sections.json)
├── src/
│   ├── ingestion.py         # PDF → text extraction
│   ├── chunking.py          # Section-aware chunking + merging
│   ├── embed.py             # Embedding + Qdrant/Chroma storage
│   ├── retrieve.py          # RAG retrieval from vector DB
│   ├── generate.py          # LLM answer generation
│   ├── summarize.py         # Hierarchical summarization pipeline
│   ├── llm.py               # Groq client with API key rotation
│   └── db.py                # Vector DB client (Qdrant Cloud / local Chroma)
├── backend/
│   └── api.py               # FastAPI server (port 8000)
├── frontend/                # Next.js app (port 3000)
│   └── src/
│       ├── app/page.tsx      # Main page with sidebar layout
│       ├── components/rag/   # QueryForm, AnswerSection, SourcesSection, etc.
│       └── hooks/            # useRAGStream (SSE streaming)
├── chroma-server/           # Docker config for self-hosted Chroma (not used currently)
├── run_pipeline.py          # Full pipeline script
├── Makefile                 # All commands
├── setup.sh                 # First-time setup script
├── requirements.txt
└── .env.example
```

---

## Commands (Makefile)

```bash
make help          # Show all commands
make setup         # Install all dependencies
make pipeline      # Run full pipeline (extract → chunk → embed → summarize)
make extract       # Stage 1: PDF → text
make chunk         # Stage 2: text → section chunks
make embed         # Stage 3: chunks → Qdrant Cloud vectors
make summarize     # Stage 4: chunks → LLM summaries
make serve         # Start backend API (port 8000)
make frontend      # Start frontend dev server (port 3000)
make dev           # Start both backend + frontend
make clean         # Remove generated data (keeps PDFs)
```

---

## How to Add New Bills

1. Download the bill PDF from https://prsindia.org/billtrack
2. Name it descriptively: `Bill_Name_Year.pdf` (e.g., `Waqf_Amendment_Bill_2024.pdf`)
3. Place it in `data/raw_pdfs/`
4. Run:
   ```bash
   make pipeline
   ```
5. The bill automatically appears in the frontend sidebar under its year
6. No code changes needed — the system auto-detects new bills

**Source for PDFs:** PRS India — https://prsindia.org/billtrack (CC 4.0 license, free)

---

## How the Pipeline Works

### Stage 1: Extract (`src/ingestion.py`)
- Uses PyMuPDF to extract text from PDFs
- Saves `.txt` files and metadata JSON to `data/extracted/`

### Stage 2: Chunk (`src/chunking.py`)
- Regex-based splitting at CHAPTER, Section, numbered clause boundaries
- Filters out filler content (TOC, page numbers, dashes)
- Merges small chunks (min 500 words) to reduce API calls
- Splits oversized chunks (max 3000 words) at paragraph boundaries
- Saves JSON to `data/chunks/`

### Stage 3: Embed (`src/embed.py`)
- Uses `all-MiniLM-L6-v2` model (runs locally, no API needed)
- Generates 384-dimensional embeddings
- Stores in Qdrant Cloud (shared) or local Chroma (fallback)
- Both developers' embeddings go to the same Qdrant instance

### Stage 4: Summarize (`src/summarize.py`)
- Section-level: Each chunk → Groq LLM → bullet-point summary
- Bill-level: All section summaries → condensed in batches → final summary
- Saves progress after each chunk (resumable on failure)
- Uses concurrent workers (5) with API key rotation
- Skips bills that already have a `.md` summary file
- Rate limit handling: auto-rotates keys, waits and retries on exhaustion

---

## Shared Vector DB (Qdrant Cloud)

Both developers push embeddings to the same Qdrant Cloud instance. This means:

- When you embed a new bill, it's immediately available to the other developer
- The frontend Q&A reads from Qdrant, so both developers see all bills
- No need to sync local databases

**Current state:** 16 bills, 569 vectors across 8 years (2019–2026)

If you need to re-embed everything:
```bash
make embed
```

---

## API Key Rotation (Groq)

Groq free tier has limits:
- **200K tokens/day** per key
- **7K input tokens/minute** per key
- **30 requests/minute** per key

The system (`src/llm.py`) automatically:
- Rotates through all keys when one hits a rate limit
- Waits and retries when ALL keys are exhausted
- Each developer uses their OWN Groq keys (create multiple with different emails)

**Recommended:** Create 3–5 Groq API keys for smooth summarization.

---

## Git Workflow

### Branches
- `main` — stable, production-ready code
- `dev-jaiprakash` — Jaiprakash's development branch
- `dev-nitish` — Nitish's development branch

### Daily workflow

```bash
# 1. Start your day — pull latest main
git checkout dev-nitish
git pull origin main

# 2. Make your changes, commit
git add <files>
git commit -m "Add: description of change"

# 3. Push your branch
git push origin dev-nitish

# 4. When ready to merge — create a PR
gh pr create --base main --title "Your PR title" --body "Description"
```

### Rules
- Never push directly to `main`
- Always create PRs from your dev branch → main
- Review each other's PRs before merging
- Keep `.env` in `.gitignore` (never commit API keys)
- Generated data (`data/extracted/`, `data/chunks/`, `data/summaries/`, `chroma_db/`) is gitignored

---

## Running the App Locally

```bash
# Terminal 1: Backend
make serve
# → http://localhost:8000

# Terminal 2: Frontend
make frontend
# → http://localhost:3000

# Or both at once:
make dev
```

---

## Key Files to Know

| File | What it does |
|---|---|
| `src/llm.py` | Groq client with multi-key rotation |
| `src/db.py` | Vector DB client (Qdrant Cloud / local Chroma) |
| `src/summarize.py` | The heaviest pipeline stage — section + bill summarization |
| `backend/api.py` | FastAPI with `/api/bills`, `/api/query`, `/api/stream` endpoints |
| `frontend/src/app/page.tsx` | Main UI — sidebar + Q&A + summary tabs |
| `run_pipeline.py` | CLI entry point for the full pipeline |
| `Makefile` | All shortcut commands |

---

## Troubleshooting

### "Rate limit exceeded" errors
- Add more Groq API keys to `.env` (GROQ_API_KEY_2, GROQ_API_KEY_3, etc.)
- Wait for daily limit reset (~24 hours) or use fresh keys from new accounts
- The pipeline auto-saves progress — just re-run `make summarize`

### "Collection not found" errors
- The bill hasn't been embedded yet. Run `make embed`

### Frontend shows "No bills processed yet"
- Backend isn't running. Start it: `make serve`
- Or the backend has a cached import. Kill and restart: `pkill -f api.py && make serve`

### Summary tab shows "not available"
- The bill hasn't been summarized yet. Run `make summarize`
- Check `data/summaries/` for `.md` files

### Qdrant connection fails
- Check QDRANT_URL and QDRANT_API_KEY in `.env`
- Test: `python3 -c "from src.db import get_qdrant_client; get_qdrant_client()"`

---

## Contact

- **Jaiprakash Sahu** — https://github.com/JaiprakashSahu
- **Repo issues** — https://github.com/JaiprakashSahu/BillSense/issues
