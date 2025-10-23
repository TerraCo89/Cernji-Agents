# Claude Code CLI Usage

Source: `/anthropics/claude-code` (Context7)

## Installation

```bash
npm install -g @anthropic-ai/claude-code

cd /path/to/your/project

claude

claude --headless "explain the main.js file"

ANTHROPIC_API_KEY=your_key claude

claude --settings /path/to/settings.json
```

## Environment Variables

```bash
# API Keys
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...

# AWS Bedrock
export AWS_REGION=us-west-2
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...

# Google Vertex
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
export GOOGLE_CLOUD_PROJECT=project-id
export GOOGLE_CLOUD_LOCATION=us-central1

# Claude Code Settings
export CLAUDE_BASH_NO_LOGIN=1  # Skip login shell
export ANTHROPIC_DEFAULT_SONNET_MODEL=claude-sonnet-4-5
export NO_PROXY=localhost,127.0.0.1  # Bypass proxy

# Launch with environment
ANTHROPIC_API_KEY=sk-ant-... claude
```

## Built-in Slash Commands

```bash
/help             # Get help with Claude Code
/bug              # Report a bug
/model            # Switch AI model
/rewind           # Undo code changes to a previous state
/usage            # Check plan limits and API usage
/cost             # View API costs and token usage
/context          # Check context usage
/memory           # View memory management
/add-dir          # Add directory to context
/mcp              # Manage MCP servers
/plugin           # Manage plugins (install, enable, disable)
/doctor           # Validate configuration and diagnose issues
/clear            # Clear conversation history
/config           # Configure Claude Code settings
```

## Model Selection

```bash
# Switch models interactively
/model

# Or specify at launch
claude --model claude-opus-4

# Available aliases: sonnet, opus, opusplan
```

## Permission Modes

```bash
claude --permission-mode acceptEdits

claude --permission-mode ask

claude /doctor

# Example permission patterns (for use in JSON config):
# "Read(**/*.ts)"

# Allow git commands with output redirection
# "Bash(git:*)"  # Matches: git status > output.txt

# Allow Python scripts in specific directory
# "Bash(python /app/scripts/*)"
```

## Session Management

```bash
# Rewind conversation to undo changes
/rewind

# Clear conversation
/clear

# Save session state (automatic)
# Resume from last session on next launch
```

## Context Management

```bash
# Check context usage
/context

# Add directory to context
/add-dir src/components

# Memory management
/memory
```

## Debugging

```bash
# Enable debug logging
claude --debug

# Check logs (migrated to file in 1.0.123+)
tail -f ~/.claude/debug.log

# Validate configuration
claude /doctor

# Common issues and fixes:
# - OAuth errors: Check token expiration with /usage
# - Permission denied: Update settings.json allowedTools
# - Path issues: Use POSIX format on Windows (//c/Users/...)
# - Hook failures: Check exit codes (1=stderr, 2=block+stderr)
# - Plugin issues: Run /plugin validate to check plugin structure
# - MCP server issues: Check /mcp for server status
```

## Keyboard Shortcuts

```bash
# Press Ctrl-G to open your prompt in your system's configured text editor

# Inside Claude Code, press Ctrl-R to search command history
# Type to filter, Enter to select, Esc to cancel

# Toggle thinking mode with Tab key (sticky across sessions)
# Temporarily disable with /t in your prompt
# Shows Claude's reasoning process
```

## VS Code Extension

```bash
# Install from VS Code marketplace
# Search for "Claude Code"

# Or via command line
code --install-extension anthropic.claude-code

# Use Cmd/Ctrl+Shift+P to open Claude Code
# Drag and drop files into chat
# Access "Open in Terminal" from login screen
```
