# Claude Behaviors Review Framework

A systematic approach to inventory, evaluate, and organize Agents, Commands, and Skills in your `.claude/` folder.

## Quick Reference

| Component | Count | Location | Purpose |
|-----------|-------|----------|---------|
| **Agents** | 2 | `.claude/agents/` | Parallel, isolated sub-tasks |
| **Commands** | 32 | `.claude/commands/` | Manual, one-off prompts |
| **Skills** | 14 | `.claude/skills/` | Automatic, reoccurring workflows |

---

## Current Inventory

### Agents (2)
Specialized for **parallel execution** and **isolated context**.

1. **langgraph-test-maintainer** - LangGraph test creation/organization
2. **repo-analyzer** - GitHub repository analysis

**Pattern Analysis:**
- Both are highly specialized, domain-specific
- Used for isolated, context-heavy tasks (testing, repo analysis)
- Explicitly invoked via Task tool with `subagent_type`

### Commands (32)
Simple, **manually triggered** prompt shortcuts.

#### Career Commands (21)
Located in `.claude/commands/career/`

**Data Operations:**
- `add-achievement.md` - Add to existing employment
- `add-experience.md` - Add new employment position
- `add-portfolio.md` - Add to portfolio library
- `list-history.md` - List employment history
- `list-portfolio.md` - List portfolio examples
- `search-portfolio.md` - Search portfolio by tech/keyword

**Job Application Workflow:**
- `apply.md` - **ORCHESTRATOR** - Full application workflow
- `analyze-job.md` - Parse job posting
- `fetch-job.md` - Fetch and cache job data
- `tailor-resume.md` - Create job-specific resume
- `cover-letter.md` - Generate cover letter
- `find-examples.md` - Search GitHub for examples
- `add-examples.md` - Add examples to application
- `enhance-for-role.md` - AI-driven career enhancement analysis
- `update-master.md` - Update master resume

**RAG Pipeline (Website Processing):**
- `process-website.md` - Add URL to RAG pipeline
- `query-websites.md` - Semantic search across websites
- `list-websites.md` - List processed websites
- `refresh-website.md` - Re-process existing website
- `delete-website.md` - Remove from RAG

**Reporting:**
- `portfolio-matrix.md` - Tech proficiency matrix
- `refresh-repos.md` - Update GitHub cache

#### Speckit Commands (9)
Located in `.claude/commands/`

Feature specification and project management workflow:
- `speckit.constitution.md` - Project principles
- `speckit.specify.md` - Feature specification
- `speckit.plan.md` - Implementation planning
- `speckit.tasks.md` - Task generation
- `speckit.implement.md` - Execute tasks
- `speckit.clarify.md` - Identify spec gaps
- `speckit.checklist.md` - Custom checklists
- `speckit.analyze.md` - Cross-artifact consistency

#### Utility Commands (2)
- `fetch-docs.md` - Fetch library docs from Context7
- `japanese/analyze.md` - Japanese OCR + dictionary

**Pattern Analysis:**
- Commands are well-organized by domain (career/, japanese/, speckit prefix)
- Many commands orchestrate skills (apply.md calls multiple skills)
- Career commands map to MCP server tools (tight integration)
- Speckit represents a complete workflow (8 related commands)

### Skills (14)
**Automatic behaviors** with dedicated structure for reoccurring workflows.

#### Career Skills (6)
- `career-enhancer/` - Gap analysis between job & career
- `cover-letter-writer/` - Generate personalized letters
- `data-access/` - Centralized data I/O layer
- `job-analyzer/` - Parse job postings
- `portfolio-finder/` - Search GitHub for examples
- `resume-writer/` - Transform master resume

#### Development Skills (5)
- `deep-researcher/` - Multi-angle parallel research
- `doc-fetcher/` - Fetch library docs
- `langgraph-builder/` - LangGraph agent patterns
- `mcp-builder/` - MCP server creation guide
- `skill-creator/` - Skill creation guide
- `test-after-changes/` - Validation workflow

#### Document Skills (2)
- `document-skills/docx/` - Word document operations
- `document-skills/pdf/` - PDF operations
- `document-skills/pptx/` - PowerPoint operations
- `document-skills/xlsx/` - Excel operations

#### Testing Skills (1)
- `webapp-testing/` - Playwright browser automation

**Pattern Analysis:**
- Skills have rich structure (SKILL.md, README.md, references/, scripts/)
- Career skills form a data pipeline (analyzer → enhancer → writer)
- Development skills are meta-tools (building other tools)
- Document skills are heavy (OOXML schemas, Python scripts)

---

## Systematic Review Process

### Step 1: Identify Purpose
Ask: **What problem am I solving?**

