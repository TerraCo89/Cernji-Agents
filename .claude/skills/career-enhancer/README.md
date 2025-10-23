# Career Enhancer Skill

## Overview
Analyzes gaps between job requirements and career history to provide specific, actionable enhancement suggestions.

## Core Capabilities
- **Gap Analysis**: Identifies missing skills, hidden strengths, keyword gaps
- **Prioritized Suggestions**: High/medium/low impact recommendations
- **Impact Projection**: Calculates match score improvements
- **Honest Assessment**: Clearly identifies genuine gaps that can't be enhancement-fixed
- **Actionable Output**: Provides specific text, commands, and effort estimates

## Input Requirements
- **Job Analysis Data** (from job-analyzer skill)
- **Career History Data** (from data access layer)

## Output
Structured analysis with:
- Current match score (X/10)
- Prioritized enhancement opportunities (high/medium/low impact)
- Projected impact scores
- Realistic assessment and recommendation

## Enhancement Types
1. **Hidden Strengths** - Relevant experience not emphasized
2. **Missing Metrics** - Achievements lacking quantification
3. **Keyword Gaps** - ATS keywords missing but candidate has related experience
4. **Reframable Experience** - Existing work can use job's terminology
5. **Technology Additions** - Technologies used but not listed

## Usage
```
User: "How can I improve my resume for this job?"
Skill: Analyzes job requirements vs. career history → Returns prioritized suggestions
```

## Files
- `SKILL.md` - Main skill instructions (272 lines, <500 line requirement ✓)
- `references/example-analysis.md` - Complete example output (15KB)

## Validation
- ✓ YAML frontmatter valid (name ≤64 chars, description ≤1024 chars)
- ✓ Line count <500 (272 lines)
- ✓ Unix-style forward slashes for all file paths
- ✓ Data-agnostic pattern (receives data, returns analysis)
- ✓ Follows job-analyzer structure pattern
- ✓ Performance target: <3 seconds

## Integration
**Prerequisite:** Requires job-analyzer skill output
**Consumers:** resume-writer (future), cover-letter-writer (future)

## Key Principles
1. Be Specific - Name exact positions, provide ready-to-use text
2. Be Honest - Distinguish reframing from fabricating
3. Be Actionable - Every suggestion = one concrete action
4. Prioritize Impact - Focus on high-impact changes first
5. Be Realistic - Assess if enhancements will actually help
