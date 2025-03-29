"""
Database handler for the RSS Feed Aggregator.
Manages connections to the SQLite database and provides methods for CRUD operations.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
import logging

# Register adapter for datetime objects
def adapt_datetime(dt):
    return dt.isoformat()

def convert_datetime(s):
    try:
        return datetime.fromisoformat(s.decode())
    except ValueError:
        return datetime.now()  # Fallback to current time if parsing fails

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("timestamp", convert_datetime)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'database.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('database')

class Database:
    """SQLite database connection manager and operations handler."""
    
    def __init__(self, db_path='rss_feeds.db'):
        """Initialize database connection and ensure tables exist.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.initialize_database()
    
    def get_connection(self):
        """Get a database connection, creating one if needed.
        
        Returns:
            sqlite3.Connection: Database connection object
        """
        if self.conn is None:
            try:
                self.conn = sqlite3.connect(
                    self.db_path,
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
                )
                # Register custom functions
                self.conn.create_function("CURRENT_TIMESTAMP", 0, lambda: datetime.now().isoformat())
                self.conn.row_factory = sqlite3.Row
            except sqlite3.Error as e:
                logger.error("Database connection error: %s", e)
                raise
        return self.conn
    
    def close(self):
        """Close the database connection if open."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def initialize_database(self):
        """Initialize the database with required tables if they don't exist."""
        try:
            conn = self.get_connection()
            
            # Read schema from file
            schema_path = Path(__file__).parent / 'schema.sql'
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_script = f.read()
            
            # Execute schema script
            conn.executescript(schema_script)
            conn.commit()
            logger.info("Database initialized successfully")
        except (sqlite3.Error, IOError) as e:
            logger.error("Database initialization error: %s", e)
            raise
    
    def execute_query(self, query, params=None):
        """Execute a query and return all results.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            list: List of sqlite3.Row objects
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error("Query execution error: %s", e)
            logger.error("Query: %s", query)
            logger.error("Params: %s", params)
            raise
    
    def execute_update(self, query, params=None):
        """Execute an update query (INSERT, UPDATE, DELETE).
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            int: Row ID of the last inserted row or number of rows affected
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("Update execution error: %s", e)
            logger.error("Query: %s", query)
            logger.error("Params: %s", params)
            raise
    
    # Feed operations
    
    def add_feed(self, url, name=None, update_interval=60):
        """Add a new feed to the database.
        
        Args:
            url (str): Feed URL
            name (str, optional): Feed name
            update_interval (int, optional): Update interval in minutes
            
        Returns:
            int: ID of the newly added feed
        """
        query = """
        INSERT INTO feeds (url, name, update_interval)
        VALUES (?, ?, ?)
        """
        return self.execute_update(query, (url, name, update_interval))
    
    def get_feed(self, feed_id):
        """Get a feed by ID.
        
        Args:
            feed_id (int): Feed ID
            
        Returns:
            sqlite3.Row: Feed data or None if not found
        """
        query = "SELECT * FROM feeds WHERE id = ?"
        results = self.execute_query(query, (feed_id,))
        return results[0] if results else None
    
    def get_feed_by_url(self, url):
        """Get a feed by URL.
        
        Args:
            url (str): Feed URL
            
        Returns:
            sqlite3.Row: Feed data or None if not found
        """
        query = "SELECT * FROM feeds WHERE url = ?"
        results = self.execute_query(query, (url,))
        return results[0] if results else None
    
    def get_all_feeds(self, active_only=True):
        """Get all feeds, optionally filtering for active only.
        
        Args:
            active_only (bool): Whether to return only active feeds
            
        Returns:
            list: List of feed rows
        """
        if active_only:
            query = "SELECT * FROM feeds WHERE active = 1"
        else:
            query = "SELECT * FROM feeds"
        return self.execute_query(query)
    
    def get_due_feeds(self):
        """Get feeds that are due for processing based on their update interval.
        
        Returns:
            list: List of feed rows
        """
        current_time = datetime.now().isoformat()
        
        query = """
        SELECT * FROM feeds 
        WHERE 
            active = 1 AND (
                last_fetched IS NULL OR
                datetime(last_fetched, '+' || update_interval || ' minutes') <= datetime(?)
            )
        ORDER BY last_fetched ASC
        """
        
        return self.execute_query(query, (current_time,))
    
    def update_feed_status(self, feed_id, success, error_message=None):
        """Update feed status after a fetch attempt.
        
        Args:
            feed_id (int): Feed ID
            success (bool): Whether the fetch was successful
            error_message (str, optional): Error message if fetch failed
            
        Returns:
            int: Number of rows affected
        """
        current_time = datetime.now().isoformat()
        
        if success:
            # Reset error count on success
            query = """
            UPDATE feeds
            SET 
                last_fetched = ?,
                fetch_status = 0,
                error_count = 0,
                error_message = NULL,
                updated_at = ?
            WHERE id = ?
            """
            return self.execute_update(query, (current_time, current_time, feed_id))
        else:
            # Increment error count on failure
            query = """
            UPDATE feeds
            SET 
                last_fetched = ?,
                fetch_status = 1,
                error_count = error_count + 1,
                error_message = ?,
                last_error = ?,
                updated_at = ?
            WHERE id = ?
            """
            return self.execute_update(query, (
                current_time, error_message, current_time, current_time, feed_id
            ))
    
    def deactivate_feed(self, feed_id):
        """Deactivate a feed.
        
        Args:
            feed_id (int): Feed ID
            
        Returns:
            int: Number of rows affected
        """
        query = """
        UPDATE feeds
        SET active = 0, updated_at = ?
        WHERE id = ?
        """
        return self.execute_update(query, (datetime.now().isoformat(), feed_id))
    
    # Post operations
    
    def add_post(self, feed_id, title, link, guid, description=None, published_date=None):
        """Add a new post to the database.
        
        Args:
            feed_id (int): Feed ID
            title (str): Post title
            link (str): Post link
            guid (str): Post GUID
            description (str, optional): Post description
            published_date (datetime, optional): Post publication date
            
        Returns:
            int: ID of the newly added post or None if post already exists
        """
        # Check if post already exists
        existing = self.get_post_by_guid(guid)
        if existing:
            return None
        
        query = """
        INSERT INTO posts (feed_id, title, link, guid, description, published_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        if published_date and not isinstance(published_date, str):
            published_date = published_date.isoformat()
            
        return self.execute_update(query, (
            feed_id, title, link, guid, description, published_date
        ))
    
    def get_post(self, post_id):
        """Get a post by ID.
        
        Args:
            post_id (int): Post ID
            
        Returns:
            sqlite3.Row: Post data or None if not found
        """
        query = "SELECT * FROM posts WHERE id = ?"
        results = self.execute_query(query, (post_id,))
        return results[0] if results else None
    
    def get_post_by_guid(self, guid):
        """Get a post by GUID.
        
        Args:
            guid (str): Post GUID
            
        Returns:
            sqlite3.Row: Post data or None if not found
        """
        query = "SELECT * FROM posts WHERE guid = ?"
        results = self.execute_query(query, (guid,))
        return results[0] if results else None
    
    def get_posts_by_feed(self, feed_id, limit=50, offset=0):
        """Get posts for a specific feed.
        
        Args:
            feed_id (int): Feed ID
            limit (int, optional): Maximum number of posts to return
            offset (int, optional): Offset for pagination
            
        Returns:
            list: List of post rows
        """
        query = """
        SELECT * FROM posts 
        WHERE feed_id = ? 
        ORDER BY published_date DESC
        LIMIT ? OFFSET ?
        """
        return self.execute_query(query, (feed_id, limit, offset))
    
    def get_latest_posts(self, limit=50):
        """Get the latest posts across all feeds.
        
        Args:
            limit (int, optional): Maximum number of posts to return
            
        Returns:
            list: List of post rows
        """
        query = """
        SELECT p.id, p.feed_id, p.title, p.link, p.guid, p.description, 
               p.published_date, p.created_at, f.name as feed_name, f.url as feed_url
        FROM posts p
        JOIN feeds f ON p.feed_id = f.id
        ORDER BY p.published_date DESC
        LIMIT ?
        """
        return self.execute_query(query, (limit,))