```
┌─ Need external integration? ───────────────────────┐
│ (API, database, third-party service)              │
└─> Create MCP Server (not covered in this doc)    │
                                                      │
┌─ Need parallel execution? ─────────────────────────┤
│ (Isolated context, scale, concurrent tasks)       │
└─> Create Agent                                    │
                                                      │
┌─ Need automatic, reoccurring behavior? ────────────┤
│ (Triggered by Claude, structured workflow)        │
└─> Create Skill                                    │
                                                      │
┌─ Simple, one-off task? ────────────────────────────┤
│ (Manual trigger, no automation needed)            │
└─> Create Command                                  │
                                                      │
┌─ Composition of multiple components? ──────────────┤
│ (Orchestrating skills, agents, commands)          │
└─> Create Command or Skill                         │
    (Command if manual, Skill if automatic)         │
```

### Step 2: Check for Duplication
Before creating, review existing components:

**For Commands:**
```bash
# Search command descriptions
grep -r "description:" .claude/commands/

# Find similar career commands
ls .claude/commands/career/
```

**For Skills:**
```bash
# List all skills
ls .claude/skills/

# Check skill descriptions (in SKILL.md frontmatter)
grep -r "^description:" .claude/skills/*/SKILL.md
```

**For Agents:**
```bash
# List all agents
ls .claude/agents/

# Check agent descriptions
grep "^description:" .claude/agents/*.md
```

### Step 3: Evaluate Overlap
Ask these questions:

1. **Does this already exist?** (Check inventory above)
2. **Can an existing component be extended?** (Add functionality vs. create new)
3. **Is this a variation of existing behavior?** (Parameterize existing vs. duplicate)
4. **Does this fit the component type?** (Right tool for the job)

### Step 4: Assess Quality
For each existing component, evaluate:

**Commands:**
- [ ] Has clear, descriptive name
- [ ] Includes argument hints
- [ ] Documents allowed tools
- [ ] Has specific, actionable prompt
- [ ] Follows domain organization (career/, japanese/, etc.)

**Skills:**
- [ ] Has SKILL.md with YAML frontmatter (name, description)
- [ ] Description ≤1024 chars, name ≤64 chars
- [ ] SKILL.md is ≤500 lines
- [ ] Includes references/ folder with examples
- [ ] Has clear input/output contract
- [ ] Follows data-agnostic pattern (receives data, returns data)

**Agents:**
- [ ] Has clear specialization (parallel execution or isolated context)
- [ ] Documents tools available
- [ ] Specifies model preference
- [ ] Has explicit trigger examples
- [ ] Follows naming convention: `{domain}-{action}` (e.g., langgraph-test-maintainer)

### Step 5: Plan Reorganization
Identify improvements:

**For Commands:**
- Group related commands into subdirectories (like career/)
- Use consistent naming: `{action}-{object}.md` (e.g., add-achievement.md)
- Ensure orchestrator commands (like apply.md) clearly delegate to skills

**For Skills:**
- Verify data-agnostic patterns (no direct file I/O in skill logic)
- Check for progressive disclosure (metadata → instructions → references)
- Ensure examples are realistic and complete

**For Agents:**
- Verify agents are truly needed (not better as skills)
- Check that parallelization or isolation is the primary need

---

## Decision Template for New Components

Use this template when considering a new component:

```markdown
## New Component Proposal

**Name:** [Your component name]
**Type:** [Agent | Command | Skill]
**Problem:** [What problem does this solve?]

### Type Justification
- [ ] Needs parallelization (Agent)
- [ ] Needs isolated context (Agent)
- [ ] Automatic behavior needed (Skill)
- [ ] Reoccurring workflow (Skill)
- [ ] Manual trigger, one-off (Command)
- [ ] Simple, single task (Command)

### Existing Analysis
**Similar components:**
1. [Component 1] - [Why different]
2. [Component 2] - [Why different]

**Could extend existing?** [Yes/No + explanation]

### Integration Plan
**Calls:** [What components will this call?]
**Called by:** [What will call this?]
**Data flow:** [Input → Processing → Output]

### Implementation Checklist
- [ ] Follow naming conventions
- [ ] Add to inventory documentation
- [ ] Create examples/references
- [ ] Test in isolation
- [ ] Test integration with callers
```

---

## Common Patterns

### Pattern 1: Orchestrator Command
**Purpose:** Coordinate multiple skills in a workflow
**Example:** `/career:apply` - Runs job-analyzer → portfolio-finder → resume-writer → cover-letter-writer

**When to use:**
- Manual trigger needed (user decides when to start)
- Multiple skills need coordination
- Workflow has clear phases
- User wants to see progress

### Pattern 2: Data-Agnostic Skill
**Purpose:** Transform data without file I/O
**Example:** `resume-writer` - Receives job analysis + career history → Returns resume content

