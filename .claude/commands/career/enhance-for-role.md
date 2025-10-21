---
description: AI-driven analysis of how to improve your career history for a specific job posting
allowed-tools: SlashCommand, Task, mcp__resume-agent__data_read_job_analysis, mcp__resume-agent__data_read_career_history
---

# Enhance Career History for Target Role

Job URL: $ARGUMENTS

## Purpose

Get AI-driven suggestions for improving your career history to better match a specific job posting.

This command:
1. Analyzes the gap between job requirements and your career history
2. Identifies hidden strengths you should emphasize
3. Suggests specific achievements to add or enhance
4. Recommends keyword optimizations for ATS
5. Provides realistic assessment of your candidacy

**This is the most valuable command for improving application success.**

## Process

**Step 1: Ensure Job Data is Cached**

Check if we have cached job analysis for this URL:
1. Run `/career:fetch-job $ARGUMENTS` to fetch and cache the job posting
2. This is idempotent - if already cached, it reuses existing data
3. Parse company and job title from the cached data

**Step 2: Load Required Data**

Use MCP tools to load both datasets:

```
mcp__resume-agent__data_read_job_analysis(company, job_title)
mcp__resume-agent__data_read_career_history()
```

If either is missing, provide clear error:
```
✗ Cannot perform enhancement analysis

Missing data:
{what's missing}

Run these commands first:
{commands to fix}
```

**Step 3: Invoke Career Enhancement Agent**

Use the Task tool with subagent_type="career-enhancer":

```
Task(
  subagent_type="career-enhancer",
  description="Analyze career enhancement opportunities",
  prompt="""
  Analyze the gap between this job posting and the candidate's career history.
  Provide specific, actionable suggestions to improve their candidacy.

  JOB ANALYSIS:
  {full job analysis data}

  CAREER HISTORY:
  {full career history data}

  Focus on:
  1. Hidden strengths (required skills they have but aren't emphasizing)
  2. Missing metrics (achievements without quantification)
  3. Keyword gaps (ATS keywords they could incorporate)
  4. Reframable experience (existing work that maps to requirements)
  5. Technology additions (skills used but not listed)

  Provide:
  - Prioritized suggestions (High/Medium/Low impact)
  - Exact commands to run for each suggestion
  - Ready-to-use achievement text
  - Realistic assessment of match improvement
  - Honest evaluation if role is good fit

  Be specific, actionable, and honest.
  """
)
```

**Step 4: Present Analysis**

The career-enhancer agent will return a detailed analysis.
Display it clearly with proper formatting.

**Step 5: Interactive Implementation**

After showing the analysis, ask:
```
NEXT STEPS
==========

Would you like to implement any of these suggestions? (y/n)
```

If yes, guide them through implementation:

**Option A: Guided Implementation**
```
Let's implement the HIGH IMPACT suggestions:

Suggestion 1: Add achievement to League of Monkeys
Would you like to:
a) Add this achievement now (I'll guide you)
b) Skip to next suggestion
c) Exit and do it manually later

Choice: [a/b/c]
```

If they choose (a), run the appropriate command:
- For achievement additions: invoke `/career:add-achievement {company}` with pre-filled text
- For technology additions: use MCP tool to add directly
- For description changes: provide exact text and guide them to edit

**Option B: Bulk Application**
```
I can apply multiple suggestions at once:

Which categories do you want to apply?
[x] Achievement additions (3 suggestions)
[x] Technology additions (2 suggestions)
[ ] Description changes (requires manual editing)

Proceed? (y/n)
```

Then apply selected changes using MCP tools.

**Option C: Manual Implementation**
```
Summary of commands to run manually:

1. /career:add-achievement "League of Monkeys"
   (Add Python/TensorFlow achievement)

2. /career:add-achievement "Domain"
   (Add OpenSearch optimization metric)

3. Edit career-history.yaml
   Update Aryza description to emphasize conversational aspects

After making changes, re-run analysis to see improvement:
/career:enhance-for-role $ARGUMENTS
```

**Step 6: Track Progress**

If suggestions were implemented, show before/after:
```
IMPLEMENTATION RESULTS
=====================

Changes made:
✓ Added achievement to League of Monkeys
✓ Added technologies to Domain
✓ 2 of 5 high-impact suggestions completed

Projected Impact:
Before: 4.5/10 match score
After: 6.5/10 match score (+2.0 points)

Remaining suggestions:
- Update Aryza description (requires manual edit)
- Add RAG-related achievement to Domain (optional)

Re-run analysis to see actual improvement:
/career:enhance-for-role $ARGUMENTS
```

**Step 7: Provide Final Recommendations**

Based on the analysis and changes:

**If match is now strong (7+/10):**
```
RECOMMENDATION: APPLY
====================

Your career history is now well-positioned for this role.

Next steps:
1. /career:tailor-resume $ARGUMENTS
2. /career:cover-letter $ARGUMENTS
3. Submit application

Good luck! 🎯
```

