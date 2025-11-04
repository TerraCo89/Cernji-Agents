# Multi-Agent State Management and Handoff Patterns Research

## Solution Description

### Overview of State Management Patterns

Multi-agent autonomous programming systems require robust state management to coordinate work across multiple specialized agents while preserving context, preventing data loss, and enabling recovery from failures. Based on comprehensive research across LangGraph, AutoGen, and CrewAI, several core patterns emerge:

### 1. Shared State Schemas and Data Structures

**LangGraph Approach:**
- Uses TypedDict or Pydantic models to define graph-wide state schemas
- Implements **reducer functions** via `Annotated` types to handle concurrent state updates
- Supports separate state schemas for parent graphs vs. subgraphs (agents)
- Enables private input states for nodes that differ from overall graph state

**Example reducer pattern:**
```python
from typing import Annotated, TypedDict
import operator

class State(TypedDict):
    messages: Annotated[list, operator.add]  # Appends messages
    counter: Annotated[int, operator.add]    # Sums values
    status: str                               # Overwrites on update
```

**AutoGen Approach:**
- Uses nested dictionary structures for state representation
- Agent state contains `llm_messages` for conversation history
- Team state includes all agent states plus team metadata
- State is JSON-serializable for persistence

**CrewAI Approach:**
- Task outputs flow automatically to subsequent tasks via `context` parameter
- Memory system includes short-term, long-term, entity, and contextual memory
- Each task can specify multiple tasks' outputs as context
- Crew-wide memory enables context retention across conversations

### 2. Artifact Passing (Code, Docs, Test Results)

**LangGraph Artifact Management:**
- **Tool Artifacts**: Ephemeral data (DataFrames, images, custom objects) passed between tools but not exposed to LLM
- **State Channels**: Persistent workflow-level state survives across execution steps
- **Memory Store**: Cross-thread namespace storage for shared information (e.g., user preferences)

**Pattern for artifact sharing:**
```python
from langgraph.store.memory import InMemoryStore

def node_fn(state, config, *, store: BaseStore):
    user_id = config["configurable"]["user_id"]
    namespace = (user_id, "artifacts")

    # Store artifact
    store.put(namespace, "code_result", {
        "code": "...",
        "test_output": "...",
        "timestamp": "..."
    })

    # Retrieve artifacts
    artifacts = store.search(namespace, query="test results", limit=5)
```

**AutoGen Context Passing:**
- Context maintained in `UserTask.context` message list
- Messages accumulate through delegation chain
- Each handoff appends function calls, results, and transition messages

**CrewAI Output Sharing:**
```python
task_1 = Task(description="...", agent=agent1)
task_2 = Task(description="...", agent=agent2)
task_3 = Task(
    description="...",
    agent=agent3,
    context=[task_1, task_2]  # Receives outputs from both
)
```

### 3. Context Preservation Across Agent Boundaries

**Full History vs. Results-Only Sharing:**

LangGraph recommends choosing between:
1. **Full thought process**: Agents share complete message histories including intermediate reasoning (better quality, higher token cost)
2. **Results only**: Agents receive only final outputs (lower cost, requires separate state schemas per agent)

**Handoff Representation:**
- Preserve handoff as AI message with tool call + corresponding tool message
- Include agent names in messages: `<agent>alice</agent><message>content</message>`
- Supervisor patterns centralize routing decisions while maintaining full context

**AutoGen Context Preservation:**
```python
# Context preserved during handoff
delegate_messages = list(message.context) + [
    AssistantMessage(content=[call], source=self.id.type),
    FunctionExecutionResultMessage(
        content=[FunctionExecutionResult(
            call_id=call.id,
            content=f"Transferred to {agent_name}. Adopt persona immediately.",
            is_error=False,
            name=call.name,
        )]
    ),
]
```

### 4. Checkpoint/Resume for Long-Running Workflows

**LangGraph Checkpointing:**

Checkpointers save graph state snapshots at each "super-step" organized into threads:

