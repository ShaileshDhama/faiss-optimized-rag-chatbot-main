import os
import json
import datetime
import re
from utils.logger import log_event
from enhancements.data_integration.market_data import MarketDataEnricher

class PortfolioManager:
    """
    Manages user portfolios and provides personalized financial insights.
    """
    
    def __init__(self, user_id):
        """Initialize the portfolio manager for a specific user."""
        self.user_id = user_id
        self.data_dir = os.path.join("data", "portfolios")
        self.portfolio = self.load_portfolio()
        self.market_data = MarketDataEnricher()
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
    
    def load_portfolio(self):
        """
        Load user portfolio from storage.
        
        Returns:
            dict: User portfolio or empty default if none exists
        """
        try:
            portfolio_path = os.path.join(self.data_dir, f"{self.user_id}.json")
            
            if os.path.exists(portfolio_path):
                with open(portfolio_path, 'r') as f:
                    return json.load(f)
            else:
                # Return empty default portfolio
                return {
                    "user_id": self.user_id,
                    "holdings": [],
                    "watchlist": [],
                    "preferences": {
                        "risk_profile": "moderate",
                        "investment_horizon": "medium",
                        "sectors_of_interest": []
                    },
                    "created_at": datetime.datetime.now().isoformat(),
                    "updated_at": datetime.datetime.now().isoformat()
                }
        except Exception as e:
            log_event(f"Error loading portfolio for user {self.user_id}: {str(e)}", level="ERROR")
            return {
                "user_id": self.user_id,
                "holdings": [],
                "watchlist": [],
                "preferences": {"risk_profile": "moderate"}
            }
    
    def save_portfolio(self):
        """Save the current portfolio to storage."""
        try:
            portfolio_path = os.path.join(self.data_dir, f"{self.user_id}.json")
            
            # Update timestamp
            self.portfolio["updated_at"] = datetime.datetime.now().isoformat()
            
            with open(portfolio_path, 'w') as f:
                json.dump(self.portfolio, f, indent=2)
                
            log_event(f"Portfolio saved for user {self.user_id}")
            return True
        except Exception as e:
            log_event(f"Error saving portfolio for user {self.user_id}: {str(e)}", level="ERROR")
            return False
    
    def add_holding(self, symbol, quantity, purchase_price):
        """
        Add a stock holding to the user's portfolio.
        
        Args:
            symbol (str): Stock ticker symbol
            quantity (float): Number of shares
            purchase_price (float): Purchase price per share
            
        Returns:
            bool: Success status
        """
        try:
            # Check if holding already exists
            for holding in self.portfolio["holdings"]:
                if holding["symbol"] == symbol:
                    # Update existing holding
                    holding["quantity"] += float(quantity)
                    holding["transactions"].append({
                        "type": "buy",
                        "quantity": float(quantity),
                        "price": float(purchase_price),
                        "date": datetime.datetime.now().isoformat()
                    })
                    return self.save_portfolio()
            
            # Add new holding
            self.portfolio["holdings"].append({
                "symbol": symbol,
                "quantity": float(quantity),
                "transactions": [{
                    "type": "buy",
                    "quantity": float(quantity),
                    "price": float(purchase_price),
                    "date": datetime.datetime.now().isoformat()
                }]
            })
            
            return self.save_portfolio()
        except Exception as e:
            log_event(f"Error adding holding {symbol} for user {self.user_id}: {str(e)}", level="ERROR")
            return False
    
    def update_preferences(self, preferences):
        """
        Update user investment preferences.
        
        Args:
            preferences (dict): User preferences
            
        Returns:
            bool: Success status
        """
        try:
            # Update preferences
            for key, value in preferences.items():
                self.portfolio["preferences"][key] = value
                
            return self.save_portfolio()
        except Exception as e:
            log_event(f"Error updating preferences for user {self.user_id}: {str(e)}", level="ERROR")
            return False
    
    def get_portfolio_summary(self):
        """
        Generate a summary of the user's portfolio with current market values.
        
        Returns:
            dict: Portfolio summary
        """
        try:
            summary = {
                "total_value": 0.0,
                "holdings": [],
                "performance": {"total_gain": 0.0, "total_gain_percent": 0.0},
                "asset_allocation": {},
                "risk_profile": self.portfolio["preferences"].get("risk_profile", "moderate"),
            }
            
            # Process each holding
            for holding in self.portfolio["holdings"]:
                symbol = holding["symbol"]
                quantity = holding["quantity"]
                
                # Get current price
                stock_data = self.market_data.fetch_stock_data(symbol)
                
                if stock_data and "price" in stock_data:
                    current_price = float(stock_data["price"])
                    
                    # Calculate average purchase price
                    transactions = holding.get("transactions", [])
                    total_cost = sum(t["price"] * t["quantity"] for t in transactions if t["type"] == "buy")
                    total_shares = sum(t["quantity"] for t in transactions if t["type"] == "buy")
                    avg_price = total_cost / total_shares if total_shares > 0 else 0
                    
                    # Calculate values
                    market_value = quantity * current_price
                    cost_basis = quantity * avg_price
                    gain_loss = market_value - cost_basis
                    gain_loss_percent = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0
                    
                    # Add to summary
                    summary["holdings"].append({
                        "symbol": symbol,
                        "quantity": quantity,
                        "current_price": current_price,
                        "market_value": market_value,
                        "avg_price": avg_price,
                        "cost_basis": cost_basis,
                        "gain_loss": gain_loss,
                        "gain_loss_percent": gain_loss_percent
                    })
                    
                    summary["total_value"] += market_value
            
            # Calculate overall performance
            total_cost = sum(h["cost_basis"] for h in summary["holdings"])
            if total_cost > 0:
                summary["performance"]["total_gain"] = summary["total_value"] - total_cost
                summary["performance"]["total_gain_percent"] = summary["performance"]["total_gain"] / total_cost * 100
            
            # Calculate asset allocation
            for holding in summary["holdings"]:
                allocation = (holding["market_value"] / summary["total_value"]) * 100 if summary["total_value"] > 0 else 0
                summary["asset_allocation"][holding["symbol"]] = allocation
            
            return summary
        except Exception as e:
            log_event(f"Error generating portfolio summary for user {self.user_id}: {str(e)}", level="ERROR")
            return {"error": str(e)}
    
    def is_portfolio_related(self, query):
        """
        Check if a query is related to the user's portfolio.
        
        Args:
            query (str): User query
            
        Returns:
            bool: Whether the query is portfolio-related
        """
        portfolio_keywords = [
            "my portfolio", "my investments", "my stocks", "my holdings",
            "my watchlist", "my performance", "my returns", "my balance"
        ]
        
        # Check for portfolio keywords
        for keyword in portfolio_keywords:
            if keyword.lower() in query.lower():
                return True
        
        # Check for user's specific holdings
        for holding in self.portfolio["holdings"]:
            if holding["symbol"].lower() in query.lower() and any(personal in query.lower() for personal in ["my", "i own", "i have"]):
                return True
        
        return False
    
    def get_portfolio_context(self):
        """
        Get portfolio context for personalizing responses.
        
        Returns:
            str: Portfolio context
        """
        try:
            summary = self.get_portfolio_summary()
            
            context = f"""
            The user has a {summary['risk_profile']} risk profile with a portfolio valued at ${summary['total_value']:.2f}.
            
            Holdings:
            """
            
            for holding in summary["holdings"]:
                context += f"- {holding['symbol']}: {holding['quantity']} shares (${holding['market_value']:.2f}, {holding['gain_loss_percent']:.2f}% return)\n"
            
            context += f"\nOverall return: ${summary['performance']['total_gain']:.2f} ({summary['performance']['total_gain_percent']:.2f}%)"
            
            return context
        except Exception as e:
            log_event(f"Error getting portfolio context for user {self.user_id}: {str(e)}", level="ERROR")
            return "User has a portfolio, but details couldn't be retrieved."
    
    def contextualize_response(self, base_response, portfolio_context):
        """
        Contextualize a response with the user's portfolio information.
        
        Args:
            base_response (str): Base RAG response
            portfolio_context (str): Portfolio context
            
        Returns:
            str: Personalized response
        """
        try:
            personalized_response = f"Based on your investment profile:\n\n{base_response}\n\n"
            
            personalized_response += "\n## Your Portfolio Analysis\n"
            personalized_response += portfolio_context
            
            # Extract portfolio insights
            summary = self.get_portfolio_summary()
            
            # Add personalized recommendations
            if summary["total_value"] > 0:
                personalized_response += "\n\n## Personalized Insights\n"
                
                # Risk profile-based recommendations
                if summary["risk_profile"] == "conservative":
                    personalized_response += "\nConsidering your conservative risk profile, you might want to focus on stability and income."
                elif summary["risk_profile"] == "aggressive":
                    personalized_response += "\nWith your aggressive risk profile, you might be open to higher-growth opportunities, balanced with your existing positions."
                else:  # moderate
                    personalized_response += "\nWith your moderate risk approach, continuing to balance growth and stability may be appropriate."
                
                # Diversification advice
                if len(summary["holdings"]) < 3:
                    personalized_response += "\n\nYour portfolio appears to have limited diversification. Consider adding positions across different sectors to reduce risk."
                
                # Performance-based advice
                if summary["performance"]["total_gain_percent"] < 0:
                    personalized_response += "\n\nYour portfolio is currently showing a loss. Remember that investing is long-term, and short-term fluctuations are normal."
                elif summary["performance"]["total_gain_percent"] > 20:
                    personalized_response += "\n\nYour portfolio is performing well. Consider if rebalancing might be appropriate to lock in some gains while maintaining your desired allocation."
            
            return personalized_response
        except Exception as e:
            log_event(f"Error contextualizing response for user {self.user_id}: {str(e)}", level="ERROR")
            return base_response  # Fall back to base response
    
    def personalize_response(self, query, base_response):
        """
        Personalize a response based on the user's portfolio.
        
        Args:
            query (str): User query
            base_response (str): Base RAG response
            
        Returns:
            str: Personalized response
        """
        try:
            if self.is_portfolio_related(query):
                portfolio_context = self.get_portfolio_context()
                return self.contextualize_response(base_response, portfolio_context)
            return base_response
        except Exception as e:
            log_event(f"Error personalizing response for user {self.user_id}: {str(e)}", level="ERROR")
            return base_response  # Fall back to base response

if __name__ == "__main__":
    # Test portfolio manager
    manager = PortfolioManager("test_user")
    
    # Add some sample holdings
    manager.add_holding("AAPL", 10, 150.0)
    manager.add_holding("MSFT", 5, 250.0)
    
    # Set preferences
    manager.update_preferences({"risk_profile": "moderate", "investment_horizon": "long"})
    
    # Get portfolio summary
    summary = manager.get_portfolio_summary()
    print(json.dumps(summary, indent=2, default=str))
    
    # Test personalizing a response
    query = "How are my investments performing with current market conditions?"
    base_response = "Market conditions are currently volatile due to economic uncertainty and changing interest rate environments."
    personalized = manager.personalize_response(query, base_response)
    print(personalized)
