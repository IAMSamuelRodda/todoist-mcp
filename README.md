# Todoist MCP Server

MCP (Model Context Protocol) server for Todoist integration, allowing AI assistants to manage your tasks, projects, and labels.

## Features

- **Tasks**: Create, list, update, complete, reopen, and delete tasks
- **Projects**: List and create projects, including sub-projects
- **Labels**: List and create labels for task organization
- **Filters**: Support for Todoist filter syntax (`today`, `overdue`, `p1`, etc.)
- **Natural language dates**: Use `tomorrow`, `next Monday`, `every week`, etc.

## Setup

### 1. Get Your Todoist API Token

1. Open Todoist (web or app)
2. Go to **Settings** → **Integrations** → **Developer**
3. Copy your **API token**

### 2. Install Dependencies

```bash
cd repos/todoist-mcp
python -m venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 3. Configure Claude Code

Add to your Claude Code MCP settings (`~/.claude/mcp_settings.json`):

```json
{
  "mcpServers": {
    "todoist": {
      "command": "/home/samuel/repos/todoist-mcp/.venv/bin/python",
      "args": ["/home/samuel/repos/todoist-mcp/todoist_mcp.py"],
      "env": {
        "TODOIST_API_TOKEN": "your-api-token-here"
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `todoist_list_projects` | List all projects |
| `todoist_get_project` | Get project details |
| `todoist_create_project` | Create a new project |
| `todoist_list_tasks` | List tasks with filters |
| `todoist_get_task` | Get task details |
| `todoist_create_task` | Create a new task |
| `todoist_update_task` | Update a task |
| `todoist_complete_task` | Mark task complete |
| `todoist_reopen_task` | Reopen a completed task |
| `todoist_delete_task` | Delete a task |
| `todoist_list_labels` | List all labels |
| `todoist_create_label` | Create a new label |

## Usage Examples

Once configured, you can ask Claude:

- "Show me my tasks for today"
- "Create a task to review the quarterly report due next Friday"
- "List all my projects"
- "Mark task 123456789 as complete"
- "What are my overdue tasks?"
- "Create a high-priority task in my Work project"

## Filter Syntax

The `todoist_list_tasks` tool supports Todoist's filter syntax:

- `today` - Tasks due today
- `tomorrow` - Tasks due tomorrow
- `overdue` - Overdue tasks
- `p1`, `p2`, `p3`, `p4` - Filter by priority
- `no due date` - Tasks without due dates
- `7 days` - Tasks due in the next 7 days
- `@label_name` - Tasks with specific label
- `#project_name` - Tasks in specific project

## License

MIT
