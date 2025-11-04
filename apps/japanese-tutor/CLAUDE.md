# Japanese Learning Agent - Claude Code Guidance

## Purpose
This app helps you learn Japanese by analyzing game screenshots with hybrid OCR (Claude Vision API + manga-ocr), tracking vocabulary progress, and managing flashcard reviews through conversational agents.

**Two Architectures Available:**

1. **LangGraph Agent (NEW)** - Conversational learning agent
   - Full stateful conversation with checkpointing
   - LangGraph Studio integration for visualization
   - Multi-turn dialogue with context awareness
   - See [LANGGRAPH_SETUP.md](LANGGRAPH_SETUP.md) for details

2. **MCP Server** - Tool-based interface for Claude Desktop
   - Single-file MCP server with FastMCP 2.0
   - Centralized data access layer
   - Tool-based workflow

## Quick Start

### Option 1: LangGraph Agent (Recommended for Development)

```bash
cd apps/japanese-tutor
pip install -e .
langgraph dev
```

Opens LangGraph Studio for interactive development.

### Option 2: MCP Server (For Claude Desktop)

```bash
cd apps/japanese-tutor
uv run japanese_agent.py
```

Then configure Claude Desktop to connect to this MCP server.

## Project Structure

### Applications

- **japanese_agent.py** - MCP server with FastMCP 2.0
  - Single-file MCP server (UV + FastMCP + Pydantic)
  - Tech Stack: Python 3.10+, UV (Astral), FastMCP 2.0
  - Transport: HTTP Streamable (port 8080)
  - Hybrid OCR: Claude Vision API + manga-ocr

- **screenshot_watcher.py** - Existing screenshot translation tool
  - Real-time translation with Claude Vision API
  - File watcher using watchdog
  - Maintained for backward compatibility

### Agent Prompts

Located in `.claude/agents/`:
- `analyze-agent.md` - Screenshot analysis & hybrid OCR orchestration
- `vocab-agent.md` - Vocabulary management
- `stats-agent.md` - Learning analytics
- `review-agent.md` - Flashcard review workflow

### Slash Commands

Located in `.claude/commands/`:
- `/japanese:analyze` - Analyze screenshot with hybrid OCR
- `/japanese:vocab-list` - List vocabulary by status
- `/japanese:vocab-stats` - Show learning statistics
- `/japanese:review` - Start flashcard review session
- `/japanese:flashcards` - Manage flashcards

### Data Files

- **Database**: `../../data/japanese_agent.db` (SQLite)
- **Config**: `config.yaml`
- **Screenshots**: `screenshots/` directory (watched by watcher)

## Architecture: Data Access Layer

**Key Principle:** Centralized data access with Pydantic validation and SQLite persistence

### Database Layer

The app uses a comprehensive SQLite database with async operations via `aiosqlite`:

- **Location**: `src/japanese_agent/database/`
  - `connection.py` - Async connection manager with WAL mode
  - `schema.sql` - Complete 13-table database schema
  - `__init__.py` - Module exports

- **Features**:
  - **WAL Mode**: Write-Ahead Logging for concurrent read/write operations
  - **13 Tables**: Vocabulary, kanji, flashcards, reviews, screenshots, sources, tags, relationships
  - **Indexes**: Optimized for common queries (due flashcards, vocabulary search, review analytics)
  - **Constraints**: CHECK constraints for data validation, foreign key cascades
  - **Triggers**: Automatic timestamp updates on record modifications
  - **SM-2 Algorithm**: Complete spaced repetition implementation in flashcard tools

- **Tools**:
  - `src/japanese_agent/tools/vocabulary_manager.py` - Database-backed vocabulary operations
  - `src/japanese_agent/tools/flashcard_manager.py` - SM-2 flashcard scheduling with database persistence

See [DATABASE_USAGE.md](DATABASE_USAGE.md) for comprehensive developer guide.

### Agent Responsibilities

All agents are **data-agnostic** - they receive data and return content:

- **analyze-agent**: Orchestrates hybrid OCR → returns extracted text + translations
- **vocab-agent**: Manages vocabulary → returns vocabulary lists/stats
- **review-agent**: Conducts flashcard reviews → returns review results
- **stats-agent**: Calculates statistics → returns analytics

### Pydantic Data Schemas

All data is validated using Pydantic models defined in `japanese_agent.py`:

