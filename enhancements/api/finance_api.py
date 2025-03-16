from flask import Flask, request, jsonify
import threading
from llm.llm_interface import LLMInterface
from enhancements.hybrid_search.hybrid_retriever import HybridRetriever
from enhancements.data_integration.market_data import MarketDataEnricher
from enhancements.portfolio.portfolio_manager import PortfolioManager
from utils.logger import log_event
import json
import os

app = Flask(__name__)

# Create data directories if they don't exist
os.makedirs(os.path.join("data", "portfolios"), exist_ok=True)
os.makedirs(os.path.join("data", "analytics"), exist_ok=True)

# Initialize services
llm_interface = LLMInterface()
market_data = MarketDataEnricher()

# Store active user sessions
user_sessions = {}

@app.route('/api/v1/query', methods=['POST'])
def query_endpoint():
    """
    Main query endpoint for RAG-based financial insights.
    
    Request format:
    {
        "query": "How do interest rates affect the stock market?",
        "user_id": "user123",  # Optional
        "enrich_with_market_data": true,  # Optional
        "personalize": true  # Optional
    }
    """
    try:
        data = request.json
        
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' parameter"}), 400
            
        query = data['query']
        user_id = data.get('user_id')
        enrich = data.get('enrich_with_market_data', False)
        personalize = data.get('personalize', False)
        
        # Log the request
        log_event(f"API request: {json.dumps(data)}")
        
        # Generate base response
        base_response = llm_interface.generate_response(query)
        
        # Enhanced response pipeline
        enhanced_response = base_response
        
        # Enrich with market data if requested
        if enrich:
            enhanced_response = market_data.enrich_response(query, enhanced_response)
        
        # Personalize if requested and user_id provided
        if personalize and user_id:
            # Check if we already have a session for this user
            if user_id not in user_sessions:
                user_sessions[user_id] = PortfolioManager(user_id)
                
            enhanced_response = user_sessions[user_id].personalize_response(query, enhanced_response)
        
        # Track query for analytics
        if user_id:
            track_query_analytics(user_id, query, len(enhanced_response))
        
        return jsonify({
            "query": query,
            "response": enhanced_response,
            "enriched": enrich,
            "personalized": personalize and user_id is not None
        })
        
    except Exception as e:
        log_event(f"API error: {str(e)}", level="ERROR")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/portfolio', methods=['GET', 'POST', 'PUT'])
def portfolio_endpoint():
    """
    Endpoint for managing user portfolios.
    
    GET: Retrieve portfolio
    POST: Add holdings
    PUT: Update preferences
    """
    try:
        data = request.json or {}
        
        if 'user_id' not in data:
            return jsonify({"error": "Missing 'user_id' parameter"}), 400
            
        user_id = data['user_id']
        
        # Initialize portfolio manager if needed
        if user_id not in user_sessions:
            user_sessions[user_id] = PortfolioManager(user_id)
        
        portfolio_manager = user_sessions[user_id]
        
        if request.method == 'GET':
            # Get portfolio summary
            summary = portfolio_manager.get_portfolio_summary()
            return jsonify(summary)
            
        elif request.method == 'POST':
            # Add holdings
            if 'holdings' not in data:
                return jsonify({"error": "Missing 'holdings' parameter"}), 400
                
            holdings = data['holdings']
            results = []
            
            for holding in holdings:
                if all(k in holding for k in ['symbol', 'quantity', 'purchase_price']):
                    success = portfolio_manager.add_holding(
                        holding['symbol'],
                        holding['quantity'],
                        holding['purchase_price']
                    )
                    results.append({
                        "symbol": holding['symbol'],
                        "success": success
                    })
                else:
                    results.append({
                        "symbol": holding.get('symbol', 'unknown'),
                        "success": False,
                        "error": "Missing required fields"
                    })
            
            return jsonify({"results": results})
            
        elif request.method == 'PUT':
            # Update preferences
            if 'preferences' not in data:
                return jsonify({"error": "Missing 'preferences' parameter"}), 400
                
            success = portfolio_manager.update_preferences(data['preferences'])
            
            return jsonify({"success": success})
            
    except Exception as e:
        log_event(f"Portfolio API error: {str(e)}", level="ERROR")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/market_data', methods=['GET'])
