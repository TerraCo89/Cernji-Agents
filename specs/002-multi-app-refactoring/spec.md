# Feature Specification: Multi-App Architecture Refactoring

**Feature Branch**: `002-multi-app-refactoring`
**Created**: 2025-10-21
**Status**: Draft
**Input**: User description: "Review the REFACTORING_PLAN.md and REFACTORING_CHECKLIST.md to convert it to the SpecKit format"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintain Resume Agent in New Location (Priority: P1)

As a user of the resume agent MCP server, I need the agent to continue functioning after being moved to the apps/ directory, so that I can continue using all career application features without interruption.

**Why this priority**: This is the foundation - existing functionality must continue working before adding new features. The resume agent is the primary working application and its continuity is critical.

**Independent Test**: Can be fully tested by starting the MCP server from the new location and running a complete job application workflow (/career:apply), which delivers a tailored resume and cover letter.

**Acceptance Scenarios**:

1. **Given** the resume agent has been moved to apps/resume-agent/, **When** the MCP server starts, **Then** it successfully connects and registers all tools
2. **Given** the MCP server is running from new location, **When** a user runs /career:analyze-job with a job URL, **Then** the job analysis is generated and saved correctly
3. **Given** the career history data exists in the root resumes/ directory, **When** the resume agent accesses it, **Then** all file paths resolve correctly
4. **Given** a complete application workflow is run, **When** data is saved, **Then** all outputs appear in the root job-applications/ directory
5. **Given** the SQLite database is in root data/ directory, **When** portfolio tools are used, **Then** database operations succeed

**Performance Requirements** (see Constitution VI):
- Response time: <2s for data reads, <5s for job analysis, <10s for complete application workflow
- Error handling: Clear error messages if paths are incorrect, with suggestions for fixing configuration
- Observability: Log file access attempts and database operations

---

### User Story 2 - Monitor Agent Activity Through Web Dashboard (Priority: P2)

As a developer running multiple AI agents, I need to see real-time activity in a web dashboard, so that I can understand what each agent is doing and debug issues quickly.

**Why this priority**: Observability is essential for multi-agent systems but not critical for basic functionality. It significantly improves developer experience and debugging capability.

**Independent Test**: Can be fully tested by starting the observability server and client, executing any slash command, and verifying that events appear in the web dashboard within 1 second.

**Acceptance Scenarios**:

1. **Given** the observability server is running, **When** an agent executes a tool, **Then** the event appears in the database within 100ms
2. **Given** the web client is connected via WebSocket, **When** a new event is saved, **Then** it appears in the UI within 1 second without refresh
3. **Given** multiple agents are running simultaneously, **When** they each execute operations, **Then** events from all agents are captured with correct source labels
4. **Given** the event timeline is displayed, **When** a user filters by app name, **Then** only events from that app are shown
5. **Given** 100+ events have been collected, **When** the dashboard loads, **Then** it displays the most recent 50 events with pagination

**Performance Requirements** (see Constitution VI):
- Response time: <100ms for event ingestion, <1s for WebSocket delivery
- Error handling: Graceful degradation if observability server is down (agents continue working)
- Observability: System must not interfere with agent operation (non-blocking, async)

---

### User Story 3 - Start Complete System With Single Command (Priority: P3)

As a developer, I need to start all system components with one command, so that I can quickly begin working without managing multiple processes manually.

**Why this priority**: Convenience feature that improves developer experience but not essential for core functionality. Developers can manually start each component.

**Independent Test**: Can be fully tested by running the start script and verifying that both the observability server and web client are accessible at their expected URLs.

**Acceptance Scenarios**:

1. **Given** the system is stopped, **When** the start-system script runs, **Then** the observability server starts on port 4000
2. **Given** the start script is running, **When** it completes, **Then** the web client is accessible at localhost:5173
3. **Given** both services are starting, **When** the script finishes, **Then** it displays URLs and status for each service
4. **Given** a service fails to start, **When** the script encounters the error, **Then** it displays a clear error message and stops
5. **Given** the system is already running, **When** the start script runs again, **Then** it detects running processes and warns the user

**Performance Requirements** (see Constitution VI):
- Response time: System fully operational within 10 seconds of script start
- Error handling: Clear messages if ports are already in use or dependencies missing
- Observability: Script logs startup progress and any errors encountered

