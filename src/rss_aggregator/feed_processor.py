#!/usr/bin/env python3
"""
Main processor script for the RSS Feed Aggregator.
Fetches and processes RSS feeds that are due for updates.
"""

import os
import sys
import logging
import time
import sqlite3
import requests
from datetime import datetime
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
        logging.FileHandler(os.path.join('logs', 'processor.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('feed_processor')

def process_feed(feed, db, fetcher):
    """Process a single feed.
    
    Args:
        feed (sqlite3.Row): Feed data from the database
        db (Database): Database connection
        fetcher (FeedFetcher): Feed fetcher instance
        
    Returns:
        tuple: (success, processed_count, error_message)
            success (bool): Whether the processing was successful
            processed_count (int): Number of new posts processed
            error_message (str): Error message if processing failed, None otherwise
    """
    feed_id = feed['id']
    feed_url = feed['url']
    feed_name = feed['name'] or feed_url
    
    logger.info("Processing feed %s (%s)", feed_name, feed_url)
    
    # Fetch the feed
    success, feed_data, error_message = fetcher.fetch_feed(feed_url)
    
    if not success:
        logger.error("Failed to fetch feed %s: %s", feed_name, error_message)
        db.update_feed_status(feed_id, False, error_message)
        return False, 0, error_message
    
    # Get feed info and update feed name if not set
    feed_info = fetcher.get_feed_info(feed_data)
    if not feed['name'] and feed_info.get('title'):
        # Update feed name in database
        query = "UPDATE feeds SET name = ?, updated_at = ? WHERE id = ?"
        db.execute_update(query, (feed_info['title'], datetime.now().isoformat(), feed_id))
        logger.info("Updated feed name to %s", feed_info['title'])
    
    # Process entries
    entries = fetcher.get_entries(feed_data)
    processed_count = 0
    
    for entry in entries:
        processed_entry = fetcher.process_entry(entry)
        
        # Skip entries without required fields
        if not processed_entry.get('title') or not processed_entry.get('link') or not processed_entry.get('guid'):
            continue
        
        # Add post to database
        post_id = db.add_post(
            feed_id,
            processed_entry['title'],
            processed_entry['link'],
            processed_entry['guid'],
            processed_entry.get('description'),
            processed_entry.get('published_date')
        )
        
        if post_id:
            processed_count += 1
    
    # Update feed status
    db.update_feed_status(feed_id, True)
    
    logger.info("Successfully processed feed %s: %d new posts", feed_name, processed_count)
    return True, processed_count, None

def calculate_backoff(error_count):
    """Calculate backoff time based on error count.
    
    Args:
        error_count (int): Number of consecutive errors
        
    Returns:
        int: Backoff time in minutes
    """
    # Exponential backoff: 2^error_count * base_interval (capped at 1 day)
    base_interval = 15  # minutes
    backoff_minutes = min(
        base_interval * (2 ** error_count),
        24 * 60  # Max 1 day
    )
    return backoff_minutes

def main():
    """Main function to process due feeds."""
    start_time = time.time()
    logger.info("Starting feed processor")
    
    try:
        # Connect to database
        db = Database()
        
        # Create feed fetcher
        fetcher = FeedFetcher()
        
        # Get feeds that are due for processing
        due_feeds = db.get_due_feeds()
        
        if not due_feeds:
            logger.info("No feeds due for processing")
            return
        
        logger.info("Processing %d feeds", len(due_feeds))
        
        # Process each feed
        total_processed = 0
        success_count = 0
        error_count = 0
        
        for feed in due_feeds:
            try:
                success, processed_count, _ = process_feed(feed, db, fetcher)
                
                if success:
                    total_processed += processed_count
                    success_count += 1
                else:
                    error_count += 1
                    
                # Small delay between feeds to avoid hammering servers
                time.sleep(1)
                
            except (requests.RequestException, sqlite3.Error, ValueError, AttributeError) as e:
                logger.exception("Error processing feed %s: %s", feed['url'], e)
                error_count += 1
                
                # Update feed status with error
                db.update_feed_status(feed['id'], False, str(e))
        
        # Log summary
        elapsed_time = time.time() - start_time
        logger.info("Feed processing completed in %.2f seconds", elapsed_time)
        logger.info("Processed %d feeds (%d successful, %d failed)", 
                   len(due_feeds), success_count, error_count)
        logger.info("Added %d new posts", total_processed)
        
    except (sqlite3.Error, IOError, OSError) as e:
        logger.exception("Database or I/O error in feed processor: %s", e)
    finally:
        # Close database connection
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main()
