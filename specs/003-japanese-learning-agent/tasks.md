# Implementation Tasks: Japanese Learning Agent

**Branch**: `003-japanese-learning-agent` | **Date**: 2025-10-21
**Feature**: Hybrid OCR-based Japanese learning with vocabulary tracking and flashcard reviews
**Architecture**: Extends `apps/japanese-tutor/` with MCP server, hybrid OCR (Vision API + manga-ocr), SQLite + Pydantic DAL

## Task Organization Strategy

**User Story Priorities** (from spec.md):
- **P1** (MVP): Screenshot Text Analysis - Hybrid OCR + translation
- **P2**: Vocabulary Tracking - Database + status management
- **P3**: Flashcard Generation - Spaced repetition reviews

**Development Approach**:
1. Test-First Development (Constitution III - NON-NEGOTIABLE)
2. Independent user story implementation (each story is testable standalone)
3. Parallel execution opportunities marked with [P]
4. Hybrid OCR maintains existing workflow + adds new capability

---

## Phase 1: Setup & Infrastructure

**Goal**: Initialize project structure, dependencies, and foundational components

### Setup Tasks

- [X] T001 Update requirements.txt with new dependencies (manga-ocr, jamdict, jamdict-data, sm-2, fastmcp) in apps/japanese-tutor/requirements.txt
- [ ] T002 Create japanese_agent.py skeleton with PEP 723 inline dependencies in apps/japanese-tutor/japanese_agent.py
- [ ] T003 Create .claude/agents/ directory structure in apps/japanese-tutor/.claude/agents/
- [ ] T004 Create .claude/commands/ directory structure in apps/japanese-tutor/.claude/commands/
- [ ] T005 [P] Create SQLite database schema file in data/japanese_agent.db (run contracts/database_schema.sql)
- [ ] T006 [P] Create CLAUDE.md agent guidance file in apps/japanese-tutor/CLAUDE.md
- [ ] T007 Update README.md with MCP server setup instructions in apps/japanese-tutor/README.md

---

## Phase 2: Foundational Layer (Test-First)

**Goal**: Implement Data Access Layer with Pydantic schemas and MCP tool infrastructure
**Blocking**: Must complete before user stories

### Contract Tests (Write First)

- [ ] T008 Write Pydantic schema validation tests in tests/contract/test_schemas.py
  - Test Screenshot schema validation
  - Test Vocabulary schema validation
  - Test Flashcard schema validation
  - Test ReviewSession schema validation

- [ ] T009 Write MCP tool signature tests in tests/contract/test_mcp_tools.py
  - Test tool parameter validation
  - Test tool return type validation
  - Test error handling contracts

### Foundational Implementation

- [ ] T010 Implement Pydantic models from contracts/pydantic_models.py in japanese_agent.py
  - Screenshot, ExtractedTextSegment
  - Vocabulary
  - Flashcard
  - ReviewSession

- [ ] T011 Implement database repository layer with Pydantic validation in japanese_agent.py
  - Base repository with WAL mode, connection pooling
  - CRUD operations with schema validation
  - Transaction handling

- [ ] T012 Initialize FastMCP server with basic configuration in japanese_agent.py
  - Server setup with transport="http"
  - Port configuration (8080)
  - Error handling middleware

---

## Phase 3: User Story 1 - Screenshot Text Analysis (P1 - MVP)

**Goal**: Hybrid OCR implementation (Vision API + manga-ocr) for real-time translation + structured extraction
**Independent Test**: Submit screenshot → receive extracted text with translations
**Delivers**: Immediate value for learners, maintains existing workflow

### US1: Contract Tests (Write First)

- [ ] T013 [US1] Write manga-ocr integration unit tests in tests/unit/test_ocr_processing.py
  - Test image preprocessing
  - Test structured text extraction
  - Test confidence score handling
  - Test error handling (corrupted images, no text)

- [ ] T014 [P] [US1] Write jamdict dictionary lookup unit tests in tests/unit/test_vocabulary_lookup.py
  - Test word lookup (kanji, hiragana, katakana)
  - Test reading extraction
  - Test meaning extraction
  - Test offline mode

