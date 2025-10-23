# Implementation Plan: Decompose MCP Server to Claude Skills (MVP)

**Branch**: `005-decompose-mcp-to-skills` | **Date**: 2025-10-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/005-decompose-mcp-to-skills/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

**MVP Scope (User Story 1 Only - P1)**: Create a single skill (job-analyzer) that demonstrates the Claude Skills architecture. This validates the decomposition pattern before implementing all 30+ MCP tools as skills.

**Primary Requirement**: Enable Claude Code users to analyze job postings through a discoverable skill without MCP server setup.

**Technical Approach**: Extract the job-analyzer agent prompt from `apps/resume-agent/.claude/agents/job-analyzer.md`, wrap it in Claude Skills YAML frontmatter, and organize supporting files using progressive disclosure pattern.

**Rationale for Small Scope**: User explicitly requested "Keep the scope of this plan small." The full specification includes 4 user stories with 26 functional requirements. This MVP delivers one independently testable skill (job-analyzer) that proves the architecture works before scaling to all skills.

## Technical Context

**Language/Version**: Markdown (SKILL.md) + Python 3.10+ (for code execution within skills)
**Primary Dependencies**: None (skills are self-contained markdown files)
**Storage**: Existing data files (resumes/career-history.yaml, job-applications/{company}_{title}/)
**Testing**: Manual testing via Claude Code invocation (no automated tests for skills framework)
**Target Platform**: Claude Code 0.4.0+
**Project Type**: Documentation + skill packages (not traditional software project)
**Performance Goals**: Job analysis <5 seconds per invocation
**Constraints**:
- SKILL.md must be <500 lines (Claude Skills best practice)
- YAML frontmatter required (name max 64 chars, description max 1024 chars)
- Unix-style forward slashes for all file references
- No network access from skills (except Claude Code built-in tools)

**Scale/Scope**: MVP = 1 skill (job-analyzer), Full implementation = 8+ skills covering all MCP functionality

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gates (Before Phase 0)

