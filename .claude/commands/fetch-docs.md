---
description: Fetch library documentation from Context7 and save it to ai_docs/ with proper categorization
allowed-tools: mcp__context7__resolve-library-id, mcp__context7__get-library-docs, Write, Bash
---

# Fetch Library Documentation

## Purpose
Fetch library documentation from Context7 and organize it in `ai_docs/` with category-based structure and metadata tracking.

## Syntax
```
/fetch-docs <library-name> [options]

Options:
  --topic=<topic>           # Fetch specific topic documentation
  --version=<version>       # Fetch specific version
  --tokens=<count>          # Override default token count (default: 5000)
  --refresh                 # Refresh existing documentation

Examples:
  /fetch-docs langgraph
  /fetch-docs nextjs --topic=routing
  /fetch-docs react --version=18
  /fetch-docs playwright --topic=testing --tokens=8000
  /fetch-docs nextjs --refresh
```

## Process

**IMPORTANT:** Invoke the `doc-fetcher` skill to handle this request. The skill provides comprehensive documentation fetching with proper categorization, metadata tracking, and error handling.

```
Skill: doc-fetcher
```

After invoking the skill, the skill will:

1. **Parse arguments** from the command
   - Library name: required first argument
   - Options: parse from --flag=value format

2. **Execute fetch workflow** via doc-fetcher skill:
   - Resolve library ID using Context7
   - Determine category (frameworks/, ai-ml/, databases/, etc.)
   - Fetch documentation with specified topic/version/tokens
   - Create directory structure in ai_docs/
   - Save markdown files and metadata
   - Report results to user

## Expected Arguments

Parse the following from the user's command:

- `library_name` (required): First positional argument after /fetch-docs
- `--topic` (optional): Specific topic to fetch (e.g., "routing", "hooks")
- `--version` (optional): Specific version to fetch (e.g., "v14", "18")
- `--tokens` (optional): Token count override (default: 5000)
- `--refresh` (optional): Boolean flag to refresh existing docs

## Examples

### Example 1: Simple Fetch
```
User: /fetch-docs langgraph
Result: Invokes doc-fetcher skill with library_name="langgraph"
Output: ai_docs/ai-ml/langgraph/README.md
```

### Example 2: Topic-Specific
```
User: /fetch-docs nextjs --topic=routing
Result: Invokes doc-fetcher with library_name="nextjs", topic="routing"
Output: ai_docs/frameworks/nextjs/routing.md
```

### Example 3: Version Specific
```
User: /fetch-docs react --version=18
Result: Invokes doc-fetcher with library_name="react", version="18"
Output: ai_docs/frameworks/react/v18/README.md
```

### Example 4: Custom Tokens
```
User: /fetch-docs playwright --topic=testing --tokens=8000
Result: Invokes doc-fetcher with library_name="playwright", topic="testing", tokens=8000
Output: ai_docs/testing/playwright/testing.md
```

### Example 5: Refresh Existing
```
User: /fetch-docs nextjs --refresh
Result: Invokes doc-fetcher with library_name="nextjs", refresh=true
Output: Refreshes ai_docs/frameworks/nextjs/README.md
```

## Error Handling

If arguments are malformed or missing:
- Missing library name: "Please provide a library name: /fetch-docs <library-name>"
- Invalid option format: "Invalid option format. Use --option=value"
- Unknown option: "Unknown option: --xyz. Valid options: --topic, --version, --tokens, --refresh"

For all other errors, the doc-fetcher skill will handle them appropriately.
