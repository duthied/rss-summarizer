#!/usr/bin/env python3
"""
Feed management utility for the RSS Feed Aggregator.
Provides commands to add, list, and remove feeds and categories.
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

# Category management functions

def add_category(db, name, description=None):
    """Add a new category to the database.
    
    Args:
        db (Database): Database connection
        name (str): Category name
        description (str, optional): Category description
        
    Returns:
        int: ID of the newly added category or None if category already exists
    """
    # Check if category already exists
    existing = db.get_category_by_name(name)
    if existing:
        logger.info("Category already exists: %s", name)
        return None
    
    # Add category to database
    category_id = db.add_category(name, description)
    logger.info("Added category: %s with ID %d", name, category_id)
    
    return category_id

def list_categories(db):
    """List all categories in the database.
    
    Args:
        db (Database): Database connection
    """
    categories = db.get_all_categories()
    
    if not categories:
        print("No categories found.")
        return
    
    print(f"Found {len(categories)} categories:")
    print("-" * 80)
    
    for category in categories:
        print(f"ID: {category['id']}")
        print(f"Name: {category['name']}")
        if category['description']:
            print(f"Description: {category['description']}")
        print("-" * 80)

def update_category(db, category_id, name=None, description=None):
    """Update a category in the database.
    
    Args:
        db (Database): Database connection
        category_id (int): Category ID
        name (str, optional): New category name
        description (str, optional): New category description
        
    Returns:
        bool: True if category was updated, False otherwise
    """
    category = db.get_category(category_id)
    if not category:
        logger.error("Category not found: %d", category_id)
        return False
    
    result = db.update_category(category_id, name, description)
    if result:
        logger.info("Updated category: %s (ID: %d)", 
                   name or category['name'], category_id)
        return True
    else:
        logger.error("Failed to update category: %d", category_id)
        return False

def delete_category(db, category_id):
    """Delete a category from the database.
    
    Args:
        db (Database): Database connection
        category_id (int): Category ID
        
    Returns:
        bool: True if category was deleted, False otherwise
    """
    category = db.get_category(category_id)
    if not category:
        logger.error("Category not found: %d", category_id)
        return False
    
    result = db.delete_category(category_id)
    if result:
        logger.info("Deleted category: %s (ID: %d)", category['name'], category_id)
        return True
    else:
        logger.error("Failed to delete category: %d", category_id)
        return False

def add_feed(db, url, name=None, category=None, update_interval=60):
    """Add a new feed to the database.
    
    Args:
        db (Database): Database connection
        url (str): Feed URL
        name (str, optional): Feed name
        category (str or int, optional): Category name or ID
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
    
    # Resolve category
    category_id = None
    if category:
        if isinstance(category, int) or category.isdigit():
            # Category ID provided
            category_id = int(category)
            cat = db.get_category(category_id)
            if not cat:
                logger.warning("Category ID %d not found, feed will be added without category", category_id)
                category_id = None
        else:
            # Category name provided
            cat = db.get_category_by_name(category)
            if cat:
                category_id = cat['id']
            else:
                # Create new category
                logger.info("Creating new category: %s", category)
                category_id = db.add_category(category)
    
    # Add feed to database
    feed_id = db.add_feed(url, name, category_id, update_interval)
    logger.info("Added feed: %s (%s) with ID %d", name or url, url, feed_id)
    
    return feed_id

def list_feeds(db, show_all=False, category_id=None):
    """List all feeds in the database.
    
    Args:
        db (Database): Database connection
        show_all (bool, optional): Whether to show inactive feeds
        category_id (int, optional): Filter by category ID
    """
    feeds = db.get_all_feeds(active_only=not show_all, category_id=category_id)
    
    if not feeds:
        print("No feeds found.")
        return
    
    # If filtering by category, show category name
    if category_id:
        category = db.get_category(category_id)
        if category:
            print(f"Feeds in category: {category['name']}")
    
    print(f"Found {len(feeds)} feeds:")
    print("-" * 80)
    
    for feed in feeds:
        status = "Active" if feed['active'] else "Inactive"
        error = f" - Error: {feed['error_message']}" if feed['error_message'] else ""
        last_fetched = feed['last_fetched'] or "Never"
        
        print(f"ID: {feed['id']}")
        print(f"Name: {feed['name'] or 'Unnamed'}")
        print(f"URL: {feed['url']}")
        print(f"Category: {feed['category_name'] or 'Uncategorized'}")
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
    
    # Feed commands
    
    # Add feed command
    add_cmd = subparsers.add_parser("add", help="Add a new feed")
    add_cmd.add_argument("url", help="Feed URL")
    add_cmd.add_argument("--name", help="Feed name (optional)")
    add_cmd.add_argument("--category", help="Category name or ID (optional)")
    add_cmd.add_argument("--interval", type=int, default=60, 
                        help="Update interval in minutes (default: 60)")
    
    # List feeds command
    list_cmd = subparsers.add_parser("list", help="List all feeds")
    list_cmd.add_argument("--all", action="store_true", 
                         help="Show all feeds, including inactive ones")
    list_cmd.add_argument("--category", type=int, 
                         help="Filter by category ID")
    
    # Remove feed command
    remove_cmd = subparsers.add_parser("remove", help="Remove a feed")
    remove_cmd.add_argument("feed_id", type=int, help="Feed ID")
    
    # Activate feed command
    activate_cmd = subparsers.add_parser("activate", help="Activate a feed")
    activate_cmd.add_argument("feed_id", type=int, help="Feed ID")
    
    # Show feed posts command
    posts_cmd = subparsers.add_parser("posts", help="Show posts for a feed")
    posts_cmd.add_argument("feed_id", type=int, help="Feed ID")
    posts_cmd.add_argument("--limit", type=int, default=10, 
                          help="Maximum number of posts to show (default: 10)")
    
    # Category commands
    
    # Add category command
    add_cat_cmd = subparsers.add_parser("add-category", help="Add a new category")
    add_cat_cmd.add_argument("name", help="Category name")
    add_cat_cmd.add_argument("--description", help="Category description (optional)")
    
    # List categories command
    _ = subparsers.add_parser("list-categories", help="List all categories")
    
    # Update category command
    update_cat_cmd = subparsers.add_parser("update-category", help="Update a category")
    update_cat_cmd.add_argument("category_id", type=int, help="Category ID")
    update_cat_cmd.add_argument("--name", help="New category name (optional)")
    update_cat_cmd.add_argument("--description", help="New category description (optional)")
    
    # Delete category command
    delete_cat_cmd = subparsers.add_parser("delete-category", help="Delete a category")
    delete_cat_cmd.add_argument("category_id", type=int, help="Category ID")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Connect to database
    db = Database()
    
    try:
        # Feed commands
        if args.command == "add":
            add_feed(db, args.url, args.name, args.category, args.interval)
        
        elif args.command == "list":
            list_feeds(db, args.all, args.category)
        
        elif args.command == "remove":
            remove_feed(db, args.feed_id)
        
        elif args.command == "activate":
            activate_feed(db, args.feed_id)
        
        elif args.command == "posts":
            show_feed_posts(db, args.feed_id, args.limit)
    
        # Category commands
        elif args.command == "add-category":
            add_category(db, args.name, args.description)
        
        elif args.command == "list-categories":
            list_categories(db)
        
        elif args.command == "update-category":
            update_category(db, args.category_id, args.name, args.description)
        
        elif args.command == "delete-category":
            delete_category(db, args.category_id)
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
