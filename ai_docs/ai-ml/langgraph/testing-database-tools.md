# Testing LangGraph Database Tools

Comprehensive guide to testing LangGraph tools and nodes that access databases, including unit tests with mocks, integration tests with real databases, and CI/CD strategies.

## Overview

Testing database-connected LangGraph components requires different strategies based on test scope: unit tests with mocks for fast feedback, integration tests with real databases for confidence, and end-to-end tests for workflow validation.

**Last Updated:** 2025-01-28

---

## Testing Strategy

### Testing Pyramid

```
           E2E Tests (Slow, High Confidence)
                      /\
                     /  \
                    /    \
                   /      \
          Integration Tests (Medium Speed, Real DB)
                  /          \
                 /            \
                /              \
       Unit Tests (Fast, Mocked DB)
              /__________________\
```

**Test Distribution:**
- **Unit Tests**: 70% - Mock database, test business logic
- **Integration Tests**: 20% - In-memory database, test database interactions
- **E2E Tests**: 10% - Full workflow, cached LLM responses

---

## Unit Testing with Mocked Databases

### Strategy

Mock external dependencies at the **boundary layer**, not internal implementation details.

**Key Principles:**
- **Mock at import point**: Patch where functions are imported, not where they're defined
- **Test business logic**: Verify tool behavior with different data scenarios
- **Avoid deep mocking**: Mock the data access wrapper, not SQLite internals
- **Use fixtures**: Centralize sample data for reusability

### Pattern: Mocking Data Access Functions

```python
"""
Unit test for LangGraph tool with mocked database access.
Follows boundary mocking pattern.
"""

import pytest
from unittest.mock import patch, MagicMock

@patch("resume_agent.data_read_master_resume")
def test_load_resume_tool_success(mock_read):
    """Test load_master_resume tool with mocked database."""
    from src.resume_agent.tools.resume_parser import load_master_resume

    # Mock database response
    mock_read.return_value = {
        "status": "success",
        "data": {
            "personal_info": {
                "name": "John Doe",
                "email": "john@example.com",
            },
            "skills": ["Python", "AWS", "Docker"],
        },
    }

    # Invoke tool
    result = load_master_resume.invoke({})

    # Verify mock was called
    mock_read.assert_called_once()

    # Verify tool returns expected structure
    assert result["status"] == "success"
    assert result["data"]["personal_info"]["name"] == "John Doe"
    assert "Python" in result["data"]["skills"]


@patch("resume_agent.data_read_master_resume")
def test_load_resume_tool_error_handling(mock_read):
    """Test tool error handling when database is unavailable."""
    from src.resume_agent.tools.resume_parser import load_master_resume

    # Mock database error
    mock_read.return_value = {
        "status": "error",
        "message": "Database connection failed",
    }

    result = load_master_resume.invoke({})

    # Tool should return error status (not raise exception)
    assert result["status"] == "error"
    assert "error" in result
```

### Pattern: Mocking LangGraph Nodes

```python
"""Test LangGraph nodes with mocked database access."""

import pytest
from unittest.mock import patch
from typing import TypedDict
from typing_extensions import Annotated
from langchain_core.messages import HumanMessage, AIMessage, add_messages

class ResumeAgentState(TypedDict):
    """State schema for resume agent."""
    messages: Annotated[list, add_messages]
    master_resume: dict | None
    error_message: str | None


def load_resume_node(state: ResumeAgentState) -> dict:
    """Node that loads resume from database."""
    from src.resume_agent.data.access import load_master_resume

    try:
        resume_data = load_master_resume()
        return {
            "master_resume": resume_data,
            "messages": [AIMessage(content="Resume loaded successfully")],
        }
    except ValueError as e:
        return {
            "error_message": str(e),
            "messages": [AIMessage(content=f"Failed to load resume: {str(e)}")],
        }


@patch("resume_agent.data_read_master_resume")
def test_load_resume_node_success(mock_read):
    """Test node that loads resume with mocked database."""
    # Mock database response
    mock_read.return_value = {
        "status": "success",
        "data": {
            "personal_info": {"name": "John Doe"},
            "skills": ["Python", "AWS"],
        },
    }

    # Create initial state
    initial_state = {
        "messages": [HumanMessage(content="Load my resume")],
        "master_resume": None,
        "error_message": None,
    }

    # Invoke node
    result = load_resume_node(initial_state)

    # Verify results
    assert result["master_resume"] is not None
    assert result["master_resume"]["personal_info"]["name"] == "John Doe"
    assert len(result["messages"]) == 1
    assert "successfully" in result["messages"][0].content


@patch("resume_agent.data_read_master_resume")
def test_load_resume_node_error(mock_read):
    """Test node error handling when database is unavailable."""
    # Mock database error
    mock_read.return_value = {
        "status": "error",
        "message": "Database connection failed",
    }

    initial_state = {
        "messages": [HumanMessage(content="Load my resume")],
        "master_resume": None,
        "error_message": None,
    }

    result = load_resume_node(initial_state)

    # Verify error handling
    assert result.get("master_resume") is None
    assert result.get("error_message") is not None
    assert "Failed to load resume" in result["messages"][0].content
```

