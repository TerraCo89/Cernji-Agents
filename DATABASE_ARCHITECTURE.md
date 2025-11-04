# Database Architecture

> **Related Issue**: [DEV-53 - Database architecture consolidation and cleanup](https://linear.app/the-cernjis/issue/DEV-53)

## Overview

This document defines the standard database architecture for the Cernji-Agents monorepo. Following these standards ensures clear separation of concerns, prevents configuration conflicts, and makes individual apps easier to deploy and maintain.

## Architecture Pattern

### App-Specific Databases

Each app owns its data independently following this pattern:

```
apps/{app-name}/data/{app-name}.db
```

**Benefits:**
- ✅ Clear separation of concerns
- ✅ Each app owns its data independently
- ✅ Easier to deploy/containerize individual apps
- ✅ No coupling between different agents
- ✅ Prevents configuration conflicts (like DEV-52 vocabulary table issue)

### Shared Databases (Exceptions)

Some databases are intentionally shared across apps:

```
data/events.db  # Observability server - cross-app event tracking
```

These are explicitly documented as shared resources and managed centrally.

## Current Database Inventory

### Resume Agent

**Location**: `apps/resume-agent/data/resume_agent.db`

**Purpose**: Career application data (job analyses, tailored resumes, cover letters, portfolio examples)

**MCP Configuration** (`.mcp.json`):
```json
{
  "mcpServers": {
    "sqlite-resume": {
      "type": "stdio",
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "mcp-sqlite",
        "apps\\resume-agent\\data\\resume_agent.db"
      ]
    }
  }
}
```

**Code Reference**: `apps/resume-agent/resume_agent.py:88`
```python
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"  # App-specific database (DEV-53)
```

### Japanese Tutor

**Location**: `apps/japanese-tutor/src/data/japanese_agent.db`

**Purpose**: Japanese learning data (vocabulary, flashcards, reviews, screenshots, OCR results)

**MCP Configuration** (`.mcp.json`):
```json
{
  "mcpServers": {
    "sqlite-japanese": {
      "type": "stdio",
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "mcp-sqlite",
        "apps\\japanese-tutor\\src\\data\\japanese_agent.db"
      ]
    }
  }
}
```

**Code Reference**: `apps/japanese-tutor/src/japanese_agent/database/connection.py:31`
```python
# Default to app-specific database (DEV-53)
# Path relative to src/japanese_agent/database/ directory
# ../../data/japanese_agent.db resolves to apps/japanese-tutor/src/data/japanese_agent.db
db_path = os.getenv("DATABASE_PATH", "../../data/japanese_agent.db")
```

### Resume Agent LangGraph

**Location**: `apps/resume-agent-langgraph/data/resume_agent.db`

**Purpose**: LangGraph experimental agent data (checkpoints, conversation state)

**Status**: Development/experimental - evaluating LangGraph for production use

### Observability Server

**Location**: `data/events.db` (shared, intentional)

**Purpose**: Cross-app event tracking and observability

**Why Shared**: Centralized event collection requires a single database accessible by all apps

**Code Reference**: `apps/observability-server/src/db.ts:9`
```typescript
const dbPath = join(import.meta.dir, '../../../data/events.db');
```

## Implementation Guide

### Creating a New App with Database

1. **Create app directory structure**:
   ```bash
   mkdir -p apps/my-new-app/data
   ```

2. **Set database path in code**:
   ```python
   from pathlib import Path

   APP_DIR = Path(__file__).resolve().parent
   DATA_DIR = APP_DIR / "data"
   DB_PATH = DATA_DIR / "my_new_app.db"
   ```

3. **Configure MCP server** (if applicable):
   ```json
   {
     "mcpServers": {
       "sqlite-my-app": {
         "type": "stdio",
         "command": "cmd",
         "args": [
           "/c",
           "npx",
           "-y",
           "mcp-sqlite",
           "apps\\my-new-app\\data\\my_new_app.db"
         ]
       }
     }
   }
   ```

4. **Document database location** in app's README/CLAUDE.md

### Migrating Existing Root-Level Databases

If you have a database at `data/{app-name}.db` that needs migration:

1. **Ensure Claude Desktop/MCP servers are stopped** (databases may be locked)

2. **Move database to app-specific location**:
   ```powershell
   # Create app data directory
   mkdir apps/my-app/data -Force

   # Move database
   Move-Item data/my_app.db apps/my-app/data/my_app.db
   ```

3. **Update code references**:
   ```python
   # Before (DEV-53 migration)
   DATA_DIR = PROJECT_ROOT / "data"

   # After (DEV-53 compliant)
   APP_DIR = Path(__file__).resolve().parent
   DATA_DIR = APP_DIR / "data"
   ```

4. **Update MCP configuration** (`.mcp.json`)

5. **Update documentation** (README.md, CLAUDE.md)

6. **Run validation script**:
   ```bash
   python scripts/validate-database-locations.py
   ```

## MCP Configuration Patterns

### Root-Level `.mcp.json`

For apps used from the repository root:

```json
{
  "mcpServers": {
    "sqlite-my-app": {
      "type": "stdio",
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "mcp-sqlite",
        "apps\\my-app\\data\\my_app.db"
      ]
    }
  }
}
```

### App-Level `.mcp.json`

For apps with their own MCP configuration:

```json
{
  "mcpServers": {
    "sqlite": {
      "type": "stdio",
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "mcp-sqlite",
        "data\\my_app.db"
      ],
      "env": {
        "cwd": "D:\\source\\Cernji-Agents\\apps\\my-app"
      }
    }
  }
}
```

## Validation

### Automated Validation Script

**Location**: `scripts/validate-database-locations.py`

**Run validation**:
```bash
python scripts/validate-database-locations.py
```

**Checks performed**:
1. ✅ Detects orphaned databases at root level (except `data/events.db`)
2. ✅ Verifies app-specific databases exist at correct locations
3. ✅ Validates MCP configurations point to correct paths
4. ✅ Identifies apps without initialized databases

**Example output**:
```
Database Architecture Validation (DEV-53)

1. Checking for orphaned databases at root level...
✓ No orphaned databases found

2. Validating app-specific database locations...
✓ resume-agent: Database found at apps/resume-agent/data/resume_agent.db
✓ japanese-tutor: Database found at apps/japanese-tutor/src/data/japanese_agent.db

3. Validating MCP configurations...
✓ MCP configurations are correct

============================================================
✓ All validations passed!
ℹ Database architecture follows DEV-53 standards.
```

### Manual Validation

1. **Find all databases**:
   ```powershell
   Get-ChildItem -Path . -Recurse -Filter *.db | Select-Object FullName
   ```

2. **Check for orphaned databases**:
   ```powershell
   Get-ChildItem -Path data -Filter *.db
   # Should only show events.db and backup files
   ```

3. **Verify MCP configurations**:
   ```bash
   # Check root .mcp.json
   cat .mcp.json | grep -A5 "sqlite-"

   # Check app-level configs
   cat apps/*/. mcp.json | grep -A5 "sqlite"
   ```

## Troubleshooting

### Database Locked Error

**Cause**: The database file is being accessed by another process (MCP server, SQLite connection, etc.)

**Solution**:
1. Stop Claude Desktop (closes MCP servers)
2. Close any SQLite clients/tools
3. Perform migration
4. Restart Claude Desktop

### MCP Server Can't Find Database

**Symptom**: MCP tools return "database not found" errors

**Solution**:
1. Check MCP configuration in `.mcp.json`
2. Verify path uses `\\` (Windows) or `/` (Unix)
3. Ensure path is relative to repository root (for root `.mcp.json`)
4. Run validation script: `python scripts/validate-database-locations.py`

### App Uses Wrong Database

**Symptom**: App creates new empty database instead of using existing one

**Solution**:
1. Check `DATA_DIR` or `DB_PATH` in app code
2. Verify environment variables (e.g., `DATABASE_PATH`, `SQLITE_DATABASE_PATH`)
3. Check if app uses relative paths correctly
4. Ensure database file exists at expected location

## Migration History

### DEV-53 (2025-11-04): Database Architecture Consolidation

**Changes**:
- Migrated `data/resume_agent.db` → `apps/resume-agent/data/resume_agent.db`
- Verified `apps/japanese-tutor/src/data/japanese_agent.db` at correct location
- Deleted orphaned `data/japanese_agent.db` (created by misconfigured MCP)
- Updated all code references to use app-specific paths
- Updated MCP configurations in `.mcp.json`
- Created validation script `scripts/validate-database-locations.py`

**Root Cause**: Inconsistent database locations caused confusion and led to DEV-52 vocabulary table issue

**Prevention**: Validation script added to detect orphaned databases and incorrect MCP configurations

## Best Practices

1. **Always use app-specific databases** unless there's a documented reason to share
2. **Run validation script** after database changes: `python scripts/validate-database-locations.py`
3. **Document database location** in app's CLAUDE.md and README
4. **Use environment variables** for configurability (with sensible defaults)
5. **Create backups before migration**: `Copy-Item db.db db_backup_YYYYMMDD.db`
6. **Update MCP configurations** when moving databases
7. **Add DEV-53 reference in comments** when setting database paths

## References

- **Linear Issue**: [DEV-53 - Database architecture consolidation and cleanup](https://linear.app/the-cernjis/issue/DEV-53)
- **Related Issue**: [DEV-52 - Vocabulary table not found (root cause)](https://linear.app/the-cernjis/issue/DEV-52)
- **Validation Script**: `scripts/validate-database-locations.py`
- **Constitution**: `.specify/memory/constitution.md` (Multi-App Isolation principle)

## Contributing

When adding a new app or modifying database locations:

1. ✅ Follow app-specific database pattern: `apps/{app-name}/data/{app-name}.db`
2. ✅ Update MCP configuration if applicable
3. ✅ Document database location in app's CLAUDE.md
4. ✅ Run validation script and fix any issues
5. ✅ Include DEV-53 reference in code comments
6. ✅ Update this document if adding new patterns or exceptions

## License

See repository root for license information.
