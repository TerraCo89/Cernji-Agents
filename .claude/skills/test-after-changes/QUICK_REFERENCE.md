# Test After Changes - Quick Reference Card

## Fast Validation (< 30 seconds)

```bash
# Windows
python -m compileall -q . && pytest --collect-only -q

# Or use the script
.\scripts\validate-changes.ps1
```

```bash
# Linux/macOS
python -m compileall -q . && pytest --collect-only -q

# Or use the script
./scripts/validate-changes.sh
```

---

## Validation Workflow (in order)

| # | Check | Command | Time | Pass Criteria |
|---|-------|---------|------|---------------|
| 1 | Syntax | `python -m compileall -q .` | <5s | No output |
| 2 | Imports (static) | `ruff check --select F401,F811,F821,E999 .` | <10s | Exit code 0 |
| 3 | Imports (dynamic) | `pytest --collect-only -q` | <15s | No errors |
| 4 | Service startup | Test service starts | <30s | Service runs |
| 5 | Tests | `pytest` | <2m | All pass |

---

## Service-Specific Imports

### Resume Agent LangGraph
```bash
cd apps/resume-agent-langgraph
python -c "from graph_registry import list_graphs; print(list_graphs())"
python -c "from examples.minimal_agent import build_graph"
```

### Resume Agent (MCP)
```bash
cd apps/resume-agent
python -c "import resume_agent"
```

---

## Common Issues

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: X` | Add `__init__.py` or fix import path |
| `ImportError: cannot import Y` | Check if Y was moved/renamed |
| `F401 unused import` | Remove import or add to `__init__.py` |
| `Circular import` | Restructure code or lazy import |

---

## Git Workflow

```bash
# 1. Make changes
vim src/my_module.py

# 2. Quick validation
python -m compileall -q . && pytest --collect-only -q

# 3. Full validation (if quick passes)
.\scripts\validate-changes.ps1

# 4. Commit (only if all pass)
git add .
git commit -m "feat: my changes"
```

---

## Exit Criteria

✅ All checks must pass before committing:
- [ ] Syntax validation
- [ ] Import validation
- [ ] Service startup
- [ ] Tests passing

**Only proceed when ALL ✅**

---

## Invoke the Skill

Ask Claude Code:
```
Use the test-after-changes skill
```

Or it will automatically invoke after code changes.
