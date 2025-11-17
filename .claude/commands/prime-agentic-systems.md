# Build Simple, Powerful Agentic Systems

You are primed to build simple, yet powerful AI agent systems using progressive disclosure and self-contained scripts.

## Core Philosophy

**Context Preservation > Feature Complexity**

The most powerful agentic systems are often the simplest. Rather than building complex MCP servers or frameworks, focus on:

1. **Progressive Disclosure** - Only load code when needed (~200-300 lines per script)
2. **Self-Contained Scripts** - Each script includes everything it needs (embedded HTTP clients, minimal dependencies)
3. **Zero Context Loss** - Agents maintain full conversational context between operations
4. **Git-Shareable** - Simple Python/TypeScript files that teams can share via version control

## The 4 Approaches (Context Window → Feature Set Trade-off)

Reference: `ai_docs/beyond-mcp/` for complete examples

### 1. MCP Server
**When:** Building for multiple LLM clients, need standardized protocol, context loss acceptable

```
Claude → MCP Protocol → MCP Server → subprocess → CLI → API
```

- ✅ Standardized integration, auto-discovery, clean abstractions
- ❌ **Instant context loss on every tool call**, wrapper overhead
- **Context Consumption:** HIGH

### 2. CLI
**When:** Need both human CLI and agent access, want single source of truth

```
Claude → subprocess → CLI commands → Direct HTTP → API
```

- ✅ Dual output modes (human/JSON), smart caching, direct control
- ❌ Subprocess overhead, full context load per call
- **Context Consumption:** MEDIUM

### 3. File System Scripts
**When:** Context preservation critical, maximum portability needed

```
Claude → Read tool → Individual script → Embedded HTTP client → API
```

- ✅ **Progressive disclosure**, complete isolation, zero dependencies between scripts
- ⚠️ Code duplication (acceptable trade-off), no shared state
- **Context Consumption:** LOW (incremental)

### 4. Skills (Claude Code)
**When:** Team collaboration via git, want autonomous discovery

```
Claude (detects trigger) → Loads SKILL.md → Runs scripts → API
```

- ✅ Model-invoked, progressive disclosure, team sharing via git
- ⚠️ Claude Code specific, requires skill system understanding
- **Context Consumption:** LOW (incremental)

## Implementation Pattern

### Self-Contained Script Template

Each script (~200-300 lines) should include:

```python
#!/usr/bin/env python3
# /// script
# dependencies = ["httpx", "click"]
# ///

"""
Brief description of what this script does.
Completely self-contained with embedded HTTP client.

Usage:
    uv run script_name.py
    uv run script_name.py --json
"""

import json
import sys
from typing import Dict, Any

import click
import httpx

# Configuration
API_BASE_URL = "https://api.example.com/v1"
API_TIMEOUT = 30.0
USER_AGENT = "Agent-Script/1.0"

class APIClient:
    """Minimal HTTP client - just what we need for this operation"""

    def __init__(self):
        self.client = httpx.Client(
            base_url=API_BASE_URL,
            timeout=API_TIMEOUT,
            headers={"User-Agent": USER_AGENT}
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def get_resource(self) -> Dict[str, Any]:
        """Fetch resource from API"""
        try:
            response = self.client.get("/resource")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise Exception(f"Network error: {str(e)}")

def format_output(data: Dict[str, Any]) -> str:
    """Format data for human-readable output"""
    # Your formatting logic here
    return str(data)

@click.command()
@click.option('--json', 'output_json', is_flag=True,
              help='Output as JSON instead of human-readable format')
def main(output_json: bool):
    """
    Script description.

    No authentication required for public APIs.
    """
    try:
        with APIClient() as client:
            data = client.get_resource()

        if output_json:
            click.echo(json.dumps(data, indent=2))
        else:
            click.echo(format_output(data))

        sys.exit(0)

    except Exception as e:
        if output_json:
            click.echo(json.dumps({"error": str(e)}, indent=2))
        else:
            click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Skill Structure (for Claude Code)

```
.claude/skills/your-skill/
├── SKILL.md              # Concise description & instructions
└── scripts/              # Self-contained scripts
    ├── operation1.py
    ├── operation2.py
    └── operation3.py
