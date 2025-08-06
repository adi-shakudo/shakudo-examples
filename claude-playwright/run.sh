#!/bin/bash
set -e  # Exit on any error

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
#!/bin/bash
echo "$CLAUDE_API_KEY"
EOF
        chmod +x ~/.claude/anthropic_key.sh
    fi
fi

# Check if settings.json exists, if not create it with basic structure
if [[ ! -f ~/.claude/settings.json ]]; then
    echo '{"apiKeyHelper": "~/.claude/anthropic_key.sh"}' > ~/.claude/settings.json
else
    # Ensure apiKeyHelper is set in existing settings.json
    if ! jq -e '.apiKeyHelper' ~/.claude/settings.json >/dev/null 2>&1; then
        jq '.apiKeyHelper = "~/.claude/anthropic_key.sh"' ~/.claude/settings.json > ~/.claude/settings.json.tmp && mv ~/.claude/settings.json.tmp ~/.claude/settings.json
    fi
fi

# Function to install packages using apt
install_packages() {
    local packages=("$@")
    echo "Installing required packages: ${packages[*]}..."
    if command -v apt >/dev/null 2>&1; then
        sudo apt update && sudo apt install -y "${packages[@]}"
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
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
        sudo apt-get install -y nodejs
    else
        echo "Error: Please install Node.js manually"
        exit 1
    fi
fi

# Check if Claude CLI is installed
if ! command -v claude >/dev/null 2>&1; then
    echo "Claude CLI not found. Installing..."
    npm install -g @anthropic-ai/claude-cli
fi

# Read the mcp.json file and extract mcpServers
MCP_SERVERS=$(cat mcp.json | jq '.mcpServers')

# Update or create the mcpServers section in Claude settings
jq --argjson mcpServers "$MCP_SERVERS" '.mcpServers = $mcpServers' ~/.claude/settings.json > ~/.claude/settings.json.tmp && mv ~/.claude/settings.json.tmp ~/.claude/settings.json

# Read prompt from prompt.txt and pipe to claude command
cat prompt.txt | claude "$@"