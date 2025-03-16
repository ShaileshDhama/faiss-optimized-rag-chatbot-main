import pandas as pd
import pandas_ta as ta
import yfinance as yf
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
from sklearn.preprocessing import StandardScaler
from loguru import logger

class MarketAnalysisService:
    def __init__(self):
        self.scaler = StandardScaler()
        self.technical_indicators = [
            'RSI', 'MACD', 'BB_UPPER', 'BB_LOWER', 'EMA_20', 'SMA_50'
        ]

    async def get_market_signals(self, symbol: str) -> Dict:
        """Get technical analysis signals for a given symbol"""
        try:
            # Fetch historical data
            stock = yf.Ticker(symbol)
            df = stock.history(period='6mo')
            
            if df.empty:
                return {"error": "No data available for symbol"}

            # Calculate technical indicators
            df.ta.rsi(length=14, append=True)
            df.ta.macd(append=True)
            df.ta.bbands(length=20, append=True)
            df.ta.ema(length=20, append=True)
            df.ta.sma(length=50, append=True)

            # Get latest values
            latest = df.iloc[-1]
            
            # Generate signals
            signals = {
                "RSI": {
                    "value": round(latest["RSI_14"], 2),
                    "signal": "Oversold" if latest["RSI_14"] < 30 else "Overbought" if latest["RSI_14"] > 70 else "Neutral"
                },
                "MACD": {
                    "value": round(latest["MACD_12_26_9"], 2),
                    "signal": "Bullish" if latest["MACD_12_26_9"] > latest["MACDs_12_26_9"] else "Bearish"
                },
                "Bollinger_Bands": {
                    "position": "Lower" if latest["Close"] < latest["BBL_20_2.0"] else "Upper" if latest["Close"] > latest["BBU_20_2.0"] else "Middle",
                    "volatility": round((latest["BBU_20_2.0"] - latest["BBL_20_2.0"]) / latest["BBM_20_2.0"] * 100, 2)
                },
                "Trend": {
                    "short_term": "Bullish" if latest["EMA_20"] > latest["SMA_50"] else "Bearish",
                    "momentum": round((latest["Close"] / latest["Close"].shift(20) - 1) * 100, 2)
                }
            }

            # Add market sentiment score
            signals["overall_sentiment"] = self._calculate_sentiment_score(signals)
            
            return signals

        except Exception as e:
            logger.error(f"Error in market analysis for {symbol}: {str(e)}")
            return {"error": str(e)}

    def _calculate_sentiment_score(self, signals: Dict) -> float:
        """Calculate overall market sentiment score (-1 to 1)"""
        score = 0.0
        
        # RSI contribution
        rsi = signals["RSI"]["value"]
        score += (rsi - 50) / 50  # Normalize to [-1, 1]
        
        # MACD contribution
        score += 0.5 if signals["MACD"]["signal"] == "Bullish" else -0.5
        
        # Bollinger Bands contribution
        if signals["Bollinger_Bands"]["position"] == "Lower":
            score += 0.3
        elif signals["Bollinger_Bands"]["position"] == "Upper":
            score -= 0.3
            
        # Trend contribution
        score += 0.5 if signals["Trend"]["short_term"] == "Bullish" else -0.5
        
        # Normalize final score to [-1, 1]
        return max(min(score / 2, 1), -1)

    async def get_market_report(self, symbol: str) -> str:
        """Generate a natural language market report"""
        signals = await self.get_market_signals(symbol)
        
        if "error" in signals:
            return f"Error analyzing {symbol}: {signals['error']}"
            
        sentiment_desc = (
            "strongly bearish" if signals["overall_sentiment"] < -0.6
            else "bearish" if signals["overall_sentiment"] < -0.2
            else "neutral" if signals["overall_sentiment"] < 0.2
            else "bullish" if signals["overall_sentiment"] < 0.6
            else "strongly bullish"
        )
        
        report = f"""Market Analysis Report for {symbol}:

Technical Indicators:
- RSI ({signals['RSI']['value']}): {signals['RSI']['signal']}
- MACD: {signals['MACD']['signal']} signal
- Bollinger Bands: Price in {signals['Bollinger_Bands']['position']} band with {signals['Bollinger_Bands']['volatility']}% volatility
- Trend: {signals['Trend']['short_term']} short-term trend with {signals['Trend']['momentum']}% momentum

Overall Market Sentiment: {sentiment_desc.title()} ({signals['overall_sentiment']:.2f})

Trading Implications:
{self._generate_trading_implications(signals)}
"""
        return report

    def _generate_trading_implications(self, signals: Dict) -> str:
        """Generate trading implications based on signals"""
        implications = []
        
        # RSI implications
        if signals["RSI"]["signal"] == "Oversold":
            implications.append("- Potential buying opportunity based on oversold RSI conditions")
        elif signals["RSI"]["signal"] == "Overbought":
            implications.append("- Consider taking profits or reducing position size")
            
        # MACD implications
        if signals["MACD"]["signal"] == "Bullish":
            implications.append("- MACD indicates positive momentum")
        else:
            implications.append("- MACD suggests caution as momentum is declining")
            
        # Bollinger Bands implications
        if signals["Bollinger_Bands"]["position"] == "Lower":
            implications.append("- Price at lower Bollinger Band suggests potential support level")
        elif signals["Bollinger_Bands"]["position"] == "Upper":
            implications.append("- Price at upper Bollinger Band indicates potential resistance")
            
        # Trend implications
        if signals["Trend"]["short_term"] == "Bullish":
            implications.append("- Short-term trend remains positive")
        else:
            implications.append("- Short-term trend shows weakness")
            
        return "\n".join(implications)
