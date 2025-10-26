# Checkpointing Strategy

**Phase 1 Deliverable**: Complete checkpointing and state persistence plan

**Created**: 2025-10-26

---

## Overview

LangGraph's checkpointing system enables **conversation state persistence** and **workflow resumption**. This document defines the checkpointing strategy for the Resume Agent, including database location, thread ID conventions, checkpoint granularity, and state recovery processes.

---

## Checkpointing Basics

### What is Checkpointing?

**Checkpointing** automatically saves the complete state of a LangGraph workflow after each node execution, enabling:

1. **Conversation Continuity**: Resume multi-turn conversations
2. **Workflow Resumption**: Resume interrupted workflows from last checkpoint
3. **State Recovery**: Recover from failures without data loss
4. **Human-in-the-Loop**: Pause for user input, resume later
5. **Time Travel**: Inspect or restore previous states

### How It Works

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph

# Create checkpointer
checkpointer = SqliteSaver.from_conn_string("data/langgraph_checkpoints.db")

# Compile graph with checkpointer
workflow = StateGraph(ResumeAgentState)
# ... add nodes and edges ...
app = workflow.compile(checkpointer=checkpointer)

# Execute with thread_id
result = app.invoke(
    initial_state,
    config={"configurable": {"thread_id": "user-123-session-20251026"}}
)
# State automatically saved after each node!

# Resume later with same thread_id
next_result = app.invoke(
    {"messages": [HumanMessage(content="Continue")]},
    config={"configurable": {"thread_id": "user-123-session-20251026"}}
)
# Previous state automatically restored!
```

---

## Checkpoint Database

### Location

```
D:\source\Cernji-Agents\data\langgraph_checkpoints.db
```

**Rationale**:
- Same directory as main application database (`resume_agent.db`)
- Isolated from application data (different concerns)
- Easy to backup/restore separately

### Schema

LangGraph's SqliteSaver creates these tables automatically:

```sql
CREATE TABLE checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint BLOB,
    metadata BLOB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

CREATE TABLE writes (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    type TEXT,
    value BLOB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);
```

**Key Fields**:
- `thread_id`: Unique conversation/session identifier
- `checkpoint_id`: Unique checkpoint identifier (UUID)
- `parent_checkpoint_id`: Links checkpoints in sequence
- `checkpoint`: Serialized state (msgpack format)
- `metadata`: Additional metadata (timestamps, node name, etc.)

---

## Thread ID Strategy

### Convention

```
thread_id = f"user-{user_id}-session-{session_id}"
```

**Components**:
- `user-{user_id}`: User identifier (default: "default")
- `session-{session_id}`: Session identifier (timestamp or UUID)

### Examples

```python
# Single user, multiple sessions
"user-default-session-20251026-100530"
"user-default-session-20251026-143022"

# Multi-user support
"user-johndoe-session-20251026-100530"
"user-janedoe-session-20251026-105600"

# UUID-based session IDs
"user-default-session-a7b3c4d5-e6f7-8a9b-0c1d-2e3f4a5b6c7d"
```

### Generation

```python
import uuid
from datetime import datetime

def generate_thread_id(user_id: str = "default") -> str:
    """Generate unique thread ID for new conversation"""

    # Timestamp-based (human-readable)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"user-{user_id}-session-{timestamp}"

    # OR UUID-based (guaranteed unique)
    # session_uuid = str(uuid.uuid4())
    # return f"user-{user_id}-session-{session_uuid}"
```

### Thread ID Scope

| Scope | Thread ID Pattern | Use Case |
|-------|------------------|----------|
| **Conversation** | `user-{user_id}-session-{timestamp}` | Multi-turn conversation about specific topic |
| **Job Application** | `user-{user_id}-job-{company}-{job_title}` | All work related to specific job application |
| **Workflow Instance** | `user-{user_id}-workflow-{workflow_type}-{timestamp}` | Single workflow execution (e.g., full application) |

**Recommendation**: Use **conversation-scoped** thread IDs by default. User can have multiple concurrent conversations.

---

## Checkpoint Granularity

### When Checkpoints Are Saved

**Automatically after each node execution**:

```mermaid
graph LR
    Node1[Node 1] --> Checkpoint1[Checkpoint 1:<br/>State after Node 1]
    Checkpoint1 --> Node2[Node 2]
    Node2 --> Checkpoint2[Checkpoint 2:<br/>State after Node 2]
    Checkpoint2 --> Node3[Node 3]
    Node3 --> Checkpoint3[Checkpoint 3:<br/>State after Node 3]
