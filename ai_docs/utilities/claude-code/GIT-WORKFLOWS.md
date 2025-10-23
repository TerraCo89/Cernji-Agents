# Claude Code Git Workflows

Source: `/anthropics/claude-code` (Context7)

## Automated Git Commit and Pull Request

```bash
user: "Commit my changes and create a PR"

# Claude will:
# 1. Run git status and git diff
# 2. Create a new branch if on main
# 3. Stage relevant files
# 4. Create commit with appropriate message
# 5. Push to origin
# 6. Create PR via gh cli

# Example commit format:
git commit -m "$(cat <<'EOF'
Add user authentication feature

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Create PR with template
gh pr create --title "Add authentication" --body "$(cat <<'EOF'
## Summary
- Implement JWT authentication
- Add login/logout endpoints
- Create auth middleware

## Test plan
- [ ] Test login flow
- [ ] Test token validation
- [ ] Test logout

🤖 Generated with [Claude.ai/code](https://claude.ai/code)
EOF
)"
```

## Clean Up [gone] Branches

### List Git worktrees to identify associated branches

```bash
git worktree list
```

### List Git branches to identify [gone] status

```bash
git branch -v
```

### Remove Git worktrees and delete [gone] branches

```bash
# Process all [gone] branches, removing '+' prefix if present
git branch -v | grep '\[gone\]' | sed 's/^[+* ]//' | awk '{print $1}' | while read branch; do
  echo "Processing branch: $branch"
  # Find and remove worktree if it exists
  worktree=$(git worktree list | grep "\\[$branch\\]" | awk '{print $1}')
  if [ ! -z "$worktree" ] && [ "$worktree" != "$(git rev-parse --show-toplevel)" ]; then
    echo "  Removing worktree: $worktree"
    git worktree remove --force "$worktree"
  fi
  # Delete the branch
  echo "  Deleting branch: $branch"
  git branch -D "$branch"
done
```

## GitHub Integration

### GitHub API Request Helper (TypeScript)

```typescript
#!/usr/bin/env bun

interface GitHubIssue {
  number: number;
  title: string;
  user: { id: number };
  created_at: string;
}

interface GitHubComment {
  id: number;
  body: string;
  created_at: string;
  user: { type: string; id: number };
}

async function githubRequest<T>(
  endpoint: string,
  token: string,
  method: string = 'GET',
  body?: any
): Promise<T> {
  const response = await fetch(`https://api.github.com${endpoint}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github.v3+json",
      "User-Agent": "auto-close-duplicates-script",
      ...(body && { "Content-Type": "application/json" }),
    },
    ...(body && { body: JSON.stringify(body) }),
  });

  if (!response.ok) {
    throw new Error(
      `GitHub API failed: ${response.status} ${response.statusText}`
    );
  }

  return response.json();
}

// Script searches for duplicates and auto-closes after 3 days
```

### GitHub Issue Deduplication

```bash
# Usage via slash command
/dedupe issue-number

# Direct script execution
./scripts/auto-close-duplicates.ts
```
