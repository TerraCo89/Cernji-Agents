# Python Refactoring Impact Analysis Tools

This directory contains comprehensive examples of tools and techniques for **planning and analyzing refactoring operations before execution**. These tools help you identify what will break BEFORE you make changes.

## Overview

Refactoring Python code safely requires understanding dependencies before making changes. This suite demonstrates three complementary approaches:

1. **AST-based Analysis** - Fast, built-in Python solution
2. **Rope Library** - Preview exact changes before applying
3. **PyDeps** - Visual dependency graphs

## Why Pre-Refactoring Analysis Matters

❌ **Without Analysis:**
- Move a file → 10 imports break
- Rename a class → hidden dependencies fail
- Refactor a module → circular dependency introduced
- Hours debugging what went wrong

✅ **With Analysis:**
- See ALL dependencies upfront
- Preview exact changes
- Identify circular dependencies
- Execute with confidence

## Tools Demonstrated

### 1. AST-based Dependency Analyzer (`01_ast_dependency_analyzer.py`)

**Pure Python solution** using the built-in `ast` module.

**Features:**
- ✅ Zero external dependencies
- ✅ Fast analysis
- ✅ Finds reverse dependencies (who imports this?)
- ✅ Shows exact import locations (line numbers)
- ✅ Generates impact reports

**Best for:**
- Quick dependency checks
- CI/CD pipeline integration
- Projects without Graphviz
- Programmatic dependency analysis

**Usage:**
```bash
python 01_ast_dependency_analyzer.py
```

**Example Output:**
```
Impact Analysis for 'demo_project.module_a'
============================================================

2 module(s) will be affected:

📦 demo_project.module_b
   File: D:\source\demo_project\module_b.py
   Line 2: from demo_project.module_a import ClassA, function_a

📦 demo_project.module_c
   File: D:\source\demo_project\module_c.py
   Line 2: from demo_project.module_a import ClassA

============================================================
⚠️  All listed imports will need updating if you move this module!
```

### 2. Rope Refactoring Preview (`02_rope_preview_refactoring.py`)

**Industry-standard refactoring library** with dry-run capabilities.

**Features:**
- ✅ Preview changes before applying (DRY RUN!)
- ✅ Shows exact diffs
- ✅ Handles complex refactorings (rename, move, extract)
- ✅ Updates all references automatically
- ✅ Integrates with IDEs (PyCharm, VS Code)

**Best for:**
- Seeing exact code changes
- Automated refactoring
- IDE integration
- Complex multi-file operations

**Usage:**
```bash
# Interactive mode
python 02_rope_preview_refactoring.py

# Specific operations
python 02_rope_preview_refactoring.py rename
python 02_rope_preview_refactoring.py move-func
python 02_rope_preview_refactoring.py move-module
```

**Example Output:**
```
📝 PREVIEW: Renaming ClassA to ClassAlpha
======================================================================

📋 Change Description:
Renamed ClassA to ClassAlpha in module_a.py

📄 Files that will be modified:
  - module_a.py
  - module_b.py
  - module_c.py

🔍 Detailed Changes:
----------------------------------------------------------------------

File: module_a.py
- class ClassA:
+ class ClassAlpha:

File: module_b.py
- from demo_project.module_a import ClassA, function_a
+ from demo_project.module_a import ClassAlpha, function_a

======================================================================
✅ Preview complete - NO CHANGES APPLIED
```

### 3. PyDeps Integration (`03_pydeps_integration.py`)

**Visual dependency graph generator** with Graphviz.

**Features:**
- ✅ Beautiful SVG/PNG dependency graphs
- ✅ Reverse dependency graphs (critical!)
- ✅ Circular dependency detection
- ✅ Configurable depth and filtering
- ✅ Interactive SVG (hover highlights paths)

**Best for:**
- Visual understanding
- Documentation
- Architecture review
- Finding circular dependencies

**Requirements:**
```bash
pip install pydeps
# Also install Graphviz: https://graphviz.org/download/
```

**Usage:**
```bash
# Full workflow
python 03_pydeps_integration.py

# Specific operations
python 03_pydeps_integration.py full      # Full graph
python 03_pydeps_integration.py reverse   # Reverse dependencies
python 03_pydeps_integration.py cycles    # Find circular deps
python 03_pydeps_integration.py compare   # Before/after comparison
```

**Key Command:**
```bash
pydeps --reverse --only module_a demo_project
```

