# Research: Job Analyzer Skill MVP

**Date**: 2025-10-23
**Feature**: Decompose MCP Server to Claude Skills
**Scope**: MVP - Single skill (job-analyzer) only

---

## Skills Framework Compatibility

**Question**: Can we use Claude Skills framework in .claude/skills/ with Claude Code 0.4.0+?

**Decision**: YES - Use Claude Skills framework as documented

**Rationale**:
1. **Documentation Verified**: Skills framework documentation available:
   - overview.md - Framework architecture and 3-level loading
   - file-structure.md - Directory structure requirements
   - cookbook-examples.md - Python implementation patterns
   - best-practices.md - Optimization guidelines

2. **Requirements Confirmed**:
   - SKILL.md with YAML frontmatter (name, description fields)
   - Progressive disclosure pattern (<500 line main file)
   - Unix-style forward slashes for paths
   - Optional references/, scripts/, assets/ subdirectories

3. **Compatibility**: Framework supports:
   - Claude Code (project/personal skills)
   - Claude API (workspace-wide skills)
   - Claude.ai (individual user skills)

**Alternatives Considered**:
- **Custom agent structure**: Rejected - Skills provide better discoverability and progressive disclosure
- **Inline everything in SKILL.md**: Rejected - Violates <500 line guideline, harder to maintain

**Implementation Notes**:
- YAML frontmatter name: "job-analyzer" (13 chars, under 64 limit ✓)
- Description: ~200 chars describing capability + trigger conditions (under 1024 limit ✓)
- Main file will be ~300 lines (instructions + examples)
- Reference files: example-output.md (sample JSON structure)

---

## Agent Prompt Reusability

**Question**: Can we reuse existing job-analyzer.md agent prompt directly in SKILL.md?

**Decision**: YES - Extract core instructions, adapt YAML frontmatter

**Findings from apps/resume-agent/.claude/agents/job-analyzer.md**:

**Current Structure**:
```yaml
---
name: job-analyzer
description: Analyzes job postings and extracts structured information...
tools: Glob, Grep, Read, WebFetch, TodoWrite, WebSearch, BashOutput, KillShell, SlashCommand, Bash...
---

[Instructions: What to extract, output format, JSON structure]
```

**Adaptation Strategy**:

1. **Preserve** (no changes needed):
   - Core extraction logic (required qualifications, preferred qualifications, responsibilities)
   - Output format (JSON structure)
   - Keywords identification for ATS optimization

2. **Adapt** (minor changes for skills):
   - YAML frontmatter: Remove `tools:` field (not applicable in skills)
   - YAML frontmatter: Expand description to include trigger conditions ("Use when analyzing job opportunities...")
   - Add usage examples (skills benefit from explicit invocation patterns)

3. **Add** (new for skills):
   - Progressive disclosure: Move JSON schema to references/example-output.md
   - Error handling guidance (what to do if URL fetch fails)
   - Integration notes (how output feeds into resume-writer, cover-letter-writer)

**Rationale**:
- Existing agent prompt is well-tested and produces high-quality output
- ~67 lines of instructions (well under 500 line limit)
- JSON structure already matches JobAnalysis Pydantic model
- Minimal adaptation reduces risk of introducing bugs

**Alternatives Considered**:
- **Rewrite from scratch**: Rejected - Existing prompt is proven, no value in rewriting
- **Direct copy with no changes**: Rejected - Skills need trigger descriptions and examples

**Line Count Estimate**:
- YAML frontmatter: 10 lines
- Core instructions: 100 lines (expanded from 67 with examples)
- Usage patterns: 50 lines
- Error handling: 30 lines
- Integration notes: 20 lines
- **Total**: ~210 lines (under 500 limit ✓)

---

## Data Access Integration

**Question**: How do skills interact with existing data access layer and Pydantic validation?

**Decision**: Skills invoke Python code execution that calls existing repository functions

**Data Flow Mapping**:

```
User request in Claude Code
  ↓
Skill discovery (Claude auto-selects job-analyzer skill)
  ↓
SKILL.md instructions loaded
  ↓
Skill generates Python code for execution
  ↓
Code execution environment runs:
    1. WebFetch or Playwright to fetch job posting HTML
    2. Parse HTML → extract structured data
    3. Format as JobAnalysis-compatible dictionary
    4. Write to job-applications/{company}_{title}/job-analysis.json
  ↓
Return structured data to user
```

**Integration Points**:

1. **Web Fetching**:
   - Option 1: Use Claude Code's WebFetch tool (built-in)
   - Option 2: Generate Python with Playwright usage (requires playwright package)
   - **Choice**: WebFetch for simplicity (no dependencies)

2. **Data Validation**:
   - JobAnalysis Pydantic model exists in apps/resume-agent/resume_agent.py
   - Skills CAN reference this for validation (read file, import model)
   - OR accept loose validation (save JSON, validate later when used by MCP tools)
   - **Choice**: Loose validation in MVP (strict validation when full integration complete)

