#!/bin/bash
set -e  # Exit on any error
set -o pipefail  # Exit on error in any part of a pipeline

# Ensure PATH includes common binary locations
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"

# Change to the directory containing this script
cd "$(dirname "$0")"

# Ensure ~/.claude directory exists
mkdir -p ~/.claude

# Set up API key helper script
if [[ ! -f ~/.claude/anthropic_key.sh ]]; then
    if [[ -z "$CLAUDE_API_KEY" ]]; then
        echo "Warning: CLAUDE_API_KEY environment variable not set"
        echo "Please set it or create ~/.claude/anthropic_key.sh manually"
    else
        echo "Creating API key helper script..."
        cat > ~/.claude/anthropic_key.sh << EOF
echo "$CLAUDE_API_KEY"
EOF
        chmod +x ~/.claude/anthropic_key.sh
    fi
fi

# Check if settings.json exists, if not create it with basic structure
if [[ ! -f ~/.claude/settings.json ]]; then
    echo '{"apiKeyHelper": "~/.claude/anthropic_key.sh", "model": "claude-sonnet-4-20250514"}' > ~/.claude/settings.json
else
    # Ensure apiKeyHelper and model are set in existing settings.json
    if ! jq -e '.apiKeyHelper' ~/.claude/settings.json >/dev/null 2>&1; then
        jq '.apiKeyHelper = "~/.claude/anthropic_key.sh"' ~/.claude/settings.json > ~/.claude/settings.json.tmp && mv ~/.claude/settings.json.tmp ~/.claude/settings.json
    fi
    if ! jq -e '.model' ~/.claude/settings.json >/dev/null 2>&1; then
        jq '.model = "claude-sonnet-4-20250514"' ~/.claude/settings.json > ~/.claude/settings.json.tmp && mv ~/.claude/settings.json.tmp ~/.claude/settings.json
    fi
fi

# Function to install packages using apt
install_packages() {
    local packages=("$@")
    echo "Installing required packages: ${packages[*]}..."
    if command -v apt >/dev/null 2>&1; then
        apt update && apt install -y "${packages[@]}"
    else
        echo "Error: apt not found. Please install packages manually: ${packages[*]}"
        exit 1
    fi
}

# Check for required system packages
missing_packages=()
for package in jq curl; do
    if ! command -v "$package" >/dev/null 2>&1; then
        missing_packages+=("$package")
    fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
    install_packages "${missing_packages[@]}"
fi

# Check if Node.js is available
if ! command -v node >/dev/null 2>&1; then
    echo "Node.js is required but not found. Installing Node.js..."
    if command -v apt >/dev/null 2>&1; then
        curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
        apt-get install -y nodejs
    else
        echo "Error: Please install Node.js manually"
        exit 1
    fi
fi

# Check if Claude CLI is installed
if ! command -v claude >/dev/null 2>&1; then
    echo "Claude CLI not found. Installing..."
    npm install -g @anthropic-ai/claude-code@1.0.61
fi

# Read the schema.json file and extract mcpServers and prompt
MCP_SERVERS=$(cat schema.json | jq '.mcpServers')
PROMPT=$(cat schema.json | jq -r '.task.prompt')

# Override prompt if AGENT_TASK_PROMPT environment variable is set
if [[ -n "$AGENT_TASK_PROMPT" ]]; then
    PROMPT="$AGENT_TASK_PROMPT"
fi

# Update or create the mcpServers section in Claude settings
jq --argjson mcpServers "$MCP_SERVERS" '.mcpServers = $mcpServers' ~/.claude/settings.json > ~/.claude/settings.json.tmp && mv ~/.claude/settings.json.tmp ~/.claude/settings.json

sleep 3000

# Use the prompt from schema.json or environment variable and pipe to claude command
echo "$PROMPT" | claude --allowedTools Read,Write,Edit,Bash,Glob,Grep,LS,MultiEdit,NotebookRead,NotebookEdit,WebFetch,WebSearch,Task,mcp__playwright__*,playwright* --print "$@" --output-format stream-json --verbose

