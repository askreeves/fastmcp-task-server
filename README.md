# FastMCP Task Manager Server

A comprehensive task management server built with FastMCP, ready for deployment on Railway.

## Features

### 🛠️ Tools (Actions)
- `create_task` - Create new tasks with title, description, priority, due date, and tags
- `get_task` - Retrieve a specific task by ID
- `update_task` - Update task details
- `delete_task` - Delete a task
- `list_tasks` - List all tasks with optional filtering by status or tag
- `complete_task` - Mark a task as completed
- `get_task_stats` - Get task statistics and overview
- `health_check` - Server health status

### 📄 Resources (Data Access)
- `task://{task_id}` - Get detailed formatted information about a specific task
- `tasks://all` - Get a formatted summary of all tasks

### 💬 Prompts (Templates)
- `task_planning_prompt` - A helpful prompt for task planning and organization

## Data Models

### Task Status
- `todo` - Planned but not started
- `in_progress` - Currently being worked on
- `completed` - Finished
- `cancelled` - Cancelled

### Priority Levels
- `low` - Nice to have, no rush
- `medium` - Normal priority
- `high` - Important, should be done soon
- `urgent` - Critical, needs immediate attention

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python main.py
```

The server will start on `http://localhost:8000`

### Deploy to Railway

1. Create a new Railway project
2. Connect your GitHub repository
3. Railway will automatically detect the Python app and deploy it
4. The server will be available at your Railway app URL

#### Manual Railway Deployment

If you prefer manual deployment:

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login and deploy:
```bash
railway login
railway init
railway up
```

## Environment Variables

- `PORT` - Server port (automatically set by Railway)
- `PYTHON_VERSION` - Python version (set to 3.11 in railway.toml)

## API Examples

### Creating a Task
```python
# Using the FastMCP tool
create_task({
    "title": "Complete project documentation",
    "description": "Write comprehensive docs for the new feature",
    "priority": "high",
    "due_date": "2025-07-15T10:00:00Z",
    "tags": ["documentation", "project"]
})
```

### Listing Tasks
```python
# Get all tasks
list_tasks()

# Get only completed tasks
list_tasks(status="completed")

# Get tasks with specific tag
list_tasks(tag="urgent")
```

### Getting Task Info
```python
# Get task by ID
get_task("1")

# Get formatted task resource
# Access resource: task://1
```

## Architecture

This FastMCP server uses:
- **FastMCP Framework** for MCP protocol handling
- **Pydantic** for data validation and serialization
- **In-memory storage** (replace with database for production)
- **Type hints** for automatic schema generation
- **Decorator-based** tool and resource definitions

## Production Considerations

For production use, consider:

1. **Database Integration**: Replace in-memory storage with PostgreSQL, MongoDB, etc.
2. **Authentication**: Add user authentication and authorization
3. **Persistence**: Implement data persistence across server restarts
4. **Monitoring**: Add logging and monitoring
5. **Rate Limiting**: Implement rate limiting for API calls
6. **Backup**: Set up data backup strategies

## Example Use Cases

1. **Personal Task Management**: Individual productivity tracking
2. **Team Collaboration**: Shared task lists and project management
3. **AI Assistant Integration**: Let AI assistants help manage your tasks
4. **Workflow Automation**: Integration with other tools and services
5. **Project Planning**: Break down projects into manageable tasks

## Testing the Server

Once deployed, you can test the server using any MCP-compatible client or by making direct HTTP requests to the endpoints.

### Health Check
```bash
curl https://your-railway-app.railway.app/health
```

### MCP Client Integration
Configure your MCP client to connect to your Railway URL to access all tools, resources, and prompts.

## Support

For FastMCP documentation and support:
- [FastMCP Documentation](https://gofastmcp.com)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Railway Documentation](https://docs.railway.app)