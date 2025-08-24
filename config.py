import os
from datetime import datetime
import pytz

class Config:
    # Email Configuration
    EMAIL_FROM = os.getenv('EMAIL_FROM')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')  # App password for Gmail
    EMAIL_TO = os.getenv('EMAIL_TO')
    
    # API Keys
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Optional for AI summaries
    
    # Timezone
    IST = pytz.timezone('Asia/Kolkata')
    
    # Email Settings
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    
    # Report Settings
    EXCLUDE_DAYS = []  # Add days to exclude (0=Monday, 6=Sunday)
    
    # Stock Settings
    TOP_STOCKS = {
        'large_cap': ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'HINDUNILVR.NS'],
        'mid_cap': ['TATAMOTORS.NS', 'BAJFINANCE.NS', 'M&M.NS', 'SUNPHARMA.NS'],
        'small_cap': ['ZEEL.NS', 'IDEA.NS']
    }
    
    # News Sources
    NEWS_SOURCES = {
        'global': ['bbc-news', 'cnn', 'reuters', 'al-jazeera-english'],
        'india': ['the-times-of-india', 'the-hindu'],
        'tech': ['techcrunch', 'ars-technica']
    }
    
    # Job Keywords
    JOB_KEYWORDS = [
        'SAP Finance Architect',
        'SAP B2P Lead',
        'SAP Workstream Lead',
        'Program Lead SAP',
        'SAP S/4HANA Finance'
    ]

# Get current IST time
def get_ist_time():
    return datetime.now(Config.IST)

# Check if today should be skipped
def should_skip_today():
    today = get_ist_time().weekday()
    return today in Config.EXCLUDE_DAYS
