# 🚀 Enhanced FAISS-Optimized RAG Chatbot for Finance

A state-of-the-art financial advisor chatbot leveraging Retrieval-Augmented Generation (RAG) with FAISS vector database for efficient knowledge retrieval, enhanced with real-time market data integration, portfolio management, and an API layer.

## ✨ Features

### Core RAG System
- **FAISS Vector Database** - Ultra-fast similarity search for retrieving relevant financial information
- **Sentence Transformers** - High-quality text embeddings for semantic understanding
- **Ollama Integration** - Local LLM execution for financial advice generation

### Premium Enhancements
- **Hybrid Search** - Combines dense (vector) and sparse (BM25) retrieval for superior results
- **Real-time Market Data** - Live stock prices, trends, and financial news integration
- **Portfolio Management** - Track investments, personalize advice based on holdings
- **Financial Analysis API** - REST API for integration with other financial systems
- **Multi-modal Output** - Enriched responses with data visualization capabilities

## 🔧 Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/faiss-optimized-rag-chatbot.git
   cd faiss-optimized-rag-chatbot
   ```

2. Create a virtual environment:
   ```
   python -m venv .venv
   .\.venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the knowledge base:
   ```
   python init_knowledge_base.py
   ```

5. Configure your API keys (optional):
   Create a `.env` file in the root directory with your API keys:
   ```
   ALPHA_VANTAGE_API=your_alpha_vantage_api_key
   ```

## 🚀 Usage

### Interactive Mode

Run the chatbot in interactive mode:
```
python main.py --user_id your_user_id
```

### API Mode

Start the API server:
```
python main.py --api --api_port 5000
```

### Available Commands

- **help** - Show available commands
- **portfolio** - Manage your investment portfolio
- **market** - Access real-time market data
- **exit** - Exit the chatbot

## 📋 API Endpoints

### Query Endpoint
```
POST /api/v1/query
{
    "query": "How do interest rates affect the stock market?",
    "user_id": "user123",  # Optional
    "enrich_with_market_data": true,  # Optional
    "personalize": true  # Optional
}
```

### Portfolio Endpoint
```
GET /api/v1/portfolio
{
    "user_id": "user123"
}

POST /api/v1/portfolio
{
    "user_id": "user123",
    "holdings": [
        {
            "symbol": "AAPL",
            "quantity": 10,
            "purchase_price": 150.00
        }
    ]
}

PUT /api/v1/portfolio
{
    "user_id": "user123",
    "preferences": {
        "risk_profile": "moderate",
        "investment_horizon": "long"
    }
}
```

### Market Data Endpoint
```
GET /api/v1/market_data?symbols=AAPL,MSFT&news=true
```

### Investment Analysis Endpoint
```
POST /api/v1/analyze_investment
{
    "investment_type": "stock",
    "parameters": {
        "symbol": "AAPL",
        "amount": 10000,
        "horizon": "long"
    },
    "risk_profile": "moderate",
    "user_id": "user123"  # Optional
}
```

## 🔍 System Architecture

### Enhanced Components

1. **Hybrid Retriever** (`enhancements/hybrid_search/hybrid_retriever.py`)
   - Combines dense vector search (FAISS) with sparse retrieval (BM25)
   - Reranks and merges results for optimal relevance

2. **Market Data Enricher** (`enhancements/data_integration/market_data.py`)
   - Connects to financial APIs for real-time data
   - Extracts financial entities from queries
   - Enriches RAG responses with current market information

3. **Portfolio Manager** (`enhancements/portfolio/portfolio_manager.py`)
   - Tracks user investment portfolios
   - Calculates portfolio performance metrics
   - Personalizes responses based on holdings

4. **Finance API** (`enhancements/api/finance_api.py`)
   - Exposes chatbot capabilities via RESTful API
   - Supports authentication and multi-user operation
   - Enables integration with other financial systems

## 🛠️ Enterprise Features

- **Multi-tiered Architecture** - Separation of concerns for scalability
- **Error Handling** - Robust error recovery at all layers
- **Caching Layer** - Performance optimization for frequently accessed data
- **Analytics Tracking** - User query patterns for system improvement

## 📊 Licensing

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
# faiss-optimized-rag-chatbot-main
