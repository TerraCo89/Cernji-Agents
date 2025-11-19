# LangGraph Progressive Disclosure Pattern

**Speed up development with simple, self-contained LangGraph agents**

## The Problem with Monolithic LangGraph Agents

Traditional LangGraph development often leads to:
- ❌ One massive `graph.py` file (300+ lines)
- ❌ High context window consumption
- ❌ Slow iteration (edit one workflow, reload everything)
- ❌ Difficult testing (hard to isolate workflows)

## The Solution: Self-Contained Agent Files

Apply the progressive disclosure pattern from `/prime-agentic-systems`:

```
apps/resume-agent-langgraph/src/resume_agent/graphs/
├── job_analyzer.py        # ~150 lines - Job analysis workflow
├── resume_tailor.py       # ~200 lines - Resume customization
├── cover_letter.py        # ~180 lines - Cover letter generation
├── portfolio_finder.py    # ~160 lines - GitHub code search
└── ats_scorer.py          # ~120 lines - ATS compatibility
```

Each file is a **complete, independent agent** with:
- Graph definition
- State schema
- Nodes
- Tools
- Routing logic

## Architecture: Multi-Agent Pattern

### 1. Self-Contained Graph Template

Each graph file (~150-200 lines):

```python
"""Job Analysis Agent - Analyze job postings and extract requirements."""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from typing import TypedDict, Annotated, Optional
from langchain_core.messages import AIMessage, HumanMessage

# ==============================================================================
# State Schema
# ==============================================================================

class JobAnalyzerState(TypedDict, total=False):
    """State for job analysis workflow."""
    messages: Annotated[list, "Messages in conversation"]
    job_url: Optional[str]
    job_content: Optional[str]
    job_analysis: Optional[dict]
    cached: bool
    errors: list[str]

# ==============================================================================
# Tools (embedded in this file)
# ==============================================================================

@tool
def fetch_job_posting(url: str) -> str:
    """Fetch job posting content from URL."""
    # Implementation here
    pass

# ==============================================================================
# Nodes (embedded in this file)
# ==============================================================================

def check_cache_node(state: JobAnalyzerState) -> dict:
    """Check if job analysis is cached."""
    # Implementation
    return {"cached": False}

def fetch_job_node(state: JobAnalyzerState) -> dict:
    """Fetch job posting content."""
    # Implementation
    return {"job_content": "..."}

def analyze_job_node(state: JobAnalyzerState) -> dict:
    """Analyze job posting with LLM."""
    # Implementation
    return {"job_analysis": {...}}

# ==============================================================================
# Graph Construction
# ==============================================================================

def build_job_analyzer_graph():
    """Build job analysis agent graph.

    Flow: check_cache → fetch_job → analyze_job → END
    """
    graph = StateGraph(JobAnalyzerState)

    # Add nodes
    graph.add_node("check_cache", check_cache_node)
    graph.add_node("fetch_job", fetch_job_node)
    graph.add_node("analyze_job", analyze_job_node)

    # Define flow
    graph.add_edge(START, "check_cache")
    graph.add_conditional_edges(
        "check_cache",
        lambda s: "fetch_job" if not s.get("cached") else END,
        {"fetch_job": "fetch_job", END: END}
    )
    graph.add_edge("fetch_job", "analyze_job")
    graph.add_edge("analyze_job", END)

    # Compile with checkpointing
    return graph.compile(checkpointer=MemorySaver())

# Export compiled graph
graph = build_job_analyzer_graph()
```

### 2. Expose Agents in langgraph.json

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "dependencies": [".", "./src"],
  "graphs": {
    "job_analyzer": "./src/resume_agent/graphs/job_analyzer.py:graph",
    "resume_tailor": "./src/resume_agent/graphs/resume_tailor.py:graph",
    "cover_letter": "./src/resume_agent/graphs/cover_letter.py:graph",
    "portfolio_finder": "./src/resume_agent/graphs/portfolio_finder.py:graph",
    "ats_scorer": "./src/resume_agent/graphs/ats_scorer.py:graph"
  },
  "env": ".env"
}
```

### 3. Agent Chat UI - Agent Selection

The UI can now switch between specialized agents:

```typescript
// Agent selection component
const agents = [
  { id: 'job_analyzer', name: 'Job Analyzer', icon: '🔍' },
  { id: 'resume_tailor', name: 'Resume Tailor', icon: '📝' },
  { id: 'cover_letter', name: 'Cover Letter', icon: '✉️' },
  { id: 'portfolio_finder', name: 'Portfolio Finder', icon: '💼' },
  { id: 'ats_scorer', name: 'ATS Scorer', icon: '📊' }
];

