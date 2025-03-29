# RSS Feed Aggregator

A Python-based RSS feed aggregator that fetches and stores posts from RSS feeds in a SQLite database. The system is designed to run periodically via a cron job, checking for feeds that are due for updates based on their individual update intervals.

## Features

- Fetch RSS feeds and store posts in a SQLite database
- Track feed fetch status and handle errors with exponential backoff
- Process only feeds that are due for updates based on their individual intervals
- Command-line utilities for managing feeds
- Comprehensive logging and error handling

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/rss-summarizer.git
   cd rss-summarizer
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create necessary directories:
   ```
   mkdir -p logs
   ```

## Usage

### Managing Feeds

The `feed_manager.py` script provides commands to add, list, and remove feeds:

#### Add a feed:
```
python src/rss_aggregator/feed_manager.py add https://example.com/feed.xml --name "Example Feed" --interval 60
```

#### List all feeds:
```
python src/rss_aggregator/feed_manager.py list
```

#### Show posts from a feed:
```
python src/rss_aggregator/feed_manager.py posts 1 --limit 20
```

#### Remove a feed:
```
python src/rss_aggregator/feed_manager.py remove 1
```

#### Activate a previously deactivated feed:
```
python src/rss_aggregator/feed_manager.py activate 1
```

### Processing Feeds

The `feed_processor.py` script fetches and processes feeds that are due for updates:

```
python src/rss_aggregator/feed_processor.py
```

This script is designed to be run periodically via a cron job.

## Setting Up a Cron Job

To run the feed processor automatically at regular intervals, set up a cron job:

1. Open your crontab file:
   ```
   crontab -e
   ```

2. Add a line to run the processor every 15 minutes:
   ```
   */15 * * * * cd /path/to/rss-summarizer && /path/to/python /path/to/rss-summarizer/src/rss_aggregator/feed_processor.py >> /path/to/rss-summarizer/logs/processor.log 2>&1
   ```

   Replace `/path/to/rss-summarizer` and `/path/to/python` with the actual paths on your system.

## Database Schema

The system uses a SQLite database with two main tables:

- `feeds`: Stores feed URLs, names, update intervals, and status information
- `posts`: Stores individual posts with references to their source feeds

For more details, see the `schema.sql` file.

## Error Handling

The system implements several error handling mechanisms:

- Feed validation before fetching
- Proper HTTP error handling
- Exponential backoff for problematic feeds
- Comprehensive logging of all operations

## Logs

Logs are stored in the `logs` directory:

- `database.log`: Database operations
- `feed_fetcher.log`: Feed fetching operations
- `feed_manager.log`: Feed management operations
- `processor.log`: Main processor operations

## License

This project is licensed under the MIT License - see the LICENSE file for details.
