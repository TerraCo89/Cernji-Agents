# Skills → Commands Conversion Analysis

Analysis of which Skills should be converted to Commands based on invocation pattern.

## Key Test
**Skill** = Automatic behavior (Claude detects need and invokes)
**Command** = Manual trigger (User explicitly requests)

---

## ✅ Correctly Skills (Keep as Skills)

### Career Pipeline Skills (6)
These are correctly skills because they're part of automatic workflows:

1. **`career-enhancer/`** ✓
   - **Invoked by:** `/career:enhance-for-role` or automatic after job analysis
   - **Automatic:** Yes, part of application workflow
   - **Keep as Skill:** ✓

2. **`cover-letter-writer/`** ✓
   - **Invoked by:** `/career:apply` workflow automatically
   - **Automatic:** Yes, generates letter without manual trigger
   - **Keep as Skill:** ✓

3. **`data-access/`** ✓
   - **Invoked by:** All career commands/skills automatically
   - **Automatic:** Yes, centralized data layer
   - **Keep as Skill:** ✓

4. **`job-analyzer/`** ✓
   - **Invoked by:** `/career:apply`, `/career:analyze-job` automatically
   - **Automatic:** Yes, parses job without manual steps
   - **Keep as Skill:** ✓

5. **`portfolio-finder/`** ✓
   - **Invoked by:** `/career:apply` workflow automatically
   - **Automatic:** Yes, searches GitHub in workflow
   - **Keep as Skill:** ✓

6. **`resume-writer/`** ✓
   - **Invoked by:** `/career:apply` workflow automatically
   - **Automatic:** Yes, transforms resume in workflow
   - **Keep as Skill:** ✓

### Detection Skills (2)
These automatically trigger when patterns are detected:

7. **`deep-researcher/`** ✓
   - **Invoked by:** Trigger phrases ("Research...", "Investigate...")
   - **Automatic:** Yes, Claude detects research needs
   - **Keep as Skill:** ✓

8. **`doc-fetcher/`** ✓
   - **Invoked by:** Trigger phrases ("Fetch docs...", "Get documentation...")
   - **Automatic:** Yes, Claude detects doc fetch requests
   - **Note:** There's also `/fetch-docs` command, but skill is for automatic detection
   - **Keep as Skill:** ✓

---

## ⚠️ Should Convert to Commands (7 skills)

### Builder/Guide Skills (3)
These are **reference guides** that require manual user decision to use:

9. **`langgraph-builder/`** → **Convert to `/langgraph:build`**
   - **Current:** Skill with trigger phrases
   - **Reality:** User manually decides "I want to build a LangGraph agent now"
   - **Problem:** Not automatic - requires conscious user choice
   - **Conversion:** Create `/langgraph:build` command
   - **Reason:** Building agents is a deliberate, manual activity

10. **`mcp-builder/`** → **Convert to `/mcp:build`**
    - **Current:** Skill with "Use when building MCP servers"
    - **Reality:** User manually decides to create MCP server
    - **Problem:** Not automatic - requires project planning
    - **Conversion:** Create `/mcp:build` command
    - **Reason:** MCP server creation is intentional, not automatic

11. **`skill-creator/`** → **Convert to `/skill:create`**
    - **Current:** Skill with "when users want to create a new skill"
    - **Reality:** User explicitly says "I want to create a skill"
    - **Problem:** Entirely manual - user-initiated
    - **Conversion:** Create `/skill:create` command
    - **Reason:** Skill creation is always deliberate

### Document Toolkits (4)
These are **reference toolkits** for when user wants to work with specific formats:

12. **`document-skills/pdf/`** → **Convert to `/docs:pdf`**
    - **Current:** "Comprehensive PDF manipulation toolkit"
    - **Reality:** User says "I need to work with PDFs"
    - **Problem:** Manual decision to process PDFs
    - **Conversion:** Create `/docs:pdf` command
    - **Reason:** PDF work is user-initiated

13. **`document-skills/docx/`** → **Convert to `/docs:docx`**
    - **Current:** Word document toolkit
    - **Reality:** User says "I need to edit a Word doc"
    - **Problem:** Manual decision to process DOCX
    - **Conversion:** Create `/docs:docx` command
    - **Reason:** DOCX work is user-initiated

14. **`document-skills/pptx/`** → **Convert to `/docs:pptx`**
    - **Current:** PowerPoint toolkit
    - **Reality:** User says "I need to work with presentations"
    - **Problem:** Manual decision to process PPTX
    - **Conversion:** Create `/docs:pptx` command
    - **Reason:** PPTX work is user-initiated

15. **`document-skills/xlsx/`** → **Convert to `/docs:xlsx`**
    - **Current:** Excel toolkit
    - **Reality:** User says "I need to work with spreadsheets"
    - **Problem:** Manual decision to process XLSX
    - **Conversion:** Create `/docs:xlsx` command
    - **Reason:** XLSX work is user-initiated

### Testing Toolkit (1)

16. **`webapp-testing/`** → **Convert to `/test:webapp`**
    - **Current:** "Toolkit for interacting with and testing local web applications"
    - **Reality:** User says "Test the frontend" or "Check if the UI works"
    - **Problem:** Manual decision to test webapp
    - **Conversion:** Create `/test:webapp` command
    - **Reason:** Testing is deliberate, user-initiated

---

## 🤔 Borderline Case (1 skill)

17. **`test-after-changes/`** - **Recommend: Keep as Skill**
    - **Current:** "ALWAYS use after: moving files, refactoring, etc."
    - **Reality:** Should be automatic after code changes
    - **Borderline because:** Could be manual OR automatic
    - **Recommendation:** Keep as Skill
    - **Reason:** This SHOULD be automatic (detect code changes → run validation)
    - **Alternative:** Could also have `/test:validate` command for manual invocation

