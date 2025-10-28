# Database Access Patterns in LangGraph

Comprehensive guide to accessing databases from LangGraph tools and nodes, covering dependency injection, tool implementation, and state management.

## Overview

LangGraph provides multiple approaches for database access, each suited to different use cases and complexity levels. This guide covers official patterns recommended by LangGraph, practical implementation examples, and production-ready best practices.

**Last Updated:** 2025-01-28 (Based on LangGraph v0.6.0+)

---

## Official LangGraph Patterns

### 1. Runtime Context API (v0.6.0+ - Recommended)

The Context API is the modern, type-safe approach for passing immutable dependencies like database connections.

**When to use:**
- Database connections
- API clients
- Configuration objects
- User IDs and authentication tokens

**Key features:**
- Immutable throughout graph execution
- Type-safe with dataclass schema
- Automatic injection into nodes and tools
- Replaces the old `config["configurable"]` pattern

**Implementation:**

```python
from dataclasses import dataclass
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime, get_runtime
from langchain_core.tools import tool

@dataclass
class AppContext:
    """Define immutable context schema."""
    db_pool: AsyncConnectionPool
    user_id: str
    api_key: str

# Define graph with context schema
graph = StateGraph(
    state_schema=MyState,
    context_schema=AppContext  # NEW in v0.6.0
)

# Access context in nodes (receives Runtime as second parameter)
def my_node(state: MyState, runtime: Runtime[AppContext]) -> dict:
    db_pool = runtime.context.db_pool
    user_id = runtime.context.user_id
    # Use database connection
    return {"data": query_result}

# Access context in tools (use get_runtime function)
@tool
def my_tool(query: str) -> dict:
    """Tool with database access."""
    runtime = get_runtime(AppContext)
    db_pool = runtime.context.db_pool
    # Use database connection
    return {"result": data}

# Pass context at invocation
result = graph.invoke(
    {"messages": [...]},
    context={
        "db_pool": pool,
        "user_id": "user_123",
        "api_key": "sk-..."
    }
)
```

### 2. InjectedToolArg Pattern

Hide parameters from LLM's tool schema while allowing runtime injection.

**When to use:**
- User-specific database access (multi-tenant)
- Authentication/authorization
- Security-sensitive parameters
- Internal system values

**Implementation:**

```python
from typing import Annotated
from langchain_core.tools import tool, InjectedToolArg

@tool
def query_user_data(
    search_query: str,  # LLM provides this
    user_id: Annotated[str, InjectedToolArg],  # System provides this
    db_path: Annotated[str, InjectedToolArg]
) -> dict:
    """Query user-specific data.

    The user_id and db_path parameters are hidden from the LLM
    and automatically injected at runtime.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM user_data WHERE user_id = ? AND content LIKE ?",
        (user_id, f"%{search_query}%")
    )
    return cursor.fetchall()
```

### 3. RunnableConfig Pattern (Legacy)

The traditional approach using `RunnableConfig` to pass configuration.

**When to use:**
- Maintaining compatibility with existing code
- Accessing session data and thread IDs
- When Context API is not available (older LangGraph versions)

**Implementation:**

```python
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

@tool
def legacy_db_tool(query: str, config: RunnableConfig) -> dict:
    """Tool using RunnableConfig pattern."""
    # Access configurable values
    configuration = config.get("configurable", {})
    db_path = configuration.get("db_path")
    user_id = configuration.get("user_id")

    # Use database
    conn = sqlite3.connect(db_path)
    # ... query database
    return results

# Pass config at invocation
result = graph.invoke(
    {"messages": [...]},
    config={
        "configurable": {
            "thread_id": "session-1",
            "db_path": "/path/to/db.sqlite",
            "user_id": "user_123"
        }
    }
)
```

---

## Tool Implementation Patterns

### Pattern 1: Closure-Based Tools (Simple & Recommended)

Factory function creates tools with captured database connections in closure.

**Advantages:**
- Simple and lightweight
- Minimal boilerplate
- Natural Python pattern
- Connection lifecycle controlled by factory scope