- [ ] T015 [US1] Write screenshot analysis integration test in tests/integration/test_screenshot_workflow.py
  - Test hybrid OCR workflow (Vision API + manga-ocr in parallel)
  - Test text extraction + translation
  - Test database persistence
  - Test error handling (no Japanese text)

### US1: Implementation Tasks

- [ ] T016 [US1] Implement hybrid OCR service in japanese_agent.py
  - Vision API integration (reuse screenshot_watcher.py patterns)
  - manga-ocr integration for structured extraction
  - Parallel execution (Vision API + manga-ocr)
  - Result merging logic

- [ ] T017 [P] [US1] Implement jamdict dictionary service in japanese_agent.py
  - Initialize jamdict with memory_mode=True
  - Word lookup with readings and meanings
  - Caching layer for repeated lookups
  - Error handling (dictionary misses)

- [ ] T018 [US1] Implement analyze_screenshot MCP tool in japanese_agent.py
  - Accept image path parameter
  - Call hybrid OCR service
  - Call dictionary service for each word
  - Return structured analysis result
  - Save to Screenshot table

- [ ] T019 [US1] Create analyze-agent.md prompt in apps/japanese-tutor/.claude/agents/analyze-agent.md
  - Hybrid OCR orchestration instructions
  - Dictionary lookup guidance
  - Error handling procedures
  - User-friendly explanations

- [ ] T020 [US1] Create /japanese:analyze slash command in apps/japanese-tutor/.claude/commands/analyze.md
  - Command description
  - Usage examples
  - Parameter documentation

### US1: Validation

- [ ] T021 [US1] Run all US1 tests and verify they pass
- [ ] T022 [US1] Test hybrid OCR with sample game screenshot
- [ ] T023 [US1] Verify <5s response time requirement
- [ ] T024 [US1] Verify OCR accuracy >90% on clear text

---

## Phase 4: User Story 2 - Vocabulary Tracking (P2)

**Goal**: Persistent vocabulary database with study status tracking
**Independent Test**: Analyze 10 screenshots → verify vocabulary list with status
**Delivers**: Learning progress tracking, reduces cognitive load

### US2: Contract Tests (Write First)

- [ ] T025 [US2] Write vocabulary tracking integration test in tests/integration/test_vocab_tracking.py
  - Test vocabulary upsert (find or create)
  - Test encounter count increment
  - Test study status transitions (new → learning → known)
  - Test vocabulary statistics calculation

### US2: Implementation Tasks

- [ ] T026 [US2] Implement vocabulary repository operations in japanese_agent.py
  - Upsert vocabulary (UNIQUE constraint on kanji_form + hiragana_reading)
  - Update last_seen_at and encounter_count
  - Study status updates
  - Query by status (new/learning/known)

- [ ] T027 [US2] Implement MCP tools for vocabulary management in japanese_agent.py
  - get_vocabulary(vocab_id) tool
  - list_vocabulary(status_filter, limit) tool
  - update_vocab_status(vocab_id, status) tool
  - search_vocabulary(query) tool
  - get_vocab_stats() tool

- [ ] T028 [P] [US2] Create vocab-agent.md prompt in apps/japanese-tutor/.claude/agents/vocab-agent.md
  - Vocabulary listing instructions
  - Status update guidance
  - Search functionality
  - User explanations

- [ ] T029 [P] [US2] Create stats-agent.md prompt in apps/japanese-tutor/.claude/agents/stats-agent.md
  - Statistics calculation instructions
  - Progress visualization guidance
  - Learning streak logic

- [ ] T030 [US2] Create /japanese:vocab-list slash command in apps/japanese-tutor/.claude/commands/vocab-list.md
- [ ] T031 [P] [US2] Create /japanese:vocab-stats slash command in apps/japanese-tutor/.claude/commands/vocab-stats.md

- [ ] T032 [US2] Update analyze_screenshot tool to save vocabulary in japanese_agent.py
  - Extract words from OCR result
  - Upsert each word to vocabulary table
  - Update encounter counts
  - Mark new words

### US2: Validation

