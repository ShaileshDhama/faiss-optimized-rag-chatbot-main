import ollama
from retrieval.retriever import FinanceRetriever
from config import LLM_MODEL
from utils.logger import log_event

class LLMInterface:
    def __init__(self):
        """Initialize retriever for fetching relevant finance data."""
        self.retriever = FinanceRetriever()
        self.model = LLM_MODEL
        self.ollama_available = self._check_ollama()
        
    def _check_ollama(self):
        """Check if Ollama is available."""
        try:
            models = ollama.list()
            log_event("Ollama is available and working")
            
            # Check if the required model is available, if not, try to pull it
            model_available = any(model.get('name') == self.model for model in models.get('models', []))
            if not model_available:
                log_event(f"Model {self.model} not found, attempting to pull it...")
                try:
                    ollama.pull(self.model)
                    log_event(f"Successfully pulled model {self.model}")
                except Exception as e:
                    log_event(f"Error pulling model {self.model}: {str(e)}", level="WARNING")
                    # Fallback to a simpler model if available
                    self.model = "llama2"
            
            return True
        except Exception as e:
            log_event(f"Ollama is not available: {str(e)}", level="WARNING")
            return False

    def generate_response(self, user_query):
        """Retrieve relevant knowledge and generate an AI response."""
        try:
            retrieved_chunks = self.retriever.retrieve(user_query)
            
            # Log the retrieved chunks
            log_event(f"Retrieved {len(retrieved_chunks)} chunks for query: {user_query}")
            for i, (chunk, score) in enumerate(retrieved_chunks):
                log_event(f"Chunk {i+1}: {chunk[:100]}... (score: {score:.4f})")
            
            context = " ".join([chunk[0] for chunk in retrieved_chunks])

            prompt = f"""
            You are an AI finance assistant. Answer based on the provided knowledge only.
            Query: {user_query}
            Context: {context}
            """

            if self.ollama_available:
                try:
                    response = ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt}])
                    return response['message']['content']
                except Exception as e:
                    log_event(f"Error generating response with Ollama: {str(e)}", level="ERROR")
                    # Fall back to direct retrieval if Ollama fails
                    return f"Based on the retrieved information:\n\n" + "\n\n".join([f"- {chunk[0]}" for chunk in retrieved_chunks])
            else:
                # If Ollama is not available, use retrieved chunks directly
                log_event("Using retrieved chunks directly as Ollama is not available")
                return f"Based on the retrieved information:\n\n" + "\n\n".join([f"- {chunk[0]}" for chunk in retrieved_chunks])
                
        except Exception as e:
            log_event(f"Error generating response: {str(e)}", level="ERROR")
            return f"Sorry, I encountered an error: {str(e)}"

if __name__ == "__main__":
    llm = LLMInterface()
    print(llm.generate_response("Explain Basel III regulations."))
