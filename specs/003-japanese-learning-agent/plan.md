# Implementation Plan: Japanese Learning Agent

**Branch**: `003-japanese-learning-agent` | **Date**: 2025-10-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-japanese-learning-agent/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build an MCP-based Japanese learning agent that helps users learn Japanese by analyzing game screenshots with hybrid OCR (Claude Vision API + manga-ocr), tracking vocabulary progress, and managing flashcard reviews through conversational Claude Code agents. The system follows the resume-agent architecture pattern with data-agnostic agents, centralized data access layer, and specialized slash commands under the `/japanese:` namespace. Leverages existing patterns from `apps/japanese-tutor/screenshot_watcher.py`.

## Technical Context

**Language/Version**: Python 3.10+ (matching resume-agent and existing japanese-tutor)
**Primary Dependencies**:
  - FastMCP 2.0 (MCP server framework)
  - Claude Agent SDK (agent orchestration)
  - **Hybrid OCR** (updated based on existing codebase):
    - Claude Vision API (real-time translation - existing workflow from japanese-tutor)
    - manga-ocr (structured vocabulary extraction - new workflow)
  - jamdict + jamdict-data (Japanese dictionary)
  - SQLite (database storage)
  - Pydantic (data validation)
  - UV (package manager)
  - **watchdog** (file watcher - UPDATED from watchfiles to match existing japanese-tutor)
  - anthropic SDK (already in japanese-tutor)
  - pyyaml (configuration - already in japanese-tutor)
**Storage**: SQLite with Pydantic schemas (following DAL pattern from resume-agent)
**Testing**: pytest with contract/integration/unit test hierarchy
**Target Platform**: Windows desktop (Claude Code environment)
**Project Type**: Single-app MCP server (extends apps/japanese-tutor/)
**Performance Goals**:
  - Screenshot analysis: <5s (hybrid OCR + extraction)
  - Vocabulary lookup: <2s
  - Flashcard display: <500ms
**Constraints**:
  - Offline-capable (local OCR/dictionary)
  - Single-file MCP server with PEP 723 inline dependencies
  - File watcher must work on Windows (watchdog already proven)
  - OCR accuracy >90% for clear text
  - Maintains existing real-time translation workflow
**Scale/Scope**:
  - Support 500+ unique vocabulary words
  - 20 flashcard review sessions
  - Multiple screenshots per day

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gates (Before Phase 0)

- [x] **Does this feature belong in an existing app or require a new one?**
  - Extends existing app: `apps/japanese-tutor/` - adds vocabulary tracking and flashcard features to existing screenshot translation tool

- [x] **If new app: Is the complexity justified? (Current count → new count)**
  - N/A - Extends existing japanese-tutor app rather than creating new app
  - Justification: Vocabulary tracking and flashcards are natural extensions of existing screenshot translation workflow

- [x] **Can this be achieved without adding new dependencies?**
  - Partially. New domain-specific dependencies required:
    - manga-ocr: Structured text extraction (Claude Vision API alone insufficient for vocabulary DB)
    - jamdict: Japanese dictionary lookups
    - sm-2: Spaced repetition algorithm
  - Reuses existing dependencies: watchdog, anthropic SDK, pyyaml
  - See Complexity Tracking for justification

- [x] **Does this follow the Data Access Layer pattern?**
  - Yes. Architecture mirrors resume-agent:
    - Data-agnostic agents receive data and return content
    - Centralized data access via MCP tools
    - Pydantic schema validation for all operations
    - SQLite backend with repository pattern

- [x] **Are performance requirements defined?**
  - Yes. See Technical Context:
    - Screenshot analysis: <5s
    - Vocabulary lookup: <2s
    - Flashcard display: <500ms
    - OCR accuracy: >90%

- [x] **Is observability integration planned?**
  - Yes. Will use root-level `.claude/hooks/` for event tracking
  - Events: PreToolUse, PostToolUse for all MCP tool calls
  - Integration with observability-server for real-time monitoring

### Post-Design Gates (After Phase 1)

