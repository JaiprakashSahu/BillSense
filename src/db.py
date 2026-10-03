"""Vector DB client — supports Qdrant Cloud (shared) and local Chroma (fallback).

Set QDRANT_URL + QDRANT_API_KEY in .env for shared cloud mode.
Leave empty for local Chroma fallback.
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

_qdrant_client = None
_chroma_client = None


def is_qdrant_enabled():
    return bool(os.getenv("QDRANT_URL", "").strip())


def get_qdrant_client():
    global _qdrant_client
    if _qdrant_client is None:
        from qdrant_client import QdrantClient
        url = os.getenv("QDRANT_URL", "").strip()
        api_key = os.getenv("QDRANT_API_KEY", "").strip()
        _qdrant_client = QdrantClient(url=url, api_key=api_key, check_compatibility=False)
        print(f"    Connected to Qdrant Cloud")
    return _qdrant_client


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        db_path = os.getenv("CHROMA_PATH", "./chroma_db")
        _chroma_client = chromadb.PersistentClient(path=db_path)
    return _chroma_client


def sanitize_collection_name(bill_name: str) -> str:
    """Sanitize bill name into a valid collection name."""
    name = "bill_" + bill_name.replace(" ", "_").replace(",", "").replace("(", "").replace(")", "")
    if len(name) > 63:
        name = name[:63]
    return name
