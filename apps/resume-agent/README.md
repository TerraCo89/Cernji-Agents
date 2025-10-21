# Resume Agent

MCP server providing career application tools for job applications.

## Overview

The Resume Agent is a Model Context Protocol (MCP) server that helps with:
- Analyzing job postings
- Tailoring resumes for specific roles
- Generating cover letters
- Finding portfolio examples from GitHub
- Managing career history and achievements

## Quick Start

### Prerequisites

- Python 3.10+
- UV package manager
- Claude Desktop (for MCP integration)

### Starting the Server

```bash
# From repository root
uv run apps/resume-agent/resume_agent.py
```

### MCP Configuration

Add to Claude Desktop's MCP configuration:

```json
{
  "mcpServers": {
    "resume-agent": {
      "command": "uv",
      "args": ["run", "apps/resume-agent/resume_agent.py"],
      "env": {}
    }
  }
}
```

## Tech Stack

- **Framework**: FastMCP 2.0
- **Dependencies**: UV (PEP 723 inline dependencies)
- **AI Orchestration**: Claude Agent SDK
- **Validation**: Pydantic models
- **Database**: SQLite
