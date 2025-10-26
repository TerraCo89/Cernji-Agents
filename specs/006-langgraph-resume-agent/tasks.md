# Tasks: LangGraph Resume Agent

**Input**: Design documents from `/specs/006-langgraph-resume-agent/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests REQUESTED per plan.md - Three-tier testing strategy (contract, integration, unit)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- Single-file Python application: `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- Tests: `apps/resume-agent-langgraph/tests/`
- All paths are absolute from repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create directory structure: `apps/resume-agent-langgraph/` with subdirectories `tests/contract/`, `tests/integration/`, `tests/unit/`
- [X] T002 Initialize UV project with `pyproject.toml` in `apps/resume-agent-langgraph/` with dependencies: LangGraph, FastMCP 2.0, Pydantic, sentence-transformers, langchain-text-splitters, sqlite-vec, pytest
- [X] T003 [P] Create `.env.example` file in `apps/resume-agent-langgraph/` with required environment variables (ANTHROPIC_API_KEY, OBSERVABILITY_SERVER_URL)
- [X] T004 [P] Create `README.md` in `apps/resume-agent-langgraph/` documenting setup, dependencies, and quick start
- [X] T005 [P] Create `CLAUDE.md` in `apps/resume-agent-langgraph/` with agent-specific development guidance and LangGraph patterns
- [X] T006 Create checkpoint database initialization script in `apps/resume-agent-langgraph/resume_agent_langgraph.py` (SqliteSaver for `data/workflow_checkpoints.db`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core workflow infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Define Pydantic schema for ApplicationWorkflowState in `apps/resume-agent-langgraph/resume_agent_langgraph.py` (from data-model.md)
- [X] T008 Define Pydantic schema for JobAnalysisWorkflowState in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [X] T009 Define Pydantic schema for ResumeTailoringWorkflowState in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [X] T010 Import existing DAL functions from `apps/resume-agent/resume_agent.py` (data_read_*, data_write_* functions) - reuse without modification
- [X] T011 Initialize FastMCP server in `apps/resume-agent-langgraph/resume_agent_langgraph.py` with MCP server name "Resume Agent LangGraph"
- [X] T012 Initialize LangGraph SqliteSaver checkpointer with `data/workflow_checkpoints.db` connection string
- [X] T013 Implement observability hook integration helper function that emits events (SessionStart, PreToolUse, PostToolUse, SessionEnd) to existing observability server
- [X] T014 Implement error accumulation helper function that appends errors to state without raising exceptions (supports partial success FR-007)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Job Analysis Workflow (Priority: P1) 🎯 MVP

**Goal**: Analyze job posting URL and extract structured requirements, skills, keywords with caching support

**Independent Test**: Provide job URL, verify structured JobAnalysis data returned (company, job_title, requirements, skills, responsibilities, keywords). Verify cached results on second request.

### Tests for User Story 1

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T015 [P] [US1] Contract test for `analyze_job_posting` MCP tool signature in `apps/resume-agent-langgraph/tests/contract/test_mcp_tools.py` - verify signature matches original implementation
- [X] T016 [P] [US1] Integration test for job analysis workflow in `apps/resume-agent-langgraph/tests/integration/test_job_analysis_workflow.py` - test with mocked Claude API and verify full workflow execution
- [X] T017 [P] [US1] Integration test for caching behavior in `apps/resume-agent-langgraph/tests/integration/test_job_analysis_workflow.py` - verify cached results on repeat requests (<3s)
- [X] T018 [P] [US1] Unit test for `check_job_analysis_cache_node` in `apps/resume-agent-langgraph/tests/unit/test_langgraph_nodes.py` - verify cache lookup logic

### Implementation for User Story 1

- [X] T019 [P] [US1] Implement `check_job_analysis_cache_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - checks DAL for cached job analysis, populates state if found
- [X] T020 [P] [US1] Implement `analyze_job_with_claude_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - calls existing DAL functions, handles errors, updates state with job_analysis
- [X] T021 [P] [US1] Implement `finalize_job_analysis_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - calculates duration, triggers observability PostToolUse event
- [X] T022 [US1] Create job analysis StateGraph in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - add nodes (check_cache, analyze_job, finalize), add conditional edge from check_cache (skip analysis if cached), set entry point
- [X] T023 [US1] Compile job analysis workflow graph with checkpointer in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [X] T024 [US1] Implement `analyze_job_posting` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - wraps job analysis workflow, maintains original signature, returns JobAnalysis dict
- [X] T025 [US1] Add observability hooks (SessionStart at workflow entry, SessionEnd at workflow exit) for job analysis workflow
- [X] T026 [US1] Add performance tracking (node_durations) to verify <15s new / <3s cached requirement (SC-003)

**Checkpoint**: ✅ User Story 1 COMPLETE (2025-10-23) - job analysis workflow functional and independently testable

---

## Phase 4: User Story 2 - Resume Tailoring Workflow (Priority: P1)

**Goal**: Generate tailored resume for specific job posting by mapping master resume to job requirements with keyword optimization

**Independent Test**: Provide job URL and verify tailored resume content returned with relevant keywords integrated. Can test independently if job analysis already cached.

### Tests for User Story 2

- [ ] T027 [P] [US2] Contract test for `tailor_resume_for_job` MCP tool signature in `apps/resume-agent-langgraph/tests/contract/test_mcp_tools.py`
- [ ] T028 [P] [US2] Integration test for resume tailoring workflow in `apps/resume-agent-langgraph/tests/integration/test_resume_tailoring_workflow.py` - test with mocked Claude API and pre-existing job analysis
- [ ] T029 [P] [US2] Unit test for `tailor_resume_node` in `apps/resume-agent-langgraph/tests/unit/test_langgraph_nodes.py`

### Implementation for User Story 2

- [ ] T030 [P] [US2] Implement `load_master_resume_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - loads master resume from DAL into state
- [ ] T031 [P] [US2] Implement `check_tailored_resume_cache_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - checks DAL for cached tailored resume
- [ ] T032 [P] [US2] Implement `tailor_resume_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - calls existing DAL functions to generate tailored resume, integrates keywords, handles errors
- [ ] T033 [P] [US2] Implement `finalize_resume_tailoring_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - calculates duration, saves resume via DAL, triggers observability events
- [ ] T034 [US2] Create resume tailoring StateGraph in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - add nodes (load_master_resume, check_cache, tailor_resume, finalize), add conditional edges
- [ ] T035 [US2] Compile resume tailoring workflow graph with checkpointer in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T036 [US2] Implement `tailor_resume_for_job` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - wraps resume tailoring workflow, maintains original signature
- [ ] T037 [US2] Add performance tracking to verify <20s requirement (SC-003)
- [ ] T038 [US2] Add observability hooks for resume tailoring workflow

**Checkpoint**: User Story 2 complete - resume tailoring workflow functional and independently testable

---

## Phase 5: User Story 5 - Complete Application Workflow (Priority: P1)

**Goal**: Orchestrate all steps (analyze → tailor → cover letter → portfolio) in single workflow with partial success support

**Why Phase 5 before 3/4**: This is P1 and demonstrates LangGraph's orchestration capabilities - critical for experiment evaluation

**Independent Test**: Provide single job URL, verify all outputs generated (job_analysis, tailored_resume, cover_letter, portfolio_examples) even if individual steps fail

### Tests for User Story 5

- [ ] T039 [P] [US5] Contract test for `complete_application_workflow` MCP tool signature in `apps/resume-agent-langgraph/tests/contract/test_mcp_tools.py`
- [ ] T040 [P] [US5] Integration test for complete workflow in `apps/resume-agent-langgraph/tests/integration/test_complete_application_workflow.py` - test full end-to-end workflow with mocked external services
- [ ] T041 [P] [US5] Integration test for partial success in `apps/resume-agent-langgraph/tests/integration/test_error_handling.py` - test workflow continues when individual nodes fail, verify errors accumulated
- [ ] T042 [P] [US5] Integration test for state recovery in `apps/resume-agent-langgraph/tests/integration/test_complete_application_workflow.py` - test workflow resumption after interruption using same thread_id

### Implementation for User Story 5

- [ ] T043 [P] [US5] Implement `check_complete_workflow_cache_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - checks if all workflow outputs already cached
- [ ] T044 [P] [US5] Implement conditional edge helper `should_continue_to_next_step` in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - evaluates state and decides whether to proceed or skip based on errors (supports FR-011)
- [ ] T045 [US5] Create complete application StateGraph in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - reuse existing nodes from US1/US2, add conditional edges for partial success, add cache node at entry
- [ ] T046 [US5] Add conditional branching logic: if job analysis fails, skip to cover letter; if resume fails, continue to cover letter; etc. (implements FR-011)
- [ ] T047 [US5] Compile complete application workflow graph with checkpointer in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T048 [US5] Implement `complete_application_workflow` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - wraps complete workflow, returns all outputs plus errors list
- [ ] T049 [US5] Add workflow-level caching logic to reduce duplicate processing by 80% (SC-004)
- [ ] T050 [US5] Add performance tracking to verify <60s requirement (SC-001)
- [ ] T051 [US5] Add comprehensive observability hooks tracking each node transition

**Checkpoint**: User Story 5 complete - complete application workflow demonstrates LangGraph orchestration with partial success and state recovery

---

## Phase 6: User Story 3 - Cover Letter Generation Workflow (Priority: P2)

**Goal**: Generate personalized cover letter demonstrating cultural fit based on job requirements and career history

**Independent Test**: Provide job analysis and company info, verify coherent personalized cover letter returned

### Tests for User Story 3

- [ ] T052 [P] [US3] Contract test for `generate_cover_letter` MCP tool signature in `apps/resume-agent-langgraph/tests/contract/test_mcp_tools.py`
- [ ] T053 [P] [US3] Integration test for cover letter generation workflow in `apps/resume-agent-langgraph/tests/integration/test_cover_letter_workflow.py` - test with mocked Claude API

### Implementation for User Story 3

- [ ] T054 [P] [US3] Implement `load_career_history_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - loads career history from DAL
- [ ] T055 [P] [US3] Implement `check_cover_letter_cache_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - checks DAL for cached cover letter
- [ ] T056 [P] [US3] Implement `generate_cover_letter_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - calls existing DAL functions, incorporates company info if available (fallback to generic if not)
- [ ] T057 [P] [US3] Implement `finalize_cover_letter_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - saves cover letter via DAL, calculates duration
- [ ] T058 [US3] Create cover letter StateGraph in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - add nodes, conditional edges
- [ ] T059 [US3] Compile cover letter workflow graph with checkpointer in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T060 [US3] Implement `generate_cover_letter` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - wraps workflow, maintains original signature (job_url, company_name, role_title)
- [ ] T061 [US3] Add performance tracking to verify <25s requirement (SC-003)
- [ ] T062 [US3] Add observability hooks for cover letter workflow

**Checkpoint**: User Story 3 complete - cover letter generation workflow functional

---

## Phase 7: User Story 4 - Portfolio Search Workflow (Priority: P2)

**Goal**: Search GitHub portfolio for code examples matching job requirements

**Independent Test**: Provide job analysis with technology requirements, verify relevant repositories and code snippets returned

### Tests for User Story 4

- [ ] T063 [P] [US4] Contract test for `find_portfolio_examples` MCP tool signature in `apps/resume-agent-langgraph/tests/contract/test_mcp_tools.py`
- [ ] T064 [P] [US4] Integration test for portfolio search workflow in `apps/resume-agent-langgraph/tests/integration/test_portfolio_search_workflow.py` - test with mocked GitHub API

### Implementation for User Story 4

- [ ] T065 [P] [US4] Implement `extract_technologies_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - extracts technology list from job analysis
- [ ] T066 [P] [US4] Implement `search_portfolio_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - calls existing DAL portfolio search functions, handles missing/private repos
- [ ] T067 [P] [US4] Implement `finalize_portfolio_search_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - formats results, calculates relevance scores
- [ ] T068 [US4] Create portfolio search StateGraph in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - add nodes, edges
- [ ] T069 [US4] Compile portfolio search workflow graph with checkpointer in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T070 [US4] Implement `find_portfolio_examples` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - wraps workflow, maintains original signature
- [ ] T071 [US4] Add performance tracking to verify <10s requirement (spec.md user story 4)
- [ ] T072 [US4] Add observability hooks for portfolio search workflow

**Checkpoint**: User Story 4 complete - portfolio search workflow functional

---

## Phase 8: User Story 6 - Career History Management (Priority: P3)

**Goal**: Update master resume, add experiences, achievements, and skills

**Independent Test**: Add new employment experience, verify career-history.yaml and master resume updated correctly

### Tests for User Story 6

- [ ] T073 [P] [US6] Contract test for `data_add_achievement` and `data_add_technology` MCP tool signatures in `apps/resume-agent-langgraph/tests/contract/test_mcp_tools.py`
- [ ] T074 [P] [US6] Integration test for career history updates in `apps/resume-agent-langgraph/tests/integration/test_career_history_workflow.py`

### Implementation for User Story 6

- [ ] T075 [P] [US6] Implement `data_add_achievement` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - wraps existing DAL function, maintains signature
- [ ] T076 [P] [US6] Implement `data_add_technology` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - wraps existing DAL function, maintains signature
- [ ] T077 [P] [US6] Implement data validation for achievement/technology additions (Pydantic validation before DAL calls)
- [ ] T078 [US6] Add observability hooks for data modification events
- [ ] T079 [US6] Add performance tracking to verify <5s requirement (spec.md user story 6)

**Checkpoint**: User Story 6 complete - career history management functional

---

## Phase 9: User Story 7 - Website RAG Pipeline (Priority: P3)

**Goal**: Process websites into searchable knowledge base for enhanced context in applications

**Independent Test**: Process company website URL, verify semantic search returns relevant content with source attribution

### Tests for User Story 7

- [ ] T080 [P] [US7] Contract test for RAG MCP tools (`rag_process_website`, `rag_query_websites`) in `apps/resume-agent-langgraph/tests/contract/test_mcp_tools.py`
- [ ] T081 [P] [US7] Integration test for website processing workflow in `apps/resume-agent-langgraph/tests/integration/test_rag_pipeline_workflow.py` - test multilingual content

### Implementation for User Story 7

- [ ] T082 [P] [US7] Implement `fetch_website_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - fetches URL content, handles fetch failures
- [ ] T083 [P] [US7] Implement `chunk_content_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - chunks HTML with langchain-text-splitters, detects language
- [ ] T084 [P] [US7] Implement `generate_embeddings_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - generates embeddings with sentence-transformers
- [ ] T085 [P] [US7] Implement `store_chunks_node` function in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - stores chunks in SQLite with sqlite-vec
- [ ] T086 [US7] Create website processing StateGraph in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - add nodes, error handling edges
- [ ] T087 [US7] Compile website processing workflow graph with checkpointer in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T088 [US7] Implement `rag_process_website` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - wraps workflow, maintains signature
- [ ] T089 [US7] Implement `rag_query_websites` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py` - semantic search with source attribution
- [ ] T090 [US7] Add staleness detection (>30 days) and refresh prompting
- [ ] T091 [US7] Add performance tracking to verify <20s processing / <3s queries (spec.md user story 7)
- [ ] T092 [US7] Add observability hooks for RAG pipeline workflow

**Checkpoint**: User Story 7 complete - RAG pipeline functional

---

## Phase 10: Remaining MCP Tools (Data Access Wrappers)

**Goal**: Implement remaining 14 data access MCP tools that wrap existing DAL functions

**Independent Test**: Each MCP tool maintains original signature and behavior

### Tests for Remaining Tools

- [ ] T093 [P] Contract tests for all 14 remaining data access MCP tools in `apps/resume-agent-langgraph/tests/contract/test_mcp_tools.py` - verify signatures match original

### Implementation for Remaining Tools

- [ ] T094 [P] Implement `data_read_master_resume` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T095 [P] Implement `data_read_job_analysis` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T096 [P] Implement `data_write_job_analysis` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T097 [P] Implement `data_read_tailored_resume` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T098 [P] Implement `data_write_tailored_resume` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T099 [P] Implement `data_read_cover_letter` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T100 [P] Implement `data_write_cover_letter` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T101 [P] Implement `data_list_applications` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T102 [P] Implement `data_add_portfolio_example` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T103 [P] Implement `data_list_portfolio_examples` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T104 [P] Implement `data_search_portfolio_examples` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T105 [P] Implement `data_get_portfolio_example` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T106 [P] Implement `data_update_portfolio_example` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- [ ] T107 [P] Implement `data_delete_portfolio_example` MCP tool in `apps/resume-agent-langgraph/resume_agent_langgraph.py`

**Checkpoint**: All 22 MCP tools implemented with backward compatibility

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T108 [P] Add workflow visualization support - implement state inspection endpoints for LangGraph Studio integration
- [ ] T109 [P] Add comprehensive error messages with actionable next steps for all workflows (95% target per SC-005)
- [ ] T110 [P] Implement checkpoint cleanup/garbage collection policy (default 7-day retention)
- [ ] T111 [P] Add concurrency testing to verify 100+ concurrent workflows supported (SC-006)
- [ ] T112 Update `README.md` with final performance benchmarks and comparison to original implementation
- [ ] T113 Update `CLAUDE.md` with lessons learned about LangGraph development patterns
- [ ] T114 Run all contract tests and verify 100% backward compatibility (SC-008)
- [ ] T115 Run all integration tests and verify performance targets met (SC-001, SC-003)
- [ ] T116 Run quickstart.md validation - verify all examples work end-to-end
- [ ] T117 Document evaluation criteria in `apps/resume-agent-langgraph/EVALUATION.md` - DX comparison, state management, debugging experience, performance observations
- [ ] T118 Code cleanup and refactoring pass - remove any debug code, ensure consistent style
- [ ] T119 Final security review - verify no API keys hardcoded, proper error handling for sensitive data

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - can start after Phase 2
- **User Story 2 (Phase 4)**: Depends on Foundational - can start after Phase 2 (parallel with US1)
- **User Story 5 (Phase 5)**: Depends on US1 + US2 completion (reuses their nodes)
- **User Story 3 (Phase 6)**: Depends on Foundational - can start after Phase 2 (parallel with US1/US2/US5)
- **User Story 4 (Phase 7)**: Depends on Foundational - can start after Phase 2 (parallel with others)
- **User Story 6 (Phase 8)**: Depends on Foundational - can start after Phase 2 (parallel with others)
- **User Story 7 (Phase 9)**: Depends on Foundational - can start after Phase 2 (parallel with others)
- **Remaining Tools (Phase 10)**: Depends on Foundational - can start after Phase 2 (parallel with user stories)
- **Polish (Phase 11)**: Depends on all user stories completion

### User Story Dependencies

- **US1 (Job Analysis)**: Independent - can start after Foundational
- **US2 (Resume Tailoring)**: Independent - can start after Foundational (may use US1 output but testable with cached job analysis)
- **US5 (Complete Workflow)**: Depends on US1 + US2 nodes (reuses them)
- **US3 (Cover Letter)**: Independent - can start after Foundational
- **US4 (Portfolio Search)**: Independent - can start after Foundational
- **US6 (Career History)**: Independent - can start after Foundational
- **US7 (RAG Pipeline)**: Independent - can start after Foundational

### Within Each User Story

- Tests FIRST → Models → Workflow Nodes → StateGraph Definition → Graph Compilation → MCP Tool Wrapper → Observability/Performance Tracking
- All tests marked [P] can run in parallel
- All model/node implementations marked [P] can run in parallel

### Parallel Opportunities

**After Phase 2 Foundational completes**, the following can proceed in parallel:
- US1 (Job Analysis) tasks T019-T026
- US2 (Resume Tailoring) tasks T030-T038
- US3 (Cover Letter) tasks T054-T062
- US4 (Portfolio Search) tasks T065-T072
- US6 (Career History) tasks T075-T079
- US7 (RAG Pipeline) tasks T082-T092
- Remaining MCP Tools tasks T094-T107

**US5 (Complete Workflow) can start after US1 + US2 complete** (requires their nodes)

**Phase 11 (Polish) requires all user stories complete**

---

## Implementation Strategy

### MVP Scope (Suggested)

**Phase 1 + Phase 2 + Phase 3 (User Story 1) = Minimal Viable Product**

This delivers:
- ✅ Job analysis workflow with LangGraph orchestration
- ✅ State persistence and recovery (demonstrates FR-005, SC-002)
- ✅ Caching support (demonstrates FR-013, SC-004)
- ✅ Observability integration (demonstrates FR-010)
- ✅ Partial success error handling (demonstrates FR-007)
- ✅ Contract tests proving backward compatibility (SC-008)

**Value**: Proves LangGraph's core capabilities (state management, orchestration, error handling) with minimal implementation. Can evaluate DX and decide whether to continue before investing in remaining stories.

### Incremental Delivery

1. **Sprint 1**: Phase 1-3 (MVP - Job Analysis only)
2. **Sprint 2**: Phase 4-5 (Resume Tailoring + Complete Workflow - demonstrates full orchestration)
3. **Sprint 3**: Phase 6-7 (Cover Letter + Portfolio - completes P1/P2 stories)
4. **Sprint 4**: Phase 8-9 (Career History + RAG - completes P3 stories)
5. **Sprint 5**: Phase 10-11 (Remaining tools + Polish + Evaluation)

Each sprint delivers independently testable functionality and can be evaluated before proceeding.

---

## Task Summary

**Total Tasks**: 119
**Tests**: 26 (contract + integration + unit)
**Implementation**: 93

**Tasks per User Story**:
- Setup (Phase 1): 6 tasks
- Foundational (Phase 2): 8 tasks
- US1 (Job Analysis): 12 tasks (4 tests + 8 impl)
- US2 (Resume Tailoring): 12 tasks (3 tests + 9 impl)
- US5 (Complete Workflow): 13 tasks (4 tests + 9 impl)
- US3 (Cover Letter): 11 tasks (2 tests + 9 impl)
- US4 (Portfolio Search): 10 tasks (2 tests + 8 impl)
- US6 (Career History): 7 tasks (2 tests + 5 impl)
- US7 (RAG Pipeline): 13 tasks (2 tests + 11 impl)
- Remaining MCP Tools: 15 tasks (1 test + 14 impl)
- Polish: 12 tasks

**Parallel Opportunities**: 67 tasks marked [P] can run in parallel within their phase

**Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 (MVP + full orchestration demo)

**Format Validation**: ✅ All 119 tasks follow checklist format with ID, [P] marker (if parallelizable), [Story] label (for user story phases), and file paths