This shows **all modules that import module_a** - critical for refactoring!

### 4. Complete Refactoring Workflow (`04_complete_refactoring_workflow.py`)

**Combines all tools** into a comprehensive analysis pipeline.

**Workflow:**
1. **AST Analysis** - Quick dependency scan
2. **Impact Assessment** - Calculate risk metrics
3. **Risk Calculation** - Low/Medium/High risk rating
4. **Rope Preview** - Show exact changes
5. **Execution Plan** - Step-by-step instructions
6. **Report Generation** - Save analysis as Markdown

**Best for:**
- Large refactorings
- Production code
- Team workflows
- Audit trails

**Usage:**
```bash
python 04_complete_refactoring_workflow.py
```

**Example Output:**
```
🔍 COMPREHENSIVE REFACTORING ANALYSIS
================================================================================

Operation: Move module
Source:      demo_project.module_a
Destination: core

--------------------------------------------------------------------------------
📋 PHASE 1: Static Dependency Analysis (AST)
--------------------------------------------------------------------------------

✓ Found 2 modules that import demo_project.module_a
  - demo_project.module_b (3 import(s))
  - demo_project.module_c (1 import(s))

--------------------------------------------------------------------------------
📊 PHASE 2: Impact Assessment
--------------------------------------------------------------------------------

Impact Metrics:
  • Modules affected: 2
  • Import statements to update: 4

--------------------------------------------------------------------------------
⚠️  PHASE 3: Risk Assessment
--------------------------------------------------------------------------------

✅ LOW RISK - Few modules affected

--------------------------------------------------------------------------------
🔬 PHASE 4: Detailed Change Preview (Rope)
--------------------------------------------------------------------------------

[Shows exact file changes...]

📄 Report saved to: refactoring_report.md
```

## Installation

### Minimal (AST only)
```bash
# No installation needed - uses Python stdlib
python 01_ast_dependency_analyzer.py
```

### Full Suite
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Graphviz (for PyDeps)
# macOS
brew install graphviz

# Ubuntu/Debian
sudo apt-get install graphviz

# Windows
# Download from: https://graphviz.org/download/
# Add to PATH
```

## Quick Start

### 1. Analyze What Will Break

```bash
python 01_ast_dependency_analyzer.py
```

Look for the **Impact Analysis** section - this shows exactly what will break.

### 2. Preview Exact Changes

```bash
python 02_rope_preview_refactoring.py
```

Choose an operation and see the exact diff BEFORE applying.

### 3. Visualize Dependencies

```bash
python 03_pydeps_integration.py reverse
```

Open the generated SVG to see a visual graph.

### 4. Complete Analysis

```bash
python 04_complete_refactoring_workflow.py
```

Get a comprehensive report with risk assessment.

## Key Concepts

### Reverse Dependencies

**Most Important Concept for Refactoring!**

- **Forward dependency**: "What does this module import?"
- **Reverse dependency**: "What imports this module?" ⭐

**Why it matters:**
When you move/rename `module_a`, you need to know every file that imports it!

**Tools that show reverse deps:**
- AST Analyzer: `find_reverse_dependencies()`
- PyDeps: `--reverse` flag
- Rope: Automatically updates all references

### Impact Analysis

**Before moving a file, ask:**
1. How many modules import it? (Reverse deps)
2. What do they import from it? (Classes, functions, constants)
3. Are there circular dependencies?
4. What's the risk level?

### Dry-Run Refactoring

**Never apply changes blindly!**

Always preview first:
```python
# Rope example
changes = refactoring.get_changes()
print(changes.get_description())  # Preview
# Review carefully...
project.do(changes)  # Then apply
```

## Best Practices

### 1. Always Analyze Before Refactoring
```bash
# Bad
git mv module_a.py core/module_a.py  # Hope for the best

# Good
python 01_ast_dependency_analyzer.py  # See what breaks
python 02_rope_preview_refactoring.py # Preview changes
# Review carefully, then apply
```

### 2. Use Multiple Tools

Each tool has strengths:
- **AST**: Fast, scriptable
- **Rope**: Exact previews
- **PyDeps**: Visual understanding

Use all three for important refactorings!

### 3. Generate Before/After Graphs

```bash
# Before refactoring
pydeps demo_project -o before.svg

# Do refactoring
# ...

# After refactoring
pydeps demo_project -o after.svg

