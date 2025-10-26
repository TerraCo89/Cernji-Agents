# MCP vs LangGraph Architecture Comparison

**Phase 1 Deliverable**: Comparison of MCP server and LangGraph implementations

**Created**: 2025-10-26

---

## Overview

This document compares the architectural differences between the original **MCP (Model Context Protocol) server** implementation and the new **LangGraph-based** implementation of the Resume Agent.

### Purpose

Understanding these differences helps guide the migration strategy and ensures we preserve the strengths of the MCP implementation while gaining LangGraph's benefits.

---

## High-Level Comparison

| Aspect | MCP Server | LangGraph |
|--------|------------|-----------|
| **Primary Use Case** | Tool exposure to Claude Desktop | Conversational agent with state |
| **Execution Model** | Request/response (stateless) | State graph with checkpointing |
| **Client Integration** | Claude Desktop, MCP clients | Web UI, API clients, LangGraph Studio |
| **State Management** | Implicit (database + context) | Explicit (StateGraph + SqliteSaver) |
| **Conversation Flow** | Claude manages context | Graph manages state transitions |
| **Deployment** | Single-file MCP server | FastAPI + LangGraph server |

---

## Detailed Comparison

### 1. Execution Model

#### MCP Server

```python
# Stateless request/response
@mcp.tool()
def analyze_job(job_url: str) -> dict:
    """Analyze job posting - single operation"""

    # Fetch job
    html = fetch_url(job_url)

    # Process with LLM
    analysis = llm.invoke(build_prompt(html))

    # Save to database
    save_job_analysis(analysis)

    # Return result
    return {
        "status": "success",
        "data": analysis
    }
```

**Characteristics**:
- Single function call = single operation
- No built-in state between calls
- Claude Desktop manages conversation context
- Tool is triggered by Claude's function calling

**Flow**:
```
User → Claude Desktop → MCP Tool → Database → Response → Claude → User
```

---

#### LangGraph

```python
# Stateful graph execution
from langgraph.graph import StateGraph

# Define workflow graph
workflow = StateGraph(ResumeAgentState)

# Add nodes
workflow.add_node("analyze_job", analyze_job_node)
workflow.add_node("tailor_resume", tailor_resume_node)
workflow.add_node("cover_letter", cover_letter_node)

# Add edges
workflow.add_edge("analyze_job", "tailor_resume")
workflow.add_edge("tailor_resume", "cover_letter")

# Compile with checkpointer
app = workflow.compile(checkpointer=SqliteSaver.from_conn_string("checkpoints.db"))

# Execute with state persistence
result = app.invoke(
    initial_state,
    config={"configurable": {"thread_id": "session-123"}}
)
```

**Characteristics**:
- Graph of interconnected nodes
- State persists across nodes via checkpointer
- Supports multi-step workflows with branching
- Can be interrupted and resumed

**Flow**:
```
User → LangGraph Graph → Node 1 → State Update → Node 2 → ... → Response → User
                ↓
         Checkpointer (persists state)
```

---

### 2. Conversation Handling

#### MCP Server

| Aspect | Implementation |
|--------|----------------|
| **Context Management** | Handled by Claude Desktop (conversation history) |
| **Multi-turn Conversations** | Each tool call is independent; Claude synthesizes across calls |
| **Follow-up Questions** | Claude asks user, then calls tool again with new info |
| **State Tracking** | Application infers state from database queries |

**Example Conversation**:
```
User: Analyze this job posting [URL]
Claude: [Calls analyze_job tool] → "I analyzed the job. It requires Python and FastAPI."

User: Tailor my resume for it
Claude: [Calls tailor_resume tool] → "I tailored your resume, highlighting FastAPI experience."

User: Write a cover letter
Claude: [Calls generate_cover_letter tool] → "Here's your cover letter..."
```

**Limitation**: Each tool call doesn't know about previous calls unless Claude explicitly passes parameters.

---

#### LangGraph

| Aspect | Implementation |
|--------|----------------|
| **Context Management** | State graph maintains conversation state |
| **Multi-turn Conversations** | State accumulates across turns via checkpointing |
| **Follow-up Questions** | Agent updates state, user resumes with same thread_id |
| **State Tracking** | Explicit state schema with typed fields |

