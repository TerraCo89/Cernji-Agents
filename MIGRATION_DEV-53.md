# DEV-53 Database Migration Instructions

> **Status**: Code changes complete, manual database file migration required

## Background

Issue DEV-53 standardizes database locations to use app-specific paths. All code changes and MCP configurations have been updated, but the actual database files are currently locked by running MCP servers and could not be moved automatically.

## ⚠️ Prerequisites

**IMPORTANT**: Before starting, you must:
1. **Close Claude Desktop** (this stops all MCP servers and releases database locks)
2. **Close any SQLite clients** (DB Browser, sqlite3 CLI, etc.)
3. **Verify no processes are using the databases**

## Migration Steps

### Step 1: Close Claude Desktop

Close Claude Desktop completely to stop all MCP servers and release database file locks.

### Step 2: Move Database Files

Run these PowerShell commands from the repository root:

```powershell
# Move resume-agent database to app-specific location
Move-Item data\resume_agent.db apps\resume-agent\data\resume_agent.db -Force

# Delete orphaned japanese-agent database (app already uses correct location)
Remove-Item data\japanese_agent.db -Force
```

### Step 3: Verify Migration

Run the validation script to ensure all databases are in the correct locations:

```bash
python scripts/validate-database-locations.py
```

Expected output:
```
Database Architecture Validation (DEV-53)

1. Checking for orphaned databases at root level...
[OK] No orphaned databases found

2. Validating app-specific database locations...
[OK] resume-agent: Database found at apps/resume-agent/data/resume_agent.db
[OK] japanese-tutor: Database found at apps/japanese-tutor/src/data/japanese_agent.db
[OK] resume-agent-langgraph: Database found at apps/resume-agent-langgraph/data/resume_agent.db

3. Validating MCP configurations...
[OK] MCP configurations are correct

============================================================
[OK] All validations passed!
[INFO] Database architecture follows DEV-53 standards.
```

### Step 4: Test Applications

#### Test Resume Agent

```bash
# Start the resume agent MCP server
uv run apps/resume-agent/resume_agent.py
```

Then in a new terminal:
```bash
# Check database connection
python -c "import sqlite3; conn = sqlite3.connect('apps/resume-agent/data/resume_agent.db'); print(f'Tables: {[row[0] for row in conn.execute(\"SELECT name FROM sqlite_master WHERE type=\\'table\\'\").fetchall()]}'); conn.close()"
```

Expected: Should list all tables (personal_info, job_applications, etc.)

#### Test Japanese Tutor

```bash
# Check database connection
python -c "import sqlite3; conn = sqlite3.connect('apps/japanese-tutor/src/data/japanese_agent.db'); print(f'Tables: {[row[0] for row in conn.execute(\"SELECT name FROM sqlite_master WHERE type=\\'table\\'\").fetchall()]}'); conn.close()"
```

Expected: Should list all tables (vocabulary, flashcards, screenshots, etc.)

### Step 5: Restart Claude Desktop

1. Restart Claude Desktop
2. MCP servers will now use the app-specific database paths
3. All tools should work as before

## Verification Checklist

- [ ] Claude Desktop is closed
- [ ] `data/resume_agent.db` moved to `apps/resume-agent/data/resume_agent.db`
- [ ] `data/japanese_agent.db` deleted (orphaned)
- [ ] Validation script passes
- [ ] Resume-agent database is accessible
- [ ] Japanese-tutor database is accessible
- [ ] Claude Desktop restarted
- [ ] MCP tools work correctly

## Rollback (If Needed)

If you encounter issues and need to rollback:

1. **Restore database from backup**:
   ```powershell
   Copy-Item data\resume_agent_backup_20251104.db data\resume_agent.db -Force
   ```

2. **Revert code changes**:
   ```bash
   git checkout master
   git branch -D kris/dev-53-database-architecture-consolidation-and-cleanup
   ```

3. **Restart Claude Desktop**

## Changes Made (Summary)

### Code Changes
- `apps/resume-agent/resume_agent.py:88` - Updated `DATA_DIR` to use app-specific path
- `apps/resume-agent/scripts/*.py` - Updated database paths
- `apps/japanese-tutor/config.yaml:19` - Updated database path documentation
- `apps/japanese-tutor/src/japanese_agent/database/connection.py:31` - Added DEV-53 comment

### MCP Configuration Changes
- `.mcp.json` - Updated `sqlite-resume` to point to `apps\resume-agent\data\resume_agent.db`
- `apps/resume-agent/.mcp.json` - Updated working directory for app-level MCP config

### Documentation
- `DATABASE_ARCHITECTURE.md` - New comprehensive database architecture documentation
- `CLAUDE.md` - Added database architecture section
- `scripts/validate-database-locations.py` - New validation script

### Backups Created
- `data/resume_agent_backup_20251104.db` - Backup of resume-agent database before migration

## Troubleshooting

### Database Still Locked

**Error**: "The process cannot access the file because it is being used by another process"

**Solutions**:
1. Ensure Claude Desktop is completely closed (check Task Manager)
2. Close any SQLite clients (DB Browser, DBeaver, etc.)
3. Check for zombie processes: `Get-Process | Where-Object {$_.Path -like "*mcp*"}`
4. If needed, restart your computer to release all locks

### MCP Server Can't Find Database

**Error**: MCP tools return "database not found" errors

**Solutions**:
1. Run validation script to verify database location
2. Check MCP configuration in `.mcp.json`
3. Ensure database file exists at expected location
4. Restart Claude Desktop to reload MCP configurations

### Database is Empty After Migration

**Error**: Database has no data after moving

**Solutions**:
1. Restore from backup: `Copy-Item data\resume_agent_backup_20251104.db apps\resume-agent\data\resume_agent.db -Force`
2. Verify file was moved (not copied): original should not exist at `data/resume_agent.db`
3. Check file size: should be ~1.8MB (not empty)

## Questions?

If you encounter any issues:
1. Check [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md) for detailed architecture docs
2. Review Linear issue [DEV-53](https://linear.app/the-cernjis/issue/DEV-53) for context
3. Run validation script for diagnostic information
4. Check git commit history for code changes made

## Next Steps After Migration

Once migration is complete:
1. Delete backup file (after verifying everything works): `Remove-Item data\resume_agent_backup_20251104.db`
2. Delete this migration guide (no longer needed): `Remove-Item MIGRATION_DEV-53.md`
3. Continue normal development workflow

---

**Migration prepared by**: DEV-53 automated migration
**Date**: 2025-11-04
**Branch**: `kris/dev-53-database-architecture-consolidation-and-cleanup`
