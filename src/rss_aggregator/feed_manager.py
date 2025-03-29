#!/usr/bin/env python3
"""
Feed management utility for the RSS Feed Aggregator.
Provides commands to add, list, and remove feeds.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from rss_aggregator.database import Database
from rss_aggregator.feed_fetcher import FeedFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'feed_manager.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('feed_manager')

def add_feed(db, url, name=None, update_interval=60):
    """Add a new feed to the database.
    
    Args:
        db (Database): Database connection
        url (str): Feed URL
        name (str, optional): Feed name
        update_interval (int, optional): Update interval in minutes
        
    Returns:
        int: ID of the newly added feed or None if feed already exists
    """
    # Check if feed already exists
    existing = db.get_feed_by_url(url)
    if existing:
        logger.info("Feed already exists: %s", url)
        return None
    
    # Validate feed URL
    fetcher = FeedFetcher()
    if not fetcher.validate_url(url):
        logger.error("Invalid feed URL: %s", url)
        return None
    
    # Try to fetch feed to validate it
    success, feed_data, error_message = fetcher.fetch_feed(url)
    if not success:
        logger.error("Failed to fetch feed: %s - %s", url, error_message)
        return None
    
    # If name is not provided, try to get it from the feed
    if not name:
        feed_info = fetcher.get_feed_info(feed_data)
        name = feed_info.get('title')
    
    # Add feed to database
    feed_id = db.add_feed(url, name, update_interval)
    logger.info("Added feed: %s (%s) with ID %d", name or url, url, feed_id)
    
    return feed_id

def list_feeds(db, show_all=False):
    """List all feeds in the database.
    
    Args:
        db (Database): Database connection
        show_all (bool, optional): Whether to show inactive feeds
    """
    feeds = db.get_all_feeds(active_only=not show_all)
    
    if not feeds:
        print("No feeds found.")
        return
    
    print(f"Found {len(feeds)} feeds:")
    print("-" * 80)
    
    for feed in feeds:
        status = "Active" if feed['active'] else "Inactive"
        error = f" - Error: {feed['error_message']}" if feed['error_message'] else ""
        last_fetched = feed['last_fetched'] or "Never"
        
        print(f"ID: {feed['id']}")
        print(f"Name: {feed['name'] or 'Unnamed'}")
        print(f"URL: {feed['url']}")
        print(f"Status: {status}{error}")
        print(f"Update Interval: {feed['update_interval']} minutes")
        print(f"Last Fetched: {last_fetched}")
        print(f"Error Count: {feed['error_count']}")
        print("-" * 80)

def remove_feed(db, feed_id):
    """Remove a feed from the database.
    
    Args:
        db (Database): Database connection
        feed_id (int): Feed ID
        
    Returns:
        bool: True if feed was removed, False otherwise
    """
    feed = db.get_feed(feed_id)
    if not feed:
        logger.error("Feed not found: %d", feed_id)
        return False
    
    # Deactivate feed instead of removing it
    db.deactivate_feed(feed_id)
    logger.info("Deactivated feed: %s (%s) with ID %d", 
               feed['name'] or 'Unnamed', feed['url'], feed_id)
    
    return True

def activate_feed(db, feed_id):
    """Activate a feed.
    
    Args:
        db (Database): Database connection
        feed_id (int): Feed ID
        
    Returns:
        bool: True if feed was activated, False otherwise
    """
    feed = db.get_feed(feed_id)
    if not feed:
        logger.error("Feed not found: %d", feed_id)
        return False
    
    # Activate feed
    query = "UPDATE feeds SET active = 1, updated_at = datetime('now') WHERE id = ?"
    db.execute_update(query, (feed_id,))
    logger.info("Activated feed: %s (%s) with ID %d", 
               feed['name'] or 'Unnamed', feed['url'], feed_id)
    
    return True

def show_feed_posts(db, feed_id, limit=10):
    """Show posts for a specific feed.
    
    Args:
        db (Database): Database connection
        feed_id (int): Feed ID
        limit (int, optional): Maximum number of posts to show
    """
    feed = db.get_feed(feed_id)
    if not feed:
        logger.error("Feed not found: %d", feed_id)
        return
    
    posts = db.get_posts_by_feed(feed_id, limit=limit)
    
    if not posts:
        print(f"No posts found for feed: {feed['name'] or feed['url']}")
        return
    
    print(f"Latest {len(posts)} posts from {feed['name'] or feed['url']}:")
    print("-" * 80)
    
    for post in posts:
        print(f"Title: {post['title']}")
        print(f"Link: {post['link']}")
        print(f"Date: {post['published_date'] or 'Unknown'}")
        print("-" * 80)

def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(description="RSS Feed Aggregator - Feed Manager")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Add feed command
    add_parser = subparsers.add_parser("add", help="Add a new feed")
    add_parser.add_argument("url", help="Feed URL")
    add_parser.add_argument("--name", help="Feed name (optional)")
    add_parser.add_argument("--interval", type=int, default=60, 
                           help="Update interval in minutes (default: 60)")
    
    # List feeds command
    list_parser = subparsers.add_parser("list", help="List all feeds")
    list_parser.add_argument("--all", action="store_true", 
                            help="Show all feeds, including inactive ones")
    
    # Remove feed command
    remove_parser = subparsers.add_parser("remove", help="Remove a feed")
    remove_parser.add_argument("feed_id", type=int, help="Feed ID")
    
    # Activate feed command
    activate_parser = subparsers.add_parser("activate", help="Activate a feed")
    activate_parser.add_argument("feed_id", type=int, help="Feed ID")
    
    # Show feed posts command
    posts_parser = subparsers.add_parser("posts", help="Show posts for a feed")
    posts_parser.add_argument("feed_id", type=int, help="Feed ID")
    posts_parser.add_argument("--limit", type=int, default=10, 
                             help="Maximum number of posts to show (default: 10)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Connect to database
    db = Database()
    
    try:
        if args.command == "add":
            add_feed(db, args.url, args.name, args.interval)
        
        elif args.command == "list":
            list_feeds(db, args.all)
        
        elif args.command == "remove":
            remove_feed(db, args.feed_id)
        
        elif args.command == "activate":
            activate_feed(db, args.feed_id)
        
        elif args.command == "posts":
            show_feed_posts(db, args.feed_id, args.limit)
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
