import sys
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# Add the parent directory to system path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collectors.news_collector import NewsCollector
from config import Config

class TestNewsCollector(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.collector = NewsCollector()
        
    def test_basic_initialization(self):
        """Test if NewsCollector initializes correctly"""
        self.assertIsNotNone(self.collector)
        self.assertIsNotNone(self.collector.config)
        self.assertIsNotNone(self.collector.session)
        
    @patch('requests.Session.get')
    def test_feed_parsing(self, mock_get):
        """Test RSS feed parsing with mock data"""
        # Mock RSS feed response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = """
        <?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0">
        <channel>
            <title>Test News Feed</title>
            <link>http://example.com</link>
            <description>Test Feed</description>
            <item>
                <title>Test News Item</title>
                <link>http://example.com/news/1</link>
                <description>Test Description</description>
                <pubDate>Wed, 03 Sep 2025 15:40:58 GMT</pubDate>
            </item>
        </channel>
        </rss>
        """
        mock_get.return_value = mock_response
        
        # Test feed parsing
        feed_url = "http://example.com/rss"
        items = self.collector._parse_rss_feed(feed_url)
        
        self.assertTrue(len(items) > 0)
        self.assertEqual(items[0]['title'], 'Test News Item')
        
    def test_date_parsing(self):
        """Test date parsing functionality"""
        test_date = "Wed, 03 Sep 2025 15:40:58 GMT"
        timestamp = self.collector._parse_date_to_timestamp(test_date)
        self.assertIsNotNone(timestamp)
        
    def test_category_filtering(self):
        """Test news category filtering"""
        test_news = {
            'title': 'Important Business Update',
            'description': 'Stock market news'
        }
        category = self.collector._categorize_news(
            test_news['title'], 
            test_news['description']
        )
        self.assertEqual(category, 'Markets')
        
    def test_excluded_categories(self):
        """Test excluded categories filtering"""
        test_news = {
            'title': 'Sports Update',
            'description': 'Cricket match results'
        }
        category = self.collector._categorize_news(
            test_news['title'], 
            test_news['description']
        )
        self.assertEqual(category, 'Excluded')

if __name__ == '__main__':
    unittest.main()
