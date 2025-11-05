# Japanese Learning Agent - LangGraph Setup Guide

This guide covers the LangGraph-based conversational agent implementation for the Japanese tutor app.

## Overview

The Japanese Learning Agent is built with LangGraph to provide:
- **Conversational Interface**: Natural chat-based interaction for learning Japanese
- **Screenshot Analysis**: OCR and translation of game screenshots
- **Vocabulary Tracking**: Persistent vocabulary database with study status
- **Flashcard Reviews**: SM-2 spaced repetition for optimal learning
- **State Persistence**: Automatic checkpointing across conversation sessions

## Version Information

**Current Versions** (Updated: 2025-11-04, Refs: DEV-50):
- **langgraph** (library): 1.0.2+
- **langgraph-api** (server): **0.5.3** ✅ **Upgraded from 0.4.46**
- **langgraph-cli**: 0.4.7
- **langgraph-checkpoint**: 3.0.1
- **langgraph-runtime-inmem**: **0.16.0** ✅ **Upgraded from 0.14.1**

### LangGraph Server v0.5.x Improvements Included

All improvements from v0.5.x server releases are now active:
- ✅ **JSON Serialization Security** (v0.5.0) - Removed JSON fallback for enhanced security
- ✅ **LangChain.js Compatibility** (v0.5.1) - Fixed persistence issues with createAgent
- ✅ **PostgreSQL Connection Retry** (v0.5.2) - Added retry logic during startup
- ✅ **Checkpoint System 3.0** - Enhanced persistence and performance
- ✅ **Performance Optimizations** - Improved checkpoint writes and database operations
- ✅ **Enhanced Error Logging** - Better troubleshooting support

### Upgrade Instructions

To upgrade to the latest LangGraph Server (if you see the "Critical support" warning):

```bash
# Upgrade langgraph-api to latest 0.5.x
pip install --upgrade "langgraph-api>=0.5.0"

# This will also upgrade related packages:
# - langgraph-runtime-inmem to 0.16.0+
# - grpcio-tools to compatible version
```

**Note**: The `langgraph-api` package is installed globally and used by `langgraph dev` command, not managed by this project's `pyproject.toml`.

