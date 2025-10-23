# Migration Guide: MCP Server to Claude Skills

**Date**: 2025-10-23
**Feature**: Job Analyzer Skill MVP

---

## Overview

This guide explains how to use the new Claude Skills architecture alongside (or instead of) the existing MCP server.

**Key Point**: Skills and MCP server are 100% compatible and can coexist. You don't need to migrate - choose the approach that fits your workflow.

---

## Architecture Comparison

### MCP Server (Existing)

**How it works:**
1. Start MCP server: `uv run apps/resume-agent/resume_agent.py`
2. Configure Claude Desktop with server URL
3. Use MCP tools through Claude Desktop
4. Server handles all data operations with Pydantic validation

**Advantages:**
- ✅ Full workflow automation (analyze → tailor → cover letter)
- ✅ Strict data validation (Pydantic schemas)
- ✅ Centralized observability and logging
- ✅ Batch operations and caching
- ✅ Works in Claude Desktop

**Disadvantages:**
- ❌ Requires server setup and configuration
- ❌ Server must be running for tools to work
- ❌ HTTP transport overhead
- ❌ Not available in Claude Code

### Claude Skills (New)

**How it works:**
1. Open repository in Claude Code 0.4.0+
2. Skills are automatically discovered
3. Use natural language: "Analyze this job posting: [URL]"
4. Claude invokes skill and generates code to execute

**Advantages:**
- ✅ Zero setup - works instantly in Claude Code
- ✅ Autodiscovery - Claude picks the right skill automatically
- ✅ No server required
- ✅ Progressive disclosure (detailed instructions loaded only when needed)
- ✅ Works in Claude Code, Claude API, Claude.ai

**Disadvantages:**
- ❌ MVP has only job-analyzer skill (more coming soon)
- ❌ No centralized validation (yet - requires data-access skill)
- ❌ Manual testing workflow (no automated tests)
- ❌ Requires Claude Code 0.4.0+

---

## When to Use Each Approach

### Use MCP Server When:

1. **You need full workflow automation**
   - Example: "Apply to this job" → analyze + tailor + cover letter + portfolio in one command
   - Skills: Only job-analyzer available in MVP

2. **You're using Claude Desktop**
   - MCP server integrates with Claude Desktop via HTTP transport
   - Skills work best in Claude Code (progressive disclosure)

3. **You need strict data validation**
   - MCP server validates all data against Pydantic schemas before saving
   - Skills have loose validation in MVP (strict validation coming with data-access skill)

4. **You need observability and logging**
   - MCP server has centralized logging and event tracking
   - Skills rely on Claude Code's built-in logging

### Use Claude Skills When:

1. **You want zero-setup experience**
   - No server configuration, no `uv run` commands
   - Just open repo in Claude Code and start analyzing jobs

2. **You're in Claude Code**
   - Skills autodiscovered and invoked automatically
   - Natural language interaction ("Analyze this job")

3. **You need quick job analysis**
   - Analyze job postings on the fly without starting the server
   - Perfect for exploratory research

4. **You want to avoid server overhead**
   - No HTTP transport, no port binding, no process management
   - Skills execute directly in Claude Code's runtime environment

---

## Migration Paths

### Path 1: Skills Only (Recommended for Claude Code users)

**Current state**: Using MCP server in Claude Desktop

**Steps**:
1. Install Claude Code 0.4.0+
2. Open `D:\source\Cernji-Agents` in Claude Code
3. Test job-analyzer skill: "Analyze this job posting: [URL]"
4. Wait for remaining skills (resume-writer, cover-letter-writer)
5. Eventually retire MCP server for Claude Desktop

**Timeline**: MVP available now, full skill set in 2-4 weeks

**Benefits**: Simplest setup, no server management

### Path 2: Hybrid (Both MCP + Skills)

**Current state**: Using MCP server

**Steps**:
1. Keep using MCP server for full workflows in Claude Desktop
2. Use job-analyzer skill in Claude Code for quick analysis
3. Both use same data files (`job-applications/{Company}_{JobTitle}/`)
4. Gradually adopt more skills as they're released
5. Retire MCP server when skill parity reaches 100%

