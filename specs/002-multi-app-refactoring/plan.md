# Implementation Plan: Multi-App Architecture Refactoring

**Branch**: `002-multi-app-refactoring` | **Date**: 2025-10-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-multi-app-refactoring/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Transform the current single-app repository into a multi-app monorepo with isolated applications in `apps/` directory. Migrate resume-agent to apps/resume-agent/ while maintaining 100% backward compatibility. Integrate observability system (server + web client) based on Disler's Multi-Agent Observability patterns. Each app operates independently with own dependencies, configuration, and .claude/ directory, while sharing root-level data directories (data/, resumes/, job-applications/).

## Technical Context

**Language/Version**:
- Python 3.10+ (resume-agent, hooks)
- TypeScript 5.x (observability-server)
- Vue 3 (web client)

**Primary Dependencies**:
- **resume-agent**: UV, FastMCP 2.0, Pydantic, Claude Agent SDK
- **observability-server**: Bun, SQLite, WebSocket
- **client**: Vue 3, Vite, TailwindCSS
- **hooks**: UV (for Python scripts)

**Storage**:
- SQLite databases in root `data/` directory (resume_agent.db, events.db)
- YAML files in root `resumes/` directory
- Generated artifacts in root `job-applications/` directory

**Testing**: NEEDS CLARIFICATION - Testing framework and strategy not yet defined

**Target Platform**:
- Windows development environment (primary)
- Localhost deployment (observability-server on port 4000, client on port 5173)
- Claude Desktop integration via MCP protocol

**Project Type**: Multi-app monorepo (3+ independent applications)

**Performance Goals**:
- MCP tool calls: <2s for reads, <5s for writes, <10s for complete workflows
- Event ingestion: <100ms from hook to database
- WebSocket delivery: <1s from event to UI display
- System startup: <10s for all components operational

**Constraints**:
- Must maintain 100% backward compatibility with existing resume-agent workflows
- Observability overhead: <5% performance impact on agent operations
- Path resolution: Must work correctly from any app location using absolute paths
- Non-blocking hooks: Event sending must not block agent operations

**Scale/Scope**:
- 3-4 applications (resume-agent, observability-server, client, future translation-teacher)
- ~10 phases of migration work
- ~100 checklist items across all phases
- Events database: Support 1000+ events with performant queries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gates (Before Phase 0)

- [x] **Does this feature belong in an existing app or require a new one?**
  - **Answer**: Requires new apps (observability-server, client) AND restructuring existing app (resume-agent)
  - **Justification**: This is infrastructure work to enable multi-app architecture - the resume-agent moves location, and observability apps are system-level components serving all apps

- [x] **If new app: Is the complexity justified? (Current count → new count)**
  - **Answer**: 1 app → 3 apps (resume-agent, observability-server, client)
  - **Justification**: Each app serves distinct purpose:
    - resume-agent: Career application workflows (existing functionality)
    - observability-server: Event collection and storage (system observability)
    - client: Real-time monitoring dashboard (developer tools)
  - Future 4th app (translation-teacher) deferred to later phase

- [x] **Can this be achieved without adding new dependencies?**
  - **Answer**: No - requires Bun runtime for TypeScript apps, Vue 3 ecosystem for client
  - **Justification**: Observability pattern from Disler's proven reference implementation requires TypeScript/Bun stack. Alternative would be building from scratch in Python (higher risk, longer development time). See Complexity Tracking for details.

- [x] **Does this follow the Data Access Layer pattern?**
  - **Answer**: Yes - resume-agent continues using existing data-access-agent pattern
  - **Details**: Observability-server has its own DAL for events database. No changes to existing DAL architecture.

- [x] **Are performance requirements defined?**
  - **Answer**: Yes - see Technical Context Performance Goals section
  - **Metrics**: <2s reads, <5s writes, <100ms event ingestion, <1s WebSocket delivery, <10s startup

- [x] **Is observability integration planned?**
  - **Answer**: Yes - this IS the observability integration
  - **Details**: Root-level hooks (PreToolUse, PostToolUse) will send events to observability-server

### Post-Design Gates (After Phase 1)

- [x] **Are all data schemas defined with Pydantic/TypeScript types?**
  - **Answer**: Yes - see data-model.md
  - **Details**:
    - Event entity: TypeScript interface with Zod validation schema
    - Application entity: TypeScript interface (in-memory)
    - HookConfiguration: JSON schema with validation
    - Existing resume-agent entities: Already have Pydantic schemas (unchanged)

- [x] **Are contract tests planned for all interfaces?**
  - **Answer**: Yes - see contracts/ directory
  - **Contracts Defined**:
    - observability-server-api.yaml: OpenAPI 3.0 spec for HTTP endpoints
    - hook-script-contract.md: Hook script CLI interface and behavior
    - websocket-stream-contract.md: WebSocket protocol and message format
  - **Test Cases**: Each contract includes test scenarios and example implementations

- [x] **Is the implementation the simplest approach?**
  - **Answer**: Yes - leveraging proven reference implementation
  - **Rationale**:
    - Copying Disler's working code is simpler than building from scratch
    - Minimal adaptation required (path changes only)
    - Single-table database design (no over-normalization)
    - No shared libraries between apps (simplest isolation)
    - Fire-and-forget hooks (no complex acknowledgement protocols)

