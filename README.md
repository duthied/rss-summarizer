# RSS Feed Aggregator

A Python-based RSS feed aggregator that fetches and stores posts from RSS feeds in a SQLite database. The system is designed to run periodically via a cron job, checking for feeds that are due for updates based on their individual update intervals.

## Features

- Fetch RSS feeds and store posts in a SQLite database
- Track feed fetch status and handle errors with exponential backoff
- Process only feeds that are due for updates based on their individual intervals
- Organize feeds into categories for better content management
- Command-line utilities for managing feeds and categories
- Comprehensive logging and error handling

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/rss-summarizer.git
   cd rss-summarizer
   ```

2. Use the setup target in the Makefile (recommended):
   ```
   make setup
   ```
   
   This will:
   - Create necessary directories
   - Set up a virtual environment
   - Install dependencies
   - Install the package in development mode
   - Initialize the database

   After setup, activate the virtual environment:
   ```
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Alternatively, you can set up manually:
   ```
   # Create a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Install the package in development mode
   pip install -e .
   
   # Create necessary directories
   mkdir -p logs
   ```

## Usage

### Managing Feeds

The `feed_manager.py` script provides commands to add, list, and remove feeds:

#### Add a feed:
```
python src/rss_aggregator/feed_manager.py add https://example.com/feed.xml --name "Example Feed" --interval 60 --category "Technology"
```

#### List all feeds:
```
python src/rss_aggregator/feed_manager.py list
```

#### List feeds in a specific category:
```
python src/rss_aggregator/feed_manager.py list --category 1
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

### Managing Categories

The `feed_manager.py` script also provides commands to manage categories:

#### Add a category:
```
python src/rss_aggregator/feed_manager.py add-category "Technology" --description "Tech news and updates"
```

#### List all categories:
```
python src/rss_aggregator/feed_manager.py list-categories
```

#### Update a category:
```
python src/rss_aggregator/feed_manager.py update-category 1 --name "Tech News" --description "Latest technology news"
```

#### Delete a category:
```
python src/rss_aggregator/feed_manager.py delete-category 1
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

The system uses a SQLite database with three main tables:

- `categories`: Stores category names and descriptions
- `feeds`: Stores feed URLs, names, categories, update intervals, and status information
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

## Using the Makefile

The project includes a Makefile that provides simplified commands for setting up the project and managing feeds and categories:

### Setup:
```
# Set up the project (create directories, virtual environment, install dependencies, initialize database)
make setup
```

### Feed Management:
```
# Add a feed with a category
make add-feed URL=https://example.com/feed.xml NAME="Example Feed" CATEGORY="Technology"

# List feeds in a specific category
make list-feeds CATEGORY=1

# Show all feeds including inactive ones
make list-feeds ALL=1
```

### Category Management:
```
# Add a category
make add-category NAME="Technology" DESC="Tech news and updates"

# List all categories
make list-categories

# Update a category
make update-category ID=1 NAME="Tech News" DESC="Latest technology news"

# Delete a category
make delete-category ID=1
```

## Testing

The project includes tests for the category feature. You can run the tests using the Makefile:

```
# Run all tests
make test

# Run only the category feature tests
make test-category
```

Or you can run the tests directly:

```
python test_category.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
