# Claude Code Slash Command Examples

A comprehensive collection of simple and advanced slash command examples for Claude Code, organized by complexity and use case.

## Table of Contents

- [Simple Commands (Beginner)](#simple-commands-beginner)
- [Intermediate Commands](#intermediate-commands)
- [Advanced Commands](#advanced-commands)
- [Domain-Specific Commands](#domain-specific-commands)
- [Real-World Production Examples](#real-world-production-examples)

---

## Simple Commands (Beginner)

### 1. Basic Test Runner

**File:** `.claude/commands/test.md`

```markdown
---
allowed-tools: Bash(npm test:*), Bash(npm run test:*)
description: Run the test suite
---

Run the project's test suite using npm test or the appropriate test command for this project.
```

**Usage:** `/test`

**When to use:** Quick test execution for projects with a standard test script.

---

### 2. Build Command

**File:** `.claude/commands/build.md`

```markdown
---
allowed-tools: Bash(npm:*), Bash(pnpm:*), Bash(yarn:*)
description: Build the project
---

Build the project using the appropriate package manager (npm, pnpm, or yarn).
Check package.json for the build script and execute it.
```

**Usage:** `/build`

**When to use:** Standard project builds before deployment or testing.

---

### 3. Code Formatter

**File:** `.claude/commands/format.md`

```markdown
---
allowed-tools: Bash(npx prettier:*), Bash(npm run format:*)
description: Format all code files
---

Format all code files in the project using Prettier or the project's configured formatter.
Run the format command and report any files that were changed.
```

**Usage:** `/format`

**When to use:** Ensure code consistency before commits.

---

### 4. Dependency Update Check

**File:** `.claude/commands/check-updates.md`

```markdown
---
allowed-tools: Bash(npm outdated:*), Bash(npx npm-check-updates:*)
description: Check for outdated dependencies
---

Check for outdated npm packages and report which dependencies have newer versions available.
Categorize updates by major, minor, and patch versions.
```

**Usage:** `/check-updates`

**When to use:** Regular dependency maintenance.

---

### 5. Dev Server Starter

**File:** `.claude/commands/dev.md`

```markdown
---
allowed-tools: Bash(npm run dev:*), Bash(npm start:*)
description: Start the development server
---

Start the development server for this project.
Check package.json for dev or start script and execute it.
```

**Usage:** `/dev`

**When to use:** Quick local development server launch.

---

## Intermediate Commands

### 6. Git Commit (Conventional Commits)

**File:** `.claude/commands/commit.md`

```markdown
---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Create a git commit with conventional commit format
model: claude-haiku-4-5
---

## Context

Current status:
!`git status`

Staged and unstaged changes:
!`git diff HEAD`

Current branch:
!`git branch --show-current`

Recent commits:
!`git log --oneline -10`

## Your task

Create a single git commit using conventional commit format.

**Commit message format:** `<type>: <description>`

**Types:**
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes (formatting, etc.)
- refactor: Code refactoring
- perf: Performance improvements
- test: Adding or updating tests
- chore: Maintenance tasks

**Rules:**
1. Use imperative mood ("add feature" not "added feature")
2. Keep first line under 72 characters
3. Add detailed description if needed (separated by blank line)
4. Only commit staged files if any exist, otherwise stage relevant files first

Only execute the permitted tool calls. No additional text or messages.
```

**Usage:** `/commit` or `/commit --no-verify`

**When to use:** Creating well-formatted commits that follow conventional commit standards.

---

### 7. Lint and Fix

**File:** `.claude/commands/lint-fix.md`

```markdown
---
allowed-tools: Bash(npm run lint:*), Bash(npx eslint:*), Edit(**/*.{js,ts,tsx,jsx})
description: Run linter and auto-fix issues
---

## Task

1. Run the project's linter (ESLint or configured linter)
2. Identify any errors or warnings
3. Auto-fix issues where possible using the linter's fix flag
4. For issues that can't be auto-fixed, offer to manually fix them
5. Report summary of fixes applied

Run linter with --fix flag first, then report remaining issues.
```

**Usage:** `/lint-fix`

**When to use:** Clean up code quality issues before commits.

---

### 8. Security Audit

**File:** `.claude/commands/security-audit.md`

```markdown
---
allowed-tools: Bash(npm audit:*), Bash(pnpm audit:*), Bash(yarn audit:*)
description: Run security vulnerability audit
---

## Task

1. Run security audit using the package manager (npm/pnpm/yarn)
2. Identify vulnerabilities by severity (critical, high, moderate, low)
3. Report which packages have vulnerabilities
4. Suggest whether to run audit fix or manual updates
5. Highlight any critical vulnerabilities that need immediate attention

Provide clear summary of security status.
```

**Usage:** `/security-audit`

**When to use:** Regular security checks, especially before releases.

---

### 9. Generate Documentation

**File:** `.claude/commands/gen-docs.md`

```markdown
---
allowed-tools: Read(**/*.{js,ts,tsx,jsx}), Write(**/*.md), Bash(npx typedoc:*)
description: Generate or update documentation
---

## Task

1. Analyze the codebase structure
2. Identify undocumented or poorly documented files
3. Generate/update:
   - API documentation
   - Component documentation
   - README sections
   - Code comments for complex functions
4. Use TypeDoc or appropriate tool if available
5. Ensure documentation follows project conventions

Focus on public APIs and exported functions.
```

**Usage:** `/gen-docs`

**When to use:** Keeping documentation in sync with code changes.

---

### 10. Fix GitHub Issue

**File:** `.claude/commands/fix-issue.md`

```markdown
---
allowed-tools: Bash(gh issue view:*), Read(**/*), Edit(**/*), Bash(npm:*), Bash(git:*)
description: Analyze and fix a GitHub issue
argument-hint: <issue-number>
---

## Task

Fix GitHub issue #$ARGUMENTS

**Steps:**
1. Use `gh issue view $ARGUMENTS` to get issue details
2. Understand the problem from issue description
3. Search codebase for relevant files
4. Implement necessary code changes
5. Write or update tests for the fix
6. Ensure tests pass: `npm test`
7. Ensure linting passes: `npm run lint`
8. Provide summary of changes made

Reference issue #$ARGUMENTS in your analysis.
```

**Usage:** `/fix-issue 123`

**When to use:** Systematic issue resolution with GitHub integration.

---

## Advanced Commands

### 11. Commit, Push, and Create PR

**File:** `.claude/commands/commit-push-pr.md`

```markdown
---
allowed-tools: Bash(git checkout --branch:*), Bash(git add:*), Bash(git status:*), Bash(git push:*), Bash(git commit:*), Bash(gh pr create:*)
description: Commit, push, and open a PR
---

## Context

Current status:
!`git status`

Changes:
!`git diff HEAD`

Current branch:
!`git branch --show-current`

## Your task

Execute ALL of the following in a single response:

1. **Create branch** (if on main/master):
   - Generate descriptive branch name based on changes
   - Format: `feature/description` or `fix/description`

2. **Commit changes**:
   - Stage all changes
   - Create commit with conventional commit format
   - Use descriptive message explaining the changes

3. **Push to remote**:
   - Push branch to origin with `-u` flag

4. **Create Pull Request**:
   - Use `gh pr create` with title and body
   - Title: Clear, concise description
   - Body: Summary of changes, testing performed, breaking changes (if any)

You MUST do all steps above in a single message using multiple tool calls.
```

**Usage:** `/commit-push-pr`

**When to use:** Complete Git workflow automation from changes to PR.

**Key feature:** Demonstrates batching multiple git operations in a single response.

---

### 12. Feature Development Workflow

**File:** `.claude/commands/feature.md`

```markdown
---
allowed-tools: Read(**/*), Write(**/*), Edit(**/*), Bash(git:*), Bash(npm:*), Bash(gh:*)
description: Implement a complete feature with tests and docs
argument-hint: <feature-description>
---

## Feature Development: $ARGUMENTS

**Workflow:**

### 1. Planning Phase
- Analyze requirements from: $ARGUMENTS
- Identify affected files and components
- Design approach and architecture
- List required tests

### 2. Implementation Phase
- Create feature branch: `feature/$ARGUMENTS`
- Implement core functionality
- Follow project's coding conventions
- Add error handling and edge cases

### 3. Testing Phase
- Write unit tests for new code
- Write integration tests if needed
- Ensure all tests pass
- Check code coverage

### 4. Documentation Phase
- Update README if needed
- Add JSDoc/TSDoc comments
- Update API documentation
- Add usage examples

### 5. Quality Check
- Run linter and fix issues
- Run formatter
- Security audit if dependencies changed
- Performance check for critical paths

### 6. Finalization
- Commit with descriptive message
- Push to remote
- Create PR with detailed description
- Add appropriate labels

Provide status updates after each phase.
```

**Usage:** `/feature add user authentication with OAuth2`

**When to use:** Complete feature implementation from scratch to PR.

**Complexity:** Multi-phase workflow with planning, implementation, testing, and documentation.

---

### 13. Code Review Automation

**File:** `.claude/commands/review.md`

```markdown
---
allowed-tools: Read(**/*), Bash(git diff:*), Bash(git log:*)
description: Comprehensive code review of current changes
---

## Code Review Checklist

Analyze changes and review for:

### 1. **Code Quality**
- [ ] Follows project conventions and style guide
- [ ] No code duplication
- [ ] Functions are focused and do one thing well
- [ ] Appropriate use of language features
- [ ] No commented-out code

### 2. **Error Handling**
- [ ] Proper error handling for all failure cases
- [ ] Meaningful error messages
- [ ] No silent failures
- [ ] Appropriate use of try-catch blocks

### 3. **Performance**
- [ ] No unnecessary computations
- [ ] Efficient algorithms used
- [ ] No memory leaks
- [ ] Appropriate use of async/await

### 4. **Security**
- [ ] No hardcoded secrets or credentials
- [ ] Input validation present
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] Secure dependencies

### 5. **Testing**
- [ ] Adequate test coverage
- [ ] Edge cases tested
- [ ] Tests are readable and maintainable

### 6. **Documentation**
- [ ] Public APIs documented
- [ ] Complex logic explained
- [ ] README updated if needed

### 7. **Accessibility** (for UI changes)
- [ ] Semantic HTML used
- [ ] ARIA attributes where needed
- [ ] Keyboard navigation works
- [ ] Screen reader compatible

**Provide:**
1. Summary of what changed
2. Issues found (categorized by severity)
3. Specific recommendations for improvements
4. Approval status (APPROVE / REQUEST_CHANGES / COMMENT)
```

**Usage:** `/review`

**When to use:** Automated code review before submitting PRs.

**Key feature:** Comprehensive checklist covering quality, security, performance, and accessibility.

---

### 14. Release Preparation

**File:** `.claude/commands/prepare-release.md`

```markdown
---
allowed-tools: Read(**/*), Edit(**/*), Bash(git:*), Bash(npm:*), Bash(gh:*)
description: Prepare codebase for a new release
argument-hint: <version> (e.g., 1.2.0)
---

## Release Preparation for v$ARGUMENTS

### 1. Version Bump
- Update version in package.json to $ARGUMENTS
- Update version in package-lock.json
- Check for other version references (README, docs)

### 2. Changelog Update
- Review commits since last release: `git log <last-tag>..HEAD --oneline`
- Generate CHANGELOG entry for v$ARGUMENTS
- Categorize changes: Features, Bug Fixes, Breaking Changes, Dependencies
- Add release date

### 3. Documentation Review
- Ensure README is up to date
- Update migration guides for breaking changes
- Verify all examples work
- Check links aren't broken

### 4. Quality Checks
- Run full test suite: `npm test`
- Run linter: `npm run lint`
- Run security audit: `npm audit`
- Check bundle size (if applicable)
- Build production bundle: `npm run build`

### 5. Final Checks
- Verify all CI checks pass
- Review open issues and PRs
- Ensure dependencies are up to date
- Check license headers if required

### 6. Git Operations
- Create commit: "chore: prepare release v$ARGUMENTS"
- Create git tag: `git tag -a v$ARGUMENTS -m "Release v$ARGUMENTS"`
- Push commits and tags

### 7. Release Notes
- Generate release notes from CHANGELOG
- Highlight breaking changes
- Include upgrade instructions
- Add contributor acknowledgments

Provide summary and checklist of completed tasks.
```

**Usage:** `/prepare-release 2.1.0`

**When to use:** Comprehensive release preparation automation.

**Complexity:** Multi-step workflow coordinating versioning, documentation, testing, and Git operations.

---

### 15. Database Migration Command

**File:** `.claude/commands/db-migrate.md`

```markdown
---
allowed-tools: Bash(npx:*), Bash(npm run db:*), Read(**/*.sql), Read(**/*migration*), Write(**/*migration*)
description: Create and apply database migration
argument-hint: <migration-name>
---

## Database Migration: $ARGUMENTS

### 1. Analysis Phase
- Review current database schema
- Understand required changes for: $ARGUMENTS
- Check existing migrations for patterns
- Identify potential conflicts or risks

### 2. Migration Creation
- Generate migration file using project's tool (Prisma, TypeORM, Knex, etc.)
- Name: `YYYYMMDDHHMMSS_$ARGUMENTS`
- Include both `up` and `down` migrations
- Add comments explaining the changes

### 3. Migration Content
**Include:**
- Schema changes (CREATE, ALTER, DROP)
- Data migrations if needed
- Indexes for new columns
- Foreign key constraints
- Rollback logic in `down` migration

**Consider:**
- Backward compatibility
- Performance impact on large tables
- Zero-downtime deployment requirements
- Transaction wrapping

### 4. Validation
- Review migration SQL
- Check for breaking changes
- Verify down migration reverses up migration
- Test on development database

### 5. Documentation
- Update schema documentation
- Add migration notes to CHANGELOG
- Document any manual steps required
- Update data model diagrams if applicable

### 6. Execution
- Run migration on development: `npm run db:migrate`
- Verify schema changes
- Test affected queries
- Provide rollback command

**Output:**
1. Migration file path
2. Summary of changes
3. Rollback command
4. Testing recommendations
```

**Usage:** `/db-migrate add_user_preferences_table`

**When to use:** Database schema changes with proper migration management.

**Complexity:** Handles migration generation, validation, and safe execution with rollback support.

---

## Domain-Specific Commands

### 16. Next.js Route Generator

**File:** `.claude/commands/nextjs-route.md`

```markdown
---
allowed-tools: Write(app/**/*), Write(src/app/**/*), Read(app/**/*), Bash(npm:*)
description: Generate Next.js App Router route
argument-hint: <route-path>
---

## Generate Next.js Route: $ARGUMENTS

### Route Structure
Create route at: `app/$ARGUMENTS/`

### 1. Page Component
**File:** `app/$ARGUMENTS/page.tsx`

```typescript
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: '...',
  description: '...',
}

export default function Page() {
  return (
    <div>
      <h1>$ARGUMENTS</h1>
    </div>
  )
}
```

### 2. Loading State
**File:** `app/$ARGUMENTS/loading.tsx`

```typescript
export default function Loading() {
  return <div>Loading...</div>
}
```

### 3. Error Boundary
**File:** `app/$ARGUMENTS/error.tsx`

```typescript
'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={() => reset()}>Try again</button>
    </div>
  )
}
```

### 4. Layout (if needed)
**File:** `app/$ARGUMENTS/layout.tsx`

```typescript
export default function Layout({ children }: { children: React.Node }) {
  return <section>{children}</section>
}
```

### 5. API Route (if applicable)
**File:** `app/api/$ARGUMENTS/route.ts`

```typescript
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  return NextResponse.json({ message: 'Hello' })
}
```

**Provide:**
- List of created files
- Route URL path
- Example navigation code
- Suggested next steps
```

**Usage:** `/nextjs-route dashboard/settings`

**When to use:** Scaffolding new Next.js routes with all necessary files.

---

### 17. React Component Generator

**File:** `.claude/commands/react-component.md`

```markdown
---
allowed-tools: Write(src/components/**/*), Write(**/*.tsx), Write(**/*.test.tsx), Read(src/components/**/*)
description: Generate React component with tests and stories
argument-hint: <ComponentName>
---

## Generate React Component: $ARGUMENTS

### 1. Component File
**File:** `src/components/$ARGUMENTS/$ARGUMENTS.tsx`

```typescript
import React from 'react'
import styles from './$ARGUMENTS.module.css'

export interface ${ARGUMENTS}Props {
  // Define props
}

export const $ARGUMENTS: React.FC<${ARGUMENTS}Props> = (props) => {
  return (
    <div className={styles.container}>
      {/* Component content */}
    </div>
  )
}
```

### 2. Test File
**File:** `src/components/$ARGUMENTS/$ARGUMENTS.test.tsx`

```typescript
import { render, screen } from '@testing-library/react'
import { $ARGUMENTS } from './$ARGUMENTS'

describe('$ARGUMENTS', () => {
  it('renders without crashing', () => {
    render(<$ARGUMENTS />)
    // Add assertions
  })
})
```

### 3. CSS Module
**File:** `src/components/$ARGUMENTS/$ARGUMENTS.module.css`

```css
.container {
  /* Component styles */
}
```

### 4. Index File
**File:** `src/components/$ARGUMENTS/index.ts`

```typescript
export { $ARGUMENTS } from './$ARGUMENTS'
export type { ${ARGUMENTS}Props } from './$ARGUMENTS'
```

### 5. Storybook Story (if Storybook configured)
**File:** `src/components/$ARGUMENTS/$ARGUMENTS.stories.tsx`

```typescript
import type { Meta, StoryObj } from '@storybook/react'
import { $ARGUMENTS } from './$ARGUMENTS'

const meta: Meta<typeof $ARGUMENTS> = {
  component: $ARGUMENTS,
}

export default meta
type Story = StoryObj<typeof $ARGUMENTS>

export const Default: Story = {
  args: {},
}
```

**Summary:**
- Component structure
- Files created
- Usage example
- Suggested props to add
```

**Usage:** `/react-component UserAvatar`

**When to use:** Creating new React components with complete boilerplate.

---

### 18. Python FastAPI Endpoint

**File:** `.claude/commands/fastapi-endpoint.md`

```markdown
---
allowed-tools: Edit(app/**/*.py), Edit(src/**/*.py), Write(**/*.py), Bash(python:*), Bash(pytest:*)
description: Create FastAPI endpoint with tests
argument-hint: <endpoint-path> <method>
---

## Create FastAPI Endpoint: $ARGUMENTS

Parse arguments: `<path>` and `<method>` from $ARGUMENTS

### 1. Router/Endpoint
Add to appropriate router file:

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter()

class RequestModel(BaseModel):
    # Define request schema
    pass

class ResponseModel(BaseModel):
    # Define response schema
    pass

@router.<method>("<path>")
async def endpoint_function(
    data: RequestModel,
    # Add dependencies
) -> ResponseModel:
    """
    Endpoint description.

    Args:
        data: Request data

    Returns:
        Response data

    Raises:
        HTTPException: If validation fails
    """
    try:
        # Implementation
        return ResponseModel()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. Test File
**File:** `tests/test_<endpoint_name>.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_endpoint_success():
    response = client.<method>("<path>", json={})
    assert response.status_code == 200
    assert "expected_field" in response.json()

def test_endpoint_validation_error():
    response = client.<method>("<path>", json={})
    assert response.status_code == 422

def test_endpoint_not_found():
    response = client.<method>("<path>/invalid", json={})
    assert response.status_code == 404
```

### 3. Update OpenAPI Docs
- Add endpoint description
- Document request/response models
- Add example payloads
- Include error responses

### 4. Run Tests
Execute: `pytest tests/test_<endpoint_name>.py -v`

**Provide:**
- Endpoint URL
- Request/response schemas
- Test results
- OpenAPI docs URL
```

**Usage:** `/fastapi-endpoint /api/users POST`

**When to use:** Adding new FastAPI endpoints with proper structure and tests.

---

## Real-World Production Examples

### 19. Pre-Deployment Checklist

**File:** `.claude/commands/pre-deploy.md`

```markdown
---
allowed-tools: Bash(git:*), Bash(npm:*), Bash(docker:*), Read(**/*), Bash(gh:*)
description: Run comprehensive pre-deployment checks
---

## Pre-Deployment Checklist

### 1. Code Quality
- [ ] All tests pass: `npm test`
- [ ] Linting passes: `npm run lint`
- [ ] Type checking passes: `npm run type-check`
- [ ] No TODO/FIXME comments in production code
- [ ] Code coverage meets threshold (check with `npm run coverage`)

### 2. Security
- [ ] Security audit clean: `npm audit --production`
- [ ] No exposed secrets or API keys
- [ ] Dependencies up to date (critical patches only)
- [ ] Security headers configured
- [ ] CORS settings reviewed

### 3. Performance
- [ ] Bundle size within limits
- [ ] Images optimized
- [ ] No console.log in production
- [ ] API rate limiting configured
- [ ] Database queries optimized

### 4. Configuration
- [ ] Environment variables documented
- [ ] Production config reviewed
- [ ] Feature flags set correctly
- [ ] Third-party service credentials valid
- [ ] Database migration ready

### 5. Documentation
- [ ] CHANGELOG updated
- [ ] API docs current
- [ ] README reflects latest changes
- [ ] Deployment instructions current

### 6. Git Status
- [ ] All changes committed
- [ ] Working on correct branch
- [ ] Branch up to date with main
- [ ] PR approved and merged
- [ ] Release tagged

### 7. Infrastructure
- [ ] CI/CD pipeline passing
- [ ] Staging deployment successful
- [ ] Database backups verified
- [ ] Monitoring/alerting configured
- [ ] Rollback plan documented

### 8. Final Checks
- [ ] Smoke tests pass on staging
- [ ] Performance tests acceptable
- [ ] Load testing (if applicable)
- [ ] Team notified of deployment

**Execute each check and provide:**
- ✅ PASS / ❌ FAIL for each item
- Details of any failures
- Recommended actions before deployment
- Overall readiness: READY / NOT READY
```

**Usage:** `/pre-deploy`

**When to use:** Before production deployments to catch issues early.

---

### 20. Hotfix Workflow

**File:** `.claude/commands/hotfix.md`

```markdown
---
allowed-tools: Bash(git:*), Bash(npm:*), Edit(**/*), Bash(gh:*), Read(**/*)
description: Emergency hotfix workflow
argument-hint: <issue-description>
---

## HOTFIX: $ARGUMENTS

**EMERGENCY WORKFLOW - EXPEDITED PROCESS**

### 1. Create Hotfix Branch (30 seconds)
```bash
git checkout main
git pull origin main
git checkout -b hotfix/$ARGUMENTS
```

### 2. Identify and Fix Issue (5-10 minutes)
- Locate problematic code
- Implement minimal fix (no refactoring!)
- Test the specific fix
- Verify no new issues introduced

### 3. Testing (2-3 minutes)
- Run affected unit tests
- Quick manual smoke test
- Check no regressions in critical paths

### 4. Fast-Track Approval Process
```bash
git add .
git commit -m "hotfix: $ARGUMENTS"
git push origin hotfix/$ARGUMENTS
gh pr create --title "HOTFIX: $ARGUMENTS" --body "Emergency fix for: $ARGUMENTS" --label hotfix
```

### 5. Deployment Steps
- Request immediate PR review
- Merge to main upon approval
- Deploy to production
- Monitor for 15 minutes post-deployment

### 6. Post-Hotfix
- Update CHANGELOG
- Create issue for proper fix
- Schedule retrospective
- Document incident

**Constraints:**
- Keep changes minimal
- Only fix the specific issue
- No feature additions
- No refactoring
- Focus on speed and safety

**Provide:**
- Issue analysis
- Fix implemented
- Test results
- Deployment commands
- Monitoring checklist
```

**Usage:** `/hotfix critical authentication bypass`

**When to use:** Production emergencies requiring immediate fixes.

**Key feature:** Optimized for speed while maintaining safety checks.

---

## Command Argument Features

### Using $ARGUMENTS

All arguments after command name:

```markdown
---
argument-hint: <description>
---

Process: $ARGUMENTS
```

Usage: `/command everything after command name`

### Using Positional Arguments

Individual arguments by position:

```markdown
---
argument-hint: <arg1> <arg2>
---

First: $1
Second: $2
All: $ARGUMENTS
```

Usage: `/command value1 value2`

### Optional Arguments

Handle optional arguments:

```markdown
---
argument-hint: <required> [optional]
---

Required parameter: $1
Optional parameter (may be empty): $2
```

## Advanced Techniques

### 1. Conditional Logic

```markdown
Check if tests exist:
!`test -d tests && echo "yes" || echo "no"`

If yes, run tests. If no, suggest creating tests.
```

### 2. Dynamic Context

```markdown
Current git status:
!`git status --porcelain`

If files are staged, commit them.
If no files staged, suggest staging files first.
```

### 3. Multi-Tool Coordination

```markdown
1. Check environment: !`node --version`
2. Based on version, use appropriate build command
3. Run build
4. If successful, run tests
5. If tests pass, create commit
```

### 4. Model Selection for Cost Optimization

```markdown
---
model: claude-haiku-4-5
---

Use faster, cheaper model for simple tasks like commits.
```

## Best Practices

1. **Start Simple**: Begin with basic commands, add complexity as needed
2. **Clear Descriptions**: Make it obvious what each command does
3. **Limit Scope**: Use `allowed-tools` to restrict what commands can do
4. **Add Context**: Use `!`command`` to provide runtime context
5. **Handle Errors**: Include error checking and recovery steps
6. **Document Arguments**: Use `argument-hint` to show usage
7. **Version Control**: Commit command files to share with team
8. **Test Commands**: Verify commands work as expected before sharing
9. **Optimize Costs**: Use `model: claude-haiku-4-5` for simple tasks
10. **Provide Feedback**: Commands should report what they did

## Community Resources

- **awesome-claude-code**: https://github.com/hesreallyhim/awesome-claude-code
- **Claude Command Suite**: https://github.com/qdhenry/Claude-Command-Suite
- **Production Commands**: https://github.com/wshobson/commands
- **Official Docs**: https://docs.claude.com/en/docs/claude-code/slash-commands

## Next Steps

1. Create `.claude/commands/` directory in your project
2. Start with 2-3 simple commands you use frequently
3. Test and refine them
4. Share useful commands with your team
5. Explore community command collections for inspiration
6. Build complex workflows as you become comfortable

---

**Pro Tip**: Commands in `.claude/commands/` are project-specific and versioned with your code. Commands in `~/.claude/commands/` are personal and available across all projects.
