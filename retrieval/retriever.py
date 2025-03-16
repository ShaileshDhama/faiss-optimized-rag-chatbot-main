from embeddings.embedding import EmbeddingHandler
from utils.logger import log_event

class FinanceRetriever:
    def __init__(self):
        """Initialize retriever for fetching relevant finance data."""
        try:
            self.embedder = EmbeddingHandler()
            log_event("Retriever initialized successfully")
        except Exception as e:
            log_event(f"Error initializing retriever: {str(e)}", level="ERROR")
            raise

    def retrieve(self, query, k=3):
        """
        Retrieve relevant text chunks for a given query.
        
        Args:
            query (str): User query
            k (int): Number of chunks to retrieve
            
        Returns:
            list: List of (text, score) tuples
        """
        try:
            results = self.embedder.search(query, k=k)
            log_event(f"Retrieved {len(results)} chunks for query")
            return results
            
        except Exception as e:
            log_event(f"Error during retrieval: {str(e)}", level="ERROR")
            return []