**If match is moderate (5-7/10):**
```
RECOMMENDATION: APPLY WITH CAUTION
==================================

Your application is competitive but not perfect.

Gaps remaining:
{list major gaps that can't be addressed}

You should apply if:
- You're excited about the role
- You're willing to learn missing skills
- Company culture > perfect skill match

Before applying:
1. Build small project demonstrating missing skills
2. Take relevant online course
3. Network with current employees

Then:
/career:tailor-resume $ARGUMENTS
/career:apply $ARGUMENTS
```

**If match is still weak (<5/10):**
```
HONEST ASSESSMENT
=================

Even with enhancements, this role isn't a strong match.

Core gaps:
{list fundamental mismatches}

Recommendation: Look for better-fit roles

Better matches for you:
- {Suggested role type 1}
- {Suggested role type 2}

Or build experience first:
- {Specific skills to develop}

Then revisit roles like this in 6-12 months.
```

## Smart Features

**Detect Improvements:**
If career history has changed since last run:
```
📈 IMPROVEMENT DETECTED

I see you've made changes since the last analysis:
- Added achievement to {Company}
- Updated technologies in {Company}

Updated Match Score: 4.5 → 6.0 (+1.5 points)

Nice work! Here's the new analysis...
```

**Suggest Related Roles:**
Based on their actual strengths:
```
BETTER-FIT ROLES
================

Based on your career history, these roles might be better matches:

1. "Applied AI Engineer" at similar companies
   Match: 8/10 (strong Python, AI integration, production systems)

2. "Platform Engineer" at AI companies
   Match: 7.5/10 (strong DevOps, CI/CD, cloud infrastructure)

Search these roles on Japan Dev or similar platforms.
```

**Compare to Past Applications:**
If they've analyzed multiple jobs:
```
COMPARISON TO PREVIOUS APPLICATIONS
===================================

This role vs others you've analyzed:

1. Cookpad - Conversational AI: 4.5/10 (current)
2. Domain - Backend Engineer: 8/10 (analyzed last week)
3. Aryza - Automation Engineer: 9/10 (best match)

Recommendation: Focus on roles similar to #2 and #3
```

## Error Handling

**Job not found:**
```
✗ Job posting not found

URL: $ARGUMENTS

Run this first to cache the job data:
/career:fetch-job $ARGUMENTS

Then re-run:
/career:enhance-for-role $ARGUMENTS
```

**Career history empty:**
```
✗ Cannot analyze empty career history

Your career history file exists but has no employment entries.

Add your work experience first:
/career:add-experience

Then run enhancement analysis.
```

**Agent failure:**
```
✗ Enhancement analysis failed

Error: {error details}

This might be due to:
- Malformed job analysis data
- Invalid career history format
- Agent timeout

Try:
1. Re-fetch job: /career:fetch-job $ARGUMENTS
2. Verify career history: /career:list-history
3. Contact support if issue persists
```

## Examples

**Example 1: Cookpad Conversational AI Role**
```
User: /career:enhance-for-role https://japan-dev.com/jobs/cookpad/...

System fetches job (if not cached)
System loads career history
System invokes career-enhancer agent

Agent returns:
- 10 suggestions (3 high, 4 medium, 3 low impact)
- Projected improvement: 4.5 → 7.0
- Honest assessment: "Still a specialist role, but competitive with changes"

System asks: "Implement suggestions?"
User: y

System guides through:
1. Add League of Monkeys achievement → DONE
2. Add Domain optimization metric → DONE
3. Update Aryza description → Guided edit

Final result:
✓ Match improved from 4.5 to 6.5
✓ Recommendation: Apply with caution, highlight learning ability
```

**Example 2: Already Strong Match**
```
User: /career:enhance-for-role {perfect-fit-role-url}

System analyzes...

Agent returns:
Match: 8.5/10 - Strong candidate!

Minor suggestions:
- Add metric to achievement X (+0.5 points)

Recommendation: Apply now!
```

**Example 3: Poor Fit**
```
User: /career:enhance-for-role {ml-research-role-url}

System analyzes...

Agent returns:
Match: 2/10 - Fundamental mismatch

This role requires:
- PhD in ML/AI
- Published research
- Deep learning expertise

You have:
- Applied AI integration
- Production engineering
- No research background

Recommendation: Don't apply. Look for "Applied AI Engineer" or "ML Engineer" roles instead.
```

## Output Format

The command should produce:
1. **Loading status** (fetching job, loading data)
2. **Enhancement analysis** (from career-enhancer agent)
3. **Interactive implementation** (if user wants)
4. **Progress tracking** (what was changed)
5. **Final recommendation** (apply or not)

Keep output focused and actionable. The user should finish with:
- Clear understanding of their match level
- Specific actions to improve
- Realistic assessment of chances
- Next steps (apply, improve, or move on)

## Success Metrics

A successful run means:
- User understands their gaps
- User has actionable improvement plan
- User knows whether to apply
- Match score improved (if changes made)
- User saved hours of manual analysis
