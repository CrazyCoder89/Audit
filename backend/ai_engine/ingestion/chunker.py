# This file takes the pages extracted by pdf_loader.py
# and splits them into smaller overlapping chunks.
# These chunks are what we will convert to vectors later.

import sys
import os

# This allows us to import config.py from the root folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CHUNK_SIZE, CHUNK_OVERLAP


def split_text_into_chunks(text: str, source: str, page_number: int) -> list[dict]:
    """
    Splits a single page's text into smaller overlapping chunks.

    Args:
        text        : the full text of one page
        source      : the filename this text came from
        page_number : which page this text is from

    Returns:
        A list of chunk dictionaries. Example:
        [
            {
                "chunk_id"   : "test.pdf_page1_chunk0",
                "text"       : "first 500 characters...",
                "source"     : "test.pdf",
                "page_number": 1
            },
            ...
        ]
    """

    chunks = []       # this will store all our chunks
    start  = 0        # starting position in the text
    chunk_index = 0   # to number each chunk

    # Keep slicing the text until we reach the end
    while start < len(text):

        # Get a slice of text from start to start + CHUNK_SIZE
        end = start + CHUNK_SIZE

        # Extract the chunk
        chunk_text = text[start:end]

        # Create a unique ID for this chunk
        chunk_id = f"{source}_page{page_number}_chunk{chunk_index}"

        # Store the chunk with its metadata
        chunk = {
            "chunk_id"   : chunk_id,
            "text"       : chunk_text.strip(),
            "source"     : source,
            "page_number": page_number
        }

        chunks.append(chunk)

        # Move start forward by CHUNK_SIZE minus CHUNK_OVERLAP
        # This creates the overlap between chunks
        start += CHUNK_SIZE - CHUNK_OVERLAP
        chunk_index += 1

    return chunks


def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Takes all pages from pdf_loader and chunks every single one.

    Args:
        pages: list of page dictionaries from pdf_loader.py

    Returns:
        A flat list of all chunks across all pages
    """

    all_chunks = []

    for page in pages:
        # Chunk this page's text
        page_chunks = split_text_into_chunks(
            text        = page["text"],
            source      = page["source"],
            page_number = page["page_number"]
        )

        # Add to our master list
        all_chunks.extend(page_chunks)

    print(f"Total chunks created: {len(all_chunks)}")
    return all_chunks


# --------------------------------------------------
# TEST: Run this file directly to test it
# --------------------------------------------------

if __name__ == "__main__":

    # First load the PDF using our pdf_loader
    from pdf_loader import load_pdf

    # Load our test PDF
    pages = load_pdf("data/raw/test.pdf")

    # Now chunk all the pages
    chunks = chunk_pages(pages)

    # Print first 2 chunks to verify
    print("\n--- Chunk Preview ---")
    for chunk in chunks[:2]:
        print(f"\nChunk ID   : {chunk['chunk_id']}")
        print(f"Source     : {chunk['source']}")
        print(f"Page Number: {chunk['page_number']}")
        print(f"Text       : {chunk['text'][:200]}")
        print(f"Length     : {len(chunk['text'])} characters")
        print("-" * 40)