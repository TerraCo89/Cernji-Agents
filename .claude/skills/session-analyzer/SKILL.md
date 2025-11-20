---
name: session-analyzer
description: Analyzes Claude Code chat history to identify optimization opportunities, track Skills/Commands utilization, detect repetitive patterns, measure token usage, and recommend improvements. This skill should be used when reviewing productivity, identifying underutilized resources, or finding patterns that could become new Skills.
---

# Session Analyzer

Analyze Claude Code chat history to identify optimization opportunities and improve productivity.

## Purpose

This skill provides comprehensive analysis of Claude Code session transcripts to:

1. **Track Resource Utilization** - Monitor which Skills and slash commands are used vs. unused
2. **Identify Patterns** - Detect repetitive tool sequences that could be optimized
3. **Measure Efficiency** - Calculate token usage and costs across sessions
4. **Find Knowledge Gaps** - Discover repeated research topics that warrant dedicated Skills
5. **Generate Recommendations** - Provide actionable suggestions for improving workflows

## When to Use This Skill

This skill should be used when:

- Reviewing productivity and identifying inefficiencies in Claude Code workflows
- Determining which Skills or slash commands are underutilized or redundant
- Finding repetitive patterns that indicate opportunities for new Skills
- Analyzing token usage and cost optimization opportunities
- Preparing to create new Skills based on frequently repeated work
- Auditing available resources vs. actual usage patterns
- Making decisions about which Skills/commands to improve or deprecate

## How to Use This Skill

### Basic Analysis

To analyze chat history for a specific time period:

```bash
python scripts/analyze-chat-sessions.py --days 7
```

**Time range options:**
- `--days 7` - Last 7 days (default)
- `--days 1` - Last 24 hours
- `--days 30` - Last 30 days
- `--days 0` - All available transcripts

### Output Modes

**Human-readable report (default):**
```bash
python scripts/analyze-chat-sessions.py --days 7
```

**JSON output for programmatic use:**
```bash
python scripts/analyze-chat-sessions.py --days 7 --json
```

### Understanding the Report

The analysis generates a comprehensive report with the following sections:

#### 1. Token Usage
- Total tokens used (input + output)
- Cost estimates based on Claude Sonnet 4.5 pricing ($3/M input, $15/M output)
- Cache efficiency (tokens saved via prompt caching)

#### 2. Top Tools Used
- Most frequently invoked tools (Read, Bash, Edit, etc.)
- Usage counts to identify common operations

#### 3. Skills Utilization
- List of all available Skills in `.claude/skills/`
- Which Skills were used and how often
- Which Skills were never used (candidates for review/deprecation)

#### 4. Slash Commands Utilization
- List of all available commands in `.claude/commands/`
- Which commands were used and how often
- Which commands were never used (candidates for review/consolidation)

#### 5. Repetitive Patterns
- Common tool call sequences (e.g., "Grep → Read → Grep → Read")
- Frequency counts to prioritize optimization efforts
- Suggestions for optimization strategies

#### 6. Knowledge Gaps
- Research topics that appeared multiple times
- Frequently used grep patterns
- Agent tasks with repeated descriptions
- Candidates for new Skills based on repeated work

#### 7. Recommendations
- Specific, actionable suggestions for improvement
- Skills to create based on patterns
- Resources to review or deprecate
- Optimization opportunities

### Integration Workflow

**Typical usage pattern:**

1. **Run analysis** on recent sessions (last 7-30 days)
2. **Review unused resources** - Identify Skills/commands with 0 usage
3. **Examine patterns** - Look for repetitive tool sequences or research topics
4. **Take action:**
   - Create new Skills for high-frequency patterns
   - Improve documentation for underutilized resources
   - Deprecate or consolidate unused resources
   - Optimize repetitive workflows

5. **Re-analyze periodically** to track improvements

### Creating Skills from Patterns

When the analysis reveals repeated research topics or patterns, use the `skill-creator` skill to formalize the knowledge:

1. Note the repeated pattern from the report
2. Invoke the `skill-creator` skill
3. Follow the skill creation process to capture the procedural knowledge
4. Package and test the new skill
5. Re-run the analysis after some time to verify the new skill is being used

## Data Sources

The script analyzes JSONL transcript files from:

