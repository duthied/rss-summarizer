"""
Feed fetcher for the RSS Feed Aggregator.
Handles fetching and validating RSS feeds.
"""

import os
import logging
import requests
import feedparser
from urllib.parse import urlparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'feed_fetcher.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('feed_fetcher')

class FeedFetcher:
    """Handles fetching and validating RSS feeds."""
    
    def __init__(self, timeout=30, user_agent=None):
        """Initialize the feed fetcher.
        
        Args:
            timeout (int): Request timeout in seconds
            user_agent (str, optional): User agent string for requests
        """
        self.timeout = timeout
        self.user_agent = user_agent or 'RSS Feed Aggregator/1.0'
    
    def validate_url(self, url):
        """Validate if a URL is properly formatted.
        
        Args:
            url (str): URL to validate
            
        Returns:
            bool: True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except (ValueError, AttributeError) as e:
            logger.error("URL validation error: %s", e)
            return False
    
    def fetch_feed(self, url):
        """Fetch and parse an RSS feed.
        
        Args:
            url (str): URL of the feed to fetch
            
        Returns:
            tuple: (success, feed_data, error_message)
                success (bool): Whether the fetch was successful
                feed_data (dict): Parsed feed data if successful, None otherwise
                error_message (str): Error message if fetch failed, None otherwise
        """
        if not self.validate_url(url):
            return False, None, "Invalid URL format"
        
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/rss+xml, application/xml, text/xml, */*'
        }
        
        try:
            # First, try to fetch the feed with a HEAD request to check if it's accessible
            head_response = requests.head(
                url, 
                timeout=self.timeout,
                headers=headers,
                allow_redirects=True
            )
            
            # If the HEAD request fails, return an error
            if head_response.status_code >= 400:
                return False, None, f"Feed not accessible: HTTP {head_response.status_code}"
            
            # If the HEAD request succeeds, fetch the feed content
            response = requests.get(
                url, 
                timeout=self.timeout,
                headers=headers
            )
            
            # Check if the response is successful
            if response.status_code != 200:
                return False, None, f"Failed to fetch feed: HTTP {response.status_code}"
            
            # Parse the feed content
            feed_data = feedparser.parse(response.content)
            
            # Check if the feed is valid
            if feed_data.bozo and feed_data.get('bozo_exception'):
                return False, None, f"Invalid feed format: {feed_data.bozo_exception}"
            
            # Check if the feed has entries
            if not feed_data.entries and not getattr(feed_data, 'feed', None):
                return False, None, "Feed contains no entries and no feed information"
            
            return True, feed_data, None
            
        except requests.exceptions.Timeout:
            return False, None, f"Request timed out after {self.timeout} seconds"
        except requests.exceptions.ConnectionError:
            return False, None, "Connection error: Could not connect to server"
        except requests.exceptions.RequestException as e:
            return False, None, f"Request error: {str(e)}"
        except (feedparser.CharacterEncodingOverride, 
                feedparser.CharacterEncodingUnknown, 
                feedparser.NonXMLContentType) as e:
            return False, None, f"Feed parsing error: {str(e)}"
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Unexpected error fetching feed: %s", e)
            return False, None, f"Unexpected error: {str(e)}"
    
    def get_feed_info(self, feed_data):
        """Extract feed information from parsed feed data.
        
        Args:
            feed_data (dict): Parsed feed data from feedparser
            
        Returns:
            dict: Feed information including title, description, etc.
        """
        feed_info = {}
        
        if not feed_data or not hasattr(feed_data, 'feed'):
            return feed_info
        
        # Extract basic feed information
        feed = feed_data.feed
        feed_info['title'] = getattr(feed, 'title', None)
        feed_info['subtitle'] = getattr(feed, 'subtitle', None)
        feed_info['link'] = getattr(feed, 'link', None)
        feed_info['description'] = getattr(feed, 'description', None) or getattr(feed, 'subtitle', None)
        feed_info['language'] = getattr(feed, 'language', None)
        feed_info['updated'] = getattr(feed, 'updated', None)
        feed_info['updated_parsed'] = getattr(feed, 'updated_parsed', None)
        
        return feed_info
    
    def get_entries(self, feed_data):
        """Extract entries from parsed feed data.
        
        Args:
            feed_data (dict): Parsed feed data from feedparser
            
        Returns:
            list: List of feed entries
        """
        if not feed_data or not hasattr(feed_data, 'entries'):
            return []
        
        return feed_data.entries
    
    def process_entry(self, entry):
        """Process a feed entry to extract relevant information.
        
        Args:
            entry (dict): Feed entry from feedparser
            
        Returns:
            dict: Processed entry with standardized fields
        """
        processed = {}
        
        # Extract basic entry information
        processed['title'] = getattr(entry, 'title', None)
        processed['link'] = getattr(entry, 'link', None)
        
        # Use id as guid, fallback to link if not available
        processed['guid'] = getattr(entry, 'id', processed['link'])
        
        # Extract description (content or summary)
        if hasattr(entry, 'content') and entry.content:
            processed['description'] = entry.content[0].value
        else:
            processed['description'] = getattr(entry, 'summary', None)
        
        # Extract publication date
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published_tuple = entry.published_parsed
            processed['published_date'] = datetime(
                published_tuple[0], published_tuple[1], published_tuple[2],
                published_tuple[3], published_tuple[4], published_tuple[5]
            )
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            updated_tuple = entry.updated_parsed
            processed['published_date'] = datetime(
                updated_tuple[0], updated_tuple[1], updated_tuple[2],
                updated_tuple[3], updated_tuple[4], updated_tuple[5]
            )
        else:
            processed['published_date'] = datetime.now()
        
        return processed
