# This is the bridge between the audit system and your RAG engine.
# It imports your existing RAG code and exposes two clean functions:
# 1. process_document() — indexes a PDF into FAISS
# 2. ask_document() — answers a question about a specific document

import sys
import os

# Add the ai_engine folder to Python path so we can import from it
# ai_engine is inside backend/ folder on Render
BACKEND_PATH = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BACKEND_PATH)

try:
    from ai_engine.embeddings.embeddings import embed_text, embed_chunks
    from ai_engine.ingestion.pdf_loader import load_pdf
    from ai_engine.ingestion.chunker import chunk_pages
    from ai_engine.retrieval.vector_store import VectorStore
    from ai_engine.rag.pipeline import generate_answer
    RAG_AVAILABLE = True
    print("[RAG] Available and ready")
except Exception as e:
    print(f"[RAG] Not available: {e}")
    RAG_AVAILABLE = False


"""from ingestion.pdf_loader import load_pdf
from ingestion.chunker import chunk_pages
from embeddings.embeddings import embed_chunks, embed_text
from retrieval.vector_store import VectorStore
from rag.pipeline import generate_answer"""

# Where we store per-document FAISS indexes
# Each document gets its own folder: vector_indexes/{document_id}/
VECTOR_INDEX_BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_indexes")
os.makedirs(VECTOR_INDEX_BASE, exist_ok=True)


def get_index_path(document_id: int) -> str:
    """Returns the folder path for a specific document's FAISS index."""
    path = os.path.join(VECTOR_INDEX_BASE, str(document_id))
    os.makedirs(path, exist_ok=True)
    return path


def process_document(file_path: str, document_id: int) -> dict:
    if not RAG_AVAILABLE:
        return {"status": "failed", "error": "RAG not available"}
    """
    Processes a PDF through the full RAG pipeline and saves the FAISS index.
    Called automatically when a document is uploaded.

    Args:
        file_path: path to the uploaded PDF on disk
        document_id: the DB id of the document

    Returns:
        dict with chunk_count and status
    """
    try:
        # Step 1: Extract text from PDF
        pages = load_pdf(file_path)
        if not pages:
            return {"status": "failed", "error": "Could not extract text from PDF"}

        # Step 2: Split into chunks
        chunks = chunk_pages(pages)

        # Step 3: Embed chunks
        embedded_chunks = embed_chunks(chunks)

        # Step 4: Build FAISS index and save it for this specific document
        vector_store = VectorStore()
        vector_store.add_chunks(embedded_chunks)

        # Override the save path to be per-document
        index_path = get_index_path(document_id)
        
        import faiss
        import pickle
        faiss.write_index(vector_store.index, os.path.join(index_path, "faiss.index"))
        with open(os.path.join(index_path, "chunks.pkl"), "wb") as f:
            pickle.dump(vector_store.chunks, f)

        return {
            "status": "success",
            "chunk_count": len(chunks),
            "page_count": len(pages)
        }

    except Exception as e:
        return {"status": "failed", "error": str(e)}


def ask_document(document_id: int, question: str) -> dict:
    if not RAG_AVAILABLE:
        return {"answer": "AI engine not available.", "sources": []}
    try:
        index_path = get_index_path(document_id)
        faiss_file = os.path.join(index_path, "faiss.index")
        chunks_file = os.path.join(index_path, "chunks.pkl")

        # If index missing — try to reprocess from uploaded file
        if not os.path.exists(faiss_file):
            print(f"[ASK] Index missing for doc {document_id}, attempting reprocess...")
            from database import SessionLocal
            from models.document import Document
            db = SessionLocal()
            try:
                doc = db.query(Document).filter(Document.id == document_id).first()
                if doc and os.path.exists(doc.file_path):
                    result = process_document(doc.file_path, document_id)
                    if result.get("status") != "success":
                        return {
                            "answer": "Document index was lost and reprocessing failed. Please re-upload the document.",
                            "sources": []
                        }
                else:
                    return {
                        "answer": "Document file not found on server. Please re-upload the document.",
                        "sources": []
                    }
            finally:
                db.close()

        import faiss
        import pickle
        import numpy as np
        from ai_engine.config import TOP_K_RESULTS

        index = faiss.read_index(faiss_file)
        with open(chunks_file, "rb") as f:
            chunks = pickle.load(f)

        query_embedding = embed_text(question)
        query_vector = np.array([query_embedding]).astype('float32')

        distances, indices = index.search(query_vector, TOP_K_RESULTS)

        retrieved_chunks = []
        for i, idx in enumerate(indices[0]):
            if idx < len(chunks):
                retrieved_chunks.append((chunks[idx], distances[0][i]))

        if not retrieved_chunks:
            return {
                "answer": "No relevant content found for your question.",
                "sources": []
            }

        result = generate_answer(question, retrieved_chunks)
        for source in result.get("sources", []):
            source["relevance"] = float(source["relevance"])

        return result

    except Exception as e:
        print(f"[ASK ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {
            "answer": f"Error: {str(e)}",
            "sources": []
        }
