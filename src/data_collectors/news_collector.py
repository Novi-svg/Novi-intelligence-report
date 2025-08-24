import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import time
import random
from config import Config

logger = logging.getLogger(__name__)

class NewsCollector:
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(self.config.USER_AGENTS)
        })
    
    def get_all_news(self):
        """Collect news from all sources using RSS feeds only"""
        news_data = {
            'global': self.get_global_news(),
            'india': self.get_india_news(),
            'business': self.get_business_news(),
            'regional': self.get_regional_news()
        }
        return news_data
    
    def get_global_news(self):
        """Get global news from RSS feeds"""
        news_items = []
        
        for feed_url in self.config.NEWS_SOURCES['global']:
            try:
                items = self._parse_rss_feed(feed_url, limit=3)
                news_items.extend(items)
                time.sleep(self.config.REQUEST_DELAY)  # Rate limiting
            except Exception as e:
                logger.warning(f"Failed to fetch global news from {feed_url}: {e}")
        
        # Remove duplicates and sort by publication date
        news_items = self._remove_duplicates(news_items)
        news_items = sorted(news_items, key=lambda x: x.get('published', ''), reverse=True)
        
        return news_items[:10]  # Top 10
    
    def get_india_news(self):
        """Get India-specific news from RSS feeds"""
        news_items = []
        
        for feed_url in self.config.NEWS_SOURCES['india']:
            try:
                items = self._parse_rss_feed(feed_url, limit=3)
                news_items.extend(items)
                time.sleep(self.config.REQUEST_DELAY)
            except Exception as e:
                logger.warning(f"Failed to fetch India news from {feed_url}: {e}")
        
        news_items = self._remove_duplicates(news_items)
        news_items = sorted(news_items, key=lambda x: x.get('published', ''), reverse=True)
        
        return news_items[:10]  # Top 10
    
    def get_business_news(self):
        """Get business news from RSS feeds"""
        news_items = []
        
        for feed_url in self.config.NEWS_SOURCES['business']:
            try:
                items = self._parse_rss_feed(feed_url, limit=4)
                news_items.extend(items)
                time.sleep(self.config.REQUEST_DELAY)
            except Exception as e:
                logger.warning(f"Failed to fetch business news from {feed_url}: {e}")
        
        news_items = self._remove_duplicates(news_items)
        news_items = sorted(news_items, key=lambda x: x.get('published', ''), reverse=True)
        
        return news_items[:8]  # Top 8
    
    def get_regional_news(self):
        """Get regional news (AP & Bangalore) by web scraping"""
        regional_news = []
        
        # Scrape regional news from various sources
        regional_news.extend(self._scrape_ap_news())
        regional_news.extend(self._scrape_bangalore_news())
        
        if not regional_news:
            # Fallback to sample regional news
            regional_news = self._get_sample_regional_news()
        
        return regional_news[:8]  # Top 8
    
    def _parse_rss_feed(self, feed_url, limit=10):
        """Parse RSS feed and extract news items"""
        try:
            # Use feedparser for RSS
            feed = feedparser.parse(feed_url)
            items = []
            
            if not feed.entries:
                logger.warning(f"No entries found in RSS feed: {feed_url}")
                return items
            
            for entry in feed.entries[:limit]:
                # Clean description
                description = getattr(entry, 'description', 'No description')
                summary = getattr(entry, 'summary', description)
                
                # Use the longer of description or summary
                content = summary if len(summary) > len(description) else description
                
                if content:
                    # Remove HTML tags from content
                    soup = BeautifulSoup(content, 'html.parser')
                    clean_content = soup.get_text()
                    # Truncate if too long
                    if len(clean_content) > 200:
                        clean_content = clean_content[:200] + '...'
                else:
                    clean_content = 'No description available'
                
                # Get publication date
                published = getattr(entry, 'published', '')
                if not published:
                    published = getattr(entry, 'updated', datetime.now().isoformat())
                
                # Get source name from feed
                source_name = 'RSS Feed'
                if hasattr(feed.feed, 'title'):
                    source_name = feed.feed.title
                elif 'bbc' in feed_url.lower():
                    source_name = 'BBC News'
                elif 'cnn' in feed_url.lower():
                    source_name = 'CNN'
                elif 'reuters' in feed_url.lower():
                    source_name = 'Reuters'
                elif 'ndtv' in feed_url.lower():
                    source_name = 'NDTV'
                elif 'thehindu' in feed_url.lower():
                    source_name = 'The Hindu'
                elif 'timesofindia' in feed_url.lower():
                    source_name = 'Times of India'
                elif 'economictimes' in feed_url.lower():
                    source_name = 'Economic Times'
                elif 'business-standard' in feed_url.lower():
                    source_name = 'Business Standard'
                elif 'livemint' in feed_url.lower():
                    source_name = 'Live Mint'
                
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
        """Scrape Andhra Pradesh specific news"""
        ap_news = []
        
        try:
            # Try scraping from AP news websites
            ap_sources = [
                'https://www.andhrajyothy.com',
                'https://www.eenadu.net',
                'https://www.sakshi.com'
            ]
            
            for source in ap_sources[:1]:  # Try first source only to avoid overloading
                try:
                    response = self.session.get(source, timeout=self.config.REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for news headlines (this is a simplified approach)
                        headlines = soup.find_all(['h1', 'h2', 'h3'], limit=3)
                        
                        for headline in headlines:
                            title = headline.get_text(strip=True)
                            if title and len(title) > 10:  # Filter out very short titles
                                ap_news.append({
                                    'title': title,
                                    'description': 'Regional news from Andhra Pradesh',
                                    'url': source,
                                    'source': 'AP News',
                                    'published': datetime.now().isoformat(),
                                    'category': 'Regional'
                                })
                        
                        break  # Success, no need to try other sources
                        
                except Exception as e:
                    logger.warning(f"Error scraping AP news from {source}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in AP news scraping: {e}")
        
        return ap_news
    
    def _scrape_bangalore_news(self):
        """Scrape Bangalore specific news"""
        blr_news = []
        
        try:
            # Try scraping from Bangalore news sources
            blr_sources = [
                'https://bangaloremirror.indiatimes.com',
                'https://www.deccanherald.com'
            ]
            
            for source in blr_sources[:1]:  # Try first source only
                try:
                    response = self.session.get(source, timeout=self.config.REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for news headlines
                        headlines = soup.find_all(['h1', 'h2', 'h3'], limit=3)
                        
                        for headline in headlines:
                            title = headline.get_text(strip=True)
                            if title and len(title) > 10:
                                blr_news.append({
                                    'title': title,
                                    'description': 'Regional news from Bangalore',
                                    'url': source,
                                    'source': 'Bangalore News',
                                    'published': datetime.now().isoformat(),
                                    'category': 'Regional'
                                })
                        
                        break
                        
                except Exception as e:
                    logger.warning(f"Error scraping Bangalore news from {source}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in Bangalore news scraping: {e}")
        
        return blr_news
    
    def _get_sample_regional_news(self):
        """Fallback regional news when scraping fails"""
        return [
            {
                'title': 'IT Sector Growth in Hyderabad and Bangalore',
                'description': 'Technology companies continue to expand operations in major South Indian cities',
                'url': '#',
                'source': 'Regional News',
                'published': datetime.now().isoformat(),
                'category': 'Regional'
            },
            {
                'title': 'Infrastructure Development Updates',
                'description': 'Metro rail and road infrastructure projects showing progress in regional cities',
                'url': '#',
                'source': 'Regional News',
                'published': datetime.now().isoformat(),
                'category': 'Regional'
            },
            {
                'title': 'Educational Initiatives in Andhra Pradesh',
                'description': 'State government launches new educational and skill development programs',
                'url': '#',
                'source': 'Regional News',
                'published': datetime.now().isoformat(),
                'category': 'Regional'
            }
        ]
    
    def _remove_duplicates(self, news_items):
        """Remove duplicate news items based on title similarity"""
        unique_items = []
        seen_titles = set()
        
        for item in news_items:
            title = item['title'].lower().strip()
            # Create a simplified title for comparison
            simplified_title = ' '.join(sorted(title.split()[:5]))  # First 5 words, sorted
            
            if simplified_title not in seen_titles:
                seen_titles.add(simplified_title)
                unique_items.append(item)
        
        return unique_items
    
    def _categorize_news(self, title, description):
        """Categorize news based on title and description"""
        content = (title + ' ' + description).lower()
        
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
    
    def get_trending_topics(self):
        """Extract trending topics from news headlines"""
        try:
            all_news = []
            all_news.extend(self.get_global_news())
            all_news.extend(self.get_india_news())
            all_news.extend(self.get_business_news())
            
            # Extract keywords from titles
            keywords = {}
            for news in all_news:
                words = news['title'].lower().split()
                for word in words:
                    if len(word) > 4 and word.isalpha():  # Only consider meaningful words
                        keywords[word] = keywords.get(word, 0) + 1
            
            # Get top trending keywords
            trending = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
            return [{'keyword': word, 'mentions': count} for word, count in trending]
            
        except Exception as e:
            logger.error(f"Error extracting trending topics: {e}")
            return []
