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
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
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
    Generate an answer using Groq LLM based on retrieved chunks.
    """
    if not retrieved_chunks:
        return {
            "answer": "No relevant information found in the document.",
            "sources": []
        }

    # Build context from retrieved chunks
    context_parts = []
    sources = []

    for i, (chunk, score) in enumerate(retrieved_chunks):
        context_parts.append(
            f"[Source {i+1}] Page {chunk.get('page_number', '?')}:\n{chunk['text']}"
        )
        sources.append({
            "source": chunk.get("source", "document"),
            "page": chunk.get("page_number", 0),
            "relevance": float(1 / (1 + score)) if score else 0.9,
            "text_preview": chunk["text"][:150]
        })

    context = "\n\n".join(context_parts)

    prompt = f"""You are an expert compliance and audit assistant. 
Answer the question based ONLY on the provided document context.
If the answer is not in the context, say so clearly.

DOCUMENT CONTEXT:
{context}

QUESTION: {question}

Provide a clear, accurate, and professional answer based on the document."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1024
        )
        answer = response.choices[0].message.content
        return {"answer": answer, "sources": sources}
    except Exception as e:
        return {
            "answer": f"Error generating answer: {str(e)}",
            "sources": sources
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