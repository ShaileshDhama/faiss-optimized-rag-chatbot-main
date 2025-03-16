import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# FAISS Configuration
FAISS_INDEX_PATH = "./embeddings/faiss_index.bin"
FAISS_METADATA_PATH = "./embeddings/metadata.pkl"

# Model Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "llama2"  # Changed to a valid Ollama model name

# API Keys (Optional for real-time data)
ALPHA_VANTAGE_API = os.getenv("ALPHA_VANTAGE_API")
