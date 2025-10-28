# Database Connection Management in LangGraph

Production-ready patterns for managing database connections, pooling, lifecycle, error handling, and async operations in LangGraph applications.

## Overview

Proper connection management is critical for LangGraph applications accessing databases. This guide covers connection pooling, lifecycle management, async patterns, SQLite-specific considerations, and production error handling.

**Last Updated:** 2025-01-28

---

## Connection Lifecycle Management

### Application Lifespan Pattern (FastAPI)

The recommended pattern uses FastAPI's `lifespan` context manager for resource initialization and cleanup.

**Pattern:**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connection pool lifecycle."""

    # Startup: Create connection pool
    print("🚀 Creating connection pool...")
    pool = AsyncConnectionPool(
        conninfo="postgresql://user:pass@localhost/db",
        min_size=5,
        max_size=20,
        timeout=30.0,
        kwargs={
            "autocommit": True,  # Avoid transaction overhead
            "prepare_threshold": 0  # Disable prepared statements for pooling
        },
        open=False  # Don't open immediately
    )

    # Open pool and wait for min_size connections
    await pool.open()
    await pool.wait()  # Validates database connectivity
    print("✅ Connection pool ready")

    # Create checkpointer
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()  # Create tables (idempotent)

    # Make available to app
    app.state.pool = pool
    app.state.checkpointer = checkpointer

    yield  # Application runs

    # Shutdown: Cleanup
    print("🛑 Closing connection pool...")
    await pool.close()
    print("✅ Cleanup complete")

app = FastAPI(lifespan=lifespan)
```

### Direct Import Pattern (MCP Server Integration)

For MCP server integration, import data access functions that manage their own connections.

**Pattern:**

```python
# Data access layer manages connections
def load_master_resume() -> dict:
    """Load resume from database."""
    conn = sqlite3.connect("resume.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resumes WHERE active = 1")
        result = cursor.fetchone()
        return dict(result)
    finally:
        cursor.close()
        conn.close()

# Tools import and use data access functions
from langchain_core.tools import tool

@tool
def get_resume() -> dict:
    """Get user's resume."""
    return load_master_resume()
```

**Advantages:**
- No explicit pool management in LangGraph code
- Database connections handled by MCP server
- Lazy loading avoids initialization issues

---

## Connection Pooling Strategies

### PostgreSQL Connection Pooling (Production)

Use `psycopg_pool` for efficient connection reuse.

**Configuration:**

```python
from psycopg_pool import AsyncConnectionPool

pool = AsyncConnectionPool(
    conninfo="postgresql://user:pass@localhost:5432/db",

    # Pool sizing (rule of thumb: 2 × concurrent users)
    min_size=5,          # Maintain warm connections
    max_size=20,         # Maximum concurrent connections

    # Timeouts
    timeout=30.0,        # Max wait time for connection
    max_waiting=10,      # Queue size before rejecting requests

    # Connection settings
    kwargs={
        "autocommit": True,           # Avoid transaction overhead
        "prepare_threshold": 0,       # Disable prepared statements
        "connect_timeout": 10,        # Connection establishment timeout
        "keepalives": 1,              # Enable TCP keepalive
        "keepalives_idle": 30,        # Keepalive idle time
        "keepalives_interval": 10,    # Keepalive interval
        "keepalives_count": 5         # Keepalive retry count
    },

    # Lifecycle
    open=False  # Delay opening until pool.open() called
)

# Open and validate
await pool.open()
await pool.wait()  # Wait for min_size connections
```

**Pool Sizing Guidelines:**

| Concurrent Users | min_size | max_size |
|-----------------|----------|----------|
| 1-10            | 2        | 5        |
| 10-50           | 5        | 20       |
| 50-100          | 10       | 40       |
| 100-500         | 20       | 100      |

### SQLite Connection Patterns

SQLite has different connection requirements due to threading limitations.

**Pattern 1: Fresh Connection Per Operation (Recommended)**

```python
DB_PATH = "app.db"

