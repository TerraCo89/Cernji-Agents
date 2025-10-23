# Claude Agent SDK for TypeScript - Advanced Usage

Source: `/anthropics/claude-agent-sdk-typescript` (Context7)

## Custom Tools with MCP

### Define Custom Tools

```typescript
import { query, createSdkMcpServer, tool } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

// Define a weather API tool
const weatherServer = createSdkMcpServer({
  name: "weather-service",
  version: "1.0.0",
  tools: [
    tool(
      "get_weather",
      "Get current weather for a location",
      {
        location: z.string().describe("City name or coordinates"),
        units: z.enum(["celsius", "fahrenheit"]).default("celsius")
      },
      async (args) => {
        try {
          const response = await fetch(
            `https://api.weather.com/v1/current?location=${args.location}&units=${args.units}`
          );
          const data = await response.json();

          return {
            content: [{
              type: "text",
              text: `Temperature: ${data.temp}° ${args.units}\nConditions: ${data.conditions}\nHumidity: ${data.humidity}%`
            }]
          };
        } catch (error) {
          return {
            content: [{
              type: "text",
              text: `Error fetching weather: ${error.message}`
            }],
            isError: true
          };
        }
      }
    )
  ]
});
```

### Database Query Tool

```typescript
const dbServer = createSdkMcpServer({
  name: "database",
  version: "1.0.0",
  tools: [
    tool(
      "query_users",
      "Query user records from the database",
      {
        email: z.string().email().optional(),
        limit: z.number().min(1).max(100).default(10),
        offset: z.number().min(0).default(0)
      },
      async (args) => {
        const query = `SELECT * FROM users WHERE email LIKE '%${args.email || ''}%' LIMIT ${args.limit} OFFSET ${args.offset}`;
        // Execute database query
        const results = await db.execute(query);

        return {
          content: [{
            type: "text",
            text: JSON.stringify(results, null, 2)
          }]
        };
      }
    ),
    tool(
      "calculate",
      "Perform mathematical calculations",
      {
        expression: z.string().describe("Mathematical expression to evaluate"),
        precision: z.number().min(0).max(10).default(2)
      },
      async (args) => {
        try {
          // Safely evaluate expression (use a proper math parser in production)
          const result = eval(args.expression);
          const rounded = Number(result.toFixed(args.precision));

          return {
            content: [{
              type: "text",
              text: `Result: ${rounded}`
            }]
          };
        } catch (error) {
          return {
            content: [{
              type: "text",
              text: `Invalid expression: ${error.message}`
            }],
            isError: true
          };
        }
      }
    )
  ]
});

// Use custom tools in query
const response = query({
  prompt: "What's the weather in San Francisco? Also query users with gmail addresses and calculate 15% tip on $85.50",
  options: {
    mcpServers: {
      "weather-service": weatherServer,
      "database": dbServer
    },
    allowedTools: [
      "mcp__weather-service__get_weather",
      "mcp__database__query_users",
      "mcp__database__calculate"
    ],
    model: "claude-sonnet-4-5"
  }
});

for await (const message of response) {
  if (message.type === 'assistant') {
    console.log(message.content);
  }
}
```

## Application-Specific Tools

```typescript
import { query, createSdkMcpServer, tool } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

// Custom tools for application
const appTools = createSdkMcpServer({
  name: "app-services",
  version: "1.0.0",
  tools: [
    tool(
      "send_notification",
      "Send a notification to users",
      {
        userId: z.string(),
        message: z.string(),
        priority: z.enum(["low", "medium", "high"])
      },
      async (args) => {
        // Integration with notification service
        await notificationService.send(args);
        return {
          content: [{ type: "text", text: "Notification sent successfully" }]
        };
      }
    ),
    tool(
      "log_event",
      "Log application events for monitoring",
      {
        event: z.string(),
        data: z.record(z.any()).optional(),
        severity: z.enum(["info", "warning", "error"])
      },
      async (args) => {
        logger.log(args.severity, args.event, args.data);
        return {
          content: [{ type: "text", text: "Event logged" }]
        };
      }
    )
  ]
});
```

## Subagents

### Orchestrate Specialized Subagents

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

const response = query({
  prompt: "Review the entire application for security vulnerabilities, performance issues, and test coverage",
  options: {
    model: "claude-sonnet-4-5",
    agents: {
      // Security review specialist
      "security-reviewer": {
        description: "Expert in security auditing and vulnerability analysis. Use this agent for security reviews, penetration testing insights, and identifying security flaws.",
        prompt: `You are a security expert specializing in web application security.
