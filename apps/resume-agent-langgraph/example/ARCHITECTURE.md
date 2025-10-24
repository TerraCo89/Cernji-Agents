# Architecture Documentation

## Design Philosophy

This project demonstrates **production-ready LangGraph patterns** with:
- **Separation of Concerns**: Clear module boundaries
- **Type Safety**: TypedDict state schemas
- **Testability**: Pure functions, dependency injection
- **Scalability**: Modular architecture for easy extension
- **Maintainability**: Centralized configuration and prompts

---

## Project Structure

```
resume-agent-langgraph/
├── src/
│   ├── resume_agent/           # Main package
│   │   ├── state/              # State definitions (TypedDict schemas)
│   │   ├── nodes/              # Node implementations (pure functions)
│   │   ├── tools/              # Reusable utilities (stateless)
│   │   ├── graphs/             # Graph orchestration
│   │   │   └── subgraphs/      # Specialized workflows
│   │   ├── prompts/            # Centralized prompt templates
│   │   └── config.py           # Configuration management
│   └── cli.py                  # CLI entry point
├── tests/                      # Unit and integration tests
├── examples/                   # Usage examples
└── README.md
```

---

## Core Patterns

### 1. State Management

**Pattern**: Centralized State Schemas

```python
# state/schemas.py
class ResumeState(TypedDict):
    resume_text: str                                    # Input
    ats_score: int                                      # Derived
    optimized_sections: Annotated[list[dict], add]     # Append-only
```

**Why?**
- Type safety with IDE autocomplete
- Clear contracts between nodes
- Explicit state reduction strategies (`add` for append-only)
- Single source of truth for state shape

**Interview Talking Point**: "I use TypedDict for compile-time type checking. The `Annotated[list, add]` pattern ensures message history is append-only, preventing accidental overwrites—critical for audit trails in legal AI."

---

### 2. Node Design

**Pattern**: Pure Functions with Partial Updates

```python
# nodes/optimizer.py
def optimize_resume_sections(state: ResumeState) -> dict:
    """
    Pure function that:
    1. Reads from state
    2. Performs computation
    3. Returns partial updates
    """
    resume = state['resume_text']
    keywords = state['ats_keywords']
    
    # ... optimization logic ...
    
    return {
        "optimized_sections": [optimized],  # Only return changes
        "ats_score": new_score,
    }
```

**Why?**
- **Testable**: No side effects, easy to unit test
- **Composable**: Nodes can be reused in different graphs
- **Debuggable**: Clear input/output contracts
- **Scalable**: Easy to parallelize

**Interview Talking Point**: "Nodes are pure functions that accept full state but return only partial updates. This is like Redux reducers—LangGraph merges the updates back into state automatically."

---

### 3. Tools Architecture

**Pattern**: Stateless Utility Functions

```python
# tools/ats_analyzer.py
class ATSAnalyzer:
    """Stateless analyzer—doesn't depend on graph state."""
    
    def analyze_ats_compatibility(self, resume_text: str) -> Dict:
        # Pure computation
        return {...}

# Module-level instance for convenience
ats_analyzer = ATSAnalyzer()
```

**Why?**
- **Reusable**: Can be used outside graphs
- **Testable**: Unit test without graph context
- **Cacheable**: Deterministic outputs enable caching
- **Portable**: Move to microservices if needed

**Interview Talking Point**: "Tools are stateless utilities that nodes call. This separation means I can unit test ATS scoring independently, and later extract it to a microservice if we need to scale horizontally."

---

### 4. Graph Orchestration

**Pattern**: Main Graph with Conditional Routing

```python
# graphs/main.py
def create_resume_agent_graph() -> StateGraph:
    graph = StateGraph(ResumeState)
    
    # Add nodes
    graph.add_node("analyze_job", analyze_job_posting)
    graph.add_node("optimize", optimize_resume_sections)
    
    # Static edges
    graph.add_edge("analyze_job", "optimize")
    
    # Conditional edges (dynamic routing)
    graph.add_conditional_edges(
        "optimize",
        should_iterate,  # Router function
        {
            "optimize": "optimize",  # Loop back
            "validate": "validate",  # Continue
        }
    )
```

**Why?**
- **Explicit Flow**: Graph structure is visible and debuggable
- **Dynamic Routing**: Conditional edges enable agent loops
- **Checkpointing**: Built-in pause/resume for human review
- **Visualization**: Can render graph for documentation

**Interview Talking Point**: "The graph definition is declarative—you can visualize the flow. Conditional edges enable the ReAct pattern: the agent loops until it reaches the ATS score threshold or max iterations. This maps directly to my game dev FSM experience, but with automatic state persistence."

---

### 5. Configuration Management

**Pattern**: Pydantic Settings with Environment Variables

```python
# config.py
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    
    anthropic_api_key: str
    max_iterations: int = 3
    ats_score_threshold: int = 80

settings = Settings()  # Auto-loads from .env
```

**Why?**
- **Type-Safe**: Pydantic validates types
- **Environment-Aware**: Works in dev/staging/prod
- **Documented**: Settings are self-documenting
- **Testable**: Easy to override in tests

---

### 6. Prompt Engineering

**Pattern**: Centralized Prompt Templates

