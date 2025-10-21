---
description: Update your master resume with new achievements, skills, or feedback
allowed-tools: mcp__resume-agent__data_read_master_resume, mcp__resume-agent__data_read_career_history, mcp__resume-agent__data_write_master_resume, mcp__resume-agent__data_write_career_history, mcp__resume-agent__data_add_achievement, mcp__resume-agent__data_add_technology, SlashCommand
---

# Update Master Resume

## Interactive Resume Update Process

**Step 1: Load Current Master Resume**
Load master resume and career history using MCP tools:
```
master_resume = mcp__resume-agent__data_read_master_resume()
career_history = mcp__resume-agent__data_read_career_history()
```

Display a summary of current sections:
- Contact information
- Professional summary
- Work experience (number of positions)
- Skills and technologies (from employment history)

**Step 2: Identify What to Update**
Ask the user what they'd like to update:

**Options:**
a) Add new work experience
b) Update existing position with new achievements
c) Add new skills or technologies
d) Update professional summary
e) Add certifications or education
f) Incorporate feedback from successful applications
g) Remove outdated information

**Step 3: Gather Information**
Based on their choice, gather relevant information:

**For new work experience:**
- Company name and role
- Start and end dates (or "Present")
- Key responsibilities
- Quantifiable achievements (with metrics)
- Technologies used

**For updating achievements:**
- Which position to update
- New accomplishments to add
- Any metrics or impact numbers

**For new skills:**
- Skill name
- Proficiency level
- Recent projects where you used it

**For incorporating feedback:**
- Which applications got positive responses
- What elements seemed to resonate
- Patterns to emphasize going forward

**Step 4: Make Updates**
Use the appropriate MCP tool or delegate to specialized commands:

**For new work experience:**
```
/career:add-experience
```
This command will handle collecting all required information and updating both career history and master resume.

**For updating achievements:**
```
mcp__resume-agent__data_add_achievement(
  company="{company}",
  achievement_description="{description}",
  metric="{metric}" if provided else None
)
```

**For new skills/technologies:**
```
mcp__resume-agent__data_add_technology(
  company="{company}",
  technologies=["{tech1}", "{tech2}", ...]
)
```

**For updating professional summary or other sections:**
Load current data, modify the relevant section, and save:
```
resume_data = mcp__resume-agent__data_read_master_resume()
resume_data['professional_summary'] = "{updated_summary}"
mcp__resume-agent__data_write_master_resume(resume_data)
```

Follow these principles:
- Use action verbs (Led, Developed, Implemented, Designed)
- Include quantifiable metrics wherever possible
- Maintain reverse chronological order
- Ensure ATS-friendly formatting

**Step 5: Review and Confirm**
Show the changes made:
- Display the updated section(s)
- Highlight what was added or modified
- Verify the changes look correct

Ask if any additional updates are needed.

**Step 6: Recommendations**
Based on the updates, provide suggestions:
- If you added new skills, recommend running `/career:portfolio-matrix` to see updated proficiency
- If you added new work experience, suggest updating your LinkedIn profile
- Recommend running `/career:refresh-repos` if the updates relate to recent projects
- Suggest which types of jobs now become more relevant targets

**Step 7: Summary**
Confirm:
- Master resume and/or career history have been updated in the database
- Summary of changes made
- Recommended next steps

**Note:** All changes are stored in the SQLite database (`data/resume_agent.db`). You can switch to file-based storage by changing `STORAGE_BACKEND=file` in the `.env` file if needed.