# Test After Changes

Quick validation workflow to run after making functional code changes. Catches broken imports, syntax errors, and service issues before committing.

## When to Use This Skill

**ALWAYS use after:**
- Moving/renaming files or modules
- Refactoring imports
- Changing function signatures
- Adding/removing dependencies
- Modifying service startup code
- Any code changes that could break existing functionality

**DO NOT use for:**
- Documentation-only changes (*.md files)
- Configuration changes that don't affect code (unless they affect imports/dependencies)
- Adding comments only

---

## Quick Validation Workflow

Run these checks in order (fastest to slowest). Stop at first failure and fix before proceeding.

### 1. Syntax Validation (< 5 seconds)
```bash
# Validate Python syntax across entire project
python -m compileall -q .

# Or for specific app
python -m compileall -q apps/resume-agent-langgraph
```

**Pass criteria**: No output = success
**If fails**: Fix syntax errors shown in output

---

### 2. Import Validation (< 10 seconds)
```bash
# Fast static analysis with ruff
ruff check --select F401,F811,F821,E999 .

# Test collection (validates all test imports)
pytest --collect-only -q
```

**Pass criteria**: Exit code 0, no errors
**If fails**: Fix import errors (missing imports, moved modules, circular dependencies)

---

### 3. Quick Import Smoke Test (< 15 seconds)

For each modified service, test critical imports:

**Resume Agent (MCP Server)**:
```bash
cd apps/resume-agent
python -c "import resume_agent; print('✅ Resume agent imports OK')"
```

**Resume Agent LangGraph**:
```bash
cd apps/resume-agent-langgraph
python -c "from examples.minimal_agent import build_graph; print('✅ Minimal agent OK')"
python -c "from graph_registry import get_graph, list_graphs; print('✅ Graph registry OK')"
python -c "import resume_agent_langgraph; print('✅ Main module OK')"
```

**Pass criteria**: All imports succeed with ✅
**If fails**: Fix import paths, missing __init__.py, or missing dependencies

---

### 4. Service Startup Test (< 30 seconds)

Start the service and verify it initializes without errors:

**Resume Agent (MCP Server)**:
```bash
cd apps/resume-agent
timeout 10 uv run resume_agent.py 2>&1 | grep -q "MCP Server running" && echo "✅ Service starts OK"
```

**Resume Agent LangGraph (FastAPI)**:
```bash
cd apps/resume-agent-langgraph
# Start server in background
uvicorn fastapi_server:app --host 127.0.0.1 --port 8080 &
SERVER_PID=$!

# Wait for startup
sleep 3

# Check health
curl -f http://127.0.0.1:8080/health && echo "✅ FastAPI OK"

# Cleanup
kill $SERVER_PID
```

**LangGraph Dev Server**:
```bash
cd apps/resume-agent-langgraph
# Check langgraph.json is valid
python -c "import json; json.load(open('langgraph.json')); print('✅ Config valid')"

# Test graph registry
python -c "from graph_registry import list_graphs; print('Graphs:', list_graphs())"
```

**Pass criteria**: Service starts without errors, responds to health checks
**If fails**: Check error logs, fix startup issues

---

### 5. Unit Tests (< 2 minutes)

Run focused tests for changed code:

```bash
# Run all tests
pytest

# Or run specific test file
pytest tests/test_nodes.py -v

# Or run tests for specific function/class
pytest tests/test_nodes.py::test_analyze_job_node -v

# With coverage
pytest --cov=src --cov-report=term-missing
```

**Pass criteria**: All tests pass
**If fails**: Fix failing tests or update tests to match new behavior

---

## Service-Specific Checklists

### Resume Agent (MCP Server)
- [ ] `python -c "import resume_agent"` succeeds
- [ ] MCP server starts without errors
- [ ] Database migrations applied (if schema changed)
- [ ] SQLite database accessible at expected path