- **Screenshot** - Screenshot metadata with OCR results
- **ExtractedTextSegment** - Individual text segment from OCR
- **Vocabulary** - Japanese vocabulary entry with translations
- **Flashcard** - Flashcard for spaced repetition
- **ReviewSession** - Individual review record

These schemas ensure type safety and data consistency across all operations.

## Hybrid OCR Architecture

The system uses a hybrid approach to balance real-time translation and vocabulary tracking:

```
Screenshot detected
    ↓
    ├─→ [Existing] Claude Vision API → Real-time translation (existing workflow)
    │
    └─→ [New] manga-ocr → Vocabulary extraction → SQLite → Flashcard generation
```

**Benefits:**
- Maintains existing real-time translation feature
- Adds new vocabulary/flashcard features without breaking existing workflow
- Leverages both Claude's contextual understanding and manga-ocr's structured output

## MCP Tools (Available to Claude Desktop)

### Screenshot Analysis
1. **analyze_screenshot(image_path)** - Extract and analyze Japanese text from screenshot

### Vocabulary Management
2. **get_vocabulary(vocab_id)** - Retrieve specific vocabulary entry
3. **list_vocabulary(status_filter, limit)** - List vocabulary by study status
4. **update_vocab_status(vocab_id, status)** - Update study status (new/learning/known)
5. **search_vocabulary(query)** - Search vocabulary by text or meaning
6. **get_vocab_stats()** - Get learning statistics

### Flashcard Management
7. **create_flashcard(vocab_id, screenshot_id)** - Create flashcard from vocabulary
8. **get_due_flashcards(limit)** - Get flashcards due for review
9. **update_flashcard_review(flashcard_id, rating)** - Record review result
10. **get_review_stats()** - Get review statistics

## Development Workflow

### Adding New Agents

1. Create agent prompt in `.claude/agents/`
2. Follow data-agnostic pattern (receive data, return content)
3. No file I/O in agents (use MCP tools instead)
4. Test with sample data before integration

### Adding New Slash Commands

1. Create command file in `.claude/commands/`
2. Use existing slash command format
3. Reference appropriate agents
4. Document usage examples

### Testing

```bash
# Run all integration tests
cd apps/japanese-tutor
pytest tests/integration/ -v

# Run specific test suites
pytest tests/integration/test_database_setup.py -v      # Database schema validation
pytest tests/integration/test_vocabulary_database.py -v # Vocabulary CRUD operations
pytest tests/integration/test_flashcard_database.py -v  # Flashcard & SM-2 algorithm
pytest tests/integration/test_full_workflow.py -v       # End-to-end learning workflows
pytest tests/integration/test_graph.py -v               # LangGraph agent tests

# Run with coverage
pytest tests/integration/ --cov=src/japanese_agent --cov-report=html

# Quick validation (syntax + imports)
python -m compileall -q . && pytest --collect-only -q
```

**Test Coverage**: 45+ integration tests covering:
- Database schema creation and validation
- Vocabulary search, filtering, and status updates
- Flashcard creation and SM-2 interval calculations
- Review session recording and statistics
- Complete learning workflows with error handling
- WAL mode concurrent access verification

## Database Schema

### 13 Tables

#### Core Entities
1. **vocabulary** - Japanese vocabulary entries with readings, meanings, JLPT levels
2. **kanji** - Individual kanji characters with metadata (readings, meanings, stroke count)
3. **sources** - Content sources (games, manga, websites)
4. **screenshots** - Processed screenshots with OCR results

#### Learning System
5. **flashcards** - Spaced repetition flashcards with SM-2 scheduling
6. **review_sessions** - Individual review records with quality ratings
7. **study_goals** - User-defined learning goals and progress tracking
8. **example_sentences** - Usage examples for vocabulary entries

#### Relationships
9. **screenshot_vocabulary** - Links screenshots to extracted vocabulary
10. **vocabulary_kanji** - Links vocabulary to component kanji
11. **tags** - User-defined tags for organization
12. **vocabulary_tags** - Links vocabulary to tags

#### System
13. **_migration_backup** - Schema version tracking and migration history

### Key Relationships

```
vocabulary ←──┬── flashcards ←── review_sessions
              ├── screenshot_vocabulary ──→ screenshots
              ├── vocabulary_kanji ──→ kanji
              ├── vocabulary_tags ──→ tags
              └── example_sentences
```

### Study Status Workflow

```
new → learning → reviewing → mastered
 ↓       ↓          ↓           ↓
 ←──────┴──────────┴───────────┘ (suspended)
```

**Valid Statuses**: `new`, `learning`, `reviewing`, `mastered`, `suspended`