---

## Integration Testing with Real Databases

### Strategy

Use **in-memory SQLite databases** for fast, isolated integration tests.

**Key Principles:**
- **In-memory databases**: `sqlite:///:memory:` for speed and isolation
- **Session-scoped setup**: Create schema once per test session
- **Function-scoped cleanup**: Rollback or clear data after each test
- **No external dependencies**: No Postgres, no API keys needed

### Pattern: In-Memory SQLite with SQLAlchemy

```python
"""
Integration test for LangGraph node with real SQLite database.
Uses in-memory database for fast, isolated testing.
"""

import pytest
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Integer, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class ResumeData(Base):
    """Resume data table schema."""
    __tablename__ = "resume_data"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, default="default_user")
    data = Column(JSON)


class JobAnalysis(Base):
    """Job analysis table schema."""
    __tablename__ = "job_analysis"

    id = Column(Integer, primary_key=True)
    company = Column(String)
    job_title = Column(String)
    data = Column(JSON)


# ============================================================================
# SESSION-SCOPED DATABASE SETUP
# ============================================================================

@pytest.fixture(scope="session")
def sync_engine():
    """Create in-memory SQLite engine (session-scoped)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(sync_engine):
    """Create database session for each test (function-scoped)."""
    Session = sessionmaker(bind=sync_engine)
    session = Session()

    yield session

    # Cleanup: rollback and close
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def seed_resume_data(db_session):
    """Seed test resume data."""
    resume = ResumeData(
        user_id="test_user",
        data={
            "personal_info": {
                "name": "John Doe",
                "email": "john@example.com",
            },
            "skills": ["Python", "AWS", "Docker"],
        }
    )
    db_session.add(resume)
    db_session.commit()
    return resume


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_load_resume_from_real_database(db_session, seed_resume_data):
    """Test loading resume from real in-memory database."""
    # Query database directly
    resume = db_session.query(ResumeData).filter_by(user_id="test_user").first()

    assert resume is not None
    assert resume.data["personal_info"]["name"] == "John Doe"
    assert "Python" in resume.data["skills"]


def test_save_job_analysis_integration(db_session):
    """Test saving job analysis to real database."""
    job_analysis = JobAnalysis(
        company="ACME Corp",
        job_title="Senior Developer",
        data={
            "url": "https://example.com/job/123",
            "required_qualifications": ["Python", "SQL", "REST APIs"],
            "keywords": ["Python", "FastAPI", "PostgreSQL"],
            "match_score": 85,
        }
    )

    db_session.add(job_analysis)
    db_session.commit()

    # Verify saved
    saved = db_session.query(JobAnalysis).filter_by(company="ACME Corp").first()
    assert saved is not None
    assert saved.data["match_score"] == 85
    assert "Python" in saved.data["required_qualifications"]
```

### Pattern: Async Database Testing

