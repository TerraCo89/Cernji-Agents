---
description: Analyze Claude Code chat history to identify optimization opportunities, track Skills/Commands utilization, and find patterns
---

Analyze Claude Code chat history from the last {{days}} days (or "all" for all time).

The analysis will:
1. Parse JSONL transcript files from `~/.claude/projects/`
2. Calculate token usage and estimated costs
3. Identify repetitive tool usage patterns
4. Track Skills and slash commands utilization
5. Find knowledge gaps (repeated research topics)
6. Generate recommendations for optimization

Run the analysis script and provide insights about:
- Token efficiency and cost breakdown
- Most frequently used tools
- Skills utilization (used vs unused)
- Slash commands utilization (used vs unused)
- Repetitive patterns that could be optimized
- Suggested new Skills based on repeated research
- Recommendations for underutilized resources

Execute: `python scripts/analyze-chat-sessions.py --days {{days}}`

If {{days}} is "all" or "0", analyze all available transcripts regardless of date.

After showing the results, ask the user if they want to:
1. Create a new Skill based on identified patterns
2. Review specific unused Skills or commands
3. Export the analysis data for further processing
4. Run the analysis for a different time period
