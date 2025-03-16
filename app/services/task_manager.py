from celery import Celery
from typing import List, Dict, Any
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from app.core.config import get_settings
import json
from loguru import logger

settings = get_settings()

# Initialize Celery
celery_app = Celery(
    'finance_chatbot',
    broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0',
    backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0'
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,  # One task per worker
    task_routes={
        'app.services.task_manager.*': {'queue': 'finance_tasks'}
    }
)

@celery_app.task(name="batch_market_analysis")
def batch_market_analysis(symbols: List[str]) -> Dict[str, Any]:
    """Process multiple stock symbols in parallel"""
    try:
        results = {}
        for symbol in symbols:
            # Fetch data
            stock = yf.Ticker(symbol)
            hist = stock.history(period='1mo')
            
            if hist.empty:
                results[symbol] = {"error": "No data available"}
                continue
                
            # Calculate key metrics
            latest = hist.iloc[-1]
            month_change = ((latest['Close'] - hist.iloc[0]['Close']) / hist.iloc[0]['Close']) * 100
            
            results[symbol] = {
                "current_price": round(latest['Close'], 2),
                "volume": int(latest['Volume']),
                "month_change": round(month_change, 2),
                "high": round(hist['High'].max(), 2),
                "low": round(hist['Low'].min(), 2),
                "volatility": round(hist['Close'].std(), 2)
            }
            
        return results
    except Exception as e:
        logger.error(f"Error in batch market analysis: {str(e)}")
        return {"error": str(e)}

@celery_app.task(name="update_knowledge_base")
def update_knowledge_base(category: str) -> Dict[str, Any]:
    """Update knowledge base with latest financial data"""
    try:
        if category == "market_news":
            # Fetch major market indices
            indices = ['^GSPC', '^DJI', '^IXIC']  # S&P 500, Dow Jones, NASDAQ
            data = {}
            
            for index in indices:
                ticker = yf.Ticker(index)
                info = ticker.info
                data[index] = {
                    "name": info.get('shortName', ''),
                    "current": info.get('regularMarketPrice', 0),
                    "change": info.get('regularMarketChangePercent', 0),
                    "volume": info.get('regularMarketVolume', 0)
                }
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
                "status": "success"
            }
            
        elif category == "economic_indicators":
            # You would typically fetch from an economic data API
            # This is a placeholder
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Economic indicators update scheduled",
                "status": "scheduled"
            }
            
        else:
            return {
                "error": f"Unknown category: {category}"
            }
            
    except Exception as e:
        logger.error(f"Error updating knowledge base: {str(e)}")
        return {"error": str(e)}

@celery_app.task(name="generate_market_report")
def generate_market_report(timeframe: str = "daily") -> Dict[str, Any]:
    """Generate comprehensive market report"""
    try:
        # Fetch major indices data
        indices = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^IXIC': 'NASDAQ',
            '^VIX': 'VIX'
        }
        
        report_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "timeframe": timeframe,
            "market_summary": {},
            "sector_performance": {},
            "risk_indicators": {}
        }
        
        # Get indices performance
        for symbol, name in indices.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='5d')
            if not hist.empty:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2]
                change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
                
                report_data["market_summary"][name] = {
                    "price": round(latest['Close'], 2),
                    "change": round(change, 2),
                    "volume": int(latest['Volume'])
                }
        
        # Add risk analysis
        vix_data = report_data["market_summary"].get("VIX", {})
        if vix_data:
            risk_level = "High" if vix_data["price"] > 30 else "Moderate" if vix_data["price"] > 20 else "Low"
            report_data["risk_indicators"]["market_volatility"] = {
                "level": risk_level,
                "vix": vix_data["price"]
            }
        
        return report_data
        
    except Exception as e:
        logger.error(f"Error generating market report: {str(e)}")
        return {"error": str(e)}