---

## Summary Statistics

| Category | Count | Recommendation |
|----------|-------|----------------|
| **Keep as Skills** | 8 | Career pipeline (6) + Detection (2) |
| **Convert to Commands** | 7 | Builders (3) + Document toolkits (4) |
| **Webapp Testing** | 1 | Convert to Command |
| **Borderline** | 1 | Keep as Skill (with optional command) |

**Total Skills Reviewed:** 17 (counting document-skills as 4 separate)

---

## Key Insights

### Pattern 1: Workflow vs. Toolkit
- **Workflows** (automatic sequences) → Skills ✓
  - Example: `/career:apply` automatically calls resume-writer, cover-letter-writer
- **Toolkits** (reference material) → Commands ✓
  - Example: PDF toolkit activated when user decides to work with PDFs

### Pattern 2: Detection vs. Invocation
- **Detection** (Claude recognizes need) → Skills ✓
  - Example: "Research error X" → deep-researcher auto-triggers
- **Invocation** (user explicitly requests) → Commands ✓
  - Example: "Build an MCP server" → user consciously starting project

### Pattern 3: Continuous vs. Episodic
- **Continuous** (recurring part of workflow) → Skills ✓
  - Example: Every job application needs resume tailoring
- **Episodic** (occasional, one-off) → Commands ✓
  - Example: Building an MCP server is a rare project

---

## Conversion Priority

### High Priority (Clear Manual Triggers)
1. **`skill-creator/`** → `/skill:create` - Always explicit user request
2. **`mcp-builder/`** → `/mcp:build` - Deliberate project initiation
3. **`langgraph-builder/`** → `/langgraph:build` - Conscious agent creation

### Medium Priority (Toolkits)
4. **`document-skills/pdf/`** → `/docs:pdf` - User decides to process PDFs
5. **`document-skills/docx/`** → `/docs:docx` - User decides to edit Word
6. **`document-skills/pptx/`** → `/docs:pptx` - User decides to work with slides
7. **`document-skills/xlsx/`** → `/docs:xlsx` - User decides to work with Excel

### Medium Priority (Testing)
8. **`webapp-testing/`** → `/test:webapp` - User decides to test UI

---

## Migration Strategy

### Phase 1: High Priority Builders
```bash
# Create new commands
mkdir -p .claude/commands/builders
touch .claude/commands/builders/langgraph-build.md
touch .claude/commands/builders/mcp-build.md
touch .claude/commands/builders/skill-create.md

# Move skill content to command format
# Keep references/ folder structure in command dir
```

### Phase 2: Document Toolkits
```bash
# Create docs command subdirectory
mkdir -p .claude/commands/docs
touch .claude/commands/docs/pdf.md
touch .claude/commands/docs/docx.md
touch .claude/commands/docs/pptx.md
touch .claude/commands/docs/xlsx.md

# Move SKILL.md content to command format
# Preserve scripts/ and references/ in command dirs
```

### Phase 3: Testing Toolkit
```bash
# Create test command subdirectory
mkdir -p .claude/commands/test
touch .claude/commands/test/webapp.md

# Move webapp-testing content to command
```

### Phase 4: Cleanup
```bash
# Archive old skills (don't delete immediately)
mkdir -p .claude/archive/skills
mv .claude/skills/langgraph-builder .claude/archive/skills/
mv .claude/skills/mcp-builder .claude/archive/skills/
# ... etc

# Test new commands work correctly
# After 1 week of successful usage, delete archives
```

---

## Command Format Template

For converting skills to commands:

```markdown
---
description: [Original skill description from YAML frontmatter]
allowed-tools: [Tools the skill used]
argument-hint: [If command takes arguments]
---

# [Skill Name as Command]

[Original SKILL.md content]

## When to Use This Command

Use `/command:name` when:
- [Explicit manual trigger scenarios]
- [User decides to...]
- [Not automatic - user chooses when]

## Usage

[Original skill workflow, adapted for manual invocation]

---

## References

[Link to references/ folder if preserved in command directory]
```

---

## Validation After Conversion

For each converted command, verify:

- [ ] Command has clear manual trigger description
- [ ] No "automatically invoked" language remains
- [ ] Trigger phrases are explicit user requests
- [ ] References/scripts preserved if needed
- [ ] Command appears in Claude Code command list
- [ ] Test invocation works as expected

---

## Benefits of Conversion

### For Builders (langgraph, mcp, skill)
- **Clearer intent:** User explicitly says "I want to build X"
- **No context pollution:** Only loaded when manually invoked
- **Better organization:** Commands for manual tasks, skills for automation

### For Document Toolkits (pdf, docx, pptx, xlsx)
- **Explicit activation:** User decides when to work with documents
- **Reduced context:** Heavy schemas only loaded when needed
- **Simpler discovery:** `/docs:pdf` is clearer than "use pdf skill"

### For Testing (webapp-testing)
- **Manual control:** User decides when to test UI
- **Clear invocation:** `/test:webapp` vs. hoping skill auto-triggers

---

## Next Steps

1. **Review this analysis** with user
2. **Prioritize conversions** (start with builders)
3. **Create conversion tasks** using `/speckit.tasks`
4. **Test each conversion** before archiving old skills
5. **Update documentation** (CLAUDE.md, inventory docs)

---

## Related Documentation

- `ai_docs/agent-features-cheat-sheet.md` - Decision criteria
- `ai_docs/component-decision-flowchart.md` - Quick reference
- `ai_docs/claude-behaviors-review-framework.md` - Full inventory