Focus on:
- Authentication and authorization vulnerabilities
- SQL injection and XSS vulnerabilities
- Insecure dependencies
- Credential exposure
- API security issues

Provide detailed explanations with severity levels and remediation steps.`,
        tools: ["Read", "Grep", "Glob", "Bash"],
        model: "sonnet"
      },

      // Performance optimization specialist
      "performance-analyst": {
        description: "Performance optimization expert. Use for analyzing bottlenecks, memory leaks, and optimization opportunities.",
        prompt: `You are a performance optimization specialist.
Analyze:
- Algorithm complexity and bottlenecks
- Memory usage patterns
- Database query optimization
- Caching strategies
- Resource utilization

Provide specific metrics and actionable recommendations.`,
        tools: ["Read", "Grep", "Glob", "Bash"],
        model: "sonnet"
      },

      // Test coverage analyst
      "test-analyst": {
        description: "Testing and quality assurance expert. Use for test coverage analysis, test recommendations, and QA improvements.",
        prompt: `You are a QA and testing expert.
Evaluate:
- Test coverage completeness
- Edge cases and boundary conditions
- Integration test scenarios
- Mock and stub usage
- Test maintainability

Suggest missing tests with code examples.`,
        tools: ["Read", "Grep", "Glob", "Bash", "Write"],
        model: "haiku"
      },

      // Code quality reviewer
      "code-reviewer": {
        description: "Code quality and best practices expert. Use for code reviews, refactoring suggestions, and architecture analysis.",
        prompt: `You are a senior software architect focused on code quality.
Review:
- Code organization and modularity
- Design patterns and SOLID principles
- Error handling and edge cases
- Code duplication and technical debt
- Documentation quality

Provide refactoring suggestions with examples.`,
        tools: ["Read", "Grep", "Glob", "Edit", "Write"],
        model: "sonnet"
      }
    }
  }
});

// The main agent will automatically invoke appropriate subagents
// based on their descriptions and the task requirements
for await (const message of response) {
  if (message.type === 'assistant') {
    console.log(message.content);
  } else if (message.type === 'system' && message.subtype === 'subagent_start') {
    console.log(`Starting subagent: ${message.agent_name}`);
  } else if (message.type === 'system' && message.subtype === 'subagent_end') {
    console.log(`Subagent completed: ${message.agent_name}`);
  }
}
```

## DevOps Agent Example

```typescript
async function runDevOpsAgent(task: string) {
  const response = query({
    prompt: task,
    options: {
      model: "claude-sonnet-4-5",
      workingDirectory: process.cwd(),
      systemPrompt: `You are a DevOps automation expert.
