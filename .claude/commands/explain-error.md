---
description: Analyze and explain errors by researching the codebase (read-only diagnostic mode)
allowed-tools: Read, Grep, Glob, WebSearch, Bash
argument-hint: [error-message-or-paste]
---

# /explain-error - Error Root Cause Analysis

Diagnostic command that identifies the root cause of errors by analyzing the codebase WITHOUT making any code changes.

## Purpose

Provides deep error analysis and root cause identification using only read-only tools. Helps users and agents understand what's wrong and why, with specific file:line references and actionable insights.

## Syntax

```
/explain-error [error-message]
```

If no error message is provided, the command will prompt the user to paste the error.

## Investigation Process

You are now in **READ-ONLY DIAGNOSTIC MODE**. Follow these steps systematically:

### 1. Parse the Error

Extract key information:
- Error type (e.g., ImportError, AttributeError, TypeError, SyntaxError)
- Failing file path and line number from stack trace
- Error message and context
- Involved modules, functions, or classes

### 2. Locate the Problem Area

Use read-only tools to investigate:

**Read files mentioned in stack trace:**
```
Read: <file-path>
```

**Search for function/class names:**
```
Grep: pattern="<function-or-class-name>" output_mode="content"
```

**Find related files:**
```
Glob: pattern="**/<related-file-pattern>"
```

**Check configuration (if dependency-related):**
```
Read: pyproject.toml, package.json, requirements.txt, etc.
```

**Check recent changes:**
```
Bash: git status
Bash: git log --oneline -10
```

### 3. Analyze Root Cause by Error Category

**Import Errors:**
- Check if module exists at expected path
- Verify import statement syntax
- Check for circular imports
- Verify package installation in dependencies

**Type Errors:**
- Examine function signatures and call sites
- Check parameter types and return types
- Look for None/null handling issues
- Check type annotations vs actual usage

**Attribute Errors:**
- Verify class/object definition
- Check if attribute exists in the class
- Look for typos in attribute names
- Check inheritance chain

**Name Errors:**
- Check variable scope and definitions
- Look for typos in variable names
- Verify imports for external functions

**File/Path Errors:**
- Verify file paths exist (use Glob to check)
- Check path construction logic
- Look for OS-specific path issues (Windows vs Unix)

**Syntax Errors:**
- Read the file and locate the syntax issue
- Check for common syntax problems (missing colons, brackets, quotes)
- Verify indentation consistency

### 4. Identify Contributing Factors

Look for:
- Recent changes that might have introduced the error
- Dependencies that might be missing or outdated
- Configuration issues
- Environment-specific problems
- Related errors in other files

### 5. Provide Diagnostic Report

Present your findings in this structured format:

```
## Error Summary
[Brief description of what's failing - one sentence]

## Root Cause
[Specific explanation of why the error occurs with technical details]

## Evidence
[Relevant code snippets with file:line references for easy navigation]

Example:
```python
# apps/resume-agent/resume_agent.py:42
from utils.parser import parse_resume  # ← Module not found
```

## Contributing Factors
[Related issues, recent changes, environmental factors, missing dependencies]

## Recommended Investigation Steps
[Specific actions to verify the diagnosis]

1. Check if X exists
2. Verify Y configuration
3. Test Z behavior

## Potential Fixes (Read-Only Suggestions)
[Describe what changes would fix it, but DO NOT make them]

1. Solution A: [Description]
   - Change file X
   - Update line Y to Z

2. Solution B (alternative): [Description]
   - Different approach if Solution A doesn't apply
```

## Constraints

**STRICT READ-ONLY MODE:**

✅ **Allowed Tools:**
- `Read` - Read files to examine code
- `Grep` - Search for patterns in code
- `Glob` - Find files matching patterns
- `WebSearch` - Search for error messages or documentation
- `Bash(git status)` - Check recent changes
- `Bash(git log)` - View recent commits

❌ **Forbidden Actions:**
- **DO NOT** use `Edit`, `Write`, or `NotebookEdit`
- **DO NOT** create or modify any files
- **DO NOT** run code to fix issues (Bash for execution)
- **DO NOT** install packages or modify dependencies
- **DO NOT** use Task tool to delegate fixes

If you need to verify something with code execution, **describe** what should be tested but don't run it.

## Output Style

**Be specific and actionable:**
- Use `file:line` references for easy navigation (e.g., `src/main.py:42`)
- Quote relevant code sections showing the problem
- Provide context about how the code should work
- Focus on actionable insights
- If multiple potential causes exist, list them in **priority order** (most likely first)

**Example reference format:**
```
The error occurs in `apps/resume-agent/resume_agent.py:156` where...
```

## Examples

### Example 1: Import Error

**User input:**
```
/explain-error ImportError: cannot import name 'JobAnalyzer' from 'agents.analyzers'
```

**Investigation:**
1. Parse error: ImportError for JobAnalyzer from agents.analyzers
2. Read agents/analyzers.py (or check if file exists)
3. Grep for "class JobAnalyzer" to find actual location
4. Check if it's a typo or moved file
5. Report findings with file:line references

### Example 2: Attribute Error with Stack Trace

**User input:**
```
/explain-error

AttributeError: 'NoneType' object has no attribute 'get'
  File "src/processor.py", line 42, in process_data
    result = data.get('key')
```

**Investigation:**
1. Read src/processor.py:42 and surrounding context
2. Identify where `data` is assigned (trace back)
3. Find why data might be None
4. Check function calls that pass data
5. Report root cause with evidence

### Example 3: No Error Provided

**User input:**
```
/explain-error
```

**Response:**
```
Please provide the error message, stack trace, or error description.

You can paste:
- Full stack trace
- Error message with file:line reference
- Description of unexpected behavior

Example:
/explain-error TypeError: expected str, got int at line 42
```

## Error Handling

**Missing error message:**
- Prompt user to provide error details
- Give examples of useful error formats

**Ambiguous error:**
- Ask clarifying questions
- Request full stack trace if only partial info given

**Cannot locate issue:**
- Report what was checked
- List possible investigation paths
- Suggest additional context needed (e.g., "Need to see the full stack trace")

**Multiple potential causes:**
- List all possibilities in priority order
- Explain why each might apply
- Suggest how to narrow down

## Related Commands

- `/research` - Deep parallel research on programming topics (can help with error solutions)
- `/fetch-docs` - Fetch library documentation (useful for API errors)

## Tips for Users

**Provide better context by including:**
- Full stack trace (not just last line)
- Steps that triggered the error
- Recent changes you made
- Environment info (Python version, OS, etc.)

**After diagnosis:**
- Review the suggested fixes
- Test the recommended investigation steps
- Use other commands to implement fixes if needed

---

**Remember: This command only diagnoses. It does not fix. Use other tools or commands to implement the suggested fixes.**
