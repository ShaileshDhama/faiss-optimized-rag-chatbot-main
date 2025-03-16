import sys
import argparse
from llm.llm_interface import LLMInterface
from enhancements.hybrid_search.hybrid_retriever import HybridRetriever
from enhancements.data_integration.market_data import MarketDataEnricher
from enhancements.portfolio.portfolio_manager import PortfolioManager
from enhancements.api.finance_api import start_api_server_in_thread
from utils.logger import log_event

class FinanceChatbot:
    """Enhanced finance chatbot with RAG, real-time data, and portfolio management."""
    
    def __init__(self, user_id=None):
        """Initialize the enhanced finance chatbot."""
        self.llm = LLMInterface()
        self.market_data = MarketDataEnricher()
        self.user_id = user_id
        self.portfolio_manager = PortfolioManager(user_id) if user_id else None
        log_event("Enhanced Finance Chatbot initialized successfully")
    
    def process_query(self, query, enrich=True, personalize=True):
        """
        Process a user query with enhanced capabilities.
        
        Args:
            query (str): User query
            enrich (bool): Whether to enrich with market data
            personalize (bool): Whether to personalize based on portfolio
            
        Returns:
            str: Enhanced response
        """
        # Generate base response
        response = self.llm.generate_response(query)
        
        # Enrich with market data if requested
        if enrich:
            response = self.market_data.enrich_response(query, response)
        
        # Personalize if requested and portfolio manager available
        if personalize and self.portfolio_manager:
            response = self.portfolio_manager.personalize_response(query, response)
        
        return response
    
    def run_interactive(self):
        """Run the chatbot in interactive mode."""
        print("\n🤖 Welcome to the Enhanced Finance Advisor!")
        print("⚡ I can provide financial insights, real-time market data, and portfolio advice.")
        print("📊 Type 'exit' to quit, 'help' for commands.")
        
        commands = {
            "help": "Show available commands",
            "portfolio": "Manage your portfolio",
            "market": "Get real-time market data",
            "exit": "Exit the chatbot"
        }
        
        while True:
            print("\n" + "-" * 50)
            query = input("You: ").strip()
            
            if query.lower() == 'exit':
                print("\nThank you for using the Enhanced Finance Advisor!")
                break
                
            elif query.lower() == 'help':
                print("\nAvailable commands:")
                for cmd, desc in commands.items():
                    print(f"  - {cmd}: {desc}")
                continue
                
            elif query.lower() == 'portfolio' and self.portfolio_manager:
                self._handle_portfolio_commands()
                continue
                
            elif query.lower() == 'market':
                self._handle_market_commands()
                continue
            
            # Process regular query
            response = self.process_query(query)
            print(f"\nAI: {response}")
    
    def _handle_portfolio_commands(self):
        """Handle portfolio management commands."""
        print("\n📊 Portfolio Management")
        print("1. View portfolio summary")
        print("2. Add holding")
        print("3. Update preferences")
        print("4. Back to main chat")
        
        choice = input("Select an option (1-4): ").strip()
        
        if choice == '1':
            summary = self.portfolio_manager.get_portfolio_summary()
            print("\n=== Portfolio Summary ===")
            print(f"Total Value: ${summary['total_value']:.2f}")
            print(f"Performance: {summary['performance']['total_gain_percent']:.2f}%")
            print("\nHoldings:")
            for holding in summary['holdings']:
                print(f"  {holding['symbol']}: {holding['quantity']} shares @ ${holding['current_price']:.2f} " +
                      f"(${holding['market_value']:.2f}, {holding['gain_loss_percent']:.2f}%)")
                
        elif choice == '2':
            symbol = input("Enter stock symbol: ").strip().upper()
            quantity = float(input("Enter quantity: ").strip())
            price = float(input("Enter purchase price per share: ").strip())
            success = self.portfolio_manager.add_holding(symbol, quantity, price)
            print(f"Holding {'added successfully' if success else 'could not be added'}")
            
        elif choice == '3':
            print("\nRisk Profile Options: conservative, moderate, aggressive")
            risk = input("Enter risk profile: ").strip().lower()
            horizon = input("Enter investment horizon (short/medium/long): ").strip().lower()
            success = self.portfolio_manager.update_preferences({
                "risk_profile": risk,
                "investment_horizon": horizon
            })
            print(f"Preferences {'updated successfully' if success else 'could not be updated'}")
            
        elif choice != '4':
            print("Invalid option, returning to main chat")
    
    def _handle_market_commands(self):
        """Handle market data commands."""
        print("\n📈 Market Data")
        print("1. Get stock quote")
        print("2. Get market news")
        print("3. Back to main chat")
        
        choice = input("Select an option (1-3): ").strip()
        
        if choice == '1':
            symbols = input("Enter stock symbols (comma-separated): ").strip().upper()
            symbols_list = [s.strip() for s in symbols.split(',') if s.strip()]
            
            for symbol in symbols_list:
                data = self.market_data.fetch_stock_data(symbol)
                if data:
                    print(f"\n{symbol}: ${data['price']} ({data['change_percent']})")
                    print(f"Volume: {data['volume']}")
                else:
                    print(f"\nNo data found for {symbol}")
                    
        elif choice == '2':
            news = self.market_data.fetch_market_news()
            if news:
                print("\n=== Latest Market News ===")
                for i, item in enumerate(news, 1):
                    print(f"\n{i}. {item['title']}")
                    print(f"   {item['summary'][:150]}...")
            else:
                print("\nNo news available at the moment")
                
        elif choice != '3':
            print("Invalid option, returning to main chat")

def main():
    """Main entry point for the enhanced chatbot."""
    parser = argparse.ArgumentParser(description='Enhanced Finance Chatbot')
    parser.add_argument('--user_id', type=str, help='User ID for personalization')
    parser.add_argument('--api', action='store_true', help='Start API server')
    parser.add_argument('--api_port', type=int, default=5000, help='API server port')
    
    args = parser.parse_args()
    
    # Start API server if requested
    if args.api:
        api_thread = start_api_server_in_thread(port=args.api_port)
        print(f"API server running at http://localhost:{args.api_port}/")
        
    # Create and run chatbot
    chatbot = FinanceChatbot(user_id=args.user_id)
    chatbot.run_interactive()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