```python
"""
Async database testing for LangGraph with AsyncSqliteSaver.
Uses pytest-asyncio for async test functions.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Column, String, Integer, JSON, select

@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """Create async in-memory SQLite engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_db_session(async_engine):
    """Create async database session for each test."""
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_async_save_job_analysis(async_db_session):
    """Test async save of job analysis."""
    job_analysis = JobAnalysis(
        company="ACME Corp",
        job_title="Senior Developer",
        data={
            "url": "https://example.com/job/123",
            "required_qualifications": ["Python", "SQL"],
            "keywords": ["Python", "FastAPI", "PostgreSQL"],
            "match_score": 85,
        }
    )

    async_db_session.add(job_analysis)
    await async_db_session.commit()

    # Verify saved
    result = await async_db_session.execute(
        select(JobAnalysis).filter_by(company="ACME Corp")
    )
    saved = result.scalar_one_or_none()

    assert saved is not None
    assert saved.data["match_score"] == 85
```

---

## Testing Complete LangGraph Workflows

### Pattern: Graph with MemorySaver

```python
"""
Test complete LangGraph workflow with MemorySaver checkpointer.
Tests graph execution with mocked tools and database access.
"""

import pytest
from unittest.mock import patch
from typing import TypedDict
from typing_extensions import Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, add_messages

class ResumeAgentState(TypedDict):
    """State schema for resume agent."""
    messages: Annotated[list, add_messages]
    master_resume: dict | None
    job_analysis: dict | None


def load_resume_node(state: ResumeAgentState) -> dict:
    """Load resume from database."""
    from src.resume_agent.data.access import load_master_resume

    try:
        resume_data = load_master_resume()
        return {
            "master_resume": resume_data,
            "messages": [AIMessage(content="Resume loaded")],
        }
    except ValueError as e:
        return {"messages": [AIMessage(content=f"Error: {str(e)}")]}


def analyze_job_node(state: ResumeAgentState) -> dict:
    """Analyze job posting."""
    return {
        "job_analysis": {"company": "ACME", "match_score": 85},
        "messages": [AIMessage(content="Job analyzed")],
    }


def create_test_graph() -> StateGraph:
    """Create test graph with two nodes."""
    graph = StateGraph(ResumeAgentState)

    graph.add_node("load_resume", load_resume_node)
    graph.add_node("analyze_job", analyze_job_node)

    graph.add_edge(START, "load_resume")
    graph.add_edge("load_resume", "analyze_job")
    graph.add_edge("analyze_job", END)

    return graph


@patch("resume_agent.data_read_master_resume")
def test_complete_workflow_with_memory_saver(mock_read):
    """Test complete workflow with MemorySaver checkpointer."""
    # Mock database
    mock_read.return_value = {
        "status": "success",
        "data": {
            "personal_info": {"name": "John Doe"},
            "skills": ["Python", "AWS"],
        },
    }

    # Compile graph with checkpointer
    checkpointer = MemorySaver()
    graph = create_test_graph().compile(checkpointer=checkpointer)

    # Initial state
    initial_state = {
        "messages": [HumanMessage(content="Analyze job for ACME")],
        "master_resume": None,
        "job_analysis": None,
    }

    # Invoke graph with thread_id
    config = {"configurable": {"thread_id": "test-thread-1"}}
    result = graph.invoke(initial_state, config=config)

    # Verify final state
    assert result["master_resume"] is not None
    assert result["master_resume"]["personal_info"]["name"] == "John Doe"
    assert result["job_analysis"] is not None
    assert result["job_analysis"]["match_score"] == 85

    # Verify message history (3 messages: human + 2 AI responses)
    assert len(result["messages"]) == 3
    assert result["messages"][0].content == "Analyze job for ACME"
    assert "Resume loaded" in result["messages"][1].content
    assert "Job analyzed" in result["messages"][2].content
```

---

## Pytest Fixtures Architecture

### Recommended conftest.py Structure

