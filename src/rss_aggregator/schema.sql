-- RSS Feed Aggregator Database Schema

-- Feeds table to store feed information and status
CREATE TABLE IF NOT EXISTS feeds (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    name TEXT,
    update_interval INTEGER DEFAULT 60, -- Minutes between updates
    last_fetched TIMESTAMP,
    fetch_status INTEGER DEFAULT 0,     -- 0=success, 1=error
    error_message TEXT,
    error_count INTEGER DEFAULT 0,
    last_error TIMESTAMP,
    active INTEGER DEFAULT 1,           -- Boolean: 1=active, 0=inactive
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Posts table to store feed items
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    feed_id INTEGER,
    title TEXT,
    link TEXT,
    guid TEXT UNIQUE,
    description TEXT,
    published_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feed_id) REFERENCES feeds(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_posts_feed_id ON posts(feed_id);
CREATE INDEX IF NOT EXISTS idx_posts_guid ON posts(guid);
CREATE INDEX IF NOT EXISTS idx_feeds_last_fetched ON feeds(last_fetched);
CREATE INDEX IF NOT EXISTS idx_feeds_active ON feeds(active);