- [x] **Are all dependencies justified in Complexity Tracking?**
  - **Answer**: Yes - see Complexity Tracking section
  - **All dependencies justified**:
    - Bun + TypeScript: Required for observability-server (proven reference implementation)
    - Vue 3: Required for reactive dashboard (industry standard)
    - pytest/Bun test/Vitest: Standard testing frameworks for each language
    - SQLite: Already in use, no new dependency

**Reference**: See `.specify/memory/constitution.md` for complete principles

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
Cernji-Agents/                          # Repository root
├── apps/                               # All applications (NEW)
│   ├── resume-agent/                   # Career application MCP server (MIGRATED)
│   │   ├── .claude/
│   │   │   ├── agents/                 # Resume-specific agents
│   │   │   └── commands/               # /career:* slash commands
│   │   ├── resume_agent.py             # FastMCP server (PEP 723)
│   │   ├── README.md                   # Setup and usage
│   │   └── .env.example                # Environment template
│   │
│   ├── observability-server/           # Event tracking server (NEW)
│   │   ├── src/
│   │   │   ├── index.ts                # HTTP + WebSocket server
│   │   │   ├── db.ts                   # SQLite event storage
│   │   │   └── types.ts                # TypeScript types
│   │   ├── package.json                # Bun dependencies
│   │   ├── tsconfig.json               # TypeScript config
│   │   ├── README.md
│   │   └── CLAUDE.md
│   │
│   └── client/                         # Web dashboard (NEW)
│       ├── src/
│       │   ├── App.vue                 # Main app
│       │   ├── components/             # Vue components
│       │   └── composables/            # Vue composables
│       ├── package.json                # Vue 3 dependencies
│       ├── vite.config.ts              # Vite configuration
│       ├── tailwind.config.js          # TailwindCSS config
│       └── README.md
│
├── .claude/                            # Root-level hooks (NEW/UPDATED)
│   ├── hooks/                          # Hook scripts (Python + UV)
│   │   └── send_event.py               # Event sender to observability
│   └── settings.json                   # Hook configuration
│
├── data/                               # Shared databases (EXISTING)
│   ├── resume_agent.db                 # Resume agent database
│   └── events.db                       # Observability events (NEW)
│
├── resumes/                            # Resume data (EXISTING)
│   ├── kris-cernjavic-resume.yaml
│   └── career-history.yaml
│
├── job-applications/                   # Generated artifacts (EXISTING)
│
├── scripts/                            # System management (NEW)
│   ├── start-system.sh                 # Start all apps
│   ├── stop-system.sh                  # Stop all apps
│   └── reset-observability.sh          # Reset events database
│
├── specs/                              # Feature specifications (EXISTING)
│   └── 002-multi-app-refactoring/      # This feature
│       ├── spec.md
│       ├── plan.md
│       ├── research.md                 # To be generated
│       ├── data-model.md               # To be generated
│       ├── quickstart.md               # To be generated
│       └── contracts/                  # To be generated
│
├── README.md                           # Root README (TO UPDATE)
├── CLAUDE.md                           # Root project instructions (TO UPDATE)
└── .mcp.json                           # MCP configuration (TO UPDATE)
```

**Structure Decision**: Multi-app monorepo (custom structure)

This is a multi-app architecture where each application in `apps/` is self-contained with its own:
- Dependencies (package.json, pyproject.toml, or PEP 723 inline)
- Configuration (.claude/ directory for agents and commands)
- Documentation (README.md, optional CLAUDE.md)

Shared resources remain at repository root:
- **data/**: SQLite databases accessible to all apps
- **resumes/**: Resume-specific YAML files
- **job-applications/**: Generated application artifacts
- **.claude/hooks/**: Root-level observability hooks
- **scripts/**: System-wide management scripts

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| **New Dependencies: Bun + TypeScript + Vue 3** | Observability system requires real-time WebSocket server and interactive web dashboard. Disler's proven reference implementation uses TypeScript/Bun stack. | Building from scratch in Python would: (1) Require reinventing WebSocket patterns, (2) Take significantly longer to develop, (3) Higher risk without proven reference, (4) Still need frontend framework anyway. Reusing proven code reduces risk and accelerates delivery. |
| **3 New Apps (1→3)** | Multi-app architecture requires: (1) Dedicated observability-server for event collection, (2) Dedicated client for real-time monitoring, (3) Isolated resume-agent location | Monolithic approach rejected because: (1) Cannot achieve independent deployment, (2) Dependencies would conflict (Python vs TypeScript), (3) Testing would be coupled, (4) Violates constitution principle I (Multi-App Isolation). This IS the infrastructure for multi-app support. |
| **Testing Framework Not Yet Defined** | NEEDS CLARIFICATION in Technical Context - will be resolved in Phase 0 research | Must research best practices for: (1) MCP contract testing, (2) Multi-app integration testing, (3) WebSocket testing patterns. Cannot define tests until framework is chosen. |

**Justification Summary**: This refactoring IS the implementation of constitution principles I (Multi-App Isolation) and IV (Observability by Default). The complexity (new apps, new dependencies) is required to establish the foundation for all future development. Using Disler's proven patterns significantly reduces risk compared to building from scratch.

