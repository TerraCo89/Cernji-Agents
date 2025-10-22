# Tasks: Website RAG Pipeline for Career Applications

**Feature**: 004-website-rag-pipeline
**Input**: Design documents from `specs/004-website-rag-pipeline/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL for this feature (not explicitly requested in spec.md). Tasks focus on implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- This feature extends existing `apps/resume-agent/` app
- Database: `data/resume_agent.db`
- Agent prompts: `apps/resume-agent/.claude/agents/`
- Slash commands: `.claude/commands/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [X] T001 Add RAG pipeline dependencies to apps/resume-agent/resume_agent.py PEP 723 header (sentence-transformers>=3.0.0, sqlite-vec>=0.1.0, langchain-text-splitters>=0.3.0)
- [X] T002 [P] Create database migration script at apps/resume-agent/scripts/create_rag_tables.py
- [X] T003 [P] Download sentence-transformers model (paraphrase-multilingual-MiniLM-L12-v2) on first run

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Define Pydantic schema for WebsiteSource in apps/resume-agent/resume_agent.py
- [X] T005 [P] Define Pydantic schema for WebsiteChunk in apps/resume-agent/resume_agent.py
- [X] T006 [P] Define Pydantic schema for QueryResult and ChunkResult in apps/resume-agent/resume_agent.py
- [X] T007 [P] Define Pydantic schema for ExtractionMetadata with JobPostingMetadata and BlogArticleMetadata in apps/resume-agent/resume_agent.py
- [X] T008 Create SQLite database tables (website_sources, website_chunks) in apps/resume-agent/scripts/create_rag_tables.py
- [X] T009 Create virtual table for vector embeddings (website_chunks_vec) using sqlite-vec in apps/resume-agent/scripts/create_rag_tables.py
- [X] T010 Create FTS5 virtual table (website_chunks_fts) with unicode61 tokenizer in apps/resume-agent/scripts/create_rag_tables.py
- [X] T011 Create database indexes for performance in apps/resume-agent/scripts/create_rag_tables.py (idx_ws_url, idx_ws_status, idx_ws_content_type, idx_wc_source_id)
- [X] T012 Implement embedding generation utility using sentence-transformers in apps/resume-agent/resume_agent.py
- [X] T013 Implement chunking utility using HTMLHeaderTextSplitter and RecursiveCharacterTextSplitter in apps/resume-agent/resume_agent.py
- [X] T014 Implement language detection function in apps/resume-agent/resume_agent.py (detect Japanese vs English vs mixed)
- [X] T015 [P] Update data-access-agent at apps/resume-agent/.claude/agents/data-access-agent.md with RAG data operations documentation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract Company Information from Job Posting (Priority: P1) 🎯 MVP

**Goal**: Process job posting URLs to extract structured company information, culture details, and role requirements

**Independent Test**: Provide a job posting URL and verify the system extracts company name, role details, requirements, and culture information into queryable chunks

### Implementation for User Story 1

**Constitution Requirements**:
- Data Access Layer (Principle II): Use Pydantic schemas for validation (T004-T007)
- Type Safety (Principle VII): All data crossing boundaries must be validated
- Observability (Principle IV): Add hook events for key operations
- Performance (Principle VI): <15s for job posting processing

- [X] T016 [US1] Implement rag_process_website MCP tool in apps/resume-agent/resume_agent.py (async function with url, content_type, force_refresh parameters)
- [X] T017 [US1] Add URL validation and cache checking logic in rag_process_website (check website_sources table for existing URL)
- [X] T018 [US1] Implement Playwright HTML fetching in rag_process_website (handle timeouts, 404s, robots.txt)
- [X] T019 [US1] Implement HTML to chunks conversion in rag_process_website (use HTMLHeaderTextSplitter + RecursiveCharacterTextSplitter)
- [X] T020 [US1] Implement embedding generation for all chunks in rag_process_website (batch process for performance)
- [X] T021 [US1] Implement database storage for WebsiteSource, WebsiteChunk, vectors, and FTS entries in rag_process_website
- [X] T022 [US1] Add processing status tracking (pending → processing → completed/failed) in apps/resume-agent/resume_agent.py
- [X] T023 [US1] Add error handling with user-friendly messages (invalid URL, fetch failure, processing failure) in rag_process_website
- [ ] T024 [US1] Add observability events (WebsiteProcessingStart, WebsiteProcessingComplete, WebsiteProcessingFailed) in rag_process_website
- [X] T025 [US1] Create /career:process-website slash command at .claude/commands/career-process-website.md
- [ ] T026 [US1] Implement async processing support (return immediately with status=processing for long operations) in rag_process_website
- [X] T027 [US1] Implement rag_get_website_status MCP tool for polling async operations in apps/resume-agent/resume_agent.py

