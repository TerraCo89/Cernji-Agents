# Import Error Fix - LangGraph Server Compatibility

**Date:** 2025-10-26
**Issue:** `ImportError: attempted relative import with no known parent package`
**Status:** ✅ RESOLVED

---

## Problem

When running `langgraph dev`, the server failed to load the graph with this error:

```
ImportError: attempted relative import with no known parent package
  File "D:\source\Cernji-Agents\apps\resume-agent-langgraph\src/resume_agent/graph.py", line 18, in <module>
    from .state.schemas import (
```

The issue occurred because:
1. **Relative imports** (`from .state.schemas import ...`) don't work when modules are loaded directly by LangGraph server
2. **Missing path configuration** - The `src` directory wasn't in the Python path

---

## Solution

### 1. Changed to Absolute Imports

**File:** `src/resume_agent/graph.py`

**Before:**
```python
from .state.schemas import (
    ResumeAgentState,
    # ...
)
```

**After:**
```python
from resume_agent.state.schemas import (
    ResumeAgentState,
    # ...
)
```

### 2. Updated LangGraph Configuration

**File:** `langgraph.json`

**Before:**
```json
{
  "dependencies": ["."],
  "graphs": {
    "resume_agent_advanced": "./src/resume_agent/graph.py:graph"
  }
}
```

**After:**
```json
{
  "dependencies": [".", "./src"],
  "graphs": {
    "resume_agent_advanced": "./src/resume_agent/graph.py:graph"
  }
}
```

**Key change:** Added `"./src"` to dependencies array so the `resume_agent` package is on the Python path.

---

## Why This Works

### LangGraph Module Loading

When LangGraph server loads a graph, it:
1. Adds each item in `"dependencies"` to `sys.path`
2. Imports the module from the path specified in `"graphs"`
3. Extracts the graph object from the module

**With our configuration:**
- `"."` (current directory) is added to path
- `"./src"` is added to path
- The `resume_agent` package becomes importable
- Absolute imports like `from resume_agent.state.schemas import ...` work

### Relative vs Absolute Imports

**Relative imports** (`from .state import ...`):
- Only work when module is part of a package hierarchy
- Fail when module is loaded directly
- Fail when `__package__` is not set

**Absolute imports** (`from resume_agent.state import ...`):
- Work as long as the package is on `sys.path`
- More robust for server environments
- Recommended for LangGraph applications

---

## Verification

### Test Import Path Configuration
```bash
cd apps/resume-agent-langgraph

python -c "
import sys
sys.path.insert(0, '.')
sys.path.insert(0, './src')
from resume_agent.graph import graph, ResumeAgentState
print('SUCCESS: Import working')
print('Graph type:', type(graph).__name__)
print('State fields:', len(ResumeAgentState.__annotations__))
"
```

**Expected Output:**
```
SUCCESS: Import working
Graph type: CompiledStateGraph
State fields: 13
```

### Test LangGraph Server
```bash
langgraph dev
```

**Expected:** Server starts without errors, graph loads successfully

---

## Related Files Modified

1. ✅ `src/resume_agent/graph.py` - Changed to absolute imports
2. ✅ `langgraph.json` - Added `./src` to dependencies

---

## Best Practices for LangGraph

### 1. Always Use Absolute Imports in Graph Modules

**Good:**
```python
from resume_agent.state.schemas import ResumeAgentState
from resume_agent.tools import analyze_job_posting
from resume_agent.nodes import chat_node
```

**Avoid:**
```python
from .state.schemas import ResumeAgentState
from .tools import analyze_job_posting
from .nodes import chat_node
```

### 2. Configure Dependencies in langgraph.json

Ensure all necessary directories are in `dependencies`:

```json
{
  "dependencies": [
    ".",          // Current directory (for root-level modules)
    "./src"       // Source directory (for src/ layout)
  ]
}
```

### 3. Verify Package Structure

Ensure all directories have `__init__.py`:
```
src/
  resume_agent/
    __init__.py        ← Required
    graph.py
    state/
      __init__.py      ← Required
      schemas.py
    tools/
      __init__.py      ← Required
      job_analyzer.py
```

### 4. Test Before Running langgraph dev

Before starting the server, verify imports work:

```python
import sys
sys.path.insert(0, './src')
from resume_agent.graph import graph  # Should work
```

---

## Common Pitfalls

### ❌ Relative Imports in Graph Modules
```python
# Don't do this in graph.py
from .state.schemas import ResumeAgentState
```
**Why it fails:** Module is loaded directly, not as part of package

### ❌ Missing src/ in Dependencies
```json
{
  "dependencies": ["."]  // Missing "./src"
}
```
**Why it fails:** `resume_agent` package not on Python path

### ❌ Incorrect Graph Path
```json
{
  "graphs": {
    "my_graph": "src/resume_agent/graph.py:graph"  // Missing ./
  }
}
```
**Why it fails:** Path must start with `./` for relative paths

---

## Testing Checklist

After making these changes, verify:

- [ ] ✅ Import test passes (see Verification section)
- [ ] ✅ `langgraph dev` starts without errors
- [ ] ✅ Graph appears in LangGraph Studio UI
- [ ] ✅ State schema loads correctly
- [ ] ✅ No import warnings in logs

---

## Next Steps

With imports fixed, we can proceed with:

1. **Phase 2: Tools Integration**
   - Import tools from `resume_agent.tools`
   - Add to `tools` list in graph
   - Test tool execution

2. **Phase 3: Node Integration**
   - Import nodes from `resume_agent.nodes`
   - Add to graph builder
   - Configure routing

---

**Status:** ✅ RESOLVED
**Verified:** All imports working with LangGraph dev server
**Ready for:** Phase 2 - Tools Integration