# Compare visually
```

### 4. Check for Circular Dependencies First

```bash
python 03_pydeps_integration.py cycles
```

Fix these BEFORE refactoring - they'll cause problems!

### 5. Save Analysis Reports

```bash
python 04_complete_refactoring_workflow.py > analysis.txt
```

Keep an audit trail, especially for large refactorings.

## Real-World Workflow

```bash
# 1. Create feature branch
git checkout -b refactor-module-structure

# 2. Analyze dependencies
python 01_ast_dependency_analyzer.py

# 3. Generate dependency graph
python 03_pydeps_integration.py full

# 4. Check for circular dependencies
python 03_pydeps_integration.py cycles

# 5. Generate reverse dependency graph
python 03_pydeps_integration.py reverse

# 6. Preview exact changes
python 02_rope_preview_refactoring.py

# 7. Review everything carefully

# 8. Apply refactoring (using Rope)
# 9. Run tests
# 10. Generate new graph to verify
python 03_pydeps_integration.py full -o after.svg

# 11. Commit
git add .
git commit -m "Refactor: Move module_a to core package"
```

## Advanced Usage

### Programmatic Integration

```python
from pathlib import Path
from ast_dependency_analyzer import DependencyAnalyzer

analyzer = DependencyAnalyzer(Path("my_project"))
analyzer.analyze_project()

# Get reverse deps
reverse_deps = analyzer.find_reverse_dependencies("my_module")

# Generate report
report = analyzer.generate_impact_report("my_module")
print(report)
```

### Custom Rope Refactorings

```python
from rope.base.project import Project
from rope.refactor.rename import Rename

project = Project("my_project")
resource = project.root.get_child("module.py")

# Preview
changes = Rename(project, resource, offset).get_changes("NewName")
print(changes.get_description())

# Apply only if satisfied
if input("Apply? (y/n): ") == "y":
    project.do(changes)

project.close()
```

### CI/CD Integration

```python
# ci_check_dependencies.py
from ast_dependency_analyzer import DependencyAnalyzer
import sys

analyzer = DependencyAnalyzer(Path("."))
analyzer.analyze_project()

# Fail if too many dependencies on core modules
critical_module = "app.core.database"
reverse_deps = analyzer.find_reverse_dependencies(critical_module)

if len(reverse_deps) > 10:
    print(f"❌ Too many modules depend on {critical_module}")
    print(f"   Refactor to reduce coupling!")
    sys.exit(1)
```

## Troubleshooting

### "pydeps command not found"
```bash
pip install pydeps
```

### "dot command not found"
Install Graphviz: https://graphviz.org/download/

### "Rope preview fails"
Make sure the file you're refactoring has valid Python syntax.

### "Circular dependency detected"
Fix circular imports before refactoring. Use PyDeps to visualize:
```bash
python 03_pydeps_integration.py cycles
```

## Files in This Directory

```
refactoring_analysis/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── 01_ast_dependency_analyzer.py      # AST-based analysis
├── 02_rope_preview_refactoring.py     # Rope dry-run examples
├── 03_pydeps_integration.py           # PyDeps integration
├── 04_complete_refactoring_workflow.py # Complete workflow
└── demo_project/                      # Example Python project
    ├── __init__.py
    ├── module_a.py                    # Will be moved
    ├── module_b.py                    # Imports module_a
    ├── module_c.py                    # Imports module_a
    └── module_d.py                    # Imports module_b
```

## Further Reading

### Documentation
- **Python AST**: https://docs.python.org/3/library/ast.html
- **Rope**: https://rope.readthedocs.io/
- **PyDeps**: https://pydeps.readthedocs.io/

### Related Tools
- **import-linter**: Enforce import rules - https://import-linter.readthedocs.io/
- **pipdeptree**: Package-level dependencies - `pip install pipdeptree`
- **findimports**: Alternative to AST approach - https://github.com/mgedmin/findimports
- **Bowler**: Safe refactoring with query syntax - https://pybowler.io/

### Articles
- "Refactoring Python Applications for Simplicity" - Real Python
- "Using Python AST to resolve dependencies" - Gaurav Sarma (Medium)
- "6 ways to improve the architecture of your Python project" - Piglei

## Contributing

These examples are for educational purposes. Feel free to adapt them to your specific refactoring needs!

## License

MIT License - See project root for details.

---

**Remember:** The goal isn't to avoid refactoring - it's to refactor **safely** by understanding the impact first!
