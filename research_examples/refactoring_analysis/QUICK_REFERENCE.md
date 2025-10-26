# Quick Reference: Refactoring Impact Analysis

A one-page reference for analyzing Python refactoring operations before execution.

## The Golden Rule

**NEVER move/rename files without first finding reverse dependencies!**

Reverse dependencies = "Who imports this module?"

---

## Quick Commands

### Find What Will Break (AST)
```bash
python 01_ast_dependency_analyzer.py
```
Shows: Modules that import your target + line numbers

### Preview Exact Changes (Rope)
```bash
python 02_rope_preview_refactoring.py
```
Shows: Exact diffs before applying

### Visualize Dependencies (PyDeps)
```bash
# All dependencies
pydeps my_project -o graph.svg

# Reverse dependencies (CRITICAL!)
pydeps --reverse --only my_project.module_a my_project -o reverse.svg

# Check for circular dependencies
pydeps --show-cycles my_project
```

### Complete Analysis
```bash
python 04_complete_refactoring_workflow.py
```
Shows: Full analysis with risk assessment

---

## Pre-Refactoring Checklist

Before moving/renaming ANY file:

- [ ] Find reverse dependencies
- [ ] Count affected modules
- [ ] Check for circular dependencies
- [ ] Preview exact changes
- [ ] Assess risk (low/medium/high)
- [ ] Ensure tests exist
- [ ] Create feature branch

---

## Risk Assessment

### Low Risk (Safe to proceed)
- 0-2 modules affected
- No circular dependencies
- Good test coverage

### Medium Risk (Review carefully)
- 3-5 modules affected
- Some circular dependencies
- Moderate test coverage

### High Risk (Consider staged approach)
- 6+ modules affected
- Complex circular dependencies
- Low test coverage

---

## Code Snippets

### AST: Find Reverse Dependencies
```python
import ast
from pathlib import Path

def find_who_imports_me(project_root, target_module):
    results = {}
    for py_file in project_root.rglob("*.py"):
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == target_module:
                    results[str(py_file)] = node.lineno
    return results

# Usage
affected = find_who_imports_me(Path("."), "my_app.models")
print(f"{len(affected)} files will break!")
```

### Rope: Preview Before Applying
```python
from rope.base.project import Project
from rope.refactor.rename import Rename

project = Project(".")
module = project.root.get_child("models.py")
offset = module.read().index("class User")

changes = Rename(project, module, offset).get_changes("UserModel")

# PREVIEW (doesn't apply)
print(changes.get_description())

# Apply only after review
project.do(changes)  # <-- This applies changes
project.close()
```

### PyDeps: Reverse Dependency Graph
```bash
# See who imports module_a
pydeps --reverse --only my_app.module_a my_app -o reverse.svg

# Open reverse.svg in browser - arrows show importers
```

---

## Complete Workflow

```bash
# 1. Create branch
git checkout -b refactor-user-model

# 2. Find what will break
python 01_ast_dependency_analyzer.py

# 3. Visualize
pydeps --reverse --only my_app.models.user my_app -o before.svg

# 4. Check cycles
pydeps --show-cycles my_app

# 5. Preview changes
python 02_rope_preview_refactoring.py

# 6. Review everything carefully

# 7. Apply refactoring (using Rope in script)

# 8. Run tests
pytest

# 9. Generate after graph
pydeps my_app -o after.svg

# 10. Compare before.svg and after.svg

# 11. Commit
git add .
git commit -m "refactor: Move user model to core package"
```

---

## Common Patterns

### Pattern 1: Moving a Module
**Before**: `app/models/user.py`
**After**: `app/core/models/user.py`

**Analysis needed**:
- Find all `from app.models.user import ...`
- Update to `from app.core.models.user import ...`
- Check for circular dependencies in new location

### Pattern 2: Renaming a Class
**Before**: `class User`
**After**: `class UserModel`

**Analysis needed**:
- Find all imports of `User`
- Find all usages of `User()` in code
- Rope handles this automatically!

### Pattern 3: Splitting a Module
**Before**: `models.py` (big file)
**After**: `models/user.py`, `models/product.py`, `models/order.py`

