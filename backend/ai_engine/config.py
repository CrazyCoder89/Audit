# This file stores all the settings for our project.
# If we want to change something, we only change it in this one file.
from pathlib import Path

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

# BASE_DIR is the root folder of our project
# Path(__file__) means "the path of this file (config.py)"
# .resolve().parent means "go up one level to the folder containing it"
BASE_DIR = Path(__file__).resolve().parent

# Folder where the user puts their PDF files
RAW_DIR = BASE_DIR / "data" / "raw"

# Folder where we save processed text after reading PDFs
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Folder where we save the FAISS vector index
VECTOR_STORE_DIR = str(BASE_DIR / "data" / "vector_store")

# --------------------------------------------------
# TEXT CHUNKING SETTINGS
# --------------------------------------------------

# When we read a PDF, the text is very long.
# We split it into smaller pieces called "chunks".
# CHUNK_SIZE = how many characters in each chunk
CHUNK_SIZE = 500

# CHUNK_OVERLAP = how many characters are shared between
# two consecutive chunks (so we don't lose context at the edges)
CHUNK_OVERLAP = 50

# --------------------------------------------------
# EMBEDDING MODEL
# --------------------------------------------------

# This is the local AI model that converts text into numbers (vectors).
# We use a free HuggingFace model — no API key needed.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# The size of each vector this model produces
EMBEDDING_DIM = 384

# --------------------------------------------------
# LLM SETTINGS (the model that generates answers)
# --------------------------------------------------

# We use Ollama to run a local LLM (no API key needed)
LLM_MODEL = "mistral"

# Lower temperature = more factual answers (good for documents)
# Higher temperature = more creative answers
LLM_TEMPERATURE = 0.2

# --------------------------------------------------
# RETRIEVAL SETTINGS
# --------------------------------------------------

# How many chunks to retrieve from FAISS for each question
TOP_K_RESULTS = 5
