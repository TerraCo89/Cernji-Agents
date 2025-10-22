# Claude Skills File Structure & Organization

Complete guide to organizing and structuring custom Claude Skills.

## Table of Contents
- [Basic Structure](#basic-structure)
- [YAML Frontmatter](#yaml-frontmatter)
- [Directory Organization](#directory-organization)
- [Bundled Resources](#bundled-resources)
- [Progressive Disclosure](#progressive-disclosure)
- [Examples](#examples)

---

## Basic Structure

### Minimal Skill

The most basic structure required for a folder to be recognized as a skill:

```
my-skill/
  └── SKILL.md
```

### Complete Structure

A fully-featured skill with all optional components:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation loaded on-demand
    └── assets/           - Files used in output (templates, icons, fonts)
```

---

## YAML Frontmatter

### Required Fields

Every SKILL.md file must start with YAML frontmatter containing:

```yaml
---
name: "my-skill"
description: "A brief description of what this skill does and when Claude should use it."
---
```

**Field Requirements:**
- `name`: Max 64 characters, lowercase letters/numbers/hyphens only
- `description`: Max 1024 characters, non-empty

### Optional Fields

```yaml
---
name: "my-skill"
description: "A brief description of what this skill does and when Claude should use it."
license: "MIT"
allowed-tools: ["code-interpreter"]
metadata:
  version: "1.0"
  author: "Your Name"
  tags: ["finance", "analysis"]
---
```

### Best Practices for Descriptions

**Good Description** (third person, capability + trigger):
```yaml
description: "Extracts text and tables from PDF files, fills forms. Use when working with PDFs or document extraction."
```

**Bad Description** (vague):
```yaml
description: "Helps with documents"
```

---

## Directory Organization

### Scripts Directory

Store executable code that Claude can run:

```
skill-name/
└── scripts/
    ├── processor.py       - Main processing logic
    ├── validator.py       - Validation functions
    ├── utils.py           - Utility functions
    └── requirements.txt   - Python dependencies
```

**Example Script:**
```python
# scripts/rotate_pdf.py
import PyPDF2

def rotate_pdf(input_path, output_path, rotation_angle):
    with open(input_path, 'rb') as infile, open(output_path, 'wb') as outfile:
        reader = PyPDF2.PdfReader(infile)
        writer = PyPDF2.PdfWriter()

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page.rotate(rotation_angle)
            writer.add_page(page)

        writer.write(outfile)

if __name__ == '__main__':
    input_file = 'input.pdf'
    output_file = 'output_rotated.pdf'
    angle = 90
    rotate_pdf(input_file, output_file, angle)
    print(f'PDF rotated by {angle} degrees')
```

### References Directory

Documentation and reference materials loaded on-demand:

```
skill-name/
└── references/
    ├── api_reference.md    - API documentation
    ├── examples.md         - Usage examples
    ├── schemas/
    │   ├── schema.md       - Data schemas
    │   └── validation.md   - Validation rules
    └── templates/
        ├── template1.json
        └── template2.yaml
```

**Progressive Disclosure Pattern:**
```markdown
# SKILL.md

## Quick Start
[Core instructions here]

## Advanced Features
See [references/api_reference.md](references/api_reference.md) for complete API documentation.
See [references/examples.md](references/examples.md) for detailed examples.
```

### Assets Directory

Files used in skill output (templates, images, etc.):

```
skill-name/
└── assets/
    ├── templates/
    │   ├── report_template.xlsx
    │   ├── invoice_template.pdf
    │   └── presentation_template.pptx
    ├── images/
    │   ├── logo.png
    │   └── watermark.png
    └── fonts/
        └── custom_font.ttf
```

---

## Progressive Disclosure

### Keep SKILL.md Concise

**Guideline:** Keep SKILL.md under 500 lines for optimal performance.

### Pattern 1: High-Level Guide with References

```markdown
# PDF Processing

## Quick Start
[Core instructions - ~200 lines]

## Advanced Features
- See [FORMS.md](FORMS.md) for form filling
- See [REFERENCE.md](REFERENCE.md) for complete API
- See [EXAMPLES.md](EXAMPLES.md) for code samples
```

### Pattern 2: Domain-Specific Organization

Organize reference files by domain:

```
skill-name/
└── references/
    ├── finance.md      - Finance-specific features
    ├── sales.md        - Sales-specific features
    └── product.md      - Product-specific features
```

This allows Claude to load only relevant context.

### Pattern 3: Conditional Details

```markdown
# Basic Usage
[Simple instructions]

## Advanced: Complex Workflows
For complex multi-step workflows, see [workflows/advanced.md](workflows/advanced.md)

## Advanced: Custom Integrations
For API integration patterns, see [integrations/api.md](integrations/api.md)
```

### Critical Rules

- ✅ Keep references one level deep from SKILL.md
- ✅ Structure long files (100+ lines) with table of contents
- ✅ Use forward slashes in paths (`reference/guide.md`)
- ❌ Never use backslashes (`reference\guide.md`)
- ❌ Avoid deeply nested references

---

## Complete Skill Example

### BigQuery Helper Skill

```
bigquery-helper/
├── SKILL.md
├── scripts/
│   ├── run_query.py
│   ├── export_results.py
│   └── requirements.txt
├── references/
│   ├── schema.md
│   ├── best_practices.md
│   └── examples.md
└── assets/
    └── templates/
        └── report_template.xlsx
```

**SKILL.md:**
```markdown
---
name: bigquery-helper
description: Execute BigQuery queries and export results. Use when working with BigQuery or data analysis.
license: MIT
allowed-tools: ["code-interpreter"]
metadata:
  version: "1.0"
---

# BigQuery Helper

## Overview
This skill helps you interact with Google BigQuery for data analysis and reporting.

## Quick Start

### Running Queries
Use `scripts/run_query.py` to execute SQL queries:

\`\`\`bash
python scripts/run_query.py "SELECT * FROM users LIMIT 10"
\`\`\`

### Exporting Results
Export query results to various formats:

\`\`\`bash
python scripts/export_results.py --format xlsx --output report.xlsx
\`\`\`

## Schema Reference
See [references/schema.md](references/schema.md) for complete table schemas.

## Examples
See [references/examples.md](references/examples.md) for common query patterns.

## Best Practices
See [references/best_practices.md](references/best_practices.md) for optimization tips.
```

**scripts/run_query.py:**
```python
#!/usr/bin/env python3
from google.cloud import bigquery
import sys

client = bigquery.Client()
query = sys.argv[1]
df = client.query(query).to_dataframe()
print(df.to_string())
```

**references/schema.md:**
```markdown
# BigQuery Schema Reference

## users table
- user_id: INT64 (primary key)
- email: STRING
- created_at: TIMESTAMP
- last_login: TIMESTAMP

## events table
- event_id: INT64 (primary key)
- user_id: INT64 (foreign key → users)
- event_type: STRING
- timestamp: TIMESTAMP
- metadata: JSON

## transactions table
- transaction_id: INT64 (primary key)
- user_id: INT64 (foreign key → users)
- amount: NUMERIC
- currency: STRING
- status: STRING
- created_at: TIMESTAMP
```

---

## Initialization Scripts

### Using init_skill.py

Create a new skill from template:

```bash
# Create skill structure
python scripts/init_skill.py my-new-skill --path skills/

# Creates:
# skills/my-new-skill/
#   ├── SKILL.md (with TODO placeholders)
#   ├── scripts/ (example script)
#   ├── references/ (example reference)
#   └── assets/ (example asset)
```

### Custom Skill Template

```bash
# Create directory structure
mkdir -p my-skill/{scripts,references,assets}

# Create SKILL.md
cat > my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: TODO: Add description
---

# My Skill

TODO: Add instructions

## Usage
TODO: Add usage examples

## References
- [Reference 1](references/reference1.md)
EOF

# Create placeholder files
touch my-skill/scripts/main.py
touch my-skill/references/reference1.md
touch my-skill/assets/.gitkeep
```

---

## Validation and Packaging

### Validation Script

```bash
# Validate skill structure and requirements
python scripts/quick_validate.py path/to/my-skill
```

### Packaging Script

```bash
# Package into distributable zip (includes validation)
python scripts/package_skill.py path/to/my-skill

# Output: my-skill.zip

# Specify custom output directory
python scripts/package_skill.py path/to/my-skill ./dist

# Output: dist/my-skill.zip
```

---

## File Path Best Practices

### ✅ Correct Paths (Unix-style)

```markdown
[Reference](references/api.md)
[Example](scripts/examples/example1.py)
[Template](assets/templates/report.xlsx)
```

### ❌ Incorrect Paths (Windows-style)

```markdown
[Reference](references\api.md)           # WRONG
[Example](scripts\examples\example1.py)  # WRONG
[Template](assets\templates\report.xlsx) # WRONG
```

---

## Token Budget Guidelines

| Component | Recommended Size | Notes |
|-----------|-----------------|-------|
| SKILL.md body | < 500 lines | Core instructions only |
| Reference files | < 200 lines each | Split large docs |
| Example files | < 100 lines each | Keep focused |
| Total skill | < 2000 lines | All files combined |

---

## Security Considerations

### Sensitive Data

**Never include:**
- API keys or secrets
- Database credentials
- Personal information
- Proprietary algorithms (unless intended)

**Instead, use:**
- Environment variables
- Configuration file templates
- Placeholder values
- Clear documentation on required setup

### Example: Safe Configuration

```python
# scripts/config.py
import os

# ✅ Good - uses environment variables
API_KEY = os.getenv('BIGQUERY_API_KEY')
PROJECT_ID = os.getenv('GCP_PROJECT_ID')

# ❌ Bad - hardcoded secrets
# API_KEY = "abc123xyz"
# PROJECT_ID = "my-project"
```

---

## Naming Conventions

### Skill Names

Use gerund form (verb + -ing):
- ✅ "Processing PDFs"
- ✅ "Analyzing spreadsheets"
- ✅ "Managing databases"
- ❌ "Helper"
- ❌ "Utils"
- ❌ "Tool"

### File Names

Use lowercase with hyphens or underscores:
- ✅ `api-reference.md`
- ✅ `data_processor.py`
- ✅ `user-guide.md`
- ❌ `APIReference.md`
- ❌ `Data Processor.py`
- ❌ `User Guide.md`

---

## Summary Checklist

**Required:**
- [ ] SKILL.md file exists
- [ ] YAML frontmatter with name and description
- [ ] Name is 64 characters or less
- [ ] Description is 1024 characters or less
- [ ] Description includes what the skill does and when to use it

**Recommended:**
- [ ] SKILL.md under 500 lines
- [ ] Complex instructions split into references/
- [ ] Scripts in scripts/ directory
- [ ] Assets in assets/ directory
- [ ] Unix-style forward slashes in all paths
- [ ] References are one level deep
- [ ] No sensitive data in files
- [ ] Clear usage examples provided

**Optional:**
- [ ] License specified
- [ ] Allowed tools defined
- [ ] Metadata included
- [ ] Version number tracked
- [ ] README or documentation
