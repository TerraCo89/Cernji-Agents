# Claude Code Documentation

Comprehensive documentation for Claude Code custom slash commands, organized and maintained for quick reference.

## Available Documentation

### 1. [custom-slash-commands.md](./custom-slash-commands.md)
**Complete reference guide** covering all aspects of Claude Code slash commands:
- Command structure and syntax
- Built-in commands
- Permission patterns
- Hooks and validation
- Plugin system
- Configuration
- Environment variables
- Best practices

**When to use:** Learning Claude Code fundamentals, configuration reference, understanding features.

### 2. [slash-command-examples.md](./slash-command-examples.md)
**Practical examples collection** with 20+ working slash commands:
- **Simple Commands** (5 examples) - Quick tasks like testing, building, formatting
- **Intermediate Commands** (5 examples) - Git workflows, linting, documentation
- **Advanced Commands** (5 examples) - Multi-step workflows, feature development, releases
- **Domain-Specific** (3 examples) - Next.js, React, FastAPI templates
- **Production Examples** (2 examples) - Pre-deployment checks, hotfix workflows

**When to use:** Creating your own commands, finding templates for common tasks, learning patterns.

## Quick Start

### Creating Your First Command

1. **Create commands directory:**
   ```bash
   mkdir -p .claude/commands
   ```

2. **Create a simple command:**
   ```bash
   cat > .claude/commands/test.md << 'EOF'
   ---
   allowed-tools: Bash(npm test:*)
   description: Run tests
   ---

   Run the project's test suite using npm test.
   EOF
   ```

3. **Use the command:**
   ```bash
   /test
   ```

### Command Types

- **Project Commands**: `.claude/commands/` - Shared with team via git
- **Personal Commands**: `~/.claude/commands/` - Personal across all projects

## Common Use Cases

### Development Workflows
- `/test` - Run test suite
- `/build` - Build project
- `/dev` - Start dev server
- `/lint-fix` - Fix linting issues
- `/format` - Format code

### Git Operations
- `/commit` - Create conventional commit
- `/commit-push-pr` - Full PR workflow
- `/fix-issue 123` - Fix GitHub issue

### Code Quality
- `/review` - Code review automation
- `/security-audit` - Check vulnerabilities
- `/gen-docs` - Generate documentation

### Deployment
- `/pre-deploy` - Pre-deployment checklist
- `/prepare-release 1.0.0` - Release preparation
- `/hotfix critical-bug` - Emergency fixes

## Features Overview

### Arguments
```markdown
---
argument-hint: <required> [optional]
---

Fix issue #$ARGUMENTS
Use $1, $2 for positional args
```

### Dynamic Context
```markdown
Current status:
!`git status`

Recent commits:
!`git log --oneline -5`
```

### Permission Control
```markdown
---
allowed-tools: Bash(git:*), Edit(**/*.ts)
---
```

### Model Selection
```markdown
---
model: claude-haiku-4-5
---

Use faster model for simple tasks
```

## Community Resources

### Official
- [Claude Code Docs](https://docs.claude.com/en/docs/claude-code/slash-commands)
- [Anthropic Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Official Plugins](https://github.com/anthropics/claude-code/tree/main/plugins)

### Community Collections
- [awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) - 13.3k stars, curated resources
- [Claude Command Suite](https://github.com/qdhenry/Claude-Command-Suite) - 148+ commands, 54 agents
- [Production Commands](https://github.com/wshobson/commands) - 57 production-ready commands
- [Claude Sessions](https://github.com/iannuttall/claude-sessions) - Session tracking commands

## Best Practices

1. **Start Simple** - Begin with basic commands before complex workflows
2. **Use Descriptive Names** - `/fix-issue` not `/fi`
3. **Limit Scope** - Use `allowed-tools` to restrict permissions
4. **Add Context** - Include runtime info with `!`command``
5. **Document Arguments** - Use `argument-hint` for clarity
6. **Version Control** - Commit commands to share with team
7. **Test Thoroughly** - Verify commands work before sharing
8. **Optimize Costs** - Use `model: claude-haiku-4-5` for simple tasks
9. **Provide Feedback** - Commands should report what they did
10. **Follow Conventions** - Match your project's patterns

## Tips for Creating Commands

### Keep Commands Focused
```markdown
✅ Good: /test - Run tests
❌ Bad: /test-build-deploy - Do everything
```

### Use Clear Descriptions
```markdown
✅ Good: description: Create git commit with conventional format
❌ Bad: description: Commit stuff
```

### Provide Usage Examples
```markdown
---
argument-hint: <issue-number>
---

## Examples
/fix-issue 123
/fix-issue 456
```

### Include Error Handling
```markdown
1. Check if tests exist
2. If yes, run tests
3. If no tests found, suggest creating them
4. If tests fail, show errors and suggest fixes
```

## Advanced Patterns

### Multi-Step Workflows
Coordinate multiple operations in sequence with validation between steps.

**Example:** Feature development (plan → implement → test → document → PR)

### Conditional Execution
Check conditions and branch logic based on state.

**Example:** Only push if tests pass

### Multi-Tool Coordination
Combine multiple tools (git, npm, gh) in single command.

**Example:** `/commit-push-pr` uses 6 different git/gh commands

### Cost Optimization
Use appropriate models for task complexity.

**Example:** `model: claude-haiku-4-5` for simple commits (2x faster, 3x cheaper)

## Troubleshooting

### Command Not Found
- Check file is in `.claude/commands/` or `~/.claude/commands/`
- Verify file has `.md` extension
- Check frontmatter syntax is valid YAML

### Permission Denied
- Review `allowed-tools` in frontmatter
- Check global permissions in `settings.json`
- Verify no conflicting `deniedTools`

### Command Doesn't Work
- Test with `/help` to see if command is registered
- Check for YAML syntax errors in frontmatter
- Verify bash commands are properly formatted
- Test tool access separately

### Arguments Not Working
- Use `$ARGUMENTS` for all args, `$1` `$2` for positional
- Check `argument-hint` matches usage
- Quote arguments with spaces: `/command "multi word arg"`

## Metadata

**Source:** Official Anthropic documentation and community repositories
**Last Updated:** 2025-10-31
**Version:** Latest
**Category:** developer-tools

**Research Sources:**
- anthropics/claude-code (official repository)
- hesreallyhim/awesome-claude-code (community curated)
- wshobson/commands (production examples)
- qdhenry/Claude-Command-Suite (comprehensive suite)
- Official Claude Code documentation

## Contributing

Found a useful command pattern? Add it to this documentation:

1. Test the command thoroughly
2. Document with clear examples
3. Include frontmatter and all options
4. Add to appropriate complexity section
5. Update this README if needed

---

**Quick Navigation:**
- [View All Examples](./slash-command-examples.md)
- [Reference Guide](./custom-slash-commands.md)
- [GitHub - awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code)