### Resume Agent LangGraph
- [ ] `from graph_registry import list_graphs` succeeds
- [ ] All registered graphs listed: `['resume_agent', 'minimal_agent']`
- [ ] FastAPI server starts on port 8080
- [ ] LangGraph dev server can compile graphs
- [ ] Checkpointer database accessible

### Agent Chat UI
- [ ] `pnpm build` succeeds
- [ ] No TypeScript errors
- [ ] Dev server starts on port 3000
- [ ] Can connect to LangGraph backend

### Observability Server
- [ ] Server starts on configured port
- [ ] WebSocket connections accepted
- [ ] SQLite WAL mode database accessible

---

## Complete Validation Script

Use this when you want to run ALL checks:

```bash
#!/bin/bash
# validate-changes.sh - Run after code changes

set -e  # Exit on first error

echo "🔍 Post-Change Validation"
echo "========================"

# 1. Syntax
echo -e "\n1️⃣  Checking syntax..."
python -m compileall -q . && echo "✅ Syntax OK" || exit 1

# 2. Imports (static)
echo -e "\n2️⃣  Checking imports (static)..."
ruff check --select F401,F811,F821,E999 . && echo "✅ Import analysis OK" || exit 1

# 3. Imports (dynamic)
echo -e "\n3️⃣  Checking imports (pytest collection)..."
pytest --collect-only -q && echo "✅ Test collection OK" || exit 1

# 4. Critical imports
echo -e "\n4️⃣  Testing critical imports..."
cd apps/resume-agent-langgraph
python -c "from graph_registry import list_graphs; print('Graphs:', list_graphs())" || exit 1
cd ../..
echo "✅ Critical imports OK"

# 5. Tests
echo -e "\n5️⃣  Running tests..."
pytest -q && echo "✅ Tests passed" || exit 1

echo -e "\n========================"
echo "✅ All validations passed!"
echo "Safe to commit."
```

**Make it executable**:
```bash
chmod +x scripts/validate-changes.sh
```

**Usage**:
```bash
# From project root
./scripts/validate-changes.sh

# Or make it a git hook
cp scripts/validate-changes.sh .git/hooks/pre-commit
```

---

## Quick Reference: Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'X'` | Add `__init__.py` to directory or fix import path |
| `ImportError: cannot import name 'Y'` | Check if Y was renamed/moved, update import |
| `SyntaxError` | Fix syntax error at reported line |
| `F401 unused import` | Remove unused import or add to `__init__.py` exports |
| `Circular import` | Restructure code or use lazy imports |
| Service won't start | Check logs, verify config files, check port availability |
| Tests fail after refactor | Update tests to match new signatures/behavior |

---

## Integration with Git Workflow

**Recommended workflow**:

```bash
# 1. Make code changes
vim src/my_module.py

# 2. Run quick validation (< 30 seconds)
python -m compileall -q . && pytest --collect-only -q

# 3. If quick validation passes, run full validation
./scripts/validate-changes.sh

# 4. Commit only if all checks pass
git add .
git commit -m "feat: my changes"
```

**Add to pre-commit hook** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-ast

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.2
    hooks:
      - id: ruff
        args: [--fix, --select, F,I]
```

---

## Success Criteria

**Minimum requirements before committing**:
- ✅ All syntax checks pass
- ✅ All import checks pass
- ✅ Modified services start successfully
- ✅ All existing tests still pass

**Ideal state**:
- ✅ All minimum requirements met
- ✅ Added tests for new functionality
- ✅ Code coverage maintained or improved
- ✅ No new ruff/mypy warnings

---

## Exit Checklist

Before marking task complete, verify:
- [ ] Ran syntax validation
- [ ] Ran import validation
- [ ] Tested service startup
- [ ] All tests passing
- [ ] Ready to commit

**If any check fails**: Stop, fix the issue, and re-run the validation workflow.

**Only proceed to commit when ALL checks pass.**