**Example Conversation**:
```
User: Analyze this job posting [URL]
Agent: [Executes analyze_job_node]
       → state["job_analysis"] = {...}
       → Checkpoint saved
       → "I analyzed the job. It requires Python and FastAPI."

User: Tailor my resume for it
Agent: [Resumes from checkpoint]
       → Loads state["job_analysis"] (from previous turn!)
       → Executes tailor_resume_node
       → state["tailored_resume"] = {...}
       → Checkpoint saved
       → "I tailored your resume..."

User: Write a cover letter
Agent: [Resumes from checkpoint]
       → Loads state["job_analysis"] and state["tailored_resume"]
       → Executes cover_letter_node
       → "Here's your cover letter..."
```

**Advantage**: Agent has full context from previous turns without Claude needing to re-pass data.

---

### 3. State Management

#### MCP Server

**Implicit State** (database + Claude's context):

```python
# State is inferred from database queries
@mcp.tool()
def tailor_resume(company: str, job_title: str) -> dict:
    """Tailor resume - requires previous job analysis"""

    # Load job analysis from database (implicit state)
    job_analysis = data_read_job_analysis(company, job_title)

    if not job_analysis:
        return {"error": "No job analysis found. Run analyze_job first."}

    # Load master resume from database
    master_resume = data_read_master_resume()

    # Process
    tailored = llm.invoke(build_tailoring_prompt(job_analysis, master_resume))

    # Save
    data_write_tailored_resume(company, job_title, tailored)

    return {"status": "success", "data": tailored}
```

**State Storage**:
- Job analysis: SQLite database
- Master resume: SQLite database
- Conversation context: Claude Desktop's memory
- No explicit state object

**State Access**:
- Query database for each tool call
- Rely on Claude to track what's been done
- No persistent "current job" or "current workflow" state

---

#### LangGraph

**Explicit State** (TypedDict + SqliteSaver):

```python
from typing import TypedDict, Optional

class ResumeAgentState(TypedDict, total=False):
    messages: List[BaseMessage]           # Conversation history
    job_analysis: Optional[JobAnalysisDict]   # Current job being analyzed
    master_resume: Optional[MasterResumeDict] # User's resume
    tailored_resume: Optional[TailoredResumeDict]  # Generated resume
    cover_letter: Optional[CoverLetterDict]        # Generated cover letter
    portfolio_examples: List[PortfolioExampleDict] # Relevant examples
    current_intent: Optional[WorkflowIntent]       # User's intent
    workflow_progress: Optional[WorkflowProgress]  # Multi-step tracking
    error_message: Optional[str]                   # Latest error

# Node function accesses explicit state
def tailor_resume_node(state: ResumeAgentState) -> dict:
    """Tailor resume - prerequisites checked via state"""

    # Validate state (explicit check)
    if not state.get("job_analysis"):
        return {
            "error_message": "No job analysis in state",
            "messages": [AIMessage(content="Please analyze a job first")]
        }

    if not state.get("master_resume"):
        # Load from database and add to state
        master_resume = data_read_master_resume()
        # ... (update state)

    # Access state fields directly
    job_analysis = state["job_analysis"]
    master_resume = state["master_resume"]

    # Process
    tailored = llm.invoke(build_tailoring_prompt(job_analysis, master_resume))

    # Return state update
    return {
        "tailored_resume": tailored,
        "messages": [AIMessage(content="Resume tailored!")]
    }
```

**State Storage**:
- In-memory state: ResumeAgentState TypedDict
- Persistent state: SqliteSaver checkpoints
- Database: SQLite (same as MCP server)

**State Access**:
- Direct field access: `state["job_analysis"]`
- Automatic checkpointing after each node
- Resume from checkpoint with same thread_id

---

### 4. Persistence

#### MCP Server

| Data | Storage | Access Pattern |
|------|---------|----------------|
| Job Analysis | SQLite database | Query by company + job_title |
| Master Resume | SQLite database | Query by user_id |
| Tailored Resumes | SQLite database | Query by job_id |
| Cover Letters | SQLite database | Query by job_id |
| Portfolio | SQLite database | Search by technology/keywords |
| Conversation State | None (Claude's memory) | Not persisted |

**Persistence Pattern**:
```python
# Tool writes to database immediately
@mcp.tool()
def analyze_job(job_url: str) -> dict:
    analysis = perform_analysis(job_url)

    # Save to database
    data_write_job_analysis(
        company=analysis["company"],
        job_title=analysis["job_title"],
        job_data=analysis
    )

    return analysis
```

**No Workflow State**: If user interrupts workflow, there's no record of "which step were we on?"

---

#### LangGraph

| Data | Storage | Access Pattern |
|------|---------|----------------|
| Job Analysis | State + Database | State first, DB for caching |
| Master Resume | State + Database | State first, DB for loading |
| Tailored Resumes | State + Database | State during workflow, DB for final save |
| Cover Letters | State + Database | State during workflow, DB for final save |
| Portfolio | State + Database | State for current search, DB for library |
| **Conversation State** | **SqliteSaver checkpoints** | **Resume with thread_id** |
| **Workflow Progress** | **SqliteSaver checkpoints** | **Resume interrupted workflows** |

**Persistence Pattern**:
```python
# Node updates state, checkpointer persists automatically
def analyze_job_node(state: ResumeAgentState) -> dict:
    analysis = perform_analysis(state["job_url"])

    # Save to database for caching
    data_write_job_analysis(...)

    # Update state (automatically checkpointed)
    return {
        "job_analysis": analysis,
        "messages": [AIMessage(content="Analysis complete")]
    }
    # Checkpoint saved after node execution!
```

**Workflow State Persistence**:
```python
# User interrupts workflow
result = app.invoke(
    {"messages": [HumanMessage(content="Analyze job at [URL]")]},
    config={"configurable": {"thread_id": "user-123-session-1"}}
)

# ... user goes away ...

# User resumes later with same thread_id
result = app.invoke(
    {"messages": [HumanMessage(content="Continue where we left off")]},
    config={"configurable": {"thread_id": "user-123-session-1"}}
)
# State restored! job_analysis, master_resume, workflow_progress all available
```

---

### 5. Error Handling

#### MCP Server

**Exception Propagation**:
```python
@mcp.tool()
def analyze_job(job_url: str) -> dict:
    try:
        html = fetch_url(job_url)
        analysis = llm.invoke(build_prompt(html))
        data_write_job_analysis(...)
        return {"status": "success", "data": analysis}
    except Exception as e:
        # Return error to Claude
        return {
            "status": "error",
            "message": str(e)
        }
```

**Error Impact**:
- Single tool call fails → Claude sees error response
- No cascading failures (each tool is independent)
- Claude can retry or ask user for help

**No Partial Success**: If `fetch_url` succeeds but `llm.invoke` fails, there's no record of the fetched HTML.

---

#### LangGraph

**Error Accumulation**:
```python
def analyze_job_node(state: ResumeAgentState) -> dict:
    """Never raises - accumulates errors in state"""

    try:
        html = fetch_url(state["job_url"])
    except Exception as e:
        return {
            "error_message": f"Failed to fetch URL: {str(e)}",
            "messages": [AIMessage(content="Could not fetch job posting")]
        }

    try:
        analysis = llm.invoke(build_prompt(html))
    except Exception as e:
        # HTML already fetched - could save for retry
        return {
            "error_message": f"LLM analysis failed: {str(e)}",
            "raw_html": html,  # Preserve partial success
            "messages": [AIMessage(content="Analysis failed, but HTML saved")]
        }

    # Save and update state
    data_write_job_analysis(...)
    return {"job_analysis": analysis}
```

**Error Impact**:
- Node fails → State updated with error_message
- Workflow can continue to next node (partial success)
- Error history preserved in state

**Partial Success**: Intermediate results saved in state even if later steps fail.

---

### 6. Tool Invocation

#### MCP Server

**Direct Tool Calls**:
```
User → Claude Desktop → Function Calling → MCP Tool → Result → Claude → User
```

**Claude Orchestrates**:
- Claude decides which tool to call
- Claude passes parameters
- Claude synthesizes tool results into conversation

**Example**:
```
User: "Apply to this job [URL]"

Claude thinks:
1. analyze_job(job_url) → get requirements
2. tailor_resume(company, title) → customize resume
3. generate_cover_letter(company, title) → write letter

Claude calls each tool sequentially, waiting for each response.
```

**Limitation**: Claude must orchestrate every step. No built-in workflow logic.

---

#### LangGraph

**Graph Orchestration**:
```
User → LangGraph Graph → [Node 1 → Node 2 → Node 3 → ...] → Result → User
```

**Graph Orchestrates**:
- Graph defines workflow structure
- Conditional edges for branching
- Automatic state passing between nodes

**Example**:
```python
# Define workflow graph
workflow = StateGraph(ResumeAgentState)

# Nodes
workflow.add_node("classify_intent", classify_intent_node)
workflow.add_node("analyze_job", analyze_job_node)
workflow.add_node("tailor_resume", tailor_resume_node)
workflow.add_node("cover_letter", cover_letter_node)

# Edges
workflow.set_entry_point("classify_intent")

# Conditional routing
def route_by_intent(state):
    intent = state["current_intent"]["intent_type"]
    if intent == "full_workflow":
        return "analyze_job"
    elif intent == "tailor_resume":
        return "tailor_resume"
    # ...

workflow.add_conditional_edges("classify_intent", route_by_intent)

# Sequential workflow
workflow.add_edge("analyze_job", "tailor_resume")
workflow.add_edge("tailor_resume", "cover_letter")
workflow.add_edge("cover_letter", END)
```

**Advantage**: Workflow logic is explicit and reusable. No need for LLM to decide each step.

---

### 7. Streaming

#### MCP Server

**No Streaming**:
- Tools return complete results
- Claude streams the response to user
- No intermediate progress updates from tools

**User Experience**:
```
User: "Analyze this job"
[Wait 10 seconds...]
Claude: "I analyzed the job. Here are the requirements..."
```

---

#### LangGraph

**Node-by-Node Streaming** (via FastAPI SSE):
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.post("/chat")
async def chat(request: ChatRequest):
    """Stream LangGraph execution to user"""

    async def event_generator():
        # Stream state updates after each node
        async for state in langgraph_app.astream(
            initial_state,
            config={"configurable": {"thread_id": request.thread_id}}
        ):
            # Emit state update to client
            yield {
                "event": "state_update",
                "data": {
                    "current_node": state.get("current_node"),
                    "messages": state.get("messages"),
                    "progress": state.get("workflow_progress")
                }
            }

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**User Experience**:
```
User: "Analyze this job"

[Immediately]
Agent: "Analyzing job posting..."

[5 seconds later]
Agent: "Extracted company: Acme Corp, Title: Senior Developer..."

[10 seconds later]
Agent: "Analysis complete! Found 12 required skills and 8 preferred skills."
```

**Advantage**: Real-time progress feedback improves UX.

---

## Feature Comparison Table

| Feature | MCP Server | LangGraph |
|---------|------------|-----------|
| **Stateful Conversations** | ❌ No (relies on Claude's context) | ✅ Yes (StateGraph + checkpointing) |
| **Multi-Step Workflows** | ⚠️ Claude orchestrates | ✅ Built-in graph execution |
| **Resume Interrupted Workflows** | ❌ No | ✅ Yes (via thread_id) |
| **Streaming Responses** | ❌ No | ✅ Yes (node-by-node streaming) |
| **Error Recovery** | ⚠️ Manual retry via Claude | ✅ State-based error accumulation |
| **Progress Tracking** | ❌ No | ✅ Yes (workflow_progress field) |
| **Conditional Branching** | ⚠️ Claude decides | ✅ Conditional edges in graph |
| **Parallel Execution** | ❌ No | ✅ Yes (parallel node execution) |
| **LLM Provider Flexibility** | ⚠️ MCP server code | ✅ Runtime configuration |
| **Web UI Integration** | ❌ Claude Desktop only | ✅ FastAPI + Agent Chat UI |
| **LangGraph Studio** | ❌ N/A | ✅ Visual debugging |
| **Database Reuse** | ✅ Yes | ✅ Yes (same DAL) |
| **Tool Reuse** | ✅ Yes (70% directly) | ✅ Yes (70% via MCP client) |

---

## Migration Strategy

### What to Preserve from MCP

1. **Data Access Layer**: All `data_read_*` and `data_write_*` functions
2. **Database Schema**: Reuse SQLite database as-is
3. **Business Logic**: Job analysis prompts, resume tailoring logic
4. **Validation**: Input validation for job URLs, company names, etc.

### What to Gain from LangGraph

1. **Stateful Conversations**: User can resume conversations
2. **Workflow Orchestration**: Multi-step workflows with explicit flow control
3. **Progress Tracking**: Users see real-time progress
4. **Error Recovery**: Partial success + retry capability
5. **Web UI**: Modern chat interface (not just Claude Desktop)
6. **Debugging**: LangGraph Studio for visual workflow debugging

### Hybrid Approach

**Best of Both Worlds**:
- **Keep MCP server running** for Claude Desktop integration
- **Wrap LangGraph workflows as MCP tools** for seamless integration
- **Expose LangGraph via FastAPI** for web UI access

```python
# MCP tool wrapping LangGraph workflow
@mcp.tool()
def analyze_job(job_url: str) -> dict:
    """MCP tool wrapping LangGraph job analysis workflow"""

    # Initialize LangGraph workflow
    initial_state = {
        "messages": [HumanMessage(content=f"Analyze job at {job_url}")],
        "current_intent": {
            "intent_type": "analyze_job",
            "extracted_params": {"job_url": job_url}
        }
    }

    # Execute workflow
    result = job_analysis_workflow.invoke(
        initial_state,
        config={"configurable": {"thread_id": str(uuid.uuid4())}}
    )

    # Return MCP-compatible response
    return {
        "status": "success" if not result.get("error_message") else "error",
        "data": result.get("job_analysis"),
        "cached": result.get("cached", False)
    }
```

**Benefits**:
- Claude Desktop users get improved workflows (via MCP)
- Web UI users get full conversational experience
- Shared business logic and database
- Gradual migration path

---

## Performance Comparison

### MCP Server

**Latency**:
- Single tool call: ~5-10 seconds (LLM + database)
- No overhead from state management

**Scalability**:
- Stateless → Easy to scale horizontally
- Each request is independent

**Resource Usage**:
- Minimal memory (no state in memory)
- Database I/O per request

---

### LangGraph

**Latency**:
- Single workflow: ~5-15 seconds (LLM + database + checkpointing)
- Small overhead from state serialization (~100ms)

**Scalability**:
- Stateful → Requires checkpoint database
- Horizontal scaling possible with shared checkpoint DB

**Resource Usage**:
- Higher memory (state in memory during execution)
- Additional database I/O for checkpoints

**Performance Notes**:
- Checkpointing adds ~5-10% overhead
- Acceptable tradeoff for resumability

---

## Deployment Comparison

### MCP Server

**Deployment**:
```bash
# Single-file server
uv run apps/resume-agent/resume_agent.py

# Claude Desktop config
{
  "mcpServers": {
    "resume-agent": {
      "command": "uv",
      "args": ["run", "apps/resume-agent/resume_agent.py"],
      "transport": "streamable-http",
      "url": "http://localhost:8080"
    }
  }
}
```

**Infrastructure**:
- Single process (MCP server)
- SQLite database
- No web UI

---

### LangGraph

**Deployment**:
```bash
# LangGraph dev server (port 2024)
langgraph dev

# FastAPI server (port 8000)
uvicorn main:app --port 8000

# Agent Chat UI (port 3000)
cd apps/agent-chat-ui && npm run dev
```

**Infrastructure**:
- Multiple processes (LangGraph server, FastAPI, web UI)
- SQLite database (shared)
- SQLite checkpoint database
- Web UI (Next.js)

**Production Deployment**:
- Docker containers for each service
- Nginx reverse proxy
- PostgreSQL (replace SQLite for production)

---

## Next Steps

- **Task 1.11**: Create workflow mapping in `workflow-mapping.md`
- **Task 1.12**: Create checkpointing plan in `checkpointing-plan.md`
- **Phase 3**: Implement LangGraph workflows while preserving MCP DAL

---

## References

- **MCP Server**: `apps/resume-agent/resume_agent.py`
- **MCP Tools Inventory**: `docs/mcp-tools-inventory.md`
- **State Schema**: `docs/state-schema.md`
- **Data Flow**: `docs/data-flow.md`

---

**Generated**: 2025-10-26
**Phase**: 1 - Analysis & Discovery
**Status**: Complete
