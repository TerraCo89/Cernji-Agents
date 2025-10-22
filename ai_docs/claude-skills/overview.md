# Agent Skills Documentation Summary

## Overview

Agent Skills are modular capabilities that extend Claude's functionality by packaging instructions, metadata, and optional resources. They enable Claude to automatically use domain-specific expertise when relevant to user requests.

## Key Benefits

- **Specialize Claude**: Tailor capabilities for specific domains
- **Reduce repetition**: Create once, use across multiple conversations
- **Compose capabilities**: Combine Skills to build complex workflows

## Three-Level Loading Architecture

Skills implement progressive disclosure with three content types:

**Level 1: Metadata (Always Loaded)**
YAML frontmatter provides discovery information (~100 tokens per Skill):
```yaml
---
name: pdf-processing
description: Extract text and tables from PDFs, fill forms, merge documents
---
```

**Level 2: Instructions (Loaded When Triggered)**
Main SKILL.md file contains procedural knowledge and workflows (under 5k tokens). Claude reads this only when the Skill matches user requests.

**Level 3: Resources (Loaded As Needed)**
Additional files like FORMS.md, scripts, templates, and reference materials are accessed only when explicitly needed, consuming effectively unlimited context.

## Skill Structure Requirements

Every Skill requires a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: your-skill-name
description: Brief description and usage triggers
---

# Your Skill Name

## Instructions
[Step-by-step guidance]

## Examples
[Concrete usage examples]
```

**Field Requirements:**
- `name`: Max 64 characters, lowercase letters/numbers/hyphens only
- `description`: Non-empty, max 1024 characters

## Where Skills Work

| Platform | Pre-built Skills | Custom Skills | Sharing Model |
|----------|------------------|---------------|---------------|
| Claude API | Yes (pptx, xlsx, docx, pdf) | Yes | Workspace-wide |
| Claude Code | No | Yes | Project/personal |
| Claude.ai | Yes | Yes | Individual user |

## Available Pre-built Skills

- PowerPoint (pptx): Create and edit presentations
- Excel (xlsx): Create spreadsheets and generate reports
- Word (docx): Create and format documents
- PDF (pdf): Generate formatted PDF documents

## Important Limitations

**No Network Access**: Skills cannot make external API calls or access the internet.

**No Runtime Installation**: Only pre-installed packages available; cannot install new packages during execution.

**Cross-Surface Gaps**: Custom Skills don't sync between surfaces; manage separately for API and claude.ai.

**Sharing Constraints**: claude.ai Skills are individual-only (no org-wide distribution); API Skills are workspace-wide.

## Security Considerations

"We strongly recommend using Skills only from trusted sources: those you created yourself or obtained from Anthropic." Audit thoroughly before using untrusted Skills, as they can direct Claude to execute code in unintended ways. Malicious Skills pose risks including data exfiltration and unauthorized system access.

## Getting Started

- **Pre-built Skills quickstart**: See the tutorial for PowerPoint, Excel, Word, and PDF Skills on the API
- **Custom Skills**: Reference the [Skills Cookbook](https://github.com/anthropics/claude-cookbooks/tree/main/skills) for complete examples
- **Best practices**: Consult authoring guidelines for effective Skill design
