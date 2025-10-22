# Get Started with Agent Skills in the API

## Overview

Agent Skills extend Claude's capabilities with specialized expertise for document creation and data processing tasks. Anthropic provides four pre-built Skills: PowerPoint (pptx), Excel (xlsx), Word (docx), and PDF.

## Prerequisites

- Anthropic API key
- Python 3.7+ or curl
- Basic API request familiarity

## Available Skills

The API provides these pre-built Agent Skills:

- **PowerPoint (pptx)**: Create and edit presentations
- **Excel (xlsx)**: Create and analyze spreadsheets
- **Word (docx)**: Create and edit documents
- **PDF (pdf)**: Generate PDF documents

## Step 1: List Available Skills

Retrieve all Anthropic-managed Skills using the Skills API:

```python
import anthropic

client = anthropic.Anthropic()

skills = client.beta.skills.list(
    source="anthropic",
    betas=["skills-2025-10-02"]
)

for skill in skills.data:
    print(f"{skill.id}: {skill.display_title}")
```

This demonstrates "progressive disclosure"—Claude discovers Skills without loading complete instructions initially.

## Step 2: Create a Presentation

Use the PowerPoint Skill to generate content:

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [{
            "type": "anthropic",
            "skill_id": "pptx",
            "version": "latest"
        }]
    },
    messages=[{
        "role": "user",
        "content": "Create a presentation about renewable energy with 5 slides"
    }],
    tools=[{
        "type": "code_execution_20250825",
        "name": "code_execution"
    }]
)
```

Key parameters:
- `container.skills`: Specifies which Skills are available
- `type: "anthropic"`: Indicates Anthropic-managed Skills
- `skill_id`: Identifies the specific Skill
- `tools`: Enables code execution (required for Skills)

## Step 3: Download the Created File

Extract and download generated files:

```python
file_id = None
for block in response.content:
    if block.type == 'tool_use' and block.name == 'code_execution':
        for result_block in block.content:
            if hasattr(result_block, 'file_id'):
                file_id = result_block.file_id
                break

if file_id:
    file_content = client.beta.files.download(
        file_id=file_id,
        betas=["files-api-2025-04-14"]
    )

    with open("renewable_energy.pptx", "wb") as f:
        file_content.write_to_file(f.name)
```

## Additional Examples

### Create a Spreadsheet

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [{
            "type": "anthropic",
            "skill_id": "xlsx",
            "version": "latest"
        }]
    },
    messages=[{
        "role": "user",
        "content": "Create a quarterly sales tracking spreadsheet with sample data"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

### Create a Word Document

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [{
            "type": "anthropic",
            "skill_id": "docx",
            "version": "latest"
        }]
    },
    messages=[{
        "role": "user",
        "content": "Write a 2-page report on the benefits of renewable energy"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

### Generate a PDF

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [{
            "type": "anthropic",
            "skill_id": "pdf",
            "version": "latest"
        }]
    },
    messages=[{
        "role": "user",
        "content": "Generate a PDF invoice template"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

## Next Steps

- Explore the Agent Skills Cookbook for custom Skill creation
- Review best practices for effective Skill implementation
- Integrate Skills into Claude Code workflows
- Create domain-specific custom Skills
