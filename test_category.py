#!/usr/bin/env python3
"""
Test script for the category feature of the RSS Feed Aggregator.
This script tests the CRUD operations for categories and the relationship between feeds and categories.
"""

import sys
import unittest
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from src.rss_aggregator.database import Database

class TestCategoryFeature(unittest.TestCase):
    """Test cases for the category feature."""
    
    def setUp(self):
        """Set up the test environment."""
        # Use an in-memory database for testing
        self.db = Database(':memory:')
    
    def tearDown(self):
        """Clean up after the test."""
        self.db.close()
    
    def test_add_category(self):
        """Test adding a category."""
        # Add a category
        category_id = self.db.add_category("Technology", "Tech news and updates")
        self.assertIsNotNone(category_id)
        
        # Verify the category was added
        category = self.db.get_category(category_id)
        self.assertIsNotNone(category)
        self.assertEqual(category['name'], "Technology")
        self.assertEqual(category['description'], "Tech news and updates")
    
    def test_get_category_by_name(self):
        """Test getting a category by name."""
        # Add a category
        category_id = self.db.add_category("Science", "Science news and updates")
        
        # Get the category by name
        category = self.db.get_category_by_name("Science")
        self.assertIsNotNone(category)
        self.assertEqual(category['id'], category_id)
        self.assertEqual(category['description'], "Science news and updates")
    
    def test_update_category(self):
        """Test updating a category."""
        # Add a category
        category_id = self.db.add_category("Sports", "Sports news")
        
        # Update the category
        result = self.db.update_category(category_id, "Sports News", "Latest sports updates")
        self.assertTrue(result)
        
        # Verify the category was updated
        category = self.db.get_category(category_id)
        self.assertEqual(category['name'], "Sports News")
        self.assertEqual(category['description'], "Latest sports updates")
    
    def test_delete_category(self):
        """Test deleting a category."""
        # Add a category
        category_id = self.db.add_category("Entertainment", "Entertainment news")
        
        # Delete the category
        result = self.db.delete_category(category_id)
        self.assertTrue(result)
        
        # Verify the category was deleted
        category = self.db.get_category(category_id)
        self.assertIsNone(category)
    
    def test_add_feed_with_category(self):
        """Test adding a feed with a category."""
        # Add a category
        category_id = self.db.add_category("News", "News updates")
        
        # Add a feed with the category
        feed_id = self.db.add_feed(
            "https://example.com/news.xml",
            "Example News",
            category_id,
            60
        )
        self.assertIsNotNone(feed_id)
        
        # Verify the feed was added with the correct category
        feed = self.db.get_feed(feed_id)
        self.assertIsNotNone(feed)
        self.assertEqual(feed['category_id'], category_id)
    
    def test_get_feeds_by_category(self):
        """Test getting feeds by category."""
        # Add a category
        category_id = self.db.add_category("Tech", "Tech news")
        
        # Add feeds with the category
        feed1_id = self.db.add_feed("https://example.com/tech1.xml", "Tech Feed 1", category_id)
        feed2_id = self.db.add_feed("https://example.com/tech2.xml", "Tech Feed 2", category_id)
        
        # Add a feed without the category
        self.db.add_feed("https://example.com/other.xml", "Other Feed", None)
        
        # Get feeds by category
        feeds = self.db.get_all_feeds(active_only=True, category_id=category_id)
        
        # Verify we got the correct feeds
        self.assertEqual(len(feeds), 2)
        feed_ids = [feed['id'] for feed in feeds]
        self.assertIn(feed1_id, feed_ids)
        self.assertIn(feed2_id, feed_ids)
    
    def test_category_null_after_deletion(self):
        """Test that feed's category_id is set to NULL after category deletion."""
        # Add a category
        category_id = self.db.add_category("Finance", "Finance news")
        
        # Add a feed with the category
        feed_id = self.db.add_feed("https://example.com/finance.xml", "Finance Feed", category_id)
        
        # Delete the category
        self.db.delete_category(category_id)
        
        # Verify the feed's category_id is NULL
        feed = self.db.get_feed(feed_id)
        self.assertIsNone(feed['category_id'])

if __name__ == '__main__':
    unittest.main()
