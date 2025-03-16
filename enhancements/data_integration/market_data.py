import os
import requests
import json
import datetime
import re
from utils.logger import log_event
from config import ALPHA_VANTAGE_API

class MarketDataEnricher:
    """
    Enriches RAG responses with real-time market data from financial APIs.
    """
    
    def __init__(self, api_key=None):
        """Initialize the market data enricher with API keys."""
        self.api_key = api_key or ALPHA_VANTAGE_API or os.getenv("ALPHA_VANTAGE_API")
        if not self.api_key:
            log_event("No API key found for financial data. Real-time enrichment will be limited.", level="WARNING")
    
    def extract_financial_entities(self, query):
        """
        Extract financial entities like ticker symbols, asset classes, etc. from the query.
        
        Args:
            query (str): The user query
            
        Returns:
            dict: Extracted entities
        """
        entities = {
            "symbols": [],
            "metrics": [],
            "asset_classes": []
        }
        
        # Extract stock symbols (simple regex for demonstration)
        symbol_pattern = r'\b[A-Z]{1,5}\b'
        potential_symbols = re.findall(symbol_pattern, query)
        
        # Filter out common words that match the pattern
        common_words = {'I', 'A', 'THE', 'TO', 'IN', 'IS', 'IT', 'AND', 'OR', 'FOR'}
        symbols = [sym for sym in potential_symbols if sym not in common_words]
        
        # Only include the first few symbols to avoid unnecessary API calls
        entities["symbols"] = symbols[:3]
        
        # Extract financial metrics
        metric_keywords = [
            "price", "return", "dividend", "yield", "eps", "p/e", "market cap", 
            "volume", "revenue", "profit", "growth", "performance", "trend"
        ]
        entities["metrics"] = [metric for metric in metric_keywords if metric.lower() in query.lower()]
        
        # Extract asset classes
        asset_classes = ["stock", "bond", "etf", "forex", "crypto", "commodity", "index"]
        entities["asset_classes"] = [asset for asset in asset_classes if asset.lower() in query.lower()]
        
        log_event(f"Extracted financial entities: {entities}")
        return entities
    
    def fetch_stock_data(self, symbol):
        """
        Fetch real-time stock data for a given symbol.
        
        Args:
            symbol (str): Stock ticker symbol
            
        Returns:
            dict: Stock data or None if unavailable
        """
        if not self.api_key:
            log_event(f"Cannot fetch data for {symbol}: No API key", level="WARNING")
            return None
            
        try:
            endpoint = f"https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.api_key
            }
            
            response = requests.get(endpoint, params=params)
            data = response.json()
            
            if "Global Quote" in data and data["Global Quote"]:
                return {
                    "symbol": symbol,
                    "price": data["Global Quote"].get("05. price"),
                    "change": data["Global Quote"].get("09. change"),
                    "change_percent": data["Global Quote"].get("10. change percent"),
                    "volume": data["Global Quote"].get("06. volume"),
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                log_event(f"No data found for symbol {symbol}", level="WARNING")
                return None
                
        except Exception as e:
            log_event(f"Error fetching stock data for {symbol}: {str(e)}", level="ERROR")
            return None
    
    def fetch_market_news(self, topic=None):
        """
        Fetch latest market news (general or topic-specific).
        
        Args:
            topic (str, optional): News topic
            
        Returns:
            list: News items or empty list if unavailable
        """
        if not self.api_key:
            log_event("Cannot fetch market news: No API key", level="WARNING")
            return []
            
        try:
            endpoint = f"https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "topics": topic or "financial_markets",
                "apikey": self.api_key,
                "limit": 3  # Limit to 3 news items
            }
            
            response = requests.get(endpoint, params=params)
            data = response.json()
            
            if "feed" in data:
                return [{
                    "title": item.get("title"),
                    "summary": item.get("summary"),
                    "url": item.get("url"),
                    "published": item.get("time_published")
                } for item in data["feed"][:3]]
            else:
                log_event("No market news found", level="WARNING")
                return []
                
        except Exception as e:
            log_event(f"Error fetching market news: {str(e)}", level="ERROR")
            return []
    
    def fetch_live_data(self, entities):
        """
        Fetch all relevant live data based on extracted entities.
        
        Args:
            entities (dict): Extracted financial entities
            
        Returns:
            dict: Compiled live data
        """
        data = {
            "stocks": {},
            "news": [],
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Fetch stock data for each symbol
        for symbol in entities.get("symbols", []):
            stock_data = self.fetch_stock_data(symbol)
            if stock_data:
                data["stocks"][symbol] = stock_data
        
        # Fetch relevant news if requested
        if "news" in entities.get("metrics", []) or not data["stocks"]:
            # Get news related to first asset class or general financial news
            topic = entities.get("asset_classes", ["financial_markets"])[0]
            data["news"] = self.fetch_market_news(topic)
        
        log_event(f"Fetched live data: {json.dumps(data, default=str)[:200]}...")
        return data
    
    def merge_knowledge_with_live_data(self, base_response, live_data):
        """
        Merge RAG response with live financial data.
        
        Args:
            base_response (str): Base RAG response
            live_data (dict): Live financial data
            
        Returns:
            str: Enhanced response
        """
        if not live_data["stocks"] and not live_data["news"]:
            return base_response
            
        enhanced_response = base_response
        
        # Add stock data section if available
        if live_data["stocks"]:
            enhanced_response += "\n\n## Current Market Data (as of " + live_data["timestamp"] + ")\n"
            
            for symbol, data in live_data["stocks"].items():
                enhanced_response += f"\n**{symbol}**: ${data['price']} ({data['change_percent']})"
                enhanced_response += f" | Volume: {data['volume']}"
        
        # Add news section if available
        if live_data["news"]:
            enhanced_response += "\n\n## Latest Market News\n"
            
            for item in live_data["news"]:
                enhanced_response += f"\n- **{item['title']}**"
                enhanced_response += f"\n  {item['summary'][:150]}..."
                enhanced_response += f"\n  [Read more]({item['url']})"
        
        enhanced_response += "\n\n*Note: Real-time data provided by Alpha Vantage.*"
        return enhanced_response
    
    def enrich_response(self, query, base_response):
        """
        Enrich the RAG response with real-time financial data.
        
        Args:
            query (str): User query
            base_response (str): Base RAG response
            
        Returns:
            str: Enriched response
        """
        try:
            # Extract entities from query
            entities = self.extract_financial_entities(query)
            
            # If no financial entities found, return the base response
            if not entities["symbols"] and not entities["metrics"] and not entities["asset_classes"]:
                return base_response
            
            # Fetch live data
            live_data = self.fetch_live_data(entities)
            
            # Merge with base response
            enhanced_response = self.merge_knowledge_with_live_data(base_response, live_data)
            
            return enhanced_response
        except Exception as e:
            log_event(f"Error enriching response with market data: {str(e)}", level="ERROR")
            return base_response  # Fall back to base response

if __name__ == "__main__":
    enricher = MarketDataEnricher()
    test_query = "What's the current price of AAPL and how do interest rates affect tech stocks?"
    base_response = "Interest rates impact tech stocks by affecting borrowing costs and valuation models. Higher rates tend to reduce the present value of future earnings, which often affects high-growth tech companies more severely than value stocks."
    enhanced = enricher.enrich_response(test_query, base_response)
    print(enhanced)