**Use when:**
- Tools are stateless except for database access
- Single database connection is sufficient
- Tools are created once at application startup

**Implementation:**

```python
import sqlite3
from langchain_core.tools import tool

def create_database_tools(db_path: str) -> list:
    """Factory function that captures database connection in closure."""
    conn = sqlite3.connect(db_path, check_same_thread=False)

    @tool
    def search_users(name: str) -> list:
        """Search users by name."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE name LIKE ?", (f"%{name}%",))
        return cursor.fetchall()

    @tool
    def save_data(key: str, value: str) -> dict:
        """Save data to database."""
        cursor = conn.cursor()
        cursor.execute("INSERT INTO data (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        return {"status": "success"}

    return [search_users, save_data]

# Usage
tools = create_database_tools("app.db")
graph = create_react_agent(llm, tools)
```

### Pattern 2: Fresh Connection Per Invocation (Production-Ready)

Each tool creates and closes its own database connection.

**Advantages:**
- No connection pooling issues
- Thread-safe by default
- Proper resource cleanup
- Works well with SQLite's locking behavior

**Use when:**
- Using SQLite (limited concurrency)
- Tools may be called from different threads
- Connection overhead is acceptable
- Reliability > performance

**Implementation:**

```python
from pathlib import Path
from langchain_core.tools import tool

DB_PATH = Path(__file__).parent / "data" / "app.db"

@tool
def query_database(table: str, conditions: dict) -> list:
    """Query database with fresh connection."""
    conn = sqlite3.connect(DB_PATH)  # Fresh connection
    try:
        cursor = conn.cursor()
        # Build query safely
        query = f"SELECT * FROM {table} WHERE "
        query += " AND ".join(f"{k} = ?" for k in conditions.keys())

        cursor.execute(query, tuple(conditions.values()))
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        conn.close()  # Always cleanup

@tool
def insert_record(table: str, data: dict) -> dict:
    """Insert record with fresh connection."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        cursor.execute(query, tuple(data.values()))
        conn.commit()

        return {"status": "success", "row_id": cursor.lastrowid}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        cursor.close()
        conn.close()
```

### Pattern 3: Class-Based Tools (Advanced)

Subclass `BaseTool` for maximum control and multiple dependencies.

**Advantages:**
- Full control over initialization
- Support for both sync and async
- Easy to test with mocks
- Natural OOP pattern for complex tools
- Can validate dependencies on creation

**Use when:**
- Tools have multiple dependencies (DB, API clients, config)
- Need custom validation logic
- Tools maintain state beyond database connection
- Using connection pools or async connections

**Implementation:**

```python
from typing import Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    """Input schema for database search."""
    query: str = Field(description="Search query")
    table: str = Field(description="Table name", default="documents")
    limit: int = Field(description="Max results", default=10)

class DatabaseSearchTool(BaseTool):
    """Advanced database search tool with dependency injection."""

    name: str = "database_search"
    description: str = "Search database tables for information"
    args_schema: Type[BaseModel] = SearchInput

    # Custom dependency fields (excluded from tool schema)
    db_config: Any = Field(exclude=True)
    cache_results: bool = Field(default=False, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, db_config: DatabaseConfig, cache_results: bool = False):
        """Initialize with database configuration."""
        super().__init__()
        self.db_config = db_config
        self.cache_results = cache_results
        self._cache = {}

    def _run(self, query: str, table: str = "documents", limit: int = 10) -> list:
        """Execute database search synchronously."""
        # Check cache
        cache_key = f"{table}:{query}:{limit}"
        if self.cache_results and cache_key in self._cache:
            return self._cache[cache_key]

        # Get connection from pool
        conn = self.db_config.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {table} WHERE content LIKE ? LIMIT ?",
                (f"%{query}%", limit)
            )
            results = [dict(row) for row in cursor.fetchall()]

            # Cache results
            if self.cache_results:
                self._cache[cache_key] = results

            return results
        finally:
            cursor.close()
            conn.close()

    async def _arun(self, query: str, table: str = "documents", limit: int = 10) -> list:
        """Execute database search asynchronously."""
        # For SQLite, fallback to sync
        # For async DBs, implement true async here
        return self._run(query, table, limit)

# Usage
db_config = DatabaseConfig("app.db", use_pool=True)
tool = DatabaseSearchTool(db_config, cache_results=True)
```

