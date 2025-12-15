# Project Status

> **Purpose**: Current work, active bugs, and recent changes (2-week rolling window)
> **Lifecycle**: Living (update daily/weekly during active development)

**Last Updated**: 2025-11-26
**Current Phase**: Stable / Production
**Version**: 0.1.0

---

## Quick Overview

| Aspect | Status | Notes |
|--------|--------|-------|
| Todoist API Integration | 🟢 | All endpoints working |
| Claude Code Registration | 🟢 | Registered with user scope |
| Test Coverage | 🟡 | Manual testing only |
| Known Bugs | 🟢 | None |

**Status Guide:** 🟢 Good | 🟡 Attention | 🔴 Critical | 🔵 In Progress

---

## Current Focus

**Completed Today:**
- ✅ Integration test passed - list projects (23 projects retrieved)
- ✅ Integration test passed - create task with due time

**Next Up:**
- [ ] Add automated tests
- [ ] Consider additional Todoist API features (sections, comments)

---

## Deployment Status

### Claude Code MCP Registration
- **Status**: Deployed (user scope)
- **Command**: `claude mcp add todoist -s user --env TODOIST_API_TOKEN=... -- /path/to/todoist-mcp/.venv/bin/python /path/to/todoist-mcp/todoist_mcp.py`
- **Verification**: `claude mcp list`

---

## Known Issues

None currently.

---

## Recent Achievements (Last 2 Weeks)

**Initial MCP Server Implementation** ✅
- Completed: 2025-11-26
- Full CRUD for tasks, projects, labels
- Natural language date support
- Todoist filter syntax support
- Markdown and JSON response formats

**Integration Tests Passed** ✅
- Completed: 2025-11-26
- List projects: Retrieved 23 projects
- Create task: Created "Play games with brothers at 8pm tonight" in Waiting For project

---

## Available Tools

| Tool | Status | Description |
|------|--------|-------------|
| `todoist_list_projects` | 🟢 | List all projects |
| `todoist_get_project` | 🟢 | Get project details |
| `todoist_create_project` | 🟢 | Create new project |
| `todoist_list_tasks` | 🟢 | List tasks with filters |
| `todoist_get_task` | 🟢 | Get task details |
| `todoist_create_task` | 🟢 | Create new task |
| `todoist_update_task` | 🟢 | Update task |
| `todoist_complete_task` | 🟢 | Mark complete |
| `todoist_reopen_task` | 🟢 | Reopen completed |
| `todoist_delete_task` | 🟢 | Delete task |
| `todoist_list_labels` | 🟢 | List labels |
| `todoist_create_label` | 🟢 | Create label |

---

## Next Steps (Priority Order)

1. **Add pytest test suite** with mocked API responses
2. **Consider sections support** - Todoist sections within projects
3. **Consider comments support** - Task comments

---

**Note**: Archive items older than 2 weeks to keep document focused.
