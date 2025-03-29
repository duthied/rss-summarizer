#!/usr/bin/env node
import { Server, StdioServerTransport, CallToolRequestSchema, ListToolsRequestSchema, McpError, ErrorCode } from '@modelcontextprotocol/sdk';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

// Helper function to execute commands and return the output
async function executeCommand(command: string): Promise<string> {
  try {
    const { stdout, stderr } = await execAsync(command);
    if (stderr) {
      console.error(`Command stderr: ${stderr}`);
    }
    return stdout;
  } catch (error: any) {
    console.error(`Command execution error: ${error.message}`);
    if (error.stderr) {
      console.error(`Command stderr: ${error.stderr}`);
    }
    throw new McpError(ErrorCode.InternalError, error.message);
  }
}

async function main() {
  const server = new Server(
    {
      name: 'rss-summarizer-server',
      version: '0.1.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Define paths
  const pythonPath = 'python';
  const feedManagerPath = 'src/rss_aggregator/feed_manager.py';
  const feedProcessorPath = 'src/rss_aggregator/feed_processor.py';
  const venvActivate = '. venv/bin/activate &&';

  // List available tools
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [
      {
        name: 'setup',
        description: 'Create necessary directories, setup virtual environment, install dependencies, and initialize database',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'add_feed',
        description: 'Add a new feed',
        inputSchema: {
          type: 'object',
          properties: {
            url: {
              type: 'string',
              description: 'Feed URL',
            },
            name: {
              type: 'string',
              description: 'Feed name (optional)',
            },
            interval: {
              type: 'number',
              description: 'Update interval in minutes (default: 60)',
            },
            category: {
              type: 'string',
              description: 'Category name or ID (optional)',
            },
          },
          required: ['url'],
        },
      },
      {
        name: 'list_feeds',
        description: 'List all active feeds',
        inputSchema: {
          type: 'object',
          properties: {
            all: {
              type: 'boolean',
              description: 'Show all feeds, including inactive ones',
            },
            category: {
              type: 'number',
              description: 'Filter by category ID',
            },
          },
        },
      },
      {
        name: 'show_posts',
        description: 'Show posts from a feed',
        inputSchema: {
          type: 'object',
          properties: {
            id: {
              type: 'number',
              description: 'Feed ID',
            },
            limit: {
              type: 'number',
              description: 'Maximum number of posts to show (default: 10)',
            },
          },
          required: ['id'],
        },
      },
      {
        name: 'remove_feed',
        description: 'Remove a feed',
        inputSchema: {
          type: 'object',
          properties: {
            id: {
              type: 'number',
              description: 'Feed ID',
            },
          },
          required: ['id'],
        },
      },
      {
        name: 'activate_feed',
        description: 'Activate a feed',
        inputSchema: {
          type: 'object',
          properties: {
            id: {
              type: 'number',
              description: 'Feed ID',
            },
          },
          required: ['id'],
        },
      },
      {
        name: 'add_category',
        description: 'Add a new category',
        inputSchema: {
          type: 'object',
          properties: {
            name: {
              type: 'string',
              description: 'Category name',
            },
            description: {
              type: 'string',
              description: 'Category description (optional)',
            },
          },
          required: ['name'],
        },
      },
      {
        name: 'list_categories',
        description: 'List all categories',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'update_category',
        description: 'Update a category',
        inputSchema: {
          type: 'object',
          properties: {
            id: {
              type: 'number',
              description: 'Category ID',
            },
            name: {
              type: 'string',
              description: 'New category name (optional)',
            },
            description: {
              type: 'string',
              description: 'New category description (optional)',
            },
          },
          required: ['id'],
        },
      },
      {
        name: 'delete_category',
        description: 'Delete a category',
        inputSchema: {
          type: 'object',
          properties: {
            id: {
              type: 'number',
              description: 'Category ID',
            },
          },
          required: ['id'],
        },
      },
      {
        name: 'init_db',
        description: 'Initialize the database',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'process',
        description: 'Process due feeds',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'test',
        description: 'Run all tests',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'test_category',
        description: 'Run category feature tests',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'clean',
        description: 'Clean up temporary files',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
    ],
  }));

  // Handle tool calls
  server.setRequestHandler(CallToolRequestSchema, async (request: any) => {
    const toolName = request.params.name;
    const args = request.params.arguments;

    try {
      let result: string;

      switch (toolName) {
        case 'setup':
          result = await executeCommand(`mkdir -p logs && \\
            echo "Created logs directory" && \\
            echo "Setting up virtual environment..." && \\
            if [ -d "venv" ]; then \\
              echo "Virtual environment already exists"; \\
            else \\
              ${pythonPath} -m venv venv; \\
              echo "Virtual environment created"; \\
            fi && \\
            echo "Installing dependencies..." && \\
            . venv/bin/activate && pip install -r requirements.txt && \\
            echo "Dependencies installed" && \\
            echo "Installing package in development mode..." && \\
            pip install -e . && \\
            echo "Package installed" && \\
            echo "Initializing database..." && \\
            python -c "from rss_aggregator.database import Database; db = Database(); db.close()" && \\
            echo "Database initialized successfully" && \\
            echo "Setup complete. Activate the virtual environment with: source venv/bin/activate"`);
          break;

        case 'add_feed':
          if (!args.url) {
            throw new McpError(ErrorCode.InvalidParams, 'URL parameter is required');
          }

          let addFeedCmd = `${venvActivate} python ${feedManagerPath} add "${args.url}"`;
          
          if (args.name) {
            addFeedCmd += ` --name "${args.name}"`;
          }
          
          if (args.interval) {
            addFeedCmd += ` --interval ${args.interval}`;
          }
          
          if (args.category) {
            addFeedCmd += ` --category "${args.category}"`;
          }
          
          result = await executeCommand(addFeedCmd);
          break;

        case 'list_feeds':
          let listFeedsCmd = `${venvActivate} python ${feedManagerPath} list`;
          
          if (args.all) {
            listFeedsCmd += ' --all';
          }
          
          if (args.category) {
            listFeedsCmd += ` --category ${args.category}`;
          }
          
          result = await executeCommand(listFeedsCmd);
          break;

        case 'show_posts':
          if (!args.id) {
            throw new McpError(ErrorCode.InvalidParams, 'Feed ID parameter is required');
          }

          let showPostsCmd = `${venvActivate} python ${feedManagerPath} posts ${args.id}`;
          
          if (args.limit) {
            showPostsCmd += ` --limit ${args.limit}`;
          }
          
          result = await executeCommand(showPostsCmd);
          break;

        case 'remove_feed':
          if (!args.id) {
            throw new McpError(ErrorCode.InvalidParams, 'Feed ID parameter is required');
          }

          result = await executeCommand(`${venvActivate} python ${feedManagerPath} remove ${args.id}`);
          break;

        case 'activate_feed':
          if (!args.id) {
            throw new McpError(ErrorCode.InvalidParams, 'Feed ID parameter is required');
          }

          result = await executeCommand(`${venvActivate} python ${feedManagerPath} activate ${args.id}`);
          break;

        case 'add_category':
          if (!args.name) {
            throw new McpError(ErrorCode.InvalidParams, 'Category name parameter is required');
          }

          let addCategoryCmd = `${venvActivate} python ${feedManagerPath} add-category "${args.name}"`;
          
          if (args.description) {
            addCategoryCmd += ` --description "${args.description}"`;
          }
          
          result = await executeCommand(addCategoryCmd);
          break;

        case 'list_categories':
          result = await executeCommand(`${venvActivate} python ${feedManagerPath} list-categories`);
          break;

        case 'update_category':
          if (!args.id) {
            throw new McpError(ErrorCode.InvalidParams, 'Category ID parameter is required');
          }

          let updateCategoryCmd = `${venvActivate} python ${feedManagerPath} update-category ${args.id}`;
          
          if (args.name) {
            updateCategoryCmd += ` --name "${args.name}"`;
          }
          
          if (args.description) {
            updateCategoryCmd += ` --description "${args.description}"`;
          }
          
          result = await executeCommand(updateCategoryCmd);
          break;

        case 'delete_category':
          if (!args.id) {
            throw new McpError(ErrorCode.InvalidParams, 'Category ID parameter is required');
          }

          result = await executeCommand(`${venvActivate} python ${feedManagerPath} delete-category ${args.id}`);
          break;

        case 'init_db':
          result = await executeCommand(`${venvActivate} python -c "from rss_aggregator.database import Database; db = Database(); db.close()"`);
          break;

        case 'process':
          result = await executeCommand(`${venvActivate} python ${feedProcessorPath}`);
          break;

        case 'test':
          result = await executeCommand(`${venvActivate} python -m unittest discover -p "test_*.py"`);
          break;

        case 'test_category':
          result = await executeCommand(`${venvActivate} python test_category.py`);
          break;

        case 'clean':
          result = await executeCommand(`find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \\
            find . -type f -name "*.pyc" -delete && \\
            find . -type f -name "*.pyo" -delete && \\
            find . -type f -name "*.pyd" -delete && \\
            find . -type f -name ".DS_Store" -delete && \\
            find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true && \\
            find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true && \\
            find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true && \\
            find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true && \\
            find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true && \\
            find . -type d -name ".tox" -exec rm -rf {} + 2>/dev/null || true && \\
            echo "Cleaned up temporary files"`);
          break;

        default:
          throw new McpError(
            ErrorCode.MethodNotFound,
            `Unknown tool: ${toolName}`
          );
      }

      return {
        content: [
          {
            type: 'text',
            text: result,
          },
        ],
      };
    } catch (error) {
      if (error instanceof McpError) {
        throw error;
      }
      throw new McpError(
        ErrorCode.InternalError,
        `Error executing tool ${toolName}: ${(error as Error).message}`
      );
    }
  });

  // Error handling
  server.onerror = (error: any) => console.error('[MCP Error]', error);
  process.on('SIGINT', async () => {
    await server.close();
    process.exit(0);
  });

  // Connect to stdio transport
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('RSS Summarizer MCP server running on stdio');
}

main().catch(console.error);