1. **Global Claude storage:** `~/.claude/projects/` (Windows: `%USERPROFILE%\.claude\projects\`)
2. **Local project logs:** `logs/` directory (if present)

Each transcript file contains:
- Message history (user and assistant turns)
- Tool invocations with parameters
- Tool results
- Token usage per message
- Timestamps
- Model information

## Bundled Resources

### Scripts

- **`scripts/analyze-chat-sessions.py`**: Main analysis script. Parses JSONL transcripts, aggregates metrics, detects patterns, and generates reports.

**Usage:**
```bash
python scripts/analyze-chat-sessions.py [--days N] [--json]
```

**Requirements:** Python 3.8+ (no external dependencies)

**Key Features:**
- Parses JSONL transcript format
- Handles Windows UTF-8 encoding automatically
- Aggregates data across multiple sessions
- Detects tool usage patterns
- Tracks Skills and slash commands usage
- Generates cost estimates
- Supports both human-readable and JSON output

## Best Practices

### Regular Analysis Cadence

- **Weekly:** Run analysis to catch emerging patterns early
- **Monthly:** Comprehensive review of Skills/commands utilization
- **After major work:** Analyze sessions after completing significant features to identify reusable patterns

### Interpreting Results

**High-value patterns to look for:**
- Repetitive grep patterns → Consider indexing or reference documents
- Repeated agent tasks with similar descriptions → Candidate for new Skill
- High tool usage (Read, Grep) with similar targets → Pre-load information in Skills
- Unused Skills with clear value → Improve discoverability or documentation

**Red flags:**
- >50% of Skills/commands unused → Over-engineered or poor documentation
- Same research topics 5+ times → Urgent need for dedicated Skill
- Expensive token patterns without caching → Optimization opportunity

### Actionable Responses

When the analysis identifies issues:

**For unused Skills:**
1. Review the Skill's description - Is it discoverable?
2. Check if functionality overlaps with other Skills
3. Consider deprecation if truly unnecessary
4. Improve documentation if valuable but undiscovered

**For repetitive patterns:**
1. Document the workflow being repeated
2. Determine if it warrants a Skill (frequency × complexity)
3. Create the Skill using `skill-creator`
4. Validate adoption in future analyses

**For high token usage:**
1. Identify expensive operations from tool usage breakdown
2. Consider prompt caching for repetitive operations
3. Pre-load frequently accessed information in Skills
4. Optimize tool call sequences

## Example Output

```
📊 Chat History Analysis (Last 7 days)
Analyzed 612 transcript(s)

💰 Token Usage:
  - Total: 16,779,669 tokens ($185.15)
  - Input: 5,545,668 tokens ($16.64)
  - Output: 11,234,001 tokens ($168.51)
  - Cache reads: 1,456,310,937 tokens (saved)

🔧 Top Tools Used:
  - Read: 2577 uses
  - Bash: 2509 uses
  - Edit: 1300 uses
  - TodoWrite: 1258 uses
  - Grep: 1022 uses

📚 Skills Utilization (18 available):
  ✅ Used:
    - deep-researcher: 7 use(s)
    - skill-creator: 2 use(s)
  ❌ Never Used:
    - career-enhancer
    - doc-fetcher
    - error-analyzer
    ... 12 more

🎯 Slash Commands Utilization (15 available):
  ✅ Used:
    - /research: 5 use(s)
    - /pr: 4 use(s)
  ❌ Never Used:
    - /analyze-error
    - /explain-error
    ... 12 more

🔄 Repetitive Patterns Found:
  - Bash → Bash (153 occurrences)
  - TodoWrite → Bash (112 occurrences)
  - WebFetch → WebFetch (97 occurrences)

🎓 Knowledge Gaps (Repeated Research Topics):
  - grep: console\.(log|error|warn|info) (8 times)
  - grep: logging\.getLogger (6 times)

💡 Recommendations:
  1. Review 15 unused Skills - consider deprecating or improving documentation
  2. Review 14 unused slash commands - consider consolidating or documenting better
  3. Create Skills for 10 frequently researched topics
  4. Optimize repetitive tool sequences with Skills or custom commands
```

## Limitations

- **File modification time:** Uses file modification timestamps, which may not reflect actual session dates if files were copied or modified externally
- **Partial transcripts:** Analysis quality depends on complete transcript files; corrupted or incomplete files may skew results
- **Cross-project analysis:** Analyzes all Claude Code sessions together; cannot filter by specific project or working directory
- **Pattern detection:** Uses simple sequence matching; may not detect complex multi-step workflows spanning multiple sessions

## Troubleshooting

**No transcripts found:**
- Check that `~/.claude/projects/` exists and contains `.jsonl` files
- Verify time range isn't too narrow (try `--days 0` for all time)
- Ensure Claude Code has been used to generate sessions

**Unicode encoding errors:**
- Script handles Windows UTF-8 encoding automatically
- If errors persist, check console encoding settings

**Inaccurate Skills/Commands list:**
- Verify `.claude/skills/` and `.claude/commands/` directories exist in project
- Ensure Skills have `SKILL.md` files and commands have `.md` files
- Script scans current working directory; run from project root

## Version History

**v1.0** - Initial release
- JSONL transcript parsing
- Token usage tracking with cost estimates
- Skills and slash commands utilization tracking
- Repetitive pattern detection
- Knowledge gap identification
- Human-readable and JSON output modes
