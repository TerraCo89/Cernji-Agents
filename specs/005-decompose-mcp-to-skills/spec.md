# Feature Specification: Decompose MCP Server to Claude Skills

**Feature Branch**: `005-decompose-mcp-to-skills`
**Created**: 2025-10-23
**Status**: Draft
**Input**: User description: "Refactor and decompose the Resume Agent MCP server into Claude Code skills"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Career Tools as Skills (Priority: P1)

As a job seeker using Claude Code, I want to access resume tailoring, job analysis, and application generation capabilities through simple, discoverable skills instead of an MCP server, so I can use these features directly within my coding workflow without additional server configuration.

**Why this priority**: This delivers the primary value proposition - making career application tools accessible within Claude Code. The current MCP server architecture requires server setup and configuration, while skills work natively in Claude Code with zero setup.

**Independent Test**: Can be fully tested by invoking the job analysis skill with a job URL and verifying it returns structured job requirements. Delivers standalone value even if other skills aren't implemented.

**Acceptance Scenarios**:

1. **Given** Claude Code is running in the project directory, **When** user requests "analyze this job posting [URL]", **Then** Claude automatically discovers and invokes the job-analyzer skill, returning structured job requirements (company, role, skills, requirements)

2. **Given** a job has been analyzed, **When** user requests "tailor my resume for this job", **Then** Claude invokes the resume-writer skill, which receives job analysis data and master resume, returning ATS-optimized resume content

3. **Given** job analysis and tailored resume exist, **When** user requests "generate a cover letter", **Then** Claude invokes the cover-letter-writer skill, returning personalized cover letter content based on job requirements and career history

4. **Given** user wants complete application package, **When** user requests "apply to [job URL]", **Then** Claude orchestrates job-analyzer → portfolio-finder → resume-writer → cover-letter-writer skills in sequence, generating complete application artifacts

**Performance Requirements** (see Constitution VI):
- [ ] Response time: Job analysis <5s, resume tailoring <10s, complete application workflow <30s
- [ ] Error handling: Graceful failures with clear error messages if job URL is invalid, data is missing, or AI generation fails
- [ ] Observability: Log skill invocations, data access operations, and AI agent calls for debugging

---

### User Story 2 - Portfolio Library Management (Priority: P2)

As a developer building a job search portfolio, I want to add, search, and manage code examples through Claude Code skills, so I can build a reusable portfolio library over time without manual file management.

**Why this priority**: Portfolio library is a key differentiator but secondary to core application workflow. Users need job analysis and resume tailoring first, then portfolio examples enhance applications.

**Independent Test**: Can be tested by adding a portfolio example through Claude Code and verifying it's stored in the database with searchable metadata. Delivers value independently of job applications.

**Acceptance Scenarios**:

1. **Given** user completed a project with notable code, **When** user requests "add this to my portfolio: [code snippet + description]", **Then** Claude invokes the portfolio-library skill to store the example with technologies, company, and project metadata

2. **Given** portfolio library has 20+ examples, **When** user requests "list my portfolio examples for [technology]", **Then** Claude invokes the portfolio-library skill to retrieve and display matching examples with metadata

3. **Given** applying for a job requiring specific technologies, **When** user requests "find portfolio examples matching this job", **Then** Claude invokes portfolio-search skill to query examples by technology and keyword relevance

**Performance Requirements**:
- [ ] Response time: Portfolio add <2s, search <3s, list <2s
- [ ] Error handling: Validate data before storage, handle duplicate detection gracefully
- [ ] Observability: Log all CRUD operations for portfolio examples

---

### User Story 3 - Website RAG Pipeline (Priority: P3)

As a job seeker researching companies and roles, I want to process job postings and company websites into a searchable knowledge base through Claude Code skills, so I can query information across multiple sources when preparing applications.

**Why this priority**: Advanced feature that enhances research capabilities but not essential for basic workflow. Users can apply to jobs without RAG pipeline, but it improves application quality.

