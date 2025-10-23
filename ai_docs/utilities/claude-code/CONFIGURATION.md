# Claude Code Configuration

Source: `/anthropics/claude-code` (Context7)

## Example settings.json Configuration

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

## Granular Permissions Configuration

```json
{
  "permissions": {
    "allowedTools": [
      "Read(/app/src/**)",
      "Edit(/app/src/**/*.js)",
      "Bash(git status:*)",
      "Bash(npm install:*)",
      "Bash(python:*)"
    ],
    "deniedTools": [
      "Bash(rm -rf:*)",
      "Edit(/config/secrets.json)"
    ]
  },
  "permissionMode": "ask"
}
```

## MCP Server Integration

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-github"],
      "oauth": {
        "clientId": "your-client-id",
        "clientSecret": "your-client-secret",
        "scopes": ["repo", "issues"]
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
    }
  }
}
```

### Managing MCP Servers

```bash
# Enable/disable MCP servers by @-mentioning them
@github help

# Or manage in /mcp command
/mcp

# MCP servers provide tools that Claude can use
# Example: GitHub MCP server provides issue search, PR management, etc.
```

## Hooks Configuration

### Pre/Post Tool Hooks

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

### Bash Command Validation Hook (Python)

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

## Plugin System

### Plugin Directory Structure

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

### Managing Plugins

```bash
# Inside Claude Code terminal
/plugin install                    # Install plugins from marketplaces
/plugin enable security-guidance   # Enable a plugin
/plugin disable security-guidance  # Disable a plugin
/plugin marketplace                # Browse available plugins
/plugin validate                   # Validate plugin structure

# Available built-in plugins:
# - security-guidance: Security reminder hooks for potential vulnerabilities
# - pr-review-toolkit: Comprehensive PR review agents
# - agent-sdk-dev: Claude Agent SDK development tools
# - feature-dev: Feature development agents
# - commit-commands: Git commit workflow commands
```

### Additional Plugin Marketplaces

```json
{
  "extraKnownMarketplaces": [
    {
      "name": "company-plugins",
      "url": "https://github.com/your-org/claude-plugins"
    }
  ]
}
```

## Custom Slash Commands

### Define a Custom Command

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
