import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import logging
from config import Config

logger = logging.getLogger(__name__)

class StockCollector:
    def __init__(self):
        self.config = Config()
        
    def get_stock_data(self):
        """Collect stock market data"""
        stock_data = {
            'large_cap': self._get_stocks_by_category('large_cap', 6),
            'mid_cap': self._get_stocks_by_category('mid_cap', 4),
            'small_cap': self._get_stocks_by_category('small_cap', 2)
        }
        
        # Add market analysis
        stock_data['analysis'] = self._generate_market_analysis(stock_data)
        
        return stock_data
    
    def get_mutual_funds(self):
        """Get mutual fund recommendations"""
        # This is a simplified version - you can enhance with real mutual fund APIs
        mutual_funds = {
            'large_cap': [
                {'name': 'Axis Bluechip Fund', 'nav': 45.50, 'returns_1y': '12.5%', 'category_rank': 1},
                {'name': 'HDFC Top 100 Fund', 'nav': 650.25, 'returns_1y': '11.8%', 'category_rank': 2}
            ],
            'mid_cap': [
                {'name': 'DSP Midcap Fund', 'nav': 85.30, 'returns_1y': '15.2%', 'category_rank': 1},
                {'name': 'HDFC Mid-Cap Opportunities', 'nav': 120.45, 'returns_1y': '14.8%', 'category_rank': 2}
            ],
            'small_cap': [
                {'name': 'SBI Small Cap Fund', 'nav': 120.45, 'returns_1y': '18.7%', 'category_rank': 1},
                {'name': 'Axis Small Cap Fund', 'nav': 55.60, 'returns_1y': '17.3%', 'category_rank': 2}
            ],
            'flexi_cap': [
                {'name': 'Parag Parikh Flexi Cap', 'nav': 55.60, 'returns_1y': '14.3%', 'category_rank': 1},
                {'name': 'PGIM India Flexi Cap', 'nav': 25.30, 'returns_1y': '13.8%', 'category_rank': 2}
            ]
        }
        
        return mutual_funds
    
    def get_investment_analysis(self):
        """Generate investment analysis"""
        analysis = {
            'allocation_strategy': {
                'large_cap': 40,
                'mid_cap': 25,
                'small_cap': 15,
                'flexi_cap': 20
            },
            'market_outlook': self._get_market_outlook(),
            'top_picks': self._get_top_investment_picks(),
            'risk_factors': self._get_current_risk_factors()
        }
        
        return analysis
    
    def _get_stocks_by_category(self, category, count):
        """Get stock data for specific category"""
        stocks = []
        stock_symbols = self.config.TOP_STOCKS.get(category, [])
        
        try:
            for symbol in stock_symbols[:count]:
                stock_info = self._get_stock_info(symbol)
                if stock_info:
                    stocks.append(stock_info)
        except Exception as e:
            logger.error(f"Error fetching {category} stocks: {e}")
        
        return stocks
    
    def _get_stock_info(self, symbol):
        """Get detailed information for a single stock"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="5d")
            info = stock.info
            
            if len(hist) < 2:
                return None
            
            current_price = hist['Close'][-1]
            prev_price = hist['Close'][-2]
            change = current_price - prev_price
            change_percent = (change / prev_price) * 100
            
            # Calculate simple scoring
            volume_score = self._calculate_volume_score(hist)
            momentum_score = self._calculate_momentum_score(hist)
            volatility_score = self._calculate_volatility_score(hist)
            
            overall_score = (momentum_score * 0.4 + volume_score * 0.3 + 
                           volatility_score * 0.2 + 5)  # Base score of 5
            
            return {
                'symbol': symbol.replace('.NS', ''),
                'name': info.get('longName', symbol),
                'current_price': round(current_price, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'volume': hist['Volume'][-1],
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'overall_score': round(overall_score, 1),
                'recommendation': self._get_recommendation(overall_score)
            }
            
        except Exception as e:
            logger.warning(f"Could not fetch data for {symbol}: {e}")
            return None
    
    def _calculate_volume_score(self, hist):
        """Calculate volume-based score (0-10)"""
        try:
            avg_volume = hist['Volume'].mean()
            current_volume = hist['Volume'][-1]
            ratio = current_volume / avg_volume
            return min(10, ratio * 5)  # Scale to 0-10
        except:
            return 5  # Neutral score
    
    def _calculate_momentum_score(self, hist):
        """Calculate momentum score (0-10)"""
        try:
            returns = hist['Close'].pct_change().fillna(0)
            momentum = returns.mean() * 100
            return max(0, min(10, momentum + 5))  # Scale to 0-10
        except:
            return 5  # Neutral score
    
    def _calculate_volatility_score(self, hist):
        """Calculate volatility score (0-10, lower volatility = higher score)"""
        try:
            returns = hist['Close'].pct_change().fillna(0)
            volatility = returns.std() * 100
            return max(0, 10 - volatility * 2)  # Invert so lower volatility = higher score
        except:
            return 5  # Neutral score
    
    def _get_recommendation(self, score):
        """Get recommendation based on score"""
        if score >= 8:
            return "Strong Buy"
        elif score >= 6:
            return "Buy"
        elif score >= 4:
            return "Hold"
        else:
            return "Sell"
    
    def _generate_market_analysis(self, stock_data):
        """Generate overall market analysis"""
        total_stocks = sum(len(stocks) for stocks in stock_data.values() if isinstance(stocks, list))
        positive_stocks = 0
        
        for category in ['large_cap', 'mid_cap', 'small_cap']:
            for stock in stock_data.get(category, []):
                if stock.get('change', 0) > 0:
                    positive_stocks += 1
        
        market_sentiment = "Positive" if positive_stocks > total_stocks / 2 else "Negative"
        
        return {
            'sentiment': market_sentiment,
            'positive_stocks': positive_stocks,
            'total_stocks': total_stocks,
            'market_trend': self._determine_market_trend()
        }
    
    def _determine_market_trend(self):
        """Determine current market trend"""
        # This is a simplified trend analysis
        # You can enhance this with technical indicators
        return "Bullish"  # Placeholder
    
    def _get_market_outlook(self):
        """Get market outlook for next 5 years"""
        return {
            'summary': "Indian markets expected to grow with focus on technology and renewable energy sectors",
            'key_themes': ['Digital transformation', 'Green energy', 'Healthcare innovation', 'Financial inclusion'],
            'risks': ['Global inflation', 'Geopolitical tensions', 'Regulatory changes']
        }
    
    def _get_top_investment_picks(self):
        """Get top investment picks for long-term"""
        return [
            {'sector': 'Technology', 'reason': 'Digital transformation driving growth'},
            {'sector': 'Healthcare', 'reason': 'Aging population and health awareness'},
            {'sector': 'Renewable Energy', 'reason': 'Government focus on clean energy'}
        ]
    
    def _get_current_risk_factors(self):
        """Get current market risk factors"""
        return [
            'Global economic slowdown concerns',
            'Rising interest rates',
            'Inflation pressures',
            'Geopolitical tensions'
        ]
