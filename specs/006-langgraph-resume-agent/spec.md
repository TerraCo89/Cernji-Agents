# Feature Specification: LangGraph Resume Agent

**Feature Branch**: `006-langgraph-resume-agent`
**Created**: 2025-10-23
**Status**: Draft
**Input**: User description: "Create a new version of the Resume Agent using LangGraph. Functionality will remain the same. This is an experiment to compare to the Claude commands and see how it would function as a proper application, before deciding to productionise it."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Job Analysis Workflow (Priority: P1)

A job seeker provides a job posting URL and the system analyzes it to extract structured requirements, skills, and keywords.

**Why this priority**: This is the foundational capability that feeds all other features. Without accurate job analysis, resume tailoring and cover letter generation cannot be effective.

**Independent Test**: Can be fully tested by providing a job URL and verifying that structured job data (requirements, skills, responsibilities, keywords) is extracted and stored. Delivers immediate value by helping users understand what the job requires.

**Acceptance Scenarios**:

1. **Given** a valid job posting URL, **When** user requests job analysis, **Then** system extracts company name, job title, required skills, responsibilities, salary range (if available), location, and ATS keywords
2. **Given** a previously analyzed job URL, **When** user requests analysis again, **Then** system retrieves cached results without re-processing
3. **Given** a job posting with minimal information, **When** analysis is performed, **Then** system extracts available data and marks missing fields as null
4. **Given** a multilingual job posting (English/Japanese), **When** analysis is performed, **Then** system detects language and processes content appropriately

**Performance Requirements**:
- Response time: <15s for new job postings, <3s for cached results
- Error handling: Graceful degradation with user feedback if URL is invalid or unreachable
- Observability: Track analysis start, completion, and errors

---

### User Story 2 - Resume Tailoring Workflow (Priority: P1)

A job seeker provides a job posting and the system generates a tailored resume optimized for that specific role by mapping their master resume to job requirements.

**Why this priority**: This is the core value proposition - helping users create job-specific resumes that pass ATS systems and resonate with hiring managers.

**Independent Test**: Can be tested by providing job analysis data and master resume, then verifying the output contains keyword-optimized content matching job requirements. Delivers standalone value even without cover letter generation.

**Acceptance Scenarios**:

1. **Given** job analysis data and master resume, **When** user requests tailored resume, **Then** system generates resume with relevant experience highlighted and keywords integrated
2. **Given** a job requiring specific technologies, **When** resume is tailored, **Then** system emphasizes relevant projects and skills from master resume
3. **Given** multiple previous job applications, **When** user requests resume tailoring, **Then** system learns from previous tailoring decisions to improve consistency
4. **Given** insufficient matching experience, **When** resume is tailored, **Then** system identifies gaps and suggests how to frame existing experience

**Performance Requirements**:
- Response time: <20s for resume generation
- Error handling: Clear messaging if master resume is missing or incomplete
- Observability: Track tailoring start, LLM calls, and completion

---

### User Story 3 - Cover Letter Generation Workflow (Priority: P2)

A job seeker requests a personalized cover letter that demonstrates cultural fit and tells a compelling story based on the job requirements and their background.

**Why this priority**: Enhances application quality but depends on job analysis and master resume. Can be omitted in initial MVP if time-constrained.

**Independent Test**: Can be tested by providing job analysis and career history, then verifying output is a coherent, personalized cover letter addressing key job requirements.

**Acceptance Scenarios**:

1. **Given** job analysis and career history, **When** user requests cover letter, **Then** system generates personalized letter highlighting relevant achievements and cultural fit
2. **Given** company-specific information (from website RAG), **When** cover letter is generated, **Then** system incorporates company values and recent news
3. **Given** minimal company information, **When** cover letter is generated, **Then** system focuses on job requirements and candidate's relevant experience

**Performance Requirements**:
- Response time: <25s for cover letter generation
- Error handling: Fallback to generic format if company data unavailable
- Observability: Track generation start, data retrieval, and completion

---

### User Story 4 - Portfolio Search Workflow (Priority: P2)

A job seeker requests code examples from their GitHub portfolio that match specific job requirements.

**Why this priority**: Adds value by helping users identify relevant projects to discuss in interviews, but not critical for initial application submission.

**Independent Test**: Can be tested by providing job requirements and portfolio data, then verifying relevant repositories and code snippets are identified.

**Acceptance Scenarios**:

1. **Given** job analysis with technology requirements, **When** user requests portfolio search, **Then** system finds matching repositories and code examples
2. **Given** cached GitHub repository data, **When** portfolio search is performed, **Then** system uses cached data for faster results
3. **Given** portfolio with limited matches, **When** search is performed, **Then** system suggests how to frame related experience

**Performance Requirements**:
- Response time: <10s for portfolio search
- Error handling: Handle missing or private repositories gracefully
- Observability: Track search queries and match quality

---

