# Claude Agent SDK for TypeScript - Quick Start

Source: `/anthropics/claude-agent-sdk-typescript` (Context7)

## Installation

```sh
npm install @anthropic-ai/claude-agent-sdk
```

Or:

```bash
npm install @anthropic-ai/claude-agent-sdk
```

## Basic Usage

### Simple Query

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// Basic query with Claude
const response = query({
  prompt: "Help me analyze this codebase and suggest improvements",
  options: {
    model: "claude-sonnet-4-5"
  }
});

for await (const message of response) {
  if (message.type === 'assistant') {
    console.log(message.content);
  } else if (message.type === 'system' && message.subtype === 'init') {
    console.log(`Session ID: ${message.session_id}`);
  }
}
```

### Advanced Query with Permissions

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

const response = query({
  prompt: "Review the authentication module for security issues",
  options: {
    model: "claude-sonnet-4-5",
    workingDirectory: "/path/to/project",
    systemPrompt: "You are a security-focused code reviewer. Analyze code for vulnerabilities and provide detailed recommendations.",
    permissionMode: "default",
    canUseTool: async (toolName, input) => {
      // Custom permission logic
      if (toolName === 'Bash' && input.command.includes('rm -rf')) {
        return { behavior: "deny", message: "Destructive commands not allowed" };
      }
      return { behavior: "allow" };
    }
  }
});

for await (const message of response) {
  switch (message.type) {
    case 'assistant':
      console.log('Assistant:', message.content);
      break;
    case 'tool_call':
      console.log(`Tool called: ${message.tool_name}`);
      break;
    case 'tool_result':
      console.log(`Tool result: ${message.result}`);
      break;
    case 'error':
      console.error('Error:', message.error);
      break;
  }
}
```

## Permission Modes

### Different Permission Modes

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// acceptEdits mode - automatically approve file edits
const autoEditResponse = query({
  prompt: "Refactor the user service to use async/await",
  options: {
    permissionMode: "acceptEdits",
    workingDirectory: "/path/to/project",
    model: "claude-sonnet-4-5"
  }
});

// default mode - standard permission checks
const controlledResponse = query({
  prompt: "Analyze and modify the database schema",
  options: {
    permissionMode: "default",
    model: "claude-sonnet-4-5"
  }
});

// bypassPermissions mode - skip all permission checks (use with caution)
const unrestricted = query({
  prompt: "Run comprehensive test suite and fix all failures",
  options: {
    permissionMode: "bypassPermissions",
    model: "claude-sonnet-4-5"
  }
});
```

### Custom Permission Callback

```typescript
const customPermissions = query({
  prompt: "Deploy the application to production",
  options: {
    permissionMode: "default",
    canUseTool: async (toolName, input) => {
      // Allow read-only operations
      if (['Read', 'Grep', 'Glob'].includes(toolName)) {
        return { behavior: "allow" };
      }

      // Deny destructive bash commands
      if (toolName === 'Bash' &&
          (input.command.includes('rm ') || input.command.includes('delete'))) {
        return {
          behavior: "deny",
          message: "Destructive operations require manual approval"
        };
      }

      // Ask for confirmation on file writes
      if (toolName === 'Write' || toolName === 'Edit') {
        return {
          behavior: "ask",
          message: `Allow modification of ${input.file_path}?`
        };
      }

      return { behavior: "allow" };
    },
    model: "claude-sonnet-4-5"
  }
});
```