```python
"""
Enhanced conftest.py with database fixtures for testing.
Combines unit test mocks with integration test databases.
"""

import sys
import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import MagicMock, Mock
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# ============================================================================
# SESSION-SCOPED FIXTURES (EXPENSIVE SETUP)
# ============================================================================

@pytest.fixture(autouse=True, scope="session")
def mock_external_dependencies():
    """Mock external dependencies that cause import errors."""
    mock_agent = MagicMock()
    mock_agent.graph = Mock()
    mock_agent.graph.graph = Mock()

    sys.modules["agent"] = mock_agent
    sys.modules["agent.graph"] = mock_agent.graph

    yield

    if "agent" in sys.modules:
        del sys.modules["agent"]
    if "agent.graph" in sys.modules:
        del sys.modules["agent.graph"]


@pytest.fixture(scope="session")
def sync_db_engine():
    """Create in-memory SQLite engine (sync)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest_asyncio.fixture(scope="session")
async def async_db_engine():
    """Create in-memory SQLite engine (async)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ============================================================================
# FUNCTION-SCOPED FIXTURES (PER-TEST STATE)
# ============================================================================

@pytest.fixture(scope="function")
def db_session(sync_db_engine):
    """Create sync database session for each test."""
    Session = sessionmaker(bind=sync_db_engine)
    session = Session()

    yield session

    session.rollback()
    session.close()


@pytest_asyncio.fixture(scope="function")
async def async_db_session(async_db_engine):
    """Create async database session for each test."""
    AsyncSessionLocal = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


# ============================================================================
# DATA FIXTURES (IMMUTABLE TEST DATA)
# ============================================================================

@pytest.fixture(scope="session")
def sample_resume_data():
    """Sample master resume data for tests."""
    return {
        "personal_info": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123-456-7890",
        },
        "skills": ["Python", "AWS", "Docker", "Kubernetes"],
    }


@pytest.fixture(scope="session")
def sample_job_analysis():
    """Sample job analysis data for tests."""
    return {
        "company": "ACME Corp",
        "job_title": "Senior Developer",
        "url": "https://example.com/job/123",
        "required_qualifications": ["Python", "SQL", "REST APIs"],
        "keywords": ["Python", "FastAPI", "PostgreSQL"],
        "match_score": 85,
    }


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_mcp_functions():
    """Mocked MCP server data access functions."""
    from unittest.mock import Mock

    return {
        "data_read_master_resume": Mock(return_value={"status": "success", "data": {}}),
        "data_read_career_history": Mock(return_value={"status": "success", "data": {}}),
        "data_read_job_analysis": Mock(return_value={"status": "not_found"}),
        "data_search_portfolio_examples": Mock(return_value={"status": "success", "examples": []}),
    }


# ============================================================================
# SEEDED DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def seeded_resume_db(db_session, sample_resume_data):
    """Database with seeded resume data."""
    resume = ResumeData(
        user_id="test_user",
        data=sample_resume_data,
    )
    db_session.add(resume)
    db_session.commit()
    return db_session
```

---

## CI/CD Testing Strategies

### Fast Feedback Loop

```bash
# 1. Syntax validation (< 5 seconds)
python -m compileall -q .

# 2. Import validation (< 10 seconds)
pytest --collect-only -q

# 3. Unit tests (< 30 seconds)
pytest tests/unit -v

# 4. Integration tests (< 2 minutes)
pytest tests/integration -v

# 5. E2E tests (< 5 minutes)
pytest tests/e2e -v --use-cached-llm
```

### Parallel Test Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto  # Use all CPU cores
pytest -n 4     # Use 4 workers
```

### Caching LLM Responses for E2E Tests

**Pattern:**

```python
import json
from pathlib import Path