- [x] **Are all data schemas defined with Pydantic/TypeScript types?**
  - Yes. See contracts/pydantic_models.py:
    - Screenshot (with ExtractedTextSegment nested model)
    - Vocabulary (with validation for study_status enum)
    - Flashcard (with SM-2 algorithm constraints)
    - ReviewSession (with user_response enum)
  - All models include field validation, constraints, and custom validators
  - Aligns with Constitution VII (Type Safety & Validation)

- [x] **Are contract tests planned for all interfaces?**
  - Yes. See quickstart.md testing section:
    - Contract tests: MCP tool signatures, Pydantic schema validation
    - Integration tests: Screenshot workflow, flashcard workflow, vocab tracking
    - Unit tests: OCR processing, spaced repetition, vocabulary lookup
  - Test-first development enforced (Constitution III)

- [x] **Is the implementation the simplest approach?**
  - Yes. Verified against alternatives:
    - Hybrid OCR (Vision API + manga-ocr) vs single OCR (maintains existing workflow + adds new capability)
    - watchdog over watchfiles (reuses existing, Windows-tested)
    - SM-2 over SM-17/FSRS (simpler, proven, sufficient)
    - jamdict over REST APIs (offline, simpler)
  - Extends existing app rather than creating new one
  - Reuses existing patterns from screenshot_watcher.py

- [x] **Are all dependencies justified in Complexity Tracking?**
  - Yes. See Complexity Tracking section:
    - manga-ocr, jamdict, sm-2 necessary for core functionality
    - watchdog, anthropic SDK, pyyaml already in project
    - Each new dependency has simpler alternative evaluated and rejected with rationale

**Reference**: See `.specify/memory/constitution.md` for complete principles

## Project Structure

### Documentation (this feature)

```
specs/003-japanese-learning-agent/
├── spec.md              # Feature specification (already exists)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (already exists with technology alignment)
├── data-model.md        # Phase 1 output (already exists)
├── quickstart.md        # Phase 1 output (already exists)
├── contracts/           # Phase 1 output (already exists)
│   ├── database_schema.sql
│   ├── pydantic_models.py
│   └── uv_scripts.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
apps/japanese-tutor/                  # EXTENDS EXISTING APP
├── screenshot_watcher.py             # Existing: Real-time translation with Claude Vision API
├── japanese_agent.py                 # NEW: MCP server with vocabulary tracking (PEP 723)
├── .claude/
│   ├── agents/
│   │   ├── analyze-agent.md          # Screenshot analysis & OCR orchestration (hybrid)
│   │   ├── review-agent.md           # Flashcard review workflow
│   │   ├── vocab-agent.md            # Vocabulary management
│   │   └── stats-agent.md            # Learning analytics
│   └── commands/
│       ├── analyze.md                # /japanese:analyze
│       ├── review.md                 # /japanese:review
│       ├── vocab-list.md             # /japanese:vocab-list
│       ├── vocab-stats.md            # /japanese:vocab-stats
│       └── flashcards.md             # /japanese:flashcards
├── config.yaml                       # Existing: Screenshot watcher configuration
├── prompts/
│   └── japanese_tutor.md             # Existing: Claude Vision API prompt
├── README.md                         # UPDATE: Add MCP server setup
├── CLAUDE.md                         # NEW: Agent-specific guidance
└── requirements.txt                  # UPDATE: Add new dependencies

tests/
├── contract/
│   ├── test_mcp_tools.py             # MCP tool signatures
│   └── test_schemas.py               # Pydantic schema validation
├── integration/
│   ├── test_screenshot_workflow.py   # Hybrid OCR workflow
│   ├── test_flashcard_workflow.py
│   └── test_vocab_tracking.py
└── unit/
    ├── test_ocr_processing.py        # manga-ocr integration
    ├── test_spaced_repetition.py     # SM-2 algorithm
    └── test_vocabulary_lookup.py     # jamdict integration

data/
└── japanese_agent.db                 # SQLite database (shared root-level)

screenshots/
└── [user screenshots]                # Watched directory (existing)
```

