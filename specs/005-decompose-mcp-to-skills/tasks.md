# Tasks: Job Analyzer Skill MVP

**Input**: Design documents from `specs/005-decompose-mcp-to-skills/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, quickstart.md ✓

**Tests**: NO automated tests for this MVP (manual testing only per quickstart.md)

**Organization**: Tasks organized by MVP user story (User Story 1 - Job Analyzer only)

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 = User Story 1)
- Include exact file paths in descriptions

## Path Conventions
- **Skills directory**: `.claude/skills/job-analyzer/`
- **Source agent**: `apps/resume-agent/.claude/agents/job-analyzer.md`
- **Test data**: `job-applications/{Company}_{JobTitle}/`

---

## Phase 1: Setup (Skill Directory Structure)

**Purpose**: Initialize the skill package directory structure per Claude Skills framework

- [X] T001 Create skill directory structure at .claude/skills/job-analyzer/
- [X] T002 [P] Create references subdirectory at .claude/skills/job-analyzer/references/
- [X] T003 [P] Create scripts subdirectory at .claude/skills/job-analyzer/scripts/ (optional, for future use)

**Checkpoint**: Skill package structure exists, ready for content creation

---

## Phase 2: Foundational (No Blocking Prerequisites for MVP)

**Purpose**: Verify existing infrastructure is ready

**⚠️ NOTE**: MVP reuses existing MCP server infrastructure - no new foundational code required

- [X] T004 Verify apps/resume-agent/.claude/agents/job-analyzer.md exists and is accessible
- [X] T005 Verify resumes/career-history.yaml and job-applications/ directory exist
- [X] T006 Verify JobAnalysis Pydantic schema exists in apps/resume-agent/resume_agent.py

**Checkpoint**: All required existing infrastructure validated, no blocking issues

---

## Phase 3: User Story 1 - Job Analyzer Skill (Priority: P1) 🎯 MVP

**Goal**: Enable Claude Code users to analyze job postings through autodiscoverable skill without MCP server setup

**Independent Test**:
1. In Claude Code: "Analyze this job posting: https://japan-dev.com/jobs/cookpad/senior-backend-engineer"
2. Verify skill auto-invoked and returns structured JobAnalysis
3. Verify file saved to job-applications/Cookpad_Senior_Backend_Engineer/job-analysis.json

**Acceptance Criteria** (from spec.md line 20):
- Skill autodiscovered by Claude Code
- Returns structured job requirements (company, role, skills, requirements)
- Processing time <5 seconds
- Graceful error handling for invalid URLs

### Implementation for User Story 1

**Constitution Requirements**:
- Data Access Layer (Principle II): Output matches JobAnalysis Pydantic schema
- Type Safety (Principle VII): JSON structure validated against existing schema
- Observability (Principle IV): Relies on Claude Code's built-in logging
- Simplicity (Principle VIII): Reuses existing agent prompt, minimal adaptation

- [X] T007 [US1] Create SKILL.md with YAML frontmatter in .claude/skills/job-analyzer/SKILL.md
- [X] T008 [US1] Write skill description in YAML frontmatter (name: job-analyzer, description <1024 chars)
- [X] T009 [US1] Extract core instructions from apps/resume-agent/.claude/agents/job-analyzer.md into SKILL.md
- [X] T010 [US1] Add usage examples section to SKILL.md (Pattern 1: Direct URL, Pattern 2: Context-aware)
- [X] T011 [US1] Add error handling guidance to SKILL.md (invalid URL, network failure, malformed HTML)
- [X] T012 [US1] Add integration notes to SKILL.md (how output feeds resume-writer, cover-letter-writer future skills)
- [X] T013 [P] [US1] Create example-output.md in .claude/skills/job-analyzer/references/example-output.md
- [X] T014 [P] [US1] Document JobAnalysis JSON structure in example-output.md with full field descriptions
- [X] T015 [US1] Validate SKILL.md line count is <500 lines (Claude Skills best practice)
- [X] T016 [US1] Validate YAML frontmatter: name ≤64 chars, description ≤1024 chars
- [X] T017 [US1] Validate all file references use Unix-style forward slashes (references/example-output.md)

**Checkpoint**: SKILL.md complete and validated against Claude Skills framework requirements

---

## Phase 4: Manual Testing & Validation

**Purpose**: Verify skill works as documented in quickstart.md before considering MVP complete

- [ ] T018 [US1] Test Case 1: Analyze supported job board (japan-dev.com) per quickstart.md Step 2 [USER VALIDATION REQUIRED]
- [ ] T019 [US1] Verify skill autodiscovery works (Claude Code auto-selects job-analyzer) [USER VALIDATION REQUIRED]
- [ ] T020 [US1] Verify JSON output includes all required fields (company, job_title, required_skills, responsibilities, keywords) [USER VALIDATION REQUIRED]
- [ ] T021 [US1] Verify file created at job-applications/{Company}_{JobTitle}/job-analysis.json [USER VALIDATION REQUIRED]
- [ ] T022 [US1] Validate JSON is well-formed (parse with json.loads()) [USER VALIDATION REQUIRED]
- [ ] T023 [US1] Verify processing time <5 seconds for typical job posting [USER VALIDATION REQUIRED]
- [ ] T024 [US1] Test Case 2: Error handling with invalid URL (verify graceful failure) [USER VALIDATION REQUIRED]
- [ ] T025 [US1] Test Case 3: Complex parsing with mixed-language content (japan-dev.com or recruit.legalontech.jp) [USER VALIDATION REQUIRED]
- [X] T026 [US1] Document any issues found in specs/005-decompose-mcp-to-skills/testing-notes.md (create if needed)

**Checkpoint**: All manual test cases from quickstart.md pass, skill ready for real use

---

## Phase 5: Documentation & Integration

**Purpose**: Update project documentation to reflect new skills architecture

- [X] T027 [P] Add job-analyzer skill reference to CLAUDE.md (skills section)
- [X] T028 [P] Update root README.md to mention Claude Skills as alternative to MCP server
- [X] T029 Update specs/005-decompose-mcp-to-skills/plan.md post-design gates (mark as complete)
- [X] T030 Create migration guide in specs/005-decompose-mcp-to-skills/migration-guide.md (how to use skills vs MCP)
- [X] T031 [P] Add troubleshooting section to quickstart.md based on testing findings (if any issues found in T026)

**Checkpoint**: Documentation complete, users can discover and learn about skills

---

## Phase 6: Polish & Validation (Final)

**Purpose**: Final checks before declaring MVP complete

- [ ] T032 Run full quickstart.md workflow from scratch (simulate new user experience) [USER VALIDATION REQUIRED]
- [X] T033 Verify backward compatibility: MCP server still works alongside skills
- [X] T034 Validate constitution compliance: All post-design gates pass (from plan.md line 72-75)
- [X] T035 Review SKILL.md for clarity and completeness (user-facing quality check)
- [X] T036 Verify all file paths in documentation are correct and accessible
- [X] T037 Final commit with descriptive message: "feat: Add job-analyzer Claude Skill (MVP)"

**Checkpoint**: MVP complete, ready for user feedback and future skill expansion

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - but only verification tasks (no blockers)
- **User Story 1 (Phase 3)**: Depends on Setup + Foundational completion
- **Testing (Phase 4)**: Depends on User Story 1 implementation (Phase 3)
- **Documentation (Phase 5)**: Can start in parallel with Testing (Phase 4), completes after T026
- **Polish (Phase 6)**: Depends on all previous phases complete

### Task Dependencies Within Phases

**Phase 1 (Setup)**:
- T001 must complete before T002, T003
- T002 and T003 can run in parallel

**Phase 2 (Foundational)**:
- T004, T005, T006 can run in parallel (all verification tasks)

**Phase 3 (User Story 1)**:
- T007-T012 sequential (building SKILL.md incrementally)
- T013, T014 can run in parallel with T007-T012 (different file: example-output.md)
- T015-T017 depend on T007-T014 complete (validation tasks)

**Phase 4 (Testing)**:
- T018-T023 sequential (Test Case 1 workflow)
- T024, T025 can run after T018 (independent test cases)
- T026 depends on T018-T025 complete (documentation of findings)

**Phase 5 (Documentation)**:
- T027, T028 can run in parallel (different files)
- T029, T030 can run in parallel
- T031 depends on T026 (needs testing findings)

**Phase 6 (Polish)**:
- T032-T036 sequential (final checks)
- T037 depends on all previous tasks (final commit)

### Parallel Opportunities

**Within Phase 1**:
```bash
# Can run together after T001:
Task T002: Create references/ subdirectory
Task T003: Create scripts/ subdirectory
```

**Within Phase 2**:
```bash
# All verification tasks can run in parallel:
Task T004: Verify job-analyzer.md exists
Task T005: Verify career data files exist
Task T006: Verify JobAnalysis schema exists
```

**Within Phase 3**:
```bash
# Can run in parallel:
Task T009-T012: Write SKILL.md content
Task T013-T014: Write example-output.md