@tool
def query_database(table: str) -> list:
    """Query with fresh connection."""
    conn = sqlite3.connect(DB_PATH)  # Fresh connection
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()  # Always cleanup
```

**Pattern 2: Connection Pool with Lock**

```python
from threading import Lock
from typing import ContextManager

class SQLiteConnectionPool:
    """Thread-safe SQLite connection pool."""

    def __init__(self, db_path: str, max_connections: int = 10):
        self.db_path = db_path
        self._connections = []
        self._in_use = set()
        self._lock = Lock()

        # Pre-create connections
        for _ in range(max_connections):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._connections.append(conn)

    @contextmanager
    def get_connection(self):
        """Acquire connection from pool."""
        with self._lock:
            # Find available connection
            for conn in self._connections:
                if conn not in self._in_use:
                    self._in_use.add(conn)
                    try:
                        yield conn
                    finally:
                        self._in_use.discard(conn)
                    return

            raise Exception("Connection pool exhausted")
```

### Passing Pool to Checkpointer

LangGraph checkpointers support connection pools directly (v1.0.4+).

**Pattern:**

```python
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# Create pool
pool = AsyncConnectionPool(conninfo=DB_URI, min_size=5, max_size=20)
await pool.open()

# Pass pool directly to checkpointer
checkpointer = AsyncPostgresSaver(pool)
await checkpointer.setup()

# Compile graph
graph = builder.compile(checkpointer=checkpointer)
```

**Benefits:**
- Checkpointer reuses pool connections
- Automatic connection rotation
- Avoids stale connection errors
- Improved performance under load

---

## Async Database Access

### Using Async Database Libraries

LangGraph fully supports async execution for high-performance database operations.

**Common Async Libraries:**
- **PostgreSQL**: `asyncpg`, `psycopg3 (async mode)`
- **SQLite**: `aiosqlite`
- **MongoDB**: `motor`
- **MySQL**: `aiomysql`

### Async Tool Definition

```python
import aiosqlite
from langchain_core.tools import tool

