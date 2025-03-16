# 🚀 Enhanced Finance Chatbot - Quick Start Guide

This guide will help you quickly set up and start using the enhanced FAISS-optimized RAG chatbot with all its premium features.

## 📋 Prerequisites

1. Python 3.8+ installed
2. Git installed
3. 8GB+ RAM recommended for optimal performance
4. [Optional] Alpha Vantage API key for real-time market data

## 🔧 Installation

1. **Activate your virtual environment:**

```bash
# On Windows
.\.venv\Scripts\activate

# On macOS/Linux
source .venv/bin/activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Initialize the knowledge base:**

```bash
python init_knowledge_base.py
```

This will create the FAISS index and process the financial knowledge base documents.

4. **[Optional] Configure API keys:**

Create a `.env` file in the root directory:

```
ALPHA_VANTAGE_API=your_alpha_vantage_api_key
```

## 🎮 Running the Chatbot

### Basic Interactive Mode

```bash
python main.py
```

### With User Profile for Personalization

```bash
python main.py --user_id your_username
```

### Start the API Server

```bash
python main.py --api --api_port 5000
```

## 🧠 Using Premium Features

### 1. Hybrid Search

The hybrid search feature is used automatically in the background, combining dense vector search (FAISS) with sparse retrieval (BM25) for more robust results.

### 2. Real-time Market Data

Try asking questions like:
- "What's the current price of AAPL?"
- "How is the tech sector performing today?"
- "Give me the latest financial news"

### 3. Portfolio Management

Use the `portfolio` command in the interactive mode:

```
You: portfolio
```

Then follow the prompts to:
- View your portfolio summary
- Add new holdings
- Update your investment preferences

### 4. API Integration

With the API server running, you can use these endpoints:

#### Query the Chatbot
```bash
curl -X POST http://localhost:5000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do interest rates affect inflation?", "enrich_with_market_data": true}'
```

#### Manage Portfolio
```bash
curl -X POST http://localhost:5000/api/v1/portfolio \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "holdings": [{"symbol": "AAPL", "quantity": 10, "purchase_price": 150.00}]}'
```

#### Get Market Data
```bash
curl "http://localhost:5000/api/v1/market_data?symbols=AAPL,MSFT&news=true"
```

#### Analyze Investment
```bash
curl -X POST http://localhost:5000/api/v1/analyze_investment \
  -H "Content-Type: application/json" \
  -d '{"investment_type": "stock", "parameters": {"symbol": "AAPL", "amount": 10000, "horizon": "long"}, "risk_profile": "moderate"}'
```

## 💡 Tips & Tricks

1. **For the best responses:**
   - Be specific in your financial questions
   - Mention specific stocks, assets, or financial concepts

2. **Portfolio personalization:** 
   - Add at least 3-5 holdings to get meaningful personalized advice
   - Set your risk profile accurately for better recommendations

3. **API integration:**
   - Use the `?user_id=your_username` parameter to maintain session context
   - For production use, implement proper authentication

4. **Performance optimization:**
   - Use the hybrid search for complex queries
   - Use the FAISS-only search for simple factual queries

## 🔍 Troubleshooting

### Common Issues

1. **"No module named..." error:**
   - Make sure your virtual environment is activated
   - Try reinstalling dependencies: `pip install -r requirements.txt`

2. **Slow response times:**
   - Check your RAM usage, the FAISS index requires memory
   - Consider reducing the `k` value in search parameters

3. **API connection errors:**
   - Verify the API server is running
   - Check the port is not in use by another application

4. **Market data not loading:**
   - Verify your API key in the `.env` file
   - Check your internet connection
   - Alpha Vantage has rate limits, you might need to wait

## 📚 Next Steps

- Explore the code in the `enhancements/` directory
- Review the API documentation for integration options
- Check out the portfolio management features for personalized insights
- Consider contributing to the project

Enjoy your enhanced financial chatbot!
