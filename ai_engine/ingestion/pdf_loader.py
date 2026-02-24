# This file is responsible for reading PDF files and extracting text from them.
# We use a library called PyMuPDF (imported as fitz) to do this.
# For each page in the PDF, we extract the text and store it with metadata.

import fitz  # this is PyMuPDF
import os    # to work with file paths

def load_pdf(file_path: str) -> list[dict]:
    """
    Reads a PDF file and extracts text page by page.

    Args:
        file_path: the full path to the PDF file

    Returns:
        A list of dictionaries. Each dictionary = one page.
        Example:
        [
            {
                "page_number": 1,
                "text": "This is the content of page 1...",
                "source": "my_document.pdf"
            },
            ...
        ]
    """

    # Check if the file actually exists before trying to open it
    if not os.path.exists(file_path):
        print(f"Error: File not found → {file_path}")
        return []

    # This will hold all our extracted pages
    pages = []

    # Get just the filename (e.g. "report.pdf") from the full path
    file_name = os.path.basename(file_path)

    print(f"Opening PDF: {file_name}")

    # Open the PDF using PyMuPDF
    # 'with' means it will automatically close the file when done
    with fitz.open(file_path) as pdf:

        total_pages = len(pdf)
        print(f"Total pages found: {total_pages}")

        # Loop through every page in the PDF
        for page_index in range(total_pages):

            # Get the page object (page_index starts from 0)
            page = pdf[page_index]

            # Extract all the text from this page
            text = page.get_text()

            # Sometimes pages are empty (like blank pages or image-only pages)
            # We skip those
            if text.strip() == "":
                print(f"  Page {page_index + 1}: empty, skipping...")
                continue

            # Create a dictionary for this page with all useful info
            page_data = {
                "page_number": page_index + 1,  # humans count from 1
                "text": text.strip(),            # remove extra whitespace
                "source": file_name              # which file this came from
            }

            # Add this page to our list
            pages.append(page_data)

            print(f"  Page {page_index + 1}: extracted {len(text)} characters")

    print(f"\nDone! Extracted {len(pages)} pages from {file_name}")
    return pages

# --------------------------------------------------
# TEST: Run this file directly to test it
# --------------------------------------------------
# When you run this file directly (not imported),
# this block runs automatically so you can test it.

if __name__ == "__main__":

    # Change this to any PDF file you have on your computer
    test_file = "data/raw/test.pdf"

    # Run the loader
    result = load_pdf(test_file)

    # Print the first page result to check it worked
    if result:
        print("\n--- First Page Preview ---")
        print(f"Source   : {result[0]['source']}")
        print(f"Page No  : {result[0]['page_number']}")
        print(f"Text Preview : {result[0]['text'][:300]}")