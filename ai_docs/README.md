# Library Documentation

This folder contains curated documentation from Context7 MCP for Claude Code and Claude Agent SDK libraries.

## Purpose

Having library documentation locally improves:
- **Accuracy**: Direct reference to official documentation
- **Speed**: No need to fetch docs repeatedly
- **Offline Access**: Documentation available without internet
- **Version Control**: Track which version of docs we're using

## Contents

### 1. Claude Code

Official Claude Code CLI tool documentation from Anthropic.

**Source**: `/anthropics/claude-code` (Context7)
**Trust Score**: 8.8
**Code Snippets**: 36

Files:
- [CLI-USAGE.md](claude-code/CLI-USAGE.md) - Installation, commands, environment setup
- [CONFIGURATION.md](claude-code/CONFIGURATION.md) - Settings, permissions, hooks, plugins
- [GIT-WORKFLOWS.md](claude-code/GIT-WORKFLOWS.md) - Git automation and GitHub integration

### 2. Claude Agent SDK (Python)

Python SDK for programmatically building AI agents with Claude Code's capabilities.

**Source**: `/anthropics/claude-agent-sdk-python` (Context7)
**Trust Score**: 8.8
**Code Snippets**: 21

Files:
- [QUICKSTART.md](claude-agent-sdk-python/QUICKSTART.md) - Installation, basic queries, error handling
- [ADVANCED.md](claude-agent-sdk-python/ADVANCED.md) - Custom tools, MCP servers, hooks, testing

### 3. Claude Agent SDK (TypeScript)

TypeScript SDK for programmatically building AI agents with Claude Code's capabilities.

**Source**: `/anthropics/claude-agent-sdk-typescript` (Context7)
**Trust Score**: 8.5
**Code Snippets**: 15

Files:
- [QUICKSTART.md](claude-agent-sdk-typescript/QUICKSTART.md) - Installation, basic queries, permissions
- [ADVANCED.md](claude-agent-sdk-typescript/ADVANCED.md) - Custom tools, subagents, sessions, external MCP servers

## Key Concepts

### Claude Code CLI
- **What**: Terminal tool for agentic coding
- **Use Case**: Interactive coding assistant in your terminal
- **Key Features**: File operations, git workflows, custom commands, plugins

### Claude Agent SDK
- **What**: Programmatic API for building custom agents
- **Use Case**: Embedding Claude Code capabilities in your applications
- **Key Features**: Custom tools, hooks, subagents, session management

### MCP (Model Context Protocol)
- **What**: Protocol for connecting Claude to external tools and data
- **Use Case**: Extend Claude's capabilities with custom integrations
- **Types**:
  - **SDK MCP Servers**: In-process Python/TypeScript tools
  - **External MCP Servers**: Standalone processes (stdio/HTTP)

## Relevance to ResumeAgent MCP Server

This documentation is critical for building our MCP server because:

1. **Programmatic Agent Creation**: We can instantiate Claude agents using the SDK rather than implementing AI logic from scratch
2. **Tool Integration**: Understanding MCP servers shows how to expose our resume tools
3. **Session Management**: Learn how to maintain context across multi-turn conversations
4. **Permission Control**: Implement safe file access for resume data
5. **Architecture Patterns**: Follow Anthropic's patterns for agent orchestration

### Key Insight for Our Project

**YES, we can use the Claude Agent SDK to simplify our MCP server!**

Instead of:
- Implementing AI logic ourselves
- Calling Claude API directly
- Managing conversation state manually

We can:
- Use `query()` from Claude Agent SDK
- Define custom tools with `@tool` decorator (Python) or `tool()` (TypeScript)
- Let the SDK handle conversation, permissions, and agent orchestration
- Focus on domain logic (resume tailoring, job analysis, portfolio search)

### Architecture Decision

Our MCP server should:
1. **HTTP Transport**: Use FastAPI (Python) with MCP Streamable HTTP
2. **Agent SDK**: Leverage `claude-agent-sdk-python` for AI capabilities
3. **Custom Tools**: Define resume operations as MCP tools
4. **Existing Prompts**: Reuse agent prompts from `.claude/agents/`
5. **Claude Desktop Subscription**: SDK will use the configured API key

## Updating Documentation

To refresh documentation from Context7:

```bash
# Use the Context7 MCP to fetch latest docs
# See examples in this project's history
```

## Last Updated

**Date**: 2025-10-18
**Claude Code Version**: Based on `/anthropics/claude-code` Context7 library
**SDK Versions**:
- Python: `/anthropics/claude-agent-sdk-python`
- TypeScript: `/anthropics/claude-agent-sdk-typescript`