### User Story 5 - Complete Application Workflow (Priority: P1)

A job seeker provides a job URL and the system orchestrates all steps: analyze job, tailor resume, generate cover letter, and find portfolio examples.

**Why this priority**: This is the end-to-end user experience and demonstrates the full value of the system. Essential for demonstrating LangGraph's orchestration capabilities.

**Independent Test**: Can be tested by providing a single job URL and verifying all outputs (job analysis, tailored resume, cover letter, portfolio examples) are generated in the correct sequence.

**Acceptance Scenarios**:

1. **Given** a job URL, **When** user requests complete application, **Then** system executes all steps in order and provides comprehensive output
2. **Given** a failure in one step, **When** complete workflow is running, **Then** system continues with remaining steps and reports which steps failed
3. **Given** cached data for some steps, **When** workflow executes, **Then** system skips redundant processing and uses cached results

**Performance Requirements**:
- Response time: <60s for complete workflow
- Error handling: Partial success - return completed steps even if some fail
- Observability: Track progress through each workflow stage

---

### User Story 6 - Career History Management (Priority: P3)

A job seeker updates their master resume, adds new experiences, achievements, or skills to keep their profile current.

**Why this priority**: Important for maintenance but not needed for immediate job application. Users can work with existing data initially.

**Independent Test**: Can be tested by adding/updating career data and verifying changes persist correctly.

**Acceptance Scenarios**:

1. **Given** new employment experience, **When** user adds it to career history, **Then** system updates both career-history.yaml and master resume
2. **Given** new achievement for existing role, **When** user adds achievement, **Then** system updates career history and optionally updates master resume
3. **Given** new technical skills, **When** user adds them to a role, **Then** system updates career history with technology associations

**Performance Requirements**:
- Response time: <5s for data updates
- Error handling: Validate data structure before saving
- Observability: Track data modification events

---

### User Story 7 - Website RAG Pipeline (Priority: P3)

The system processes websites (job postings, company blogs, career pages) into a searchable knowledge base for enhanced context in applications.

**Why this priority**: Adds richness to cover letters and job analysis but not essential for basic functionality. Can be deferred to later iterations.

**Independent Test**: Can be tested by processing a website URL and verifying semantic search returns relevant content.

**Acceptance Scenarios**:

1. **Given** a company website URL, **When** user requests processing, **Then** system fetches, chunks, embeds, and stores content for semantic search
2. **Given** processed websites, **When** user queries for specific information, **Then** system returns relevant chunks with source attribution
3. **Given** stale cached content (>30 days), **When** accessed, **Then** system flags staleness and offers to refresh
4. **Given** multilingual content, **When** processing, **Then** system detects language and generates appropriate embeddings

**Performance Requirements**:
- Response time: <20s for website processing, <3s for queries
- Error handling: Handle fetch failures, parsing errors, and embedding failures gracefully
- Observability: Track processing steps and query performance

---

### Edge Cases

- What happens when a job posting URL becomes unavailable after initial analysis?
  - System should serve cached analysis data and note that source is unavailable
- How does system handle extremely long job postings (>10,000 words)?
  - Chunk content and process in segments, ensuring no critical information is lost
- What happens when master resume is empty or incomplete?
  - System should provide clear guidance on what information is needed
- How does system handle rate limits from external services (GitHub API, Claude API)?
  - Implement exponential backoff and surface errors clearly to user
- What happens when LangGraph workflow is interrupted mid-execution?
  - System should maintain state and allow resumption from last completed step
- How does system handle concurrent requests for the same job analysis?
  - Use locking mechanism or queue to prevent duplicate processing

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement all existing Resume Agent functionality using LangGraph state machine architecture
- **FR-002**: System MUST maintain data compatibility with existing SQLite backend (resume_agent.db schema)
- **FR-003**: System MUST expose identical MCP tool interfaces to maintain compatibility with existing Claude Desktop integration
- **FR-004**: System MUST orchestrate multi-step workflows (analyze → tailor → generate cover letter → find examples) using LangGraph nodes and edges
- **FR-005**: System MUST persist workflow state to enable resumption after interruptions
- **FR-006**: System MUST support both streaming and batch execution modes for workflow steps
- **FR-007**: System MUST handle workflow errors gracefully with partial success capability (return completed steps even if some fail)
- **FR-008**: System MUST maintain existing performance targets: job analysis <15s, resume tailoring <20s, cover letter <25s
- **FR-009**: System MUST support the same 22 MCP tools/slash commands as existing implementation
- **FR-010**: System MUST integrate with existing observability server for event tracking
- **FR-011**: System MUST support conditional workflow branching based on intermediate results (e.g., skip cover letter if job analysis fails)
- **FR-012**: System MUST allow users to execute individual workflow steps or complete end-to-end workflows
- **FR-013**: System MUST cache intermediate results to avoid redundant processing
- **FR-014**: System MUST validate workflow inputs before execution to prevent cascading failures
- **FR-015**: System MUST provide workflow visualization capabilities showing current state and execution path