- Monitor system health
- Deploy applications safely
- Handle incidents and alerts
- Maintain infrastructure
Always log your actions and notify relevant stakeholders.`,

      // Custom tools
      mcpServers: {
        "app-services": appTools
      },

      // Subagents for specialized tasks
      agents: {
        "deployment-agent": {
          description: "Handles application deployments and rollbacks",
          prompt: "You manage deployments. Verify tests pass, deploy to staging first, then production. Always create rollback plans.",
          tools: ["Bash", "Read", "mcp__app-services__log_event", "mcp__app-services__send_notification"],
          model: "sonnet"
        },
        "incident-responder": {
          description: "Responds to production incidents and outages",
          prompt: "You handle incidents. Assess impact, identify root cause, implement fixes, and communicate status updates.",
          tools: ["Bash", "Read", "Grep", "mcp__app-services__log_event", "mcp__app-services__send_notification"],
          model: "sonnet"
        },
        "monitoring-agent": {
          description: "Monitors system metrics and health checks",
          prompt: "You monitor systems. Check metrics, analyze trends, detect anomalies, and alert on issues.",
          tools: ["Bash", "Read", "mcp__app-services__log_event", "mcp__app-services__send_notification"],
          model: "haiku"
        }
      },

      // Permission control
      permissionMode: "default",
      canUseTool: async (toolName, input) => {
        // Log all tool usage
        console.log(`Tool requested: ${toolName}`);

        // Prevent destructive operations
        if (toolName === 'Bash') {
          const dangerousPatterns = ['rm -rf', 'dd if=', 'mkfs', '> /dev/'];
          if (dangerousPatterns.some(pattern => input.command.includes(pattern))) {
            return {
              behavior: "deny",
              message: "Destructive command blocked for safety"
            };
          }
        }

        // Require confirmation for deployments
        if (input.command?.includes('deploy') || input.command?.includes('kubectl apply')) {
          return {
            behavior: "ask",
            message: "Confirm deployment to production?"
          };
        }

        return { behavior: "allow" };
      }
    }
  });

  // Process agent responses
  let sessionId: string | undefined;
  const results: string[] = [];

  try {
    for await (const message of response) {
      switch (message.type) {
        case 'system':
          if (message.subtype === 'init') {
            sessionId = message.session_id;
            console.log(`Session started: ${sessionId}`);
          }
          break;

        case 'assistant':
          results.push(message.content);
          console.log('Agent:', message.content);
          break;

        case 'tool_call':
          console.log(`Executing: ${message.tool_name}`);
          break;

        case 'error':
          console.error('Error:', message.error);
          break;
      }
    }
  } catch (error) {
    console.error('Agent failed:', error);
    throw error;
  }

  return { sessionId, results };
}

// Usage examples
async function main() {
  // Deploy application
  await runDevOpsAgent("Deploy the latest version to production with health checks");

  // Investigate incident
  await runDevOpsAgent("API response time increased by 300% in last hour. Investigate and fix");
}
```

## Multi-Turn Conversations

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

async function* conversationFlow() {
  yield "Analyze the user authentication system";
  yield "Now add OAuth2 support";
  yield "Generate unit tests for the OAuth implementation";
}

const response = query({
  prompt: conversationFlow(),
  options: {
    model: "claude-sonnet-4-5",
    workingDirectory: "/path/to/project"
  }
});

for await (const message of response) {
  if (message.type === 'assistant') {
    console.log(message.content);
  }
}
```

### Event-Driven Conversation

```typescript
async function interactiveAgent() {
  const userInputs: string[] = [];

  async function* getUserInput() {
    for (const input of userInputs) {
      yield input;
    }
  }

  // Start the query
  const response = query({
    prompt: getUserInput(),
    options: { model: "claude-sonnet-4-5" }
  });

  // Simulate user adding requests over time
  setTimeout(() => userInputs.push("Create a REST API server"), 1000);
  setTimeout(() => userInputs.push("Add authentication middleware"), 3000);
  setTimeout(() => userInputs.push("Write integration tests"), 5000);

  for await (const message of response) {
    console.log(message);
  }
}
```

## Session Management

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// Start a new session and capture the session ID
let sessionId: string | undefined;

const initialResponse = query({
  prompt: "Help me build a REST API with user authentication",
  options: { model: "claude-sonnet-4-5" }
});

for await (const message of initialResponse) {
  if (message.type === 'system' && message.subtype === 'init') {
    sessionId = message.session_id;
    console.log(`Session started: ${sessionId}`);
  }
}

// Resume the same session to continue the conversation
const resumedResponse = query({
  prompt: "Now add rate limiting to the API endpoints",
  options: {
    resume: sessionId,
    model: "claude-sonnet-4-5"
  }
});

for await (const message of resumedResponse) {
  // Process continued conversation
}

// Fork the session to explore an alternative approach
const forkedResponse = query({
  prompt: "Actually, let's redesign this as a GraphQL API instead",
  options: {
    resume: sessionId,
    forkSession: true,  // Creates a new branch without modifying original
    model: "claude-sonnet-4-5"
  }
});

for await (const message of forkedResponse) {
  // Explore alternative implementation
}
```

## Filesystem Settings

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// Load settings from all sources (user, project, local)
const allSettings = query({
  prompt: "Build a new feature with project conventions",
  options: {
    settingSources: ["user", "project", "local"],
    model: "claude-sonnet-4-5"
  }
});

