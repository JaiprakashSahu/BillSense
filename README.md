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
                 (Gemini)                        ↓
                          ↓              RAG Retrieval on
                 Bill-Level              User Query
                 Summary                        ↓
                          ↓              LLM Answer with
                 Display in              Citations
                 Streamlit                      ↓
                                        Display in
                                        Streamlit
```

## Tech Stack

| Component | Choice |
|---|---|
| LLM | Google Gemini 1.5 Pro (free tier) |
| Embeddings | Gemini embedding-001 |
| Vector DB | Chroma (local) |
| Web UI | Streamlit |
| PDF Parsing | PyMuPDF |

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/JaiprakashSahu/BillSense.git
   cd BillSense
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your Gemini API key
   ```

5. Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Usage

1. Place bill PDFs in `data/raw_pdfs/`
2. Run the Streamlit app:
   ```bash
   streamlit run app/streamlit_app.py
   ```

## Sample Bills

- Personal Data Protection Bill 2019
- Digital Personal Data Protection Act 2023
- Bharatiya Nyaya Sanhita 2023

## Author

Jaiprakash Sahu