def market_data_endpoint():
    """
    Endpoint for retrieving market data.
    
    Query parameters:
    - symbols: Comma-separated list of symbols
    - news: Boolean, whether to include news
    """
    try:
        symbols = request.args.get('symbols', '').split(',')
        include_news = request.args.get('news', 'false').lower() == 'true'
        
        symbols = [s.strip() for s in symbols if s.strip()]
        
        response = {
            "data": {},
            "timestamp": market_data.fetch_live_data({"symbols": []})["timestamp"]
        }
        
        # Get data for each symbol
        for symbol in symbols:
            stock_data = market_data.fetch_stock_data(symbol)
            if stock_data:
                response["data"][symbol] = stock_data
        
        # Get news if requested
        if include_news:
            response["news"] = market_data.fetch_market_news()
        
        return jsonify(response)
        
    except Exception as e:
        log_event(f"Market data API error: {str(e)}", level="ERROR")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/analyze_investment', methods=['POST'])
def analyze_investment():
    """
    Endpoint for deep analysis of an investment opportunity.
    
    Request format:
    {
        "investment_type": "stock" | "bond" | "etf" | "crypto",
        "parameters": {
            "symbol": "AAPL",
            "amount": 10000,
            "horizon": "long" | "medium" | "short"
        },
        "risk_profile": "conservative" | "moderate" | "aggressive",
        "user_id": "user123"  # Optional
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "Missing request body"}), 400
            
        required_fields = ["investment_type", "parameters", "risk_profile"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing '{field}' parameter"}), 400
        
        # Extract data
        investment_type = data["investment_type"]
        parameters = data["parameters"]
        risk_profile = data["risk_profile"]
        user_id = data.get("user_id")
        
        # Create analysis prompt
        prompt = f"""
        Analyze the following {investment_type} investment opportunity:
        
        Investment details:
        - Type: {investment_type}
        - Symbol/Asset: {parameters.get('symbol', 'N/A')}
        - Investment amount: ${parameters.get('amount', 'N/A')}
        - Time horizon: {parameters.get('horizon', 'N/A')}
        - Investor risk profile: {risk_profile}
        
        Provide a detailed investment analysis including:
        1. Overview of the investment
        2. Potential risks and rewards
        3. Historical performance analysis
        4. Future outlook
        5. Allocation recommendations
        """
        
        # Generate analysis
        analysis = llm_interface.generate_response(prompt)
        
        # Enhance with market data
        if "symbol" in parameters:
            entities = {"symbols": [parameters["symbol"]], "metrics": [], "asset_classes": [investment_type]}
            live_data = market_data.fetch_live_data(entities)
            analysis = market_data.merge_knowledge_with_live_data(analysis, live_data)
        
        # Personalize if user_id provided
        if user_id:
            if user_id not in user_sessions:
                user_sessions[user_id] = PortfolioManager(user_id)
                
            # Check if personalization is relevant
            if "parameters" in data and "symbol" in parameters:
                # Check if symbol is in portfolio
                for holding in user_sessions[user_id].portfolio["holdings"]:
                    if holding["symbol"] == parameters["symbol"]:
                        # Personalize the analysis
                        portfolio_context = user_sessions[user_id].get_portfolio_context()
                        analysis = user_sessions[user_id].contextualize_response(analysis, portfolio_context)
                        break
        
        return jsonify({
            "analysis": analysis,
            "investment_type": investment_type,
            "risk_profile": risk_profile
        })
        
    except Exception as e:
        log_event(f"Investment analysis API error: {str(e)}", level="ERROR")
        return jsonify({"error": str(e)}), 500

def track_query_analytics(user_id, query, response_length):
    """Track query for analytics purposes."""
    try:
        analytics_dir = os.path.join("data", "analytics")
        os.makedirs(analytics_dir, exist_ok=True)
        
        analytics_file = os.path.join(analytics_dir, f"{user_id}_queries.jsonl")
        
        with open(analytics_file, 'a') as f:
            entry = {
                "timestamp": market_data.fetch_live_data({"symbols": []})["timestamp"],
                "query": query,
                "response_length": response_length
            }
            f.write(json.dumps(entry) + '\n')
    except Exception as e:
        log_event(f"Error tracking analytics: {str(e)}", level="WARNING")

def run_api_server(host='0.0.0.0', port=5000):
    """Run the API server."""
    app.run(host=host, port=port)

def start_api_server_in_thread(host='0.0.0.0', port=5000):
    """Start the API server in a separate thread."""
    api_thread = threading.Thread(target=run_api_server, args=(host, port))
    api_thread.daemon = True
    api_thread.start()
    log_event(f"API server started on http://{host}:{port}/")
    return api_thread

if __name__ == "__main__":
    run_api_server()
