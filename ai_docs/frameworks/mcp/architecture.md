# MCP Server Architecture for ResumeAgent

Based on Claude Code and Claude Agent SDK documentation.

## Overview

This document outlines the architecture for transforming ResumeAgent into an MCP server that exposes career application tools to any MCP client.

## Technology Stack

### Core Components
- **Language**: Python 3.10+
- **MCP Transport**: HTTP Streamable (via `mcp` Python SDK)
- **AI Agent Engine**: `claude-agent-sdk-python`
- **Web Framework**: FastAPI (for HTTP transport)
- **API Key**: Uses Claude Desktop subscription (configured on PC)

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Clients                              │
│          (Claude Desktop, VS Code, etc.)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP Streamable Transport
┌──────────────────────▼──────────────────────────────────────┐
│                   MCP Server Layer                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  MCP Tools (exposed via mcp Python SDK)                │ │
│  │  - analyze_job(job_url)                                │ │
│  │  - tailor_resume(job_analysis)                         │ │
│  │  - generate_cover_letter(job_analysis)                 │ │
│  │  - search_portfolio(technologies[])                    │ │
│  │  - apply_to_job(job_url)                               │ │
│  │  - update_master_resume(section, data)                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  MCP Resources (data exposure)                         │ │
│  │  - resume://master                                     │ │
│  │  - resume://applications/recent                        │ │
│  │  - resume://portfolio-matrix                           │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 Agent Orchestration Layer                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Claude Agent SDK (claude-agent-sdk-python)            │ │
│  │  - Manages AI interactions                             │ │
│  │  - Handles tool calling                                │ │
│  │  - Maintains conversation state                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Agent Definitions (reuse existing prompts)            │ │
│  │  - JobAnalyzer (from .claude/agents/)                  │ │
│  │  - ResumeWriter                                        │ │
│  │  - CoverLetterWriter                                   │ │
│  │  - PortfolioFinder                                     │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Business Logic Layer                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Core Services                                         │ │
│  │  - ResumeService (YAML parsing, tailoring logic)       │ │
│  │  - JobAnalysisService (web scraping, parsing)          │ │
│  │  - PortfolioService (GitHub API integration)           │ │
│  │  - DocumentGenerationService (file creation)           │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                      Data Layer                             │
│  - Master Resume (YAML)                                     │
│  - Career History (YAML)                                    │
│  - Portfolio Matrix (JSON)                                  │
│  - Generated Applications (job-applications/)               │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Use Claude Agent SDK (Not Direct API Calls)

**Why**: Simplifies implementation dramatically

Instead of:
```python
# Manual approach - complex
response = anthropic.messages.create(
    model="claude-sonnet-4-5",
    messages=[...],
    tools=[...]
)
# Handle streaming, tool calls, conversation state manually
```

We do:
```python
# Agent SDK approach - simple
from claude_agent_sdk import query, ClaudeAgentOptions

async for message in query(
    prompt="Analyze this job posting: [URL]",
    options=ClaudeAgentOptions(
        system_prompt=job_analyzer_prompt,
        allowed_tools=["Read", "WebFetch", "Bash(gh:*)"]
    )
):
    # SDK handles everything
    print(message)
```

### 2. Reuse Existing Agent Prompts

Our `.claude/agents/` directory already contains expert prompts:
- `job-analyzer.md`
- `resume-writer.md`
- `cover-letter-writer.md`
- `portfolio-finder.md`

**Implementation**:
```python
# Load agent prompt from file
with open('.claude/agents/job-analyzer.md', 'r') as f:
    job_analyzer_prompt = f.read()

# Use in Claude Agent SDK
async def analyze_job(job_url: str):
    async for msg in query(
        prompt=f"Analyze this job: {job_url}",
        options=ClaudeAgentOptions(
            system_prompt=job_analyzer_prompt,
            allowed_tools=["WebFetch", "Read", "Bash(gh:*)"]
        )
    ):
        # Process response
        pass
```

### 3. HTTP Streamable Transport

**Why**: Best compatibility and performance for production

```python
from mcp.server.fastmcp import FastMCP

app = FastMCP(name="resume-agent")

@app.tool()
async def analyze_job(job_url: str) -> dict:
    # Implementation using Claude Agent SDK
    pass

if __name__ == '__main__':
    app.run(transport='streamable-http', port=8080)
```

### 4. Tool Definitions with Type Safety

```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

app = FastMCP(name="resume-agent")

class JobAnalysisResult(BaseModel):
    company: str
    role: str
    required_skills: list[str]
    optional_skills: list[str]
    match_score: float = Field(ge=0, le=10)
    recommendations: list[str]

@app.tool()
async def analyze_job(
    job_url: str = Field(description="URL of the job posting")
) -> JobAnalysisResult:
    """
    Analyze a job posting and extract structured requirements.

    Returns detailed analysis including required skills, company info,
    and match score against your master resume.
    """
    # Use Claude Agent SDK with JobAnalyzer agent
    job_analyzer_prompt = load_agent_prompt('job-analyzer.md')

    result = {}
    async for msg in query(
        prompt=f"Analyze: {job_url}",
        options=ClaudeAgentOptions(
            system_prompt=job_analyzer_prompt,
            allowed_tools=["WebFetch", "Read"]
        )
    ):
        # Extract structured data from agent response
        if isinstance(msg, AssistantMessage):
            result = parse_job_analysis(msg.content)

    return JobAnalysisResult(**result)
```