@tool
async def search_database(query: str, limit: int = 10) -> list:
    """Search database asynchronously."""
    async with aiosqlite.connect("app.db") as db:
        async with db.execute(
            "SELECT * FROM documents WHERE content LIKE ? LIMIT ?",
            (f"%{query}%", limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
```

### Async Node Implementation

```python
async def database_query_node(state: MyState) -> dict:
    """Node that queries database asynchronously."""
    async with aiosqlite.connect("app.db") as db:
        async with db.execute(
            "SELECT * FROM users WHERE id = ?",
            (state["user_id"],)
        ) as cursor:
            row = await cursor.fetchone()
            return {"user_data": dict(row) if row else None}
```

### Async Graph Invocation

**Critical:** When using async checkpointers, MUST use `ainvoke()` or `astream()`.

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# Create async checkpointer
async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)

    # Use async invocation
    result = await graph.ainvoke(initial_state, config=config)

    # OR streaming
    async for event in graph.astream(initial_state, config=config):
        print(event)
```

**Warning:** Using sync `invoke()` with async checkpointer will cause the program to hang.

### Concurrency Patterns

**Parallel Database Queries:**

```python
import asyncio

async def parallel_queries_node(state: MyState) -> dict:
    """Execute multiple database queries concurrently."""

    async def query_users():
        async with aiosqlite.connect("app.db") as db:
            async with db.execute("SELECT * FROM users") as cursor:
                return await cursor.fetchall()

    async def query_orders():
        async with aiosqlite.connect("app.db") as db:
            async with db.execute("SELECT * FROM orders") as cursor:
                return await cursor.fetchall()

    # Execute concurrently
    users, orders = await asyncio.gather(
        query_users(),
        query_orders()
    )

    return {
        "users": users,
        "orders": orders
    }
```

**Rate Limiting with Semaphore:**

```python
async def rate_limited_queries_node(state: MyState) -> dict:
    """Limit concurrent database connections."""
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent

    async def limited_query(query_id: int):
        async with semaphore:
            async with aiosqlite.connect("app.db") as db:
                async with db.execute(
                    "SELECT * FROM data WHERE id = ?",
                    (query_id,)
                ) as cursor:
                    return await cursor.fetchone()

    # Execute with rate limiting
    query_ids = range(100)
    results = await asyncio.gather(
        *[limited_query(qid) for qid in query_ids]
    )

    return {"results": results}
```

---

## SQLite-Specific Considerations

### Threading Model

SQLite has three threading modes:

1. **Single-thread**: All mutexes disabled (unsafe)
2. **Multi-thread**: Safe when no single connection used in multiple threads simultaneously
3. **Serialized** (default): Safe for multiple threads with no restrictions

### Thread Safety Patterns

**Pattern 1: check_same_thread=False with Lock**

```python
import sqlite3
from threading import Lock

# Create connection with thread checking disabled
conn = sqlite3.connect(
    "app.db",
    check_same_thread=False  # Required for multi-threaded apps
)

# Use lock to ensure thread safety
lock = Lock()

def safe_query(query: str) -> list:
    """Thread-safe database query."""
    with lock:
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results
```

**Pattern 2: Connection Per Thread**

```python
import threading
import sqlite3

# Thread-local storage for connections
thread_local = threading.local()

def get_thread_connection() -> sqlite3.Connection:
    """Get or create connection for current thread."""
    if not hasattr(thread_local, "connection"):
        thread_local.connection = sqlite3.connect("app.db")
        thread_local.connection.row_factory = sqlite3.Row
    return thread_local.connection

@tool
def query_with_thread_connection(query: str) -> list:
    """Query using thread-local connection."""
    conn = get_thread_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()
```

### WAL Mode Configuration

LangGraph's SQLite checkpointers automatically enable WAL mode for better concurrency.

**Manual Configuration:**

```python
conn = sqlite3.connect("app.db")

# Enable WAL mode (automatically by LangGraph)
conn.execute("PRAGMA journal_mode=WAL")

# Additional optimizations
conn.execute("PRAGMA synchronous=NORMAL")  # Faster writes in WAL
conn.execute("PRAGMA cache_size=-64000")   # 64MB cache
conn.execute("PRAGMA temp_store=MEMORY")   # Temp tables in memory
conn.execute("PRAGMA mmap_size=30000000000")  # 30GB memory-mapped I/O
```

### Production Limitations

**SQLite is NOT recommended for production with high concurrency:**
- Limited write concurrency (one writer at a time)
- Connection per thread overhead
- Not suitable for distributed systems

**For production, migrate to PostgreSQL:**
```python
# Development (SQLite)
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
checkpointer = AsyncSqliteSaver.from_conn_string("checkpoints.db")

# Production (PostgreSQL)
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
checkpointer = AsyncPostgresSaver(connection_pool)
```

---

## Error Handling and Resilience

### Connection Health Checks

**Pattern:**

```python
async def health_check() -> dict:
    """Check database connectivity."""
    try:
        async with connection_pool.connection() as conn:
            await conn.execute("SELECT 1")

        # Get pool statistics
        stats = connection_pool.get_stats()

        return {
            "status": "healthy",
            "database": "connected",
            "pool": {
                "size": stats.pool_size,
                "available": stats.pool_available,
                "waiting": stats.requests_waiting
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

### Retry Logic with Exponential Backoff

**Using Tenacity:**

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

class TransientDatabaseError(Exception):
    """Retryable database error."""
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=60),
    retry=retry_if_exception_type(TransientDatabaseError)
)
async def query_with_retry(query: str) -> list:
    """Query database with automatic retry."""
    try:
        async with connection_pool.connection() as conn:
            result = await conn.execute(query)
            return await result.fetchall()
    except asyncpg.exceptions.ConnectionDoesNotExistError as e:
        # Transient error - retry
        raise TransientDatabaseError(str(e)) from e
    except asyncpg.exceptions.InvalidCatalogNameError as e:
        # Permanent error - don't retry
        raise
```

### Transaction Management

**Pattern:**

```python
async def save_with_transaction(data: dict) -> dict:
    """Save data with transaction management."""
    async with connection_pool.connection() as conn:
        # Start transaction
        async with conn.transaction():
            try:
                # Multiple operations in transaction
                await conn.execute(
                    "INSERT INTO table1 (data) VALUES ($1)",
                    json.dumps(data)
                )
                await conn.execute(
                    "UPDATE table2 SET updated = NOW()"
                )

                # Commit happens automatically on exit
                return {"status": "success"}

            except Exception as e:
                # Rollback happens automatically on exception
                logger.error(f"Transaction failed: {e}")
                return {"status": "error", "error": str(e)}
```

### Graceful Degradation

**Pattern:**

```python
@tool
async def search_with_fallback(query: str) -> list:
    """Search with graceful degradation."""
    try:
        # Primary database
        async with primary_pool.connection() as conn:
            result = await conn.execute(
                "SELECT * FROM documents WHERE content LIKE $1",
                f"%{query}%"
            )
            return await result.fetchall()

    except Exception as primary_error:
        logger.warning(f"Primary database failed: {primary_error}")

        try:
            # Fallback to cache
            cached_results = await cache.get(f"search:{query}")
            if cached_results:
                return cached_results
        except Exception as cache_error:
            logger.warning(f"Cache failed: {cache_error}")

        # Return empty results (graceful degradation)
        return []
```

---

## Production Checklist

### Connection Pool Configuration

- [ ] Set appropriate `min_size` and `max_size` based on load
- [ ] Configure timeout and `max_waiting` for queue management
- [ ] Enable connection keepalive parameters
- [ ] Set `autocommit=True` for checkpointer operations
- [ ] Disable prepared statements (`prepare_threshold=0`) for pooling

### Lifecycle Management

- [ ] Use FastAPI `lifespan` for resource initialization
- [ ] Call `pool.open()` and `pool.wait()` at startup
- [ ] Call `checkpointer.setup()` to create required tables
- [ ] Implement graceful shutdown with `pool.close()`

### Error Handling

- [ ] Implement retry logic for transient errors
- [ ] Add health check endpoints
- [ ] Monitor connection pool statistics
- [ ] Log connection failures and timeouts
- [ ] Implement fallback strategies for database unavailability

### Async Patterns

- [ ] Use async tools and nodes for I/O-bound operations
- [ ] Use `ainvoke()` or `astream()` with async checkpointers
- [ ] Implement rate limiting with semaphores
- [ ] Handle concurrent queries with `asyncio.gather()`

### SQLite Specific

- [ ] Use fresh connections per operation (preferred)
- [ ] If pooling, use `check_same_thread=False` with locks
- [ ] Enable WAL mode for better concurrency
- [ ] Plan migration to PostgreSQL for production scale

---

## References

### Official Documentation
- [LangGraph Discussion #1357](https://github.com/langchain-ai/langgraph/discussions/1357) - Connection pooling patterns with FastAPI
- [LangGraph Discussion #1429](https://github.com/langchain-ai/langgraph/discussions/1429) - Passing pool directly to checkpointer
- [psycopg3 Connection Pools](https://www.psycopg.org/psycopg3/docs/advanced/pool.html) - Pool configuration and lifecycle
- [SQLite Write-Ahead Logging](https://sqlite.org/wal.html) - WAL mode benefits and configuration

### Community Resources
- [Python, SQLite, and Thread Safety](https://ricardoanderegg.com/posts/python-sqlite-thread-safety/) - Threading modes and check_same_thread
- [LangGraph with AsyncSqliteSaver + FastAPI](https://medium.com/@devwithll/simple-langgraph-implementation-with-memory-asyncsqlitesaver-checkpointer-fastapi-54f4e4879a2e) - Production patterns

### Related Documentation
- See `database-access-patterns.md` for tool implementation patterns
- See `testing-database-tools.md` for testing connection management
- See `ai_docs/ai-ml/langgraph/official-docs/checkpointing.md` for checkpoint configuration
