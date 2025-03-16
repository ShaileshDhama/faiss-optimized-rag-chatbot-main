import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from config import FAISS_INDEX_PATH, FAISS_METADATA_PATH, EMBEDDING_MODEL

class FinanceRetriever:
    def __init__(self):
        """Load FAISS index and embeddings model."""
        self.index = faiss.read_index(FAISS_INDEX_PATH)
        with open(FAISS_METADATA_PATH, "rb") as f:
            self.metadata = pickle.load(f)
        self.model = SentenceTransformer(EMBEDDING_MODEL)

    def retrieve(self, query, top_k=5):
        """Finds top K relevant chunks for a given query."""
        query_embedding = np.array([self.model.encode(query)], dtype=np.float32)
        distances, indices = self.index.search(query_embedding, top_k)
        results = [(self.metadata[idx], distances[0][i]) for i, idx in enumerate(indices[0])]
        return results

if __name__ == "__main__":
    retriever = FinanceRetriever()
    query = "What are the key risk management strategies in hedge funds?"
    print(f"🔎 Query: {query}")
    print("📚 Relevant Chunks:")
    for doc, score in retriever.retrieve(query):
        print(f"  - {doc} (Similarity: {score:.4f})")
