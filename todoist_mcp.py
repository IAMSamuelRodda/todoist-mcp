#!/usr/bin/env python3
"""
MCP Server for Todoist.

This server provides tools to interact with the Todoist API, including
task management, project organization, and label handling.

API Token: Set TODOIST_API_TOKEN environment variable
           Get from: Todoist Settings → Integrations → Developer → API token
"""

import json
import os
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Initialize the MCP server
mcp = FastMCP("todoist_mcp")

# Constants
API_BASE_URL = "https://api.todoist.com/rest/v2"
CHARACTER_LIMIT = 25000


# =============================================================================
# Enums
# =============================================================================


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


class TaskPriority(int, Enum):
    """Todoist priority levels (1=lowest, 4=highest)."""

    P1 = 1  # Lowest
    P2 = 2
    P3 = 3
    P4 = 4  # Highest (red)


# =============================================================================
# Pydantic Input Models
# =============================================================================


class ListProjectsInput(BaseModel):
    """Input model for listing projects."""

    model_config = ConfigDict(str_strip_whitespace=True)

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class GetProjectInput(BaseModel):
    """Input model for getting a single project."""

    model_config = ConfigDict(str_strip_whitespace=True)

    project_id: str = Field(
        ..., description="The project ID (e.g., '2203306141')", min_length=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class CreateProjectInput(BaseModel):
    """Input model for creating a project."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        description="Name of the project (e.g., 'Work Tasks', 'Home Renovation')",
        min_length=1,
        max_length=500,
    )
    parent_id: Optional[str] = Field(
        default=None, description="Parent project ID to create as a sub-project"
    )
    color: Optional[str] = Field(
        default=None,
        description="Color name: berry_red, red, orange, yellow, olive_green, lime_green, green, mint_green, teal, sky_blue, light_blue, blue, grape, violet, lavender, magenta, salmon, charcoal, grey, taupe",
    )
    is_favorite: bool = Field(default=False, description="Whether to mark as favorite")


class ListTasksInput(BaseModel):
    """Input model for listing tasks."""

    model_config = ConfigDict(str_strip_whitespace=True)

    project_id: Optional[str] = Field(
        default=None, description="Filter by project ID. If not set, returns all tasks."
    )
    label: Optional[str] = Field(
        default=None, description="Filter by label name (e.g., 'urgent', 'work')"
    )
    filter: Optional[str] = Field(
        default=None,
        description="Todoist filter query (e.g., 'today', 'overdue', 'p1', 'due before: tomorrow')",
    )
    limit: int = Field(
        default=50, description="Maximum tasks to return", ge=1, le=200
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class GetTaskInput(BaseModel):
    """Input model for getting a single task."""

    model_config = ConfigDict(str_strip_whitespace=True)

    task_id: str = Field(
        ..., description="The task ID (e.g., '2995104339')", min_length=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class CreateTaskInput(BaseModel):
    """Input model for creating a task."""

    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(
        ...,
        description="Task content/title (e.g., 'Buy groceries', 'Review PR #123')",
        min_length=1,
        max_length=5000,
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed task description",
        max_length=16000,
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID to add task to. If not set, adds to Inbox.",
    )
    due_string: Optional[str] = Field(
        default=None,
        description="Natural language due date (e.g., 'tomorrow', 'next Monday', 'Jan 15', 'every week')",
    )
    due_date: Optional[str] = Field(
        default=None,
        description="Due date in YYYY-MM-DD format (e.g., '2024-01-15')",
    )
    priority: Optional[TaskPriority] = Field(
        default=None,
        description="Priority 1-4 (4 is highest/red, 1 is lowest)",
    )
    labels: Optional[list[str]] = Field(
        default=None,
        description="List of label names to apply (e.g., ['work', 'urgent'])",
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="Parent task ID to create as a subtask",
    )

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: Optional[str]) -> Optional[str]:
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("due_date must be in YYYY-MM-DD format")
        return v


class UpdateTaskInput(BaseModel):
    """Input model for updating a task."""

    model_config = ConfigDict(str_strip_whitespace=True)

    task_id: str = Field(..., description="The task ID to update", min_length=1)
    content: Optional[str] = Field(
        default=None,
        description="New task content/title",
        max_length=5000,
    )
    description: Optional[str] = Field(
        default=None,
        description="New task description",
        max_length=16000,
    )
    due_string: Optional[str] = Field(
        default=None,
        description="Natural language due date (e.g., 'tomorrow', 'next Monday')",
    )
    due_date: Optional[str] = Field(
        default=None,
        description="Due date in YYYY-MM-DD format",
    )
    priority: Optional[TaskPriority] = Field(
        default=None,
        description="Priority 1-4 (4 is highest)",
    )
    labels: Optional[list[str]] = Field(
        default=None,
        description="List of label names (replaces existing labels)",
    )


class CompleteTaskInput(BaseModel):
    """Input model for completing a task."""

    model_config = ConfigDict(str_strip_whitespace=True)

    task_id: str = Field(..., description="The task ID to complete", min_length=1)


class ReopenTaskInput(BaseModel):
    """Input model for reopening a task."""

    model_config = ConfigDict(str_strip_whitespace=True)

    task_id: str = Field(..., description="The task ID to reopen", min_length=1)


class DeleteTaskInput(BaseModel):
    """Input model for deleting a task."""

    model_config = ConfigDict(str_strip_whitespace=True)

    task_id: str = Field(..., description="The task ID to delete", min_length=1)


class ListLabelsInput(BaseModel):
    """Input model for listing labels."""

    model_config = ConfigDict(str_strip_whitespace=True)

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class CreateLabelInput(BaseModel):
    """Input model for creating a label."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        description="Label name (e.g., 'urgent', 'work', 'personal')",
        min_length=1,
        max_length=255,
    )
    color: Optional[str] = Field(
        default=None,
        description="Color name: berry_red, red, orange, yellow, olive_green, lime_green, green, mint_green, teal, sky_blue, light_blue, blue, grape, violet, lavender, magenta, salmon, charcoal, grey, taupe",
    )
    is_favorite: bool = Field(default=False, description="Whether to mark as favorite")


