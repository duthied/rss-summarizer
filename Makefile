# RSS Feed Aggregator Makefile
# Provides simplified commands for managing RSS feeds

PYTHON = python
FEED_MANAGER = src/rss_aggregator/feed_manager.py
FEED_PROCESSOR = src/rss_aggregator/feed_processor.py

# Default target
.PHONY: help
help:
	@echo "RSS Feed Aggregator - Available commands:"
	@echo ""
	@echo "  make setup              - Create necessary directories + setup virtual environment + initialize database"
	@echo "  make add-feed URL=...   - Add a new feed"
	@echo "                            Optional: NAME=\"Feed Name\" INTERVAL=60 CATEGORY=\"Category Name\""
	@echo "  make list-feeds         - List all active feeds"
	@echo "                            Optional: ALL=1 (include inactive feeds) CATEGORY=1 (filter by category ID)"
	@echo "  make show-posts ID=...  - Show posts from a feed"
	@echo "                            Optional: LIMIT=10"
	@echo "  make remove-feed ID=... - Remove a feed"
	@echo "  make activate-feed ID=... - Activate a feed"
	@echo "  make add-category NAME=... - Add a new category"
	@echo "                            Optional: DESC=\"Category description\""
	@echo "  make list-categories    - List all categories"
	@echo "  make update-category ID=... - Update a category"
	@echo "                            Optional: NAME=\"New name\" DESC=\"New description\""
	@echo "  make delete-category ID=... - Delete a category"
	@echo "  make init-db            - Initialize the database"
	@echo "  make process            - Process due feeds"
	@echo "  make test               - Run all tests"
	@echo "  make test-category      - Run category feature tests"
	@echo "  make clean              - Clean up temporary files"
	@echo ""
	@echo "Examples:"
	@echo "  make add-feed URL=https://example.com/feed.xml NAME=\"Example Feed\" INTERVAL=30 CATEGORY=\"Technology\""
	@echo "  make show-posts ID=1 LIMIT=20"
	@echo "  make add-category NAME=\"Technology\" DESC=\"Tech news and updates\""
	@echo "  make list-feeds CATEGORY=1"

# Create necessary directories, setup virtual environment, install dependencies, and initialize database
.PHONY: setup
setup:
	@mkdir -p logs
	@echo "Created logs directory"
	@echo "Setting up virtual environment..."
	@if [ -d "venv" ]; then \
		echo "Virtual environment already exists"; \
	else \
		$(PYTHON) -m venv venv; \
		echo "Virtual environment created"; \
	fi
	@echo "Installing dependencies..."
	@. venv/bin/activate && pip install -r requirements.txt && \
	echo "Dependencies installed" && \
	echo "Installing package in development mode..." && \
	pip install -e . && \
	echo "Package installed" && \
	echo "Initializing database..." && \
	python -c "from rss_aggregator.database import Database; db = Database(); db.close()" && \
	echo "Database initialized successfully"
	@echo "Setup complete. Activate the virtual environment with: source venv/bin/activate"

# Add a new feed
.PHONY: add-feed
add-feed:
	@if [ -z "$(URL)" ]; then \
		echo "Error: URL parameter is required"; \
		echo "Usage: make add-feed URL=https://example.com/feed.xml [NAME=\"Feed Name\"] [INTERVAL=60] [CATEGORY=\"Category\"]"; \
		exit 1; \
	fi; \
	cmd=". venv/bin/activate && python $(FEED_MANAGER) add $(URL)"; \
	if [ ! -z "$(NAME)" ]; then \
		cmd="$$cmd --name \"$(NAME)\""; \
	fi; \
	if [ ! -z "$(INTERVAL)" ]; then \
		cmd="$$cmd --interval $(INTERVAL)"; \
	fi; \
	if [ ! -z "$(CATEGORY)" ]; then \
		cmd="$$cmd --category \"$(CATEGORY)\""; \
	fi; \
	echo "Executing: $$cmd"; \
	eval $$cmd

# List all feeds
.PHONY: list-feeds
list-feeds:
	@cmd=". venv/bin/activate && python $(FEED_MANAGER) list"; \
	if [ ! -z "$(ALL)" ] && [ "$(ALL)" = "1" ]; then \
		cmd="$$cmd --all"; \
	fi; \
	if [ ! -z "$(CATEGORY)" ]; then \
		cmd="$$cmd --category $(CATEGORY)"; \
	fi; \
	echo "Executing: $$cmd"; \
	eval $$cmd

