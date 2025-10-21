---
description: Add an achievement to an existing employment position (updates resumes/career-history.yaml)
allowed-tools: mcp__resume-agent__data_read_career_history, mcp__resume-agent__data_add_achievement
---

# Add Achievement to Employment History

## Purpose
Add quantified achievements to strengthen your resume with measurable impact and improve ATS optimization.

## Process

1. **Load career history**
   ```
   mcp__resume-agent__data_read_career_history()
   ```

2. **Determine target company**
   - If company provided as argument (e.g., `/career:add-achievement Aryza`), verify it exists
   - If not provided, display list of companies and ask user to select

3. **Collect achievement details**
   - Ask: "Describe the achievement (what you did and the impact):"
   - Ask: "Metric (optional, e.g., '95%', '10x', '#1'):" [can skip]

4. **Save achievement**
   ```
   mcp__resume-agent__data_add_achievement(
     company="{company}",
     achievement_description="{description}",
     metric="{metric}" if provided else None
   )
   ```

5. **Confirm success**
   Display confirmation with the added achievement and current list of all achievements for that company.