# Resume Agent

MCP server for career application management using Claude AI.

## Overview

This MCP server exposes career application tools to Claude Desktop and other MCP clients. It helps you:
- Analyze job postings
- Tailor resumes for specific roles
- Generate cover letters
- Track portfolio examples
- Manage career history

## Architecture

- **Language**: Python 3.10+
- **Package Manager**: UV (Astral)
- **Framework**: FastMCP 2.0
- **AI Integration**: Claude Agent SDK
- **Storage**: SQLite (via SQLModel) or YAML files
- **Transport**: HTTP Streamable (port 8080) or stdio

## Quick Start

### Prerequisites

- Python 3.10+
- [UV package manager](https://docs.astral.sh/uv/)
- Claude Desktop or other MCP client

### Installation

1. **Install UV** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run the MCP server**:
   ```bash
   uv run resume_agent.py
   ```

   For HTTP server mode (production):
   ```bash
   uv run resume_agent.py --transport streamable-http --port 8080
   ```

## Configuration

### MCP Client Setup (Claude Desktop)

Update your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "resume-agent": {
      "command": "uv",
      "args": ["run", "D:/source/ResumeAgent/apps/resume-agent/resume_agent.py"],
      "env": {}
    }
  }
}
```

Or use the root `.mcp.json` (recommended for multi-app setup):

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

### Environment Variables

Create `.env` file:

```env
# Storage Backend (default: sqlite)
STORAGE_BACKEND=sqlite

# SQLite Database Path (default: ../../data/resume_agent.db)
SQLITE_DATABASE_PATH=../../data/resume_agent.db

# User ID (for multi-user support)
USER_ID=default
```

## Available MCP Tools

### Workflow Tools
- **analyze_job(job_url)** - Analyze job posting and assess match
- **tailor_resume(job_url)** - Generate ATS-optimized resume
- **apply_to_job(job_url, include_cover_letter)** - Complete application workflow

### Data Access Tools
- **data_read_master_resume()** - Read master resume
- **data_read_career_history()** - Read career history
- **data_read_job_analysis(company, job_title)** - Read job analysis
- **data_write_job_analysis(company, job_title, job_data)** - Save job analysis
- **data_add_achievement(company, achievement_description, metric)** - Add achievement
- **data_add_technology(company, technologies)** - Add technologies

### Portfolio Library Tools
- **data_add_portfolio_example(title, content, ...)** - Add code example
- **data_list_portfolio_examples(limit, technology_filter, company_filter)** - List examples
- **data_search_portfolio_examples(query, technologies)** - Search examples

## Data Storage

All data is stored in the root project directories:

- **Master Resume**: `../../resumes/kris-cernjavic-resume.yaml`
- **Career History**: `../../resumes/career-history.yaml`
- **SQLite Database**: `../../data/resume_agent.db`
- **Job Applications**: `../../job-applications/{Company}_{JobTitle}/`

## Slash Commands

This app includes slash commands for direct CLI usage:

- `/career:analyze-job [job-url]` - Analyze job posting
- `/career:tailor-resume [job-url]` - Tailor resume
- `/career:apply [job-url]` - Complete application workflow
- `/career:add-portfolio [title]` - Add portfolio example
- `/career:search-portfolio [query]` - Search portfolio
- `/career:list-portfolio` - List all portfolio examples
- `/career:update-master` - Update master resume

## Development

### File Structure

```
apps/resume-agent/
├── .claude/
│   ├── agents/           # Agent prompts
│   └── commands/         # Slash command definitions
├── resume_agent.py       # Main MCP server
├── README.md            # This file
└── .env.example         # Environment template
```

### Testing

Test the MCP server:

```bash
# Run server
uv run resume_agent.py

# Test with Claude Desktop
# Open Claude Desktop and use MCP tools
```

Test slash commands:

```bash
# From project root
claude -- /career:analyze-job https://example.com/job-posting
```

## Architecture Notes

- **Single-file deployment**: All code in `resume_agent.py` using PEP 723 inline dependencies
- **UV package manager**: 10-100x faster than pip, auto-handles venvs
- **FastMCP framework**: High-level MCP abstractions, decorator-based
- **Claude Agent SDK**: Reuses `.claude/agents/` prompts, handles AI orchestration
- **Pydantic validation**: All data validated before read/write
- **Data Access Layer**: Centralized file I/O with schema validation

## Troubleshooting

### MCP Server Not Starting

1. Check UV is installed: `uv --version`
2. Check Python version: `python --version` (needs 3.10+)
3. Check logs in Claude Desktop console

### Database Errors

1. Verify `STORAGE_BACKEND=sqlite` in .env
2. Check database exists: `../../data/resume_agent.db`
3. Verify data directory has write permissions

### Path Issues

1. Verify paths in .mcp.json point to correct location
2. Use absolute paths if relative paths fail
3. Check working directory is project root

## Related Documentation

- [Root README](../../README.md) - Overall project architecture
- [Root CLAUDE.md](../../CLAUDE.md) - Project instructions for AI
- [Slash Commands](../../.claude/commands/career/) - Command definitions
- [Agent Prompts](../../.claude/agents/) - AI agent configurations
