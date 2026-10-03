import os
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def get_embedding(text: str) -> list[float]:
    """Get embedding vector for a text using Gemini."""
    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    return result['embedding']


def build_vector_store(chunks: list[dict], bill_name: str):
    """Embed chunks and store them in Chroma."""
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(
        name=f"bill_{bill_name}",
        metadata={"hnsw:space": "cosine"}
    )

    for chunk in chunks:
        embedding = get_embedding(chunk['content'])
        collection.add(
            embeddings=[embedding],
            documents=[chunk['content']],
            metadatas=[{
                'section_id': chunk['section_id'],
                'bill_name': bill_name,
            }],
            ids=[f"{bill_name}_section_{chunk['section_id']}"]
        )