- [ ] T033 [US2] Run all US2 tests and verify they pass
- [ ] T034 [US2] Test vocabulary tracking with 10 screenshots
- [ ] T035 [US2] Verify <2s lookup time requirement
- [ ] T036 [US2] Verify 500+ words support without degradation

---

## Phase 5: User Story 3 - Flashcard Generation (P3)

**Goal**: Spaced repetition flashcard system with SM-2 algorithm
**Independent Test**: Create flashcards from new words → review with interval updates
**Delivers**: Long-term retention through systematic review

### US3: Contract Tests (Write First)

- [ ] T037 [US3] Write SM-2 spaced repetition unit tests in tests/unit/test_spaced_repetition.py
  - Test interval calculation
  - Test ease factor updates
  - Test review history tracking
  - Test due date calculation

- [ ] T038 [US3] Write flashcard workflow integration test in tests/integration/test_flashcard_workflow.py
  - Test flashcard creation from vocabulary
  - Test flashcard review session
  - Test SM-2 interval updates
  - Test review history persistence

### US3: Implementation Tasks

- [ ] T039 [US3] Implement SM-2 algorithm integration in japanese_agent.py
  - Initialize sm-2 Scheduler
  - Card state management (ease_factor, interval, repetitions)
  - Review calculation (quality rating → next interval)
  - JSON serialization for SQLite storage

- [ ] T040 [US3] Implement flashcard repository operations in japanese_agent.py
  - Create flashcard from vocabulary
  - Query due flashcards (next_review_at <= NOW)
  - Update flashcard state after review
  - Review session history logging

- [ ] T041 [US3] Implement MCP tools for flashcard management in japanese_agent.py
  - create_flashcard(vocab_id, screenshot_id) tool
  - get_due_flashcards(limit) tool
  - update_flashcard_review(flashcard_id, rating) tool
  - get_review_stats() tool

- [ ] T042 [P] [US3] Create review-agent.md prompt in apps/japanese-tutor/.claude/agents/review-agent.md
  - Conversational flashcard presentation
  - Feedback and encouragement
  - Adaptive explanations based on performance
  - Rating system (again/hard/good/easy)

- [ ] T043 [P] [US3] Create /japanese:review slash command in apps/japanese-tutor/.claude/commands/review.md
- [ ] T044 [P] [US3] Create /japanese:flashcards slash command in apps/japanese-tutor/.claude/commands/flashcards.md

### US3: Validation

- [ ] T045 [US3] Run all US3 tests and verify they pass
- [ ] T046 [US3] Test flashcard creation from new vocabulary
- [ ] T047 [US3] Test flashcard review session with 20 cards
- [ ] T048 [US3] Verify <1s creation time, <500ms display time
- [ ] T049 [US3] Verify SM-2 intervals update correctly

---

## Phase 6: Polish & Cross-Cutting Concerns

**Goal**: Error handling, observability, documentation, edge cases

### Error Handling & Edge Cases

- [ ] T050 [P] Implement vertical text detection handling in analyze_screenshot tool
- [ ] T051 [P] Implement furigana separation logic in OCR preprocessing
- [ ] T052 [P] Add OCR confidence threshold checks (<0.7 → warning)
- [ ] T053 Implement graceful degradation for dictionary misses (proper nouns, slang)
- [ ] T054 [P] Add retry logic for OCR failures (3 attempts, exponential backoff)

### Observability Integration

- [ ] T055 Integrate with root-level .claude/hooks/ for event tracking
  - PreToolUse events for all MCP tool calls
  - PostToolUse events with success/failure status
  - Metrics: OCR success rate, vocabulary growth, review completion

### Documentation

- [ ] T056 [P] Update README.md with complete setup guide in apps/japanese-tutor/README.md
  - MCP server installation
  - Claude Desktop configuration
  - Usage examples for all slash commands
  - Troubleshooting section

- [ ] T057 [P] Create comprehensive CLAUDE.md in apps/japanese-tutor/CLAUDE.md
  - Agent architecture overview
  - Hybrid OCR workflow explanation
  - Data Access Layer pattern
  - Development guidelines

### Final Integration Testing

