"""
BillSense Pipeline — Run all stages end-to-end.

Stages:
  1. Extract  — PDF → text
  2. Chunk    — text → section-aware chunks
  3. Embed    — chunks → Chroma vector store
  4. Summarize — chunks → section summaries → bill summary

Usage:
  python run_pipeline.py              # Run all stages
  python run_pipeline.py --stage 1    # Run only extraction
  python run_pipeline.py --stage 2    # Run only chunking
  python run_pipeline.py --stage 3    # Run only embedding
  python run_pipeline.py --stage 4    # Run only summarization
"""

import os
import sys
import argparse
import time

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "data", "raw_pdfs")
EXTRACTED_DIR = os.path.join(BASE_DIR, "data", "extracted")
CHUNKS_DIR = os.path.join(BASE_DIR, "data", "chunks")
SUMMARIES_DIR = os.path.join(BASE_DIR, "data", "summaries")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")


def stage_extract():
    """Stage 1: Extract text from PDFs."""
    print("\n" + "=" * 60)
    print("STAGE 1: PDF Extraction")
    print("=" * 60)

    from src.ingestion import extract_all_pdfs
    results = extract_all_pdfs(PDF_DIR, EXTRACTED_DIR)
    print(f"\n  Done! Extracted {len(results)} bills.")
    return results


def stage_chunk():
    """Stage 2: Chunk extracted texts."""
    print("\n" + "=" * 60)
    print("STAGE 2: Section-Aware Chunking")
    print("=" * 60)

    from src.chunking import chunk_all_bills
    all_chunks = chunk_all_bills(EXTRACTED_DIR, CHUNKS_DIR)
    total = sum(len(v) for v in all_chunks.values())
    print(f"\n  Done! Created {total} chunks across {len(all_chunks)} bills.")
    return all_chunks


def stage_embed():
    """Stage 3: Embed chunks into Chroma."""
    print("\n" + "=" * 60)
    print("STAGE 3: Embedding → Chroma Vector Store")
    print("=" * 60)

    from src.embed import embed_all_bills
    collections = embed_all_bills(CHUNKS_DIR, CHROMA_DIR)
    print(f"\n  Done! Created {len(collections)} collections in Chroma.")
    return collections


def stage_summarize():
    """Stage 4: Summarize bills."""
    print("\n" + "=" * 60)
    print("STAGE 4: Hierarchical Summarization")
    print("=" * 60)

    from src.summarize import summarize_all_bills
    summarize_all_bills(CHUNKS_DIR, SUMMARIES_DIR, rate_delay=4.0)
    print(f"\n  Done! Summaries saved to {SUMMARIES_DIR}")


def main():
    parser = argparse.ArgumentParser(description="BillSense Pipeline")
    parser.add_argument("--stage", type=int, choices=[1, 2, 3, 4],
                        help="Run a specific stage (1=extract, 2=chunk, 3=embed, 4=summarize)")
    args = parser.parse_args()

    start = time.time()

    print("\n" + "#" * 60)
    print("#  BillSense Pipeline")
    print("#" * 60)

    if args.stage is None or args.stage == 1:
        stage_extract()

    if args.stage is None or args.stage == 2:
        stage_chunk()

    if args.stage is None or args.stage == 3:
        stage_embed()

    if args.stage is None or args.stage == 4:
        stage_summarize()

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"Pipeline complete! Total time: {elapsed / 60:.1f} minutes")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