```

**SKILL.md template:**

```markdown
---
name: your-skill-name
description: Brief description triggering keywords like "specific domain", "API name", "use case". Use when user asks about X, Y, or Z.
---

# Your Skill Name

Standalone, self-contained scripts for [purpose].
Each script is independently executable with zero dependencies between scripts.

## Instructions

- **Default to `--json` flag** for all commands when processing data
- **IMPORTANT**: **Don't read scripts unless absolutely needed** - instead, use `<script.py> --help` first, then call with `uv run <script.py> <options>`
- All scripts work from any directory (use absolute paths internally)

## Progressive Disclosure

Each script contains ~200-300 lines with complete functionality.
Only load the script you need - no unnecessary context.

## Available Scripts

### `scripts/operation1.py`
**When to use:** [Specific use case]

### `scripts/operation2.py`
**When to use:** [Specific use case]

## Architecture

- **Self-Contained:** Each script includes all necessary code
- **No External Dependencies:** HTTP client embedded in each script
- **Progressive Discovery:** Only see what you need
- **Incrementally Adoptable:** Use one script or many

## Quick Start

All scripts support `--help` and `--json`:

```bash
uv run scripts/[script].py --help
uv run scripts/[script].py --json
```
```

## Decision Framework

Choose your approach based on these priorities:

| Priority                  | Recommended Approach      |
|---------------------------|---------------------------|
| Context preservation      | Scripts or Skills         |
| Multi-client support      | MCP Server                |
| Team collaboration (git)  | Skills                    |
| Human + Agent access      | CLI                       |
| Maximum portability       | Scripts                   |
| Autonomous discovery      | Skills or MCP             |
| Customization/control     | CLI, Scripts, or Skills   |
| Minimal engineering       | MCP (external) or Skills  |

## Key Principles

1. **Start Simple** - One script doing one thing well
2. **Embed Dependencies** - Include HTTP client in each script (acceptable duplication)
3. **Support --help and --json** - Agent-friendly and human-friendly
4. **Use absolute paths** - `Path(__file__).resolve()` for portability
5. **Progressive disclosure** - Load only what you need, when you need it
6. **Git as distribution** - Share via version control, not package managers

## Reference Implementation

See complete working examples in `ai_docs/beyond-mcp/`:
- `apps/1_mcp_server/` - MCP Server wrapping CLI
- `apps/2_cli/` - Direct CLI with HTTP client
- `apps/3_file_system_scripts/` - 10 standalone scripts
- `apps/4_skill/` - Claude Code skill with progressive disclosure

## The IndyDevDan Approach

**For existing external tools:**
- 80% Just use MCP servers (don't overthink it)
- 15% Use CLI if you need control/customization
- 5% Scripts or Skills for serious context preservation

**For new tools you're building:**
- 80% Start with CLI + prime prompt (works for you, team, and agents)
- 10% Wrap in MCP when you need multiple agents at scale
- 10% Scripts or Skills for context preservation, portability, or ecosystem reuse

## Anti-Patterns to Avoid

- ❌ Building MCP server before validating with simple scripts
- ❌ Sharing state between scripts (defeats progressive disclosure)
- ❌ Using complex dependencies when httpx + click suffices
- ❌ Reading entire script files when `--help` would suffice
- ❌ Optimizing for "clean code" over context preservation

## Success Metrics

Your agentic system is well-designed if:

- ✅ Each operation is ~200-300 lines of self-contained code
- ✅ Agent can use `--help` to understand options without reading code
- ✅ Scripts work from any directory (absolute paths)
- ✅ Both `--json` and human-readable output modes exist
- ✅ Team members can `git pull` and immediately use
- ✅ Context window consumption is minimal (progressive disclosure)

---

**Remember:** The goal is NOT to build the most sophisticated framework. The goal is to build the simplest system that preserves agent context while providing powerful capabilities.

Reference the `beyond-mcp` repo examples when implementing - they demonstrate these patterns in production-ready code.