See [LangGraph Server Changelog](https://docs.langchain.com/langgraph-platform/langgraph-server-changelog) for details.

## Quick Start

### 1. Install Dependencies

```bash
cd D:\source\Cernji-Agents\apps\japanese-tutor

# Install with pip
pip install -e .

# Or install with LangGraph CLI for development
pip install -e . "langgraph-cli[inmem]"
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
# Set either OPENAI_API_KEY or ANTHROPIC_API_KEY
```

Example `.env`:
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### 3. Start LangGraph Dev Server

```bash
# Start the development server with Studio UI
langgraph dev
```

This will:
- Start the LangGraph server on port 2024
- Open LangGraph Studio in your browser
- Enable real-time graph visualization and debugging

### 4. Test the Agent

In LangGraph Studio:
1. Create a new conversation thread
2. Send a message: "Analyze this screenshot: path/to/screenshot.png"
3. Watch the graph execute in real-time
4. View state updates and tool calls

## Architecture

### State Management

**State Schema**: `src/japanese_agent/state/schemas.py`

The agent maintains persistent state across conversation turns:

```python
class JapaneseAgentState(TypedDict):
    # Conversation history
    messages: List[BaseMessage]

    # Learning data
    current_screenshot: Optional[ScreenshotDict]
    vocabulary: List[VocabularyDict]
    flashcards: List[FlashcardDict]

    # Workflow control
    current_intent: Optional[WorkflowIntent]
    workflow_progress: Optional[WorkflowProgress]
    error_message: Optional[str]

    # Learning statistics
    total_vocabulary: int
    known_vocabulary: int
    review_due_count: int
```

**Custom Reducers**:
- `append_unique_vocabulary()` - Deduplicate vocabulary by id/word
- `append_unique_flashcards()` - Deduplicate flashcards by id
- `replace_with_latest()` - Always use newest value

### Graph Structure

**Main Graph**: `src/japanese_agent/graph.py`

```
START → chatbot → tools (if tool calls) → chatbot → END
              ↓
            (END if no tool calls)
```

**Key Components**:
- **Chatbot Node**: Invokes LLM with tools bound, generates responses
- **Tool Node**: Executes tool calls (OCR, vocabulary, flashcards)
- **Routing**: Conditional edges based on tool calls

### Available Tools

All tools use database persistence with async operations via `aiosqlite`.

**Screenshot Analysis** (`tools/screenshot_analyzer.py`):
- `analyze_screenshot_claude()` - Claude Vision API OCR + translation
- `analyze_screenshot_manga_ocr()` - manga-ocr specialized extraction
- `hybrid_screenshot_analysis()` - Combined approach for best results

**Vocabulary Management** (`tools/vocabulary_manager.py`) - ✅ Database-backed:
- `search_vocabulary()` - Search by Japanese text or English meaning (LIKE queries)
- `list_vocabulary_by_status()` - Filter by new/learning/reviewing/mastered/suspended
- `update_vocabulary_status()` - Update study progress with validation
- `get_vocabulary_statistics()` - Aggregate learning metrics from database

**Flashcard Management** (`tools/flashcard_manager.py`) - ✅ Database-backed with SM-2:
- `get_due_flashcards()` - Get cards due for review (indexed queries)
- `record_flashcard_review()` - Record review with full SM-2 algorithm implementation
- `create_flashcard()` - Create flashcard from vocabulary with default ease factor 2.5
- `get_review_statistics()` - Review performance metrics and completion rates

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=japanese_agent --cov-report=term-missing

# Run specific test suites
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

### Debugging with LangGraph Studio

1. **Start dev server**: `langgraph dev`
2. **Studio opens automatically** in browser
3. **Create thread** and send messages
4. **Visualize execution**:
   - See node transitions in real-time
   - Inspect state at each step
   - View tool calls and responses
5. **Time travel debugging**:
   - Edit past state
   - Rerun from specific nodes
   - Test edge cases

## Project Structure

```
apps/japanese-tutor/
├── src/japanese_agent/
│   ├── graph.py                 # Main LangGraph definition
│   ├── state/
│   │   └── schemas.py           # State TypedDict + reducers
│   ├── tools/
│   │   ├── screenshot_analyzer.py
│   │   ├── vocabulary_manager.py
│   │   └── flashcard_manager.py
│   ├── nodes/                   # Future: specialized nodes
│   └── prompts/                 # Future: prompt templates
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── contract/                # Contract tests
├── examples/                    # Usage examples
├── docs/                        # Documentation
├── langgraph.json              # LangGraph server config
├── pyproject.toml              # Dependencies
└── .env.example                # Environment template
```

## Configuration

### Environment Variables

**Required** (choose one LLM provider):
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key

**Optional**:
- `LLM_PROVIDER` - "openai" or "anthropic" (default: openai)
- `OPENAI_MODEL` - OpenAI model name (default: gpt-4o-mini)
- `ANTHROPIC_MODEL` - Anthropic model name (default: claude-sonnet-4-5)
- `DATABASE_PATH` - SQLite database path (default: ../../data/japanese_agent.db)
- `MIN_OCR_CONFIDENCE` - OCR confidence threshold (default: 0.7)
- `AUTO_FLASHCARD` - Auto-create flashcards (default: true)

### LangGraph Configuration

`langgraph.json` defines the graph:

```json
{
  "graphs": {
    "japanese_agent": "./src/japanese_agent/graph.py:graph"
  },
  "env": ".env",
  "python_version": "3.11"
}
```

## Usage Examples

### Programmatic Invocation

```python
from japanese_agent.graph import graph
from langchain_core.messages import HumanMessage

# Create initial state
initial_state = {
    "messages": [HumanMessage(content="Analyze screenshot.png")],
}

# Invoke graph with thread ID for persistence
result = graph.invoke(
    initial_state,
    config={"configurable": {"thread_id": "user-session-123"}}
)

# Access final state
print(result["messages"][-1].content)
```

### Common Workflows

**Screenshot Analysis**:
```
User: "Analyze this screenshot: /path/to/game.png"
Agent: [Calls hybrid_screenshot_analysis tool]
Agent: "I found the text: ポケモンずかん..."
      [Provides translation, vocabulary, context]
```

**Vocabulary Review**:
```
User: "Show me new vocabulary words"
Agent: [Calls list_vocabulary_by_status with status="new"]
Agent: "Here are 20 new words you've encountered..."
```

**Flashcard Study**:
```
User: "Let's review flashcards"
Agent: [Calls get_due_flashcards]
Agent: "You have 15 cards due. First card: ポケモン"
User: "Pokemon - I know this!"
Agent: [Calls record_flashcard_review with rating=3]
Agent: "Great! Next review in 6 days. Next card..."
```

## Integration with Existing Tools

The LangGraph implementation coexists with the existing tools:

- **`screenshot_watcher.py`** - Real-time screenshot translation (still functional)
- **`fastapi_server.py`** - FastAPI server (if needed)
- **MCP Server** - Can expose same tools via MCP protocol

Choose the interface that fits your workflow:
- **LangGraph**: Best for conversational learning sessions
- **Screenshot Watcher**: Best for real-time game translation
- **MCP**: Best for Claude Desktop integration

## Database Integration ✅

The vocabulary and flashcard tools now use a comprehensive SQLite database layer:

### Database Features

- **13-table schema** in `src/japanese_agent/database/schema.sql`
- **Async connection manager** with WAL mode for concurrent access
- **45+ integration tests** covering all operations
- **SM-2 algorithm** fully implemented with ease factor adjustments
- **Optimized indexes** for common queries (due flashcards, vocabulary search)
- **Data validation** with CHECK constraints and foreign key cascades

See [DATABASE_USAGE.md](DATABASE_USAGE.md) for comprehensive developer guide.

### Remaining Implementation

**OCR Integration** (screenshot_analyzer.py):
- Add Claude Vision API calls for contextual understanding
- Integrate manga-ocr library for structured text extraction
- Implement hybrid mode combining both approaches
- Store extracted text in screenshots table

### Add Specialized Nodes

Move complex workflows to dedicated nodes:

```python
# Example: Screenshot analysis workflow
graph_builder.add_node("extract_text", extract_text_node)
graph_builder.add_node("translate", translate_node)
graph_builder.add_node("extract_vocabulary", extract_vocab_node)

graph_builder.add_edge("extract_text", "translate")
graph_builder.add_edge("translate", "extract_vocabulary")
```

### Add Prompts

Create prompt templates for consistent behavior:

```python
# prompts/templates.py
SCREENSHOT_ANALYSIS_PROMPT = """
Analyze this Japanese game screenshot and provide:
1. All Japanese text found
2. Hiragana readings (furigana)
3. English translation
4. Key vocabulary with meanings
5. Context of the game scene
"""
```

## Resources

- **LangGraph Docs**: https://python.langchain.com/docs/langgraph
- **LangGraph Studio**: https://blog.langchain.dev/langgraph-studio/
- **manga-ocr**: https://github.com/kha-white/manga-ocr
- **jamdict**: https://jamdict.readthedocs.io/
- **SM-2 Algorithm**: https://www.supermemo.com/en/archives1990-2015/english/ol/sm2

## Troubleshooting

### LangGraph server won't start

**Issue**: `langgraph dev` fails with module not found

**Solution**: Ensure package is installed in editable mode:
```bash
pip install -e .
```

### Tools not executing

**Issue**: Tools are called but don't return results

**Solution**: Check tool implementation - they're currently stubs. Add actual logic or return mock data for testing.

### State not persisting

**Issue**: State resets between messages

**Solution**: Ensure you're using the same `thread_id` in config:
```python
config={"configurable": {"thread_id": "same-id-each-time"}}
```

## Contributing

When adding features:

1. **Update state schema** if adding new data fields
2. **Create tools** for LLM-accessible operations
3. **Add nodes** for complex multi-step workflows
4. **Write tests** for all new functionality
5. **Update documentation** with examples

---

**Status**:
- ✅ LangGraph structure with state management and checkpointing
- ✅ Database layer with 13-table schema and async operations
- ✅ Vocabulary and flashcard tools fully implemented
- ✅ SM-2 spaced repetition algorithm complete
- ✅ 45+ integration tests passing
- ⏳ OCR integration pending (screenshot_analyzer.py stubs)
