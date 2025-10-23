# LangGraph Official Documentation

Source: https://langchain-ai.github.io/langgraph

This directory contains reference documentation from the official LangGraph website.

## Contents

### [Core Concepts](./core-concepts.md)
Fundamental building blocks of LangGraph:
- States, Nodes, and Edges
- State reducers and annotations
- Graph construction and compilation
- Command objects and control flow
- Special nodes (START, END, INTERRUPT)

### [Checkpointing](./checkpointing.md)
Persistence and state management:
- Checkpoint structure and operations
- Storage backends (Memory, PostgreSQL, SQLite)
- State snapshots and time-travel
- Cross-thread persistence
- Advanced checkpoint utilities

### [API Reference](./api-reference.md)
Complete API documentation:
- Core modules (graph, checkpoint, prebuilt)
- Type definitions
- Error classes
- Utility functions
- Database-specific extensions

## Key Features Covered

1. **State Management**
   - TypedDict schemas
   - Reducers and annotations
   - MessagesState prebuilt
   - Multiple state schemas

2. **Persistence**
   - In-memory checkpointing
   - PostgreSQL integration
   - SQLite storage
   - Custom checkpoint savers

3. **API Components**
   - Graph construction
   - Node definitions
   - Edge routing
   - Control flow

4. **Advanced Features**
   - Subgraphs
   - Command objects
   - Error handling
   - Async operations

## Usage Examples

Throughout these docs, you'll find examples in both Python and TypeScript for:
- Building basic chatbots
- Implementing memory
- Using tools
- Managing state
- Checkpointing conversations

## Integration

LangGraph integrates seamlessly with:
- LangChain (LLM framework)
- PostgreSQL (persistence)
- SQLite (local storage)
- Various LLM providers

## Additional Resources

- GitHub Repository: `/langchain-ai/langgraph`
- Trust Score: 7.5-9.2 (varies by source)
- Code Snippets: 4,000+ examples available

## Getting Help

For more information:
1. Review the [Core Concepts](./core-concepts.md) guide
2. Check the [API Reference](./api-reference.md)
3. Explore [Checkpointing](./checkpointing.md) for persistence
4. See [../github-repo/](../github-repo/) for tutorials

Last Updated: 2025-10-23