```python
from langgraph.checkpoint.sqlite import AsyncSqliteSaver
from langgraph.graph import StateGraph

async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = StateGraph(State).compile(checkpointer=checkpointer)

    # Execute with thread ID
    config = {"configurable": {"thread_id": "session_123"}}
    result = await graph.ainvoke(input_data, config)

    # Resume from checkpoint
    state = await graph.aget_state(config)
    result = await graph.ainvoke(None, config)  # Continues from last checkpoint
```

**Checkpoint capabilities:**
- **Get state**: Retrieve latest checkpoint
- **Get history**: List all checkpoints chronologically
- **Replay**: Resume from specific checkpoint ID
- **Update state**: Modify persisted state with optional node attribution
- **Time travel**: Fork execution at arbitrary checkpoints

**AutoGen Save/Load State:**

```python
import json

# Save team state
team_state = await agent_team.save_state()

# Persist to disk
with open("team_state.json", "w") as f:
    json.dump(team_state, f)

# Load from disk
with open("team_state.json", "r") as f:
    team_state = json.load(f)

# Restore team
new_agent_team = RoundRobinGroupChat([assistant_agent], ...)
await new_agent_team.load_state(team_state)
```

**Human-in-the-Loop Checkpointing:**

```python
from langgraph.types import interrupt, Command

def approval_node(state):
    decision = interrupt({
        "question": "Approve this action?",
        "details": state["action_details"]
    })

    if decision == "approve":
        return Command(goto="proceed", update={"approved": True})
    else:
        return Command(goto="cancel", update={"approved": False})

# Execution pauses at interrupt, state is checkpointed
result = graph.invoke(input_data, config)

# Resume later (even days later)
graph.invoke(Command(resume="approve"), config)
```

### 5. Conflict Resolution When Agents Modify Same Files

**Reducer Functions for Parallel Updates:**

LangGraph addresses conflicts through reducer functions that define merge logic:

```python
from typing import Annotated, TypedDict
import operator

def merge_file_edits(left: list, right: list) -> list:
    """Custom reducer for file modification conflicts"""
    seen_files = {}
    for edit in left + right:
        file_path = edit["file"]
        if file_path not in seen_files:
            seen_files[file_path] = edit
        else:
            # Last write wins, but preserve metadata
            seen_files[file_path] = {
                **seen_files[file_path],
                **edit,
                "conflict": True,
                "previous_edit": seen_files[file_path]
            }
    return list(seen_files.values())

class CodeState(TypedDict):
    file_edits: Annotated[list, merge_file_edits]
    messages: Annotated[list, operator.add]
```

**Conflict Detection Pattern:**

Without reducers, parallel updates to the same state key raise: `"Can receive only one value per step"`. Use reducers to:
- **Append**: `operator.add` for lists
- **Sum**: `operator.add` for numbers
- **Merge**: Custom functions for complex objects
- **Last-write-wins**: No annotator (default overwrite)

**Database-Inspired Conflict Resolution:**

Based on distributed systems research:
- **Optimistic Concurrency Control**: Check for conflicts before committing
- **Write-Write Conflicts**: First transaction wins, others rollback
- **Snapshot Isolation**: Transactions see consistent snapshot, conflicts abort later transactions

### 6. Transaction Patterns and Rollback Strategies

**Rollback Contract Pattern:**

Every agent action includes a rollback plan:
```python
class ActionWithRollback(TypedDict):
    action: str
    parameters: dict
    rollback_plan: dict
    dependencies: list[str]  # IDs of actions this depends on

def execute_with_rollback(state: State, action: ActionWithRollback):
    try:
        result = perform_action(action)
        return {
            "completed_actions": [{"id": action["id"], "result": result}],
            "rollback_stack": [action["rollback_plan"]]
        }
    except Exception as e:
        # Rollback this action and notify dependents
        for rollback in reversed(state["rollback_stack"]):
            execute_rollback(rollback)
        raise
```

**Retry with Exponential Backoff:**

