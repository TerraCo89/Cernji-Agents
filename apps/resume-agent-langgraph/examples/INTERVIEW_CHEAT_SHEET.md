# Interview Cheat Sheet - LangGraph Concepts

## 🎯 Opening Statement

"I've built a production-ready Resume Agent with LangGraph that demonstrates scalable architecture patterns. It combines my game dev state machine experience with modern agent orchestration. Let me walk you through the key concepts."

---

## 📊 Core Concepts (30 seconds each)

### 1. StateGraph
**What**: Typed state that flows through the graph  
**Code**: `class ResumeState(TypedDict): ...`  
**Why**: Type safety, clear contracts, IDE autocomplete  
**Analogy**: "Like my NPC state in game dev, but with automatic state merging"

### 2. Nodes
**What**: Pure functions that transform state  
**Code**: `def node(state) -> dict: return {"field": value}`  
**Why**: Testable, composable, no side effects  
**Analogy**: "Like animation controllers—take state, return updates"

### 3. Conditional Edges
**What**: Dynamic routing based on state  
**Code**: `graph.add_conditional_edges("node", router, {"a": "a", "b": "b"})`  
**Why**: Enables loops, agent decision-making  
**Analogy**: "Animation state transitions—if health < 20, go to flee state"

### 4. Checkpointing
**What**: Pause/resume execution at any point  
**Code**: `compile(checkpointer=MemorySaver(), interrupt_before=["node"])`  
**Why**: Human-in-the-loop, debugging, A/B testing  
**Analogy**: "Save/load game state at any frame"

### 5. Subgraphs
**What**: Compiled graphs used as nodes  
**Code**: `worker = SubGraph(...).compile(); graph.add_node("worker", worker)`  
**Why**: Manager-worker pattern, modular components  
**Analogy**: "My orchestrator pattern—manager delegates to specialized sub-agents"

### 6. Parallel Execution
**What**: Dynamic fan-out to multiple nodes  
**Code**: `return [Send("worker", {...}) for item in items]`  
**Why**: Scale, speed, independent operations  
**Analogy**: "My parallel agents analyzing different parts simultaneously"

---

## 🎮 Game Dev → LangGraph Translation

| Game Dev | LangGraph | Use Case |
|----------|-----------|----------|
| FSM states | StateGraph nodes | Agent workflow |
| State transitions | Conditional edges | Dynamic routing |
| Animation controller | Node functions | State updates |
| AI behavior tree | Graph structure | Complex logic |
| Manager-worker pattern | Subgraphs | Orchestration |
| Parallel systems | Send() API | Concurrent ops |
| Save/load | Checkpointing | Human review |

---

## 🏗️ Architecture Patterns (Quick Reference)

### State Schema
```python
class ResumeState(TypedDict):
    resume_text: str                            # Input
    optimized_sections: Annotated[list, add]    # Append-only
    ats_score: int                              # Derived
```
**Key**: Use `Annotated[list, add]` for append-only (message history)

### Node Pattern
```python
def optimize_node(state: ResumeState) -> dict:
    # Read full state
    resume = state['resume_text']
    
    # Return partial updates
    return {"optimized_sections": [...], "ats_score": 95}
```
**Key**: Pure function, partial updates

### Conditional Router
```python
def should_continue(state: ResumeState) -> Literal["loop", "end"]:
    if state['ats_score'] >= 80:
        return "end"
    return "loop"
```
**Key**: Return node name based on state

### Graph Definition
```python
graph = StateGraph(ResumeState)
graph.add_node("optimize", optimize_node)
graph.add_conditional_edges("optimize", should_continue, {
    "loop": "optimize",  # Loop back
    "end": END
})
app = graph.compile(checkpointer=MemorySaver())
```
**Key**: Declarative flow, automatic persistence

---

## 💬 Interview Q&A Preparation

### Q: "How does this compare to N8N?"
**A**: "N8N is visual but stateless. LangGraph has persistent state across the entire graph, first-class loops via conditional edges, and is code-native for version control and testing."

