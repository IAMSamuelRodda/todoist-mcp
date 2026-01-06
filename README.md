# Todoist MCP Server

MCP server for Todoist task management. Provides 12 tools for tasks, projects, and labels.

## Features

- **Tasks**: Create, list, update, complete, reopen, and delete tasks
- **Projects**: List and create projects, including sub-projects
- **Labels**: List and create labels for task organization
- **Filters**: Support for Todoist filter syntax (`today`, `overdue`, `p1`, etc.)
- **Natural language dates**: Use `tomorrow`, `next Monday`, `every week`, etc.

## Installation

### Option 1: uvx (Recommended)

Zero-install method using [uv](https://docs.astral.sh/uv/). Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "todoist": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/IAMSamuelRodda/todoist-mcp", "todoist-mcp"],
      "env": {
        "TODOIST_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

### Option 2: Local Clone

```bash
mkdir -p ~/.claude/mcp-servers
git clone https://github.com/IAMSamuelRodda/todoist-mcp.git ~/.claude/mcp-servers/todoist-mcp
cd ~/.claude/mcp-servers/todoist-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "todoist": {
      "command": "~/.claude/mcp-servers/todoist-mcp/.venv/bin/python",
      "args": ["~/.claude/mcp-servers/todoist-mcp/todoist_mcp.py"],
      "env": {
        "TODOIST_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

### Get Your API Token

1. Open Todoist (web or app)
2. Go to **Settings** → **Integrations** → **Developer**
3. Copy your **API token**

## Updating

### uvx users

```bash
uv cache clean todoist-mcp
```

### Local clone users

```bash
cd ~/.claude/mcp-servers/todoist-mcp
git pull
source .venv/bin/activate
pip install -r requirements.txt
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
