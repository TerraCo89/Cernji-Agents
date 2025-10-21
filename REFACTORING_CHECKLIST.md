# Multi-App Refactoring Checklist

## Phase 1: Resume Agent Migration

### Directory Setup
- [x] Create `apps/resume-agent/` directory structure
- [x] Create `apps/resume-agent/.claude/agents/` directory
- [x] Create `apps/resume-agent/.claude/commands/` directory

### File Migration
- [x] Copy `resume_agent.py` → `apps/resume-agent/resume_agent.py`
- [x] Copy all `.claude/agents/*.md` → `apps/resume-agent/.claude/agents/`
- [x] Copy `.claude/commands/career/` → `apps/resume-agent/.claude/commands/`

### Code Updates
- [x] Update `PROJECT_ROOT` path in `resume_agent.py` to point to repo root
- [x] Update `APP_ROOT` to reference `apps/resume-agent/`
- [x] Update `DATA_DIR` to point to root `data/` directory
- [x] Update `RESUMES_DIR` to point to root `resumes/` directory
- [x] Update `APPLICATIONS_DIR` to point to root `job-applications/` directory
- [x] Update SQLite database path to use `DATA_DIR`

### Configuration
- [x] Update `.mcp.json` to point to `apps/resume-agent/resume_agent.py`
- [x] Create `apps/resume-agent/README.md` with setup instructions
- [x] Create `apps/resume-agent/.env.example` with configuration template

### Testing
- [ ] Test MCP server starts from new location
- [ ] Test slash commands work from new location
- [ ] Test database connections work
- [ ] Test file paths resolve correctly
- [ ] Verify all MCP tools function properly

---

## Phase 2: Observability Server Setup (TypeScript/Bun)

### Directory Setup
- [x] Create `apps/observability-server/` directory
- [x] Create `apps/observability-server/src/` directory

### File Migration
- [x] Copy `src/index.ts` from Disler's repo
- [x] Copy `src/db.ts` from Disler's repo
- [x] Copy `src/types.ts` from Disler's repo
- [x] Copy `src/theme.ts` from Disler's repo (if exists)
- [x] Copy `package.json` from Disler's repo
- [x] Copy `tsconfig.json` from Disler's repo

### Code Updates
- [x] Update database path in `db.ts` to `../../data/events.db`
- [x] Add path import to `db.ts` for proper path resolution

### Documentation
- [x] Create `apps/observability-server/README.md`
- [x] Create `apps/observability-server/CLAUDE.md`

### Testing
- [ ] Run `bun install` in observability-server directory
- [ ] Test server starts on port 4000
- [ ] Test POST /events endpoint accepts events
- [ ] Test GET /events/recent returns events
- [ ] Test WebSocket /stream connection works
- [ ] Verify database creates at `data/events.db`

---

## Phase 3: Web Client Setup (Vue 3)

### Directory Setup
- [x] Copy entire `apps/client/` directory from Disler's repo

### Configuration Updates
- [ ] Review and update `apps/client/.env.sample`
- [ ] Update API endpoint URLs if needed
- [ ] Update WebSocket endpoint if needed
- [ ] Verify Vite port configuration (5173)

### Documentation
- [ ] Review `apps/client/README.md`
- [ ] Update README with any ResumeAgent-specific changes
- [ ] Document relationship with observability-server

### Testing
- [ ] Run `bun install` in client directory
- [ ] Test `bun run dev` starts Vite server
- [ ] Test client connects to observability-server
- [ ] Test WebSocket connection establishes
- [ ] Test event display in UI
- [ ] Test filtering functionality
- [ ] Test live updates when events arrive

---

## Phase 4: Translation Teacher Agent

### Directory Setup
- [ ] Create `apps/translation-teacher/` directory
- [ ] Create `apps/translation-teacher/.claude/` directory
- [ ] Create `apps/translation-teacher/.claude/agents/` directory
- [ ] Create `apps/translation-teacher/.claude/commands/translate/` directory

### Agent Definitions
- [ ] Create translation-specific agents in `.claude/agents/`
  - [ ] `translation-teacher.md` - Main teaching agent
  - [ ] `vocabulary-builder.md` - Vocabulary management
  - [ ] `grammar-explainer.md` - Grammar explanations
  - [ ] `conversation-partner.md` - Practice conversations