**Analysis needed**:
- For each split: find reverse dependencies
- Update all imports to new paths
- Highest risk - do incrementally

---

## Tool Comparison

| Tool | Speed | Accuracy | Visualization | Preview | Auto-fix |
|------|-------|----------|---------------|---------|----------|
| AST  | +++   | ++       | -             | -       | -        |
| PyDeps | +   | ++       | +++           | -       | -        |
| Rope | ++    | +++      | -             | +++     | +++      |

**Use**:
- **AST** for quick scripting
- **PyDeps** for understanding/documentation
- **Rope** for actual refactoring

---

## Red Flags

### Stop and Fix First
- Circular dependencies detected
- No tests for affected modules
- More than 10 modules affected (consider splitting)
- Working on main branch (create feature branch!)

### Warning Signs
- Import statements scattered across file
- Dynamic imports (`importlib`)
- String-based imports
- `__import__()` usage

---

## Installation

### Minimal (AST only)
```bash
# Nothing to install - uses Python stdlib
```

### Full Suite
```bash
# Python packages
pip install rope pydeps

# Graphviz (for PyDeps)
# macOS
brew install graphviz

# Ubuntu
sudo apt-get install graphviz

# Windows
# Download from https://graphviz.org/download/
```

---

## Files in This Project

```
refactoring_analysis/
├── QUICK_REFERENCE.md              # This file
├── README.md                        # Full documentation
├── RESEARCH_SUMMARY.md              # Detailed findings
├── SOURCES.md                       # All references
├── requirements.txt                 # Dependencies
├── 01_ast_dependency_analyzer.py    # AST tool
├── 02_rope_preview_refactoring.py   # Rope examples
├── 03_pydeps_integration.py         # PyDeps wrapper
├── 04_complete_refactoring_workflow.py  # Full workflow
└── demo_project/                    # Example project
```

---

## Emergency Debugging

### "I moved a file and imports broke!"

1. **Find what broke**:
```bash
python 01_ast_dependency_analyzer.py
```

2. **See the damage**:
```bash
grep -r "from old.path.to.module" .
```

3. **Fix with Rope** (next time!):
Use Rope BEFORE moving to preview and auto-fix imports

### "Circular dependency detected!"

1. **Visualize it**:
```bash
pydeps --show-cycles my_app
```

2. **Fix strategies**:
- Move shared code to new module
- Use dependency injection
- Lazy imports (import inside function)

### "Tests pass but app crashes!"

**Possible causes**:
- Dynamic imports not detected by static analysis
- Import in `if TYPE_CHECKING` block
- Plugin/extension loading

**Fix**: Add manual test of affected code paths

---

## Pro Tips

1. **Always work in a branch** - Easy rollback
2. **Generate before/after graphs** - Visual proof of success
3. **Use Rope for renames** - Catches edge cases
4. **Check for cycles first** - Prevents cascading issues
5. **Small commits** - Easier to review and debug
6. **Run tests between steps** - Catch issues early

---

## One-Liner Cheatsheet

```bash
# Find reverse deps
python -c "from pathlib import Path; import ast; [print(f) for f in Path('.').rglob('*.py') if 'target_module' in open(f).read()]"

# Generate graph
pydeps --reverse --only my_module . -o rev.svg

# Preview rename (interactive)
python -m rope.refactor.rename

# Check cycles
pydeps --show-cycles .
```

---

## When to Use Each Tool

### Use AST when:
- Quick dependency check needed
- Writing custom analysis scripts
- CI/CD integration
- No Graphviz available

### Use PyDeps when:
- Need to understand architecture
- Creating documentation
- Finding circular dependencies
- Showing impact to team

### Use Rope when:
- Actually performing refactoring
- Need exact preview
- Want automatic import updates
- Complex multi-file changes

---

## Remember

> "Measure twice, cut once"

**In refactoring terms**:
1. Measure with AST (quick)
2. Measure with PyDeps (visual)
3. Measure with Rope (exact)
4. Cut (apply changes)

---

*Keep this file handy when refactoring!*
