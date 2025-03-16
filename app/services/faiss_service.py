import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict
import pickle
from pathlib import Path
from app.core.config import get_settings
from loguru import logger

settings = get_settings()

class FAISSService:
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.index = None
        self.documents: Dict[int, str] = {}
        self.initialize_index()

    def initialize_index(self):
        """Initialize or load existing FAISS index"""
        index_path = Path(settings.FAISS_INDEX_PATH)
        if index_path.exists():
            logger.info(f"Loading existing FAISS index from {index_path}")
            self.index = faiss.read_index(str(index_path))
            with open(str(index_path).replace('.faiss', '_docs.pkl'), 'rb') as f:
                self.documents = pickle.load(f)
        else:
            logger.info("Creating new FAISS index")
            embedding_dim = self.model.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatL2(embedding_dim)
            self._save_index()

    def add_documents(self, texts: List[str]) -> None:
        """Add new documents to the FAISS index"""
        if not texts:
            return

        embeddings = self.model.encode(texts, show_progress_bar=True)
        start_id = len(self.documents)
        
        for i, text in enumerate(texts):
            self.documents[start_id + i] = text
        
        self.index.add(np.array(embeddings))
        self._save_index()

    def hybrid_search(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """Perform hybrid search combining FAISS similarity and keyword matching"""
        # Get semantic search results
        query_vector = self.model.encode([query])[0]
        D, I = self.index.search(np.array([query_vector]), k)
        
        results = []
        for i, (distance, idx) in enumerate(zip(D[0], I[0])):
            if idx < 0 or idx >= len(self.documents):
                continue
            
            # Convert distance to similarity score (1 / (1 + distance))
            similarity_score = 1 / (1 + distance)
            document = self.documents[idx]
            
            # Simple keyword matching score
            keyword_score = self._calculate_keyword_score(query, document)
            
            # Combine scores (70% semantic, 30% keyword)
            final_score = (0.7 * similarity_score) + (0.3 * keyword_score)
            
            results.append((document, final_score))
        
        # Sort by final score
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def _calculate_keyword_score(self, query: str, document: str) -> float:
        """Calculate simple keyword matching score"""
        query_words = set(query.lower().split())
        doc_words = set(document.lower().split())
        matching_words = query_words.intersection(doc_words)
        return len(matching_words) / len(query_words) if query_words else 0.0

    def _save_index(self) -> None:
        """Save FAISS index and documents to disk"""
        index_path = Path(settings.FAISS_INDEX_PATH)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        
        faiss.write_index(self.index, str(index_path))
        with open(str(index_path).replace('.faiss', '_docs.pkl'), 'wb') as f:
            pickle.dump(self.documents, f)
        
        logger.info(f"Saved FAISS index with {len(self.documents)} documents")
