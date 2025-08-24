import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
from config import Config

logger = logging.getLogger(__name__)

class NewsCollector:
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_all_news(self):
        """Collect news from all sources"""
        news_data = {
            'global': self.get_global_news(),
            'india': self.get_india_news(),
            'regional': self.get_regional_news()
        }
        return news_data
    
    def get_global_news(self):
        """Get global news from multiple sources"""
        news_items = []
        
        # News API method
        if self.config.NEWS_API_KEY:
            try:
                news_items.extend(self._get_news_from_api('general', 10))
            except Exception as e:
                logger.warning(f"News API failed: {e}")
        
        # RSS Fallback
        if len(news_items) < 5:
            news_items.extend(self._get_news_from_rss())
        
        return news_items[:10]  # Top 10
    
    def get_india_news(self):
        """Get India-specific news"""
        india_news = []
        
        # RSS feeds for Indian news
        indian_sources = [
            'https://feeds.feedburner.com/ndtvnews-top-stories',
            'https://www.thehindu.com/news/national/feeder/default.rss',
            'https://timesofindia.indiatimes.com/rssfeedstopstories.cms'
        ]
        
        for source in indian_sources:
            try:
                items = self._parse_rss_feed(source, limit=4)
                india_news.extend(items)
            except Exception as e:
                logger.warning(f"Failed to fetch from {source}: {e}")
        
        return india_news[:10]  # Top 10
    
    def get_regional_news(self):
        """Get regional news (AP & Bangalore)"""
        regional_news = []
        
        # You can add specific regional RSS feeds here
        regional_sources = [
            # Add AP and Bangalore specific news sources
        ]
        
        # For now, return some sample regional news
        regional_news = [
            {
                'title': 'Regional Development Updates',
                'description': 'Local infrastructure and development news',
                'url': '#',
                'source': 'Regional News',
                'published': datetime.now().isoformat()
            }
        ]
        
        return regional_news[:10]  # Top 10
    
    def _get_news_from_api(self, category, count=10):
        """Get news using News API"""
        url = 'https://newsapi.org/v2/top-headlines'
        params = {
            'apiKey': self.config.NEWS_API_KEY,
            'country': 'us',  # or 'in' for India
            'category': category,
            'pageSize': count,
            'sortBy': 'publishedAt'
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        news_items = []
        
        if data['status'] == 'ok':
            for article in data['articles']:
                news_items.append({
                    'title': article['title'],
                    'description': article['description'] or 'No description available',
                    'url': article['url'],
                    'source': article['source']['name'],
                    'published': article['publishedAt']
                })
        
        return news_items
    
    def _get_news_from_rss(self):
        """Fallback: Get news from RSS feeds"""
        rss_feeds = [
            'http://feeds.bbci.co.uk/news/rss.xml',
            'http://rss.cnn.com/rss/edition.rss',
            'https://feeds.reuters.com/reuters/topNews'
        ]
        
        news_items = []
        for feed_url in rss_feeds:
            try:
                items = self._parse_rss_feed(feed_url, limit=3)
                news_items.extend(items)
            except Exception as e:
                logger.warning(f"RSS feed {feed_url} failed: {e}")
        
        return news_items
    
    def _parse_rss_feed(self, feed_url, limit=10):
        """Parse RSS feed and extract news items"""
        try:
            feed = feedparser.parse(feed_url)
            items = []
            
            for entry in feed.entries[:limit]:
                # Clean description
                description = getattr(entry, 'description', 'No description')
                if description:
                    # Remove HTML tags from description
                    soup = BeautifulSoup(description, 'html.parser')
                    description = soup.get_text()[:200] + '...' if len(soup.get_text()) > 200 else soup.get_text()
                
                items.append({
                    'title': entry.title,
                    'description': description,
                    'url': entry.link,
                    'source': feed.feed.title if hasattr(feed.feed, 'title') else 'RSS Feed',
                    'published': getattr(entry, 'published', datetime.now().isoformat())
                })
            
            return items
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed {feed_url}: {e}")
            return []
