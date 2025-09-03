import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import time
import random
from typing import List, Dict, Any
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsCollector:
    def __init__(self):
        self.config = Config()
        self.session = self._create_session()
        # Define excluded categories
        self.excluded_categories = [
            'entertainment', 'sports', 'celebrity', 'bollywood', 'hollywood',
            'cricket', 'football', 'tennis', 'movies', 'music', 'fashion',
            'lifestyle', 'gossip', 'celebrity news', 'film', 'actor', 'actress'
        ]
        
    def _create_session(self) -> requests.Session:
        """Create a session with retry mechanism"""
        session = requests.Session()
        
        # Configure retries
        retry_strategy = Retry(
            total=3,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504]  # HTTP status codes to retry on
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default timeout and headers
        session.timeout = (5, 15)  # (connect timeout, read timeout)
        session.headers.update({
            'User-Agent': random.choice(self.config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        
        return session

    def get_all_news(self) -> Dict[str, List[Dict[str, Any]]]:
        """Collect top news stories from last 24 hours from all sources"""
        try:
            news_data = {
                'global': self.get_global_news(),
                'india': self.get_india_news(),
                'business': self.get_business_news(),
                'regional': self.get_regional_news()
            }
            
            # Validate collected data
            for category, items in news_data.items():
                if not items:
                    logger.warning(f"No news items collected for category: {category}")
                    news_data[category] = self._get_fallback_news(category)
                    
            return news_data
            
        except Exception as e:
            logger.error(f"Error collecting all news: {str(e)}")
            return self._get_fallback_news_data()

    def _parse_rss_feed(self, feed_url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Parse RSS feed with improved error handling and validation"""
        items = []
        try:
            # Validate feed URL
            if not feed_url.startswith(('http://', 'https://')):
                logger.error(f"Invalid feed URL: {feed_url}")
                return items

            # Parse feed with timeout
            feed = feedparser.parse(feed_url, timeout=10)
            
            # Validate feed structure
            if not hasattr(feed, 'entries') or not feed.entries:
                logger.warning(f"No entries found in feed: {feed_url}")
                return items
            
            if hasattr(feed, 'status') and feed.status != 200:
                logger.warning(f"Feed returned status {feed.status}: {feed_url}")
                return items

            for entry in feed.entries[:limit]:
                try:
                    item = self._process_feed_entry(entry, feed_url, feed)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.warning(f"Error processing feed entry: {str(e)}")
                    continue

            return items

        except Exception as e:
            logger.error(f"Error parsing RSS feed {feed_url}: {str(e)}")
            return items

    def _process_feed_entry(self, entry: Any, feed_url: str, feed: Any) -> Dict[str, Any]:
        """Process individual feed entries with validation"""
        try:
            # Validate required fields
            if not hasattr(entry, 'title') or not entry.title:
                return None

            # Clean and validate description
            description = self._get_clean_description(entry)
            
            # Get and validate publication date
            published_timestamp = self._parse_date_to_timestamp(
                getattr(entry, 'published', '') or 
                getattr(entry, 'updated', datetime.now().isoformat())
            )
            
            # Get source name
            source_name = self._determine_source_name(feed_url, feed)
            
            # Validate and clean URL
            url = self._validate_and_clean_url(
                getattr(entry, 'link', ''), 
                feed_url
            )

            return {
                'title': entry.title[:200],  # Limit title length
                'description': description,
                'url': url,
                'source': source_name,
                'published': datetime.fromtimestamp(published_timestamp).isoformat(),
                'published_timestamp': published_timestamp,
                'category': self._categorize_news(entry.title, description)
            }

        except Exception as e:
            logger.warning(f"Error processing feed entry: {str(e)}")
            return None

    def _get_clean_description(self, entry: Any) -> str:
        """Clean and validate entry description"""
        try:
            # Get description or summary
            description = getattr(entry, 'description', '')
            summary = getattr(entry, 'summary', '')
            
            # Use the longer of description or summary
            content = summary if len(summary) > len(description) else description
            
            if content:
                # Remove HTML tags
                soup = BeautifulSoup(content, 'html.parser')
                clean_content = soup.get_text()
                
                # Truncate if too long
                if len(clean_content) > 200:
                    clean_content = clean_content[:200] + '...'
                    
                return clean_content
            
            return 'No description available'
            
        except Exception as e:
            logger.warning(f"Error cleaning description: {str(e)}")
            return 'Description unavailable'

    def _validate_and_clean_url(self, url: str, feed_url: str) -> str:
        """Validate and clean URLs"""
        if not url or url == '#':
            return feed_url
            
        # Ensure URL starts with http/https
        if not url.startswith(('http://', 'https://')):
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                # Get base URL from feed_url
                from urllib.parse import urlparse
                parsed = urlparse(feed_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                url = base_url + url
            else:
                url = feed_url
                
        return url

    def _get_fallback_news_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Provide fallback news data when collection fails"""
        current_time = datetime.now()
        fallback_item = {
            'title': 'Service Temporarily Unavailable',
            'description': 'Our news service is temporarily unavailable. Please try again later.',
            'url': 'https://example.com/news',
            'source': 'System',
            'published': current_time.isoformat(),
            'published_timestamp': current_time.timestamp(),
            'category': 'System'
        }
        
        return {
            'global': [fallback_item],
            'india': [fallback_item],
            'business': [fallback_item],
            'regional': [fallback_item]
        }

    # ... (rest of the methods remain the same but with improved error handling)