**Independent Test**: Can be tested by processing a website URL and verifying it's chunked, embedded, and searchable. Delivers value independently by enabling semantic search across saved content.

**Acceptance Scenarios**:

1. **Given** user finds an interesting job posting, **When** user requests "save this job posting for analysis: [URL]", **Then** Claude invokes the rag-website-processor skill to fetch, chunk, embed, and store the content with metadata

2. **Given** 10+ websites have been processed, **When** user requests "what are the common requirements across these job postings?", **Then** Claude invokes the rag-query skill to perform semantic search and synthesize insights from stored content

3. **Given** a previously processed website needs updating, **When** user requests "refresh the data for [company website]", **Then** Claude invokes the rag-refresh skill to re-fetch and re-process the content

**Performance Requirements**:
- [ ] Response time: Website processing <15s, semantic queries <5s
- [ ] Error handling: Handle network failures, invalid URLs, and processing errors gracefully
- [ ] Observability: Log processing status, chunk counts, and embedding generation

---

### User Story 4 - Data Access and Career Management (Priority: P2)

As a user managing career data, I want to update my master resume, add achievements, and track application history through Claude Code skills, so I can maintain accurate career records without manual YAML editing.

**Why this priority**: Essential for data maintenance but users typically do this less frequently than job applications. Must work reliably to keep career data current.

**Independent Test**: Can be tested by adding an achievement to an employment entry and verifying it's written to career-history.yaml with validation. Delivers standalone value for career data maintenance.

**Acceptance Scenarios**:

1. **Given** user completed a significant project, **When** user requests "add achievement: increased system performance by 40%", **Then** Claude invokes the career-data skill to add the achievement to the appropriate employment entry with validation

2. **Given** user learned new technologies, **When** user requests "add skills: Rust, WebAssembly to my current role", **Then** Claude invokes the career-data skill to update technologies for the employment entry and sync to master resume

3. **Given** user wants to review past applications, **When** user requests "list my job applications", **Then** Claude invokes the career-data skill to retrieve application metadata sorted by date

**Performance Requirements**:
- [ ] Response time: Data reads <1s, writes <2s
- [ ] Error handling: Validate all data against Pydantic schemas before writing, preserve data integrity on failures
- [ ] Observability: Log all data access operations with timestamps and user context

---

### Edge Cases

- What happens when a job URL requires JavaScript rendering and Playwright fails to load content?
- How does the system handle malformed job postings that don't match expected structure?
- What happens when portfolio search returns no matching examples for a job?
- How does the system handle concurrent updates to career-history.yaml from multiple Claude Code sessions?
- What happens when the RAG pipeline encounters non-English content requiring language detection?
- How does the system handle GitHub API rate limits when searching portfolio repositories?
- What happens when a skill is invoked without required dependencies (e.g., resume-writer without job analysis)?
- How does the system handle file system permissions issues when writing career data?

## Requirements *(mandatory)*

### Functional Requirements

**Core Skills Creation:**

- **FR-001**: System MUST decompose the MCP server into at least 4 core Claude Code skills: job-analyzer, resume-writer, cover-letter-writer, and portfolio-finder
- **FR-002**: Each skill MUST include YAML frontmatter with name (max 64 chars) and description (max 1024 chars) following Claude Skills framework requirements
- **FR-003**: Each skill MUST implement progressive disclosure with main SKILL.md under 500 lines and additional references in separate files
- **FR-004**: Skills MUST reuse existing agent prompts from apps/resume-agent/.claude/agents/ without modification to preserve proven workflows
- **FR-005**: Skills MUST be organized in a new directory structure: .claude/skills/ or similar location distinct from MCP server

**Data Access Layer:**

- **FR-006**: System MUST provide a centralized data-access skill that handles all file I/O operations (read/write career-history.yaml, master resume, job analyses)
- **FR-007**: Data access operations MUST validate all data against existing Pydantic schemas before reading or writing
- **FR-008**: Skills MUST NOT perform direct file operations; all data access MUST go through the data-access skill
- **FR-009**: Data access skill MUST maintain backward compatibility with existing file formats (YAML, JSON, TXT) used by MCP server

