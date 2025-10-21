# Claude Agent SDK for Python - Quick Start

Source: `/anthropics/claude-agent-sdk-python` (Context7)

## Installation

```bash
pip install claude-agent-sdk
```

**Requirements:**
- Python 3.10+
- Node.js (for full functionality including Claude Code CLI)

## Basic Usage

### Simple Asynchronous Query

```python
import anyio
from claude_agent_sdk import query

async def main():
    async for message in query(prompt="What is 2 + 2?"):
        print(message)

anyio.run(main)
```

### Query with Custom Options

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

# Simple query
async for message in query(prompt="Hello Claude"):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print(block.text)
```

### Query with System Prompt and Options

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

# With options
options = ClaudeAgentOptions(
    system_prompt="You are a helpful assistant",
    max_turns=1
)

async for message in query(prompt="Tell me a joke", options=options):
    print(message)
```

## Configuration

### Set Working Directory

```python
from pathlib import Path

options = ClaudeAgentOptions(
    cwd="/path/to/project"  # or Path("/path/to/project")
)
```

### Configure Tools and Permission Mode

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode='acceptEdits'  # auto-accept file edits
)

async for message in query(
    prompt="Create a hello.py file",
    options=options
):
    # Process tool use and results
    pass
```

## Error Handling

```python
from claude_agent_sdk import (
    ClaudeSDKError,      # Base error
    CLINotFoundError,    # Claude Code not installed
    CLIConnectionError,  # Connection issues
    ProcessError,        # Process failed
    CLIJSONDecodeError,  # JSON parsing issues
)

try:
    async for message in query(prompt="Hello"):
        pass
except CLINotFoundError:
    print("Please install Claude Code")
except ProcessError as e:
    print(f"Process failed with exit code: {e.exit_code}")
except CLIJSONDecodeError as e:
    print(f"Failed to parse response: {e}")
```

## Environment Setup

### Set ANTHROPIC_API_KEY

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Or for troubleshooting:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```
