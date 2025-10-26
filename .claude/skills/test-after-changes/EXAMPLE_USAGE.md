# Example Usage: Test After Changes Skill

## Scenario 1: After Refactoring (Moving Files)

**User Request:**
```
Move minimal_agent.py to the examples/ directory
```

**Claude Code Response:**

```
I'll move minimal_agent.py to examples/ and update all references.

[Performs file move and import updates]

Now let me validate these changes using the test-after-changes workflow:

1️⃣ Checking syntax...
   Running: python -m compileall -q .
   ✅ Syntax check passed

2️⃣ Checking imports (static)...
   Running: ruff check --select F401,F811,F821,E999 .
   ✅ Import analysis passed

3️⃣ Testing imports (pytest collection)...
   Running: pytest --collect-only -q
   ✅ Test collection passed

4️⃣ Testing critical imports...
   Running: python -c "from graph_registry import list_graphs; ..."
   Available graphs: ['resume_agent', 'minimal_agent']
   ✅ Graph registry imports OK

5️⃣ Running tests...
   Running: pytest -q
   ✅ All tests passed (12 passed in 2.3s)

========================
✅ All validations passed!
========================

The refactoring is complete and all services are working correctly.
Changes are safe to commit.
```

---

## Scenario 2: After Adding a New Feature

**User Request:**
```
Add a new job_scraper tool to the resume agent
```

**Claude Code Response:**

```
I've added the job_scraper tool with the following changes:
- Created src/resume_agent/tools/job_scraper.py
- Updated src/resume_agent/tools/__init__.py
- Added tests in tests/test_job_scraper.py

Now validating the changes:

1️⃣ Syntax: ✅ Passed
2️⃣ Imports (static): ✅ Passed
3️⃣ Imports (pytest): ✅ Passed
4️⃣ Critical imports: ✅ Passed
5️⃣ Tests: ❌ Failed

Test output:
  tests/test_job_scraper.py::test_scrape_job_posting FAILED
  AttributeError: 'JobScraper' object has no attribute 'parse_html'

I need to fix the failing test. Let me update the JobScraper class...

[Makes fix]

Re-running validation:
5️⃣ Tests: ✅ All passed (15 passed in 3.1s)

========================
✅ All validations passed!
========================

The new job_scraper tool is ready and all tests are passing.
```

---

## Scenario 3: Validation Failure - Import Error

**User Request:**
```
Rename module_a to core_module
```

**Claude Code Response:**

```
I've renamed module_a.py to core_module.py.

Validating changes:

1️⃣ Syntax: ✅ Passed
2️⃣ Imports (static): ❌ Failed

Ruff found import issues:
  src/services/analyzer.py:5: F401 'module_a' imported but unused
  src/services/processor.py:12: F821 undefined name 'module_a'

I need to update the import statements in these files...

[Updates imports from module_a to core_module]

Re-running validation:

1️⃣ Syntax: ✅ Passed
2️⃣ Imports (static): ✅ Passed
3️⃣ Imports (pytest): ✅ Passed
4️⃣ Critical imports: ✅ Passed
5️⃣ Tests: ✅ All passed

========================
✅ All validations passed!
========================

All references to module_a have been updated to core_module.
```

---

## Scenario 4: Manual Invocation

**User Request:**
```
I just made some changes to the graph_registry.py file. Can you validate that everything still works?
```

**Claude Code Response:**

```
I'll run the test-after-changes validation workflow to verify your changes.

Running validation checks on graph_registry.py changes...

1️⃣ Syntax: ✅ Passed
2️⃣ Imports (static): ✅ Passed
3️⃣ Imports (pytest): ✅ Passed

4️⃣ Testing critical imports:
   python -c "from graph_registry import get_graph, list_graphs; ..."
   Available graphs: ['resume_agent', 'minimal_agent']
   ✅ Graph registry imports OK

5️⃣ Tests:
   Running relevant tests for graph_registry...
   tests/test_graph_registry.py ✅ All passed (8 passed in 1.2s)

========================
✅ All validations passed!
========================

Your changes to graph_registry.py are working correctly!
All imports resolve and tests are passing.
```

---

## Scenario 5: Quick Validation Only

**User Request:**
```
Just run a quick validation, skip the full test suite
```

**Claude Code Response:**

```
Running quick validation (syntax + imports only):

1️⃣ Syntax: python -m compileall -q .
   ✅ Passed

2️⃣ Imports: pytest --collect-only -q
   ✅ Passed (38 tests collected)

3️⃣ Critical imports:
   ✅ Graph registry: OK
   ✅ Resume agent: OK

========================
✅ Quick validation passed!
========================

All syntax and import checks passed.
Run 'pytest' to execute the full test suite.
```

---

## Key Patterns

### 1. Automatic Invocation
The skill is automatically invoked after:
- File moves/renames
- Import changes
- Dependency updates
- Feature additions

### 2. Progressive Validation
Checks run in order of speed (fastest first):
- If syntax fails → stop, fix syntax
- If imports fail → stop, fix imports
- If tests fail → stop, fix tests

### 3. Clear Reporting
Each check reports:
- ✅ Pass or ❌ Fail
- Specific errors if failed
- Commands run for transparency

### 4. Actionable Fixes
When validation fails:
- Shows specific error messages
- Identifies which files need fixing
- Re-runs validation after fixes
- Only marks complete when ALL checks pass

### 5. Exit Criteria
Task is only complete when:
- All validation checks pass
- User is informed of status
- Clear next steps provided