**Skill Orchestration:**

- **FR-010**: System MUST enable Claude Code to orchestrate multi-skill workflows (e.g., job-analyzer → resume-writer → cover-letter-writer) in a single conversation
- **FR-011**: Skills MUST receive input data as structured arguments (dictionaries, strings) rather than file paths
- **FR-012**: Skills MUST return output as structured data (dictionaries, strings) that can be passed to subsequent skills or saved by data-access skill
- **FR-013**: Skills MUST include clear examples demonstrating single-skill usage and multi-skill orchestration patterns

**Portfolio Library:**

- **FR-014**: System MUST provide portfolio-library skill for CRUD operations on job-agnostic code examples
- **FR-015**: Portfolio library skill MUST support searching examples by technology, company, project, or keyword
- **FR-016**: Portfolio library operations MUST interact with SQLite database through data-access skill (not direct SQL)

**RAG Pipeline:**

- **FR-017**: System MUST provide website-rag skill for processing job postings and company websites into searchable chunks
- **FR-018**: Website RAG skill MUST support semantic search combining vector similarity and keyword search
- **FR-019**: RAG processing MUST handle both English and Japanese content with automatic language detection
- **FR-020**: RAG operations MUST interact with database through data-access skill

**Migration Support:**

- **FR-021**: System MUST document migration path from MCP server to Claude Code skills for existing users
- **FR-022**: Skills MUST work with existing data files without requiring data migration or reformatting
- **FR-023**: System MUST provide comparison documentation showing feature parity between MCP tools and skills

**Testing & Validation:**

- **FR-024**: Each skill MUST include test scenarios demonstrating successful execution with sample data
- **FR-025**: Skills MUST handle missing dependencies gracefully with clear error messages (e.g., "Job analysis required before resume tailoring")
- **FR-026**: System MUST provide validation script to check skill structure follows Claude Skills framework requirements

### Key Entities *(include if feature involves data)*

- **Skill Package**: Directory structure containing SKILL.md (YAML frontmatter + instructions), optional references/, scripts/, and assets/ subdirectories
- **Job Analysis**: Structured data extracted from job posting (company, role, requirements, skills, keywords) - passed between skills as dictionary
- **Master Resume**: User's complete career history and skills - read by data-access skill, provided to resume-writer skill
- **Career History**: Extended employment details with achievements and technologies - read by data-access skill, updated by career-data skill
- **Tailored Resume**: ATS-optimized resume content generated for specific job - returned by resume-writer skill, saved by data-access skill
- **Cover Letter**: Personalized cover letter content - returned by cover-letter-writer skill, saved by data-access skill
- **Portfolio Example**: Code example with metadata (title, company, project, technologies, content) - managed by portfolio-library skill
- **RAG Chunk**: Processed website content segment with embeddings - managed by website-rag skill
- **Application Package**: Complete set of artifacts for job application (job analysis, tailored resume, cover letter, portfolio examples) - orchestrated across multiple skills

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can invoke any career skill within Claude Code conversation and receive results in under 10 seconds per skill
- **SC-002**: Complete job application workflow (analyze → tailor → generate cover letter) completes in under 30 seconds
- **SC-003**: Skills work with zero setup - no server configuration, API keys, or environment variables required for basic usage
- **SC-004**: 100% of existing MCP server functionality is available through equivalent skills (feature parity)
- **SC-005**: Users can add portfolio examples and search by technology with results returned in under 3 seconds
- **SC-006**: Skills correctly handle error conditions (missing data, invalid URLs, AI failures) with actionable error messages in 95% of cases
- **SC-007**: All skills follow Claude Skills framework requirements (YAML frontmatter validation, file structure, progressive disclosure)
- **SC-008**: Documentation enables new users to understand skills architecture and usage within 15 minutes

## Assumptions