## Agent SDK Integration Pattern

### Pattern 1: Simple Agent Invocation

```python
async def invoke_agent(agent_name: str, task: str) -> str:
    """Generic agent invocation."""
    agent_prompt = load_agent_prompt(f'{agent_name}.md')

    response_text = ""
    async for msg in query(
        prompt=task,
        options=ClaudeAgentOptions(
            system_prompt=agent_prompt,
            allowed_tools=get_allowed_tools(agent_name)
        )
    ):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    response_text += block.text

    return response_text
```

### Pattern 2: Agent with Custom Tools

```python
from claude_agent_sdk import create_sdk_mcp_server, tool

# Define custom tools for agents
@tool("load_resume", "Load master resume data", {"section": str})
async def load_resume(args):
    with open('./resumes/kris-cernjavic-resume.yaml', 'r') as f:
        resume = yaml.safe_load(f)

    section = args.get("section", "all")
    if section == "all":
        return {"content": [{"type": "text", "text": yaml.dump(resume)}]}
    else:
        return {"content": [{"type": "text", "text": yaml.dump(resume.get(section, {}))}]}

# Create SDK MCP server with custom tools
resume_tools = create_sdk_mcp_server(
    name="resume-tools",
    version="1.0.0",
    tools=[load_resume]
)

# Use in agent
async def tailor_resume(job_analysis: dict) -> str:
    agent_prompt = load_agent_prompt('resume-writer.md')

    async for msg in query(
        prompt=f"Tailor resume for: {job_analysis}",
        options=ClaudeAgentOptions(
            system_prompt=agent_prompt,
            mcp_servers={"resume-tools": resume_tools},
            allowed_tools=["mcp__resume-tools__load_resume", "Write"]
        )
    ):
        # Process
        pass
```

### Pattern 3: Multi-Agent Orchestration

```python
async def apply_to_job(job_url: str) -> dict:
    """Orchestrate multiple agents for complete application."""

    # Step 1: Analyze job
    job_analysis = await invoke_agent(
        agent_name="job-analyzer",
        task=f"Analyze this job posting: {job_url}"
    )

    # Step 2: Search portfolio
    portfolio_examples = await invoke_agent(
        agent_name="portfolio-finder",
        task=f"Find code examples for: {job_analysis['required_skills']}"
    )

    # Step 3: Tailor resume
    tailored_resume = await invoke_agent(
        agent_name="resume-writer",
        task=f"Tailor resume for: {job_analysis}"
    )

    # Step 4: Generate cover letter
    cover_letter = await invoke_agent(
        agent_name="cover-letter-writer",
        task=f"Write cover letter for: {job_analysis}"
    )

    # Step 5: Save artifacts
    save_application(job_analysis, tailored_resume, cover_letter, portfolio_examples)

    return {
        "job_analysis": job_analysis,
        "resume_path": f"job-applications/{job_analysis['company']}_{job_analysis['role']}/Resume.txt",
        "cover_letter_path": f"job-applications/{job_analysis['company']}_{job_analysis['role']}/CoverLetter.txt"
    }
```

## API Key Configuration

The Claude Agent SDK will use the `ANTHROPIC_API_KEY` environment variable:

```python
# No need to pass API key explicitly
# SDK reads from environment or Claude Desktop config

async for msg in query(prompt="Hello"):
    print(msg)
```

For deployment:
```bash
# Set environment variable
export ANTHROPIC_API_KEY=sk-ant-...

# Or use Claude Desktop subscription (already configured on PC)
# SDK will automatically detect and use it
```

## MCP Server Deployment

### Local Development
```bash
# Install dependencies
pip install -e ".[dev]"

# Run server
python -m resume_agent_mcp.server --port 8080
```

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "resume-agent": {
      "url": "http://localhost:8080/mcp",
      "transport": "streamable-http"
    }
  }
}
```

### Docker Deployment (Future)
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .
RUN pip install -e .

ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

CMD ["python", "-m", "resume_agent_mcp.server", "--port", "8080"]
```

## Benefits of This Architecture

1. **Simplicity**: Claude Agent SDK handles AI complexity
2. **Reusability**: Existing agent prompts work as-is
3. **Maintainability**: Clear separation of concerns
4. **Extensibility**: Easy to add new tools/agents
5. **Type Safety**: Pydantic models for all data
6. **Production Ready**: HTTP transport, error handling
7. **Cost Effective**: Uses existing Claude Desktop subscription

## Next Steps

1. Create Python package structure
2. Implement MCP server with FastMCP
3. Port agent prompts to SDK format
4. Implement core tools (analyze_job, tailor_resume, etc.)
5. Test with Claude Desktop
6. Add error handling and logging
7. Document API for users
