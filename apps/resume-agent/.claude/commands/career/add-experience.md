---
description: Add a new employment position to your career history (updates resumes/career-history.yaml and master resume)
allowed-tools: mcp__resume-agent__data_read_career_history, mcp__resume-agent__data_write_career_history, mcp__resume-agent__data_read_master_resume, mcp__resume-agent__data_write_master_resume
---

# Add New Employment Experience

## Purpose
Add a complete new employment entry to your career history and master resume.

## Process

1. **Load current data**
   ```
   mcp__resume-agent__data_read_career_history()
   mcp__resume-agent__data_read_master_resume()
   ```

2. **Collect required information**
   - Company name
   - Job title
   - Start date (format: YYYY-MM or Month YYYY)
   - End date (format: YYYY-MM, Month YYYY, or blank for current position)
   - Job description (2-4 sentences)

3. **Collect optional information**
   - Employment type (default: Full-time)
   - Technologies (comma-separated list)
   - Achievements (can add now or later with `/career:add-achievement`)

4. **Save to both files**

   Create employment entry and add to career history (prepend to list - newest first):
   ```
   new_employment = {
     "company": company,
     "title": title,
     "employment_type": employment_type,
     "start_date": start_date,
     "end_date": end_date or None,
     "description": description,
     "technologies": technologies,
     "achievements": achievements or None
   }

   history_data['employment_history'].insert(0, new_employment)
   mcp__resume-agent__data_write_career_history(history_data)
   ```

   Add to master resume:
   ```
   resume_entry = {
     "company": company,
     "position": title,
     "employment_type": employment_type,
     "start_date": start_date,
     "end_date": end_date or None,
     "description": description,
     "technologies": technologies
   }

   resume_data['employment_history'].insert(0, resume_entry)
   mcp__resume-agent__data_write_master_resume(resume_data)
   ```

5. **Confirm success**
   Display confirmation showing the new position has been added to both career history and master resume.