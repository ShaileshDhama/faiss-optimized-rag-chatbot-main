from llm.llm_interface import LLMInterface

def main():
    print("Testing LLM Interface...")
    llm = LLMInterface()
    query = "How do interest rates affect stock markets?"
    print(f"Query: {query}")
    response = llm.generate_response(query)
    print(f"Response: {response}")

if __name__ == "__main__":
    main()
