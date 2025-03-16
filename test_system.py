from llm.llm_interface import LLMInterface
import time

def main():
    print("Testing Full RAG System...")
    llm = LLMInterface()
    
    test_queries = [
        "How do interest rates affect stock markets?",
        "What are the principles of algorithmic trading?",
        "Explain the concepts of risk management in finance"
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\nTest #{i+1}: {query}")
        
        start_time = time.time()
        response = llm.generate_response(query)
        elapsed_time = time.time() - start_time
        
        print(f"Response: {response}")
        print(f"Time taken: {elapsed_time:.2f} seconds")
        print("="*50)

if __name__ == "__main__":
    main()
