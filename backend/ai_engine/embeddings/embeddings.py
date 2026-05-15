# embeddings/embedder.py
# This file converts text chunks into vectors (embeddings).
# We use a free local model from HuggingFace called all-MiniLM-L6-v2.
# No API key needed — it runs 100% on your machine.

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL

# Load the embedding model once when this file is imported.
# First time it runs, it will download the model (~90MB).
# After that it loads from cache instantly.
print(f"Loading embedding model: {EMBEDDING_MODEL}")
model = SentenceTransformer(EMBEDDING_MODEL)
print("Model loaded successfully!")


def embed_text(text: str):
    """
    Converts a single piece of text into a vector.

    Args:
        text: any string you want to embed

    Returns:
        A numpy array of 384 numbers representing the meaning of the text
    """
    vector = model.encode(text)
    return vector


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Takes all our chunks and adds an embedding to each one.

    Args:
        chunks: list of chunk dictionaries from chunker.py

    Returns:
        Same list of chunks but with an extra "embedding" key added
    """

    print(f"Embedding {len(chunks)} chunks...")

    # Extract just the text from each chunk for batch processing
    texts = [chunk["text"] for chunk in chunks]

    # Embed all texts at once (faster than one by one)
    # show_progress_bar shows a nice loading bar in terminal
    embeddings = model.encode(texts, show_progress_bar=True)

    # Add the embedding back into each chunk dictionary
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i]

    print(f"Done! Each chunk now has a vector of {len(embeddings[0])} numbers")
    return chunks


# --------------------------------------------------
# TEST: Run this file directly to test it
# --------------------------------------------------

if __name__ == "__main__":

    # Import our previous steps
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ingestion'))
    from pdf_loader import load_pdf
    from chunker import chunk_pages

    # Step 1: Load PDF
    pages = load_pdf("data/raw/test.pdf")

    # Step 2: Chunk pages
    chunks = chunk_pages(pages)

    # Step 3: Embed chunks
    embedded_chunks = embed_chunks(chunks)

    # Preview the result
    print("\n--- Embedding Preview ---")
    first_chunk = embedded_chunks[0]
    print(f"Chunk ID  : {first_chunk['chunk_id']}")
    print(f"Text      : {first_chunk['text'][:100]}")
    print(f"Embedding shape : {first_chunk['embedding'].shape}")
    print(f"First 5 numbers : {first_chunk['embedding'][:5]}")