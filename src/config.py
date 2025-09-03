from typing import Dict, List
from datetime import timedelta

class Config:
    # User agents list for rotating requests
    USER_AGENTS: List[str] = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/116.0.1938.69',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5.2 Safari/605.1.15'
    ]

    # News sources categorized by type
    NEWS_SOURCES: Dict[str, List[str]] = {
        'global': [
            'http://rss.cnn.com/rss/edition.rss',
            'http://feeds.bbci.co.uk/news/world/rss.xml',
            'https://www.reuters.com/rss/world',
            'https://feeds.npr.org/1004/rss.xml',
            'https://www.aljazeera.com/xml/rss/all.xml'
        ],
        'india': [
            'https://feeds.feedburner.com/ndtvnews-india-news',
            'https://www.thehindu.com/news/national/feeder/default.rss',
            'https://timesofindia.indiatimes.com/rssfeeds/296589292.cms',
            'https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml',
            'https://indianexpress.com/feed/'
        ],
        'business': [
            'https://feeds.feedburner.com/ndtvprofit-latest',
            'https://www.business-standard.com/rss/latest.rss',
            'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
            'https://www.livemint.com/rss/markets',
            'https://feeds.feedburner.com/moneycontrol/rss/buzzingstocks.xml',
            'https://www.thehindubusinessline.com/markets/stock-markets/feeder/default.rss'
        ],
        'regional': [
            'https://www.thehindu.com/news/cities/bangalore/feeder/default.rss',
            'https://www.thehindu.com/news/cities/Hyderabad/feeder/default.rss',
            'https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms',  # Bangalore
            'https://timesofindia.indiatimes.com/rssfeeds/-2128816011.cms'   # Hyderabad
        ]
    }

    # Request timeout settings (in seconds)
    REQUEST_TIMEOUT = {
        'connect': 5,    # Connection timeout
        'read': 15      # Read timeout
    }

    # Delay between requests (in seconds)
    REQUEST_DELAY = 1.5

    # RSS feed timeout (in seconds)
    FEED_TIMEOUT = 10

    # Maximum retries for failed requests
    MAX_RETRIES = 3

    # Backoff factor for retries
    RETRY_BACKOFF_FACTOR = 1

    # Maximum news items per category
    MAX_ITEMS = {
        'global': 10,
        'india': 10,
        'business': 8,
        'regional': 8
    }

    # News cache duration
    CACHE_DURATION = timedelta(minutes=15)

    # HTTP Status codes to retry on
    RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

    # Date formats to try when parsing feed dates
    DATE_FORMATS = [
        '%Y-%m-%dT%H:%M:%S%z',          # ISO 8601 with timezone
        '%Y-%m-%dT%H:%M:%SZ',           # ISO 8601 UTC
        '%a, %d %b %Y %H:%M:%S %z',     # RFC 822
        '%a, %d %b %Y %H:%M:%S %Z',     # RFC 822 with timezone name
        '%Y-%m-%d %H:%M:%S',            # Basic datetime
        '%Y-%m-%d'                       # Just date
    ]

    def __init__(self):
        # Validate configuration
        self._validate_config()

    def _validate_config(self):
        """Validate configuration settings"""
        # Validate USER_AGENTS
        if not self.USER_AGENTS or not isinstance(self.USER_AGENTS, list):
            raise ValueError("USER_AGENTS must be a non-empty list")

        # Validate NEWS_SOURCES
        required_categories = ['global', 'india', 'business', 'regional']
        for category in required_categories:
            if category not in self.NEWS_SOURCES:
                raise ValueError(f"Missing required category '{category}' in NEWS_SOURCES")
            if not isinstance(self.NEWS_SOURCES[category], list):
                raise ValueError(f"NEWS_SOURCES['{category}'] must be a list")
            if not self.NEWS_SOURCES[category]:
                raise ValueError(f"NEWS_SOURCES['{category}'] cannot be empty")

        # Validate timeout settings
        if not isinstance(self.REQUEST_TIMEOUT, dict):
            raise ValueError("REQUEST_TIMEOUT must be a dictionary")
        if 'connect' not in self.REQUEST_TIMEOUT or 'read' not in self.REQUEST_TIMEOUT:
            raise ValueError("REQUEST_TIMEOUT must contain 'connect' and 'read' keys")

        # Validate REQUEST_DELAY
        if not isinstance(self.REQUEST_DELAY, (int, float)) or self.REQUEST_DELAY <= 0:
            raise ValueError("REQUEST_DELAY must be a positive number")

        # Validate MAX_RETRIES
        if not isinstance(self.MAX_RETRIES, int) or self.MAX_RETRIES < 0:
            raise ValueError("MAX_RETRIES must be a non-negative integer")

    @property
    def timeout(self) -> tuple:
        """Get timeout as a tuple for requests"""
        return (self.REQUEST_TIMEOUT['connect'], self.REQUEST_TIMEOUT['read'])
