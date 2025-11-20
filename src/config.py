import os
from datetime import datetime, timedelta
import pytz
from typing import Dict, List

class Config:
    # Email Configuration
    EMAIL_FROM = os.getenv('EMAIL_FROM')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')  # App password for Gmail
    EMAIL_TO = os.getenv('EMAIL_TO')

    # Timezone
    IST = pytz.timezone('Asia/Kolkata')

    # Email Settings
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587

    # Report Settings
    EXCLUDE_DAYS = []  # Add days to exclude (0=Monday, 6=Sunday)

    # Enhanced Stock Exchange URLs for scraping
    STOCK_SOURCES = {
        'nse': 'https://www.nseindia.com',
        'moneycontrol': 'https://www.moneycontrol.com',
        'screener': 'https://www.screener.in',
        'investing': 'https://in.investing.com'
    }

    # Enhanced Mutual Fund Sources
    MUTUAL_FUND_SOURCES = {
        'valueresearch': 'https://www.valueresearchonline.com',
        'morningstar': 'https://www.morningstar.in',
        'moneycontrol_mf': 'https://www.moneycontrol.com/mutual-funds'
    }

    # Enhanced News Sources (RSS based - no API needed)
    NEWS_SOURCES: Dict[str, List[str]] = {
        'global': [
            'http://feeds.bbci.co.uk/news/rss.xml',
            'http://rss.cnn.com/rss/edition.rss',
            'https://feeds.reuters.com/reuters/topNews',
            'https://feeds.reuters.com/reuters/businessNews'
        ],
        'india': [
            'https://feeds.feedburner.com/ndtvnews-top-stories',
            'https://www.thehindu.com/news/national/feeder/default.rss',
            'https://timesofindia.indiatimes.com/rssfeedstopstories.cms',
            'https://www.business-standard.com/rss/home_page_top_stories.rss'
        ],
        'business': [
            'https://economictimes.indiatimes.com/rssfeedsdefault.cms',
            'https://www.business-standard.com/rss/markets-106.rss',
            'https://www.livemint.com/rss/money'
        ],
        'regional': [
            'https://www.thehindu.com/news/cities/bangalore/feeder/default.rss',
            'https://www.thehindu.com/news/cities/Hyderabad/feeder/default.rss',
            'https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms',  # Bangalore
            'https://timesofindia.indiatimes.com/rssfeeds/-2128816011.cms'   # Hyderabad
        ]
    }

    # Enhanced Job Search URLs
    JOB_SOURCES = {
        'naukri': 'https://www.naukri.com',
        'linkedin': 'https://www.linkedin.com/jobs',
        'indeed': 'https://in.indeed.com',
        'glassdoor': 'https://www.glassdoor.co.in',
        'timesjobs': 'https://www.timesjobs.com',
        'shine': 'https://www.shine.com'
    }

    # Enhanced Job Keywords for SAP and AI roles
    JOB_KEYWORDS = {
        'sap': [
            'SAP Finance Architect',
            'SAP B2P Lead',
            'SAP Workstream Lead',
            'Program Lead SAP',
            'SAP S/4HANA Finance',
            'SAP FICO Consultant',
            'SAP Program Manager',
            'SAP Solution Architect',
            'SAP HANA Cloud Finance',
            'SAP Controlling AI'
        ],
        'ai_transition': [
            'AI ML SAP background',
            'Machine Learning SAP experience',
            'Data Science SAP transition',
            'AI Solutions Architect Enterprise',
            'ML Engineer Financial Analytics',
            'Data Scientist SAP Domain'
        ]
    }

    # Enhanced web scraping settings
    REQUEST_DELAY = 2  # Delay between requests in seconds
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = {
        'connect': 10,    # Connection timeout
        'read': 20      # Read timeout
    }

    # Enhanced User agents for web scraping
    USER_AGENTS: List[str] = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]

    # RSS feed timeout (in seconds)
    FEED_TIMEOUT = 10

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

# Get current IST time
def get_ist_time():
    return datetime.now(Config.IST)

# Check if today should be skipped
def should_skip_today():
    today = get_ist_time().weekday()
    return today in Config.EXCLUDE_DAYS
