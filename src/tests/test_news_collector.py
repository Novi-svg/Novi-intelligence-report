import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import time
import sys
import os

# Adjust the path to import NewsCollector
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data_collectors.news_collector import NewsCollector

class TestNewsCollector(unittest.TestCase):
    def setUp(self):
        """Set up a NewsCollector instance for testing."""
        self.collector = NewsCollector()

    @patch('data_collectors.news_collector.feedparser')
    def test_feed_parsing(self, mock_feedparser):
        """Test RSS feed parsing with mock data."""
        # Mock feedparser.parse
        mock_feed = MagicMock()
        mock_entry = MagicMock()
        mock_entry.title = 'Test Title'
        mock_entry.description = 'Test Description'
        mock_entry.link = 'http://example.com/news'
        mock_entry.published = datetime.now().isoformat()
        mock_feed.entries = [mock_entry]
        mock_feed.status = 200
        mock_feed.feed.title = "Test Feed"
        mock_feedparser.parse.return_value = mock_feed
        
        # Call the method
        items = self.collector._parse_rss_feed('http://example.com/rss')
        
        # Assertions
        self.assertTrue(len(items) > 0)
        self.assertEqual(items[0]['title'], 'Test Title')
        
    def test_clean_description(self):
        """Test HTML cleaning from descriptions."""
        entry = MagicMock()
        entry.description = '<p>This is a test.</p>'
        entry.summary = ''
        clean_desc = self.collector._get_clean_description(entry)
        self.assertEqual(clean_desc, 'This is a test.')

    def test_date_parsing(self):
        """Test date parsing functionality."""
        test_date = "2023-10-27T10:00:00Z"
        timestamp = self.collector._parse_date_to_timestamp(test_date)
        self.assertIsInstance(timestamp, float)

    def test_category_filtering(self):
        """Test news category filtering."""
        title = "Big Market News"
        description = "Stocks are going up"
        category = self.collector._categorize_news(title, description)
        self.assertEqual(category, 'Business')

    @patch('data_collectors.news_collector.NewsCollector.get_global_news')
    def test_fallback_news(self, mock_get_global_news):
        """Test fallback mechanism when news collection fails."""
        mock_get_global_news.return_value = []

        # Call the get_all_news method
        news = self.collector.get_all_news()
        
        # Check if fallback data is provided
        self.assertTrue('global' in news)
        self.assertEqual(len(news['global']), 1)
        self.assertEqual(news['global'][0]['title'], 'Service Temporarily Unavailable')

if __name__ == '__main__':
    unittest.main()
