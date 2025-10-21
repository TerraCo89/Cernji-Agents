---
description: Refresh cached list of your GitHub repositories for faster portfolio searches
allowed-tools: Bash(gh:*), Write
---

# Refresh Repository Cache

## Process

**Step 1: Verify GitHub CLI Access**
Check that GitHub CLI is authenticated and has repository access:
- Run `gh auth status` to verify authentication
- Ensure you have the 'repo' scope for accessing private repositories

If not authenticated or missing scopes, provide instructions to run:
```
gh auth login --scopes repo
```

**Step 2: Fetch Complete Repository List**
Use `gh repo list --limit 100 --json name,description,primaryLanguage,url,updatedAt,isPrivate --source`

This gets all your source repositories (not forks) with relevant metadata in JSON format.

**Step 3: Filter and Process**
Process the JSON to:
- Separate private vs public repos
- Sort by last updated (most recent first)
- Extract key metadata for quick lookups
- Count repositories by primary language

**Step 4: Save Cache**
Create the cache directory if it doesn't exist: `.claude/.cache/`

Write to `.claude/.cache/repositories.json` with structure:
```json
{
  "last_updated": "2025-10-14T10:30:00Z",
  "total_repos": 45,
  "private_count": 30,
  "public_count": 15,
  "languages": {
    "Python": 15,
    "JavaScript": 12,
    "TypeScript": 8,
    "Go": 5,
    "Other": 5
  },
  "repos": [
    {
      "name": "owner/repo-name",
      "description": "Brief description",
      "language": "Python",
      "url": "https://github.com/owner/repo-name",
      "updated": "2025-10-10T15:20:00Z",
      "is_private": true
    }
  ]
}
```

**Step 5: Summary Report**
Report:
- Total repositories found
- Breakdown by language
- Number of private vs public
- Most recently updated repositories (top 5)
- Cache location and timestamp
- When to refresh next (recommend weekly)

Tell me: "Repository cache refreshed successfully. Portfolio searches will now be faster. Cache valid for 7 days."