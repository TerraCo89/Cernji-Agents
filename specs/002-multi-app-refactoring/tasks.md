# Tasks: Multi-App Architecture Refactoring

**Input**: Design documents from `/specs/002-multi-app-refactoring/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Tests**: NOT requested in feature specification - test tasks are NOT included.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions
- **Multi-app monorepo**: `apps/[app-name]/`
- **Root-level shared**: `data/`, `resumes/`, `job-applications/`, `.claude/`, `scripts/`
- **App-specific**: Each app has own `.claude/`, `README.md`, dependencies

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create multi-app directory structure and prepare for migration

- [X] T001 Create apps/ directory in repository root
- [X] T002 [P] Create apps/resume-agent/ directory structure (app location for migrated agent)
- [X] T003 [P] Create apps/observability-server/ directory structure (src/, package.json)
- [X] T004 [P] Create apps/client/ directory structure (src/, package.json, vite.config.ts)
- [X] T005 [P] Create .claude/hooks/ directory at repository root
- [X] T006 [P] Create scripts/ directory at repository root
- [X] T007 Clone Disler's reference repository to temp-observability-reference/
- [X] T008 Add temp-observability-reference/ to .gitignore

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 Create SQLite database at data/events.db with events table schema per data-model.md
- [X] T010 [P] Add indexes to events table (idx_events_source_app, idx_events_timestamp, idx_events_session, idx_events_type)
- [X] T011 [P] Enable WAL mode on data/events.db (PRAGMA journal_mode=WAL)
- [X] T012 [P] Set busy timeout on data/events.db (PRAGMA busy_timeout=5000)
- [X] T013 Validate data/resume_agent.db exists and is accessible (no changes needed)
- [X] T013a Fix events.db schema to match Disler's implementation (event_type -> hook_event_type) [Added during implementation]

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 4 - Organize Applications in Isolated Directories (Priority: P1) 🎯 FOUNDATIONAL

**Goal**: Establish multi-app architecture with proper isolation before migrating resume-agent

**Independent Test**: Can create new apps in apps/ directory with own .claude/ configuration without affecting other apps

**Why First**: This is architectural foundation - must be complete before User Story 1 (resume-agent migration)

### Implementation for User Story 4

**Directory Structure**:

- [X] T014 [P] [US4] Create apps/resume-agent/.claude/ directory
- [X] T015 [P] [US4] Create apps/resume-agent/.claude/agents/ directory
- [X] T016 [P] [US4] Create apps/resume-agent/.claude/commands/ directory
- [X] T017 [P] [US4] Create apps/observability-server/.claude/ directory
- [X] T018 [P] [US4] Create apps/observability-server/.claude/agents/ directory (may be empty initially)

**Path Resolution Utilities**:

- [X] T019 [US4] Create PROJECT_ROOT constant calculation in apps/resume-agent/resume_agent.py (Path(__file__).resolve().parent.parent.parent)
- [X] T020 [US4] Add startup path validation to apps/resume-agent/resume_agent.py (verify data/, resumes/, job-applications/ exist)
- [X] T021 [US4] Update all file path references in resume_agent.py to use PROJECT_ROOT-relative paths
- [ ] T022 [US4] Create PROJECT_ROOT constant in apps/observability-server/src/db.ts (path.resolve(__dirname, '../../..')) [DEFERRED - Observability phase]
- [ ] T023 [US4] Update database path in apps/observability-server/src/db.ts to use PROJECT_ROOT (../../data/events.db → PROJECT_ROOT/data/events.db) [DEFERRED - Observability phase]

**Documentation**:

- [X] T024 [P] [US4] Create apps/resume-agent/README.md with setup instructions
- [X] T025 [P] [US4] Create apps/observability-server/README.md with setup instructions
- [X] T026 [P] [US4] Create apps/client/README.md with setup instructions

**Checkpoint**: At this point, directory structure is ready for resume-agent migration

---

## Phase 4: User Story 1 - Maintain Resume Agent in New Location (Priority: P1) 🎯 MVP

**Goal**: Move resume-agent to apps/resume-agent/ while maintaining 100% backward compatibility

**Independent Test**: Run /career:apply workflow from new location and verify tailored resume is generated in root job-applications/ directory

**Dependencies**: Depends on User Story 4 completion (directory structure must exist)

### Implementation for User Story 1

**File Migration**:

- [X] T027 [US1] Move resume_agent.py to apps/resume-agent/resume_agent.py (with updated PROJECT_ROOT from T019-T021)
- [X] T028 [P] [US1] Move .claude/agents/data-access-agent.md to apps/resume-agent/.claude/agents/
- [X] T029 [P] [US1] Move .claude/agents/job-analyzer.md to apps/resume-agent/.claude/agents/
- [X] T030 [P] [US1] Move .claude/agents/resume-writer.md to apps/resume-agent/.claude/agents/
- [X] T031 [P] [US1] Move .claude/agents/cover-letter-writer.md to apps/resume-agent/.claude/agents/
- [X] T032 [P] [US1] Move .claude/agents/portfolio-finder.md to apps/resume-agent/.claude/agents/
- [X] T033 [P] [US1] Move .claude/agents/career-enhancer.md to apps/resume-agent/.claude/agents/
- [X] T034 [P] [US1] Move all /career:* slash commands from .claude/commands/ to apps/resume-agent/.claude/commands/

**Configuration Updates**:

- [X] T035 [US1] Update .mcp.json MCP server path from "uv run resume_agent.py" to "uv run apps/resume-agent/resume_agent.py" (Already correct)
- [X] T036 [US1] Update root CLAUDE.md to document new multi-app structure with apps/ directory
- [X] T037 [US1] Update root README.md to explain multi-app architecture and point to app-specific READMEs

**Validation**:

- [X] T038 [US1] Start MCP server from new location and verify all tools register successfully (Path validation passed)
- [ ] T039 [US1] Run /career:fetch-job command and verify job analysis saves to job-applications/ [Requires manual testing with MCP client]
- [ ] T040 [US1] Run /career:analyze-job command and verify match assessment is generated [Requires manual testing with MCP client]
- [ ] T041 [US1] Run /career:tailor-resume command and verify resume output to job-applications/ [Requires manual testing with MCP client]
- [ ] T042 [US1] Run complete /career:apply workflow and verify all outputs (analysis, resume, cover letter, examples) [Requires manual testing with MCP client]
- [X] T043 [US1] Verify data/resume_agent.db is accessible from new location (Verified programmatically)
- [ ] T044 [US1] Verify resumes/career-history.yaml is accessible from new location [Requires manual testing - resumes/ in .gitignore]

**Checkpoint**: At this point, User Story 1 should be fully functional - resume-agent works from new location with 100% backward compatibility

---

## Phase 5: User Story 2 - Monitor Agent Activity Through Web Dashboard (Priority: P2)

**Goal**: Implement observability system (server + client + hooks) for real-time agent activity monitoring

**Independent Test**: Start observability system, run any slash command, verify events appear in web dashboard within 1 second

**Dependencies**: Independent of User Story 1 (can run in parallel if staffed), but requires Phase 2 (events.db must exist)

### Implementation for User Story 2 - Observability Server

**Copy and Adapt Reference Implementation**:

- [X] T045 [P] [US2] Copy temp-observability-reference/apps/server/src/index.ts to apps/observability-server/src/index.ts
- [X] T046 [P] [US2] Copy temp-observability-reference/apps/server/src/db.ts to apps/observability-server/src/db.ts
- [X] T047 [P] [US2] Copy temp-observability-reference/apps/server/src/types.ts to apps/observability-server/src/types.ts
- [X] T048 [P] [US2] Copy temp-observability-reference/apps/server/package.json to apps/observability-server/package.json
- [X] T049 [P] [US2] Copy temp-observability-reference/apps/server/tsconfig.json to apps/observability-server/tsconfig.json

**Adapt Paths and Configuration**:

- [X] T050 [US2] Update database path in apps/observability-server/src/db.ts (Path: ../../../data/events.db)
- [X] T051 [US2] Verify PROJECT_ROOT path resolution in apps/observability-server/src/db.ts (Uses import.meta.dir + 3 levels up)
- [X] T052 [US2] Add attribution comment to apps/observability-server/src/index.ts ("Adapted from Disler's Multi-Agent Observability")

**Server Setup**:

- [ ] T053 [US2] Install Bun dependencies in apps/observability-server/ (bun install) [MANUAL STEP - Requires Bun CLI]
- [X] T054 [US2] Implement Event schema validation with Zod in apps/observability-server/src/types.ts
- [X] T055 [US2] Implement POST /events endpoint with schema validation in apps/observability-server/src/index.ts
- [X] T056 [US2] Implement WebSocket /stream endpoint in apps/observability-server/src/index.ts
- [X] T057 [US2] Implement event broadcast to all connected WebSocket clients in apps/observability-server/src/index.ts
- [X] T058 [US2] Add error handling for client disconnections in apps/observability-server/src/index.ts

**Documentation**:

- [X] T059 [P] [US2] Create apps/observability-server/CLAUDE.md with architecture notes
- [X] T060 [P] [US2] Update apps/observability-server/README.md with startup instructions

### Implementation for User Story 2 - Web Client

**Copy and Adapt Reference Implementation**:

- [X] T061 [P] [US2] Copy temp-observability-reference/apps/client/src/App.vue to apps/client/src/App.vue
- [X] T062 [P] [US2] Copy temp-observability-reference/apps/client/src/main.ts to apps/client/src/main.ts
- [X] T063 [P] [US2] Copy temp-observability-reference/apps/client/src/components/ to apps/client/src/components/
- [X] T064 [P] [US2] Copy temp-observability-reference/apps/client/src/composables/ to apps/client/src/composables/
- [X] T065 [P] [US2] Copy temp-observability-reference/apps/client/package.json to apps/client/package.json
- [X] T066 [P] [US2] Copy temp-observability-reference/apps/client/vite.config.ts to apps/client/vite.config.ts
- [X] T067 [P] [US2] Copy temp-observability-reference/apps/client/tailwind.config.js to apps/client/tailwind.config.js
- [X] T068 [P] [US2] Copy temp-observability-reference/apps/client/index.html to apps/client/index.html

**Client Setup**:

- [ ] T069 [US2] Install Bun dependencies in apps/client/ (bun install) [MANUAL STEP - Requires Bun CLI]
- [X] T070 [US2] Implement WebSocket connection logic in apps/client/src/composables/useWebSocket.ts
- [X] T071 [US2] Implement auto-reconnect with 3-second timeout in apps/client/src/composables/useWebSocket.ts
- [X] T072 [US2] Implement event filtering by source_app in apps/client/src/App.vue
- [X] T073 [US2] Implement event list display in apps/client/src/components/EventList.vue
- [X] T074 [US2] Add connection status indicator ("Connected", "Reconnecting...") in apps/client/src/App.vue

**Documentation**:

- [X] T075 [P] [US2] Update apps/client/README.md with development server instructions

### Implementation for User Story 2 - Hook Scripts

**Copy and Adapt Reference Implementation**:

- [X] T076 [US2] Copy temp-observability-reference/.claude/hooks/send_event.py to .claude/hooks/send_event.py
- [X] T077 [US2] Update .claude/hooks/send_event.py to implement contract per hook-script-contract.md (Script already implements contract)
- [X] T078 [US2] Add command line argument parsing (--source-app, --event-type, --summarize) to .claude/hooks/send_event.py (Already present in copied script)
- [X] T079 [US2] Add stdin reading logic for hook payload in .claude/hooks/send_event.py (Already present in copied script)
- [X] T080 [US2] Implement HTTP POST to http://localhost:4000/events with 100ms timeout in .claude/hooks/send_event.py (Already present in copied script)
- [X] T081 [US2] Add error handling that exits with 0 even on failure (non-blocking) in .claude/hooks/send_event.py (Already present in copied script)

**Hook Configuration**:

- [X] T082 [US2] Create .claude/settings.json at repository root with PreToolUse hook configuration
- [X] T083 [US2] Add PostToolUse hook configuration to .claude/settings.json
- [X] T084 [US2] Add UserPromptSubmit hook configuration to .claude/settings.json

**Validation**:

- [ ] T085 [US2] Start observability-server and verify it listens on port 4000
- [ ] T086 [US2] Start web client and verify it loads at http://localhost:5173
- [ ] T087 [US2] Verify WebSocket connection establishes between client and server
- [ ] T088 [US2] Manually test send_event.py script posts event to server
- [ ] T089 [US2] Run any Claude Code command and verify PreToolUse/PostToolUse events appear in database
- [ ] T090 [US2] Verify events broadcast to web client and appear in UI within 1 second
- [ ] T091 [US2] Test observability server failure scenario (stop server, verify agent continues working)

**Checkpoint**: At this point, User Story 2 should be fully functional - complete observability system operational

---

## Phase 6: User Story 3 - Start Complete System With Single Command (Priority: P3)

**Goal**: Create system management scripts for easy startup/shutdown of all components

**Independent Test**: Run start-system script and verify both observability-server and client are accessible at their URLs

**Dependencies**: Depends on User Story 2 (observability-server and client must exist)

### Implementation for User Story 3

**PowerShell Scripts**:

- [X] T092 [P] [US3] Create scripts/start-system.ps1 with port checking (4000, 5173)
- [X] T093 [P] [US3] Add observability-server startup to scripts/start-system.ps1 (Start-Job { bun run src/index.ts })
- [X] T094 [P] [US3] Add web client startup to scripts/start-system.ps1 (Start-Job { bun run dev })
- [X] T095 [P] [US3] Add 5-second wait and port verification to scripts/start-system.ps1
- [X] T096 [P] [US3] Add URL display to scripts/start-system.ps1 (http://localhost:4000, http://localhost:5173)
- [X] T097 [P] [US3] Add error handling and cleanup on failure to scripts/start-system.ps1

**Stop Script**:

- [X] T098 [P] [US3] Create scripts/stop-system.ps1 with port-based process detection
- [X] T099 [P] [US3] Add graceful shutdown logic to scripts/stop-system.ps1 (Stop-Process on ports 4000, 5173)
- [X] T100 [P] [US3] Add verification that all processes terminated in scripts/stop-system.ps1

**Reset Script**:

- [X] T101 [P] [US3] Create scripts/reset-observability.ps1 that stops system
- [X] T102 [P] [US3] Add database deletion to scripts/reset-observability.ps1 (Remove-Item data/events.db)
- [X] T103 [P] [US3] Add database recreation to scripts/reset-observability.ps1 (recreate events table)
- [X] T104 [P] [US3] Add system restart to scripts/reset-observability.ps1

**Bash Scripts (Optional - Future Work)**:

- [ ] T105 [P] [US3] Create scripts/start-system.sh (Linux/macOS equivalent)
- [ ] T106 [P] [US3] Create scripts/stop-system.sh (Linux/macOS equivalent)
- [ ] T107 [P] [US3] Create scripts/reset-observability.sh (Linux/macOS equivalent)

**Validation**:

- [ ] T108 [US3] Run scripts/start-system.ps1 and verify both services start
- [ ] T109 [US3] Verify URLs are accessible (http://localhost:4000, http://localhost:5173)
- [ ] T110 [US3] Test error scenario: start when services already running
- [ ] T111 [US3] Run scripts/stop-system.ps1 and verify all processes terminate
- [ ] T112 [US3] Run scripts/reset-observability.ps1 and verify database is cleared and system restarts

**Checkpoint**: At this point, User Story 3 should be fully functional - complete system manageable with single commands

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T113 [P] Cleanup: Remove temp-observability-reference/ directory
- [X] T114 [P] Documentation: Update root README.md with quick start guide
- [X] T115 [P] Documentation: Update root CLAUDE.md with final multi-app architecture notes
- [X] T116 [P] Documentation: Add apps/ directory architecture diagram to README.md
- [X] T117 [P] Documentation: Update all relative path references in existing documentation
- [ ] T118 Validation: Run complete quickstart.md workflow to verify all steps work [Requires manual testing]
- [ ] T119 Validation: Verify all 8 acceptance scenarios from spec.md success criteria [Requires manual testing]
- [X] T120 [P] Create .env.example files for each app (if needed)
- [ ] T121 [P] Add performance validation: verify MCP tool calls <2s, event ingestion <100ms, WebSocket delivery <1s [Requires manual testing]
- [ ] T122 Final verification: Run /career:apply workflow end-to-end from new architecture [Requires manual testing]

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 (Setup) - BLOCKS all user stories
- **Phase 3 (US4 - Directory Structure)**: Depends on Phase 2 - BLOCKS US1 (resume-agent migration)
- **Phase 4 (US1 - Resume Agent Migration)**: Depends on Phase 3 (US4 must complete first)
- **Phase 5 (US2 - Observability System)**: Depends on Phase 2 only - CAN RUN IN PARALLEL with US1 and US4
- **Phase 6 (US3 - System Scripts)**: Depends on Phase 5 (US2 completion - scripts manage observability components)
- **Phase 7 (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

```
Phase 1: Setup (T001-T008)
         ↓