### Slash Commands
- [ ] Create `/translate:*` commands in `.claude/commands/translate/`
  - [ ] `lesson.md` - Start a new lesson
  - [ ] `practice.md` - Practice session
  - [ ] `vocabulary.md` - Vocabulary review
  - [ ] `correct.md` - Correction and feedback
  - [ ] `progress.md` - Track learning progress

### Documentation
- [ ] Create `apps/translation-teacher/README.md`
- [ ] Create `apps/translation-teacher/.env.example`
- [ ] Document learning workflow
- [ ] Document slash command usage

### Data Storage
- [ ] Define data structure for learning progress
- [ ] Create vocabulary database schema
- [ ] Create progress tracking schema

---

## Phase 5: Root-Level Observability Hooks

### Directory Setup
- [ ] Create root `.claude/hooks/` directory (if not exists)
- [ ] Backup existing `.claude/` directory contents

### Hook Scripts Migration
- [ ] Copy `send_event.py` from Disler's repo
- [ ] Copy other hook scripts from Disler's repo:
  - [ ] `pre_tool_use.py`
  - [ ] `post_tool_use.py`
  - [ ] `user_prompt_submit.py`
  - [ ] `notification.py`
  - [ ] `stop.py`
  - [ ] `subagent_stop.py`
  - [ ] `pre_compact.py`
  - [ ] `session_start.py`
  - [ ] `session_end.py`

### Configuration
- [ ] Create/update root `.claude/settings.json` with hooks
- [ ] Configure `--source-app` flags for each app:
  - [ ] `resume-agent`
  - [ ] `translation-teacher`
  - [ ] `observability-server`
  - [ ] `client`
- [ ] Set up hook matchers if needed
- [ ] Configure AI summarization flags (`--summarize`)

### Hook Customization
- [ ] Update `send_event.py` to use correct server URL (localhost:4000)
- [ ] Verify hook scripts have proper Python dependencies
- [ ] Test hook scripts work with UV

### Testing
- [ ] Test PreToolUse hook fires and sends events
- [ ] Test PostToolUse hook fires and sends events
- [ ] Test UserPromptSubmit hook fires
- [ ] Verify events appear in observability-server
- [ ] Verify events display in web client
- [ ] Test with multiple concurrent sessions

---

## Phase 6: System Management Scripts

### Script Creation
- [ ] Create `scripts/start-system.sh`
  - [ ] Start observability-server
  - [ ] Start web client
  - [ ] Display startup status
  - [ ] Display URLs for access
  - [ ] Instructions for MCP servers
- [ ] Create `scripts/stop-system.sh`
  - [ ] Stop observability-server
  - [ ] Stop web client
  - [ ] Kill any background processes
  - [ ] Display shutdown status
- [ ] Create `scripts/reset-observability.sh`
  - [ ] Stop all services
  - [ ] Delete events database
  - [ ] Restart services
  - [ ] Confirm reset complete

### Windows Compatibility
- [ ] Create `scripts/start-system.bat` (Windows equivalent)
- [ ] Create `scripts/stop-system.bat` (Windows equivalent)
- [ ] Create `scripts/reset-observability.bat` (Windows equivalent)

### Script Testing
- [ ] Test start-system script
- [ ] Test stop-system script
- [ ] Test reset-observability script
- [ ] Verify all processes start correctly
- [ ] Verify all processes stop cleanly

---

## Phase 7: Documentation Updates

### Root README
- [ ] Update `README.md` with new multi-app architecture
- [ ] Add overview of all apps
- [ ] Add quick start instructions
- [ ] Add system startup instructions
- [ ] Update project structure diagram
- [ ] Add links to individual app READMEs

### Root CLAUDE.md
- [ ] Update `CLAUDE.md` with new structure
- [ ] Update file paths to reflect new locations
- [ ] Document multi-app organization
- [ ] Update architecture diagrams
- [ ] Add observability system documentation
- [ ] Update development workflow

### App Documentation
- [ ] Create `app_docs/` directory
- [ ] Create workflow documentation:
  - [ ] `app_docs/resume_workflow.md`
  - [ ] `app_docs/translation_workflow.md`
  - [ ] `app_docs/observability_workflow.md`