# =============================================================================
# Shared Utilities
# =============================================================================


def _get_api_token() -> str:
    """Get API token from environment."""
    token = os.environ.get("TODOIST_API_TOKEN")
    if not token:
        raise ValueError(
            "TODOIST_API_TOKEN environment variable not set. "
            "Get your token from: Todoist Settings → Integrations → Developer → API token"
        )
    return token


async def _make_api_request(
    endpoint: str,
    method: str = "GET",
    json_data: Optional[dict] = None,
    params: Optional[dict] = None,
) -> dict | list | None:
    """Make authenticated request to Todoist API."""
    token = _get_api_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            f"{API_BASE_URL}/{endpoint}",
            headers=headers,
            json=json_data,
            params=params,
            timeout=30.0,
        )
        response.raise_for_status()

        if response.status_code == 204:
            return None
        return response.json()


def _handle_api_error(e: Exception) -> str:
    """Format API errors with actionable messages."""
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 400:
            return "Error: Invalid request. Check your parameters are correct."
        elif status == 401:
            return "Error: Invalid API token. Check TODOIST_API_TOKEN is correct."
        elif status == 403:
            return "Error: Permission denied. You may not have access to this resource."
        elif status == 404:
            return "Error: Resource not found. Check the ID is correct."
        elif status == 429:
            return "Error: Rate limit exceeded. Please wait before making more requests."
        elif status >= 500:
            return "Error: Todoist server error. Please try again later."
        return f"Error: API request failed with status {status}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Please try again."
    elif isinstance(e, ValueError):
        return f"Error: {str(e)}"
    return f"Error: {type(e).__name__}: {str(e)}"


def _format_due(due: Optional[dict]) -> str:
    """Format due date for markdown display."""
    if not due:
        return "No due date"
    date_str = due.get("date", "")
    if due.get("datetime"):
        return due["datetime"]
    if due.get("string"):
        return f"{due['string']} ({date_str})"
    return date_str


def _priority_label(priority: int) -> str:
    """Convert priority number to label."""
    labels = {1: "P4 (lowest)", 2: "P3", 3: "P2", 4: "P1 (highest)"}
    return labels.get(priority, str(priority))


def _truncate_response(result: str, item_count: int) -> str:
    """Truncate response if it exceeds character limit."""
    if len(result) > CHARACTER_LIMIT:
        truncated = result[: CHARACTER_LIMIT - 200]
        truncated += f"\n\n---\n**Response truncated** ({item_count} items). Use filters to narrow results."
        return truncated
    return result