**Checkpoint**: At this point, User Story 1 should be fully functional - users can process job posting URLs and get structured, queryable content

---

## Phase 4: User Story 2 - Process Career Advice Blogs and Articles (Priority: P2)

**Goal**: Extract actionable insights from career advice blogs to inform job search strategy

**Independent Test**: Provide a blog article URL and verify the system extracts key recommendations, tips, and structured advice

### Implementation for User Story 2

- [X] T028 [P] [US2] Extend rag_process_website to handle blog_article content_type in apps/resume-agent/resume_agent.py (different chunk sizes: 1000-1200 chars for English, 700-900 for Japanese)
- [ ] T029 [P] [US2] Create website-processor-agent at apps/resume-agent/.claude/agents/website-processor-agent.md for content extraction and chunking
- [ ] T030 [US2] Implement metadata extraction for blog articles (main_topics, key_insights, actionable_tips) in website-processor-agent
- [ ] T031 [US2] Add blog-specific parsing logic to handle article structure (title, sections, author, date) in website-processor-agent
- [X] T032 [US2] Update /career:process-website command to support --type=blog_article at .claude/commands/career-process-website.md
- [ ] T033 [US2] Add handling for paywalled content (graceful degradation, partial results) in rag_process_website

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - users can process job postings AND career blogs independently

---

## Phase 5: User Story 3 - Query Processed Content for Application Generation (Priority: P1)

**Goal**: Enable semantic search and retrieval across all processed content to power application generation

**Independent Test**: Pre-load sample processed content, query with questions like "What are the key requirements?" and verify relevant, accurate responses with source citations

### Implementation for User Story 3

**Constitution Requirements**:
- Source Citations (FR-006, SC-008): 100% of results must include source_url
- Performance (Principle VI): <3s for semantic queries
- Observability (Principle IV): Track query performance

- [X] T034 [US3] Implement hybrid search query function in apps/resume-agent/resume_agent.py (vector similarity + FTS keyword search with 70/30 weighted scoring)
- [X] T035 [US3] Implement rag_query_websites MCP tool in apps/resume-agent/resume_agent.py (query, max_results, content_type_filter, source_ids, include_synthesis parameters)
- [X] T036 [US3] Add query embedding generation in rag_query_websites
- [X] T037 [US3] Implement vector similarity search using sqlite-vec in rag_query_websites (top 20 results)
- [X] T038 [US3] Implement FTS keyword search using FTS5 in rag_query_websites (top 20 results)
- [X] T039 [US3] Implement hybrid score combination (vector * 0.7 + fts * 0.3) and ranking in rag_query_websites
- [X] T040 [US3] Add source citation formatting (include source_url, metadata headers) in rag_query_websites
- [X] T041 [US3] Implement confidence level calculation (high/medium/low based on top score) in rag_query_websites
- [X] T042 [US3] Add optional AI synthesis (send top 5 results to Claude for summary) in rag_query_websites
- [X] T043 [US3] Add content_type and source_id filtering in rag_query_websites
- [ ] T044 [US3] Add observability events (SemanticQueryStart, SemanticQueryComplete) in rag_query_websites
- [X] T045 [US3] Create /career:query-websites slash command at .claude/commands/career-query-websites.md
- [X] T046 [US3] Add validation for empty query and max_results range in rag_query_websites