- [ ] T058 End-to-end test: Screenshot → Hybrid OCR → Vocabulary → Flashcard → Review
- [ ] T059 Performance test: 100 screenshots, verify <5s average
- [ ] T060 Load test: 500+ vocabulary words, verify no degradation

---

## Dependency Graph

```
Setup & Infrastructure (Phase 1)
    ↓
Foundational Layer (Phase 2) [BLOCKING]
    ↓
    ├─→ US1: Screenshot Analysis (P1 - MVP) [INDEPENDENT]
    │       ↓
    ├─→ US2: Vocabulary Tracking (P2) [DEPENDS ON US1]
    │       ↓
    └─→ US3: Flashcard Generation (P3) [DEPENDS ON US1 + US2]
            ↓
Polish & Cross-Cutting (Phase 6)
```

**User Story Dependencies**:
- **US1** (P1): No dependencies - fully independent
- **US2** (P2): Requires US1 (needs OCR output for vocabulary extraction)
- **US3** (P3): Requires US1 + US2 (needs vocabulary DB for flashcard generation)

---

## Parallel Execution Opportunities

### Phase 1 (Setup)
- Tasks T005, T006, T007 can run in parallel (different files)

### Phase 2 (Foundational)
- T008 and T009 (test writing) can run in parallel
- After tests: T010, T011, T012 must run sequentially (dependencies)

### Phase 3 (US1)
- T013 and T014 (test writing) can run in parallel
- T016 depends on T013 passing (manga-ocr tests)
- T017 depends on T014 passing (jamdict tests)
- T019, T020 can run in parallel (documentation)

### Phase 4 (US2)
- T028, T029, T030, T031 can run in parallel (documentation)

### Phase 5 (US3)
- T037 and T038 (test writing) can run in parallel
- T042, T043, T044 can run in parallel (documentation)

### Phase 6 (Polish)
- T050, T051, T052, T054, T055, T056, T057 can run in parallel (independent concerns)

---

## Implementation Strategy

### MVP Scope (Recommended First Release)

**Phase 1 + Phase 2 + Phase 3 (US1 only)**:
- Hybrid OCR (Vision API + manga-ocr)
- Screenshot analysis with translations
- Dictionary lookups
- MCP tools + slash commands
- **Deliverable**: Fully functional screenshot translation tool with structured extraction

**Value**: Immediate assistance for learners, maintains existing workflow

### Incremental Delivery

**Release 1 (MVP)**: US1 - Screenshot Text Analysis
- Hybrid OCR workflow
- Real-time translation
- Structured vocabulary extraction (foundation for US2)

**Release 2**: US2 - Vocabulary Tracking
- Database persistence
- Study status management
- Vocabulary statistics
- Progress tracking

**Release 3**: US3 - Flashcard Generation
- SM-2 spaced repetition
- Flashcard creation
- Conversational review sessions
- Retention analytics

---

## Task Summary

**Total Tasks**: 60
- **Phase 1 (Setup)**: 7 tasks
- **Phase 2 (Foundational)**: 5 tasks (test-first)
- **Phase 3 (US1 - MVP)**: 12 tasks (4 tests + 8 implementation)
- **Phase 4 (US2)**: 12 tasks (2 tests + 10 implementation)
- **Phase 5 (US3)**: 13 tasks (3 tests + 10 implementation)
- **Phase 6 (Polish)**: 11 tasks

**Parallel Opportunities**: 19 tasks marked [P] (31.7% of total)

**Test Coverage**:
- Contract tests: 2 files (schemas, MCP tools)
- Unit tests: 3 files (OCR, spaced repetition, dictionary)
- Integration tests: 3 files (screenshot workflow, vocab tracking, flashcard workflow)
- End-to-end tests: 1 comprehensive test

**Independent Test Criteria**:
- **US1**: Submit screenshot → receive extracted text with translations (<5s)
- **US2**: Analyze 10 screenshots → verify vocabulary list with status (<2s lookup)
- **US3**: Create flashcards → review session with interval updates (<500ms display)

---

**Status**: Ready for implementation with test-first development
**Next Step**: Execute Phase 1 + Phase 2 + Phase 3 (US1) for MVP release
