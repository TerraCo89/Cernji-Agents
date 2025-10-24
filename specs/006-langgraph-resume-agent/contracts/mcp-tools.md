# MCP Tool Contracts: LangGraph Resume Agent

**Date**: 2025-10-23
**Feature**: LangGraph Resume Agent (006)
**Purpose**: Define MCP tool interfaces for backward compatibility verification

## Overview

The LangGraph implementation MUST maintain 100% backward compatibility with existing MCP tool signatures. This document defines the contract for all 22 MCP tools exposed by the resume agent.

**Compatibility Requirement (FR-003)**: All tool signatures, parameter names, parameter types, and return types must match the existing implementation exactly.

---

## Career Application Workflow Tools

### 1. complete_application_workflow

**Purpose**: Execute complete job application workflow (analyze → tailor → cover letter → portfolio)

**Signature**:
```python
@mcp.tool()
def complete_application_workflow(job_url: str) -> dict[str, Any]:
    """
    Complete job application workflow: analyze job, tailor resume,
    generate cover letter, and find portfolio examples.

    Args:
        job_url: URL of the job posting

    Returns:
        dict with keys: job_analysis, tailored_resume, cover_letter,
        portfolio_examples, errors (if any)
    """
```

**Parameters**:
| Name | Type | Required | Validation |
|------|------|----------|------------|
| job_url | str | Yes | Must be valid HTTP/HTTPS URL |

**Return Schema**:
```python
{
    "job_analysis": {
        "company": str,
        "job_title": str,
        "requirements": List[str],
        "skills": List[str],
        "responsibilities": List[str],
        "salary_range": str | None,
        "location": str,
        "keywords": List[str],
        "url": str,
        "fetched_at": str  # ISO 8601 datetime
    } | None,
    "tailored_resume": str | None,  # Markdown content
    "cover_letter": str | None,     # Markdown content
    "portfolio_examples": List[dict] | None,
    "errors": List[str]  # Empty list if no errors
}
```

**Error Handling**:
- Partial success: Returns completed steps even if some fail
- Errors accumulated in `errors` list
- HTTP 200 even with partial failures (errors in response body)

**Performance Target**: <60s (SC-001)

---

### 2. analyze_job_posting

**Purpose**: Analyze job posting to extract structured requirements

**Signature**:
```python
@mcp.tool()
def analyze_job_posting(job_url: str) -> dict[str, Any]:
    """
    Analyze a job posting and extract structured information.

    Args:
        job_url: URL of the job posting

    Returns:
        dict with job analysis data
    """
```

**Parameters**:
| Name | Type | Required | Validation |
|------|------|----------|------------|
| job_url | str | Yes | Must be valid HTTP/HTTPS URL |

**Return Schema**:
```python
{
    "company": str,
    "job_title": str,
    "requirements": List[str],
    "skills": List[str],
    "responsibilities": List[str],
    "salary_range": str | None,
    "location": str,
    "keywords": List[str],
    "url": str,
    "fetched_at": str,  # ISO 8601 datetime
    "cached": bool  # True if retrieved from cache
}
```

**Performance Target**: <15s new, <3s cached (SC-003)

---

### 3. tailor_resume_for_job

**Purpose**: Generate tailored resume for specific job posting

**Signature**:
```python
@mcp.tool()
def tailor_resume_for_job(job_url: str) -> dict[str, Any]:
    """
    Tailor resume for a specific job posting.

    Args:
        job_url: URL of the job posting

    Returns:
        dict with tailored resume content and metadata
    """
```

**Parameters**:
| Name | Type | Required | Validation |
|------|------|----------|------------|
| job_url | str | Yes | Must be valid HTTP/HTTPS URL |

**Return Schema**:
```python
{
    "company": str,
    "job_title": str,
    "content": str,  # Markdown formatted resume
    "keywords_integrated": List[str],
    "created_at": str,  # ISO 8601 datetime
    "file_path": str,  # Absolute path to saved resume file
    "cached": bool
}
```

**Performance Target**: <20s (SC-003)

---

### 4. generate_cover_letter

**Purpose**: Generate personalized cover letter for job application

**Signature**:
```python
@mcp.tool()
def generate_cover_letter(job_url: str, company_name: str, role_title: str) -> dict[str, Any]:
    """
    Generate a personalized cover letter for a job application.

    Args:
        job_url: URL of the job posting
        company_name: Name of the company
        role_title: Title of the role

    Returns:
        dict with cover letter content and metadata
    """
```

**Parameters**:
| Name | Type | Required | Validation |
|------|------|----------|------------|
| job_url | str | Yes | Must be valid HTTP/HTTPS URL |
| company_name | str | Yes | Non-empty string |
| role_title | str | Yes | Non-empty string |

**Return Schema**:
```python
{
    "company": str,
    "job_title": str,
    "content": str,  # Markdown formatted cover letter
    "created_at": str,  # ISO 8601 datetime
    "file_path": str,  # Absolute path to saved cover letter file
    "cached": bool
}
```

**Performance Target**: <25s (SC-003)

---

### 5. find_portfolio_examples

**Purpose**: Search GitHub portfolio for code examples matching job requirements

**Signature**:
```python
@mcp.tool()
def find_portfolio_examples(job_url: str) -> dict[str, Any]:
    """
    Find portfolio code examples matching job requirements.

    Args:
        job_url: URL of the job posting

    Returns:
        dict with portfolio examples matching job technologies
    """
```