- [ ] Create integration documentation:
  - [ ] `app_docs/hook_integration.md`
  - [ ] `app_docs/mcp_integration.md`

### Specifications
- [ ] Create `specs/` directory
- [ ] Create feature specifications:
  - [ ] `specs/multi_app_architecture.md`
  - [ ] `specs/observability_system.md`
  - [ ] `specs/translation_teacher.md`

### Migration Guide
- [ ] Create `MIGRATION_GUIDE.md`
- [ ] Document breaking changes
- [ ] Document path updates needed
- [ ] Document configuration changes
- [ ] Add troubleshooting section

---

## Phase 8: Testing & Validation

### Unit Testing
- [ ] Test resume-agent MCP tools individually
- [ ] Test observability-server endpoints
- [ ] Test web client components
- [ ] Test hook scripts

### Integration Testing
- [ ] Test full resume application workflow
- [ ] Test event flow: hooks → server → client
- [ ] Test multi-session support
- [ ] Test concurrent agent operations
- [ ] Test database operations under load

### End-to-End Testing
- [ ] Start entire system with start-system script
- [ ] Submit a resume application
- [ ] Verify events appear in client
- [ ] Verify data persists correctly
- [ ] Stop system cleanly with stop-system script

### Performance Testing
- [ ] Test with high event volume
- [ ] Test WebSocket connection stability
- [ ] Test database performance
- [ ] Test client rendering performance

---

## Phase 9: Cleanup & Optimization

### File Cleanup
- [ ] Remove old `resume_agent.py` from root (after verification)
- [ ] Remove old `.claude/agents/` from root (if fully migrated)
- [ ] Remove old `.claude/commands/career/` from root (if fully migrated)
- [ ] Clean up temporary files
- [ ] Remove reference repo: `temp-observability-reference/`

### Configuration Cleanup
- [ ] Remove unused environment variables
- [ ] Consolidate duplicate configurations
- [ ] Update gitignore for new structure
- [ ] Clean up old MCP configurations

### Optimization
- [ ] Optimize database queries
- [ ] Optimize WebSocket message size
- [ ] Optimize client bundle size
- [ ] Review and optimize hook execution time

---

## Phase 10: Production Readiness

### Security
- [ ] Review and secure API endpoints
- [ ] Add authentication if needed
- [ ] Review CORS configuration
- [ ] Secure WebSocket connections
- [ ] Review environment variable handling

### Monitoring
- [ ] Add error logging to all apps
- [ ] Add performance monitoring
- [ ] Add health check endpoints
- [ ] Set up alerting (optional)

### Deployment
- [ ] Document deployment process
- [ ] Create deployment scripts
- [ ] Document environment setup
- [ ] Create backup/restore procedures

### Documentation
- [ ] Final review of all READMEs
- [ ] Update all CLAUDE.md files
- [ ] Create troubleshooting guide
- [ ] Create FAQ document

---

## Summary

### Completed
- ✅ Phase 1: Resume Agent Migration (files migrated, code updated, docs created)
- ✅ Phase 2: Observability Server (files copied, paths updated, docs created)
- ✅ Phase 3: Web Client (directory copied)

### In Progress
- 🔄 Phase 3: Web Client (testing pending)

### Pending
- ⏳ Phase 4: Translation Teacher Agent
- ⏳ Phase 5: Root-Level Observability Hooks
- ⏳ Phase 6: System Management Scripts
- ⏳ Phase 7: Documentation Updates
- ⏳ Phase 8: Testing & Validation
- ⏳ Phase 9: Cleanup & Optimization
- ⏳ Phase 10: Production Readiness

---

## Next Steps

1. **Immediate**: Test Phase 1 (resume-agent in new location)
2. **Next**: Test Phase 2 (observability-server functionality)
3. **Then**: Test Phase 3 (web client integration)
4. **After**: Complete Phase 4 (translation-teacher skeleton)
5. **Continue**: Phases 5-10 in sequence

---

**Last Updated**: 2025-10-21
**Status**: Phase 3 completed, testing pending for Phases 1-3
