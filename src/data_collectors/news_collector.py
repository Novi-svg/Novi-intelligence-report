import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import random
from config import Config

logger = logging.getLogger(__name__)

class NewsCollector:
    EXCLUDED_CATEGORIES = [
        'entertainment', 'sports', 'celebrity', 'bollywood', 'hollywood', 'cricket', 'movie', 'music', 'film', 'showbiz', 'soccer', 'football', 'tennis'
    ]

    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(self.config.USER_AGENTS)
        })

    def get_top_stories(self):
        """Collect top stories from last 24 hours, exclude entertainment/sports/celebrity news"""
        news_data = {
            'global': self.get_filtered_news('global'),
            'india': self.get_filtered_news('india'),
            'business': self.get_filtered_news('business'),
            'regional': self.get_filtered_regional_news()
        }
        return news_data

    def get_filtered_news(self, source_key):
        news_items = []
        feeds = self.config.NEWS_SOURCES.get(source_key, [])
        for feed_url in feeds:
            try:
                items = self._parse_rss_feed(feed_url, limit=10)
                news_items.extend(items)
            except Exception as e:
                logger.warning(f"Failed to fetch news from {feed_url}: {e}")
        # Filter for last 24 hours & exclude unwanted categories
        news_items = [
            item for item in news_items
            if self._is_recent(item.get('published')) and not self._is_excluded(item)
        ]
        # Remove duplicates and sort by pub date
        news_items = self._remove_duplicates(news_items)
        news_items = sorted(news_items, key=lambda x: x.get('published', ''), reverse=True)
        return news_items[:10]

    def get_filtered_regional_news(self):
        regional_news = []
        regional_news.extend(self._scrape_ap_news())
        regional_news.extend(self._scrape_bangalore_news())
        # Filter for last 24 hours & exclude unwanted categories
        regional_news = [
            item for item in regional_news
            if self._is_recent(item.get('published')) and not self._is_excluded(item)
        ]
        if not regional_news:
            regional_news = self._get_sample_regional_news()
        return regional_news[:8]

    def _parse_rss_feed(self, feed_url, limit=10):
        try:
            feed = feedparser.parse(feed_url)
            items = []
            for entry in feed.entries[:limit]:
                content = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                soup = BeautifulSoup(content, 'html.parser')
                clean_content = soup.get_text()
                if len(clean_content) > 200:
                    clean_content = clean_content[:200] + '...'
                published = getattr(entry, 'published', '') or getattr(entry, 'updated', datetime.now().isoformat())
                source_name = getattr(feed.feed, 'title', 'RSS Feed')
                items.append({
                    'title': entry.title,
                    'description': clean_content,
                    'url': entry.link,
                    'source': source_name,
                    'published': published,
                    'category': self._categorize_news(entry.title, clean_content)
                })
            return items
        except Exception as e:
            logger.error(f"Error parsing RSS feed {feed_url}: {e}")
            return []

    def _scrape_ap_news(self):
        ap_news = []
        ap_sources = [
            'https://www.andhrajyothy.com',
            'https://www.eenadu.net',
            'https://www.sakshi.com'
        ]
        for source in ap_sources[:1]:
            try:
                response = self.session.get(source, timeout=self.config.REQUEST_TIMEOUT)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    headlines = soup.find_all(['h1', 'h2', 'h3'], limit=5)
                    for headline in headlines:
                        title = headline.get_text(strip=True)
                        if title and len(title) > 10:
                            ap_news.append({
                                'title': title,
                                'description': 'Regional news from Andhra Pradesh',
                                'url': source,
                                'source': 'AP News',
                                'published': datetime.now().isoformat(),
                                'category': self._categorize_news(title, 'Regional news from Andhra Pradesh')
                            })
            except Exception as e:
                logger.warning(f"Error scraping AP news from {source}: {e}")
        return ap_news

    def _scrape_bangalore_news(self):
        blr_news = []
        blr_sources = [
            'https://bangaloremirror.indiatimes.com',
            'https://www.deccanherald.com'
        ]
        for source in blr_sources[:1]:
            try:
                response = self.session.get(source, timeout=self.config.REQUEST_TIMEOUT)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    headlines = soup.find_all(['h1', 'h2', 'h3'], limit=5)
                    for headline in headlines:
                        title = headline.get_text(strip=True)
                        if title and len(title) > 10:
                            blr_news.append({
                                'title': title,
                                'description': 'Regional news from Bangalore',
                                'url': source,
                                'source': 'Bangalore News',
                                'published': datetime.now().isoformat(),
                                'category': self._categorize_news(title, 'Regional news from Bangalore')
                            })
            except Exception as e:
                logger.warning(f"Error scraping Bangalore news from {source}: {e}")
        return blr_news

    def _get_sample_regional_news(self):
        return [
            {
                'title': 'IT Sector Growth in Hyderabad and Bangalore',
                'description': 'Technology companies continue to expand operations in major South Indian cities',
                'url': '#',
                'source': 'Regional News',
                'published': datetime.now().isoformat(),
                'category': 'General'
            }
        ]

    def _remove_duplicates(self, news_items):
        unique_items = []
        seen_titles = set()
        for item in news_items:
            title = item['title'].lower().strip()
            simplified_title = ' '.join(sorted(title.split()[:5]))
            if simplified_title not in seen_titles:
                seen_titles.add(simplified_title)
                unique_items.append(item)
        return unique_items

    def _categorize_news(self, title, description):
        content = (title + ' ' + description).lower()
        if any(word in content for word in self.EXCLUDED_CATEGORIES):
            return 'Excluded'
        if any(word in content for word in ['stock', 'market', 'share', 'nse', 'bse', 'sensex', 'nifty']):
            return 'Markets'
        elif any(word in content for word in ['tech', 'technology', 'software', 'ai', 'digital']):
            return 'Technology'
        elif any(word in content for word in ['economy', 'gdp', 'inflation', 'fiscal', 'budget']):
            return 'Economy'
        elif any(word in content for word in ['politics', 'election', 'government', 'minister']):
            return 'Politics'
        elif any(word in content for word in ['health', 'medical', 'hospital', 'covid']):
            return 'Health'
        else:
            return 'General'

    def _is_recent(self, published):
        try:
            # Try parsing published date, fallback to now
            pub_dt = feedparser._parse_date(published)
            if pub_dt is None:
                pub_dt = datetime.now().timetuple()
            pub_date = datetime(*pub_dt[:6])
            return (datetime.now() - pub_date) < timedelta(days=1)
        except Exception:
            return True  # If can't parse, keep

    def _is_excluded(self, item):
        cat = item.get('category', '').lower()
        title = item.get('title', '').lower()
        desc = item.get('description', '').lower()
        for word in self.EXCLUDED_CATEGORIES:
            if word in cat or word in title or word in desc:
                return True
        return False
