# Phase 1 Data Model: Multi-App Architecture Refactoring

**Feature**: Multi-App Architecture Refactoring
**Date**: 2025-10-21
**Status**: Complete

## Overview

This feature introduces a new observability event system while maintaining existing resume-agent data structures. The primary new entity is the **Event** (observability events), stored in a new database (`data/events.db`). All existing resume-agent data structures remain unchanged.

---

## Entity: Event (Observability)

**Purpose**: Capture agent activity (tool calls, prompts, session events) for real-time monitoring and debugging.

**Storage**: SQLite database at `data/events.db`

### Schema (TypeScript)

```typescript
interface Event {
  id: number;                    // Primary key (auto-increment)
  timestamp: string;             // ISO 8601 timestamp
  source_app: string;            // "resume-agent", "translation-teacher", "observability-server", "client"
  event_type: EventType;         // "PreToolUse" | "PostToolUse" | "UserPromptSubmit" | "SessionStart" | "SessionEnd" | "Notification" | "Stop" | "SubagentStop" | "PreCompact"
  tool_name?: string;            // Tool/function name (optional, for tool events)
  summary?: string;              // AI-generated or manual summary
  session_id?: string;           // UUID for grouping related events
  metadata?: string;             // JSON blob for additional context
  created_at: string;            // Database insert timestamp (auto)
}

enum EventType {
  PreToolUse = "PreToolUse",
  PostToolUse = "PostToolUse",
  UserPromptSubmit = "UserPromptSubmit",
  SessionStart = "SessionStart",
  SessionEnd = "SessionEnd",
  Notification = "Notification",
  Stop = "Stop",
  SubagentStop = "SubagentStop",
  PreCompact = "PreCompact"
}
```

### Database Schema (SQL)

```sql
CREATE TABLE events (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp       TEXT NOT NULL,              -- ISO 8601 format (e.g., "2025-10-21T10:30:45.123Z")
  source_app      TEXT NOT NULL,              -- Application identifier
  event_type      TEXT NOT NULL,              -- Event type enum value
  tool_name       TEXT,                       -- Optional: tool name for tool events
  summary         TEXT,                       -- Optional: human-readable summary
  session_id      TEXT,                       -- Optional: UUID for session grouping
  metadata        TEXT,                       -- Optional: JSON string with additional data
  created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common query patterns
CREATE INDEX idx_events_source_app ON events(source_app);
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_events_session ON events(session_id);
CREATE INDEX idx_events_type ON events(event_type);
```

### Validation Rules

1. **timestamp**: REQUIRED, must be valid ISO 8601 string
2. **source_app**: REQUIRED, non-empty string (validated against known apps)
3. **event_type**: REQUIRED, must be one of EventType enum values
4. **tool_name**: OPTIONAL, if provided must be non-empty string
5. **summary**: OPTIONAL, max length 1000 characters
6. **session_id**: OPTIONAL, if provided must be valid UUID v4 format
7. **metadata**: OPTIONAL, if provided must be valid JSON string

### Relationships

- **No foreign keys**: Events are append-only, self-contained records
- **Implicit relationship via session_id**: Events with same session_id are part of the same session
- **Implicit relationship via source_app**: Events can be filtered/grouped by application

### State Lifecycle

Events are **immutable** after creation (append-only log):

```
[Created] → [Stored] → [Broadcasted via WebSocket] → [Displayed in Dashboard]
                    ↓
            (Never Updated or Deleted in normal operation)
```

Cleanup: Optional manual deletion of old events (future: auto-delete events older than 30 days).

---

## Entity: Application (Metadata)

**Purpose**: Represent each application in the multi-app monorepo.

**Storage**: In-memory / filesystem (no database table)

### Structure (Conceptual)

```typescript
interface Application {
  name: string;                  // "resume-agent", "observability-server", "client", "translation-teacher"
  path: string;                  // Relative path from repo root (e.g., "apps/resume-agent")
  language: string;              // "Python", "TypeScript", "Vue 3"
  entry_point: string;           // Main file (e.g., "resume_agent.py", "src/index.ts")
  dependencies_file: string;     // "package.json", "pyproject.toml", or "inline (PEP 723)"
  has_claude_config: boolean;    // Whether .claude/ directory exists
  has_mcp_server: boolean;       // Whether app exposes MCP server
}
```

### Example Instances

```typescript
const applications: Application[] = [
  {
    name: "resume-agent",
    path: "apps/resume-agent",
    language: "Python",
    entry_point: "resume_agent.py",
    dependencies_file: "inline (PEP 723)",
    has_claude_config: true,
    has_mcp_server: true
  },
  {
    name: "observability-server",
    path: "apps/observability-server",
    language: "TypeScript",
    entry_point: "src/index.ts",
    dependencies_file: "package.json",
    has_claude_config: true,
    has_mcp_server: false
  },
  {
    name: "client",
    path: "apps/client",
    language: "Vue 3",
    entry_point: "src/App.vue",
    dependencies_file: "package.json",
    has_claude_config: false,
    has_mcp_server: false
  }
];
```

### Validation Rules

1. **name**: REQUIRED, unique, lowercase-with-hyphens
2. **path**: REQUIRED, must exist in filesystem
3. **entry_point**: REQUIRED, file must exist at `{path}/{entry_point}`
4. **has_claude_config**: If true, `{path}/.claude/` directory must exist

### Relationships

- **One-to-Many with Events**: One application produces many events (via source_app field)

