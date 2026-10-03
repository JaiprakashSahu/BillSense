import os
import json
import chromadb
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

# Local embedding model — no API key needed
_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print("    Loading embedding model (first time only)...")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def get_embedding(text: str) -> list[float]:
    """Get embedding vector using local sentence-transformers model."""
    model = get_embedding_model()
    return model.encode(text, show_progress_bar=False).tolist()


def build_vector_store(chunks: list[dict], bill_name: str, db_path: str = "./chroma_db"):
    """Embed chunks and store them in Chroma."""
    client = chromadb.PersistentClient(path=db_path)

    # Sanitize collection name
    collection_name = "bill_" + bill_name.replace(" ", "_").replace(",", "").replace("(", "").replace(")", "")
    if len(collection_name) > 63:
        collection_name = collection_name[:63]

    # Delete existing collection if it exists to avoid duplicates
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    model = get_embedding_model()

    # Batch embed for speed
    texts = [chunk['content'][:5000] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32).tolist()

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

    return collection_name


def embed_all_bills(chunks_dir: str, db_path: str = "./chroma_db") -> dict[str, str]:
    """Embed all chunked bills and store in Chroma. Returns mapping of bill_name -> collection_name."""
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

    # Save collection mapping
    mapping_path = os.path.join(db_path, "bill_collections.json")
    os.makedirs(db_path, exist_ok=True)
    with open(mapping_path, 'w') as f:
        json.dump(bill_collections, f, indent=2)

    return bill_collections
