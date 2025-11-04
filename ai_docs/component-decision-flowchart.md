# Component Decision Flowchart

Quick reference for deciding what type of Claude behavior to create.

## The 30-Second Decision

```
START: I need to...
│
├─> Integrate with external API/service/database
│   └─> ✓ Create MCP Server
│
├─> Run multiple tasks in parallel
│   └─> ✓ Create Agent (.claude/agents/)
│
├─> Isolate context-heavy work
│   └─> ✓ Create Agent (.claude/agents/)
│
├─> Automate a reoccurring workflow
│   └─> ✓ Create Skill (.claude/skills/)
│
├─> Trigger something manually, one time
│   └─> ✓ Create Command (.claude/commands/)
│
└─> Orchestrate multiple skills/commands
    ├─> Manual trigger? ─> ✓ Create Command
    └─> Automatic? ─────> ✓ Create Skill
```

## Validation Questions

Before creating, answer these:

### 1. Does it already exist?
```bash
# Search commands
grep -r "description:.*<your-keyword>" .claude/commands/

# Search skills
ls .claude/skills/ | grep <your-keyword>

# Search agents
ls .claude/agents/ | grep <your-keyword>
```

### 2. Parallel execution needed?
- [ ] Yes → **Agent**
- [ ] No → Continue

### 3. Will this repeat automatically?
- [ ] Yes → **Skill**
- [ ] No → **Command**

### 4. Is this an orchestrator?
- [ ] Manual trigger → **Command** (like /career:apply)
- [ ] Automatic → **Skill** (like resume-writer)

### 5. External integration?
- [ ] Yes → **MCP Server** (not Command/Skill/Agent)

## Real-World Examples

### Example 1: Job Application Workflow
**Need:** Complete workflow (analyze job → tailor resume → cover letter)

**Decision Path:**
1. Parallel? No (sequential workflow)
2. Automatic? No (user decides when to apply)
3. Orchestrator? Yes (calls multiple skills)
4. Manual trigger? Yes

**Result:** ✓ Command `/career:apply`

**Why not:**
- ✗ Agent (no parallelization needed)
- ✗ Skill (manual trigger, not automatic)
- ✗ MCP (no external integration)

### Example 2: Portfolio Search
**Need:** Search GitHub for code examples matching job requirements

**Decision Path:**
1. Parallel? No (single search operation)
2. Automatic? Yes (triggered by /career:apply automatically)
3. Orchestrator? No (single focused task)
4. Reoccurring? Yes (every job application)

**Result:** ✓ Skill `portfolio-finder`

**Why not:**
- ✗ Command (should be automatic, not manual)
- ✗ Agent (no isolation needed)
- ✗ MCP (GitHub already has gh CLI, no new integration)

### Example 3: LangGraph Test Generation
**Need:** Create comprehensive tests for LangGraph code

**Decision Path:**
1. Parallel? Yes (can test multiple nodes concurrently)
2. Context-heavy? Yes (testing requires significant context)
3. Isolation valuable? Yes (protect main conversation)

**Result:** ✓ Agent `langgraph-test-maintainer`

**Why not:**
- ✗ Skill (need parallel execution + isolation)
- ✗ Command (automatic detection + parallel processing)
- ✗ MCP (no external service integration)

### Example 4: Resume Transformation
**Need:** Transform master resume for specific job

**Decision Path:**
1. Parallel? No (single transformation)
2. Automatic? Yes (part of application workflow)
3. Orchestrator? No (focused transformation task)
4. Reoccurring? Yes (every application)
5. Data-agnostic? Yes (receives data → returns data)

**Result:** ✓ Skill `resume-writer`

