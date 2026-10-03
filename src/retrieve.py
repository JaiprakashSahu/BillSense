from src.embed import get_embedding
from src.db import is_qdrant_enabled, get_qdrant_client, get_chroma_client, sanitize_collection_name


def retrieve_relevant_chunks(query: str, bill_name: str, top_k: int = 5, db_path: str = "./chroma_db") -> list[dict]:
    """Retrieve most relevant chunks from Qdrant Cloud or local Chroma."""
    collection_name = sanitize_collection_name(bill_name)
    query_embedding = get_embedding(query)

    if is_qdrant_enabled():
        return _retrieve_qdrant(query_embedding, collection_name, top_k)
    else:
        return _retrieve_chroma(query_embedding, collection_name, top_k)


def _retrieve_qdrant(query_embedding, collection_name, top_k):
    client = get_qdrant_client()

    results = client.query_points(
        collection_name=collection_name,
        query=query_embedding,
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            'content': point.payload.get('content', ''),
            'section_header': point.payload.get('section_header', ''),
            'chunk_id': point.payload.get('chunk_id', ''),
            'distance': 1 - point.score,  # Convert similarity to distance
        }
        for point in results.points
    ]


def _retrieve_chroma(query_embedding, collection_name, top_k):
    client = get_chroma_client()
    collection = client.get_collection(collection_name)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return [
        {
            'content': doc,
            'section_header': meta.get('section_header', ''),
            'chunk_id': meta.get('chunk_id', ''),
            'distance': dist
        }
        for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )
    ]
