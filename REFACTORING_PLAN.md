# Multi-App Refactoring Plan

## Overview
Transform ResumeAgent into a multi-app monorepo following Disler's Multi-Agent Observability patterns.

**Reference Repository**: https://github.com/disler/claude-code-hooks-multi-agent-observability

## Planned Applications

1. **resume-agent** - MCP server for career applications (Python + UV + FastMCP)
2. **translation-teacher** - Claude 2.0 agent for language learning (slash commands + agents)
3. **observability-server** - Event tracking server (TypeScript/Bun + SQLite + WebSocket)
4. **client** - Web dashboard for monitoring agents (Vue 3 + Vite + TailwindCSS)

## New Directory Structure

```
ResumeAgent/
├── apps/
│   ├── resume-agent/          # MCP server (Python + UV + FastMCP)
│   │   ├── .claude/
│   │   │   ├── agents/       # Resume-specific agents
│   │   │   └── commands/     # /career:* slash commands
│   │   ├── resume_agent.py   # Moved from root
│   │   ├── README.md
│   │   └── .env.example
│   │
│   ├── translation-teacher/   # NEW: Claude 2.0 agent
│   │   ├── .claude/
│   │   │   ├── agents/       # Translation-specific agents
│   │   │   └── commands/     # /translate:* slash commands
│   │   ├── README.md
│   │   └── .env.example
│   │
│   ├── observability-server/  # NEW: TypeScript/Bun (Disler pattern)
│   │   ├── src/
│   │   │   ├── index.ts      # HTTP + WebSocket server
│   │   │   ├── db.ts         # SQLite event storage
│   │   │   └── types.ts      # TypeScript types
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── README.md
│   │   └── CLAUDE.md
│   │
│   └── client/                # NEW: Vue 3 web client (Disler pattern)
│       ├── src/
│       │   ├── App.vue       # Main app
│       │   ├── components/   # Vue components
│       │   └── composables/  # Vue composables
│       ├── package.json
│       ├── vite.config.ts
│       ├── tailwind.config.js
│       └── README.md
│
├── .claude/                   # Root-level hooks (observability)
│   ├── hooks/                 # Hook scripts (Python + UV)
│   │   └── send_event.py     # Event sender to observability
│   └── settings.json          # Hook configuration
│
├── scripts/                   # System management
│   ├── start-system.sh       # Start all apps
│   ├── stop-system.sh        # Stop all apps
│   └── reset-observability.sh
│
├── data/                      # Shared data (SQLite DBs)
│   └── resume_agent.db       # Resume agent database
│
├── resumes/                   # Resume-specific data
│   ├── kris-cernjavic-resume.yaml
│   └── career-history.yaml
│
├── job-applications/          # Application outputs
│
├── ai_docs/                   # AI documentation
├── app_docs/                  # Application documentation
├── specs/                     # Feature specifications
│
├── README.md                  # Root README
├── CLAUDE.md                  # Root project instructions
└── .env.example               # Root environment template
```

## Migration Steps

### Phase 1: Resume Agent Migration ✓
1. Move resume_agent.py → `apps/resume-agent/resume_agent.py`
2. Move .claude/agents/ (resume-specific) → `apps/resume-agent/.claude/agents/`
3. Move .claude/commands/career/ → `apps/resume-agent/.claude/commands/`
4. Create apps/resume-agent/README.md with setup instructions
5. Update paths in resume_agent.py to reference root-level data directories
6. Update .mcp.json to point to new location

### Phase 2: Observability Server Setup (TypeScript/Bun)
1. Copy from Disler's repo:
   - apps/server/ structure
   - SQLite + WebSocket patterns
   - Database initialization
2. Adapt for multi-app monitoring
3. Create CLAUDE.md with Disler-style prompts
4. Add package.json with Bun dependencies

### Phase 3: Web Client Setup (Vue 3)
1. Copy from Disler's repo:
   - apps/client/ structure
   - Vue 3 + Vite + TailwindCSS setup
   - Event timeline components
2. Adapt UI for resume + translation monitoring
3. Configure Vite for proper ports

### Phase 4: Translation Teacher Agent
1. Create .claude/agents/ for translation agents
2. Create .claude/commands/translate/ for slash commands
3. Document translation workflow in README.md
4. Add .env.example for API keys

### Phase 5: Root-Level Observability Hooks
1. Copy .claude/hooks/ from Disler's repo
2. Create root .claude/settings.json with hooks for all apps
3. Configure --source-app flags for each app

### Phase 6: System Scripts
1. Create scripts/start-system.sh:
   - Start observability server (bun)
   - Start web client (bun/vite)
   - Instructions for MCP servers
2. Create scripts/stop-system.sh
3. Create scripts/reset-observability.sh

### Phase 7: Documentation Updates
1. Update root README.md with multi-app architecture
2. Update root CLAUDE.md with new structure
3. Create app_docs/ for workflow documentation
4. Create specs/ for feature specs

## Key Design Decisions

1. **Data stays at root**: `data/`, `resumes/`, `job-applications/` remain accessible to all apps
2. **Each app is self-contained**: Own dependencies, own .claude/ directory
3. **Observability is opt-in**: Root `.claude/hooks/` sends events, apps can disable
4. **Single command startup**: `scripts/start-system.sh` launches everything
5. **Disler patterns**: Reuse proven observability + client code
6. **No shared libs**: Each app maintains its own dependencies

## Testing Strategy

1. Test resume-agent in new location
2. Test observability server receives events
3. Test web client displays events
4. Add translation-teacher incrementally
5. Verify all slash commands work

## Configuration Changes

### .mcp.json (root)
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

### Root .claude/settings.json
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "uv run .claude/hooks/send_event.py --source-app resume-agent --event-type PreToolUse --summarize"
      }]
    }],
    "PostToolUse": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "uv run .claude/hooks/send_event.py --source-app resume-agent --event-type PostToolUse --summarize"
      }]
    }]
  }
}
```

## Migration Notes

- Backup current working state before starting
- Test each phase independently
- Keep old files until new structure is verified
- Update all path references in Python code
- Test MCP server connectivity after migration