```python
# prompts/templates.py
JOB_ANALYSIS_PROMPT = PromptTemplate("""
You are an expert job posting analyzer.
Extract: {requirements}
""")
```

**Why?**
- **Version Control**: Prompts live with code
- **A/B Testing**: Easy to swap templates
- **Consistency**: Reuse across nodes
- **Iteration**: Change prompts without touching node logic

**Interview Talking Point**: "All prompts are centralized in one module. This is critical for legal AI—you need version control and audit trails for prompts. When we iterate on prompt engineering, we don't touch the node implementations."

---

## Scaling Patterns

### Subgraphs (Manager-Worker)

```python
# graphs/subgraphs/analysis.py
def create_clause_analyzer() -> StateGraph:
    """Worker subgraph for analyzing individual clauses."""
    graph = StateGraph(ClauseState)
    # ... build specialized workflow
    return graph

# graphs/main.py
clause_analyzer = create_clause_analyzer().compile()

def analyze_all_clauses(state):
    results = []
    for clause in state['clauses']:
        # Invoke subgraph (worker)
        result = clause_analyzer.invoke({"clause_text": clause})
        results.append(result)
    return {"analyses": results}
```

**When to Use**: 
- Specialized workflows (e.g., different analyzers for different contract types)
- Reusable components across multiple graphs
- Isolation of complex logic

---

### Parallel Execution

```python
from langgraph.types import Send

def route_to_workers(state):
    """Fan out to parallel workers."""
    return [
        Send("analyze_clause", {"clause": clause})
        for clause in state['clauses']
    ]

graph.add_conditional_edges("split", route_to_workers)
```

**When to Use**:
- Independent operations (e.g., analyzing multiple contract sections)
- I/O-bound tasks that can run concurrently
- Horizontal scaling opportunities

---

## Testing Strategy

### Unit Tests
```python
# tests/test_tools.py
def test_ats_score_calculation():
    resume = "Test content"
    result = analyze_resume_ats(resume)
    assert 0 <= result['ats_score'] <= 100
```

### Integration Tests
```python
# tests/test_graphs.py
def test_full_workflow():
    app = compile_resume_agent()
    result = app.invoke(initial_state)
    assert "final_resume" in result
```

### Mocking Strategy
```python
@pytest.fixture
def mock_llm(monkeypatch):
    def fake_invoke(messages):
        return AIMessage(content="Mocked response")
    monkeypatch.setattr(llm, "invoke", fake_invoke)
```

---

## Production Considerations

### Observability
- **Logging**: Structured logging at each node
- **Metrics**: Track ATS scores, iteration counts
- **Tracing**: LangSmith integration for debugging

### Error Handling
```python
def resilient_node(state):
    try:
        result = risky_operation(state)
        return result
    except Exception as e:
        logger.error(f"Node failed: {e}")
        return {"error": str(e)}
```

### Rate Limiting
- Use exponential backoff for API calls
- Queue long-running jobs
- Cache expensive operations

### Deployment
- **Containerization**: Dockerfile for consistent environments
- **API Service**: FastAPI wrapper for REST endpoints
- **Background Jobs**: Celery for async processing

---

## Comparison to Other Patterns

### vs N8N
| Aspect | N8N | LangGraph |
|--------|-----|-----------|
| Visual | ✅ GUI | ❌ Code |
| State | Per-node | Persistent graph state |
| Loops | Limited | First-class (conditional edges) |
| Testing | Manual | Automated unit tests |
| Version Control | JSON exports | Git-native |

### vs Raw Claude SDK
| Aspect | Raw SDK | LangGraph |
|--------|---------|-----------|
| Orchestration | Manual | Built-in |
| State | You manage | Automatic merging |
| Checkpointing | DIY | Built-in |
| Visualization | None | Graph rendering |

---

## Interview Highlights

**Technical Depth**:
- "I use TypedDict for state schemas—gives me IDE autocomplete and catches type errors at compile time"
- "Nodes are pure functions with partial updates—testable and composable"
- "Conditional edges enable the ReAct pattern—agent loops until done"

**Production Readiness**:
- "Centralized config with Pydantic Settings—works across environments"
- "All prompts in one module—version control and A/B testing"
- "Comprehensive test coverage—unit tests for tools, integration tests for graphs"

**Scalability**:
- "Subgraphs for manager-worker patterns—my orchestrator experience translates directly"
- "Send() API for parallel execution—analyze multiple contract sections simultaneously"
- "Tools are stateless—easy to extract to microservices later"

**Legal AI Specific**:
- "Human-in-the-loop checkpoints—critical for lawyer approval before finalizing"
- "Audit trails via append-only message history—required for compliance"
- "Deterministic prompt templates—reproducible outputs for legal review"

---

## Future Enhancements

1. **Multi-format support**: DOCX, PDF resume parsing
2. **Advanced RAG**: Vector store for job posting database
3. **Feedback loop**: Learn from human corrections
4. **Multi-agent**: Separate agents for analysis, optimization, validation
5. **Streaming**: Real-time progress updates to UI
6. **Caching**: Cache LLM responses for repeated analyses

---

This architecture demonstrates enterprise-grade LangGraph patterns suitable for production legal AI systems. The modular design enables rapid iteration while maintaining code quality and testability.