**Parameters**:
| Name | Type | Required | Validation |
|------|------|----------|------------|
| job_url | str | Yes | Must be valid HTTP/HTTPS URL |

**Return Schema**:
```python
{
    "examples": List[{
        "example_id": int,
        "title": str,
        "description": str,
        "technologies": List[str],
        "repository_url": str,
        "code_snippet": str | None,
        "relevance_score": float  # 0.0 to 1.0
    }],
    "total_found": int,
    "technologies_matched": List[str]
}
```

**Performance Target**: <10s (spec.md user story 4)

---

## Data Access Tools (22 total - abbreviated for space)

All data access tools maintain existing signatures. Below are representative examples:

### 6. data_read_master_resume

**Signature**:
```python
@mcp.tool()
def data_read_master_resume() -> dict[str, Any]:
    """Read the master resume data."""
```

**Return Schema**: Existing MasterResume Pydantic schema

---

### 7. data_read_job_analysis

**Signature**:
```python
@mcp.tool()
def data_read_job_analysis(company: str, job_title: str) -> dict[str, Any]:
    """
    Read job analysis data for a specific application.

    Args:
        company: Company name
        job_title: Job title

    Returns:
        dict with job analysis data or error
    """
```

**Parameters**:
| Name | Type | Required | Validation |
|------|------|----------|------------|
| company | str | Yes | Non-empty string |
| job_title | str | Yes | Non-empty string |

**Return Schema**: Existing JobAnalysis Pydantic schema

---

### 8. data_write_job_analysis

**Signature**:
```python
@mcp.tool()
def data_write_job_analysis(company: str, job_title: str, job_data: dict) -> dict[str, Any]:
    """
    Write job analysis data for a specific application.

    Args:
        company: Company name
        job_title: Job title
        job_data: Job analysis data dict

    Returns:
        dict with success status and file path
    """
```

**Parameters**:
| Name | Type | Required | Validation |
|------|------|----------|------------|
| company | str | Yes | Non-empty string |
| job_title | str | Yes | Non-empty string |
| job_data | dict | Yes | Must match JobAnalysis schema |

---

### Additional Tools (9-22)

The following tools maintain existing signatures (not detailed here for brevity):

9. `data_read_tailored_resume`
10. `data_write_tailored_resume`
11. `data_read_cover_letter`
12. `data_write_cover_letter`
13. `data_write_portfolio_examples`
14. `data_list_applications`
15. `data_add_achievement`
16. `data_add_technology`
17. `data_add_portfolio_example`
18. `data_list_portfolio_examples`
19. `data_search_portfolio_examples`
20. `data_get_portfolio_example`
21. `data_update_portfolio_example`
22. `data_delete_portfolio_example`

**Contract Guarantee**: All 22 tools MUST have identical signatures to existing implementation.

---

## Contract Testing Strategy

### Test Coverage Requirements

1. **Signature Verification**:
   - Function name matches exactly
   - Parameter names match exactly
   - Parameter types match exactly
   - Return type matches exactly
   - Docstring format matches (for MCP introspection)

2. **Behavior Verification**:
   - Same inputs produce same output structure
   - Error responses match format
   - Performance targets met (SC-003)

3. **Backward Compatibility**:
   - Existing Claude Desktop configuration works without changes
   - Existing slash commands work without changes
   - Existing data files readable/writable

### Contract Test Structure

```python
# tests/contract/test_mcp_tools.py

import inspect
from apps.resume_agent import resume_agent as original
from apps.resume_agent_langgraph import resume_agent_langgraph as langgraph

def test_complete_application_workflow_signature():
    """Verify complete_application_workflow signature matches"""
    orig_sig = inspect.signature(original.complete_application_workflow)
    new_sig = inspect.signature(langgraph.complete_application_workflow)

    assert orig_sig == new_sig, "Signature mismatch"

def test_complete_application_workflow_return_schema():
    """Verify return schema matches"""
    # Mock execution
    result = langgraph.complete_application_workflow("https://example.com/job")

    assert "job_analysis" in result
    assert "tailored_resume" in result
    assert "cover_letter" in result
    assert "portfolio_examples" in result
    assert "errors" in result
```

---

## Breaking Change Policy

**PROHIBITION**: The following changes are FORBIDDEN during LangGraph implementation:

❌ Renaming MCP tools
❌ Adding required parameters to existing tools
❌ Removing parameters from existing tools
❌ Changing parameter types
❌ Changing return schema structure
❌ Changing error response format

**ALLOWED**: The following changes are acceptable:

✅ Adding optional parameters with defaults
✅ Adding new MCP tools (not removing existing)
✅ Improving performance (as long as behavior unchanged)
✅ Improving error messages (as long as format unchanged)
✅ Internal refactoring (as long as interface unchanged)

---

## Version Compatibility Matrix

| Component | Current Version | LangGraph Version | Compatible? |
|-----------|-----------------|-------------------|-------------|
| MCP Tool Signatures | 1.0.0 | 1.0.0 | ✅ Required |
| Claude Desktop Config | N/A | N/A | ✅ No changes |
| Data Schemas (DB/Files) | 1.0.0 | 1.0.0 | ✅ No changes |
| Observability Events | 1.0.0 | 1.0.0 | ✅ No changes |
| Performance Targets | See SC-003 | See SC-003 | ✅ Must maintain |

**Validation Gate**: All contract tests MUST pass before merging LangGraph implementation (Constitution Check post-design gate).
