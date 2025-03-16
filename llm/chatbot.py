import ollama
from retrieval.retriever import FinanceRetriever
from config import LLM_MODEL

class FinanceChatbot:
    def __init__(self):
        self.retriever = FinanceRetriever()

    def generate_response(self, user_query):
        """Retrieves knowledge & generates AI response."""
        retrieved_chunks = self.retriever.retrieve(user_query)
        context = " ".join([chunk[0] for chunk in retrieved_chunks])
        
        prompt = f"""
        You are an AI finance assistant. Answer based on the provided knowledge only.
        Query: {user_query}
        Context: {context}
        """

        response = ollama.chat(model=LLM_MODEL, messages=[{"role": "user", "content": prompt}])
        return response['message']['content']

if __name__ == "__main__":
    chatbot = FinanceChatbot()
    query = "Explain Basel III regulations."
    print(f"💬 AI Response: {chatbot.generate_response(query)}")