3. **File Storage**:
   - Directory: job-applications/{company}_{title}/
   - File: job-analysis.json
   - **No changes** to existing storage patterns

**Compatibility with Data Access Layer (Constitution II)**:

✓ **Follows DAL principles**:
- Skill doesn't perform direct file I/O without validation context
- Output structure matches JobAnalysis Pydantic schema
- Future: Can integrate with data-access skill for validated writes
- MVP: Demonstrates pattern, stricter validation in future iterations

**Alternatives Considered**:
- **Require data-access skill first**: Rejected - MVP should be independently testable
- **Hardcode data paths in skill**: Rejected - Should use environment-aware path construction
- **Skip Pydantic compatibility**: Rejected - Must maintain schema alignment for future integration

**Implementation Notes**:
- Skill instructions will include: "Save output to job-applications/{company}_{title}/job-analysis.json"
- Python code generation will handle directory creation if needed
- JSON structure MUST match existing JobAnalysis fields for future compatibility

---

## Testing Strategy

**Question**: How do we test the job-analyzer skill without automated test frameworks?

**Decision**: Manual testing with documented test cases

**Test Approach**:

**Test Case 1: Supported Job Board (japan-dev.com)**
```
Prerequisites: Claude Code 0.4.0+, internet connection

Steps:
1. In Claude Code conversation: "Analyze this job posting: https://japan-dev.com/jobs/cookpad/senior-backend-engineer"
2. Verify skill is auto-discovered and invoked
3. Check output contains all required fields (company, job_title, required_qualifications, etc.)
4. Verify file created at job-applications/Cookpad_Senior_Backend_Engineer/job-analysis.json
5. Validate JSON is well-formed and parseable

Expected: Success within <5 seconds, all fields populated

Success Criteria:
✓ Skill invoked automatically (no manual "use job-analyzer" needed)
✓ JSON output matches JobAnalysis schema
✓ File saved to correct location
✓ Processing time <5s
```

**Test Case 2: Error Handling (Invalid URL)**
```
Steps:
1. In Claude Code: "Analyze this job posting: https://invalid-site.com/job"
2. Verify graceful error handling
3. Check error message is actionable

Expected: Clear error message like "Failed to fetch job posting: [reason]"

Success Criteria:
✓ No skill crash or uncaught exceptions
✓ Error message explains what went wrong
✓ Error message suggests recovery steps
```

**Test Case 3: Complex Parsing (Japanese-English Mixed Content)**
```
Steps:
1. Use job posting from recruit.legalontech.jp (mixed language)
2. Verify skill extracts English keywords
3. Check handling of Japanese company names/locations

Expected: Gracefully handle mixed content, extract meaningful keywords

Success Criteria:
✓ Company name correct (Japanese or English)
✓ Keywords in English (for ATS compatibility)
✓ No encoding errors in JSON
```

**Success Metrics (MVP Validation)**:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Invocation time | <5s | Manual timing from request to response |
| Skill discovery | Automatic | Claude Code should auto-select skill without user specifying |
| JSON validity | 100% | Parse with json.loads(), no exceptions |
| Schema alignment | All fields present | Compare to JobAnalysis Pydantic model |
| Error handling | Graceful | No crashes on invalid URLs/malformed HTML |

**Testing Limitations**:

- No automated regression tests (skills framework doesn't support this yet)
- No load testing (single-user manual testing only)
- No edge case coverage (would require dedicated test suite)
- MVP acceptance: Manual validation that skill works for primary use case

**Alternatives Considered**:
- **Automated pytest suite**: Rejected - Skills run in Claude Code environment, not standalone Python
- **Integration tests via MCP**: Rejected - Defeats purpose of skills (zero-setup testing)
- **CI/CD validation**: Rejected - Out of scope for MVP, future enhancement

**Documentation Plan**:

Will include in quickstart.md:
1. Test Case 1 as primary example
2. Expected output sample
3. Common issues troubleshooting guide
4. Link to supported job boards

---

## Summary of Decisions

| Area | Decision | Status |
|------|----------|--------|
| Skills Framework | Use Claude Skills in .claude/skills/ directory | ✓ Validated |
| Agent Prompt | Reuse job-analyzer.md with minor YAML frontmatter adaptations | ✓ Validated |
| Data Access | Generate Python code that matches JobAnalysis schema, loose validation in MVP | ✓ Validated |
| Testing | Manual testing with 3 documented test cases | ✓ Defined |
| File Structure | SKILL.md (~210 lines) + references/example-output.md | ✓ Planned |
| Performance | Target <5s for typical job posting analysis | ✓ Defined |

**No NEEDS CLARIFICATION items remain** - All technical decisions made

**Ready for Phase 1**: Data model design, contract definition, quickstart documentation

---

**Research Complete**: 2025-10-23