1. **Claude Code Native Support**: Assumes Claude Code 0.4.0+ supports custom skills in .claude/skills/
2. **Existing Data Compatibility**: Assumes current YAML/JSON file formats remain unchanged, enabling skills to read existing career data
3. **Agent Prompt Reusability**: Assumes existing .claude/agents/ prompts can be embedded in SKILL.md files without modification
4. **Progressive Disclosure**: Assumes skills can reference external files (references/*.md) and Claude Code will load them on-demand
5. **Stateless Execution**: Assumes each skill invocation is stateless, receiving all required data as arguments
6. **Database Access**: Assumes skills can use Python code execution to interact with SQLite database through data access layer
7. **No External Dependencies**: Assumes skills run within Claude Code's code execution environment without requiring package installation
8. **Backward Compatibility**: Assumes MCP server continues to exist alongside skills for users who prefer server architecture

## Out of Scope

- **Real-time MCP Server Replacement**: Skills complement but don't replace MCP server - both architectures coexist
- **Skills API Integration**: Creating skills for Anthropic API (claude.ai) - this focuses on Claude Code only
- **Data Migration Tools**: Automated migration from old formats to new formats - skills work with existing data
- **Observability Dashboard**: UI for monitoring skill usage - relies on existing Claude Code logging
- **Skill Marketplace**: Publishing or distributing skills to other users - skills remain project-local
- **Multi-language Support**: Skills UI/documentation in languages other than English
- **Mobile/Web Interface**: Skills work only in Claude Code CLI, not web or mobile interfaces

## Dependencies

- **Claude Code 0.4.0+**: Framework support for custom skills with progressive disclosure
- **Existing MCP Server Codebase**: Reuses Pydantic schemas, agent prompts, and data access logic from apps/resume-agent/
- **SQLite Database**: Portfolio library and RAG pipeline require existing database schema
- **Python Code Execution**: Skills use Claude Code's code execution environment for data processing
- **File System Access**: Skills require read/write access to D:\source\Cernji-Agents\resumes\ and job-applications\ directories
- **Anthropic API**: AI agent execution within skills requires valid API key (inherited from Claude Code session)

## Technical Constraints

- **Skill Size Limits**: SKILL.md files should stay under 500 lines per Claude Skills best practices
- **No Network Access**: Skills cannot make external API calls (except through Claude Code's built-in tools)
- **No Runtime Installation**: Cannot install Python packages during skill execution - must use pre-installed libraries
- **File Path Format**: All internal skill references must use Unix-style forward slashes (references/guide.md not references\guide.md)
- **YAML Frontmatter**: All skills must start with valid YAML frontmatter (name, description fields required)
- **Stateless Design**: Skills cannot maintain state between invocations - all context must be passed as arguments
- **Data Validation**: All data reads/writes must validate against existing Pydantic schemas to maintain data integrity

## Security Considerations

- **No Hardcoded Secrets**: Skills must not contain API keys, credentials, or personal information
- **Input Validation**: All user-provided URLs and data must be validated before processing
- **File System Isolation**: Skills should only access designated directories (resumes/, job-applications/, data/)
- **SQL Injection Prevention**: Database queries must use parameterized statements, not string concatenation
- **Trusted Sources Only**: Skills should only be used from trusted sources (project maintainer) per Claude Skills security guidelines

## References

- **Existing Agent Prompts**: apps/resume-agent/.claude/agents/ (job-analyzer.md, resume-writer.md, cover-letter-writer.md, portfolio-finder.md, data-access-agent.md)
- **Current MCP Server**: apps/resume-agent/resume_agent.py (30+ MCP tools to decompose)
- **Claude Skills Documentation**: .claude/skills/ (SKILL.md files with YAML frontmatter)
- **Project Constitution**: .specify/memory/constitution.md (architectural principles, testing requirements)
- **Career Data Files**: resumes/kris-cernjavic-resume.yaml, resumes/career-history.yaml
- **Database Schema**: apps/resume-agent/resume_agent.py (Pydantic models: PersonalInfo, Employment, MasterResume, JobAnalysis, etc.)