**When to use:**
- Reoccurring transformation needed
- Testable in isolation required
- Future database migration planned
- Type safety important

### Pattern 3: Centralized Data Access
**Purpose:** Single source of truth for data operations
**Example:** `data-access` skill - Handles all file I/O with Pydantic validation

**When to use:**
- Multiple components access same data
- Schema validation needed
- Future storage changes likely (file → database)

### Pattern 4: Parallel Sub-Agent
**Purpose:** Isolated, parallel task execution
**Example:** `langgraph-test-maintainer` - Create/organize tests in isolation

**When to use:**
- Task is context-heavy (testing, analysis)
- Can run in parallel with other tasks
- Context isolation valuable (protect main context)
- Transient context acceptable (results are final)

### Pattern 5: Domain-Grouped Commands
**Purpose:** Organize related commands by domain
**Example:** `.claude/commands/career/` - All career-related commands

**When to use:**
- 5+ commands in same domain
- Commands share common patterns
- Commands call same skills/tools
- Logical grouping improves discoverability

---

## Gap Analysis

### Missing Components

Based on your current inventory, consider these gaps:

**Potential New Commands:**
- `/career:stats` - Application success metrics
- `/career:compare-jobs` - Side-by-side job comparison
- `/career:interview-prep` - Generate interview questions from job analysis
- `/speckit:review` - Review artifacts before implementation

**Potential New Skills:**
- `interview-prep/` - Generate interview prep from job + portfolio
- `application-tracker/` - Track application status, follow-ups
- `skill-gap-trainer/` - Suggest learning resources for missing skills

**Potential New Agents:**
- `portfolio-enhancer` - Batch improve README files across repos
- `test-generator` - Generate comprehensive tests for new code

### Refactoring Opportunities

**Commands that might become Skills:**
- `enhance-for-role.md` - Could be automatic when job analysis runs
- `refresh-repos.md` - Could auto-refresh on schedule

**Skills that might become Commands:**
- (None identified - skills are appropriately automatic)

**Overlapping Functionality:**
- `fetch-docs.md` (command) + `doc-fetcher` (skill) - Verify distinction is clear

---

## Review Checklist

Use this checklist monthly or after significant additions:

### Component Health
- [ ] All commands have clear descriptions
- [ ] All skills follow structure guidelines (SKILL.md, references/)
- [ ] All agents have explicit trigger examples
- [ ] No duplicate functionality across components
- [ ] Naming conventions are consistent

### Organization
- [ ] Commands grouped by domain logically
- [ ] Skills have clear boundaries (no overlap)
- [ ] Agents are truly needed (vs. skills)
- [ ] Documentation is up-to-date

### Performance
- [ ] Skills complete in <5 seconds (or document why not)
- [ ] Commands don't block unnecessarily
- [ ] Agents don't over-isolate (balance context vs. performance)

### Integration
- [ ] Data flow between components is clear
- [ ] Orchestrators properly delegate to skills
- [ ] Skills are data-agnostic (no direct file I/O)
- [ ] Error handling is consistent

### Documentation
- [ ] This review framework is current
- [ ] CLAUDE.md reflects actual architecture
- [ ] Examples in skills are realistic
- [ ] Agent trigger patterns documented

---

## Quick Commands for Review

### Generate Component Inventory
```bash
# Commands count
find .claude/commands -name "*.md" | wc -l

# Skills count
ls -1 .claude/skills | wc -l

# Agents count
ls -1 .claude/agents | wc -l

# Find large skills (>500 lines)
find .claude/skills -name "SKILL.md" -exec wc -l {} \; | awk '$1 > 500'

# Find skills without references
for skill in .claude/skills/*/; do
  [ ! -d "$skill/references" ] && echo "Missing references: $skill"
done
```

### Search for Patterns
```bash
# Find all orchestrator commands (commands that call skills)
grep -r "Skill(" .claude/commands/

# Find data-agnostic skills (no file I/O)
grep -L "Write\|Edit\|Bash.*>>" .claude/skills/*/SKILL.md

# Find commands without argument hints
grep -L "argument-hint:" .claude/commands/*.md
```

---

## Next Steps

After reviewing with this framework:

1. **Document Findings:** Create a review report in `ai_docs/`
2. **Prioritize Changes:** High/medium/low impact changes
3. **Create Tasks:** Use `/speckit.tasks` for implementation plan
4. **Iterate:** Run this review quarterly or after 5+ new components

---

## Related Documentation

- `ai_docs/agent-features-cheat-sheet.md` - Quick decision guide
- `CLAUDE.md` - Project architecture overview
- `.claude/skills/skill-creator/` - Skill creation guide
- `.claude/commands/speckit.*.md` - Feature specification workflow