---

### User Story 4 - Organize Applications in Isolated Directories (Priority: P1)

As a developer working on multiple independent applications, I need each application to have its own directory with isolated dependencies and configuration, so that changes to one app don't affect others.

**Why this priority**: This is the architectural foundation that enables all other stories. Without proper isolation, the multi-app structure cannot function correctly.

**Independent Test**: Can be fully tested by making a change to one app's dependencies or configuration and verifying that other apps are unaffected and continue to function.

**Acceptance Scenarios**:

1. **Given** the apps/ directory structure exists, **When** each app has its own .claude/ directory, **Then** agent prompts and slash commands are isolated per app
2. **Given** resume-agent is in apps/resume-agent/, **When** it accesses shared data directories, **Then** it uses correct relative paths from its location
3. **Given** observability-server has TypeScript dependencies, **When** resume-agent runs with Python, **Then** neither app's dependencies conflict
4. **Given** a new app is added to apps/, **When** it defines its own configuration, **Then** it operates independently without affecting existing apps
5. **Given** shared data exists in root directories (data/, resumes/, job-applications/), **When** any app accesses it, **Then** paths resolve correctly from any app location

**Performance Requirements** (see Constitution VI):
- Response time: No performance degradation from directory structure
- Error handling: Path resolution errors clearly indicate which app and which target path failed
- Observability: Log cross-app resource access

---

### Edge Cases

- What happens when the observability server is down but agents try to send events? (Agents must continue functioning without blocking)
- How does the system handle corrupted or missing data in shared directories? (Clear error messages indicating which file and which app attempted access)
- What happens when multiple MCP servers try to access the same SQLite database simultaneously? (SQLite handles locking, but apps should implement retry logic)
- How does the system behave when an app's .claude/ directory is missing or incomplete? (App should fail gracefully with clear message about missing configuration)
- What happens when paths are referenced using different conventions (absolute vs relative)? (All apps should normalize to absolute paths internally)
- How does the system handle WebSocket disconnection during active monitoring? (Client should automatically reconnect and resume event stream)
- What happens when starting the system with some components already running? (Start script should detect and report status of each component)

## Requirements *(mandatory)*

### Functional Requirements

#### Directory Structure and Organization

- **FR-001**: System MUST organize all applications in an apps/ directory with each app in its own subdirectory
- **FR-002**: System MUST maintain shared data directories (data/, resumes/, job-applications/) at repository root
- **FR-003**: Each app MUST have its own .claude/ directory containing app-specific agents and commands
- **FR-004**: System MUST support both root-level and app-level .claude/settings.json for hook configuration

#### Resume Agent Migration

- **FR-005**: Resume agent MUST run from apps/resume-agent/resume_agent.py location
- **FR-006**: Resume agent MUST access root-level data directories using absolute paths
- **FR-007**: Resume agent MUST resolve paths to resumes/, data/, and job-applications/ from its new location
- **FR-008**: MCP configuration MUST reference correct path to apps/resume-agent/resume_agent.py
- **FR-009**: All resume agent slash commands MUST function identically to pre-migration behavior
- **FR-010**: Resume agent MUST use SQLite database in root data/ directory

#### Observability System

- **FR-011**: System MUST include an observability server that collects events from all apps
- **FR-012**: Observability server MUST expose HTTP endpoint for event submission
- **FR-013**: Observability server MUST expose WebSocket endpoint for real-time event streaming
- **FR-014**: Observability server MUST store events in SQLite database at root data/events.db
- **FR-015**: System MUST include hooks that send events on PreToolUse and PostToolUse
- **FR-016**: Each event MUST include source app identifier (resume-agent, translation-teacher, etc.)
- **FR-017**: Hook scripts MUST not block agent operations if observability server is unavailable

#### Web Client Dashboard

- **FR-018**: System MUST include web client for visualizing agent events
- **FR-019**: Web client MUST connect to observability server via WebSocket
- **FR-020**: Web client MUST display events in real-time as they occur
- **FR-021**: Web client MUST support filtering events by source app
- **FR-022**: Web client MUST display at least 50 most recent events with pagination

#### System Management