**Timeline**: Indefinite (use both as long as needed)

**Benefits**: Best of both worlds, gradual transition

### Path 3: MCP Server Only (Stay on current architecture)

**Current state**: Using MCP server

**Steps**:
1. No migration - continue using MCP server
2. Skills are optional, not required
3. Monitor skill development for future migration

**Timeline**: No changes

**Benefits**: No disruption, proven architecture

---

## Data Compatibility

### File Locations

**Both architectures use identical file paths:**

```
job-applications/
├── Cookpad_Senior_Backend_Engineer/
│   ├── job-analysis.json          # Same structure for both
│   ├── Resume_Cookpad.txt         # (MCP server only for now)
│   └── CoverLetter_Cookpad.txt    # (MCP server only for now)
```

**No migration needed**: Files created by skills can be read by MCP server, and vice versa.

### JSON Structure

**JobAnalysis schema is identical:**

```json
{
  "url": "https://...",
  "fetched_at": "2025-10-23T11:30:00Z",
  "company": "Cookpad",
  "job_title": "Senior Backend Engineer",
  "location": "Tokyo, Japan",
  "salary_range": "¥8M-¥12M",
  "required_qualifications": [...],
  "preferred_qualifications": [...],
  "responsibilities": [...],
  "keywords": [...],
  "candidate_profile": "...",
  "raw_description": "..."
}
```

**Validation differences:**
- MCP server: Strict Pydantic validation before saving
- Skills MVP: Loose validation (relies on LLM correctness)
- Skills future: data-access skill will provide Pydantic validation

---

## Feature Comparison

| Feature | MCP Server | Skills MVP | Skills Future |
|---------|------------|------------|---------------|
| Job Analysis | ✅ | ✅ | ✅ |
| Resume Tailoring | ✅ | ❌ | ✅ (resume-writer) |
| Cover Letter | ✅ | ❌ | ✅ (cover-letter-writer) |
| Portfolio Search | ✅ | ❌ | ✅ (portfolio-finder) |
| Data Validation | ✅ (Pydantic) | ⚠️ (loose) | ✅ (data-access skill) |
| Observability | ✅ | ⚠️ (Claude Code logs) | ✅ (future) |
| Setup Required | ❌ (server + config) | ✅ (zero setup) | ✅ (zero setup) |
| Claude Desktop | ✅ | ❌ | ❌ |
| Claude Code | ❌ | ✅ | ✅ |
| Autodiscovery | ❌ (manual tool calls) | ✅ | ✅ |

**Legend:**
- ✅ = Fully supported
- ⚠️ = Partial/basic support
- ❌ = Not supported

---

## Workflow Examples

### Example 1: Job Analysis Only

**MCP Server Approach:**
```bash
# Start server
uv run apps/resume-agent/resume_agent.py

# In Claude Desktop
You: "Analyze this job posting: https://japan-dev.com/jobs/cookpad/senior-backend-engineer"
Claude: [Calls data_read_job_analysis() MCP tool]
```

**Skills Approach:**
```bash
# Open repo in Claude Code
# No server needed!

# In Claude Code
You: "Analyze this job posting: https://japan-dev.com/jobs/cookpad/senior-backend-engineer"
Claude: [Autodiscovers and invokes job-analyzer skill]
```

**Result**: Identical `job-analysis.json` file created in both cases

### Example 2: Full Application Workflow

**MCP Server Approach (Current):**
```bash
# In Claude Desktop
You: "/career:apply https://japan-dev.com/jobs/cookpad/senior-backend-engineer"
Claude: [Orchestrates: analyze → portfolio → tailor → cover letter]
```

**Skills Approach (Future - not in MVP):**
```bash
# In Claude Code
You: "Help me apply to this job: https://japan-dev.com/jobs/cookpad/senior-backend-engineer"
Claude: [Autodiscovers skills: job-analyzer → portfolio-finder → resume-writer → cover-letter-writer]
```

**Current limitation**: MVP has only job-analyzer skill, so full workflow still requires MCP server.

### Example 3: Hybrid Workflow

**Step 1: Quick analysis in Claude Code (Skills)**
```
You: "Analyze this Cookpad job"
Claude: [Uses job-analyzer skill, saves job-analysis.json]
```