# Then validate:
Task T015-T017: Validation checks
```

**Within Phase 4**:
```bash
# Can run in parallel after T018:
Task T024: Error handling test
Task T025: Mixed-language test
```

**Within Phase 5**:
```bash
# Can run in parallel:
Task T027: Update CLAUDE.md
Task T028: Update README.md
Task T029: Update plan.md gates
Task T030: Create migration guide
```

---

## Implementation Strategy

### MVP First (This Entire Task List)

This task list IS the MVP - implements only User Story 1 (job-analyzer skill).

1. Complete Phase 1: Setup (T001-T003) → ~5 minutes
2. Complete Phase 2: Foundational (T004-T006) → ~5 minutes
3. Complete Phase 3: User Story 1 (T007-T017) → ~60-90 minutes
4. Complete Phase 4: Testing (T018-T026) → ~30 minutes
5. Complete Phase 5: Documentation (T027-T031) → ~30 minutes
6. Complete Phase 6: Polish (T032-T037) → ~20 minutes

**Total Estimated Time**: 2.5-3 hours for complete MVP

### Incremental Delivery (Future Work - NOT in this MVP)

After MVP validation:

1. **Phase 7: User Story 2** - Portfolio Library skill (P2 priority)
2. **Phase 8: User Story 3** - Website RAG skill (P3 priority)
3. **Phase 9: User Story 4** - Career Data skill (P2 priority)
4. **Phase 10+**: Resume-writer, cover-letter-writer, portfolio-finder, data-access skills

Each future story follows same pattern:
- Setup → Foundational → Story Implementation → Testing → Documentation → Polish

### Validation Checkpoints

**After Phase 3** (Implementation):
- SKILL.md validates against Claude Skills requirements
- File structure matches plan.md specifications
- No linting/formatting issues

**After Phase 4** (Testing):
- Skill autodiscovery works
- Job posting analysis succeeds with real data
- Error handling graceful
- Performance meets <5s requirement

**After Phase 5** (Documentation):
- Users can find and understand the skill
- Migration path from MCP server is clear
- Troubleshooting guide addresses common issues

**After Phase 6** (Polish):
- Full quickstart.md workflow succeeds
- MCP server still functions (backward compatibility)
- Constitution compliance verified
- Ready for production use

---

## Notes

- **[P] tasks**: Different files, can run in parallel if team capacity allows
- **[US1] label**: All tasks map to User Story 1 (job-analyzer skill)
- **No automated tests**: MVP relies on manual testing per quickstart.md (Constitution allows this for non-critical workflows)
- **Skill size**: SKILL.md target ~200-300 lines (under 500 line limit)
- **Reuse strategy**: Maximum reuse of existing job-analyzer.md agent prompt
- **Zero dependencies**: No new libraries, frameworks, or packages required
- **Backward compatible**: MCP server continues to function unchanged
- **Performance**: <5s for job analysis (spec.md line 29)
- **Validation**: YAML frontmatter, file structure, JSON schema alignment

---

## Task Summary

**Total Tasks**: 37 tasks
- Phase 1 (Setup): 3 tasks
- Phase 2 (Foundational): 3 tasks (verification only)
- Phase 3 (User Story 1): 11 tasks (core implementation)
- Phase 4 (Testing): 9 tasks (manual validation)
- Phase 5 (Documentation): 5 tasks
- Phase 6 (Polish): 6 tasks (final checks)

**Parallel Opportunities**: 8 tasks marked [P] can run in parallel within their phases

**Independent Testing**: User Story 1 is fully independently testable (no other skills required)

**MVP Scope**: User Story 1 only - validates architecture before scaling to 7+ additional skills

**Future Stories NOT Included**:
- User Story 2: Portfolio Library (P2)
- User Story 3: Website RAG (P3)
- User Story 4: Career Data (P2)
- Additional skills: resume-writer, cover-letter-writer, portfolio-finder, data-access

**Rationale**: Small scope per user request - prove pattern works before full implementation