// Create thread for specific agent
const threadId = await client.threads.create({
  metadata: { agent: selectedAgent }
});

// Stream from specific agent
const stream = client.runs.stream(
  threadId,
  selectedAgent, // Agent name from langgraph.json
  { input: { messages: [{ role: "human", content: message }] } }
);
```

## Benefits vs Monolithic Approach

| Aspect | Monolithic Graph | Progressive Disclosure |
|--------|------------------|------------------------|
| File Size | 300+ lines | 150-200 lines each |
| Context Window | HIGH (load everything) | LOW (load one agent) |
| Iteration Speed | Slow (reload all) | Fast (edit one file) |
| Testing | Complex (full graph) | Simple (isolated) |
| Collaboration | Merge conflicts | Independent files |
| Production Ready | ✅ Yes | ✅ Yes |

## Implementation Strategy

### Step 1: Extract Existing Workflows

You already have modular graphs! Just expose them:

**Current structure:**
```
src/resume_agent/graphs/
├── job_analysis.py        ✅ Already exists!
├── resume_tailor.py       ✅ Already exists!
├── cover_letter.py        ✅ Already exists!
└── conversation.py        ✅ Already exists!
```

**Action:** Update `langgraph.json` to expose each graph.

### Step 2: Ensure Self-Containment

Each graph file should be independently runnable:

```python
# At the bottom of each graph file, enable standalone testing:
if __name__ == "__main__":
    # Quick test
    graph = build_job_analyzer_graph()
    result = graph.invoke(
        {"job_url": "https://example.com/job"},
        config={"configurable": {"thread_id": "test-1"}}
    )
    print(result)
```

### Step 3: Update Agent Chat UI

Add agent selection to the UI:

```typescript
// components/agent-selector.tsx
export function AgentSelector() {
  const [selectedAgent, setSelectedAgent] = useState('job_analyzer');

  return (
    <select onChange={(e) => setSelectedAgent(e.target.value)}>
      <option value="job_analyzer">🔍 Job Analyzer</option>
      <option value="resume_tailor">📝 Resume Tailor</option>
      <option value="cover_letter">✉️ Cover Letter</option>
    </select>
  );
}
```

## Progressive Disclosure in Practice

### Scenario: Adding a New Agent

**Without Progressive Disclosure** (Monolithic):
1. Open massive `graph.py` (300+ lines)
2. Add new state fields (risk breaking existing)
3. Add new nodes (scroll through file)
4. Add new routing logic (complex conditionals)
5. Test entire graph (slow feedback)

**With Progressive Disclosure:**
1. Create new file: `linkedin_optimizer.py` (~150 lines)
2. Define isolated state schema
3. Write nodes in same file
4. Build graph
5. Add one line to `langgraph.json`
6. Test isolated graph (fast feedback)

**Time saved: 80%** 🚀

### Scenario: Debugging a Workflow

**Without Progressive Disclosure:**
```bash
# Load entire graph with all workflows
pytest tests/integration/test_all_workflows.py  # 5 minutes
```

**With Progressive Disclosure:**
```bash
# Test only the workflow you're debugging
pytest tests/integration/test_job_analyzer.py   # 30 seconds
```

## Best Practices

### 1. Keep Graphs Under 200 Lines

If a graph exceeds 200 lines, split it:

```python
# TOO BIG: job_application_complete.py (400 lines)

# BETTER: Split into focused agents
# - job_analyzer.py (150 lines)
# - resume_tailor.py (180 lines)
# - cover_letter.py (160 lines)
```

### 2. Embed Dependencies

Include tools and nodes in the same file (acceptable duplication):

```python
# ✅ Good: Self-contained
# graphs/job_analyzer.py contains:
# - State schema
# - Tools
# - Nodes
# - Graph definition

# ❌ Avoid: Excessive sharing
# - Shared tool files that couple graphs
# - Complex import hierarchies
```

### 3. Use Descriptive Agent Names

```json
{
  "graphs": {
    "job_analyzer": "...",           // ✅ Clear purpose
    "resume_tailor": "...",          // ✅ Clear purpose
    "agent1": "...",                 // ❌ Unclear
    "workflow": "..."                // ❌ Too generic
  }
}
```

### 4. Add Standalone Testing

Each graph should be testable independently:

```python
# Bottom of job_analyzer.py
if __name__ == "__main__":
    import sys
    graph = build_job_analyzer_graph()

    result = graph.invoke(
        {"job_url": sys.argv[1]},
        config={"configurable": {"thread_id": "cli-test"}}
    )

    print(result["job_analysis"])
