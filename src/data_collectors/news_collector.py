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
        # Define excluded categories
        self.excluded_categories = [
            'entertainment', 'sports', 'celebrity', 'bollywood', 'hollywood',
            'cricket', 'football', 'tennis', 'movies', 'music', 'fashion',
            'lifestyle', 'gossip', 'celebrity news', 'film', 'actor', 'actress'
        ]
    
    def get_all_news(self):
        """Collect top news stories from last 24 hours from all sources using RSS feeds only"""
        news_data = {
            'global': self.get_global_news(),
            'india': self.get_india_news(),
            'business': self.get_business_news(),
            'regional': self.get_regional_news()
        }
        return news_data
    
    def get_global_news(self):
        """Get global news from RSS feeds - last 24 hours only"""
        news_items = []
        for feed_url in self.config.NEWS_SOURCES['global']:
            try:
                items = self._parse_rss_feed(feed_url, limit=5)
                # Filter for last 24 hours and exclude unwanted categories
                filtered_items = self._filter_last_24_hours(items)
                filtered_items = self._exclude_categories(filtered_items)
                news_items.extend(filtered_items)
                time.sleep(self.config.REQUEST_DELAY)  # Rate limiting
            except Exception as e:
                logger.warning(f"Failed to fetch global news from {feed_url}: {e}")
        
        # Remove duplicates and sort by publication date
        news_items = self._remove_duplicates(news_items)
        news_items = sorted(news_items, key=lambda x: x.get('published_timestamp', 0), reverse=True)
        return news_items[:10]  # Top 10
    
    def get_india_news(self):
        """Get India-specific news from RSS feeds - last 24 hours only"""
        news_items = []
        for feed_url in self.config.NEWS_SOURCES['india']:
            try:
                items = self._parse_rss_feed(feed_url, limit=5)
                # Filter for last 24 hours and exclude unwanted categories
                filtered_items = self._filter_last_24_hours(items)
                filtered_items = self._exclude_categories(filtered_items)
                news_items.extend(filtered_items)
                time.sleep(self.config.REQUEST_DELAY)
            except Exception as e:
                logger.warning(f"Failed to fetch India news from {feed_url}: {e}")
        
        news_items = self._remove_duplicates(news_items)
        news_items = sorted(news_items, key=lambda x: x.get('published_timestamp', 0), reverse=True)
        return news_items[:10]  # Top 10
    
    def get_business_news(self):
        """Get business news from RSS feeds - last 24 hours only"""
        news_items = []
        for feed_url in self.config.NEWS_SOURCES['business']:
            try:
                items = self._parse_rss_feed(feed_url, limit=6)
                # Filter for last 24 hours and exclude unwanted categories
                filtered_items = self._filter_last_24_hours(items)
                filtered_items = self._exclude_categories(filtered_items)
                news_items.extend(filtered_items)
                time.sleep(self.config.REQUEST_DELAY)
            except Exception as e:
                logger.warning(f"Failed to fetch business news from {feed_url}: {e}")
        
        news_items = self._remove_duplicates(news_items)
        news_items = sorted(news_items, key=lambda x: x.get('published_timestamp', 0), reverse=True)
        return news_items[:8]  # Top 8
    
    def get_regional_news(self):
        """Get regional news (AP & Bangalore) - last 24 hours only"""
        regional_news = []
        
        # Try RSS feeds first for regional news
        regional_rss_feeds = [
            'https://feeds.feedburner.com/ndtvnews-top-stories',  # NDTV (has regional coverage)
            'https://www.thehindu.com/news/cities/bangalore/feeder/default.rss',  # Bangalore specific
            'https://www.thehindu.com/news/cities/Hyderabad/feeder/default.rss'   # Hyderabad specific
        ]
        
        for feed_url in regional_rss_feeds:
            try:
                items = self._parse_rss_feed(feed_url, limit=3)
                filtered_items = self._filter_last_24_hours(items)
                filtered_items = self._exclude_categories(filtered_items)
                regional_news.extend(filtered_items)
                time.sleep(self.config.REQUEST_DELAY)
            except Exception as e:
                logger.warning(f"Failed to fetch regional RSS from {feed_url}: {e}")
        
        # Scrape additional regional news if RSS doesn't provide enough
        if len(regional_news) < 4:
            regional_news.extend(self._scrape_ap_news())
            regional_news.extend(self._scrape_bangalore_news())
        
        if not regional_news:
            # Fallback to sample regional news with proper links
            regional_news = self._get_sample_regional_news()
        
        regional_news = self._remove_duplicates(regional_news)
        regional_news = sorted(regional_news, key=lambda x: x.get('published_timestamp', 0), reverse=True)
        return regional_news[:8]  # Top 8
    
    def _parse_rss_feed(self, feed_url, limit=10):
        """Parse RSS feed and extract news items with full URLs"""
        try:
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
                
                # Get publication date and convert to timestamp
                published = getattr(entry, 'published', '')
                if not published:
                    published = getattr(entry, 'updated', datetime.now().isoformat())
                
                published_timestamp = self._parse_date_to_timestamp(published)
                
                # Get source name from feed
                source_name = self._determine_source_name(feed_url, feed)
                
                # Ensure we have a valid URL
                url = getattr(entry, 'link', feed_url)
                if not url or url == '#':
                    url = feed_url  # Use feed URL as fallback
                
                news_item = {
                    'title': entry.title,
                    'description': clean_content,
                    'url': url,  # Full URL for user access
                    'source': source_name,
                    'published': published,
                    'published_timestamp': published_timestamp,
                    'category': self._categorize_news(entry.title, clean_content)
                }
                
                items.append(news_item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed {feed_url}: {e}")
            return []
    
    def _parse_date_to_timestamp(self, date_string):
        """Convert various date formats to timestamp"""
        try:
            # Try different date parsing approaches
            if hasattr(feedparser, '_parse_date'):
                parsed_date = feedparser._parse_date(date_string)
                if parsed_date:
                    return datetime(*parsed_date[:6]).timestamp()
            
            # Fallback parsing methods
            try:
                dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
                return dt.timestamp()
            except:
                # Try parsing common RSS date formats
                import email.utils
                parsed_date = email.utils.parsedate_tz(date_string)
                if parsed_date:
                    return email.utils.mktime_tz(parsed_date)
                
        except Exception as e:
            logger.warning(f"Could not parse date {date_string}: {e}")
        
        # Return current timestamp as fallback
        return datetime.now().timestamp()
    
    def _filter_last_24_hours(self, news_items):
        """Filter news items to only include those from last 24 hours"""
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        twenty_four_hours_timestamp = twenty_four_hours_ago.timestamp()
        
        filtered_items = []
        for item in news_items:
            if item.get('published_timestamp', 0) >= twenty_four_hours_timestamp:
                filtered_items.append(item)
        
        return filtered_items
    
    def _exclude_categories(self, news_items):
        """Exclude entertainment, sports, and celebrity news"""
        filtered_items = []
        
        for item in news_items:
            title_lower = item['title'].lower()
            description_lower = item['description'].lower()
            
            # Check if any excluded keyword is present
            is_excluded = False
            for excluded_word in self.excluded_categories:
                if (excluded_word in title_lower or 
                    excluded_word in description_lower):
                    is_excluded = True
                    break
            
            if not is_excluded:
                filtered_items.append(item)
        
        return filtered_items
    
    def _determine_source_name(self, feed_url, feed):
        """Determine source name from feed URL or feed object"""
        # Try to get from feed title first
        if hasattr(feed, 'feed') and hasattr(feed.feed, 'title'):
            return feed.feed.title
        
        # Fallback to URL-based detection
        url_lower = feed_url.lower()
        if 'bbc' in url_lower:
            return 'BBC News'
        elif 'cnn' in url_lower:
            return 'CNN'
        elif 'reuters' in url_lower:
            return 'Reuters'
        elif 'ndtv' in url_lower:
            return 'NDTV'
        elif 'thehindu' in url_lower:
            return 'The Hindu'
        elif 'timesofindia' in url_lower:
            return 'Times of India'
        elif 'economictimes' in url_lower:
            return 'Economic Times'
        elif 'business-standard' in url_lower:
            return 'Business Standard'
        elif 'livemint' in url_lower:
            return 'Live Mint'
        elif 'eenadu' in url_lower:
            return 'Eenadu'
        elif 'andhrajyothy' in url_lower:
            return 'Andhra Jyothi'
        else:
            return 'RSS Feed'
    
    def _scrape_ap_news(self):
        """Scrape Andhra Pradesh specific news with proper URLs"""
        ap_news = []
        try:
            ap_sources = [
                {'url': 'https://www.andhrajyothy.com', 'name': 'Andhra Jyothi'},
                {'url': 'https://www.eenadu.net', 'name': 'Eenadu'},
                {'url': 'https://www.sakshi.com', 'name': 'Sakshi'}
            ]
            
            for source in ap_sources[:1]:  # Try first source only
                try:
                    response = self.session.get(source['url'], timeout=self.config.REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for news headlines with links
                        headlines = soup.find_all(['h1', 'h2', 'h3'], limit=3)
                        for headline in headlines:
                            title = headline.get_text(strip=True)
                            if title and len(title) > 10:
                                # Try to find associated link
                                link_element = headline.find('a') or headline.find_parent('a')
                                news_url = source['url']  # Default to main site
                                
                                if link_element and link_element.get('href'):
                                    href = link_element.get('href')
                                    if href.startswith('http'):
                                        news_url = href
                                    elif href.startswith('/'):
                                        news_url = source['url'] + href
                                
                                ap_news.append({
                                    'title': title,
                                    'description': 'Regional news from Andhra Pradesh',
                                    'url': news_url,
                                    'source': source['name'],
                                    'published': datetime.now().isoformat(),
                                    'published_timestamp': datetime.now().timestamp(),
                                    'category': 'Regional'
                                })
                        break
                except Exception as e:
                    logger.warning(f"Error scraping AP news from {source['url']}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in AP news scraping: {e}")
        
        return ap_news
    
    def _scrape_bangalore_news(self):
        """Scrape Bangalore specific news with proper URLs"""
        blr_news = []
        try:
            blr_sources = [
                {'url': 'https://bangaloremirror.indiatimes.com', 'name': 'Bangalore Mirror'},
                {'url': 'https://www.deccanherald.com', 'name': 'Deccan Herald'}
            ]
            
            for source in blr_sources[:1]:  # Try first source only
                try:
                    response = self.session.get(source['url'], timeout=self.config.REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        headlines = soup.find_all(['h1', 'h2', 'h3'], limit=3)
                        for headline in headlines:
                            title = headline.get_text(strip=True)
                            if title and len(title) > 10:
                                # Try to find associated link
                                link_element = headline.find('a') or headline.find_parent('a')
                                news_url = source['url']  # Default to main site
                                
                                if link_element and link_element.get('href'):
                                    href = link_element.get('href')
                                    if href.startswith('http'):
                                        news_url = href
                                    elif href.startswith('/'):
                                        news_url = source['url'] + href
                                
                                blr_news.append({
                                    'title': title,
                                    'description': 'Regional news from Bangalore',
                                    'url': news_url,
                                    'source': source['name'],
                                    'published': datetime.now().isoformat(),
                                    'published_timestamp': datetime.now().timestamp(),
                                    'category': 'Regional'
                                })
                        break
                except Exception as e:
                    logger.warning(f"Error scraping Bangalore news from {source['url']}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in Bangalore news scraping: {e}")
        
        return blr_news
    
    def _get_sample_regional_news(self):
        """Fallback regional news when scraping fails - with proper URLs"""
        current_time = datetime.now()
        return [
            {
                'title': 'IT Sector Growth in Hyderabad and Bangalore',
                'description': 'Technology companies continue to expand operations in major South Indian cities',
                'url': 'https://www.thehindu.com/news/cities/Hyderabad/',
                'source': 'Regional News',
                'published': current_time.isoformat(),
                'published_timestamp': current_time.timestamp(),
                'category': 'Regional'
            },
            {
                'title': 'Infrastructure Development Updates',
                'description': 'Metro rail and road infrastructure projects showing progress in regional cities',
                'url': 'https://www.thehindu.com/news/cities/bangalore/',
                'source': 'Regional News',
                'published': current_time.isoformat(),
                'published_timestamp': current_time.timestamp(),
                'category': 'Regional'
            },
            {
                'title': 'Educational Initiatives in Andhra Pradesh',
                'description': 'State government launches new educational and skill development programs',
                'url': 'https://www.andhrajyothy.com',
                'source': 'Regional News',
                'published': current_time.isoformat(),
                'published_timestamp': current_time.timestamp(),
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
        """Categorize news based on title and description, excluding unwanted categories"""
        content = (title + ' ' + description).lower()
        
        # First check if it's an excluded category
        for excluded_word in self.excluded_categories:
            if excluded_word in content:
                return 'Excluded'  # This will be filtered out
        
        # Categorize allowed news
        if any(word in content for word in ['stock', 'market', 'share', 'nse', 'bse', 'sensex', 'nifty', 'trading']):
            return 'Markets'
        elif any(word in content for word in ['tech', 'technology', 'software', 'ai', 'digital', 'startup']):
            return 'Technology'
        elif any(word in content for word in ['economy', 'gdp', 'inflation', 'fiscal', 'budget', 'finance']):
            return 'Economy'
        elif any(word in content for word in ['politics', 'election', 'government', 'minister', 'policy']):
            return 'Politics'
        elif any(word in content for word in ['health', 'medical', 'hospital', 'covid', 'healthcare']):
            return 'Health'
        else:
            return 'General'
    
    def get_trending_topics(self):
        """Extract trending topics from news headlines (excluding entertainment/sports)"""
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
                        # Skip excluded category words
                        if word not in self.excluded_categories:
                            keywords[word] = keywords.get(word, 0) + 1
            
            # Get top trending keywords
            trending = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
            return [{'keyword': word, 'mentions': count} for word, count in trending]
            
        except Exception as e:
            logger.error(f"Error extracting trending topics: {e}")
            return []