### Key Entities

- **WorkflowState**: Represents the current state of a multi-step job application workflow
  - Attributes: workflow_id, current_node, job_url, job_analysis, tailored_resume, cover_letter, portfolio_examples, errors, completion_percentage
  - Relationships: Contains job analysis, resume, cover letter, and portfolio data at various stages

- **WorkflowNode**: Represents a single step in the LangGraph workflow
  - Attributes: node_id, node_type (job_analysis, resume_tailoring, cover_letter, portfolio_search), status (pending, in_progress, completed, failed), duration_ms, error_message
  - Relationships: Part of WorkflowState, connects to other nodes via edges

- **WorkflowEdge**: Defines transitions between workflow nodes
  - Attributes: source_node, target_node, condition (optional branching logic)
  - Relationships: Connects WorkflowNodes

- **JobAnalysis**: Structured data extracted from job posting (existing entity, maintained for compatibility)
  - Attributes: company, job_title, requirements, skills, responsibilities, salary_range, location, keywords, url, fetched_at

- **TailoredResume**: Job-specific resume version (existing entity, maintained for compatibility)
  - Attributes: company, job_title, content, keywords_integrated, created_at, metadata

- **CoverLetter**: Personalized cover letter (existing entity, maintained for compatibility)
  - Attributes: company, job_title, content, created_at, metadata

- **PortfolioExample**: Code example from GitHub portfolio (existing entity, maintained for compatibility)
  - Attributes: example_id, title, description, technologies, repository_url, code_snippet, created_at

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete full job application workflow (analyze + tailor + cover letter + portfolio) in under 60 seconds
- **SC-002**: System successfully handles workflow interruptions with 100% state recovery (can resume from last completed step)
- **SC-003**: LangGraph implementation maintains performance parity with existing system: <15s job analysis, <20s resume tailoring, <25s cover letter generation
- **SC-004**: System reduces duplicate processing by 80% through workflow-level caching of intermediate results
- **SC-005**: 95% of workflow failures provide actionable error messages identifying specific failed step
- **SC-006**: System supports execution of 100+ concurrent workflows without performance degradation
- **SC-007**: Workflow visualization clearly shows execution progress for 100% of running workflows
- **SC-008**: System maintains 100% backward compatibility with existing MCP tool interfaces
- **SC-009**: Partial workflow success rate achieves 90%+ (at least some steps complete even when others fail)
- **SC-010**: Development team can add new workflow nodes in under 30 minutes (demonstrates LangGraph's extensibility advantage)

## Assumptions *(optional)*

- LangGraph will be used as the orchestration framework (vs. alternatives like Temporal, Airflow, or custom state machine)
- Existing SQLite backend schema remains unchanged for data compatibility
- MCP (Model Context Protocol) will remain the interface for exposing tools to Claude Desktop
- Observability server integration remains intact for event tracking
- Existing performance benchmarks are acceptable targets for the new implementation
- Users will interact with the system through Claude Desktop (MCP client) rather than a standalone CLI or web UI
- GitHub API access and Claude API access remain available with current rate limits
- The experiment's primary goal is comparing developer experience and maintainability of LangGraph vs. Claude Agent SDK approach

## Out of Scope *(optional)*

- Changes to existing SQLite database schema
- New user-facing features beyond existing 22 MCP tools/slash commands
- Migration of existing data from old to new implementation (maintains compatibility)
- Web UI or standalone CLI (focuses on MCP integration only)
- Authentication or multi-user support (remains single-user system)
- Integration with job application platforms (LinkedIn, Indeed, etc.)
- Real-time collaboration features
- Mobile application
- Performance optimizations beyond maintaining parity with existing system

## Dependencies *(optional)*

### External Dependencies

- LangGraph library for workflow orchestration
- Claude API (Anthropic) for LLM-powered analysis, tailoring, and generation
- GitHub API for portfolio repository access
- FastMCP 2.0 for MCP server implementation
- SQLite + sqlite-vec for data persistence and vector search
- sentence-transformers for embedding generation
- langchain-text-splitters for content chunking
- Existing observability server for event tracking

### Internal Dependencies

- Existing SQLite database schema and data (resume_agent.db)
- Existing career-history.yaml format
- Existing master resume structure
- MCP protocol compatibility with Claude Desktop

## Technical Constraints *(optional)*

- Must maintain compatibility with existing MCP tool signatures
- Must use existing SQLite database without schema migration
- Must integrate with existing observability server (no protocol changes)
- Must support Windows development environment (uses PowerShell, UV package manager)
- Must operate as single-file Python application for deployment simplicity
- Must use HTTP Streamable transport (port 8080) for MCP communication

## Open Questions *(if any remain after clarification)*

None - this is a well-defined experiment with clear functional parity requirements.

