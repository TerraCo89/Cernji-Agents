# Claude Skills Documentation

Comprehensive documentation for building, deploying, and managing Claude Agent Skills.

## 📚 Documentation Index

### Core Documentation
1. **[overview.md](overview.md)** - Agent Skills overview and architecture
   - Three-level loading architecture
   - Skill structure requirements
   - Platform availability
   - Pre-built skills (pptx, xlsx, docx, pdf)
   - Security considerations and limitations

2. **[quickstart.md](quickstart.md)** - Get started with Skills API
   - Prerequisites and setup
   - Using pre-built skills (PowerPoint, Excel, Word, PDF)
   - Step-by-step examples with Python
   - File download and handling

3. **[best-practices.md](best-practices.md)** - Skill authoring guidelines
   - Core principles (conciseness, progressive disclosure)
   - Skill structure and naming conventions
   - Workflow patterns and validation
   - Anti-patterns to avoid
   - Effectiveness checklist

### Advanced Documentation
4. **[api-reference.md](api-reference.md)** - Complete API documentation
   - Skills management endpoints
   - Skill versions management
   - Request/response schemas
   - Using skills in Messages API
   - Pre-built skills reference
   - Error responses and rate limits

5. **[cookbook-examples.md](cookbook-examples.md)** - Python code examples
   - Environment setup
   - Creating and managing skills
   - Testing workflows
   - Skill versioning
   - Utility functions
   - Complete workflow examples

6. **[file-structure.md](file-structure.md)** - File organization guide
   - Directory structure patterns
   - YAML frontmatter requirements
   - Progressive disclosure patterns
   - Bundled resources (scripts, references, assets)
   - Validation and packaging
   - Security considerations

7. **[advanced-examples.md](advanced-examples.md)** - Production code examples
   - Document generation (Excel, PDF, Word, PowerPoint)
   - Data processing (PDF manipulation, format conversion)
   - MCP server integration
   - Algorithmic art with p5.js
   - Animation and GIF creation

---

## 🚀 Quick Start

### 1. Basic Skill Structure
```
my-skill/
├── SKILL.md           # Required: Instructions for Claude
├── scripts/           # Optional: Python/JS code
│   └── processor.py
└── references/        # Optional: Documentation
    └── api_docs.md
```

### 2. SKILL.md Template
```markdown
---
name: my-skill
description: Brief description of what this skill does and when to use it.
---

# My Skill

## Overview
[What the skill does]

## Usage
[How to use the skill]

## Examples
[Code examples]
```

### 3. Create a Skill (Python)
```python
from anthropic import Anthropic
from anthropic.lib import files_from_dir

client = Anthropic(
    api_key="YOUR_API_KEY",
    default_headers={"anthropic-beta": "skills-2025-10-02"}
)

skill = client.beta.skills.create(
    display_title="My Custom Skill",
    files=files_from_dir("path/to/skill")
)

print(f"Created skill: {skill.id}")
```

