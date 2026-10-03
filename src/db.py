"""Chroma DB client — supports both local and remote (shared) modes.

Set CHROMA_URL in .env for remote mode:
  CHROMA_URL=https://your-chroma-server.onrender.com

Leave empty for local mode (./chroma_db).
"""

import os
import chromadb
from dotenv import load_dotenv

load_dotenv(override=True)

_client = None


def get_chroma_client():
    """Get Chroma client — remote if CHROMA_URL is set, local otherwise."""
    global _client
    if _client is not None:
        return _client

    chroma_url = os.getenv("CHROMA_URL", "").strip()

    if chroma_url:
        # Remote shared Chroma server
        print(f"    Connecting to remote Chroma: {chroma_url}")
        _client = chromadb.HttpClient(host=chroma_url.rstrip("/"))
    else:
        # Local Chroma
        db_path = os.getenv("CHROMA_PATH", "./chroma_db")
        _client = chromadb.PersistentClient(path=db_path)

    return _client
