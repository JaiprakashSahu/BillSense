from src.embed import get_embedding
from src.db import get_chroma_client


def retrieve_relevant_chunks(query: str, bill_name: str, top_k: int = 5, db_path: str = "./chroma_db") -> list[dict]:
    """Retrieve the most relevant chunks for a query from Chroma (local or remote)."""
    client = get_chroma_client()

    # Sanitize collection name to match what was stored
    collection_name = "bill_" + bill_name.replace(" ", "_").replace(",", "").replace("(", "").replace(")", "")
    if len(collection_name) > 63:
        collection_name = collection_name[:63]

    collection = client.get_collection(collection_name)

    query_embedding = get_embedding(query)

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