---

## State Management with Database Results

### Defining State Schemas

Use TypedDict for LangGraph state schemas (NOT Pydantic).

**Why TypedDict:**
- Compatible with msgpack serialization
- Part of Python stdlib (stable)
- Better performance (no validation overhead)
- Recommended by LangGraph for production

**When to use Pydantic:**
- Only at MCP tool boundaries for validation
- Convert to dict before passing to graph

**Example:**

```python
from typing import TypedDict, Annotated, Optional, List, Dict, Any
from langgraph.graph.message import add_messages

def replace_with_latest(existing: Optional[Dict], new: Optional[Dict]) -> Optional[Dict]:
    """Custom reducer: replace existing with new."""
    return new if new is not None else existing

def append_unique_records(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    """Custom reducer: append only unique records by ID."""
    if not existing:
        return new if new else []
    if not new:
        return existing

    existing_ids = {record.get('id') for record in existing if 'id' in record}
    unique_new = [record for record in new if record.get('id') not in existing_ids]
    return existing + unique_new

class ResumeAgentState(TypedDict):
    """State schema with database query results."""

    # Conversation history (append messages)
    messages: Annotated[List[BaseMessage], add_messages]

    # Single database records (replace pattern)
    job_analysis: Annotated[Optional[Dict[str, Any]], replace_with_latest]
    master_resume: Annotated[Optional[Dict[str, Any]], replace_with_latest]

    # Collections of database records (append with deduplication)
    portfolio_examples: Annotated[List[Dict[str, Any]], append_unique_records]
    search_results: Annotated[List[Dict[str, Any]], append_unique_records]

    # Query metadata
    query_executed: Annotated[Optional[str], replace_with_latest]
    error_message: Annotated[Optional[str], replace_with_latest]
```

### Storing Query Results in State

Nodes query database and return partial state updates.

```python
def query_job_analysis_node(state: ResumeAgentState) -> dict:
    """Node that queries database and updates state."""
    try:
        job_url = extract_url_from_messages(state["messages"])

        # Query database
        conn = sqlite3.connect("app.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM job_analyses WHERE url = ?",
            (job_url,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            job_analysis = {
                "company": row["company"],
                "job_title": row["job_title"],
                "keywords": json.loads(row["keywords"]),
                "requirements": json.loads(row["requirements"])
            }

            # Return partial state update
            return {
                "job_analysis": job_analysis,
                "query_executed": "SELECT * FROM job_analyses",
                "messages": [AIMessage(content=f"Found job: {job_analysis['job_title']}")]
            }
        else:
            return {
                "error_message": "Job analysis not found",
                "messages": [AIMessage(content="No cached job analysis found.")]
            }

    except Exception as e:
        return {
            "error_message": str(e),
            "messages": [AIMessage(content=f"Database error: {str(e)}")]
        }
```

### Passing Database Data to LLM

Format database results for LLM consumption in prompts.

```python
def generate_resume_node(state: ResumeAgentState) -> dict:
    """Node that uses database results to generate LLM response."""

    job_analysis = state.get("job_analysis")
    master_resume = state.get("master_resume")

    if not job_analysis or not master_resume:
        return {
            "messages": [AIMessage(content="Missing required data.")]
        }

    # Format database data for LLM context
    prompt = f"""
Tailor this resume for the job posting:

JOB REQUIREMENTS:
Company: {job_analysis['company']}
Title: {job_analysis['job_title']}
Keywords: {', '.join(job_analysis['keywords'])}
Requirements:
{chr(10).join(f"- {req}" for req in job_analysis['requirements'])}

MASTER RESUME:
Name: {master_resume['personal_info']['name']}
Skills: {', '.join(master_resume['skills'])}
Experience:
{json.dumps(master_resume['experience'], indent=2)}

Provide a tailored resume emphasizing relevant skills and experience.
"""

    # Call LLM with formatted data
    response = llm.invoke(prompt)

    return {
        "tailored_resume": response,
        "messages": [AIMessage(content=response)]
    }
```

