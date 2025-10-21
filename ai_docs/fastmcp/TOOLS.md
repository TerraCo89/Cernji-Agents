# FastMCP - Tools Guide

Source: `/jlowin/fastmcp` (Context7)

## Tool Registration

### Basic Decorator Usage

```python
from fastmcp import FastMCP

mcp = FastMCP()

# Simplest form
@mcp.tool
def my_tool(x: int) -> str:
    return str(x)

# With custom name
@mcp.tool("custom_name")
def my_tool(x: int) -> str:
    return str(x)

# With explicit name parameter
@mcp.tool(name="custom_name")
def my_tool(x: int) -> str:
    return str(x)

# Direct function registration
mcp.tool(my_function, name="custom_name")
```

### Tool with Context

```python
from fastmcp import FastMCP, Context

mcp = FastMCP()

@mcp.tool
async def analyze_with_context(table_name: str, ctx: Context) -> str:
    await ctx.info(f"Analyzing table {table_name}")
    schema = read_table_schema(table_name)
    return f"Schema: {schema}"
```

## Error Handling

### Using ToolError

```python
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

@mcp.tool
def divide(a: float, b: float) -> float:
    """Divide a by b."""

    if b == 0:
        # Error messages from ToolError are always sent to clients,
        # regardless of mask_error_details setting
        raise ToolError("Division by zero is not allowed.")

    # If mask_error_details=True, this message would be masked
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers.")

    return a / b
```

### Client-Side Error Handling

```python
from fastmcp.exceptions import ToolError

# Automatic error raising (default)
async with client:
    try:
        result = await client.call_tool("potentially_failing_tool", {"param": "value"})
        print("Tool succeeded:", result.data)
    except ToolError as e:
        print(f"Tool failed: {e}")

# Manual error checking
async with client:
    result = await client.call_tool(
        "potentially_failing_tool",
        {"param": "value"},
        raise_on_error=False
    )

    if result.is_error:
        print(f"Tool failed: {result.content[0].text}")
    else:
        print(f"Tool succeeded: {result.data}")
```

## Async Background Execution

For blocking synchronous operations that shouldn't freeze the event loop:

```python
import asyncer
import functools
from typing import Callable, ParamSpec, TypeVar, Awaitable

_P = ParamSpec("_P")
_R = TypeVar("_R")

def make_async_background(fn: Callable[_P, _R]) -> Callable[_P, Awaitable[_R]]:
    @functools.wraps(fn)
    async def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        return await asyncer.asyncify(fn)(*args, **kwargs)
    return wrapper

# Usage
from fastmcp import FastMCP
import time

mcp = FastMCP()

@mcp.tool()
@make_async_background
def my_tool() -> None:
    time.sleep(5)  # Won't block the event loop
```

## Dynamic Tool Management

### Add Tool Programmatically

```python
from fastmcp import FastMCP
from fastmcp.server import Tool

mcp = FastMCP(name="DynamicServer")

# Create and add tool
tool = Tool(...)  # Tool instance
mcp.add_tool(tool)
```

### Remove Tool at Runtime

```python
from fastmcp import FastMCP

mcp = FastMCP(name="DynamicToolServer")

@mcp.tool
def calculate_sum(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

# Remove the tool
mcp.remove_tool("calculate_sum")
```

## Duplicate Tool Handling

### Raise Error on Duplicates

```python
from fastmcp import FastMCP

mcp = FastMCP(
    name="StrictServer",
    on_duplicate_tools="error"  # Will raise ValueError on duplicates
)

@mcp.tool
def my_tool():
    return "Version 1"

# This will now raise a ValueError
# @mcp.tool
# def my_tool():
#     return "Version 2"
```

## Tool Output Serialization

### Custom Serializer (YAML Example)

```python
import yaml
from fastmcp import FastMCP

# Define a custom serializer that formats dictionaries as YAML
def yaml_serializer(data):
    return yaml.dump(data, sort_keys=False)

# Create a server with the custom serializer
mcp = FastMCP(name="MyServer", tool_serializer=yaml_serializer)

@mcp.tool
def get_config():
    """Returns configuration in YAML format."""
    return {"api_key": "abc123", "debug": True, "rate_limit": 100}
```

## Testing Tools

### Basic Test

```python
async def test_tool_execution_with_error():
    """Test that tool errors are properly handled."""
    mcp = FastMCP("test-server")

    @mcp.tool
    def divide(a: int, b: int) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    async with Client(mcp) as client:
        with pytest.raises(Exception):
            await client.call_tool("divide", {"a": 10, "b": 0})
```

## Tool Annotations and Metadata

### With MCPMixin

```python
from mcp.types import ToolAnnotations
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool

class MyComponent(MCPMixin):
    @mcp_tool(
        name="my_tool",
        description="Does something cool.",
        annotations=ToolAnnotations(
            title="Attn LLM, use this tool first!",
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
        ),
        meta={"version": "2.0", "category": "database", "author": "dev-team"}
    )
    def tool_method(self, user_id: int):
        return f"Fetching data for user {user_id}"
```

### Disable Tool

```python
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool

class MyComponent(MCPMixin):
    @mcp_tool(name="my_tool", enabled=False)
    def disabled_tool_method(self):
        # This function can't be called by client because it's disabled
        return "You'll never get here!"
```

### Exclude Parameters

```python
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool

class MyComponent(MCPMixin):
    @mcp_tool(
        name="my_tool",
        description="Does something cool.",
        exclude_args=['delete_everything']
    )
    def excluded_param_tool_method(self, delete_everything=False):
        # MCP tool calls can't pass the "delete_everything" argument
        if delete_everything:
            return "Nothing to delete!"
        return "Safe operation"
```

## Client Tool Calling

### Structured Output

```python
async with client:
    result = await client.call_tool("calculate", {"a": 10, "b": 5})

    if result.data is not None:
        # Structured output available and successfully deserialized
        print(f"Structured: {result.data}")
    else:
        # No structured output or deserialization failed - use content blocks
        for content in result.content:
            if hasattr(content, 'text'):
                print(f"Text result: {content.text}")
            elif hasattr(content, 'data'):
                print(f"Binary data: {len(content.data)} bytes")
```

### Raw MCP Protocol

```python
async with client:
    result = await client.call_tool_mcp("potentially_failing_tool", {"param": "value"})
    # result -> mcp.types.CallToolResult

    if result.isError:
        print(f"Tool failed: {result.content}")
    else:
        print(f"Tool succeeded: {result.content}")
        # Note: No automatic deserialization with call_tool_mcp()
```

## Best Practices

1. **Use ToolError for client-facing errors** - Messages are never masked
2. **Provide clear docstrings** - Used as tool descriptions
3. **Use type hints** - Automatically generates JSON schemas
4. **Test with both success and error cases**
5. **Consider async for I/O-bound operations**
6. **Use background execution for CPU-bound sync operations**
7. **Name tools clearly** - Tool names should be self-descriptive
8. **Handle edge cases** - Validate inputs before processing
