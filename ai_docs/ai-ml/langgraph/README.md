# LangGraph Documentation

This directory contains comprehensive documentation for LangGraph, a framework for building stateful, multi-actor applications with LLMs, with specialized guides for database integration patterns.

## Structure

### Core Documentation

- **github-repo/** - Documentation from the LangGraph GitHub repository
  - Core concepts and tutorials
  - Getting started guides
  - State management patterns
  - Agent workflows

- **official-docs/** - Documentation from the official LangGraph website
  - API references
  - Advanced concepts
  - Checkpointing and persistence
  - Production deployment

### Database Integration Guides (NEW)

In-depth guides for production-ready database access patterns:

- **[database-access-patterns.md](database-access-patterns.md)** - Tool implementation and dependency injection
  - Context API (v0.6.0+), InjectedToolArg, RunnableConfig patterns
  - Closure-based, fresh connection, and class-based tool patterns
  - State management with database query results
  - Migration guides

- **[connection-management.md](connection-management.md)** - Connection pooling and lifecycle
  - FastAPI lifespan patterns for resource management
  - PostgreSQL connection pooling with psycopg_pool
  - SQLite threading considerations and limitations
  - Async database access patterns
  - Error handling, retries, and graceful degradation

- **[testing-database-tools.md](testing-database-tools.md)** - Testing strategies
  - Unit tests with mocked databases
  - Integration tests with in-memory SQLite
  - Async database testing with pytest-asyncio
  - CI/CD strategies and LLM response caching

## Key Concepts

LangGraph enables you to build complex AI applications by modeling workflows as graphs:

- **States** - Manage application data
- **Nodes** - Contain agent logic and processing
- **Edges** - Control flow between nodes
- **Checkpointing** - Enable persistence and time-travel debugging
- **Database Integration** - Tools and nodes that query/update databases

## Quick Reference

**When you need to:**
- **Add database tools to agent** → See `database-access-patterns.md`
- **Set up connection pooling** → See `connection-management.md` → FastAPI lifespan
- **Use async database operations** → See `connection-management.md` → Async patterns
- **Test database tools** → See `testing-database-tools.md`
- **Handle SQLite threading** → See `connection-management.md` → SQLite considerations

**Pattern Selection Guide:**
```
Production app with PostgreSQL → Context API + Connection Pool
Development with SQLite → Fresh connection per tool
Complex multi-dependency tools → Class-based tools with DI
Security-sensitive parameters → InjectedToolArg
```

## Quick Links

- Main Repository: `/langchain-ai/langgraph`
- Official Docs: https://langchain-ai.github.io/langgraph
- Trust Score: 9.2 (GitHub repo), 7.5 (official docs)
- Related Skill: `.claude/skills/langgraph-builder/` - Complete agent building guide

## Last Updated

- Official docs: Fetched from Context7 on 2025-10-23
- Database guides: Created 2025-01-28 (based on LangGraph v0.6.0+)
