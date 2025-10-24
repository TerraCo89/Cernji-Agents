# Implementation Plan: LangGraph Resume Agent

**Branch**: `006-langgraph-resume-agent` | **Date**: 2025-10-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-langgraph-resume-agent/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Reimplement the Resume Agent using LangGraph for workflow orchestration while maintaining 100% functional parity with the existing Claude Agent SDK implementation. This is an experimental comparison to evaluate LangGraph's developer experience, maintainability, and state management capabilities for multi-step job application workflows (job analysis → resume tailoring → cover letter generation → portfolio search).

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: LangGraph (workflow orchestration), FastMCP 2.0 (MCP server), Claude Agent SDK, Pydantic (schemas), sentence-transformers (embeddings), langchain-text-splitters (chunking), sqlite-vec (vector search)
**Storage**: SQLite with sqlite-vec extension (existing resume_agent.db schema, no migration required)
**Testing**: pytest with contract tests for MCP tools, integration tests for workflows
**Target Platform**: Windows 10+, deployed as single-file Python application via UV package manager
**Project Type**: Single application (monolithic MCP server)
**Performance Goals**: Job analysis <15s, resume tailoring <20s, cover letter <25s, complete workflow <60s
**Constraints**: Must maintain backward compatibility with existing 22 MCP tool interfaces, must use existing SQLite schema without migration, must integrate with existing observability server (no protocol changes)
**Scale/Scope**: Single-user system, 22 MCP tools/slash commands, 7 core workflows, ~5000 LOC estimated

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gates (Before Phase 0)

- [x] Does this feature belong in an existing app or require a new one?
  - **Requires new app**: `apps/resume-agent-langgraph/` parallel to existing `apps/resume-agent/`
  - **Justification**: This is an experimental implementation to compare LangGraph vs Claude Agent SDK. Must coexist with existing implementation for evaluation.

- [x] If new app: Is the complexity justified? (Current count → new count)
  - **Current**: 3 apps (resume-agent, observability-server, client)
  - **New**: 4 apps (adds resume-agent-langgraph)
  - **Justified**: This is a time-boxed experiment. Once evaluation is complete, one implementation will be removed (either keep LangGraph or revert to Claude Agent SDK).

- [⚠️] Can this be achieved without adding new dependencies?
  - **No**: Requires LangGraph library (new dependency)
  - **Justification**: LangGraph is the entire point of this experiment - evaluating its workflow orchestration capabilities vs. Claude Agent SDK approach.

- [x] Does this follow the Data Access Layer pattern?
  - **Yes**: Will reuse existing DAL (data access functions) from current resume-agent implementation
  - **Implementation**: LangGraph nodes will call existing `data_read_*` and `data_write_*` functions

- [x] Are performance requirements defined?
  - **Yes**: Documented in spec.md Success Criteria (SC-003)
  - **Targets**: Job analysis <15s, resume tailoring <20s, cover letter <25s, complete workflow <60s

- [x] Is observability integration planned?
  - **Yes**: Will maintain existing observability hooks at workflow node boundaries
  - **Integration**: LangGraph state transitions trigger observability events

### Post-Design Gates (After Phase 1)

- [x] Are all data schemas defined with Pydantic/TypeScript types?
  - **Yes**: All workflow state schemas defined with Pydantic in data-model.md
  - **Schemas**: ApplicationWorkflowState, JobAnalysisWorkflowState, ResumeTailoringWorkflowState
  - **Validation**: All existing data entities (JobAnalysis, TailoredResume, etc.) remain Pydantic-validated

- [x] Are contract tests planned for all interfaces?
  - **Yes**: Three-tier testing strategy documented in research.md and contracts/mcp-tools.md
  - **Contract tests**: Verify all 22 MCP tool signatures match original implementation
  - **Integration tests**: Test complete workflows with mocked external services
  - **Unit tests**: Test individual LangGraph nodes in isolation

- [x] Is the implementation the simplest approach?
  - **Yes**: Reuses existing DAL functions (no refactoring), adds minimal LangGraph orchestration layer
  - **Simplicity**: StateGraph with functional nodes, no complex abstractions
  - **Justification**: LangGraph provides state persistence, error handling, and visualization without custom implementation

- [x] Are all dependencies justified in Complexity Tracking?
  - **Yes**: See Complexity Tracking table
  - **Justification**: LangGraph dependency is the experiment's purpose; 4th app is temporary for A/B comparison

**Reference**: See `.specify/memory/constitution.md` for complete principles

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```
apps/resume-agent-langgraph/
├── resume_agent_langgraph.py  # Single-file MCP server (main entry point)
├── pyproject.toml              # UV dependencies
├── .env.example                # Environment template
├── README.md                   # Setup and usage docs
├── CLAUDE.md                   # Agent-specific development guidance
└── tests/
    ├── contract/               # MCP tool interface tests
    │   ├── test_mcp_tools.py
    │   └── test_workflow_state.py
    ├── integration/            # Workflow integration tests
    │   ├── test_job_analysis_workflow.py
    │   ├── test_resume_tailoring_workflow.py
    │   ├── test_complete_application_workflow.py
    │   └── test_error_handling.py
    └── unit/                   # Node logic unit tests
        ├── test_langgraph_nodes.py
        ├── test_state_management.py
        └── test_caching.py

# Reuses existing shared directories:
data/resume_agent.db            # Existing SQLite database (no changes)
resumes/                        # Existing resume files (no changes)
job-applications/               # Existing application artifacts (no changes)
```

**Structure Decision**: Single-file Python application following existing `apps/resume-agent/` pattern. LangGraph implementation lives in `apps/resume-agent-langgraph/resume_agent_langgraph.py` as a self-contained MCP server. Reuses existing data access layer and SQLite backend without modification.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation                      | Why Needed                                                                                              | Simpler Alternative Rejected Because                                                                                                          |
|--------------------------------|---------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| 4th application (3→4)          | Experimental comparison of LangGraph vs Claude Agent SDK orchestration approaches                       | Cannot modify existing app in-place (would break production use). Must coexist for A/B evaluation. Temporary - one will be removed post-eval. |
| New dependency (LangGraph)     | LangGraph provides state machine orchestration, workflow persistence, and visual debugging capabilities | This is the experiment's purpose - evaluating LangGraph's DX vs current approach. No evaluation possible without adding the dependency.       |

