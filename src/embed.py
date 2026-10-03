import os
import json
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from src.db import is_qdrant_enabled, get_qdrant_client, get_chroma_client, sanitize_collection_name

_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print("    Loading embedding model (first time only)...")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def get_embedding(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text, show_progress_bar=False).tolist()


def build_vector_store(chunks: list[dict], bill_name: str, db_path: str = "./chroma_db"):
    """Embed chunks and store in Qdrant Cloud (if configured) or local Chroma."""
    collection_name = sanitize_collection_name(bill_name)
    model = get_embedding_model()

    # Batch embed
    texts = [chunk['content'][:5000] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32).tolist()

    if is_qdrant_enabled():
        _store_qdrant(chunks, embeddings, bill_name, collection_name)
    else:
        _store_chroma(chunks, embeddings, bill_name, collection_name)

    return collection_name


def _store_qdrant(chunks, embeddings, bill_name, collection_name):
    from qdrant_client.models import Distance, VectorParams, PointStruct

    client = get_qdrant_client()
    vector_size = len(embeddings[0])

    # Recreate collection
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )

    # Upload points
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        points.append(PointStruct(
            id=i,
            vector=embedding,
            payload={
                'content': chunk['content'],
                'chunk_id': chunk['chunk_id'],
                'section_header': chunk.get('section_header', ''),
                'bill_name': bill_name,
                'word_count': chunk['word_count'],
            }
        ))

    # Upload in batches of 100
    for i in range(0, len(points), 100):
        client.upsert(collection_name=collection_name, points=points[i:i+100])


def _store_chroma(chunks, embeddings, bill_name, collection_name):
    client = get_chroma_client()

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        collection.add(
            embeddings=[embedding],
            documents=[chunk['content']],
            metadatas=[{
                'chunk_id': chunk['chunk_id'],
                'section_header': chunk.get('section_header', ''),
                'bill_name': bill_name,
                'word_count': chunk['word_count'],
            }],
            ids=[f"{bill_name}_chunk_{chunk['chunk_id']}"]
        )


def embed_all_bills(chunks_dir: str, db_path: str = "./chroma_db") -> dict[str, str]:
    bill_collections = {}

    for fname in sorted(os.listdir(chunks_dir)):
        if not fname.endswith('_chunks.json'):
            continue

        bill_name = fname.replace('_chunks.json', '')
        chunks_path = os.path.join(chunks_dir, fname)

        with open(chunks_path, 'r') as f:
            chunks = json.load(f)

        print(f"\n  Embedding: {bill_name} ({len(chunks)} chunks)")
        collection_name = build_vector_store(chunks, bill_name, db_path)
        bill_collections[bill_name] = collection_name
        print(f"    → Stored in collection: {collection_name}")

    return bill_collections