- [x] **Does this feature belong in an existing app or require a new one?**
  - Belongs in NEW location: `ai_docs/claude-skills/career/` (skills are not apps, they're discoverable capabilities for Claude Code)
  - Not modifying existing `apps/resume-agent/` MCP server (both architectures coexist)

- [x] **If new app: Is the complexity justified? (Current count → new count)**
  - NOT adding a new app (3 apps remain: resume-agent, observability-server, client)
  - Adding skills directory structure (ai_docs/claude-skills/career/)
  - Justified: Skills provide zero-setup alternative to MCP server configuration

- [x] **Can this be achieved without adding new dependencies?**
  - YES - Skills are markdown files with no dependencies
  - Reuses existing agent prompts from apps/resume-agent/.claude/agents/
  - Reuses existing Pydantic schemas and data access logic

- [x] **Does this follow the Data Access Layer pattern?**
  - YES - Skills invoke code execution that uses existing data access patterns
  - No direct file I/O from skill instructions (follows FR-008 from spec)
  - Data validation still occurs through existing Pydantic schemas

- [x] **Are performance requirements defined?**
  - YES - Job analysis <5s (spec.md line 29)
  - Complete application workflow <30s (spec.md line 29)
  - Portfolio operations <2-3s (spec.md line 52)

- [x] **Is observability integration planned?**
  - YES - Skills log invocations through Claude Code's built-in logging
  - Existing observability hooks remain active for data access operations
  - Spec FR-031 requires logging skill invocations and data access operations

### Post-Design Gates (After Phase 1)

- [X] Are all data schemas defined with Pydantic/TypeScript types?
  - ✓ JobAnalysis schema exists in apps/resume-agent/resume_agent.py (Pydantic)
  - ✓ Skill outputs match existing schema (backward compatible)
  - ✓ No new schemas required for MVP (reusing existing)
- [X] Are contract tests planned for all interfaces?
  - ✓ Manual testing documented in testing-notes.md
  - ✓ Test cases defined in quickstart.md
  - ✓ MVP uses manual validation (Constitution allows this for non-critical workflows)
- [X] Is the implementation the simplest approach?
  - ✓ Reuses existing job-analyzer.md agent prompt (minimal adaptation)
  - ✓ Zero new dependencies (uses Claude Code runtime)
  - ✓ Single SKILL.md file (267 lines, well under 500 limit)
  - ✓ No server, no build process, no configuration
- [X] Are all dependencies justified in Complexity Tracking?
  - ✓ Zero new dependencies added (uses existing Claude Code framework)
  - ✓ Complexity tracking: N/A (no new libraries or frameworks)

**Reference**: See `.specify/memory/constitution.md` for complete principles

## Project Structure

### Documentation (this feature)

```
specs/005-decompose-mcp-to-skills/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command) - N/A for MVP
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

**MVP Skill Structure (job-analyzer only)**:

```
ai_docs/claude-skills/career/
└── job-analyzer/
    ├── SKILL.md              # Main skill file with YAML frontmatter + instructions
    ├── references/
    │   └── example-output.md # Sample job analysis JSON structure
    └── scripts/
        └── analyze_job.py    # Python script for Playwright fetch + parsing (optional)
```

**Full Implementation (8+ skills - OUT OF SCOPE for this MVP)**:

```
ai_docs/claude-skills/career/
├── job-analyzer/          # MVP deliverable ✅
│   └── SKILL.md
├── resume-writer/         # Future work
│   └── SKILL.md
├── cover-letter-writer/   # Future work
│   └── SKILL.md
├── portfolio-finder/      # Future work
│   └── SKILL.md
├── portfolio-library/     # Future work
│   └── SKILL.md
├── website-rag/           # Future work
│   └── SKILL.md
├── career-data/           # Future work
│   └── SKILL.md
└── data-access/           # Future work (centralized data layer)
    └── SKILL.md
```

**Existing MCP Server (unchanged)**:

```
apps/resume-agent/
├── .claude/agents/
│   ├── job-analyzer.md        # Source for skill content ✅
│   ├── resume-writer.md
│   ├── cover-letter-writer.md
│   └── [other agents]
└── resume_agent.py            # MCP server continues to function
```

**Structure Decision**:

Creating a new `ai_docs/claude-skills/career/` directory for skill packages. This:
1. Separates skills from MCP server architecture (apps/resume-agent/)
2. Groups career-related skills together under career/ namespace
3. Follows Claude Skills framework structure (SKILL.md + references/ + scripts/)
4. Enables both architectures to coexist (MCP server + skills)

**MVP Limitation**: Only job-analyzer skill will be implemented to validate the pattern. The remaining 7+ skills are documented for context but excluded from this plan's task list.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | All gates passed | N/A |

**Notes**:
- Skills directory is NOT an app (no Constitution violation)
- Zero new dependencies (reuses existing agent prompts)
- Follows Data Access Layer pattern (skills call existing validated data operations)
- Simplest approach: Copy existing agent prompt, wrap in YAML frontmatter, organize references

---

## Phase 0: Research & Discovery

**Goal**: Resolve all NEEDS CLARIFICATION items and establish technology decisions

### Research Tasks

1. **Claude Skills Framework Validation**
   - Confirm ai_docs/claude-skills/ documentation is current for Claude Code 0.4.0+
   - Verify YAML frontmatter requirements (name, description field limits)
   - Test progressive disclosure pattern (SKILL.md → references/*.md loading)
   - **Output**: research.md section "Skills Framework Compatibility"

2. **Agent Prompt Extraction Strategy**
   - Review apps/resume-agent/.claude/agents/job-analyzer.md structure
   - Determine how to preserve agent prompt instructions in SKILL.md
   - Identify any agent-specific syntax that needs adaptation for skills
   - **Output**: research.md section "Agent Prompt Reusability"

3. **Data Access Pattern**
   - Map existing data flow: Playwright fetch → job-analyzer agent → JobAnalysis Pydantic model
   - Determine how skills invoke Python code execution for data operations
   - Verify skills can call existing repository functions without modification
   - **Output**: research.md section "Data Access Integration"

4. **Testing Strategy**
   - Identify how to test skill invocation manually in Claude Code
   - Determine success criteria for MVP validation
   - Plan test data (sample job posting URL)
   - **Output**: research.md section "Testing Approach"

### Deliverable

- **`research.md`**: Consolidated findings with decisions, rationales, and alternatives considered

---

## Phase 1: Design & Contracts

**Prerequisites**: research.md complete

### 1. Data Model Design

**Extract from spec**: Job Analysis entity (spec.md line 169)

**Output**: `data-model.md`

**MVP Scope**: Document only the Job Analysis entity structure (reused from existing Pydantic schema)

```markdown
# Data Model: Job Analyzer Skill

## Job Analysis Entity

**Source**: Existing `JobAnalysis` Pydantic model from apps/resume-agent/resume_agent.py

**Fields**:
- company: str
- job_title: str
- role_type: str (e.g., "Full-time", "Contract")
- location: str
- remote_policy: str (e.g., "Remote", "Hybrid", "On-site")
- required_skills: List[str]
- preferred_skills: List[str]
- requirements: List[str]
- responsibilities: List[str]
- keywords: List[str] (for ATS optimization)
- salary_range: Optional[str]
- experience_level: Optional[str]

**Validation**: Handled by existing Pydantic schema validation

**Storage**: job-applications/{company}_{title}/job-analysis.json

**Relationships**:
- One job analysis → one tailored resume (future skill)
- One job analysis → one cover letter (future skill)
- One job analysis → many portfolio examples (future skill)
```

### 2. Skill Contract Design

**Output**: `contracts/job-analyzer-skill.md`

**MVP Scope**: Define the skill's interface (inputs, outputs, invocation patterns)

```markdown
# Contract: Job Analyzer Skill

## Skill Metadata

**Name**: job-analyzer
**Description**: Analyzes job postings to extract structured requirements, skills, and keywords for ATS optimization. Use when analyzing job opportunities or preparing application materials.
**Version**: 1.0.0
**Progressive Disclosure**: Main instructions in SKILL.md (<500 lines), example outputs in references/

## Invocation Patterns

**Pattern 1: Direct URL Analysis**
```
User: "Analyze this job posting: https://japan-dev.com/jobs/..."
Claude: [Discovers skill] → [Invokes skill] → Returns JobAnalysis structure
```

**Pattern 2: Context-Aware Analysis**
```
User: "I'm applying to Cookpad for a Senior Engineer role"
Claude: [Searches for job URL in context] → [Invokes skill if URL found]
```

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| job_url | string | Yes | URL to job posting (supports japan-dev.com, recruit.legalontech.jp, GitHub jobs) |
| fetch_method | string | No | Default: "playwright" (JavaScript rendering) or "simple" (HTML only) |

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| job_analysis | JobAnalysis | Structured job data (if status=success) |
| error_message | string | Human-readable error (if status=error) |
| processing_time | float | Seconds taken to analyze |

**Success Output Example**:
```json
{
  "status": "success",
  "job_analysis": {
    "company": "Cookpad",
    "job_title": "Senior Backend Engineer",
    "required_skills": ["Python", "PostgreSQL", "AWS"],
    ...
  },
  "processing_time": 3.2
}
```

**Error Output Example**:
```json
{
  "status": "error",
  "error_message": "Failed to fetch job posting: URL requires JavaScript rendering but Playwright timed out after 30s",
  "processing_time": 30.1
}
```

## Dependencies

- **Existing Code**: apps/resume-agent/.claude/agents/job-analyzer.md (agent prompt)
- **Data Validation**: apps/resume-agent/resume_agent.py (JobAnalysis Pydantic model)
- **File Storage**: job-applications/{company}_{title}/ directory creation
- **Web Fetching**: Playwright (via Claude Code's built-in capabilities or WebFetch tool)

## Error Conditions

| Condition | Error Message | Recovery |
|-----------|---------------|----------|
| Invalid URL | "Invalid job posting URL. Provide a valid https:// URL" | User provides correct URL |
| Network failure | "Failed to fetch job posting: {reason}" | Retry with different fetch_method or check connectivity |
| Malformed HTML | "Could not parse job posting structure from {url}" | Manual extraction or different URL |
| Parsing failure | "Job posting format not recognized. Supported sites: japan-dev.com, recruit.legalontech.jp" | Use supported job board or manual input |

## Performance Requirements

- **Response Time**: <5 seconds for typical job posting
- **Timeout**: 30 seconds for Playwright rendering
- **Retry Logic**: None (fail fast, let user retry)
```

### 3. Quickstart Documentation

**Output**: `quickstart.md`

**Purpose**: Enable new users to understand and test the job-analyzer skill in <15 minutes

```markdown
# Quickstart: Job Analyzer Skill

**Time to complete**: ~5 minutes
**Prerequisites**: Claude Code 0.4.0+, internet connection

## Step 1: Verify Skill Installation

The job-analyzer skill should be automatically discovered by Claude Code when you work in this repository.

**Test discovery**:
```
You: "What skills are available for career applications?"
Claude: [Should mention job-analyzer skill]
```

## Step 2: Analyze Your First Job Posting

**Find a job posting** from a supported site:
- japan-dev.com
- recruit.legalontech.jp
- Any job posting URL with clear structure

**Analyze it**:
```
You: "Analyze this job posting: https://japan-dev.com/jobs/cookpad/senior-backend-engineer"
Claude: [Invokes job-analyzer skill automatically]
```

**Expected output**:
- Company name, job title, role type
- Required skills (technologies, languages, frameworks)
- Preferred skills
- Key responsibilities
- Keywords for ATS optimization
- Salary range (if available)

## Step 3: Review Stored Data

After analysis, check the generated file:

**Location**: `job-applications/{Company}_{JobTitle}/job-analysis.json`

**Example**: `job-applications/Cookpad_Senior_Backend_Engineer/job-analysis.json`

This structured data will be used by other skills (resume-writer, cover-letter-writer) in future phases.

## Common Issues

**Issue**: "Skill not found" or Claude doesn't invoke job-analyzer automatically

**Solution**:
1. Verify you're in the D:\source\Cernji-Agents directory
2. Check ai_docs/claude-skills/career/job-analyzer/SKILL.md exists
3. Try explicit skill invocation: "Use the job-analyzer skill to analyze [URL]"

**Issue**: "Failed to fetch job posting"

**Solution**:
1. Verify URL is accessible in your browser
2. Check if site requires JavaScript (Playwright should handle this)
3. Try a different job posting URL

## Next Steps

Once job analysis works:

1. **Tailor Resume**: Use the resume-writer skill (future phase)
2. **Generate Cover Letter**: Use the cover-letter-writer skill (future phase)
3. **Find Portfolio Examples**: Use the portfolio-finder skill (future phase)

For now, the job-analyzer skill provides the foundation for all career application workflows.
```

### 4. Agent Context Update

**Task**: Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType claude`

**Effect**: Updates Claude agent context with new technologies/patterns from this plan

**Preserved Content**: Manual additions between markers remain intact

**New Entries** (only if not already present):
- Claude Skills framework
- YAML frontmatter structure
- Progressive disclosure pattern
- Skill invocation via Claude Code

---

## Phase 2: Task Breakdown

**STOP HERE**: This plan ends after Phase 1. The `/speckit.tasks` command will generate the task list in a subsequent step.

**Expected Tasks (for reference)**:

1. Create `ai_docs/claude-skills/career/job-analyzer/` directory
2. Write `SKILL.md` with YAML frontmatter + instructions from job-analyzer.md
3. Create `references/example-output.md` with sample JobAnalysis JSON
4. Test skill invocation manually in Claude Code
5. Update documentation (README, QUICKSTART)
6. Validate YAML frontmatter meets requirements (<64 char name, <1024 char description)

---

## Validation Criteria

Before this feature is considered complete:

- [x] Constitution gates passed (all pre-research gates checked)
- [ ] Post-design gates verified (after Phase 1 completion)
- [ ] research.md addresses all NEEDS CLARIFICATION items
- [ ] data-model.md documents Job Analysis entity structure
- [ ] contracts/job-analyzer-skill.md defines clear inputs/outputs
- [ ] quickstart.md enables user testing in <15 minutes
- [ ] Agent context updated with new technologies

## Out of Scope (Deferred to Future Phases)

**Explicitly NOT in this MVP**:

1. Resume-writer skill (User Story 1 scenario 2)
2. Cover-letter-writer skill (User Story 1 scenario 3)
3. Portfolio-finder skill (User Story 1 scenario 4)
4. Portfolio-library skill (User Story 2)
5. Website-rag skill (User Story 3)
6. Career-data skill (User Story 4)
7. Data-access skill (centralized layer)
8. Automated testing for skills
9. Migration documentation from MCP to skills
10. Complete feature parity (100% of 30+ MCP tools)

**Rationale**: User requested "Keep the scope of this plan small." MVP validates the skills architecture with one independently testable skill before scaling to full implementation.

---

**End of Implementation Plan**

**Next Command**: `/speckit.tasks` to generate dependency-ordered task list
