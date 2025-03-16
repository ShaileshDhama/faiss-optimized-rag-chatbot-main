import ollama

try:
    models = ollama.list()
    print(f'Available models: {models}')
except Exception as e:
    print(f'Error connecting to Ollama server: {e}')