### Q: "Why not just use the Claude SDK directly?"
**A**: "LangGraph provides built-in state management, automatic checkpointing, and graph visualization. With raw SDK, I'd have to build all that infrastructure myself."

### Q: "How do you handle human-in-the-loop?"
**A**: "I use checkpointing with `interrupt_before=['review_node']`. The graph pauses, we can inspect state, get human approval, then resume with the same thread_id. Critical for legal review."

### Q: "How would you scale this?"
**A**: "Three ways: (1) Subgraphs for specialized workers, (2) Send() for parallel execution, (3) Extract stateless tools to microservices. The modular architecture makes this straightforward."

### Q: "How do you test this?"
**A**: "Unit tests for tools (no LLM), mocked LLM responses for nodes, integration tests for full graphs. Tools are stateless so they're easy to test. Nodes are pure functions."

### Q: "What about observability?"
**A**: "I'd integrate LangSmith for tracing, add structured logging at each node, track metrics (ATS scores, iteration counts), and use checkpointing for debugging."

### Q: "How does state management work?"
**A**: "TypedDict defines the schema. Nodes return partial updates—only changed fields. LangGraph automatically merges them. Annotated[list, add] makes message history append-only."

---

## 🚀 Demo Flow (If Showing Code)

### 1. Show Structure (30 sec)
```bash
tree src/resume_agent -L 2
```
"Separation of concerns—state, nodes, tools, graphs"

### 2. Show State (30 sec)
Open: `src/resume_agent/state/schemas.py`  
"TypedDict for type safety, Annotated for append-only"

### 3. Show Node (1 min)
Open: `src/resume_agent/nodes/optimizer.py`  
"Pure function—takes full state, returns partial updates"

### 4. Show Graph (2 min)
Open: `src/resume_agent/graphs/main.py`  
"Conditional edges enable loops, checkpointing enables human review"

### 5. Show Tests (30 sec)
Open: `tests/test_tools.py`  
"Unit tests without mocking, integration tests with mocking"

---

## 🎯 Key Differentiators

**Production-Ready**:
- ✅ Type-safe with TypedDict + Pydantic
- ✅ Comprehensive testing structure
- ✅ Configuration management
- ✅ CLI interface

**Scalable**:
- ✅ Modular architecture (easy to extend)
- ✅ Subgraph support (manager-worker)
- ✅ Parallel execution ready
- ✅ Stateless tools (microservice-ready)

**Professional**:
- ✅ Separation of concerns
- ✅ Centralized prompts (version control)
- ✅ Documentation (README, ARCHITECTURE)
- ✅ Following best practices

---

## 💡 Power Phrases

- "TypedDict gives me compile-time type checking"
- "Nodes are pure functions—testable and composable"
- "Conditional edges enable the ReAct pattern"
- "Checkpointing is critical for human-in-the-loop"
- "Subgraphs map to my manager-worker orchestrators"
- "Send() enables dynamic parallelization"
- "Tools are stateless—easy to extract to services"
- "Centralized prompts enable version control and A/B testing"

---

## ⚠️ Avoid These Pitfalls

- ❌ Don't say "I just learned this yesterday"
- ❌ Don't apologize for code quality
- ❌ Don't say "I couldn't get X working"
- ❌ Don't compare negatively to other frameworks
- ✅ DO emphasize your orchestrator experience
- ✅ DO draw game dev parallels
- ✅ DO talk about production concerns

---

## 🎤 Closing Statement

"This architecture demonstrates production-ready patterns for legal AI. The modular design enables rapid iteration while maintaining quality. The human-in-the-loop checkpointing is critical for lawyer approval. And my game dev state machine experience translates directly to LangGraph's conditional routing. I'm excited to apply these patterns at LegalOn."

---

**Remember**: You're not a beginner—you're bringing orchestration expertise to a new framework. Confidence!