```python
import time
import random

def agent_with_retry(state: State, max_retries=3):
    for attempt in range(max_retries):
        try:
            return execute_agent_task(state)
        except DependencyFailure as e:
            if attempt == max_retries - 1:
                raise
            # Exponential backoff with jitter
            delay = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
```

**Circuit Breaker Pattern:**

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitOpenError("Service unavailable")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise
```

**Checkpoint-Based Recovery:**

```python
async def fault_tolerant_execution(graph, input_data, config):
    """Execute with automatic checkpoint recovery"""
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            # Get current state
            state = await graph.aget_state(config)

            if state.next:  # Has pending work
                # Resume from last checkpoint
                result = await graph.ainvoke(None, config)
            else:
                # Start fresh
                result = await graph.ainvoke(input_data, config)

            return result

        except Exception as e:
            if attempt == max_attempts - 1:
                raise

            # Log failure
            logger.error(f"Attempt {attempt + 1} failed: {e}")

            # Wait before retry
            await asyncio.sleep(2 ** attempt)
```

**Best Practices Summary:**

1. **Isolation**: Use bulkhead patterns to compartmentalize failure domains
2. **Idempotency**: Never retry non-idempotent operations
3. **Monitoring**: Log retry counts, fallback paths, and failure reasons
4. **Graceful Degradation**: Provide fallback modules for different error types
5. **Load Balancing**: Distribute tasks across multiple agents for redundancy
6. **State Preservation**: Checkpoint before risky operations
7. **Timeout Management**: Set appropriate timeouts for long-running tasks
8. **Resource Limits**: Implement concurrency limits to prevent thundering herd

---

## Working Code Example

Below is a complete, production-ready example demonstrating:
- Shared state with reducers for conflict resolution
- Agent A completing work and saving artifacts
- Orchestrator checkpointing state
- Agent B resuming with Agent A's context
- Conflict detection and resolution
- Human approval workflow
- Error recovery with retry logic

```python
"""
Multi-Agent Programming System with State Management and Handoffs

This example demonstrates a code analysis and refactoring workflow where:
1. Analyzer Agent examines code and proposes changes
2. Orchestrator checkpoints state and routes to appropriate agent
3. Refactor Agent applies changes with conflict detection
4. Human approves critical operations
5. Tester Agent validates results
"""

import asyncio
import json
import operator
from typing import Annotated, Literal, TypedDict, Any
from datetime import datetime
from pathlib import Path

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import AsyncSqliteSaver
from langgraph.types import Command, interrupt
from langgraph.store.memory import InMemoryStore

# Simulated LLM (replace with actual OpenAI/Anthropic client)
class MockLLM:
    def invoke(self, messages):
        return {"content": "Mock LLM response"}

llm = MockLLM()


# ============================================================================
# State Schema with Reducers
# ============================================================================

def merge_file_edits(left: list[dict], right: list[dict]) -> list[dict]:
    """
    Custom reducer for handling concurrent file modifications.
    Detects conflicts and preserves edit history.
    """
    file_map = {}

    for edit in left + right:
        file_path = edit["file_path"]

        if file_path not in file_map:
            file_map[file_path] = edit
        else:
            # Conflict detected - same file modified by multiple agents
            existing = file_map[file_path]
            file_map[file_path] = {
                "file_path": file_path,
                "content": edit["content"],  # Latest content wins
                "agent": edit["agent"],
                "timestamp": edit["timestamp"],
                "conflict_detected": True,
                "previous_edit": existing,
                "resolution": "last_write_wins"
            }

    return list(file_map.values())