- **FR-023**: System MUST provide start script that launches observability server and web client
- **FR-024**: System MUST provide stop script that gracefully shuts down all components
- **FR-025**: Start script MUST display URLs and status for each launched component
- **FR-026**: Stop script MUST verify all processes have terminated
- **FR-027**: System MUST provide reset script that clears observability database

#### Configuration and Documentation

- **FR-028**: Each app MUST have its own README.md with setup and usage instructions
- **FR-029**: Root README.md MUST document multi-app architecture and quick start
- **FR-030**: Root CLAUDE.md MUST reflect new directory structure with updated paths
- **FR-031**: System MUST maintain backward compatibility for existing resume agent workflows

### Key Entities *(include if feature involves data)*

- **Application**: Independent software component in apps/ directory with own dependencies, configuration, and .claude/ directory. Attributes: name, directory path, language/runtime, MCP server status (if applicable).

- **Event**: Record of agent activity captured by hooks. Attributes: timestamp, source app, event type (PreToolUse, PostToolUse, etc.), tool name, summarized payload, session identifier.

- **Shared Data Directory**: Root-level directory (data/, resumes/, job-applications/) accessible to all apps. Attributes: path, purpose, owning apps, access pattern (read-only vs read-write).

- **Hook Configuration**: Settings that define when and how to send observability events. Attributes: hook type (PreToolUse, PostToolUse, etc.), matcher pattern, source app flag, command to execute.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Resume agent operates from new location with 100% of existing functionality intact (all MCP tools and slash commands work)
- **SC-002**: All resume agent slash commands complete in same time as pre-migration (no performance degradation)
- **SC-003**: Observability system captures and displays events within 1 second of occurrence
- **SC-004**: System starts from single command with both observability server and client operational within 10 seconds
- **SC-005**: Multiple apps can run simultaneously without dependency conflicts or resource contention
- **SC-006**: Developers can add new apps to apps/ directory without modifying existing apps
- **SC-007**: System documentation enables a new developer to understand architecture within 15 minutes
- **SC-008**: All file path references resolve correctly from any app location (zero path resolution errors in testing)

## Assumptions

1. **Development Environment**: Assumes Windows development environment with PowerShell, UV package manager, and Bun runtime available
2. **Reference Implementation**: Observability patterns from Disler's repository are proven and can be adapted without significant modification
3. **Database Concurrency**: SQLite's built-in locking is sufficient for concurrent access from multiple apps (low concurrent write volume)
4. **Network Availability**: Observability server and client run on localhost; no external network access required
5. **Browser Compatibility**: Web client targets modern browsers with WebSocket support (Chrome, Firefox, Edge)
6. **Migration Timing**: Refactoring occurs while only resume-agent exists; translation-teacher is future work
7. **Backward Compatibility**: Existing data files (YAML resumes, SQLite database) do not require migration or format changes
8. **Hook Performance**: Event summarization and transmission adds <50ms overhead per tool use

## Out of Scope

1. **Translation Teacher Implementation**: Phase 4 defines structure but actual agent implementation is future work
2. **Remote Deployment**: System designed for local development; production deployment is out of scope
3. **Authentication/Security**: No user authentication; all components run on localhost for single developer
4. **Database Migration**: No changes to existing database schemas or data file formats
5. **Cross-Platform Scripts**: Windows scripts provided; Linux/macOS equivalents are future work
6. **Advanced Observability Features**: Metrics aggregation, alerting, and dashboards beyond basic event timeline
7. **Shared Libraries**: Each app maintains independent dependencies; no shared code libraries
8. **Hot Reload**: Changes to agent prompts or code require manual restarts

## Dependencies

- **External**: Disler's Multi-Agent Observability reference repository must be accessible for copying code
- **Technical**: Bun runtime required for observability server and web client
- **Technical**: UV package manager required for Python apps and hooks
- **Technical**: SQLite 3 for data persistence
- **Internal**: Resume agent must be fully functional before migration begins (current state)
- **Internal**: Root data directories (data/, resumes/, job-applications/) must remain at current locations

## Constraints

- **Compatibility**: Must maintain 100% backward compatibility with existing resume agent workflows
- **Performance**: Observability system must add <5% overhead to agent operations
- **Complexity**: Directory structure must be understandable to new developers within 15 minutes
- **Isolation**: Changes to one app must never require changes to other apps
- **Data Access**: All apps must use absolute paths when accessing shared root directories