```

Run with: `python -m resume_agent.graphs.job_analyzer https://example.com/job`

## Integration with Agent Chat UI

### Multi-Agent Architecture

```
User → Agent Chat UI → LangGraph Server (port 2024)
                            ↓
                    [Multiple Agents]
                    ├── job_analyzer
                    ├── resume_tailor
                    ├── cover_letter
                    └── portfolio_finder
```

### Agent Selection Flow

1. **User selects agent** in UI dropdown
2. **UI creates thread** for that agent
3. **UI streams from specific graph** endpoint
4. **LangGraph server** loads only that graph
5. **Progressive disclosure** - minimal context consumption

### Code Example

```typescript
// lib/langgraph-client.ts
export async function createAgentThread(agentId: string) {
  const client = new Client({ apiUrl: LANGGRAPH_API_URL });

  // Create thread for specific agent
  const thread = await client.threads.create({
    metadata: {
      agent: agentId,
      created_at: new Date().toISOString()
    }
  });

  return thread.thread_id;
}

export async function streamAgentResponse(
  agentId: string,
  threadId: string,
  message: string
) {
  const client = new Client({ apiUrl: LANGGRAPH_API_URL });

  // Stream from specific agent graph
  const stream = client.runs.stream(
    threadId,
    agentId, // This is the key from langgraph.json
    {
      input: {
        messages: [{ role: "human", content: message }]
      }
    }
  );

  for await (const chunk of stream) {
    yield chunk;
  }
}
```

## Comparison: The 4 Approaches

Applied to LangGraph development:

### 1. MCP Server Wrapping CLI
**When:** External tools, multi-client support needed

```
Claude → MCP → CLI → LangGraph API
```
- ❌ Context loss on every call
- ✅ Works with any MCP client

### 2. LangGraph CLI + Scripts
**When:** Need both programmatic and CLI access

```
Claude → uv run script.py → LangGraph HTTP API
```
- ✅ Direct control, caching possible
- ⚠️ Subprocess overhead

### 3. Self-Contained Graph Files (RECOMMENDED)
**When:** Building agents for production

```
Claude → Read graph file → LangGraph Server exposes graph
```
- ✅ Progressive disclosure
- ✅ Fast iteration
- ✅ Production-ready
- ✅ Minimal context consumption

### 4. Skills (Claude Code)
**When:** Team collaboration, autonomous discovery

```
Claude (detects trigger) → Reads SKILL.md → Calls LangGraph API
```
- ✅ Git-shareable workflows
- ✅ Autonomous invocation
- ⚠️ Claude Code specific

## Migration Checklist

Transform your LangGraph development:

- [ ] Audit existing `graph.py` size (>300 lines?)
- [ ] Identify distinct workflows (job analysis, resume tailoring, etc.)
- [ ] Extract each workflow to `graphs/{workflow}.py` (~150-200 lines each)
- [ ] Ensure each graph is self-contained (state, tools, nodes in same file)
- [ ] Update `langgraph.json` to expose each graph as separate agent
- [ ] Add standalone testing (`if __name__ == "__main__"`)
- [ ] Update Agent Chat UI to support agent selection
- [ ] Test each agent independently
- [ ] Deploy to LangGraph Cloud (all agents auto-discovered)

## Success Metrics

Your LangGraph development is optimized when:

- ✅ Each graph file is 100-200 lines
- ✅ Graphs are independently testable
- ✅ Adding new agents takes <30 minutes
- ✅ Context window consumption is minimal
- ✅ Team members can work on different agents without conflicts
- ✅ UI lets users switch between specialized agents
- ✅ LangGraph server auto-discovers all agents from `langgraph.json`

## Next Steps

1. **Review existing graphs** - You already have `job_analysis.py`, `resume_tailor.py`, etc.
2. **Update langgraph.json** - Expose each graph as a separate agent
3. **Test independently** - Verify each graph works in isolation
4. **Update Agent Chat UI** - Add agent selection dropdown
5. **Deploy** - LangGraph Cloud auto-deploys all agents

## Resources

- **Current Implementation:** `apps/resume-agent-langgraph/src/resume_agent/graphs/`
- **LangGraph Multi-Agent:** https://langchain-ai.github.io/langgraph/how-tos/branching/
- **Agent Chat UI:** `apps/agent-chat-ui/`
- **Prime Agentic Systems:** `.claude/commands/prime-agentic-systems.md`

---

**Remember:** The goal is NOT to build the most sophisticated multi-agent system. The goal is to build simple, specialized agents that are fast to iterate on and maintain full conversational context.
