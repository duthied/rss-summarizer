#!/usr/bin/env python3
"""
Test script for the RSS Feed Aggregator.
Adds a sample feed, processes it, and displays the results.
"""

import os
import sys
import time
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from rss_aggregator.database import Database
from rss_aggregator.feed_fetcher import FeedFetcher
from rss_aggregator.feed_processor import process_feed

# Sample RSS feeds
SAMPLE_FEEDS = [
    {
        'url': 'https://news.ycombinator.com/rss',
        'name': 'Hacker News',
        'interval': 60
    },
    {
        'url': 'https://www.reddit.com/r/programming/.rss',
        'name': 'Reddit Programming',
        'interval': 120
    }
]

def main():
    """Main function to test the RSS feed aggregator."""
    print("RSS Feed Aggregator - Test Script")
    print("-" * 50)
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Connect to database
    db = Database()
    
    try:
        # Add sample feeds
        for feed_info in SAMPLE_FEEDS:
            # Check if feed already exists
            existing = db.get_feed_by_url(feed_info['url'])
            if existing:
                print(f"Feed already exists: {feed_info['name']} ({feed_info['url']})")
                continue
            
            # Add feed
            feed_id = db.add_feed(
                feed_info['url'],
                feed_info['name'],
                feed_info['interval']
            )
            
            if feed_id:
                print(f"Added feed: {feed_info['name']} ({feed_info['url']}) with ID {feed_id}")
        
        # Get all feeds
        feeds = db.get_all_feeds()
        
        if not feeds:
            print("No feeds found in database.")
            return
        
        # Create feed fetcher
        fetcher = FeedFetcher()
        
        # Process each feed
        for feed in feeds:
            print(f"\nProcessing feed: {feed['name'] or feed['url']}")
            
            # Process feed
            success, processed_count, error = process_feed(feed, db, fetcher)
            
            if success:
                print(f"Successfully processed feed: {processed_count} new posts")
            else:
                print(f"Failed to process feed: {error}")
            
            # Small delay between feeds
            time.sleep(1)
        
        # Show latest posts
        print("\nLatest posts:")
        print("-" * 50)
        
        latest_posts = db.get_latest_posts(limit=10)
        
        if not latest_posts:
            print("No posts found.")
            return
        
        for post in latest_posts:
            print(f"Feed: {post['feed_name']}")
            print(f"Title: {post['title']}")
            print(f"Link: {post['link']}")
            print(f"Date: {post['published_date'] or 'Unknown'}")
            print("-" * 50)
        
    finally:
        # Close database connection
        db.close()

if __name__ == "__main__":
    main()
