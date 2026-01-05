#!/usr/bin/env bash
# Todoist MCP Server - Claude Code Installation Script
# Reads from config.json and registers the MCP server with Claude Code

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Check for config.json
if [[ ! -f "$CONFIG_FILE" ]]; then
    if [[ -f "${SCRIPT_DIR}/config.json.example" ]]; then
        info "Creating config.json from example..."
        cp "${SCRIPT_DIR}/config.json.example" "$CONFIG_FILE"
        warn "Please edit config.json with your Todoist API token, then re-run this script."
        warn "Get your token from: Todoist Settings → Integrations → Developer"
        exit 0
    else
        error "config.json not found. Create it from config.json.example"
    fi
fi

# Parse config.json
TODOIST_TOKEN=$(jq -r '.todoist_api_token // ""' "$CONFIG_FILE")
OPENBAO_ENABLED=$(jq -r '.openbao_enabled // false' "$CONFIG_FILE")

# Validate
if [[ "$OPENBAO_ENABLED" != "true" && -z "$TODOIST_TOKEN" ]]; then
    error "todoist_api_token required when openbao_enabled is false"
fi

# Check for Python venv
if [[ ! -d "${SCRIPT_DIR}/.venv" ]]; then
    info "Creating Python virtual environment..."
    python3 -m venv "${SCRIPT_DIR}/.venv"
    info "Installing dependencies..."
    "${SCRIPT_DIR}/.venv/bin/pip" install -q -r "${SCRIPT_DIR}/requirements.txt"
fi

# Build claude mcp add command
MCP_NAME="todoist"
PYTHON_PATH="${SCRIPT_DIR}/.venv/bin/python"

if [[ "$OPENBAO_ENABLED" == "true" ]]; then
    info "Registering with OpenBao credential management..."
    claude mcp add "$MCP_NAME" -s user -- "$PYTHON_PATH" "${SCRIPT_DIR}/todoist_mcp.py"
else
    info "Registering with environment variable credentials..."
    claude mcp add "$MCP_NAME" -s user \
        --env "TODOIST_API_TOKEN=${TODOIST_TOKEN}" \
        --env "OPENBAO_DEV_MODE=1" \
        -- "$PYTHON_PATH" "${SCRIPT_DIR}/todoist_mcp.py"
fi

info "Todoist MCP server registered successfully!"
info "Restart Claude Code to use the new server."
