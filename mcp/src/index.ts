#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
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

class RssSummarizerServer {
  private server: Server;
  private pythonPath: string = 'python';
  private feedManagerPath: string = 'src/rss_aggregator/feed_manager.py';
  private feedProcessorPath: string = 'src/rss_aggregator/feed_processor.py';
  private venvActivate: string = '. venv/bin/activate &&';

  constructor() {
    this.server = new Server(
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

    this.setupToolHandlers();
    
    // Error handling
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
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

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const toolName = request.params.name;
      const args = request.params.arguments;

      try {
        let result: string;

        switch (toolName) {
          case 'setup':
            result = await this.setup();
            break;
          case 'add_feed':
            result = await this.addFeed(args);
            break;
          case 'list_feeds':
            result = await this.listFeeds(args);
            break;
          case 'show_posts':
            result = await this.showPosts(args);
            break;
          case 'remove_feed':
            result = await this.removeFeed(args);
            break;
          case 'activate_feed':
            result = await this.activateFeed(args);
            break;
          case 'add_category':
            result = await this.addCategory(args);
            break;
          case 'list_categories':
            result = await this.listCategories();
            break;
          case 'update_category':
            result = await this.updateCategory(args);
            break;
          case 'delete_category':
            result = await this.deleteCategory(args);
            break;
          case 'init_db':
            result = await this.initDb();
            break;
          case 'process':
            result = await this.process();
            break;
          case 'test':
            result = await this.runTests();
            break;
          case 'test_category':
            result = await this.testCategory();
            break;
          case 'clean':
            result = await this.clean();
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
  }

  // Tool implementations
  private async setup(): Promise<string> {
    const command = `mkdir -p logs && \\
      echo "Created logs directory" && \\
      echo "Setting up virtual environment..." && \\
      if [ -d "venv" ]; then \\
        echo "Virtual environment already exists"; \\
      else \\
        ${this.pythonPath} -m venv venv; \\
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
      echo "Setup complete. Activate the virtual environment with: source venv/bin/activate"`;
    
    return executeCommand(command);
  }

  private async addFeed(args: any): Promise<string> {
    if (!args.url) {
      throw new McpError(ErrorCode.InvalidParams, 'URL parameter is required');
    }

    let command = `${this.venvActivate} python ${this.feedManagerPath} add "${args.url}"`;
    
    if (args.name) {
      command += ` --name "${args.name}"`;
    }
    
    if (args.interval) {
      command += ` --interval ${args.interval}`;
    }
    
    if (args.category) {
      command += ` --category "${args.category}"`;
    }
    
    return executeCommand(command);
  }

  private async listFeeds(args: any): Promise<string> {
    let command = `${this.venvActivate} python ${this.feedManagerPath} list`;
    
    if (args.all) {
      command += ' --all';
    }
    
    if (args.category) {
      command += ` --category ${args.category}`;
    }
    
    return executeCommand(command);
  }

  private async showPosts(args: any): Promise<string> {
    if (!args.id) {
      throw new McpError(ErrorCode.InvalidParams, 'Feed ID parameter is required');
    }

    let command = `${this.venvActivate} python ${this.feedManagerPath} posts ${args.id}`;
    
    if (args.limit) {
      command += ` --limit ${args.limit}`;
    }
    
    return executeCommand(command);
  }

  private async removeFeed(args: any): Promise<string> {
    if (!args.id) {
      throw new McpError(ErrorCode.InvalidParams, 'Feed ID parameter is required');
    }

    const command = `${this.venvActivate} python ${this.feedManagerPath} remove ${args.id}`;
    return executeCommand(command);
  }

  private async activateFeed(args: any): Promise<string> {
    if (!args.id) {
      throw new McpError(ErrorCode.InvalidParams, 'Feed ID parameter is required');
    }

    const command = `${this.venvActivate} python ${this.feedManagerPath} activate ${args.id}`;
    return executeCommand(command);
  }

  private async addCategory(args: any): Promise<string> {
    if (!args.name) {
      throw new McpError(ErrorCode.InvalidParams, 'Category name parameter is required');
    }

    let command = `${this.venvActivate} python ${this.feedManagerPath} add-category "${args.name}"`;
    
    if (args.description) {
      command += ` --description "${args.description}"`;
    }
    
    return executeCommand(command);
  }

  private async listCategories(): Promise<string> {
    const command = `${this.venvActivate} python ${this.feedManagerPath} list-categories`;
    return executeCommand(command);
  }

  private async updateCategory(args: any): Promise<string> {
    if (!args.id) {
      throw new McpError(ErrorCode.InvalidParams, 'Category ID parameter is required');
    }

    let command = `${this.venvActivate} python ${this.feedManagerPath} update-category ${args.id}`;
    
    if (args.name) {
      command += ` --name "${args.name}"`;
    }
    
    if (args.description) {
      command += ` --description "${args.description}"`;
    }
    
    return executeCommand(command);
  }

  private async deleteCategory(args: any): Promise<string> {
    if (!args.id) {
      throw new McpError(ErrorCode.InvalidParams, 'Category ID parameter is required');
    }

    const command = `${this.venvActivate} python ${this.feedManagerPath} delete-category ${args.id}`;
    return executeCommand(command);
  }

  private async initDb(): Promise<string> {
    const command = `${this.venvActivate} python -c "from rss_aggregator.database import Database; db = Database(); db.close()"`;
    return executeCommand(command);
  }

  private async process(): Promise<string> {
    const command = `${this.venvActivate} python ${this.feedProcessorPath}`;
    return executeCommand(command);
  }

  private async runTests(): Promise<string> {
    const command = `${this.venvActivate} python -m unittest discover -p "test_*.py"`;
    return executeCommand(command);
  }

  private async testCategory(): Promise<string> {
    const command = `${this.venvActivate} python test_category.py`;
    return executeCommand(command);
  }

  private async clean(): Promise<string> {
    const command = `find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \\
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
      echo "Cleaned up temporary files"`;
    
    return executeCommand(command);
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('RSS Summarizer MCP server running on stdio');
  }
}

const server = new RssSummarizerServer();
server.run().catch(console.error);
