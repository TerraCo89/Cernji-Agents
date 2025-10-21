---
description: List user's employment history
allowed-tools: mcp__resume-agent__data_read_career_history
---

# List Career History

## Purpose
Display the user's employment history in an organized view to help:
- Find specific positions to update
- Identify gaps to fill for target roles
- Prepare for adding new achievements

## Process

1. **Load career history**
   ```
   mcp__resume-agent__data_read_career_history()
   ```

2. **Display employment history**
   Return a simplified list of employment positions from the career history in YAML format.

   **IMPORTANT**: Only use information from the loaded career history data. Do not include examples.