Phase 2: Foundational (T009-T013)
         ↓
         ├─→ Phase 3: US4 Directory Structure (T014-T026)
         │              ↓
         │   Phase 4: US1 Resume Agent Migration (T027-T044)
         │
         └─→ Phase 5: US2 Observability System (T045-T091)
                        ↓
             Phase 6: US3 System Scripts (T092-T112)

         All stories complete ↓

Phase 7: Polish (T113-T122)
```

**Critical Path**: Setup → Foundational → US4 → US1 (resume-agent migration is top priority)

**Parallel Opportunity**: US2 (Observability) can start as soon as Foundational completes, even before US4/US1

### Within Each User Story

**User Story 4 (Directory Structure)**:
- All directory creation tasks (T014-T018) can run in parallel
- Path resolution tasks (T019-T023) depend on directories existing
- Documentation tasks (T024-T026) can run in parallel after implementation

**User Story 1 (Resume Agent Migration)**:
- File migration tasks (T028-T034) can run in parallel after T027
- Configuration updates (T035-T037) depend on file migration
- Validation tasks (T038-T044) must run sequentially after configuration

**User Story 2 (Observability System)**:
- Server file copies (T045-T049) can run in parallel
- Client file copies (T061-T068) can run in parallel
- Server and Client setup can run in parallel (different directories)
- Hook scripts (T076-T081) can run in parallel with server/client
- Validation tasks (T085-T091) must run sequentially

**User Story 3 (System Scripts)**:
- All PowerShell script tasks (T092-T104) can run in parallel
- Bash scripts (T105-T107) can run in parallel
- Validation must run sequentially

### Parallel Opportunities

**Maximum Parallelism** (with sufficient team capacity):

1. **Phase 1**: T002, T003, T004, T005, T006 can all run in parallel
2. **Phase 2**: T010, T011, T012 can run in parallel
3. **Phase 3**: T014-T018 (directory creation) can run in parallel
   - T024, T025, T026 (documentation) can run in parallel
4. **Phase 4**: T028-T034 (agent file moves) can run in parallel
5. **Phase 5**:
   - Server copies (T045-T049) in parallel
   - Client copies (T061-T068) in parallel
   - Hooks (T076-T081) in parallel
   - Documentation (T059, T060, T075) in parallel
6. **Phase 6**: T092-T107 (all scripts) can run in parallel
7. **Phase 7**: T113-T117, T120, T121 can run in parallel

---

## Parallel Example: Phase 5 (User Story 2)

```bash
# Server setup (parallel):
Task: "Copy server/src/index.ts to apps/observability-server/src/index.ts"
Task: "Copy server/src/db.ts to apps/observability-server/src/db.ts"
Task: "Copy server/src/types.ts to apps/observability-server/src/types.ts"
Task: "Copy server/package.json to apps/observability-server/package.json"
Task: "Copy server/tsconfig.json to apps/observability-server/tsconfig.json"

