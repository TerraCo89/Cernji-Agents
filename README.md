# Cernji Agents

Multi-app monorepo for AI-powered career tools and agent observability.

## Architecture

This repository uses a multi-app architecture with isolated applications in the `apps/` directory. Each app has its own dependencies, configuration, and `.claude/` directory, while sharing root-level data directories.

### Directory Structure

```
Cernji-Agents/                      # Repository root
├── apps/                           # Isolated applications
│   ├── resume-agent/               # Career application MCP server
│   │   ├── .claude/
│   │   │   ├── agents/             # Resume-specific AI agents
│   │   │   └── commands/           # /career:* slash commands
│   │   ├── resume_agent.py         # FastMCP server (PEP 723)
│   │   └── README.md
│   │
│   ├── observability-server/       # Event tracking server
│   │   ├── src/
│   │   │   ├── index.ts            # HTTP + WebSocket server
│   │   │   ├── db.ts               # SQLite event storage
│   │   │   └── types.ts            # TypeScript types
│   │   ├── package.json
│   │   └── README.md
│   │
│   └── client/                     # Web dashboard
│       ├── src/
│       │   ├── App.vue             # Main app component
│       │   ├── components/         # Vue components
│       │   └── composables/        # Vue composables
│       ├── package.json
│       └── README.md
│
├── .claude/                        # Root-level hooks
│   ├── hooks/
│   │   └── send_event.py           # Event sender to observability
│   └── settings.json               # Hook configuration
│
├── data/                           # Shared databases
│   ├── resume_agent.db             # Resume agent data
│   └── events.db                   # Observability events
│
├── resumes/                        # Resume data files
│   ├── kris-cernjavic-resume.yaml
│   └── career-history.yaml
│
├── job-applications/               # Generated artifacts
│
├── scripts/                        # System management
│   ├── start-system.ps1            # Start all apps
│   ├── stop-system.ps1             # Stop all apps
│   └── reset-observability.ps1     # Reset events database
│
├── specs/                          # Feature specifications
└── README.md                       # This file
```

### Applications

- **[resume-agent](apps/resume-agent/)** - MCP server for career application workflows
- **[observability-server](apps/observability-server/)** - Event tracking server for real-time monitoring
- **[client](apps/client/)** - Web dashboard for monitoring agent activities

### Shared Resources

- `data/` - SQLite databases (resume_agent.db, events.db)
- `resumes/` - Resume files (YAML, PDF)
- `job-applications/` - Generated application materials
- `.claude/hooks/` - Root-level observability hooks
- `scripts/` - System management scripts (PowerShell)

## Quick Start

### NEW: Claude Skills (Zero Setup)

**Use career tools instantly in Claude Code 0.4.0+ without MCP server setup:**

1. Open this repository in Claude Code
2. Try: "Analyze this job posting: https://japan-dev.com/jobs/cookpad/senior-backend-engineer"
3. Claude automatically discovers and uses the **job-analyzer** skill

**Available Skills:**
- `.claude/skills/career/job-analyzer/` - Job posting analysis

**Coming Soon:** resume-writer, cover-letter-writer, portfolio-finder, data-access

See [specs/005-decompose-mcp-to-skills/quickstart.md](specs/005-decompose-mcp-to-skills/quickstart.md) for testing guide.

---

### Prerequisites

- **Python 3.10+** with UV package manager
- **Bun** (for observability server and client)
- **Claude Desktop** (for MCP integration) OR **Claude Code 0.4.0+** (for skills)

### Starting the Complete System

```powershell
# Start observability server + web client (Windows)
.\scripts\start-system.ps1

# Stop the system
.\scripts\stop-system.ps1

# Reset observability database
.\scripts\reset-observability.ps1
```

### Running Resume Agent Only

```bash
# From repository root
uv run apps/resume-agent/resume_agent.py
```

### MCP Configuration

Add to Claude Desktop's `claude_desktop_config.json`:

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

## Features

### Resume Agent

- Analyze job postings and assess fit
- Generate ATS-optimized tailored resumes
- Create personalized cover letters
- Search GitHub portfolio for relevant examples
- Manage career history and achievements

See [apps/resume-agent/README.md](apps/resume-agent/README.md) for details.

### Observability System

- **Real-time event tracking** across all agents via hooks
- **Web dashboard** at http://localhost:5173 for monitoring
- **Hook-based instrumentation** (PreToolUse, PostToolUse, UserPromptSubmit)
- **Session timeline** and debugging capabilities
- **AI-generated summaries** of tool usage

**Usage**:
1. Start system: `.\scripts\start-system.ps1`
2. Open dashboard: http://localhost:5173
3. Use Claude Desktop - events appear automatically
4. Filter by app, session, or event type

## Development

Each app is independently developed and tested:

```bash
# Resume Agent
cd apps/resume-agent
pytest

# Observability Server
cd apps/observability-server
bun install
bun test

# Web Client
cd apps/client
bun install
npm run test
```

## Documentation

- [CLAUDE.md](CLAUDE.md) - Complete project instructions
- [specs/](specs/) - Feature specifications and design docs
- [.specify/](\.specify/) - Specification framework and templates

## Project Governance

This project follows the **Cernji-Agents Constitution** (`.specify/memory/constitution.md`).

Core principles:
- Multi-App Isolation
- Data Access Layer with validation
- Test-First Development
- Observability by Default
- Performance Standards

## Tech Stack

- **Resume Agent**: Python 3.10+, UV, FastMCP, Pydantic, SQLite
- **Observability Server**: Bun, TypeScript, SQLite (WAL mode), WebSocket
- **Web Client**: Vue 3, Vite, TailwindCSS, Bun
- **Hooks**: Python with UV (PEP 723 scripts)

## License

Private project for personal use.