---

## Entity: HookConfiguration (Root-Level Hooks)

**Purpose**: Define which hooks send events to observability-server.

**Storage**: JSON configuration file at `.claude/settings.json`

### Structure (JSON Schema)

```typescript
interface HookConfiguration {
  hooks: {
    [hookType: string]: HookDefinition[];
  };
}

interface HookDefinition {
  matcher: string;                // Pattern to match (empty = all)
  hooks: HookScript[];
}

interface HookScript {
  type: "command";               // Only "command" type supported
  command: string;               // Shell command to execute
}
```

### Example Configuration

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
    }],
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "uv run .claude/hooks/send_event.py --source-app resume-agent --event-type UserPromptSubmit"
      }]
    }]
  }
}
```

### Validation Rules

1. **hooks**: REQUIRED, object with hook type keys
2. **matcher**: REQUIRED (can be empty string for "match all")
3. **type**: REQUIRED, must be "command"
4. **command**: REQUIRED, non-empty string, executable must exist

### Relationships

- **Triggers Events**: Hook commands create Event records in database
- **Per-Application**: Different apps can have different hook configurations (though root-level is shared)

---

## Existing Entities (Unchanged)

The following entities from resume-agent remain **unchanged**:

### Resume-Agent Data (Existing)

```python
# Pydantic models (in resume_agent.py)
class PersonalInfo(BaseModel):
    name: str
    email: str
    # ... existing fields

class Employment(BaseModel):
    company: str
    title: str
    # ... existing fields

class MasterResume(BaseModel):
    personal_info: PersonalInfo
    employment: list[Employment]
    # ... existing fields

class CareerHistory(BaseModel):
    employment: list[Employment]
    # ... existing fields

class JobAnalysis(BaseModel):
    company: str
    job_title: str
    # ... existing fields
```

**Storage**:
- `data/resume_agent.db` (SQLite)
- `resumes/*.yaml` (YAML files)

**No Changes Required**: Resume-agent data model is complete and validated. This refactoring only changes file locations, not data structures.

---

## Data Migration

### New Databases

1. **Create `data/events.db`**: New SQLite database for observability events
   ```sql
   -- Run on first startup of observability-server
   CREATE TABLE events (...);  -- See schema above
   CREATE INDEX ...;
   ```

### Existing Databases

2. **`data/resume_agent.db`**: No changes required, database stays at root level
3. **`resumes/*.yaml`**: No changes required, YAML files stay at root level
4. **`job-applications/`**: No changes required, output directory stays at root level

### Migration Script

**Not needed** - This is a code reorganization, not a data migration. All existing data stays in place.

---

## Query Patterns

### Common Event Queries

```sql
-- Recent events across all apps
SELECT * FROM events
ORDER BY timestamp DESC
LIMIT 50;

-- Events from specific app
SELECT * FROM events
WHERE source_app = 'resume-agent'
ORDER BY timestamp DESC;

-- Events in a session
SELECT * FROM events
WHERE session_id = 'uuid-here'
ORDER BY timestamp ASC;

-- Events by type
SELECT * FROM events
WHERE event_type = 'PreToolUse'
ORDER BY timestamp DESC;

-- Event count by app (for dashboard stats)
SELECT source_app, COUNT(*) as count
FROM events
GROUP BY source_app;
```

### Performance Considerations

- **Indexes**: All common query patterns are indexed (source_app, timestamp, session_id, event_type)
- **No JOINs**: Single table, no complex queries
- **Append-only**: Writes are fast (no updates, no deletes)
- **WAL Mode**: Enable Write-Ahead Logging for better concurrent access

---

## Data Validation

### Event Validation (TypeScript)

```typescript
// In observability-server/src/types.ts
import { z } from 'zod';

const EventSchema = z.object({
  timestamp: z.string().datetime(),
  source_app: z.string().min(1),
  event_type: z.enum([
    "PreToolUse", "PostToolUse", "UserPromptSubmit",
    "SessionStart", "SessionEnd", "Notification",
    "Stop", "SubagentStop", "PreCompact"
  ]),
  tool_name: z.string().optional(),
  summary: z.string().max(1000).optional(),
  session_id: z.string().uuid().optional(),
  metadata: z.string().optional(), // JSON string
});

// Validation function
function validateEvent(data: unknown): Event {
  return EventSchema.parse(data);
}
```

### Hook Configuration Validation

```typescript
// Validate .claude/settings.json on startup
const HookConfigSchema = z.object({
  hooks: z.record(z.array(z.object({
    matcher: z.string(),
    hooks: z.array(z.object({
      type: z.literal("command"),
      command: z.string().min(1)
    }))
  })))
});
```

---

## Summary

**New Entities**:
- ✅ Event (observability events) - SQLite database `data/events.db`
- ✅ Application (metadata) - In-memory/filesystem
- ✅ HookConfiguration - JSON file `.claude/settings.json`

**Unchanged Entities**:
- ✅ Resume-agent data structures (PersonalInfo, Employment, MasterResume, etc.)
- ✅ Resume-agent databases (`data/resume_agent.db`)
- ✅ YAML files (`resumes/*.yaml`)

**Data Migration**:
- ✅ None required - pure code reorganization
- ✅ New database created on first observability-server startup

**Validation**:
- ✅ TypeScript with Zod for event validation
- ✅ Pydantic for resume-agent data (existing)

**Ready for Phase 1 Contracts**: Data model complete, proceed to API contract generation.
