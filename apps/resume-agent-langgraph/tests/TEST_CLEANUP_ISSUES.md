# Test Cleanup Issues

This document tracks pre-existing test issues discovered during test reorganization on 2025-10-28.

## Overview

5 test files have import errors or reference outdated code that was refactored. These issues existed before the test reorganization and need to be addressed to restore full test coverage.

## Issue Details

### 1. tests/integration/test_job_analysis.py

**Problem**: References old `ConversationState` schema that doesn't exist

**Current State Schema**: `ResumeAgentState` (from `src/resume_agent/state/schemas.py`)

**Required Changes**:
- Update imports from `ConversationState` to `ResumeAgentState`
- Update all state type hints and instantiations
- Verify test logic still makes sense with new state schema

**Affected Lines**: Unknown (needs detailed inspection)

**Priority**: HIGH (integration test for core job analysis functionality)

---

### 2. tests/integration/test_resume_tailoring.py

**Problem**: References non-existent `parse_resume_yaml` function

**Current Resume Parser Functions** (from `src/resume_agent/tools/resume_parser.py`):
- `load_master_resume()` - Returns dict[str, Any]
- `extract_skills_from_resume(resume_data: dict)` - Returns list[str]
- `extract_achievements_from_resume(resume_data: dict)` - Returns list[dict]

**Required Changes**:
- Replace `parse_resume_yaml()` calls with appropriate alternative
- Most likely replacement: `load_master_resume()`
- Update test logic to match current resume parsing API

**Affected Lines**:
```
Line 28: Import statement
Line 234-261: test_parse_resume_yaml_not_dict_root()
Line 242-251: test_parse_resume_yaml_invalid_personal_info()
Line 253-261: test_parse_resume_yaml_invalid_employment_history()
```

**Priority**: HIGH (integration test for resume tailoring workflow)

---

### 3. tests/integration/test_job_analysis_workflow.py

**Problem**: References old `JobAnalysisWorkflowState` schema that doesn't exist

**Current State Schemas** (from `src/resume_agent/state/schemas.py`):
- `ResumeAgentState` - Main state with all fields
- `JobAnalysisState` - Focused subset for job analysis only

**Required Changes**:
- Update imports from `JobAnalysisWorkflowState` to `JobAnalysisState` or `ResumeAgentState`
- Update all state type hints and instantiations
- Determine if tests need full `ResumeAgentState` or just `JobAnalysisState`
- Verify workflow progression logic still valid

**Affected Lines**:
```
Line 32: Import statement
Line 295: Test docstring
Line 308-321: test_job_analysis_workflow_state_schema()
Line 333-396: Additional state validation tests
Line 452-465: Helper function create_job_analysis_state()
```

**Priority**: HIGH (tests multi-step workflow coordination)

---

### 4. tests/integration/test_modular_structure.py

**Problem**: References old `ConversationState` schema

**Current State Schema**: `ResumeAgentState`

**Required Changes**:
- Update imports from `ConversationState` to `ResumeAgentState`
- Update validation checks in module structure tests
- Ensure all exported state types are validated

**Affected Lines**:
```
Line 32: Import check
Line 36: Print statement
Line 100: Second import check
```

**Priority**: MEDIUM (validates module structure, less critical than workflow tests)

---

### 5. tests/unit/test_nodes.py

**Problem**: Multiple issues - old `ConversationState` schema and outdated node signatures

**Current Issues**:
- Uses `ConversationState` instead of `ResumeAgentState`
- Node function signatures may have changed
- State structure expectations may be outdated

**Required Changes**:
- Update imports to use `ResumeAgentState`
- Review all node function signatures against current implementation
- Update test state dictionaries to match current schema
- Update assertions to match current node return values

**Affected Lines**:
```
Line 5: Import statement
Line 11-20: test_conversation_node() state setup
Line 41-50: test_llm_invocation_node() state setup
```

**Priority**: HIGH (unit tests for core node functions)

---

### 6. tests/unit/test_workflow_nodes.py

**Problem**: References old `JobAnalysisWorkflowState` schema

**Current State Schema**: `JobAnalysisState` or `ResumeAgentState`

**Required Changes**:
- Update imports from `JobAnalysisWorkflowState` to appropriate schema
- Update all state instantiations and type hints
- Verify helper functions match current implementation