---

## Best Practices

### 1. Architectural Principles

**Separation of Concerns:**
- **State**: Dynamic data that changes during workflow
- **Context**: Immutable dependencies (DB connections, API keys)
- **Configuration**: Runtime metadata (thread IDs, tracing)

**Keep state minimal:**
- Store only essential data
- Use IDs/references instead of entire objects
- Avoid redundant information

### 2. Connection Management

**Never store connections in state:**
- State is serialized (connections are not serializable)
- Pass connections via Context API or create per-tool
- Store query results (data), not connections (resources)

**Connection lifecycle:**
- Context API: Pass pools at invocation time
- Fresh connections: Create and close per operation
- Class-based tools: Inject pool in __init__

### 3. Error Handling

**Tools should never raise exceptions:**
- Return error dict: `{"status": "error", "error": "message"}`
- Allows LLM to self-correct or retry
- Enables partial workflow success

**Nodes accumulate errors in state:**
```python
return {
    "error_message": error_msg,
    "errors": state.get("errors", []) + [error_msg]
}
```

### 4. Performance Optimization

**Minimize state size:**
- Serialize efficiently with TypedDict
- Keep nested structures shallow (max 2-3 levels)
- Use pagination for large datasets

**Pagination pattern:**
```python
class QueryResultsDict(TypedDict, total=False):
    results: List[Dict[str, Any]]  # Current page
    page: int
    total_pages: int
    has_more: bool
```

---

## Migration Guide: Old → New Patterns

### From config.configurable to Context API

**Old Pattern (Pre-v0.6.0):**
```python
# Define graph
graph = StateGraph(MyState)

# Access in tool
@tool
def my_tool(query: str, config: RunnableConfig) -> dict:
    db_path = config["configurable"]["db_path"]
    # ...

# Invoke
result = graph.invoke(
    state,
    config={"configurable": {"db_path": "/path/to/db.sqlite"}}
)
```

**New Pattern (v0.6.0+):**
```python
from dataclasses import dataclass
from langgraph.runtime import get_runtime

# Define context schema
@dataclass
class AppContext:
    db_path: str

# Define graph with context
graph = StateGraph(
    state_schema=MyState,
    context_schema=AppContext
)

# Access in tool
@tool
def my_tool(query: str) -> dict:
    runtime = get_runtime(AppContext)
    db_path = runtime.context.db_path
    # ...

# Invoke
result = graph.invoke(
    state,
    context={"db_path": "/path/to/db.sqlite"}
)
```

---

## References

### Official Documentation
- [LangGraph Context API](https://langchain-ai.github.io/langgraph/agents/context/) - Official guide on Context API (v0.6.0+)
- [LangGraph Graphs Reference](https://langchain-ai.github.io/langgraph/reference/graphs/) - StateGraph constructor with context_schema
- [LangChain Tool Runtime Values](https://python.langchain.com/docs/how_to/tool_runtime/) - InjectedToolArg pattern
- [LangGraph Customer Support Tutorial](https://langchain-ai.github.io/langgraph/tutorials/customer-support/customer-support/) - Real-world SQLite example

### Community Resources
- [LangGraph Discussion #1357](https://github.com/langchain-ai/langgraph/discussions/1357) - Connection pooling patterns
- [LangGraph Discussion #5023](https://github.com/langchain-ai/langgraph/issues/5023) - Context API migration
- [Forum: Dependency Injection](https://forum.langchain.com/t/dependency-injection-singleton-management/1786) - Database connection management

### Related Documentation
- See `connection-management.md` for connection pooling and lifecycle patterns
- See `testing-database-tools.md` for testing strategies and examples
- See official LangGraph docs for latest patterns: `/fetch-docs langgraph`