```

**Example Workflow**: Full Application

| Step | Node | Checkpoint Contains |
|------|------|---------------------|
| 0 | (entry) | Initial state: messages=[], user_id="default" |
| 1 | classify_intent | current_intent={intent_type: "full_workflow", ...} |
| 2 | analyze_job | job_analysis={company: "Acme", job_title: "Senior Dev", ...} |
| 3 | tailor_resume | master_resume={...}, tailored_resume={...} |
| 4 | cover_letter | cover_letter={...} |
| 5 | portfolio_search | portfolio_examples=[...] |
| 6 | format_response | messages=[..., AIMessage(content="Application complete!")] |

**Storage Size**: Each checkpoint stores the **full state**, not just deltas. With reasonable state sizes (< 100KB), this is acceptable for SQLite.

---

## State Recovery Process

### Scenario 1: Resume Interrupted Workflow

**User starts workflow, interrupts after job analysis**:

```python
# Session 1: User starts full application workflow
result_1 = app.invoke(
    {"messages": [HumanMessage(content="Apply to job at https://example.com/job")]},
    config={"configurable": {"thread_id": "user-default-session-20251026-100000"}}
)

# Workflow executes:
# - classify_intent (checkpoint 1)
# - analyze_job (checkpoint 2) <- User interrupts here
# State contains: job_analysis={...}, workflow_progress={current_step: "tailor_resume", ...}

# ... User goes away for 1 hour ...

# Session 2: User resumes
result_2 = app.invoke(
    {"messages": [HumanMessage(content="Continue with the application")]},
    config={"configurable": {"thread_id": "user-default-session-20251026-100000"}}
)

# LangGraph automatically:
# 1. Loads latest checkpoint for thread_id
# 2. Restores state (job_analysis, workflow_progress, etc.)
# 3. Resumes from workflow_progress.current_step ("tailor_resume")
# 4. Continues workflow: tailor_resume → cover_letter → portfolio_search
```

**Implementation**:

```python
def route_by_workflow_progress(state: ResumeAgentState) -> str:
    """Router that checks workflow progress for resumption"""

    progress = state.get("workflow_progress")

    if not progress:
        # New workflow - start from beginning
        return "analyze_job"

    current_step = progress.get("current_step")

    if current_step == "tailor_resume":
        return "tailor_resume"
    elif current_step == "cover_letter":
        return "cover_letter"
    elif current_step == "portfolio_search":
        return "portfolio_search"
    else:
        # Workflow complete
        return END
```

---

### Scenario 2: Recover from Node Failure

**Node fails due to LLM API error**:

```python
def tailor_resume_node(state: ResumeAgentState) -> dict:
    """Tailor resume with error recovery"""

    try:
        # LLM call fails (rate limit, timeout, etc.)
        tailored_resume = llm.invoke(build_prompt(state))
    except Exception as e:
        # Accumulate error in state (don't raise)
        return {
            "error_message": f"Resume tailoring failed: {str(e)}",
            "workflow_progress": {
                **state.get("workflow_progress", {}),
                "errors": state.get("workflow_progress", {}).get("errors", []) + [str(e)],
                "current_step": "tailor_resume"  # Stay on this step for retry
            },
            "messages": [AIMessage(content="Resume tailoring failed. Please retry.")]
        }
        # Checkpoint saved with error state!

    # Success - proceed to next step
    return {
        "tailored_resume": tailored_resume,
        "workflow_progress": {
            **state.get("workflow_progress", {}),
            "steps_completed": state.get("workflow_progress", {}).get("steps_completed", []) + ["tailor_resume"],
            "current_step": "cover_letter"
        }
    }
```

**User retries**:

```python
# Retry with same thread_id
result = app.invoke(
    {"messages": [HumanMessage(content="Retry tailoring my resume")]},
    config={"configurable": {"thread_id": "user-default-session-20251026-100000"}}
)

# LangGraph:
# 1. Loads checkpoint with error state
# 2. Routes to "tailor_resume" (from workflow_progress.current_step)
# 3. Retries LLM call (hopefully succeeds this time)
# 4. Proceeds to next step if successful
```

---

### Scenario 3: Human-in-the-Loop Approval

**Workflow pauses for user approval before sending application**:

```python
def approval_gate_node(state: ResumeAgentState) -> dict:
    """Pause workflow for user approval"""

    # Check if user has approved
    user_approved = state.get("user_approved")

    if user_approved is None:
        # First time - request approval
        return {
            "requires_user_input": True,
            "messages": [AIMessage(content="Review your resume and cover letter. Reply 'approve' to proceed or 'edit' to make changes.")]
        }

    if user_approved:
        # Approved - proceed
        return {
            "messages": [AIMessage(content="Application approved. Proceeding...")]
        }
    else:
        # Not approved - wait for edits
        return {
            "requires_user_input": True,
            "messages": [AIMessage(content="Please make edits and reply 'approve' when ready.")]
        }

