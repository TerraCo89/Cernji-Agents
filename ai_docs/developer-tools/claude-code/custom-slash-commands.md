# Claude Code Custom Slash Commands

Source: https://context7.com/anthropics/claude-code

## Overview

Custom slash commands in Claude Code enable automation of multi-step workflows using Markdown files. They can be defined in `.claude/commands/` directory and executed via `/command-name` syntax.

## Define a Custom Slash Command

Create a Markdown file in `.claude/commands/` with the following structure:

```markdown
# File: .claude/commands/deploy.md
---
allowed-tools: Bash(npm:*), Bash(git:*)
description: Build and deploy to production
---

## Your task

1. Run `npm run build`
2. Run `npm run test`
3. If tests pass, deploy with `npm run deploy`
4. Tag the release with current version
```

### Command File Structure

- **Front matter (YAML)**: Define allowed tools and description
  - `allowed-tools`: Tool permissions for this command (e.g., `Bash(npm:*)`, `Bash(git:*)`)
  - `description`: Brief description of what the command does
- **Content**: Instructions or tasks for Claude to execute

## Built-in Slash Commands

Claude Code provides several built-in commands:

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

### Plugin-Provided Commands

Built-in plugins provide additional commands:

```bash
/commit-push-pr   # Commit changes, push, and create PR (commit-commands plugin)
/dedupe           # Find duplicate GitHub issues (pr-review-toolkit plugin)
/pr-review-toolkit:review-pr  # Run comprehensive PR review
```

## Permission Patterns

When defining `allowed-tools`, use these patterns:

```bash
# File operations
Read(**/*.ts)                    # Read all TypeScript files
Edit(**/*.{js,ts})              # Edit JavaScript and TypeScript files

# Bash commands
Bash(git:*)                      # Allow all git commands
Bash(npm:*)                      # Allow all npm commands
Bash(python /app/scripts/*)     # Allow Python scripts in specific directory
```

## Managing Context

Commands for context management:

```bash
# Check context usage
/context

# Add directory to context
/add-dir src/components

# Memory management
/memory
```

## Session Management

```bash
# Rewind conversation to undo changes
/rewind

# Clear conversation
/clear

# Sessions are automatically saved and resumed on next launch
```

## MCP Server Integration

Interact with Model Context Protocol servers:

```bash
# Enable/disable MCP servers by @-mentioning them
@github help

# Or manage via /mcp command
/mcp

# MCP servers provide tools that Claude can use
# Example: GitHub MCP server provides issue search, PR management, etc.
```

## Plugin System

Manage plugins via CLI:

```bash
# Inside Claude Code terminal
/plugin install                    # Install plugins from marketplaces
/plugin enable security-guidance   # Enable a plugin
/plugin disable security-guidance  # Disable a plugin
/plugin marketplace                # Browse available plugins
/plugin validate                   # Validate plugin structure
```

### Available Built-in Plugins

- **security-guidance**: Security reminder hooks for potential vulnerabilities
- **pr-review-toolkit**: Comprehensive PR review agents
- **agent-sdk-dev**: Claude Agent SDK development tools
- **feature-dev**: Feature development agents
- **commit-commands**: Git commit workflow commands

### Custom Plugin Directory Structure

```text
my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── my-command.md
├── agents/
│   └── my-agent.md
└── hooks/
    └── hooks.json
```

## Hooks

Configure pre/post-tool execution hooks:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/validator.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npm run lint"
          }
        ]
      }
    ]
  }
}
```

### Example Validation Hook (Python)

```python
#!/usr/bin/env python3
import json
import re
import sys

VALIDATION_RULES = [
    (r"^grep\b", "Use 'rg' instead of 'grep'"),
    (r"^rm -rf", "Dangerous command blocked")
]

def validate_command(command: str) -> list[str]:
    issues = []
    for pattern, message in VALIDATION_RULES:
        if re.search(pattern, command):
            issues.append(message)
    return issues

def main():
    input_data = json.load(sys.stdin)

    if input_data.get("tool_name") != "Bash":
        sys.exit(0)

    command = input_data.get("tool_input", {}).get("command", "")
    issues = validate_command(command)

    if issues:
        for message in issues:
            print(f"• {message}", file=sys.stderr)
        sys.exit(2)  # Block tool call

if __name__ == "__main__":
    main()
```

## Permission Modes

Launch Claude Code with different permission modes:

```bash
claude --permission-mode acceptEdits  # Automatically accept edits
claude --permission-mode ask          # Ask for confirmation
claude /doctor                        # Validate permissions
```

## Thinking Mode

Toggle Claude's reasoning display:

```bash
# Toggle thinking mode with Tab key (sticky across sessions)
# Temporarily disable with /t in your prompt
# Shows Claude's reasoning process
```

## Command History

Search through command history:

```bash
# Inside Claude Code, press Ctrl-R to search command history
# Type to filter, Enter to select, Esc to cancel
```

## Usage Tracking

Monitor API usage and costs:

```bash
# View API usage and costs
/cost

# Check plan limits
/usage
```

## Example: GitHub Issue Deduplication

```bash
# Usage via slash command
/dedupe issue-number

# Direct script execution
./scripts/auto-close-duplicates.ts
```

## Environment Variables

Configure Claude Code behavior with environment variables:

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

## Settings Configuration

Example `settings.json` configuration:

```json
{
  "permissions": {
    "allowedTools": [
      "Read(**/*.{js,ts,json,md})",
      "Edit(**/*.{js,ts})",
      "Bash(git:*)",
      "Bash(npm:*)",
      "Bash(node:*)"
    ],
    "deniedTools": [
      "Edit(/config/secrets.json)",
      "Bash(rm -rf:*)"
    ]
  },
  "permissionMode": "acceptEdits",
  "spinnerTipsEnabled": true,
  "hooks": {
    "PreToolUse": [],
    "PostToolUse": []
  },
  "statusLine": {
    "enabled": true,
    "format": "{{model}} | {{tokens}}"
  },
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-github"],
      "oauth": {
        "clientId": "your-client-id",
        "clientSecret": "your-client-secret",
        "scopes": ["repo", "issues"]
      }
    }
  },
  "extraKnownMarketplaces": [
    {
      "name": "company-plugins",
      "url": "https://github.com/your-org/claude-plugins"
    }
  ]
}
```

## Git Integration Commands

### List Git Worktrees

```bash
git worktree list
```

Shows all existing worktrees with their paths and associated branches.

### List Git Branches

```bash
git branch -v
```

Displays all local branches with status information, including '[gone]' status for deleted remote branches.

## Installation

### Via npm

```bash
npm install -g @anthropic-ai/claude-code

cd /path/to/your/project

claude

# Headless mode for single commands
claude --headless "explain the main.js file"

# With API key
ANTHROPIC_API_KEY=your_key claude

# With custom settings
claude --settings /path/to/settings.json
```

### VS Code Extension

```bash
# Install from VS Code marketplace
# Search for "Claude Code"

# Or via command line
code --install-extension anthropic.claude-code

# Use Cmd/Ctrl+Shift+P to open Claude Code
# Drag and drop files into chat
# Access "Open in Terminal" from login screen
```

## Best Practices

1. **Define clear allowed-tools** in custom commands to limit scope
2. **Use descriptive command names** that reflect their purpose
3. **Implement validation hooks** for safety-critical operations
4. **Document custom commands** in your project's README
5. **Use permission modes** appropriately for automation vs. interactive work
6. **Leverage MCP servers** for external integrations
7. **Create plugins** for reusable command sets across projects
