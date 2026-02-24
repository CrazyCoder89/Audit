# retrieval/vector_store.py
# This file manages the FAISS vector index.
# FAISS = Facebook AI Similarity Search - ultra-fast nearest neighbor search.
# We store all chunk embeddings here and can search them by similarity.

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import faiss
import numpy as np
import pickle
from pathlib import Path
from config import EMBEDDING_DIM, TOP_K_RESULTS, VECTOR_STORE_DIR


class VectorStore:
    """
    Manages FAISS index for storing and searching chunk embeddings.
    """

    def __init__(self):
        """Initialize empty FAISS index"""
        # IndexFlatL2 = exact search using L2 (Euclidean) distance
        # For semantic search, cosine similarity is better, but FAISS L2 works well
        self.index = faiss.IndexFlatL2(EMBEDDING_DIM)
        
        # This will store our chunk metadata (text, source, page number)
        self.chunks = []
        
        print(f"Initialized FAISS index (dimension: {EMBEDDING_DIM})")

    def add_chunks(self, chunks_with_embeddings: list[dict]):
        """
        Add chunks and their embeddings to the FAISS index.

        Args:
            chunks_with_embeddings: list of chunk dicts with 'embedding' key
        """
        print(f"\nAdding {len(chunks_with_embeddings)} chunks to FAISS index...")

        # Extract just the embeddings as a numpy array
        embeddings = np.array([chunk["embedding"] for chunk in chunks_with_embeddings])
        
        # Make sure embeddings are float32 (FAISS requirement)
        embeddings = embeddings.astype('float32')

        # Add to FAISS index
        self.index.add(embeddings)

        # Store the full chunk data (we need this to show results later)
        self.chunks.extend(chunks_with_embeddings)

        print(f"✓ Index now contains {self.index.ntotal} vectors")

    def search(self, query_embedding, k=TOP_K_RESULTS):
        """
        Search for the top-k most similar chunks to a query.

        Args:
            query_embedding: the embedded query (384-dim vector)
            k: how many results to return

        Returns:
            List of (chunk, distance) tuples, ordered by relevance
        """
        # Make sure query is the right shape and type
        query_vector = np.array([query_embedding]).astype('float32')

        # Search the index
        # distances = how far each result is (lower = more similar)
        # indices = which chunks matched
        distances, indices = self.index.search(query_vector, k)

        # Build results list
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.chunks):  # safety check
                chunk = self.chunks[idx]
                distance = distances[0][i]
                results.append((chunk, distance))

        print(f"\nFound {len(results)} relevant chunks")
        return results

    def save_to_disk(self):
        """
        Save the FAISS index and chunk metadata to disk.
        This way we don't have to rebuild it every time.
        """
        # Create directory if it doesn't exist
        os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

        # Save FAISS index
        index_path = os.path.join(VECTOR_STORE_DIR, "faiss.index")
        faiss.write_index(self.index, index_path)

        # Save chunk metadata using pickle
        chunks_path = os.path.join(VECTOR_STORE_DIR, "chunks.pkl")
        with open(chunks_path, "wb") as f:
            pickle.dump(self.chunks, f)

        print(f"\n✓ Saved index to {VECTOR_STORE_DIR}")

    def load_from_disk(self):
        """
        Load a previously saved FAISS index from disk.
        """
        index_path = os.path.join(VECTOR_STORE_DIR, "faiss.index")
        chunks_path = os.path.join(VECTOR_STORE_DIR, "chunks.pkl")

        if not os.path.exists(index_path) or not os.path.exists(chunks_path):
            print("No saved index found. Starting fresh.")
            return False

        # Load FAISS index
        self.index = faiss.read_index(index_path)

        # Load chunk metadata
        with open(chunks_path, "rb") as f:
            self.chunks = pickle.load(f)

        print(f"✓ Loaded index with {self.index.ntotal} vectors from disk")
        return True


# --------------------------------------------------
# TEST: Run this file directly to test it
# --------------------------------------------------

if __name__ == "__main__":

    # Import our previous components
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ingestion'))
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'embeddings'))
    
    from pdf_loader import load_pdf
    from chunker import chunk_pages
    from embeddings import embed_chunks, embed_text

    # Step 1-3: Load, chunk, and embed
    pages = load_pdf("data/raw/test.pdf")
    chunks = chunk_pages(pages)
    embedded_chunks = embed_chunks(chunks)

    # Step 4: Build FAISS index
    vector_store = VectorStore()
    vector_store.add_chunks(embedded_chunks)

    # Step 5: Test search with a query
    print("\n" + "="*50)
    print("TESTING SEARCH")
    print("="*50)

    test_query = "What is machine learning?"
    print(f"\nQuery: '{test_query}'")

    # Embed the query
    query_embedding = embed_text(test_query)

    # Search
    results = vector_store.search(query_embedding, k=2)

    # Show results
    for i, (chunk, distance) in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(f"Chunk ID : {chunk['chunk_id']}")
        print(f"Source   : {chunk['source']} (Page {chunk['page_number']})")
        print(f"Distance : {distance:.4f}")
        print(f"Text     : {chunk['text'][:150]}...")

    # Step 6: Save to disk for later
    vector_store.save_to_disk()