**Checkpoint**: All P1 user stories complete - MVP ready! Users can process URLs and query content for job applications

---

## Phase 6: User Story 4 - Manage Processed Content Library (Priority: P3)

**Goal**: Allow users to view, organize, and update their library of processed websites

**Independent Test**: Process several URLs, list them, filter by date or source, verify update/delete operations work

### Implementation for User Story 4

- [X] T047 [P] [US4] Implement rag_list_websites MCP tool in apps/resume-agent/resume_agent.py (content_type, status, limit, offset, order_by parameters)
- [X] T048 [P] [US4] Implement rag_refresh_website MCP tool in apps/resume-agent/resume_agent.py (delete old chunks, re-process URL)
- [X] T049 [P] [US4] Implement rag_delete_website MCP tool in apps/resume-agent/resume_agent.py (cascading delete)
- [X] T050 [US4] Add staleness detection (>30 days) in rag_list_websites
- [X] T051 [US4] Add pagination support (limit/offset) in rag_list_websites
- [X] T052 [US4] Create /career:list-websites slash command at .claude/commands/career/list-websites.md
- [X] T053 [US4] Create /career:refresh-website slash command at .claude/commands/career/refresh-website.md
- [X] T054 [US4] Create /career:delete-website slash command at .claude/commands/career/delete-website.md
- [X] T055 [US4] Add confirmation prompt for destructive operations (delete) in /career:delete-website command

**Checkpoint**: All user stories complete - full feature ready with library management capabilities

---

## Phase 7: Integration with Existing Resume Agent Workflow

**Purpose**: Connect RAG pipeline to existing /career:apply workflow for enhanced application generation

- [X] T056 Update /career:apply slash command at .claude/commands/career-apply.md to call /career:process-website for job posting
- [X] T057 Update /career:apply to query company culture insights using /career:query-websites before generating cover letter
- [X] T058 Update resume-writer agent at apps/resume-agent/.claude/agents/resume-writer.md to accept RAG insights for tailoring
- [X] T059 Update cover-letter-writer agent at apps/resume-agent/.claude/agents/cover-letter-writer.md to incorporate company culture from RAG
- [X] T060 Update /career:analyze-job command to use RAG-extracted requirements instead of re-parsing HTML

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T061 [P] Update apps/resume-agent/README.md with RAG pipeline documentation
- [ ] T062 [P] Add performance optimization (parallel embedding generation) in apps/resume-agent/resume_agent.py
- [ ] T063 [P] Add database connection pooling for concurrent queries in apps/resume-agent/resume_agent.py
- [ ] T064 Verify all observability events are emitted correctly (test with observability server)
- [ ] T065 Run quickstart.md validation (process test URL, query, verify performance targets)
- [ ] T066 [P] Add comprehensive error messages with actionable suggestions for all failure modes
- [ ] T067 [P] Add rate limiting for Playwright fetches (respect robots.txt, avoid hammering servers)
- [ ] T068 Optimize chunk size parameters based on testing (adjust for Japanese vs English)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1) and User Story 3 (P1): Critical MVP path
  - User Story 2 (P2): Can proceed in parallel with US1/US3
  - User Story 4 (P3): Can proceed in parallel with other stories
- **Integration (Phase 7)**: Depends on User Story 1 and User Story 3 completion
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1 - Job Postings)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2 - Blog Articles)**: Extends User Story 1 (shares rag_process_website tool) but independently testable
- **User Story 3 (P1 - Query Content)**: Can start after Foundational (Phase 2) - Independent of US1/US2 but complements them
- **User Story 4 (P3 - Library Management)**: Can start after Foundational (Phase 2) - Independent of all other stories

### Critical Path for MVP

**Minimal viable product requires only:**
1. Phase 1: Setup (T001-T003)
2. Phase 2: Foundational (T004-T015)
3. Phase 3: User Story 1 - Job Postings (T016-T027)
4. Phase 5: User Story 3 - Query Content (T034-T046)
5. Phase 7: Integration (T056-T060)