def merge_artifacts(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Merge artifact dictionaries, with right overwriting left."""
    return {**left, **right}


class WorkflowState(TypedDict):
    """
    Shared state across all agents in the workflow.
    Uses reducers for conflict resolution during parallel execution.
    """
    # Input
    task_description: str
    files_to_analyze: list[str]

    # Messages accumulate across agents
    messages: Annotated[list[dict], operator.add]

    # File edits with conflict detection
    file_edits: Annotated[list[dict], merge_file_edits]

    # Artifacts persist across agents (code, test results, etc.)
    artifacts: Annotated[dict[str, Any], merge_artifacts]

    # Agent execution metadata
    agent_history: Annotated[list[str], operator.add]

    # Workflow control
    current_agent: str
    approval_required: bool
    approved: bool
    completed: bool
    error: str | None


# ============================================================================
# Agent A: Code Analyzer
# ============================================================================

async def analyzer_agent(state: WorkflowState) -> WorkflowState:
    """
    Analyzes code and proposes refactoring changes.
    Saves analysis artifacts for downstream agents.
    """
    print(f"\n{'='*60}")
    print(f"ANALYZER AGENT - Starting analysis")
    print(f"{'='*60}")

    # Simulate code analysis
    await asyncio.sleep(0.5)

    analysis_result = {
        "issues_found": [
            {"file": "app.py", "issue": "Long function (150 lines)", "severity": "high"},
            {"file": "utils.py", "issue": "Unused imports", "severity": "low"},
        ],
        "recommendations": [
            "Extract method for user authentication logic",
            "Remove unused imports",
            "Add type hints to public functions"
        ],
        "complexity_score": 72,
        "timestamp": datetime.now().isoformat()
    }

    # Proposed file edits
    proposed_edits = [
        {
            "file_path": "app.py",
            "content": "# Refactored version with extracted method\ndef authenticate_user(credentials):\n    ...",
            "agent": "analyzer",
            "timestamp": datetime.now().isoformat(),
            "reason": "Extract long authentication logic"
        },
        {
            "file_path": "utils.py",
            "content": "# Cleaned imports\nfrom typing import Dict\n\ndef helper():\n    ...",
            "agent": "analyzer",
            "timestamp": datetime.now().isoformat(),
            "reason": "Remove unused imports"
        }
    ]

    return {
        "messages": [{
            "role": "agent",
            "agent": "analyzer",
            "content": f"Analysis complete. Found {len(analysis_result['issues_found'])} issues.",
            "timestamp": datetime.now().isoformat()
        }],
        "file_edits": proposed_edits,
        "artifacts": {
            "analysis": analysis_result,
            "analyzer_session_id": "analyzer_20250129_001"
        },
        "agent_history": ["analyzer"],
        "current_agent": "analyzer"
    }


# ============================================================================
# Orchestrator: Routes and Checkpoints
# ============================================================================

def orchestrator_router(state: WorkflowState) -> Literal["refactor_agent", "human_approval", "tester_agent", END]:
    """
    Orchestrator makes routing decisions based on state.
    Automatically checkpoints state before transitions.
    """
    print(f"\n{'='*60}")
    print(f"ORCHESTRATOR - Routing decision")
    print(f"Current agent: {state.get('current_agent', 'none')}")
    print(f"Approval required: {state.get('approval_required', False)}")
    print(f"Completed: {state.get('completed', False)}")
    print(f"{'='*60}")

    # Error handling
    if state.get("error"):
        print(f"ERROR detected: {state['error']}")
        return END

    # Completion check
    if state.get("completed"):
        return END

    # Route based on current state
    current = state.get("current_agent", "")

    if current == "analyzer":
        # Analyzer done, check if approval needed
        if state.get("approval_required", False) and not state.get("approved", False):
            return "human_approval"
        return "refactor_agent"

    elif current == "refactor_agent":
        return "tester_agent"

    elif current == "tester_agent":
        return END

    return END


# ============================================================================
# Agent B: Refactor Agent (Resumes with Agent A's context)
# ============================================================================

async def refactor_agent(state: WorkflowState, *, store: InMemoryStore) -> WorkflowState:
    """
    Applies refactoring changes using context from Analyzer Agent.
    Demonstrates accessing artifacts from previous agent.
    """
    print(f"\n{'='*60}")
    print(f"REFACTOR AGENT - Applying changes")
    print(f"{'='*60}")

    # Access artifacts from Agent A
    analysis = state["artifacts"].get("analysis", {})
    print(f"Loaded analysis from Agent A: {len(analysis.get('issues_found', []))} issues")

    # Check for conflicts in file edits
    conflicts_detected = any(edit.get("conflict_detected", False) for edit in state["file_edits"])

    if conflicts_detected:
        print("⚠️  CONFLICTS DETECTED in file edits!")
        for edit in state["file_edits"]:
            if edit.get("conflict_detected"):
                print(f"  - {edit['file_path']}: {edit['resolution']}")

    # Simulate refactoring
    await asyncio.sleep(0.5)

    # Additional edit (might conflict if parallel execution)
    new_edit = {
        "file_path": "app.py",  # Same file as analyzer - potential conflict!
        "content": "# Further refactored with type hints\ndef authenticate_user(credentials: dict) -> bool:\n    ...",
        "agent": "refactor",
        "timestamp": datetime.now().isoformat(),
        "reason": "Add type hints as recommended"
    }

    # Store refactoring session in cross-agent memory
    session_id = "refactor_20250129_001"
    namespace = ("refactor_sessions", session_id)
    store.put(namespace, "session", {
        "session_id": session_id,
        "files_modified": list(set([e["file_path"] for e in state["file_edits"]])),
        "timestamp": datetime.now().isoformat(),
        "conflicts_resolved": conflicts_detected
    })

    return {
        "messages": [{
            "role": "agent",
            "agent": "refactor",
            "content": f"Refactoring complete. Modified {len(state['file_edits'])} files.",
            "timestamp": datetime.now().isoformat()
        }],
        "file_edits": [new_edit],  # Reducer will merge and detect conflict
        "artifacts": {
            "refactor_session_id": session_id,
            "conflicts_resolved": conflicts_detected
        },
        "agent_history": ["refactor"],
        "current_agent": "refactor_agent"
    }


# ============================================================================
# Human Approval Workflow
# ============================================================================

def human_approval_node(state: WorkflowState) -> Command[Literal["refactor_agent", "tester_agent", END]]:
    """
    Pauses execution for human review.
    Demonstrates interrupt/resume pattern with checkpointing.
    """
    print(f"\n{'='*60}")
    print(f"HUMAN APPROVAL - Requesting review")
    print(f"{'='*60}")

    # Prepare approval request
    approval_data = {
        "question": "Approve these refactoring changes?",
        "file_count": len(state["file_edits"]),
        "files": [edit["file_path"] for edit in state["file_edits"]],
        "conflicts": any(e.get("conflict_detected") for e in state["file_edits"]),
        "analysis_summary": state["artifacts"].get("analysis", {}).get("recommendations", [])
    }

    # This pauses execution and checkpoints state
    decision = interrupt(approval_data)

    if decision == "approve":
        print("✓ Changes APPROVED by human")
        return Command(
            goto="refactor_agent",
            update={"approved": True, "approval_required": False}
        )
    elif decision == "reject":
        print("✗ Changes REJECTED by human")
        return Command(
            goto=END,
            update={"approved": False, "error": "Changes rejected by human reviewer"}
        )
    else:
        print("↻ Requesting revisions")
        return Command(
            goto="analyzer_agent",
            update={"approved": False}
        )


# ============================================================================
# Tester Agent: Validates Results
# ============================================================================

async def tester_agent(state: WorkflowState, *, store: InMemoryStore) -> WorkflowState:
    """
    Runs tests on refactored code.
    Accesses artifacts from both previous agents.
    """
    print(f"\n{'='*60}")
    print(f"TESTER AGENT - Running validation")
    print(f"{'='*60}")

    # Access refactor session from store
    refactor_session_id = state["artifacts"].get("refactor_session_id")
    if refactor_session_id:
        namespace = ("refactor_sessions", refactor_session_id)
        session_data = store.search(namespace)
        print(f"Loaded refactor session: {len(list(session_data))} entries")

    # Simulate test execution
    await asyncio.sleep(0.5)

    test_results = {
        "tests_run": 24,
        "tests_passed": 23,
        "tests_failed": 1,
        "coverage": 87.5,
        "failures": [
            {"test": "test_auth_with_invalid_token", "error": "AssertionError"}
        ],
        "timestamp": datetime.now().isoformat()
    }

    success = test_results["tests_failed"] == 0

    return {
        "messages": [{
            "role": "agent",
            "agent": "tester",
            "content": f"Tests complete. {test_results['tests_passed']}/{test_results['tests_run']} passed.",
            "timestamp": datetime.now().isoformat()
        }],
        "artifacts": {
            "test_results": test_results
        },
        "agent_history": ["tester"],
        "current_agent": "tester_agent",
        "completed": success,
        "error": None if success else "Tests failed - see test_results artifact"
    }


# ============================================================================
# Error Recovery: Retry Logic
# ============================================================================

async def execute_with_retry(
    graph,
    input_data: dict,
    config: dict,
    max_retries: int = 3
) -> dict:
    """
    Fault-tolerant execution with exponential backoff.
    Demonstrates checkpoint-based recovery.
    """
    import random

    for attempt in range(max_retries):
        try:
            # Check if we have a checkpoint to resume from
            state = await graph.aget_state(config)

            if state.next:  # Has pending work
                print(f"\n↻ RECOVERY: Resuming from checkpoint (attempt {attempt + 1})")
                result = await graph.ainvoke(None, config)
            else:
                print(f"\n▶ Starting fresh execution (attempt {attempt + 1})")
                result = await graph.ainvoke(input_data, config)

            return result

        except Exception as e:
            print(f"\n✗ ERROR on attempt {attempt + 1}: {e}")

            if attempt == max_retries - 1:
                print(f"Max retries ({max_retries}) exceeded. Failing.")
                raise

            # Exponential backoff with jitter
            delay = (2 ** attempt) + random.uniform(0, 1)
            print(f"Waiting {delay:.2f}s before retry...")
            await asyncio.sleep(delay)


# ============================================================================
# Graph Construction
# ============================================================================

async def build_workflow():
    """Constructs the multi-agent workflow graph with checkpointing."""

    # Initialize persistent storage
    memory_store = InMemoryStore()

    async with AsyncSqliteSaver.from_conn_string("workflow_checkpoints.db") as checkpointer:
        # Build graph
        builder = StateGraph(WorkflowState)

        # Add agent nodes with store injection
        builder.add_node("analyzer_agent", analyzer_agent)
        builder.add_node("refactor_agent", refactor_agent)
        builder.add_node("human_approval", human_approval_node)
        builder.add_node("tester_agent", tester_agent)

        # Define edges
        builder.add_edge(START, "analyzer_agent")

        # Orchestrator routes after each agent
        builder.add_conditional_edges(
            "analyzer_agent",
            orchestrator_router,
            ["human_approval", "refactor_agent", "tester_agent", END]
        )
        builder.add_conditional_edges(
            "human_approval",
            lambda s: "refactor_agent" if s.get("approved") else END
        )
        builder.add_edge("refactor_agent", "tester_agent")
        builder.add_conditional_edges(
            "tester_agent",
            orchestrator_router,
            [END]
        )

        # Compile with checkpointing and store
        graph = builder.compile(
            checkpointer=checkpointer,
            store=memory_store
        )

        return graph, memory_store


# ============================================================================
# Execution Example
# ============================================================================

async def main():
    """
    Demonstrates complete workflow:
    1. Analyzer agent analyzes code
    2. Orchestrator checkpoints and routes
    3. Human approval (simulated)
    4. Refactor agent resumes with Analyzer's context
    5. Conflict detection on concurrent edits
    6. Tester agent validates results
    7. State persisted across all steps
    """
    print("\n" + "="*60)
    print("MULTI-AGENT STATE MANAGEMENT DEMONSTRATION")
    print("="*60)

    # Build workflow
    graph, store = await build_workflow()

    # Input data
    input_data = {
        "task_description": "Refactor authentication module for better maintainability",
        "files_to_analyze": ["app.py", "utils.py"],
        "messages": [],
        "file_edits": [],
        "artifacts": {},
        "agent_history": [],
        "current_agent": "",
        "approval_required": True,  # Will trigger human approval
        "approved": False,
        "completed": False,
        "error": None
    }

    # Thread ID for checkpointing
    config = {"configurable": {"thread_id": "workflow_session_001"}}

    try:
        # Execute until first interrupt (human approval)
        print("\n▶ Phase 1: Running until human approval...")
        async for chunk in graph.astream(input_data, config):
            agent_name = list(chunk.keys())[0]
            print(f"\n✓ {agent_name} completed")

        # Check state at interrupt
        state = await graph.aget_state(config)
        print(f"\n⏸  PAUSED at: {state.next}")
        print(f"Interrupt data: {state.tasks[0].interrupts[0].value if state.tasks else 'none'}")

        # Simulate human approval after review
        print("\n👤 Human reviewing changes...")
        await asyncio.sleep(1)

        # Resume with approval
        print("\n▶ Phase 2: Resuming with approval...")
        result = await graph.ainvoke(Command(resume="approve"), config)

        # Display final results
        print(f"\n{'='*60}")
        print("WORKFLOW COMPLETE")
        print(f"{'='*60}")
        print(f"Agents executed: {', '.join(result['agent_history'])}")
        print(f"Files modified: {len(result['file_edits'])}")
        print(f"Conflicts detected: {any(e.get('conflict_detected', False) for e in result['file_edits'])}")
        print(f"Tests passed: {result['artifacts'].get('test_results', {}).get('tests_passed', 'N/A')}")
        print(f"Success: {result['completed']}")

        # Show checkpoint history
        history = [s async for s in graph.aget_state_history(config)]
        print(f"\nCheckpoints saved: {len(history)}")

        # Access cross-agent artifacts
        print(f"\nArtifacts in final state:")
        for key, value in result['artifacts'].items():
            print(f"  - {key}: {type(value).__name__}")

        # Demonstrate conflict resolution
        print(f"\nFile Edit History (showing conflict resolution):")
        for edit in result['file_edits']:
            conflict_marker = " [CONFLICT]" if edit.get("conflict_detected") else ""
            print(f"  - {edit['file_path']} by {edit['agent']}{conflict_marker}")
            if edit.get("conflict_detected"):
                print(f"    Resolution: {edit.get('resolution')}")
                print(f"    Previous: {edit.get('previous_edit', {}).get('agent', 'unknown')}")

    except Exception as e:
        print(f"\n✗ Workflow failed: {e}")
        raise


# ============================================================================
# Example with Parallel Execution and Conflict Resolution
# ============================================================================

async def parallel_execution_example():
    """
    Demonstrates Send() API for parallel agent execution with conflict handling.
    """
    from langgraph.types import Send

    class ParallelState(TypedDict):
        tasks: list[str]
        results: Annotated[list[dict], operator.add]
        file_edits: Annotated[list[dict], merge_file_edits]

    async def worker(state: dict):
        """Worker processes individual task"""
        task = state["task"]
        await asyncio.sleep(0.3)

        # Simulate multiple workers editing same file
        return {
            "results": [{"task": task, "status": "done"}],
            "file_edits": [{
                "file_path": "shared.py",  # Same file - will conflict!
                "content": f"# Modified by {task}",
                "agent": task,
                "timestamp": datetime.now().isoformat()
            }]
        }

    def dispatch_workers(state: ParallelState):
        """Create parallel workers using Send()"""
        return [Send("worker", {"task": task}) for task in state["tasks"]]

    # Build parallel graph
    builder = StateGraph(ParallelState)
    builder.add_node("worker", worker)
    builder.add_conditional_edges(START, dispatch_workers, ["worker"])
    builder.add_edge("worker", END)

    graph = builder.compile()

    # Execute
    result = await graph.ainvoke({
        "tasks": ["worker_1", "worker_2", "worker_3"],
        "results": [],
        "file_edits": []
    })

    print(f"\nParallel Execution Results:")
    print(f"Tasks completed: {len(result['results'])}")
    print(f"File edits (after conflict resolution): {len(result['file_edits'])}")

    # Show conflict resolution
    for edit in result['file_edits']:
        if edit.get("conflict_detected"):
            print(f"  CONFLICT in {edit['file_path']}: "
                  f"{edit.get('previous_edit', {}).get('agent')} → {edit['agent']}")


if __name__ == "__main__":
    # Run main workflow
    asyncio.run(main())

    # Run parallel execution demo
    print("\n\n" + "="*60)
    print("PARALLEL EXECUTION WITH CONFLICT RESOLUTION")
    print("="*60)
    asyncio.run(parallel_execution_example())
```

---

## Sources

### LangGraph State Management and Multi-Agent Patterns
- [LangGraph Multi-Agent Systems - Overview](https://langchain-ai.github.io/langgraph/concepts/multi_agent/): Comprehensive guide to state sharing, handoff protocols, and message passing conventions
- [LangGraph Persistence - Checkpointers](https://langchain-ai.github.io/langgraph/concepts/persistence/): Complete documentation on checkpoint mechanisms, state schemas with TypedDict, replay/resume patterns
- [LangGraph Orchestrator-Worker Pattern](https://docs.langchain.com/oss/python/langgraph/workflows-agents): Full code example showing Send() API for parallel execution and result aggregation
- [Command for Multi-Agent Handoffs](https://blog.langchain.com/command-a-new-tool-for-multi-agent-architectures-in-langgraph/): Announcement and examples of Command primitive for state updates during handoffs
- [Multi-Agent Supervisor Tutorial](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/): Complete implementation with handoff tools and context sharing
- [Human-in-the-Loop with Interrupts](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/add-human-in-the-loop/): Detailed examples of interrupt/resume patterns for approval workflows
- [LangGraph Reducer Functions](https://github.com/langchain-ai/langgraph/discussions/2975): Discussion of reducer patterns for parallel state updates and conflict resolution

### AutoGen State Persistence and Handoffs
- [AutoGen Managing State](https://microsoft.github.io/autogen/stable//user-guide/agentchat-user-guide/tutorial/state.html): Complete documentation of save_state()/load_state() with code examples for persistent sessions
- [AutoGen Handoff Patterns](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/design-patterns/handoffs.html): Implementation guide for agent delegation using tool calls and context preservation

### CrewAI Context Sharing and Memory
- [CrewAI Tasks and Context](https://docs.crewai.com/en/concepts/tasks): Documentation on task output sharing via context parameter
- [CrewAI Memory System](https://www.geeksforgeeks.org/artificial-intelligence/memory-in-crewai/): Explanation of short-term, long-term, entity, and contextual memory components

### Error Recovery and Fault Tolerance
- [Multi-Agent Error Handling Best Practices](https://procodebase.com/article/implementing-error-handling-and-recovery-in-multi-agent-systems): Comprehensive guide to retry patterns, circuit breakers, and checkpoint recovery
- [Error Recovery in AI Agents](https://www.gocodeo.com/post/error-recovery-and-fallback-strategies-in-ai-agent-development): Fallback strategies and state preservation during failures
- [Retry Pattern Best Practices](https://harish-bhattbhatt.medium.com/best-practices-for-retry-pattern-f29d47cd5117): Exponential backoff, jitter, and circuit breaker patterns

### Conflict Resolution and Transaction Patterns
- [Optimistic Concurrency Control](https://en.wikipedia.org/wiki/Optimistic_concurrency_control): Database-inspired conflict detection and resolution strategies
- [Design Patterns for Multi-Agent Future](https://dev.to/rohit_gavali_0c2ad84fe4e0/design-patterns-for-a-multi-agent-future-3jpe): Rollback contracts and transaction patterns for multi-agent coordination
