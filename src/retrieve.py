import chromadb
import google.generativeai as genai


def retrieve_relevant_chunks(query: str, bill_name: str, top_k: int = 5) -> list[dict]:
    """Retrieve the most relevant chunks for a query from Chroma."""
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