## SM-2 Spaced Repetition Algorithm

Flashcards use the SM-2 algorithm for optimal review scheduling:

- **Ease Factor**: Starts at 2.5, adjusted based on performance
- **Intervals**: 1 day → 6 days → (previous * ease factor)
- **Ratings**: again (0), hard (1), medium (2), easy (3)
- **Reset**: Rating below 2 resets interval to 1 day

## Performance Requirements

- Screenshot analysis: <5s (hybrid OCR + extraction)
- Vocabulary lookup: <2s
- Flashcard display: <500ms
- OCR accuracy: >90% for clear text

## Observability Integration

The agent integrates with root-level `.claude/hooks/` for event tracking:

- **PreToolUse** - Before MCP tool execution
- **PostToolUse** - After MCP tool execution
- **Metrics** - OCR success rate, vocabulary growth, review completion

## Key Design Decisions

1. **Single-file MCP server** - `japanese_agent.py` with PEP 723 inline dependencies
2. **UV package manager** - 10-100x faster than pip, auto-handles venvs
3. **FastMCP framework** - High-level MCP abstractions, decorator-based
4. **Hybrid OCR** - Claude Vision API (contextual) + manga-ocr (structured)
5. **Data Access Layer** - Centralized data access with Pydantic validation
6. **Agent Data-Agnosticism** - Agents receive data and return content (no file operations)
7. **Type Safety** - All data validated against Pydantic schemas before read/write

## Troubleshooting

### Issue: manga-ocr installation fails

**Solution**: manga-ocr requires PyTorch (~1GB download). Ensure you have sufficient disk space and a stable internet connection.

```bash
uv pip install manga-ocr
```

### Issue: Database locked error

**Solution**: Ensure WAL mode is enabled (should be automatic):

```python
conn.execute("PRAGMA journal_mode=WAL")
```

### Issue: OCR accuracy is low

**Solution**: Check image preprocessing. The system applies:
1. Grayscale conversion
2. Contrast enhancement (CLAHE)
3. Upscaling for small text (2x bicubic)

### Issue: Dictionary lookup fails

**Solution**: Ensure jamdict data is downloaded:

```bash
python -c "import jamdict; jamdict.Jamdict()"
```

This will auto-download JMDict data (~100MB) on first use.

## Project Governance

This project follows the **Cernji-Agents Constitution** (`.specify/memory/constitution.md`).

**Core Principles:**
- Multi-App Isolation (apps/ directory)
- Data Access Layer with validation
- Test-First Development (NON-NEGOTIABLE)
- Observability by Default
- Type Safety & Validation
- Simplicity & YAGNI

## Contributing

When making changes:

1. **Follow constitution principles** - Check gates before implementation
2. **Test-first development** - Write tests before code
3. **Update documentation** - Keep CLAUDE.md and README.md in sync
4. **Validate schemas** - Ensure Pydantic models are updated
5. **Run full test suite** - All tests must pass before commit

## References

### Internal Documentation

- **Database Usage Guide**: [DATABASE_USAGE.md](DATABASE_USAGE.md) - Comprehensive database developer guide
- **LangGraph Setup**: [LANGGRAPH_SETUP.md](LANGGRAPH_SETUP.md) - LangGraph agent configuration
- **Specification**: `specs/003-japanese-learning-agent/spec.md`
- **Implementation Plan**: `specs/003-japanese-learning-agent/plan.md`
- **Research**: `specs/003-japanese-learning-agent/research.md`
- **Data Model**: `specs/003-japanese-learning-agent/data-model.md`
- **Contracts**: `specs/003-japanese-learning-agent/contracts/`
- **Constitution**: `.specify/memory/constitution.md`

### External Documentation

- [manga-ocr](https://github.com/kha-white/manga-ocr) - OCR for Japanese manga/game text
- [jamdict](https://jamdict.readthedocs.io/) - Japanese dictionary library
- [SM-2 Algorithm](https://www.supermemo.com/en/archives1990-2015/english/ol/sm2) - Spaced repetition algorithm
- [FastMCP Documentation](https://github.com/anthropics/fastmcp) - MCP server framework
- [Pydantic V2](https://docs.pydantic.dev/latest/) - Data validation library
- [aiosqlite](https://aiosqlite.omnilib.dev/) - Async SQLite library
- [SQLite WAL Mode](https://www.sqlite.org/wal.html) - Write-Ahead Logging documentation

## License

See repository root for license information.
