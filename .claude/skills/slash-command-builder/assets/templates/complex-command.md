---
description: [Brief description of what this command does - under 100 characters]
allowed-tools: [List of tools: Task, Read, Write, Bash, etc.]
argument-hint: [input-description]
---

# [Command Name]

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/[command-name]` in the triggering message **is** the input. Assume you always have it available in this conversation even if `$ARGUMENTS` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that input, do this:

1. **[Step 1 Name]** (e.g., "Parse and Validate Input")
   - [Substep description]
   - [What to extract/identify]
   - [Validation criteria]

2. **[Step 2 Name]** (e.g., "Execute Script/Tool")
   - [Command to run or tool to use]
   - [Expected output format]
   - [How to parse output]
   - [Error handling for this step]

3. **[Step 3 Name]** (e.g., "Process Results")
   - [What to do with output from step 2]
   - [Transformations needed]
   - [Data structures to build]

4. **[Step 4 Name]** (e.g., "Validate Output")
   - [Validation checks to perform]
   - [Success criteria]
   - [What to do if validation fails]

5. **[Step 5 Name]** (e.g., "Generate Final Output")
   - [How to format results]
   - [What to report to user]
   - [Next steps or recommendations]

## Execution Flow

### Phase 1: Input Processing

1. **Parse user input from $ARGUMENTS**
   - If empty: ERROR "[Provide error message]"
   - Extract: [What to extract from input]
   - Validate: [Validation rules]

2. **[Additional parsing steps if needed]**
   - [Step description]
   - [Expected output]

### Phase 2: Execution

1. **[Main execution step]**
   - Tool/Command: `[command or tool to use]`
   - Input: [What to pass to tool]
   - Expected output: [Format description]

2. **Parse execution output**
   - Extract: [What to extract]
   - Validate: [Checks to perform]
   - Handle errors: [Error cases]

### Phase 3: Validation

**[Validation Stage Name]**

After [execution phase], validate the output:

1. **Check [condition 1]**
   - Criteria: [What to check]
   - Pass: [What happens if valid]
   - Fail: [What to do if invalid]

2. **Verify [condition 2]**
   - Criteria: [What to check]
   - Pass: [What happens if valid]
   - Fail: [What to do if invalid]

3. **Ensure [condition 3]**
   - Criteria: [What to check]
   - Pass: [What happens if valid]
   - Fail: [What to do if invalid]

**If validation fails:**
- [Error handling step 1]
- [Error handling step 2]
- [Retry logic if applicable]
- [User notification format]

### Phase 4: Finalization

1. **[Generate output]**
   - Format: [Output structure]
   - Include: [What to include]
   - Omit: [What to omit]

2. **[Report to user]**
   - Success message format
   - Next steps
   - Related commands or actions

## Output Format

```
[Define the structured output format]

Example:

[SECTION 1 NAME]
================

Item 1: [Details]
Item 2: [Details]
Item 3: [Details]

[SECTION 2 NAME]
----------------
[Details]

[SECTION 3 NAME]
----------------
[Summary or next steps]
```

## Error Handling

### Scenario 1: [Error Type - e.g., "Invalid Input"]

**Symptoms:**
- [What indicates this error]

**Error Message:**
```
Error: [Specific error message]

Cause: [What caused this error]

Solution:
1. [Fix step 1]
2. [Fix step 2]

Example: /[command-name] [corrected usage]
```

### Scenario 2: [Error Type - e.g., "Script Execution Failed"]

**Symptoms:**
- [What indicates this error]

**Error Message:**
```
Error: [Specific error message]

Possible causes:
1. [Cause 1]
2. [Cause 2]
3. [Cause 3]

Solutions:
1. [Solution for cause 1]
2. [Solution for cause 2]
3. [Solution for cause 3]

Retry: /[command-name] [arguments]
```

### Scenario 3: [Error Type - e.g., "Validation Failed"]

**Symptoms:**
- [What indicates this error]

**Error Message:**
```
Error: [Specific error message]

Validation failed on:
- [Check 1 that failed]
- [Check 2 that failed]

Next steps:
1. [What to fix]
2. [How to fix it]
3. [How to verify fix]

Help: [Link to documentation or related commands]
```

### Scenario 4: [Error Type - e.g., "Partial Success"]

**Symptoms:**
- [What indicates this situation]

**Message:**
```
Warning: Partial success

Completed:
✓ [Step 1]
✓ [Step 2]

Failed:
✗ [Step 3] - [Reason]

You can:
1. [Option 1 to proceed]
2. [Option 2 to retry]
3. [Option 3 to fix and rerun]
```

## General Guidelines

### [Guideline Category 1 - e.g., "Input Requirements"]
- [Guideline 1]
- [Guideline 2]
- [Guideline 3]

### [Guideline Category 2 - e.g., "Performance Considerations"]
- [Guideline 1]
- [Guideline 2]
- [Guideline 3]

### [Guideline Category 3 - e.g., "Best Practices"]
- [Guideline 1]
- [Guideline 2]
- [Guideline 3]

## Examples

### Example 1: [Scenario Name - e.g., "Basic Usage"]

**Input:**
```
/[command-name] [example input]
```

**Process:**
1. Parse input: `[example input]`
2. Execute: [what gets executed]
3. Validate: [what gets validated]
4. Output: [what gets returned]

**Output:**
```
[Actual output example]
```

### Example 2: [Scenario Name - e.g., "With Options"]

**Input:**
```
/[command-name] [example input] --option=value
```

**Process:**
1. Parse input and option
2. Execute with custom configuration
3. Validate results
4. Output enhanced results

**Output:**
```
[Actual output example showing option effect]
```

### Example 3: [Scenario Name - e.g., "Error Case"]

**Input:**
```
/[command-name] [invalid input]
```

**Process:**
1. Parse input
2. Detect invalid format
3. Return error with guidance

**Output:**
```
Error: [Error message]
[Guidance on fix]
```

## Integration

This command works with:

- **[Related Command 1]**: [How they integrate]
- **[Related Command 2]**: [How they integrate]
- **[Tool/System]**: [How it integrates]

## Notes

- **Idempotency**: [Is this command safe to run multiple times?]
- **State**: [Does this command maintain state? Where?]
- **Caching**: [What gets cached? How long?]
- **Performance**: [How long does this typically take?]
- **Prerequisites**: [What needs to exist before running?]
