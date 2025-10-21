# Claude Agent SDK for Python - Advanced Usage

Source: `/anthropics/claude-agent-sdk-python` (Context7)

## Custom Tools with SDK MCP Server

### Define In-Process Custom Tool

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions, ClaudeSDKClient

# Define a tool using the @tool decorator
@tool("greet", "Greet a user", {"name": str})
async def greet_user(args):
    return {
        "content": [
            {"type": "text", "text": f"Hello, {args['name']}!"}
        ]
    }

# Create an SDK MCP server
server = create_sdk_mcp_server(
    name="my-tools",
    version="1.0.0",
    tools=[greet_user]
)

# Use it with Claude
options = ClaudeAgentOptions(
    mcp_servers={"tools": server},
    allowed_tools=["mcp__tools__greet"]
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("Greet Alice")

    # Extract and print response
    async for msg in client.receive_response():
        print(msg)
```

## MCP Server Configuration

### Mixed SDK and External MCP Servers

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "internal": sdk_server,      # In-process SDK server
        "external": {                # External subprocess server
            "type": "stdio",
            "command": "external-server"
        }
    }
)
```

### Migration from External to In-Process

```python
# BEFORE: External MCP server (separate process)
options = ClaudeAgentOptions(
    mcp_servers={
        "calculator": {
            "type": "stdio",
            "command": "python",
            "args": ["-m", "calculator_server"]
        }
    }
)
```

```python
# AFTER: SDK MCP server (in-process)
from my_tools import add, subtract  # Your tool functions

calculator = create_sdk_mcp_server(
    name="calculator",
    tools=[add, subtract]
)

options = ClaudeAgentOptions(
    mcp_servers={"calculator": calculator}
)
```

## Hooks

### PreToolUse Hook to Block Bash Commands

```python
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher

async def check_bash_command(input_data, tool_use_id, context):
    tool_name = input_data["tool_name"]
    tool_input = input_data["tool_input"]
    if tool_name != "Bash":
        return {}
    command = tool_input.get("command", "")
    block_patterns = ["foo.sh"]
    for pattern in block_patterns:
        if pattern in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Command contains invalid pattern: {pattern}",
                }
            }
    return {}

options = ClaudeAgentOptions(
    allowed_tools=["Bash"],
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash", hooks=[check_bash_command]),
        ],
    }
)

async with ClaudeSDKClient(options=options) as client:
    # Test 1: Command with forbidden pattern (will be blocked)
    await client.query("Run the bash command: ./foo.sh --help")
    async for msg in client.receive_response():
        print(msg)

    print("\n" + "=" * 50 + "\n")

    # Test 2: Safe command that should work
    await client.query("Run the bash command: echo 'Hello from hooks example!'")
    async for msg in client.receive_response():
        print(msg)
```

## Development

### Run Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_client.py
```

### Linting and Type Checking

```bash
# Lint and style
# Check for issues and fix automatically
python -m ruff check src/ tests/ --fix
python -m ruff format src/ tests/

# Typecheck (only done for src/)
python -m mypy src/
```

### End-to-End Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Run all E2E tests
python -m pytest e2e-tests/ -v

# Run tests with specific marker
python -m pytest e2e-tests/ -v -m e2e

# Run specific test
python -m pytest e2e-tests/test_mcp_calculator.py::test_basic_addition -v
```
