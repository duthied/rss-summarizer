# RSS Summarizer MCP Server

This MCP server provides tools for managing RSS feeds through the Model Context Protocol (MCP). It wraps the functionality of the RSS Summarizer's feed management and processing scripts, making them accessible as MCP tools.

## Features

The server provides the following tools:

- **setup**: Create necessary directories, setup virtual environment, install dependencies, and initialize database
- **add_feed**: Add a new feed with optional name, interval, and category
- **list_feeds**: List all active feeds with options to show inactive feeds or filter by category
- **show_posts**: Show posts from a specific feed with optional limit
- **remove_feed**: Remove a feed
- **activate_feed**: Activate a feed
- **add_category**: Add a new category with optional description
- **list_categories**: List all categories
- **update_category**: Update a category's name or description
- **delete_category**: Delete a category
- **init_db**: Initialize the database
- **process**: Process due feeds
- **test**: Run all tests
- **test_category**: Run category feature tests
- **clean**: Clean up temporary files

## Installation

The server is automatically installed and configured in the MCP settings file. It can be used with Claude or any other MCP-compatible client.

## Usage

Once the server is running, you can use the tools through the MCP client. For example, to add a new feed:

```
use_mcp_tool(
  server_name="rss-summarizer",
  tool_name="add_feed",
  arguments={
    "url": "https://example.com/feed.xml",
    "name": "Example Feed",
    "interval": 30,
    "category": "Technology"
  }
)
```

## Development

The server is built using the MCP SDK and TypeScript. It executes commands on the underlying RSS Summarizer Python scripts to perform the actual operations.

To build the server:

```bash
npm run build
```

To run the server manually:

```bash
node build/index.js