# =============================================================================
# Project Tools
# =============================================================================


@mcp.tool(
    name="todoist_list_projects",
    annotations={
        "title": "List Todoist Projects",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def todoist_list_projects(params: ListProjectsInput) -> str:
    """
    List all projects in your Todoist account.

    Returns all projects including personal projects, shared projects, and sub-projects.
    Use this to get project IDs for creating tasks in specific projects.

    Args:
        params: ListProjectsInput containing:
            - response_format: 'markdown' or 'json'

    Returns:
        List of projects with their IDs, names, and metadata.
    """
    try:
        projects = await _make_api_request("projects")

        if not projects:
            return "No projects found."

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(projects, indent=2)

        # Markdown format
        lines = ["# Todoist Projects", ""]
        for p in projects:
            favorite = " ⭐" if p.get("is_favorite") else ""
            indent = "  " if p.get("parent_id") else ""
            lines.append(f"{indent}- **{p['name']}**{favorite} (ID: `{p['id']}`)")
            if p.get("comment_count"):
                lines.append(f"{indent}  - {p['comment_count']} comments")

        return _truncate_response("\n".join(lines), len(projects))

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="todoist_get_project",
    annotations={
        "title": "Get Todoist Project",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def todoist_get_project(params: GetProjectInput) -> str:
    """
    Get details of a specific project.

    Args:
        params: GetProjectInput containing:
            - project_id: The project ID
            - response_format: 'markdown' or 'json'

    Returns:
        Project details including name, color, and metadata.
    """
    try:
        project = await _make_api_request(f"projects/{params.project_id}")

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(project, indent=2)

        # Markdown format
        lines = [
            f"# {project['name']}",
            "",
            f"- **ID**: `{project['id']}`",
            f"- **Color**: {project.get('color', 'default')}",
            f"- **Favorite**: {'Yes' if project.get('is_favorite') else 'No'}",
            f"- **Shared**: {'Yes' if project.get('is_shared') else 'No'}",
            f"- **Comments**: {project.get('comment_count', 0)}",
        ]
        if project.get("parent_id"):
            lines.append(f"- **Parent Project**: `{project['parent_id']}`")

        return "\n".join(lines)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="todoist_create_project",
    annotations={
        "title": "Create Todoist Project",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def todoist_create_project(params: CreateProjectInput) -> str:
    """
    Create a new project in Todoist.

    Args:
        params: CreateProjectInput containing:
            - name: Project name
            - parent_id: Optional parent project ID for sub-projects
            - color: Optional color name
            - is_favorite: Whether to mark as favorite

    Returns:
        Created project details including the new project ID.
    """
    try:
        data = {"name": params.name}
        if params.parent_id:
            data["parent_id"] = params.parent_id
        if params.color:
            data["color"] = params.color
        if params.is_favorite:
            data["is_favorite"] = params.is_favorite

        project = await _make_api_request("projects", method="POST", json_data=data)

        return f"✅ Created project **{project['name']}** (ID: `{project['id']}`)"

    except Exception as e:
        return _handle_api_error(e)


# =============================================================================
# Task Tools
# =============================================================================


@mcp.tool(
    name="todoist_list_tasks",
    annotations={
        "title": "List Todoist Tasks",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def todoist_list_tasks(params: ListTasksInput) -> str:
    """
    List tasks from Todoist with optional filters.

    Supports filtering by project, label, or using Todoist's filter syntax.
    Common filters: 'today', 'tomorrow', 'overdue', 'p1', 'p2', 'no due date',
    'due before: tomorrow', '7 days', '@label_name', '#project_name'.

    Args:
        params: ListTasksInput containing:
            - project_id: Filter by project
            - label: Filter by label name
            - filter: Todoist filter query
            - limit: Maximum tasks to return
            - response_format: 'markdown' or 'json'

    Returns:
        List of tasks with their content, due dates, and priorities.
    """
    try:
        query_params = {}
        if params.project_id:
            query_params["project_id"] = params.project_id
        if params.label:
            query_params["label"] = params.label
        if params.filter:
            query_params["filter"] = params.filter

        tasks = await _make_api_request("tasks", params=query_params)

        if not tasks:
            return "No tasks found matching your criteria."

        # Apply limit
        tasks = tasks[: params.limit]

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(tasks, indent=2)

        # Markdown format
        lines = ["# Todoist Tasks", f"*Showing {len(tasks)} tasks*", ""]

        for t in tasks:
            priority = "🔴" if t.get("priority") == 4 else (
                "🟠" if t.get("priority") == 3 else (
                    "🔵" if t.get("priority") == 2 else ""
                )
            )
            due = _format_due(t.get("due"))
            labels = ", ".join(t.get("labels", [])) or "none"

            lines.append(f"### {priority} {t['content']}")
            lines.append(f"- **ID**: `{t['id']}`")
            lines.append(f"- **Due**: {due}")
            lines.append(f"- **Priority**: {_priority_label(t.get('priority', 1))}")
            lines.append(f"- **Labels**: {labels}")
            if t.get("description"):
                desc = t["description"][:200] + "..." if len(t.get("description", "")) > 200 else t["description"]
                lines.append(f"- **Description**: {desc}")
            lines.append("")

        return _truncate_response("\n".join(lines), len(tasks))

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="todoist_get_task",
    annotations={
        "title": "Get Todoist Task",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def todoist_get_task(params: GetTaskInput) -> str:
    """
    Get details of a specific task.

    Args:
        params: GetTaskInput containing:
            - task_id: The task ID
            - response_format: 'markdown' or 'json'

    Returns:
        Full task details including content, description, due date, and labels.
    """
    try:
        task = await _make_api_request(f"tasks/{params.task_id}")

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(task, indent=2)

        # Markdown format
        lines = [
            f"# {task['content']}",
            "",
            f"- **ID**: `{task['id']}`",
            f"- **Project**: `{task.get('project_id', 'Inbox')}`",
            f"- **Due**: {_format_due(task.get('due'))}",
            f"- **Priority**: {_priority_label(task.get('priority', 1))}",
            f"- **Labels**: {', '.join(task.get('labels', [])) or 'none'}",
            f"- **Created**: {task.get('created_at', 'unknown')}",
        ]
        if task.get("description"):
            lines.extend(["", "## Description", task["description"]])
        if task.get("parent_id"):
            lines.append(f"- **Parent Task**: `{task['parent_id']}`")

        return "\n".join(lines)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="todoist_create_task",
    annotations={
        "title": "Create Todoist Task",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def todoist_create_task(params: CreateTaskInput) -> str:
    """
    Create a new task in Todoist.

    Supports natural language due dates like 'tomorrow', 'next Monday', 'every week'.
    Priority 4 is highest (red), priority 1 is lowest.

    Args:
        params: CreateTaskInput containing:
            - content: Task title/content
            - description: Optional detailed description
            - project_id: Project to add to (defaults to Inbox)
            - due_string: Natural language due date
            - due_date: Due date in YYYY-MM-DD format
            - priority: 1-4 (4 is highest)
            - labels: List of label names
            - parent_id: Parent task ID for subtasks

    Returns:
        Created task details including the new task ID.
    """
    try:
        data: dict[str, Any] = {"content": params.content}

        if params.description:
            data["description"] = params.description
        if params.project_id:
            data["project_id"] = params.project_id
        if params.due_string:
            data["due_string"] = params.due_string
        elif params.due_date:
            data["due_date"] = params.due_date
        if params.priority:
            data["priority"] = params.priority.value
        if params.labels:
            data["labels"] = params.labels
        if params.parent_id:
            data["parent_id"] = params.parent_id

        task = await _make_api_request("tasks", method="POST", json_data=data)

        due_info = f" due {_format_due(task.get('due'))}" if task.get("due") else ""
        return f"✅ Created task **{task['content']}**{due_info} (ID: `{task['id']}`)"

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="todoist_update_task",
    annotations={
        "title": "Update Todoist Task",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def todoist_update_task(params: UpdateTaskInput) -> str:
    """
    Update an existing task in Todoist.

    Only provided fields will be updated. To clear a due date, use the Todoist app.

    Args:
        params: UpdateTaskInput containing:
            - task_id: The task ID to update
            - content: New task title
            - description: New description
            - due_string: New due date (natural language)
            - due_date: New due date (YYYY-MM-DD)
            - priority: New priority (1-4)
            - labels: New labels (replaces existing)

    Returns:
        Updated task confirmation.
    """
    try:
        data: dict[str, Any] = {}

        if params.content:
            data["content"] = params.content
        if params.description is not None:
            data["description"] = params.description
        if params.due_string:
            data["due_string"] = params.due_string
        elif params.due_date:
            data["due_date"] = params.due_date
        if params.priority:
            data["priority"] = params.priority.value
        if params.labels is not None:
            data["labels"] = params.labels

        if not data:
            return "Error: No fields to update. Provide at least one field to change."

        task = await _make_api_request(
            f"tasks/{params.task_id}", method="POST", json_data=data
        )

        return f"✅ Updated task **{task['content']}** (ID: `{task['id']}`)"

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="todoist_complete_task",
    annotations={
        "title": "Complete Todoist Task",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def todoist_complete_task(params: CompleteTaskInput) -> str:
    """
    Mark a task as complete.

    For recurring tasks, this will close the current occurrence and create the next one.

    Args:
        params: CompleteTaskInput containing:
            - task_id: The task ID to complete

    Returns:
        Confirmation that the task was completed.
    """
    try:
        await _make_api_request(f"tasks/{params.task_id}/close", method="POST")
        return f"✅ Completed task (ID: `{params.task_id}`)"

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="todoist_reopen_task",
    annotations={
        "title": "Reopen Todoist Task",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def todoist_reopen_task(params: ReopenTaskInput) -> str:
    """
    Reopen a completed task.

    Args:
        params: ReopenTaskInput containing:
            - task_id: The task ID to reopen

    Returns:
        Confirmation that the task was reopened.
    """
    try:
        await _make_api_request(f"tasks/{params.task_id}/reopen", method="POST")
        return f"✅ Reopened task (ID: `{params.task_id}`)"

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="todoist_delete_task",
    annotations={
        "title": "Delete Todoist Task",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def todoist_delete_task(params: DeleteTaskInput) -> str:
    """
    Permanently delete a task.

    ⚠️ This action cannot be undone. The task will be permanently removed.

    Args:
        params: DeleteTaskInput containing:
            - task_id: The task ID to delete

    Returns:
        Confirmation that the task was deleted.
    """
    try:
        await _make_api_request(f"tasks/{params.task_id}", method="DELETE")
        return f"🗑️ Deleted task (ID: `{params.task_id}`)"

    except Exception as e:
        return _handle_api_error(e)


# =============================================================================
# Label Tools
# =============================================================================


@mcp.tool(
    name="todoist_list_labels",
    annotations={
        "title": "List Todoist Labels",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def todoist_list_labels(params: ListLabelsInput) -> str:
    """
    List all personal labels in your Todoist account.

    Labels can be applied to tasks for organization and filtering.

    Args:
        params: ListLabelsInput containing:
            - response_format: 'markdown' or 'json'

    Returns:
        List of labels with their names and colors.
    """
    try:
        labels = await _make_api_request("labels")

        if not labels:
            return "No labels found. Create labels to organize your tasks."

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(labels, indent=2)

        # Markdown format
        lines = ["# Todoist Labels", ""]
        for label in labels:
            favorite = " ⭐" if label.get("is_favorite") else ""
            lines.append(
                f"- **{label['name']}**{favorite} (ID: `{label['id']}`, color: {label.get('color', 'default')})"
            )

        return "\n".join(lines)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="todoist_create_label",
    annotations={
        "title": "Create Todoist Label",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def todoist_create_label(params: CreateLabelInput) -> str:
    """
    Create a new label.

    Labels help organize tasks across projects. Apply labels to tasks for easy filtering.

    Args:
        params: CreateLabelInput containing:
            - name: Label name
            - color: Optional color name
            - is_favorite: Whether to mark as favorite

    Returns:
        Created label details including the new label ID.
    """
    try:
        data: dict[str, Any] = {"name": params.name}
        if params.color:
            data["color"] = params.color
        if params.is_favorite:
            data["is_favorite"] = params.is_favorite

        label = await _make_api_request("labels", method="POST", json_data=data)

        return f"✅ Created label **{label['name']}** (ID: `{label['id']}`)"

    except Exception as e:
        return _handle_api_error(e)


# =============================================================================
# Main Entry Point
# =============================================================================


if __name__ == "__main__":
    mcp.run()
