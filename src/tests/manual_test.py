import sys
import os
import logging
from datetime import datetime

# Add the parent directory to system path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collectors.news_collector import NewsCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_news_collector():
    """Manual test for news collector"""
    try:
        # Initialize collector
        collector = NewsCollector()
        logger.info("NewsCollector initialized successfully")
        
        # Test global news
        logger.info("Testing global news collection...")
        global_news = collector.get_global_news()
        logger.info(f"Collected {len(global_news)} global news items")
        
        # Test India news
        logger.info("Testing India news collection...")
        india_news = collector.get_india_news()
        logger.info(f"Collected {len(india_news)} India news items")
        
        # Test business news
        logger.info("Testing business news collection...")
        business_news = collector.get_business_news()
        logger.info(f"Collected {len(business_news)} business news items")
        
        # Test regional news
        logger.info("Testing regional news collection...")
        regional_news = collector.get_regional_news()
        logger.info(f"Collected {len(regional_news)} regional news items")
        
        # Test all news collection
        logger.info("Testing complete news collection...")
        all_news = collector.get_all_news()
        
        # Print sample news items
        for category, items in all_news.items():
            logger.info(f"\nCategory: {category}")
            for item in items[:2]:  # Print first 2 items from each category
                logger.info(f"Title: {item['title']}")
                logger.info(f"Source: {item['source']}")
                logger.info(f"URL: {item['url']}")
                logger.info("---")
                
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    logger.info(f"Starting test at {datetime.now().isoformat()}")
    test_news_collector()
    logger.info("Test completed")
