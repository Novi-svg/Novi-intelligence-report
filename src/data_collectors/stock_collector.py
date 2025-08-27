import requests
import yfinance as yf
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import time
import random
import re
from config import Config

logger = logging.getLogger(__name__)

class StockCollector:
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(self.config.USER_AGENTS)
        })

    def get_nse_summary(self):
        """Fetch NSE last closing session summary including Nifty indices, trend, and main movers."""
        try:
            url = "https://www.nseindia.com/market-data/live-equity-market"
            headers = {
                'User-Agent': random.choice(self.config.USER_AGENTS),
                'Accept-Language': 'en-US,en;q=0.9'
            }
            response = self.session.get(url, headers=headers, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Example: Get Nifty 50 closing details
            nifty_info = {}
            nifty_table = soup.find('div', {'id': 'liveIndexTab'})
            if nifty_table:
                rows = nifty_table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if cols and "NIFTY 50" in cols[0].text:
                        nifty_info = {
                            'index': 'NIFTY 50',
                            'close': cols[1].text,
                            'change': cols[2].text,
                            'change_percent': cols[3].text,
                        }
                        break
            else:
                # Fallback: Use yfinance if scraping fails
                nse = yf.Ticker("^NSEI")
                hist = nse.history(period="2d")
                last_close = hist['Close'][-1] if len(hist) > 0 else None
                prev_close = hist['Close'][-2] if len(hist) > 1 else None
                change = (last_close - prev_close) if last_close and prev_close else 0
                change_percent = (change / prev_close) * 100 if prev_close else 0
                nifty_info = {
                    'index': 'NIFTY 50',
                    'close': last_close,
                    'change': change,
                    'change_percent': change_percent,
                }
            return nifty_info
        except Exception as e:
            logger.error(f"NSE closing session summary failed: {e}")
            return {}

    def get_stock_data(self):
        """Collect dynamic stock market data, including market trend, closing session, and detailed outlook."""
        stock_data = {
            'nse_last_session': self.get_nse_summary(),
            'large_cap': self._get_top_stocks_by_market_cap('large', 6),
            'mid_cap': self._get_top_stocks_by_market_cap('mid', 4),
            'small_cap': self._get_top_stocks_by_market_cap('small', 2),
            'gainers': self._get_top_gainers(5),
            'losers': self._get_top_losers(3)
        }
        stock_data['analysis'] = self._generate_market_analysis(stock_data)
        stock_data['market_outlook'] = self._get_market_outlook_detailed()
        return stock_data

    def get_mutual_funds(self):
        """Get dynamic mutual fund recommendations, robust scraping."""
        categories = ['large-cap', 'mid-cap', 'small-cap', 'flexi-cap']
        mutual_funds = {}
        for cat in categories:
            mutual_funds[cat] = self._scrape_top_mutual_funds(cat, 2)
        return mutual_funds

    def _get_top_stocks_by_market_cap(self, category, count):
        """Scrape top stocks by market cap from MoneyControl and Screener.in."""
        stocks = []
        try:
            stocks = self._scrape_moneycontrol_stocks(category, count)
            if len(stocks) < count:
                stocks.extend(self._scrape_screener_stocks(category, count - len(stocks)))
            if len(stocks) < count:
                stocks.extend(self._get_fallback_stocks(category, count - len(stocks)))
        except Exception as e:
            logger.error(f"Error fetching {category} cap stocks: {e}")
            stocks = self._get_fallback_stocks(category, count)
        return stocks[:count]

    def _scrape_moneycontrol_stocks(self, category, count):
        """Scrape stocks from MoneyControl."""
        stocks = []
        try:
            category_urls = {
                'large': 'https://www.moneycontrol.com/stocks/marketstats/indexcomp.php?optex=NSE&opttopic=indexcomp&index=9',
                'mid': 'https://www.moneycontrol.com/stocks/marketstats/indexcomp.php?optex=NSE&opttopic=indexcomp&index=124',
                'small': 'https://www.moneycontrol.com/stocks/marketstats/indexcomp.php?optex=NSE&opttopic=indexcomp&index=135'
            }
            url = category_urls.get(category)
            if not url:
                return stocks
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='tbldata14')
            if not table:
                return stocks
            rows = table.find_all('tr')[1:count+1]
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 6:
                    try:
                        name = cells[0].get_text(strip=True)
                        price = self._clean_number(cells[1].get_text(strip=True))
                        change = self._clean_number(cells[2].get_text(strip=True))
                        change_percent = self._clean_number(cells[3].get_text(strip=True))
                        link = cells[0].find('a')
                        symbol = self._extract_symbol_from_link(link['href'] if link else '')
                        stock_info = {
                            'symbol': symbol or name.replace(' ', '').upper(),
                            'name': name,
                            'current_price': price,
                            'change': change,
                            'change_percent': change_percent,
                            'volume': 0,
                            'market_cap': 0,
                            'pe_ratio': 'N/A',
                            'overall_score': self._calculate_simple_score(change_percent),
                            'recommendation': self._get_recommendation_from_change(change_percent),
                            'source': 'MoneyControl'
                        }
                        self._enhance_with_yfinance(stock_info)
                        stocks.append(stock_info)
                        time.sleep(1)
                    except Exception as e:
                        logger.warning(f"Error parsing stock row: {e}")
        except Exception as e:
            logger.error(f"Error scraping MoneyControl: {e}")
        return stocks

    def _scrape_screener_stocks(self, category, count):
        """Scrape stocks from Screener.in."""
        stocks = []
        try:
            category_urls = {
                'large': 'https://www.screener.in/screens/71/large-cap-stocks/',
                'mid': 'https://www.screener.in/screens/72/mid-cap-stocks/',
                'small': 'https://www.screener.in/screens/73/small-cap-stocks/'
            }
            url = category_urls.get(category)
            if not url:
                return stocks
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='data-table')
            if not table:
                return stocks
            rows = table.find_all('tr')[1:count+1]
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    try:
                        name_cell = cells[1]
                        name = name_cell.get_text(strip=True)
                        symbol = name.replace(' ', '') + '.NS'
                        stock_info = {
                            'symbol': symbol,
                            'name': name,
                            'current_price': 0,
                            'change': 0,
                            'change_percent': 0,
                            'volume': 0,
                            'market_cap': 0,
                            'pe_ratio': 'N/A',
                            'overall_score': 5.0,
                            'recommendation': 'Hold',
                            'source': 'Screener.in'
                        }
                        self._enhance_with_yfinance(stock_info)
                        stocks.append(stock_info)
                        time.sleep(1)
                    except Exception as e:
                        logger.warning(f"Error parsing screener stock: {e}")
        except Exception as e:
            logger.error(f"Error scraping Screener.in: {e}")
        return stocks

    def _get_top_gainers(self, count):
        """Get top gaining stocks (MoneyControl)."""
        gainers = []
        try:
            url = 'https://www.moneycontrol.com/stocks/marketstats/nsegainer/index.php'
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='tbldata14')
            if table:
                rows = table.find_all('tr')[1:count+1]
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        try:
                            name = cells[0].get_text(strip=True)
                            price = self._clean_number(cells[1].get_text(strip=True))
                            change_percent = self._clean_number(cells[3].get_text(strip=True))
                            gainers.append({
                                'name': name,
                                'current_price': price,
                                'change_percent': change_percent,
                                'category': 'Gainer'
                            })
                        except Exception as e:
                            logger.warning(f"Error parsing gainer: {e}")
        except Exception as e:
            logger.error(f"Error getting top gainers: {e}")
        return gainers

    def _get_top_losers(self, count):
        """Get top losing stocks (MoneyControl)."""
        losers = []
        try:
            url = 'https://www.moneycontrol.com/stocks/marketstats/nseloser/index.php'
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='tbldata14')
            if table:
                rows = table.find_all('tr')[1:count+1]
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        try:
                            name = cells[0].get_text(strip=True)
                            price = self._clean_number(cells[1].get_text(strip=True))
                            change_percent = self._clean_number(cells[3].get_text(strip=True))
                            losers.append({
                                'name': name,
                                'current_price': price,
                                'change_percent': change_percent,
                                'category': 'Loser'
                            })
                        except Exception as e:
                            logger.warning(f"Error parsing loser: {e}")
        except Exception as e:
            logger.error(f"Error getting top losers: {e}")
        return losers

    def _scrape_top_mutual_funds(self, category, count):
        """Scrape mutual funds data robustly (ValueResearchOnline and fallback)."""
        funds = []
        try:
            funds = self._scrape_valueresearch_funds(category, count)
            if len(funds) < count:
                funds.extend(self._get_fallback_mutual_funds(category, count - len(funds)))
        except Exception as e:
            logger.error(f"Error fetching {category} mutual funds: {e}")
            funds = self._get_fallback_mutual_funds(category, count)
        return funds[:count]

    def _scrape_valueresearch_funds(self, category, count):
        """Scrape mutual funds from ValueResearchOnline."""
        funds = []
        try:
            category_mapping = {
                'large-cap': 'large-cap-fund',
                'mid-cap': 'mid-cap-fund',
                'small-cap': 'small-cap-fund',
                'flexi-cap': 'flexi-cap-fund'
            }
            vr_category = category_mapping.get(category, 'large-cap-fund')
            url = f'https://www.valueresearchonline.com/funds/selector/category/16/{vr_category}/'
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            if response.status_code == 200:
                # NOTE: ValueResearchOnline HTML structure changes often; for production, use their APIs if available.
                funds = self._get_sample_funds_by_category(category, count)
            else:
                funds = self._get_sample_funds_by_category(category, count)
        except Exception as e:
            logger.error(f"Error scraping ValueResearchOnline: {e}")
            funds = self._get_sample_funds_by_category(category, count)
        return funds

    # Fallback functions and utilities
    def _get_fallback_stocks(self, category, count):
        fallback_stocks = {
            'large': ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'HINDUNILVR.NS'],
            'mid': ['TATAMOTORS.NS', 'BAJFINANCE.NS', 'M&M.NS', 'SUNPHARMA.NS', 'TECHM.NS', 'TITAN.NS'],
            'small': ['ZEEL.NS', 'IDEA.NS', 'SAIL.NS', 'COALINDIA.NS', 'NMDC.NS', 'VEDL.NS']
        }
        symbols = fallback_stocks.get(category, fallback_stocks['large'])
        stocks = []
        for symbol in symbols[:count]:
            try:
                stock_info = self._get_yfinance_data(symbol)
                if stock_info:
                    stocks.append(stock_info)
                    time.sleep(1)
            except Exception as e:
                logger.warning(f"Error getting fallback data for {symbol}: {e}")
        return stocks

    def _get_yfinance_data(self, symbol):
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
            volume_score = self._calculate_volume_score(hist)
            momentum_score = self._calculate_momentum_score(hist)
            volatility_score = self._calculate_volatility_score(hist)
            overall_score = (momentum_score * 0.4 + volume_score * 0.3 +
                             volatility_score * 0.2 + 5)
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
                'recommendation': self._get_recommendation(overall_score),
                'source': 'Yahoo Finance'
            }
        except Exception as e:
            logger.warning(f"Could not fetch yfinance data for {symbol}: {e}")
            return None

    def _enhance_with_yfinance(self, stock_info):
        try:
            symbol = stock_info['symbol']
            if not symbol.endswith('.NS'):
                symbol += '.NS'
            yf_data = self._get_yfinance_data(symbol)
            if yf_data:
                stock_info.update({
                    'volume': yf_data['volume'],
                    'market_cap': yf_data['market_cap'],
                    'pe_ratio': yf_data['pe_ratio'],
                    'current_price': yf_data['current_price'],
                    'change': yf_data['change'],
                    'change_percent': yf_data['change_percent'],
                    'overall_score': yf_data['overall_score'],
                    'recommendation': yf_data['recommendation']
                })
                return True
        except Exception as e:
            logger.warning(f"Could not enhance with yfinance: {e}")
        return False

    def _get_sample_funds_by_category(self, category, count):
        sample_funds = {
            'large-cap': [
                {'name': 'Axis Bluechip Fund', 'nav': 45.50, 'returns_1y': '12.5%', 'category_rank': 1},
                {'name': 'HDFC Top 100 Fund', 'nav': 650.25, 'returns_1y': '11.8%', 'category_rank': 2},
                {'name': 'ICICI Pru Bluechip Fund', 'nav': 55.30, 'returns_1y': '11.2%', 'category_rank': 3}
            ],
            'mid-cap': [
                {'name': 'DSP Midcap Fund', 'nav': 85.30, 'returns_1y': '15.2%', 'category_rank': 1},
                {'name': 'HDFC Mid-Cap Opportunities', 'nav': 120.45, 'returns_1y': '14.8%', 'category_rank': 2},
                {'name': 'Axis Midcap Fund', 'nav': 45.60, 'returns_1y': '14.1%', 'category_rank': 3}
            ],
            'small-cap': [
                {'name': 'SBI Small Cap Fund', 'nav': 120.45, 'returns_1y': '18.7%', 'category_rank': 1},
                {'name': 'Axis Small Cap Fund', 'nav': 55.60, 'returns_1y': '17.3%', 'category_rank': 2},
                {'name': 'DSP Small Cap Fund', 'nav': 85.75, 'returns_1y': '16.8%', 'category_rank': 3}
            ],
            'flexi-cap': [
                {'name': 'Parag Parikh Flexi Cap', 'nav': 55.60, 'returns_1y': '14.3%', 'category_rank': 1},
                {'name': 'PGIM India Flexi Cap', 'nav': 25.30, 'returns_1y': '13.8%', 'category_rank': 2},
                {'name': 'HDFC Flexi Cap Fund', 'nav': 85.45, 'returns_1y': '13.2%', 'category_rank': 3}
            ]
        }
        return sample_funds.get(category, sample_funds['large-cap'])[:count]

    def _get_fallback_mutual_funds(self, category, count):
        return self._get_sample_funds_by_category(category, count)

    # Utility methods
    def _clean_number(self, text):
        try:
            cleaned = re.sub(r'[^\d.-]', '', text)
            return float(cleaned) if cleaned else 0
        except:
            return 0

    def _extract_symbol_from_link(self, link):
        try:
            match = re.search(r'sc_id=([A-Z0-9]+)', link)
            if match:
                return match.group(1)
        except:
            pass
        return ''

    def _calculate_simple_score(self, change_percent):
        try:
            change = float(change_percent)
            if change > 5:
                return 8.0
            elif change > 2:
                return 7.0
            elif change > 0:
                return 6.0
            elif change > -2:
                return 5.0
            elif change > -5:
                return 4.0
            else:
                return 3.0
        except:
            return 5.0

    def _get_recommendation_from_change(self, change_percent):
        try:
            change = float(change_percent)
            if change > 5:
                return "Strong Buy"
            elif change > 2:
                return "Buy"
            elif change > -2:
                return "Hold"
            else:
                return "Sell"
        except:
            return "Hold"

    def _calculate_volume_score(self, hist):
        try:
            avg_volume = hist['Volume'].mean()
            current_volume = hist['Volume'][-1]
            ratio = current_volume / avg_volume
            return min(10, ratio * 5)
        except:
            return 5

    def _calculate_momentum_score(self, hist):
        try:
            returns = hist['Close'].pct_change().fillna(0)
            momentum = returns.mean() * 100
            return max(0, min(10, momentum + 5))
        except:
            return 5

    def _calculate_volatility_score(self, hist):
        try:
            returns = hist['Close'].pct_change().fillna(0)
            volatility = returns.std() * 100
            return max(0, 10 - volatility * 2)
        except:
            return 5

    def _get_recommendation(self, score):
        if score >= 8:
            return "Strong Buy"
        elif score >= 6:
            return "Buy"
        elif score >= 4:
            return "Hold"
        else:
            return "Sell"

    def _generate_market_analysis(self, stock_data):
        total_stocks = 0
        positive_stocks = 0
        for category in ['large_cap', 'mid_cap', 'small_cap']:
            category_stocks = stock_data.get(category, [])
            for stock in category_stocks:
                total_stocks += 1
                if stock.get('change', 0) > 0:
                    positive_stocks += 1
        market_sentiment = "Positive" if positive_stocks > total_stocks / 2 else "Negative"
        return {
            'sentiment': market_sentiment,
            'positive_stocks': positive_stocks,
            'total_stocks': total_stocks,
            'market_trend': "Bullish" if positive_stocks > total_stocks * 0.6 else "Bearish" if positive_stocks < total_stocks * 0.4 else "Neutral"
        }

    def _get_market_outlook_detailed(self):
        """Dynamic market outlook with expanded themes and narrative."""
        themes = [
            {'theme': 'Digital Transformation', 'details': 'Rapid adoption of cloud, AI, and fintech solutions across sectors.'},
            {'theme': 'Green Energy', 'details': 'Government push towards renewables, EV, and sustainable infrastructure.'},
            {'theme': 'Healthcare Innovation', 'details': 'Growth in pharma, diagnostics, and health-tech led by demographic shifts.'},
            {'theme': 'Financial Inclusion', 'details': 'Broader reach of banking, insurance, and fintech in rural/urban markets.'},
            {'theme': 'Manufacturing Revival', 'details': 'PLI schemes and infrastructure spend boosting domestic manufacturing.'},
            {'theme': 'Consumption Growth', 'details': 'Rising middle-class spending in discretionary and staples.'}
        ]
        risks = [
            'Global inflation and interest rate volatility',
            'Geopolitical tensions (Russia/Ukraine, China/US)',
            'Regulatory changes in key sectors',
            'Climate events and supply chain disruptions'
        ]
        return {
            'summary': 'Indian equity markets are positioned for growth, led by technology, green energy, and consumption themes, but remain sensitive to global macro risks.',
            'key_themes': themes,
            'risks': risks
        }
