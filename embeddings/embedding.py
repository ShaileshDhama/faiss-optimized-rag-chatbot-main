import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from config import FAISS_INDEX_PATH, FAISS_METADATA_PATH, EMBEDDING_MODEL
from utils.logger import log_event

class EmbeddingHandler:
    def __init__(self):
        """Initialize embedding model and FAISS index."""
        try:
            # Create embeddings directory if it doesn't exist
            os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
            
            self.model = SentenceTransformer(EMBEDDING_MODEL)
            self.index = faiss.IndexFlatL2(self.model.get_sentence_embedding_dimension())
            self.metadata = []

            # Load existing FAISS index if available
            if os.path.exists(FAISS_INDEX_PATH):
                self.index = faiss.read_index(FAISS_INDEX_PATH)
                with open(FAISS_METADATA_PATH, "rb") as f:
                    self.metadata = pickle.load(f)
                log_event("FAISS index loaded successfully.")
        except Exception as e:
            log_event(f"Error initializing embedding handler: {str(e)}", level="ERROR")
            raise

    def encode_text(self, text):
        """Convert text to embeddings."""
        return self.model.encode(text)

    def add_to_index(self, text_chunks):
        """Add new text chunks to FAISS index."""
        try:
            embeddings = [self.encode_text(chunk) for chunk in text_chunks]
            embeddings_array = np.array(embeddings).astype('float32')
            self.index.add(embeddings_array)
            self.metadata.extend(text_chunks)

            # Save updated index and metadata
            faiss.write_index(self.index, FAISS_INDEX_PATH)
            with open(FAISS_METADATA_PATH, "wb") as f:
                pickle.dump(self.metadata, f)
            log_event("New embeddings added to FAISS index.")
        except Exception as e:
            log_event(f"Error adding to index: {str(e)}", level="ERROR")
            raise

    def search(self, query, k=3):
        """Search for similar text chunks."""
        try:
            query_embedding = self.encode_text(query)
            query_embedding = np.array([query_embedding]).astype('float32')
            distances, indices = self.index.search(query_embedding, k)
            
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx != -1:  # FAISS returns -1 for empty slots
                    results.append((self.metadata[idx], float(dist)))
            return results
        except Exception as e:
            log_event(f"Error during search: {str(e)}", level="ERROR")
            return []

if __name__ == "__main__":
    embedder = EmbeddingHandler()
    embedder.add_to_index(["Sample financial data"])