**Structure Decision**: Extends existing `apps/japanese-tutor/` app with MCP server functionality while maintaining existing screenshot watcher. The hybrid architecture supports both real-time translation (existing) and vocabulary tracking (new) workflows without breaking changes.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **New dependencies** (manga-ocr, jamdict, sm-2) | Core functionality requirements: <br>- manga-ocr: Structured OCR output with text segments, confidence scores, bounds (needed for vocabulary DB)<br>- jamdict: Japanese dictionary lookups<br>- sm-2: Spaced repetition algorithm | - Claude Vision API alone: Provides translations but no structured OCR output for database<br>- REST APIs: Require internet, violate offline requirement<br>- Custom implementations: YAGNI violation, reinventing wheel |
| **Hybrid OCR approach** (Vision API + manga-ocr) | - Vision API: Real-time translation (existing workflow, must maintain)<br>- manga-ocr: Structured extraction (new workflow, vocabulary tracking) | - Single OCR only: Would either break existing translation workflow OR not provide structured data for vocabulary DB<br>- Dual purpose needed for both real-time + database workflows |

**Justification Summary**:
- Extends existing app (no new app complexity)
- Reuses existing dependencies (watchdog, anthropic, pyyaml)
- New dependencies are minimal and domain-specific
- Hybrid OCR maintains backward compatibility while adding new capability

---

## Planning Summary

### Phase 0: Research Complete ✅

Research completed in [research.md](./research.md) with **technology alignment update**:
- **Hybrid OCR**: Claude Vision API (real-time) + manga-ocr (structured extraction)
- **File watcher**: watchdog (reuses existing, Windows-tested)
- **jamdict**: Offline Japanese dictionary (4 databases)
- **SM-2 algorithm**: Industry-standard spaced repetition (sm-2 library)

### Phase 1: Design Complete ✅

Design artifacts already generated (from previous planning run):
- [data-model.md](./data-model.md): 4-entity SQLite schema with Pydantic models
- [contracts/database_schema.sql](./contracts/database_schema.sql): SQL DDL with indexes
- [contracts/pydantic_models.py](./contracts/pydantic_models.py): Validated data models
- [contracts/uv_scripts.md](./contracts/uv_scripts.md): CLI tool specifications
- [quickstart.md](./quickstart.md): 5-minute setup guide

### Constitution Compliance ✅

**All gates passed:**
- ✅ Extends existing app (japanese-tutor) instead of creating new one
- ✅ Data Access Layer pattern followed
- ✅ Performance requirements defined (<5s OCR, <2s vocab lookup)
- ✅ Observability integration planned
- ✅ All data schemas defined with Pydantic validation
- ✅ Contract tests planned for all interfaces
- ✅ Simplest approach: Hybrid OCR maintains existing + adds new capability
- ✅ All dependencies justified in Complexity Tracking

### Technology Alignment Update (2025-10-21)

**Key Changes from Initial Plan**:
1. **File Watcher**: watchfiles → **watchdog** (matches existing japanese-tutor)
2. **OCR Strategy**: manga-ocr only → **Hybrid** (Vision API + manga-ocr)
3. **App Structure**: New app → **Extends existing** apps/japanese-tutor/

**Benefits**:
- Maintains existing real-time translation feature
- Adds vocabulary tracking without breaking changes
- Reuses proven Windows-tested patterns
- Reduces duplicate dependencies

### Next Steps

**Ready for Phase 2: Task Generation** (`/speckit.tasks`)

The planning phase is complete. All technical decisions are documented, design artifacts are ready, constitution compliance is verified, and technology stack aligns with existing codebase.

1. Run `/speckit.tasks` to generate dependency-ordered task list
2. Execute tasks in order (test-first development)
3. Follow quickstart.md for setup guidance
4. Reference contracts/ for implementation details

**Branch**: `003-japanese-learning-agent` (already checked out)
**Artifacts Location**: `specs/003-japanese-learning-agent/`

---

**Planning completed**: 2025-10-21
**Status**: Ready for implementation ✅