# Router function
def route_after_approval(state: ResumeAgentState) -> str:
    """Route based on approval status"""

    if state.get("requires_user_input"):
        return "wait_for_user"  # Special node that ends workflow
    else:
        return "submit_application"
```

**Workflow**:

```mermaid
graph TB
    Resume[tailor_resume_node] --> CoverLetter[cover_letter_node]
    CoverLetter --> Approval[approval_gate_node]

    Approval --> CheckApproval{User Approved?}

    CheckApproval -->|No| WaitForUser[wait_for_user_node<br/>END]
    CheckApproval -->|Yes| Submit[submit_application_node]

    WaitForUser --> Checkpoint[Checkpoint Saved]

    Checkpoint --> UserReturns[User Returns<br/>with Approval]

    UserReturns --> ResumeWorkflow[Resume from<br/>approval_gate_node]

    ResumeWorkflow --> Submit

    Submit --> End([Complete])
```

---

## Checkpoint Metadata

### Custom Metadata

Add custom metadata to checkpoints for debugging and monitoring:

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# Create checkpointer with metadata callback
def checkpoint_metadata_callback(state: ResumeAgentState) -> dict:
    """Generate metadata for checkpoint"""

    return {
        "user_id": state.get("user_id"),
        "workflow_type": state.get("workflow_progress", {}).get("workflow_type"),
        "current_step": state.get("workflow_progress", {}).get("current_step"),
        "timestamp": datetime.utcnow().isoformat(),
        "has_errors": len(state.get("workflow_progress", {}).get("errors", [])) > 0
    }

checkpointer = SqliteSaver.from_conn_string(
    "data/langgraph_checkpoints.db",
    metadata_callback=checkpoint_metadata_callback
)
```

**Query Checkpoints**:

```python
# List all checkpoints for a thread
checkpoints = checkpointer.list(thread_id="user-default-session-20251026-100000")

for checkpoint in checkpoints:
    print(f"Checkpoint {checkpoint.checkpoint_id}:")
    print(f"  Metadata: {checkpoint.metadata}")
    print(f"  State: {checkpoint.state}")
```

---

## Checkpoint Cleanup

### Retention Policy

**Problem**: Checkpoints accumulate over time, consuming disk space.

**Solution**: Implement retention policy:

```python
import sqlite3
from datetime import datetime, timedelta

def cleanup_old_checkpoints(
    db_path: str = "data/langgraph_checkpoints.db",
    retention_days: int = 30
):
    """Delete checkpoints older than retention period"""

    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Delete old checkpoints
    cursor.execute(
        """DELETE FROM checkpoints
           WHERE json_extract(metadata, '$.timestamp') < ?""",
        (cutoff_date.isoformat(),)
    )

    # Delete orphaned writes
    cursor.execute(
        """DELETE FROM writes
           WHERE NOT EXISTS (
               SELECT 1 FROM checkpoints
               WHERE checkpoints.thread_id = writes.thread_id
               AND checkpoints.checkpoint_id = writes.checkpoint_id
           )"""
    )

    conn.commit()
    deleted_count = cursor.rowcount
    conn.close()

    print(f"Deleted {deleted_count} old checkpoints")

# Run daily via cron or scheduler
cleanup_old_checkpoints(retention_days=30)
```

### Manual Cleanup

```python
def delete_thread_checkpoints(thread_id: str):
    """Delete all checkpoints for a specific thread"""

    conn = sqlite3.connect("data/langgraph_checkpoints.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
    cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))

    conn.commit()
    conn.close()
```

---

## Checkpoint Inspection

### Debugging with Checkpoint Inspector

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("data/langgraph_checkpoints.db")

def inspect_thread_history(thread_id: str):
    """Inspect all checkpoints for a thread"""

    checkpoints = list(checkpointer.list(thread_id=thread_id))

    print(f"\nThread: {thread_id}")
    print(f"Total checkpoints: {len(checkpoints)}\n")

    for i, checkpoint in enumerate(checkpoints):
        print(f"Checkpoint {i + 1}:")
        print(f"  ID: {checkpoint.checkpoint_id}")
        print(f"  Parent: {checkpoint.parent_checkpoint_id}")
        print(f"  Metadata: {checkpoint.metadata}")

        state = checkpoint.state
        print(f"  State fields:")
        print(f"    - messages: {len(state.get('messages', []))} messages")
        print(f"    - job_analysis: {'present' if state.get('job_analysis') else 'absent'}")
        print(f"    - tailored_resume: {'present' if state.get('tailored_resume') else 'absent'}")
        print(f"    - cover_letter: {'present' if state.get('cover_letter') else 'absent'}")
        print(f"    - error_message: {state.get('error_message', 'None')}")
        print()

