import os
from datetime import datetime
import pytz

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
    NEWS_SOURCES = {
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
    REQUEST_TIMEOUT = 30
    
    # Enhanced User agents for web scraping
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]

# Get current IST time
def get_ist_time():
    return datetime.now(Config.IST)

# Check if today should be skipped
def should_skip_today():
    today = get_ist_time().weekday()
    return today in Config.EXCLUDE_DAYS