# Client setup (parallel with server):
Task: "Copy client/src/App.vue to apps/client/src/App.vue"
Task: "Copy client/src/main.ts to apps/client/src/main.ts"
Task: "Copy client/src/components/ to apps/client/src/components/"
Task: "Copy client/package.json to apps/client/package.json"
Task: "Copy client/vite.config.ts to apps/client/vite.config.ts"

# Hook scripts (parallel with both):
Task: "Copy .claude/hooks/send_event.py"
Task: "Add command line argument parsing"
Task: "Add stdin reading logic"
Task: "Implement HTTP POST with timeout"
```

---

## Implementation Strategy

### MVP First (User Stories 4 + 1 Only)

This gets resume-agent working in new location as quickly as possible:

1. Complete Phase 1: Setup (T001-T008)
2. Complete Phase 2: Foundational (T009-T013)
3. Complete Phase 3: User Story 4 - Directory Structure (T014-T026)
4. Complete Phase 4: User Story 1 - Resume Agent Migration (T027-T044)
5. **STOP and VALIDATE**: Test all /career:* commands work from new location
6. **Success Criteria**: Resume agent fully functional with 100% backward compatibility

**MVP Delivery**: At this point, the core architecture refactoring is complete. Observability is nice-to-have.

### Incremental Delivery

Each user story adds independent value:

1. **Setup + Foundational** (T001-T013) → Multi-app structure ready
2. **+ US4 Directory Structure** (T014-T026) → Apps can be organized in isolated directories
3. **+ US1 Resume Agent Migration** (T027-T044) → Resume agent works from new location ✅ MVP!
4. **+ US2 Observability System** (T045-T091) → Real-time monitoring available
5. **+ US3 System Scripts** (T092-T112) → One-command system management
6. **+ Polish** (T113-T122) → Production-ready

Each increment is independently valuable and testable.

### Parallel Team Strategy

With multiple developers (assumes 3 developers):

1. **All developers**: Complete Setup + Foundational together (T001-T013)
2. **All developers**: Complete US4 Directory Structure together (T014-T026)
3. **Split work after foundational**:
   - **Developer A**: US1 Resume Agent Migration (T027-T044) - CRITICAL PATH
   - **Developer B**: US2 Observability Server (T045-T060) - Can start immediately
   - **Developer C**: US2 Web Client (T061-T075) - Can start immediately
4. **Developer B + C**: Coordinate on US2 Hook Scripts (T076-T091)
5. **Any developer**: US3 System Scripts (T092-T112) - After US2 complete
6. **All developers**: Polish (T113-T122) - Final validation together

---

## Task Summary

**Total Tasks**: 122 tasks

**By Phase**:
- Phase 1 (Setup): 8 tasks
- Phase 2 (Foundational): 5 tasks
- Phase 3 (US4 - Directory Structure): 13 tasks
- Phase 4 (US1 - Resume Agent Migration): 18 tasks
- Phase 5 (US2 - Observability System): 47 tasks
- Phase 6 (US3 - System Scripts): 21 tasks
- Phase 7 (Polish): 10 tasks

**By User Story**:
- User Story 4 (Directory Structure): 13 tasks
- User Story 1 (Resume Agent Migration): 18 tasks
- User Story 2 (Observability System): 47 tasks
- User Story 3 (System Scripts): 21 tasks
- Setup/Foundational/Polish: 23 tasks

**Parallel Opportunities**: 68 tasks marked [P] can run in parallel (56% of all tasks)

**MVP Scope** (US4 + US1): 31 tasks (Setup + Foundational + US4 + US1)

**Critical Path**: Setup → Foundational → US4 → US1 (31 tasks minimum to achieve working resume-agent migration)

---

## Notes

- [P] tasks = different files, no dependencies within their phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Constitution principles embedded throughout (Data Access Layer, Type Safety, Observability, Multi-App Isolation)
- Stop at any checkpoint to validate story independently
- Commit after each task or logical group
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
