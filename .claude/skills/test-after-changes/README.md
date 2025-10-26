# Test After Changes Skill

Quick validation workflow skill for testing services after making functional code changes.

## Purpose

Provides a standardized, fast checklist to validate code changes before committing. Catches common issues like broken imports, syntax errors, and service startup failures.

## When to Invoke

This skill should be invoked automatically by Claude Code **after completing any functional code changes**, including:
- Refactoring (moving files, renaming modules, changing imports)
- Adding new features
- Fixing bugs
- Changing dependencies
- Modifying service configuration

## Skill Behavior

When invoked, the skill instructs Claude Code to:

1. **Run fast validation checks** (syntax, imports, service startup)
2. **Report results clearly** (pass/fail with specific errors)
3. **Provide actionable fixes** if validation fails
4. **Only mark task complete** after all validations pass

## Key Features

- **Ordered by speed**: Fastest checks first (fail fast)
- **Service-specific**: Different validation for different apps in the monorepo
- **Actionable**: Specific commands to run, not abstract advice
- **Exit criteria**: Clear definition of "done"

## Usage

### Automatic Invocation

Claude Code should automatically use this skill after:
- Completing a refactoring task
- Finishing feature implementation
- Fixing a bug that involved code changes

### Manual Invocation

User can explicitly request:
```
Run the test-after-changes skill
```

Or:
```
Validate the changes I just made
```

## Example Workflow

1. User: "Move minimal_agent.py to examples/ directory"
2. Claude: *Moves files, updates imports*
3. Claude: *Automatically invokes test-after-changes skill*
4. Claude: *Runs syntax check, import validation, service startup test*
5. Claude: Reports results to user
6. Claude: Only marks task complete if all validations pass

## Integration with Development Workflow

The skill recommends creating:
- `scripts/validate-changes.sh` - Complete validation script
- `.pre-commit-config.yaml` - Git pre-commit hooks
- `.github/workflows/validate.yml` - CI/CD validation

## Related Skills

- **skill-creator** - For creating/modifying skills
- **deep-researcher** - For researching validation approaches
- **doc-fetcher** - For fetching testing library documentation

## Customization

The skill can be extended to include:
- Performance benchmarks (if changes affect performance-critical code)
- Security scans (if changes touch authentication/authorization)
- Database migration validation (if schema changes)
- API contract testing (if API changes)

## Success Metrics

This skill is successful when:
- All functional code changes are validated before committing
- Broken imports are caught immediately (not in CI/production)
- Service startup failures are caught locally
- Users receive clear pass/fail status with actionable fixes