**Step 2: Full application in Claude Desktop (MCP)**
```
You: "/career:tailor-resume https://japan-dev.com/jobs/cookpad/senior-backend-engineer"
Claude: [Reads job-analysis.json created by skill, tailors resume]
```

**Result**: Best of both - quick analysis without server, then full workflow when needed.

---

## Troubleshooting

### Issue: Skill not discovered in Claude Code

**Cause**: Skills directory not in correct location or Claude Code version <0.4.0

**Solutions**:
1. Verify `.claude/skills/job-analyzer/SKILL.md` exists
2. Upgrade Claude Code to 0.4.0+
3. Restart Claude Code session (skill discovery happens at startup)
4. Try explicit invocation: "Use the job-analyzer skill to analyze [URL]"

### Issue: MCP server and skill both trying to analyze

**Cause**: Both MCP server and skills responding to same request

**Solutions**:
1. Use specific invocation:
   - MCP: "/career:analyze-job [URL]" (slash command)
   - Skill: "Use job-analyzer skill for [URL]" (explicit skill reference)
2. Use different environments (MCP in Claude Desktop, skills in Claude Code)

### Issue: Different JSON structures from MCP vs. skill

**Cause**: Should not happen (both use same JobAnalysis schema), but if it does:

**Solutions**:
1. Check skill version matches MCP server schema
2. Validate JSON with online validator
3. Report schema mismatch as bug (both should be identical)

---

## Rollback Plan

If you try skills and want to go back to MCP-only:

1. **No data loss**: All files are compatible
2. **Simply use MCP server**: Skills are opt-in, not required
3. **Delete skills (optional)**: Remove `.claude/skills/` directory if you want to disable autodiscovery

**Time to rollback**: <1 minute (just use MCP server, ignore skills)

---

## Future Roadmap

### MVP (Current - 2025-10-23)
- ✅ job-analyzer skill
- ✅ Zero-setup experience in Claude Code
- ✅ Autodiscovery and invocation
- ✅ Backward compatible with MCP server

### Phase 2 (2-4 weeks)
- [ ] resume-writer skill
- [ ] cover-letter-writer skill
- [ ] portfolio-finder skill
- [ ] data-access skill (strict validation)

### Phase 3 (Future)
- [ ] Full workflow orchestration via skills
- [ ] MCP server deprecation (optional)
- [ ] Skills available in Claude.ai and Claude API
- [ ] Performance optimizations

---

## FAQ

**Q: Do I need to migrate from MCP server?**
A: No! Skills are complementary, not a replacement (yet). Use both if you want.

**Q: Will MCP server be deprecated?**
A: Not immediately. When skills reach feature parity (100% of MCP functionality), we'll provide a deprecation timeline. Until then, both are supported.

**Q: Can I use skills in Claude Desktop?**
A: No. Skills work best in Claude Code (autodiscovery, progressive disclosure). MCP server is the right choice for Claude Desktop.

**Q: What if I already have job-analysis.json from MCP server?**
A: Skills will read and use it. Both architectures use the same file structure.

**Q: How do I know which approach is being used?**
A:
- MCP server: You'll see `[Calling MCP tool: data_read_job_analysis]`
- Skills: You'll see `[Invoking skill: job-analyzer]`

**Q: Can I contribute new skills?**
A: Yes! See `specs/005-decompose-mcp-to-skills/plan.md` for architecture guidelines. Follow the same pattern as job-analyzer skill.

---

## Support

**For MCP server issues:**
- See [README-MCP-SERVER.md](../../README-MCP-SERVER.md)
- Check [DEPLOYMENT.md](../../DEPLOYMENT.md) for troubleshooting

**For skills issues:**
- See [quickstart.md](quickstart.md) for testing guide
- Check [testing-notes.md](testing-notes.md) for known issues
- Review [plan.md](plan.md) for architecture details

**General questions:**
- Open issue in repository
- Check [CLAUDE.md](../../CLAUDE.md) for project overview

---

**Last Updated**: 2025-10-23
**MVP Status**: job-analyzer skill available, remaining skills in development