# Show posts from a feed
.PHONY: show-posts
show-posts:
	@if [ -z "$(ID)" ]; then \
		echo "Error: ID parameter is required"; \
		echo "Usage: make show-posts ID=1 [LIMIT=10]"; \
		exit 1; \
	fi; \
	cmd=". venv/bin/activate && python $(FEED_MANAGER) posts $(ID)"; \
	if [ ! -z "$(LIMIT)" ]; then \
		cmd="$$cmd --limit $(LIMIT)"; \
	fi; \
	echo "Executing: $$cmd"; \
	eval $$cmd

# Remove a feed
.PHONY: remove-feed
remove-feed:
	@if [ -z "$(ID)" ]; then \
		echo "Error: ID parameter is required"; \
		echo "Usage: make remove-feed ID=1"; \
		exit 1; \
	fi; \
	echo "Executing: . venv/bin/activate && python $(FEED_MANAGER) remove $(ID)"; \
	. venv/bin/activate && python $(FEED_MANAGER) remove $(ID)

# Activate a feed
.PHONY: activate-feed
activate-feed:
	@if [ -z "$(ID)" ]; then \
		echo "Error: ID parameter is required"; \
		echo "Usage: make activate-feed ID=1"; \
		exit 1; \
	fi; \
	echo "Executing: . venv/bin/activate && python $(FEED_MANAGER) activate $(ID)"; \
	. venv/bin/activate && python $(FEED_MANAGER) activate $(ID)

# Initialize database
.PHONY: init-db
init-db:
	@echo "Initializing database..."
	@. venv/bin/activate && python -c "from rss_aggregator.database import Database; db = Database(); db.close()"
	@echo "Database initialized successfully"

# Process due feeds
.PHONY: process
process:
	@echo "Executing: . venv/bin/activate && python $(FEED_PROCESSOR)"; \
	. venv/bin/activate && python $(FEED_PROCESSOR)

# Add a new category
.PHONY: add-category
add-category:
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME parameter is required"; \
		echo "Usage: make add-category NAME=\"Category Name\" [DESC=\"Category description\"]"; \
		exit 1; \
	fi; \
	cmd=". venv/bin/activate && python $(FEED_MANAGER) add-category \"$(NAME)\""; \
	if [ ! -z "$(DESC)" ]; then \
		cmd="$$cmd --description \"$(DESC)\""; \
	fi; \
	echo "Executing: $$cmd"; \
	eval $$cmd

# List all categories
.PHONY: list-categories
list-categories:
	@echo "Executing: . venv/bin/activate && python $(FEED_MANAGER) list-categories"; \
	. venv/bin/activate && python $(FEED_MANAGER) list-categories

# Update a category
.PHONY: update-category
update-category:
	@if [ -z "$(ID)" ]; then \
		echo "Error: ID parameter is required"; \
		echo "Usage: make update-category ID=1 [NAME=\"New name\"] [DESC=\"New description\"]"; \
		exit 1; \
	fi; \
	cmd=". venv/bin/activate && python $(FEED_MANAGER) update-category $(ID)"; \
	if [ ! -z "$(NAME)" ]; then \
		cmd="$$cmd --name \"$(NAME)\""; \
	fi; \
	if [ ! -z "$(DESC)" ]; then \
		cmd="$$cmd --description \"$(DESC)\""; \
	fi; \
	echo "Executing: $$cmd"; \
	eval $$cmd

# Delete a category
.PHONY: delete-category
delete-category:
	@if [ -z "$(ID)" ]; then \
		echo "Error: ID parameter is required"; \
		echo "Usage: make delete-category ID=1"; \
		exit 1; \
	fi; \
	echo "Executing: . venv/bin/activate && python $(FEED_MANAGER) delete-category $(ID)"; \
	. venv/bin/activate && python $(FEED_MANAGER) delete-category $(ID)

# Run all tests
.PHONY: test
test:
	@echo "Running all tests..."
	@. venv/bin/activate && python -m unittest discover -p "test_*.py"

# Run category feature tests
.PHONY: test-category
test-category:
	@echo "Running category feature tests..."
	@. venv/bin/activate && python test_category.py

# Clean up temporary files
.PHONY: clean
clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".DS_Store" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name "*.egg" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".coverage" -exec rm -rf {} +
	@find . -type d -name "htmlcov" -exec rm -rf {} +
	@find . -type d -name ".tox" -exec rm -rf {} +
	@echo "Cleaned up temporary files"