This delivers the core value: process job postings → query for insights → enhance applications

### Within Each User Story

- Pydantic schemas (Phase 2) must exist before implementation
- Database tables must exist before MCP tools
- MCP tools before slash commands
- Core implementation before integration with existing workflow

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T001-T003 are independent)
- All Foundational schema definitions (T004-T007) can run in parallel
- User Story 1 (T016-T027) and User Story 3 (T034-T046) can be developed in parallel by different team members
- User Story 2 (T028-T033) can proceed in parallel with US3
- User Story 4 (T047-T055) can proceed in parallel with US2/US3
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch foundational schemas together:
Task: "Define Pydantic schema for WebsiteSource"
Task: "Define Pydantic schema for WebsiteChunk"
Task: "Define Pydantic schema for QueryResult"
Task: "Define Pydantic schema for ExtractionMetadata"

# Launch US1 observability and slash command together:
Task: "Add observability events in rag_process_website"
Task: "Create /career:process-website slash command"
```

---

## Parallel Example: Multiple User Stories

```bash
# After Foundational phase completes, launch in parallel:
Developer A: User Story 1 (T016-T027) - Job posting processing
Developer B: User Story 3 (T034-T046) - Semantic query
Developer C: User Story 2 (T028-T033) - Blog article support

# All three stories will integrate seamlessly when complete
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 3 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T015) - CRITICAL
3. Complete Phase 3: User Story 1 (T016-T027)
4. Complete Phase 5: User Story 3 (T034-T046)
5. **STOP and VALIDATE**: Test job posting processing + semantic queries
6. Complete Phase 7: Integration (T056-T060)
7. Deploy/demo MVP

**Estimated MVP Time**: 12-15 tasks, ~2-3 days for single developer

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 + User Story 3 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test blog processing → Deploy/Demo
4. Add User Story 4 → Test library management → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T015)
2. Once Foundational is done:
   - Developer A: User Story 1 (T016-T027)
   - Developer B: User Story 3 (T034-T046)
   - Developer C: User Story 2 (T028-T033)
3. Stories complete and integrate independently
4. Team completes Integration (T056-T060) together
5. Team completes Polish (T061-T068) in parallel

---

## Performance Targets Summary

| Operation | Target | Task Reference |
|-----------|--------|----------------|
| Job posting processing | <15s | T016-T021 |
| Cached URL lookup | <1s | T017 |
| Semantic query | <3s | T034-T041 |
| Library listing | <500ms | T047 |
| Refresh website | <15s | T048 |
| Delete website | <100ms | T049 |

**Constitution Compliance**: All targets meet Principle VI (Performance Standards)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests are OPTIONAL for this feature (not explicitly requested)
- All tasks follow Constitution principles (Data Access Layer, Type Safety, Observability, Performance)
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Task Count Summary

- **Total Tasks**: 68
- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 12 tasks (BLOCKING)
- **Phase 3 (User Story 1 - P1)**: 12 tasks
- **Phase 4 (User Story 2 - P2)**: 6 tasks
- **Phase 5 (User Story 3 - P1)**: 13 tasks
- **Phase 6 (User Story 4 - P3)**: 9 tasks
- **Phase 7 (Integration)**: 5 tasks
- **Phase 8 (Polish)**: 8 tasks

**MVP Tasks Only**: 15 foundational + 12 US1 + 13 US3 + 5 integration = **45 tasks**

**Parallel Opportunities**: 18 tasks marked [P] can run concurrently

---

## Suggested MVP Scope

**Recommended first delivery**: User Story 1 (Job Postings) + User Story 3 (Query Content)

This provides immediate value:
- ✅ Process job posting URLs
- ✅ Semantic search across processed content
- ✅ Enhanced /career:apply workflow with company insights
- ✅ All P1 functionality delivered

**Defer to Phase 2**: User Story 2 (Blog Articles), User Story 4 (Library Management)

---

**Format Validation**: ✅ All tasks follow checklist format (checkbox, ID, optional [P], [Story] label for user story phases, file paths included)