**Affected Lines**:
```
Line 29: Import statement
Line 333-370: State default value tests
Line 370-396: Pydantic validation tests
Line 452-465: create_job_analysis_state() helper function
```

**Priority**: HIGH (unit tests for workflow-specific nodes)

---

## Root Cause Analysis

**Timeline**:
1. Initial implementation used `ConversationState` and `JobAnalysisWorkflowState`
2. State schema was refactored to unified `ResumeAgentState` with focused `JobAnalysisState`
3. Some functions were removed/renamed (e.g., `parse_resume_yaml`)
4. Tests were not updated to match refactored code
5. Tests accumulated drift from implementation

**Lessons**:
- Need test-driven refactoring approach (update tests first)
- Could benefit from contract tests to catch schema changes
- Consider using type checking (mypy) in CI to catch these earlier

---

## Recommended Fix Order

1. **Phase 1 - Schema Updates** (can be done in parallel)
   - Fix `test_modular_structure.py` (simplest - just import changes)
   - Fix `test_job_analysis.py` (schema update)
   - Fix `test_nodes.py` (schema + signature updates)
   - Fix `test_workflow_nodes.py` (schema update)
   - Fix `test_job_analysis_workflow.py` (schema update)

2. **Phase 2 - API Updates**
   - Fix `test_resume_tailoring.py` (function signature changes)

3. **Phase 3 - Validation**
   - Run full test suite
   - Verify test coverage is adequate
   - Consider adding new tests for recently added features

---

## Testing Status

### Working Tests (53 tests total)

**Unit Tests** (44 tests):
- ✅ `test_data_access.py` - All data access wrapper tests passing
- ✅ `test_resume_parser.py` - Resume parser tool tests passing
- ✅ `test_browser_automation_structure.py` - Static analysis tests passing
- ✅ `test_config.py` - Configuration tests passing

**Contract Tests** (9 tests):
- ✅ `test_mcp_tools.py` - MCP tool contract tests passing

### Broken Tests (count unknown until fixed)

**Integration Tests**:
- ❌ `test_job_analysis.py` - Schema mismatch
- ❌ `test_resume_tailoring.py` - Missing function
- ❌ `test_job_analysis_workflow.py` - Schema mismatch
- ❌ `test_modular_structure.py` - Schema mismatch
- ❓ `test_llm_provider.py` - Status unknown

**Unit Tests**:
- ❌ `test_nodes.py` - Schema mismatch + signature changes
- ❌ `test_workflow_nodes.py` - Schema mismatch

**E2E Tests**:
- ❓ `test_agent.py` - Status unknown (may have schema issues)
- ❓ `test_job_analysis_e2e.py` - Status unknown (requires API keys)

---

## Commands to Run

```bash
# Attempt to run each broken test individually
pytest tests/integration/test_job_analysis.py -v
pytest tests/integration/test_resume_tailoring.py -v
pytest tests/integration/test_job_analysis_workflow.py -v
pytest tests/integration/test_modular_structure.py -v
pytest tests/unit/test_nodes.py -v
pytest tests/unit/test_workflow_nodes.py -v

# Run all working tests
pytest tests/unit/test_data_access.py tests/unit/test_resume_parser.py tests/unit/test_browser_automation_structure.py tests/unit/test_config.py tests/contract/test_mcp_tools.py -v

# After fixes - run full suite
pytest -v
```

---

## Related Files

**Current Implementation**:
- `src/resume_agent/state/schemas.py` - Current state schemas
- `src/resume_agent/state/__init__.py` - State exports
- `src/resume_agent/tools/resume_parser.py` - Current resume parser API
- `src/resume_agent/graph.py` - Main graph with current node signatures

**Documentation**:
- `apps/resume-agent-langgraph/CLAUDE.md` - LangGraph implementation guide
- `apps/resume-agent-langgraph/docs/state-schema.md` - State schema documentation

---

## Completion Criteria

- [ ] All 5 broken test files fixed
- [ ] Full test suite runs without import errors
- [ ] Test coverage maintained or improved
- [ ] Test documentation updated if needed
- [ ] CI/CD pipeline passing (if exists)

---

**Created**: 2025-10-28
**Status**: Open
**Assignee**: TBD