class LLMCache:
    """Cache LLM responses for deterministic E2E tests."""

    def __init__(self, cache_dir: Path = Path("tests/e2e/llm_cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, messages: list, model: str) -> str:
        """Generate cache key from messages and model."""
        import hashlib
        content = json.dumps({"messages": messages, "model": model}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, messages: list, model: str) -> str | None:
        """Get cached response if available."""
        cache_key = self.get_cache_key(messages, model)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
                return data["response"]
        return None

    def set(self, messages: list, model: str, response: str):
        """Cache LLM response."""
        cache_key = self.get_cache_key(messages, model)
        cache_file = self.cache_dir / f"{cache_key}.json"

        with open(cache_file, "w") as f:
            json.dump({"messages": messages, "model": model, "response": response}, f)


# Usage in E2E tests
@pytest.fixture(scope="session")
def llm_cache():
    """LLM response cache for E2E tests."""
    return LLMCache()


def test_e2e_with_cached_llm(llm_cache):
    """E2E test with cached LLM responses."""
    messages = [{"role": "user", "content": "Hello"}]
    model = "claude-sonnet-4"

    # Try cache first
    cached_response = llm_cache.get(messages, model)
    if cached_response:
        response = cached_response
    else:
        # Call real LLM
        response = llm.invoke(messages)
        # Cache for future runs
        llm_cache.set(messages, model, response)

    assert "hello" in response.lower()
```

---

## Best Practices

### 1. Test Organization

**Directory Structure:**
```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Fast, mocked tests
│   ├── test_data_access.py
│   ├── test_resume_parser.py
│   └── test_workflow_nodes.py
├── integration/             # Real database tests
│   ├── test_job_analysis.py
│   └── test_resume_tailoring.py
└── e2e/                     # End-to-end workflow tests
    ├── llm_cache/           # Cached LLM responses
    └── test_complete_workflow.py
```

### 2. Fixture Scope Guidelines

- **session**: Expensive setup (database schema, external mocks)
- **function**: Per-test state (database sessions, test data)
- **Use `yield` for cleanup**: Code after `yield` runs after test

### 3. Database Test Isolation

**Ensure test isolation:**
- Use in-memory databases when possible
- Rollback transactions after each test
- Clear state between tests
- Don't rely on test execution order

### 4. Mock Verification

**Verify mock calls:**
```python
# Verify called with specific args
mock_function.assert_called_with(arg1, arg2)

# Verify called once
mock_function.assert_called_once()

# Verify call count
assert mock_function.call_count == 3
```

### 5. Async Testing

**Use pytest-asyncio:**
```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result == expected
```

---

## Troubleshooting

### Issue: Import Errors in Tests

**Solution:** Add project root to Python path in conftest.py

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

### Issue: Database Locked (SQLite)

**Solution:** Use `check_same_thread=False` and shorter timeouts

```python
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False, "timeout": 5.0},
)
```

### Issue: Async Fixtures Not Working

**Solution:** Install `pytest-asyncio` and use `pytest_asyncio.fixture`

```python
import pytest_asyncio

@pytest_asyncio.fixture(scope="function")
async def async_fixture():
    # Setup
    yield value
    # Cleanup
```

### Issue: Tests Pass Individually, Fail Together

**Solution:** Ensure proper test isolation with cleanup

```python
@pytest.fixture(scope="function")
def db_session(engine):
    session = Session(bind=engine)
    yield session
    session.rollback()  # Clean up after test
    session.close()
```

---

## References

### Official Documentation
- [LangGraph Testing Documentation](https://docs.langchain.com/oss/python/langgraph/test) - Official testing patterns
- [Pytest Documentation](https://docs.pytest.org/) - pytest framework guide
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) - Async test support

### Community Resources
- [How to write tests for Langgraph Workflows](https://github.com/langchain-ai/langgraph/discussions/633) - Testing pyramid and best practices
- [Testing LLM Applications with LangChain in Django](https://lincolnloop.com/blog/avoiding-mocks-testing-llm-applications-with-langchain-in-django/) - FakeListChatModel patterns
- [How to Setup Memory Database Test with PyTest and SQLAlchemy](https://medium.com/@johnidouglasmarangon/how-to-setup-memory-database-test-with-pytest-and-sqlalchemy-ca2872a92708) - In-memory database patterns

### Project-Specific Examples
- `apps/resume-agent-langgraph/tests/unit/test_data_access.py` - Unit test examples
- `apps/resume-agent-langgraph/tests/conftest.py` - Fixture configuration
- `apps/resume-agent-langgraph/tests/integration/` - Integration test examples

### Related Documentation
- See `database-access-patterns.md` for tool implementation patterns
- See `connection-management.md` for connection pooling strategies
- See project CLAUDE.md for validation workflow: `scripts/validate-changes.ps1`