**Why not:**
- ✗ Command (automatic, not manual)
- ✗ Agent (no parallelization/isolation needed)
- ✗ MCP (transforms data, doesn't integrate external service)

### Example 5: RAG Website Processing
**Need:** Add website to semantic search pipeline

**Decision Path:**
1. External service? No (local processing)
2. Parallel? No (single URL processing)
3. Automatic? No (user chooses what to process)
4. Orchestrator? No (single focused task)

**Result:** ✓ Command `/career:process-website`

**Why not:**
- ✗ Skill (manual trigger, user decides what to process)
- ✗ Agent (no parallelization needed)
- ✗ MCP (no new external integration, uses existing tools)

## Anti-Patterns to Avoid

### ✗ Command as Automatic Behavior
```yaml
# BAD: Command that should be automatic
name: auto-tailor-resume
description: Automatically tailor resume when job is analyzed
```
**Problem:** Commands are manually triggered, use Skill instead

### ✗ Skill with Manual Trigger
```yaml
# BAD: Skill that waits for user to invoke
name: generate-cover-letter-on-demand
description: Wait for user to request cover letter
```
**Problem:** Skills are automatic, use Command instead

### ✗ Agent without Parallelization
```yaml
# BAD: Agent for sequential task
name: sequential-resume-writer
description: Write resume one section at a time sequentially
```
**Problem:** No parallel benefit, use Skill instead

### ✗ MCP for Local Data Transformation
```yaml
# BAD: MCP for simple data transformation
name: mcp-resume-formatter
description: Transform resume data formats
```
**Problem:** No external integration, use Skill instead

## Composition Patterns

### Pattern 1: Command → Multiple Skills
```
/career:apply (Command)
├─> job-analyzer (Skill)
├─> portfolio-finder (Skill)
├─> resume-writer (Skill)
└─> cover-letter-writer (Skill)
```
**When:** Manual orchestration of automatic behaviors

### Pattern 2: Skill → Agent (Parallel)
```
test-after-changes (Skill)
└─> langgraph-test-maintainer (Agent × N)
```
**When:** Skill needs parallel sub-tasks

### Pattern 3: Command → Agent
```
/repo:analyze (Command)
└─> repo-analyzer (Agent)
```
**When:** Manual trigger for isolated, context-heavy work

### Pattern 4: Skill → MCP
```
job-analyzer (Skill)
└─> mcp__resume-agent__data_read_job_analysis (MCP)
```
**When:** Automatic workflow needs external data

### Pattern 5: Command → Command
```
/career:apply (Command)
├─> /career:fetch-job (Command)
├─> /career:process-website (Command)
└─> ... (continues workflow)
```
**When:** Orchestrating multiple manual steps

## Size Matters

### Commands: Keep it Simple
- **1 file:** `{name}.md`
- **~10-100 lines:** Focused prompt
- **No scripts:** Pure prompt text

### Skills: Structured but Lightweight
- **Structure:**
  ```
  skill-name/
  ├── SKILL.md (<500 lines)
  ├── README.md (optional)
  └── references/ (examples)
  ```
- **Focus:** Single responsibility
- **Progressive disclosure:** Metadata → Instructions → References

### Agents: Comprehensive Instructions
- **1 file:** `{name}.md`
- **~100-300 lines:** Detailed behavior specification
- **Examples:** Show trigger patterns

## Naming Conventions

### Commands
```
{action}-{object}.md
├─ add-achievement.md
├─ analyze-job.md
└─ fetch-job.md

{domain}/{action}-{object}.md
├─ career/add-achievement.md
└─ japanese/analyze.md

{namespace}.{action}.md
└─ speckit.plan.md
```

### Skills
```
{domain}-{role}/
├─ job-analyzer/
├─ resume-writer/
└─ portfolio-finder/

{capability}-{specialty}/
└─ deep-researcher/
```

### Agents
```
{domain}-{specialty}.md
├─ langgraph-test-maintainer.md
└─ repo-analyzer.md
```

## Quick Checklist

Before creating a new component:

- [ ] Searched existing components for similar functionality
- [ ] Answered "parallel execution needed?" → Agent
- [ ] Answered "automatic behavior needed?" → Skill
- [ ] Answered "manual trigger needed?" → Command
- [ ] Answered "external integration needed?" → MCP
- [ ] Chosen appropriate naming convention
- [ ] Planned composition (what calls this? what does this call?)
- [ ] Considered data flow (input → processing → output)

## Help! I'm Still Unsure

### Decision Tree #2: By Problem Type

**Problem:** I need to respond to user actions
- User manually triggers → **Command**
- Automatically detects and acts → **Skill**

**Problem:** I need to process data
- Transform data (no external I/O) → **Skill**
- Store/retrieve data (external I/O) → **MCP**

**Problem:** I need to scale
- Parallel execution → **Agent**
- Sequential scaling → **Skill**

**Problem:** I need to orchestrate
- Manual orchestration → **Command**
- Automatic orchestration → **Skill**

**Problem:** I need to isolate
- Protect context → **Agent**
- Share context → **Skill** or **Command**

## Related Documentation

- `ai_docs/agent-features-cheat-sheet.md` - Detailed feature comparison
- `ai_docs/claude-behaviors-review-framework.md` - Systematic review process
- `.claude/skills/skill-creator/` - Skill creation guide