### 4. Use a Skill
```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [{
            "type": "custom",
            "skill_id": skill.id,
            "version": "latest"
        }]
    },
    messages=[{
        "role": "user",
        "content": "Use this skill to process my data"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

---

## 📖 Key Concepts

### Progressive Disclosure
Skills use a three-level loading system:

1. **Metadata** (always loaded) - YAML frontmatter (~100 tokens)
2. **Instructions** (loaded when triggered) - SKILL.md main content (<5k tokens)
3. **Resources** (loaded as needed) - Additional files (unlimited)

### Pre-built Skills (API)
Anthropic provides four ready-to-use skills:

| Skill ID | Description |
|----------|-------------|
| `pptx` | Create and edit PowerPoint presentations |
| `xlsx` | Create spreadsheets with formulas and formatting |
| `docx` | Create and format Word documents |
| `pdf` | Generate formatted PDF documents |

### Platform Availability

| Platform | Pre-built Skills | Custom Skills | Sharing |
|----------|------------------|---------------|---------|
| Claude API | ✅ | ✅ | Workspace-wide |
| Claude Code | ❌ | ✅ | Project/personal |
| Claude.ai | ✅ | ✅ | Individual user |

---

## 🛠️ Development Workflow

### 1. Plan Your Skill
- Define what the skill does
- Identify when it should be used
- Plan required parameters and outputs

### 2. Create Structure
```bash
mkdir -p my-skill/{scripts,references,assets}
touch my-skill/SKILL.md
```

### 3. Write Instructions
- Keep SKILL.md under 500 lines
- Use progressive disclosure for complex docs
- Include concrete examples
- Document expected inputs/outputs

### 4. Test Locally
```bash
python scripts/quick_validate.py my-skill/
```

### 5. Upload to API
```python
skill = client.beta.skills.create(
    display_title="My Skill",
    files=files_from_dir("my-skill/")
)
```

### 6. Test with Claude
```python
response = test_skill(client, skill.id, "Test this skill")
```

### 7. Iterate
- Update skill files
- Create new version
- Test changes
- Deploy updates

---

## ✅ Best Practices Checklist

### Required
- [ ] SKILL.md exists with YAML frontmatter
- [ ] `name` field (max 64 chars, lowercase/hyphens)
- [ ] `description` field (max 1024 chars, non-empty)
- [ ] Description includes what skill does AND when to use it
- [ ] Instructions are clear and concise

### Recommended
- [ ] SKILL.md under 500 lines
- [ ] Complex docs split into references/
- [ ] Executable code in scripts/
- [ ] Templates/assets in assets/
- [ ] Unix-style paths (forward slashes)
- [ ] No sensitive data (API keys, secrets)
- [ ] Clear usage examples
- [ ] Error handling in scripts

### Optional
- [ ] License specified
- [ ] Allowed tools defined
- [ ] Version metadata
- [ ] Comprehensive test cases
- [ ] Performance optimizations

---

## 🔍 Common Use Cases

### Document Generation
- PowerPoint presentations from data
- Excel reports with formulas
- PDF invoices and reports
- Word documents with templates

### Data Processing
- PDF text extraction
- Spreadsheet analysis
- Data format conversion
- Batch processing workflows

### API Integration
- External service connections
- Database queries
- File storage operations
- Third-party tool integration

### Specialized Analysis
- Financial calculations
- Statistical modeling
- Image processing
- Natural language analysis

---

## 📦 Resources

### Official Links
- [Anthropic Skills Repository](https://github.com/anthropics/skills)
- [Anthropic Cookbook](https://github.com/anthropics/anthropic-cookbook/tree/main/skills)
- [Claude API Documentation](https://docs.anthropic.com)

### Example Skills
- Financial Ratio Analyzer
- Corporate Brand Guidelines
- BigQuery Helper
- Document Processor
- Slack GIF Creator

### Tools & Libraries
- **Python**: anthropic, pydantic, pypdf, reportlab, openpyxl
- **JavaScript**: pptxgenjs, docx, @modelcontextprotocol/sdk
- **Validation**: zod (TS), pydantic (Python)

---

## ⚠️ Important Limitations

### Security
- ✅ **DO** use environment variables for secrets
- ✅ **DO** validate all inputs
- ✅ **DO** audit untrusted skills
- ❌ **DON'T** hardcode API keys
- ❌ **DON'T** include sensitive data

### Runtime
- ❌ No network access from skills
- ❌ No runtime package installation
- ❌ No interactive input (like `git rebase -i`)
- ✅ Pre-installed packages only
- ✅ Code execution via tool

### Distribution
- Custom skills don't sync across platforms
- claude.ai skills are individual-only
- API skills are workspace-wide
- Manage separately per surface

---

## 🆘 Troubleshooting

### Skill Not Loading
- Check YAML frontmatter syntax
- Verify name/description requirements
- Ensure SKILL.md exists
- Check file permissions

### Skill Not Triggering
- Improve description with keywords
- Add usage examples
- Include trigger conditions
- Test with explicit skill reference

### Performance Issues
- Reduce SKILL.md size (target <500 lines)
- Split large docs into references
- Optimize script efficiency
- Cache expensive operations

### Version Conflicts
- List all versions: `client.beta.skills.versions.list(skill_id)`
- Specify version: `"version": "1.0.0"` (not "latest")
- Delete old versions if needed
- Track version changes in metadata

---

## 📝 Contributing

Found an issue or want to improve the documentation?

1. Check existing issues/discussions
2. Test your changes thoroughly
3. Follow existing documentation style
4. Include code examples where relevant
5. Update this README if adding new files

---

## 📄 License

This documentation is provided for educational purposes. Check individual code examples for specific licenses.

---

## 🔗 Related Documentation

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)
- [Agent SDK Documentation](https://docs.anthropic.com/en/docs/agents-and-tools)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io)

---

**Last Updated:** 2025-10-23
**Documentation Version:** 1.0
**Claude Model:** claude-sonnet-4-5-20250929
