import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from embeddings.embedding import EmbeddingHandler
from utils.logger import log_event

class HybridRetriever:
    """
    Implements a hybrid retrieval system combining dense embeddings (FAISS) with 
    sparse retrieval (BM25) for more robust information retrieval.
    """
    
    def __init__(self, embedding_handler=None):
        """Initialize hybrid retriever with both vector and sparse search capabilities."""
        self.embedding_handler = embedding_handler or EmbeddingHandler()
        self.bm25 = None
        self.corpus = None
        self.initialize_sparse_index()
        log_event("Hybrid retriever initialized with dense and sparse capabilities")
    
    def initialize_sparse_index(self):
        """Initialize the BM25 sparse index using the same corpus as FAISS."""
        try:
            # Use the same corpus as the FAISS index
            self.corpus = self.embedding_handler.metadata
            
            # Tokenize documents
            tokenized_corpus = [doc.lower().split() for doc in self.corpus]
            
            # Create BM25 index
            self.bm25 = BM25Okapi(tokenized_corpus)
            log_event(f"Sparse index initialized with {len(self.corpus)} documents")
        except Exception as e:
            log_event(f"Error initializing sparse index: {str(e)}", level="ERROR")
            raise
    
    def dense_search(self, query, k=5):
        """Search using dense embeddings via FAISS."""
        try:
            results = self.embedding_handler.search(query, k=k)
            return results
        except Exception as e:
            log_event(f"Error in dense search: {str(e)}", level="ERROR")
            return []
    
    def sparse_search(self, query, k=5):
        """Search using sparse retrieval via BM25."""
        try:
            query_tokens = query.lower().split()
            scores = self.bm25.get_scores(query_tokens)
            
            # Get top-k document indices
            top_indices = np.argsort(scores)[::-1][:k]
            
            # Create results in the same format as dense search
            results = [(self.corpus[idx], float(scores[idx])) for idx in top_indices]
            return results
        except Exception as e:
            log_event(f"Error in sparse search: {str(e)}", level="ERROR")
            return []
    
    def hybrid_search(self, query, k=5, alpha=0.5):
        """
        Perform hybrid search combining dense and sparse retrieval.
        
        Args:
            query (str): The search query
            k (int): Number of results to return
            alpha (float): Weight for dense search (1-alpha for sparse search)
            
        Returns:
            list: Combined and reranked results
        """
        try:
            # Get results from both methods
            dense_results = self.dense_search(query, k=k*2)  # Get more candidates
            sparse_results = self.sparse_search(query, k=k*2)
            
            # Combine results
            combined_results = self._fusion_merge(dense_results, sparse_results, alpha)
            
            # Return top-k results
            return combined_results[:k]
        except Exception as e:
            log_event(f"Error in hybrid search: {str(e)}", level="ERROR")
            # Fall back to dense search if hybrid fails
            return self.dense_search(query, k=k)
    
    def _fusion_merge(self, dense_results, sparse_results, alpha=0.5):
        """
        Merge dense and sparse results using a weighted approach.
        
        Args:
            dense_results (list): Results from dense search [(text, score), ...]
            sparse_results (list): Results from sparse search [(text, score), ...]
            alpha (float): Weight for dense results
            
        Returns:
            list: Reranked results
        """
        # Create a dictionary to store combined scores
        combined_scores = {}
        
        # Normalize dense scores
        if dense_results:
            max_dense = max(score for _, score in dense_results)
            min_dense = min(score for _, score in dense_results)
            dense_range = max_dense - min_dense if max_dense != min_dense else 1.0
            
            # Add dense scores to combined scores
            for text, score in dense_results:
                # Invert the score as lower distance is better in FAISS
                normalized_score = 1.0 - ((score - min_dense) / dense_range)
                combined_scores[text] = alpha * normalized_score
        
        # Normalize sparse scores
        if sparse_results:
            max_sparse = max(score for _, score in sparse_results)
            min_sparse = min(score for _, score in sparse_results)
            sparse_range = max_sparse - min_sparse if max_sparse != min_sparse else 1.0
            
            # Add sparse scores to combined scores
            for text, score in sparse_results:
                normalized_score = (score - min_sparse) / sparse_range
                if text in combined_scores:
                    combined_scores[text] += (1 - alpha) * normalized_score
                else:
                    combined_scores[text] = (1 - alpha) * normalized_score
        
        # Sort by combined score (descending)
        sorted_results = [(text, score) for text, score in combined_scores.items()]
        sorted_results.sort(key=lambda x: x[1], reverse=True)
        
        return sorted_results

if __name__ == "__main__":
    retriever = HybridRetriever()
    results = retriever.hybrid_search("How do interest rates affect inflation?", k=3)
    print("Hybrid search results:")
    for text, score in results:
        print(f"Score: {score:.4f} | {text[:100]}...")