# Usage
inspect_thread_history("user-default-session-20251026-100000")
```

**Output**:
```
Thread: user-default-session-20251026-100000
Total checkpoints: 5

Checkpoint 1:
  ID: 7f3e4d5c-6b7a-8c9d-0e1f-2a3b4c5d6e7f
  Parent: None
  Metadata: {'timestamp': '2025-10-26T10:00:00Z', 'current_step': 'classify_intent'}
  State fields:
    - messages: 1 messages
    - job_analysis: absent
    - tailored_resume: absent
    - cover_letter: absent
    - error_message: None

Checkpoint 2:
  ID: 8g4f5e6d-7c8b-9d0e-1f2a-3b4c5d6e7f8g
  Parent: 7f3e4d5c-6b7a-8c9d-0e1f-2a3b4c5d6e7f
  Metadata: {'timestamp': '2025-10-26T10:00:15Z', 'current_step': 'analyze_job'}
  State fields:
    - messages: 2 messages
    - job_analysis: present
    - tailored_resume: absent
    - cover_letter: absent
    - error_message: None

...
```

---

## Time Travel: Restore Previous State

### Use Case: Undo Last Action

```python
def restore_previous_checkpoint(thread_id: str) -> dict:
    """Restore state to previous checkpoint (undo last action)"""

    checkpointer = SqliteSaver.from_conn_string("data/langgraph_checkpoints.db")

    # Get all checkpoints for thread
    checkpoints = list(checkpointer.list(thread_id=thread_id))

    if len(checkpoints) < 2:
        return {"error": "No previous checkpoint to restore"}

    # Get second-to-last checkpoint (last is current, second-to-last is previous)
    previous_checkpoint = checkpoints[-2]

    # Load state from previous checkpoint
    previous_state = previous_checkpoint.state

    # Execute workflow with this state (overwrites current checkpoint)
    result = app.invoke(
        previous_state,
        config={"configurable": {"thread_id": thread_id}}
    )

    return {
        "message": "Restored to previous state",
        "checkpoint_id": previous_checkpoint.checkpoint_id
    }
```

---

## Production Considerations

### Database Backend

**Development**: SQLite (`SqliteSaver`)
- Simple, file-based
- Good for single-server deployments
- No additional infrastructure

**Production**: PostgreSQL (`PostgresSaver`)
- Concurrent access support
- Better performance for high-traffic
- Can scale horizontally with connection pooling

```python
from langgraph.checkpoint.postgres import PostgresSaver

# Production checkpointer
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:password@localhost:5432/langgraph_checkpoints"
)
```

### Checkpoint Size Optimization

**Problem**: Large states consume disk space and slow serialization.

**Solutions**:

1. **Exclude Large Fields from State**:
```python
# Don't store full HTML in state
# Instead, store source_id and load from database when needed
return {
    "job_analysis": analysis,
    # "raw_html": html  # Don't include in state
}
```

2. **Compress Checkpoints**:
```python
import zlib

def compress_checkpoint(checkpoint: bytes) -> bytes:
    return zlib.compress(checkpoint)

def decompress_checkpoint(compressed: bytes) -> bytes:
    return zlib.decompress(compressed)
```

3. **Lazy Loading**:
```python
# Store references in state, load data from DB when needed
class ResumeAgentState(TypedDict):
    job_analysis_id: Optional[int]  # Reference, not full object
    # ...

def load_job_analysis_from_id(state: ResumeAgentState) -> JobAnalysisDict:
    job_id = state["job_analysis_id"]
    return data_read_job_analysis_by_id(job_id)
```

---

## Next Steps

- **Task 1.13**: Create architecture decisions in `architecture-decisions.md`
- **Task 1.14**: Create Phase 1 summary in `phase-1-summary.md`
- **Phase 3**: Implement checkpointing in LangGraph workflows

---

## References

- **State Schema**: `docs/state-schema.md`
- **Workflow Mapping**: `docs/workflow-mapping.md`
- **LangGraph Checkpointing Docs**: https://langchain-ai.github.io/langgraph/concepts/persistence/
- **SqliteSaver API**: https://langchain-ai.github.io/langgraph/reference/checkpoints/#sqlitesaver

---

**Generated**: 2025-10-26
**Phase**: 1 - Analysis & Discovery
**Status**: Complete