// Load only project settings (useful for CI/CD)
const projectOnly = query({
  prompt: "Run automated code review",
  options: {
    settingSources: ["project"],
    model: "claude-sonnet-4-5"
  }
});

// No filesystem settings (fully isolated)
const isolated = query({
  prompt: "Analyze this code snippet",
  options: {
    settingSources: [],  // Don't load any settings files
    workingDirectory: "/tmp/sandbox",
    model: "claude-sonnet-4-5"
  }
});

// Combine with programmatic configuration
const hybrid = query({
  prompt: "Implement the user authentication system",
  options: {
    settingSources: ["project"],  // Load CLAUDE.md and settings.json
    systemPrompt: "Follow security best practices and company coding standards.",
    agents: {
      "security-checker": {
        description: "Security validation specialist",
        prompt: "Validate all security implementations against OWASP guidelines.",
        tools: ["Read", "Grep"]
      }
    },
    model: "claude-sonnet-4-5"
  }
});

for await (const message of hybrid) {
  console.log(message);
}
```

## External MCP Servers

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// Configure external MCP servers
const response = query({
  prompt: "List all files in the project directory and analyze the codebase structure",
  options: {
    mcpServers: {
      // Filesystem server via stdio
      "filesystem": {
        command: "npx",
        args: ["@modelcontextprotocol/server-filesystem"],
        env: {
          ALLOWED_PATHS: "/Users/developer/projects:/tmp"
        }
      },
      // Git operations server
      "git": {
        command: "npx",
        args: ["@modelcontextprotocol/server-git"],
        env: {
          GIT_REPO_PATH: "/Users/developer/projects/my-repo"
        }
      },
      // HTTP/SSE server
      "remote-service": {
        url: "https://api.example.com/mcp",
        headers: {
          "Authorization": "Bearer your-token-here"
        }
      }
    },
    allowedTools: [
      "mcp__filesystem__list_files",
      "mcp__filesystem__read_file",
      "mcp__git__log",
      "mcp__git__diff",
      "mcp__remote-service__analyze"
    ],
    model: "claude-sonnet-4-5"
  }
});

for await (const message of response) {
  if (message.type === 'assistant') {
    console.log(message.content);
  } else if (message.type === 'tool_result') {
    console.log(`Tool ${message.tool_name} completed`);
  }
}
```

## Error Handling

```typescript
async function processWithErrorHandling() {
  try {
    const response = query({
      prompt: "Analyze and refactor the payment processing module",
      options: {
        model: "claude-sonnet-4-5",
        workingDirectory: "/path/to/project",
        permissionMode: "default"
      }
    });

    for await (const message of response) {
      switch (message.type) {
        case 'assistant':
          // Handle assistant messages
          if (typeof message.content === 'string') {
            console.log('Assistant:', message.content);
          } else {
            message.content.forEach(block => {
              if (block.type === 'text') {
                console.log('Text:', block.text);
              } else if (block.type === 'tool_use') {
                console.log(`Tool request: ${message.name}`);
              }
            });
          }
          break;

        case 'tool_call':
          console.log(`Executing tool: ${message.tool_name}`);
          console.log(`Input:`, JSON.stringify(message.input, null, 2));
          break;

        case 'tool_result':
          console.log(`Tool ${message.tool_name} result:`, message.result);
          break;

        case 'error':
          console.error('Agent error:', message.error);
          if (message.error.type === 'permission_denied') {
            console.log('Permission was denied for:', message.error.tool);
          }
          break;

        case 'system':
          if (message.subtype === 'init') {
            console.log(`Session ID: ${message.session_id}`);
          } else if (message.subtype === 'completion') {
            console.log('Task completed');
          }
          break;

        default:
          console.log('Other message:', message);
      }
    }
  } catch (error) {
    console.error('Fatal error:', error);

    // Handle specific error types
    if (error.code === 'AUTHENTICATION_FAILED') {
      console.error('Check your API key configuration');
    } else if (error.code === 'RATE_LIMIT_EXCEEDED') {
      console.error('Rate limit exceeded, retry after delay');
    } else if (error.code === 'CONTEXT_LENGTH_EXCEEDED') {
      console.error('Context too large, consider session compaction');
    }
  }
}

processWithErrorHandling();
```
