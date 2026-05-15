# This is the RAG (Retrieval-Augmented Generation) pipeline.
# It combines retrieval from FAISS with generation from the LLM.
# When a user asks a question:
# 1. Embed the question
# 2. Search FAISS for relevant chunks
# 3. Send chunks + question to LLM
# 4. LLM generates an answer based on the retrieved context

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ollama
from config import LLM_MODEL, LLM_TEMPERATURE, TOP_K_RESULTS


def build_context(retrieved_chunks: list) -> str:
    """
    Takes the retrieved chunks and formats them into a context string.
    
    Args:
        retrieved_chunks: list of (chunk, distance) tuples from vector_store
        
    Returns:
        Formatted context string with sources
    """
    context_parts = []
    
    for i, (chunk, distance) in enumerate(retrieved_chunks, 1):
        source_info = f"[Source: {chunk['source']}, Page {chunk['page_number']}]"
        chunk_text = chunk['text']
        
        context_parts.append(f"Chunk {i} {source_info}:\n{chunk_text}\n")
    
    return "\n".join(context_parts)

def create_prompt(question: str, context: str) -> str:
    """
    Creates the full prompt for the LLM with instructions.
    
    Args:
        question: user's question
        context: retrieved document chunks
        
    Returns:
        Complete prompt string
    """
    prompt = f"""You are a helpful AI assistant that answers questions based on the provided document context.

IMPORTANT INSTRUCTIONS:
- Only use information from the context below to answer the question
- If the answer is not in the context, say "I cannot find this information in the provided documents"
- Always cite which source and page number you got the information from
- Be concise and accurate

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
    
    return prompt


def generate_answer(question: str, retrieved_chunks: list) -> dict:
    """
    Main RAG function - generates an answer using retrieved context.
    
    Args:
        question: user's question
        retrieved_chunks: list of (chunk, distance) tuples from FAISS
        
    Returns:
        Dictionary with answer and sources
    """
    print(f"\nGenerating answer for: '{question}'")
    
    # Build context from retrieved chunks
    context = build_context(retrieved_chunks)
    
    # Create the full prompt
    prompt = create_prompt(question, context)
    
    print("\n--- Calling LLM ---")
    
    # Call Ollama API
    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ],
        options={
            'temperature': LLM_TEMPERATURE,
        }
    )
    
    # Extract the answer
    answer = response['message']['content']
    
    # Extract sources from retrieved chunks
    sources = []
    for chunk, distance in retrieved_chunks:
        source_info = {
            'source': chunk['source'],
            'page': chunk['page_number'],
            'relevance': round(1 / (1 + distance), 2)  # Convert distance to relevance score
        }
        if source_info not in sources:
            sources.append(source_info)
    
    return {
        'answer': answer,
        'sources': sources
    }

# --------------------------------------------------
# TEST: Full end-to-end RAG pipeline
# --------------------------------------------------

if __name__ == "__main__":
    
    # Import all our previous components
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ingestion'))
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'embeddings'))
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'retrieval'))
    
    from pdf_loader import load_pdf
    from chunker import chunk_pages
    from embeddings import embed_chunks, embed_text
    from vector_store import VectorStore
    
    print("="*60)
    print("FULL RAG PIPELINE TEST")
    print("="*60)
    
    # Step 1-3: Load, chunk, embed
    print("\n[1/5] Loading and processing PDF...")
    pages = load_pdf("data/raw/test.pdf")
    chunks = chunk_pages(pages)
    embedded_chunks = embed_chunks(chunks)
    
    # Step 4: Build FAISS index
    print("\n[2/5] Building vector store...")
    vector_store = VectorStore()
    vector_store.add_chunks(embedded_chunks)
    
    # Step 5: Ask a question
    question = "What is RAG and how does it work?"
    print(f"\n[3/5] Question: '{question}'")
    
    # Step 6: Retrieve relevant chunks
    print("\n[4/5] Retrieving relevant chunks...")
    query_embedding = embed_text(question)
    retrieved_chunks = vector_store.search(query_embedding, k=TOP_K_RESULTS)
    
    print(f"Retrieved {len(retrieved_chunks)} chunks:")
    for i, (chunk, distance) in enumerate(retrieved_chunks, 1):
        print(f"  {i}. {chunk['source']} (Page {chunk['page_number']}) - Distance: {distance:.4f}")
    
    # Step 7: Generate answer
    print("\n[5/5] Generating answer with LLM...")
    result = generate_answer(question, retrieved_chunks)
    
    # Display result
    print("\n" + "="*60)
    print("FINAL ANSWER")
    print("="*60)
    print(result['answer'])
    print("\n" + "="*60)
    print("SOURCES")
    print("="*60)
    for source in result['sources']:
        print(f"• {source['source']} (Page {source['page']}) - Relevance: {source['relevance']}")