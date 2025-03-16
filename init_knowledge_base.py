import os
from embeddings.embedding import EmbeddingHandler
from utils.logger import log_event

def load_knowledge_base():
    """Load and process all knowledge base text files."""
    kb_dir = "./knowledge_base"
    text_chunks = []
    
    try:
        # Verify knowledge base directory exists
        if not os.path.exists(kb_dir):
            raise FileNotFoundError(f"Knowledge base directory not found: {kb_dir}")
        
        # Read all text files from knowledge base directory
        for filename in sorted(os.listdir(kb_dir)):
            if filename.endswith(".txt"):
                with open(os.path.join(kb_dir, filename), 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Split content into smaller chunks (you can adjust the chunk size)
                    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                    text_chunks.extend(paragraphs)
        
        log_event(f"Loaded {len(text_chunks)} text chunks from knowledge base")
        return text_chunks
    
    except Exception as e:
        log_event(f"Error loading knowledge base: {str(e)}", level="ERROR")
        return []

def main():
    """Initialize FAISS index with knowledge base content."""
    try:
        # Create embeddings directory if it doesn't exist
        os.makedirs("./embeddings", exist_ok=True)
        
        # Load text chunks from knowledge base
        text_chunks = load_knowledge_base()
        if not text_chunks:
            log_event("No text chunks found. Exiting.", level="ERROR")
            return
        
        # Initialize embedding handler and add chunks to index
        embedder = EmbeddingHandler()
        embedder.add_to_index(text_chunks)
        log_event("Knowledge base initialization complete")
    except Exception as e:
        log_event(f"Error during initialization: {str(e)}", level="ERROR")
        raise

if __name__ == "__main__":
    main()
