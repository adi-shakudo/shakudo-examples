#!/bin/bash
set -e  # Exit on any error

# Ensure PATH includes common binary locations
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"

# Change to the directory containing this script
cd "$(dirname "$0")"

# Ensure ~/.claude directory exists
mkdir -p ~/.claude

# Check if settings.json exists, if not create it with basic structure
if [[ ! -f ~/.claude/settings.json ]]; then
    echo '{}' > ~/.claude/settings.json
fi

# Check if jq is available
if ! command -v jq >/dev/null 2>&1; then
    echo "Error: jq is required but not found in PATH"
    echo "Please install jq: brew install jq"
    exit 1
fi

# Read the mcp.json file and extract mcpServers
MCP_SERVERS=$(cat mcp.json | jq '.mcpServers')

# Update or create the mcpServers section in Claude settings
jq --argjson mcpServers "$MCP_SERVERS" '.mcpServers = $mcpServers' ~/.claude/settings.json > ~/.claude/settings.json.tmp && mv ~/.claude/settings.json.tmp ~/.claude/settings.json

# Read prompt from prompt.txt and pipe to claude command
cat prompt.txt | claude "$@"