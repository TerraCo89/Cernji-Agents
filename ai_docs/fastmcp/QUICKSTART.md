# FastMCP - Quick Start

Source: `/jlowin/fastmcp` and `/llmstxt/gofastmcp_llms_txt` (Context7)

## Installation

```bash
pip install fastmcp
```

## Basic Server Creation

### Simple Tool Definition

```python
from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    mcp.run()
```

### With Resources

```python
from fastmcp import FastMCP

mcp = FastMCP(name="My First MCP Server")

@mcp.tool
def add(a: int, b: int) -> int:
    """Adds two integer numbers together."""
    return a + b

@mcp.resource("resource://config")
def get_config() -> dict:
    """Provides the application's configuration."""
    return {"version": "1.0", "author": "MyTeam"}

if __name__ == "__main__":
    mcp.run()
```

## Running with Different Transports

### STDIO (Default)

```python
if __name__ == "__main__":
    mcp.run()  # Default STDIO transport for local CLI
```

### HTTP Transport

```python
if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)
```

### Streamable HTTP (Recommended for Production)

```python
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/mcp")
```

### SSE Transport

```python
if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8080)
```

## Client Usage

### Connect to Server

```python
import asyncio
from fastmcp import Client

client = Client("http://localhost:8000/mcp")

async def call_tool(name: str):
    async with client:
        result = await client.call_tool("greet", {"name": name})
        print(result)

asyncio.run(call_tool("Ford"))
```

### Basic Client Operations

```python
import asyncio
from fastmcp import Client, FastMCP

# In-memory server (ideal for testing)
server = FastMCP("TestServer")
client = Client(server)

# HTTP server
client = Client("https://example.com/mcp")

# Local Python script
client = Client("my_mcp_server.py")

async def main():
    async with client:
        # Basic server interaction
        await client.ping()

        # List available operations
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()

        # Execute operations
        result = await client.call_tool("example_tool", {"param": "value"})
        print(result)

asyncio.run(main())
```

## Tool Definition Patterns

### Simple Tool

```python
@mcp.tool
def multiply(a: float, b: float) -> float:
    """Multiplies two numbers together."""
    return a * b
```

### Custom Named Tool

```python
@mcp.tool("custom_name")
def my_tool(x: int) -> str:
    return str(x)
```

### Async Tool

```python
@mcp.tool
async def fetch_weather(city: str) -> str:
    """Fetch current weather for a city"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.weather.com/{city}")
        return response.text
```

## Resource Definition Patterns

### Basic Resource

```python
@mcp.resource("data://config")
def get_config() -> dict:
    """Provides the application configuration."""
    return {"theme": "dark", "version": "1.0"}
```

### Templated Resource with Parameters

```python
@mcp.resource("resource://{city}/weather")
def get_weather(city: str) -> str:
    return f"Weather for {city}"
```

### Async Resource

```python
@mcp.resource("resource://my-resource")
async def get_data() -> str:
    data = await fetch_data()
    return f"Hello, world! {data}"
```

## Error Handling

### In Tools

```python
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

mcp = FastMCP()

@mcp.tool
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        # Error messages from ToolError are always sent to clients
        raise ToolError("Division by zero is not allowed.")

    return a / b
```

### Client-Side

```python
from fastmcp.exceptions import ToolError

async with client:
    try:
        result = await client.call_tool("potentially_failing_tool", {"param": "value"})
        print("Tool succeeded:", result.data)
    except ToolError as e:
        print(f"Tool failed: {e}")
```

## Custom HTTP Routes

```python
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse

mcp = FastMCP("MyServer")

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

if __name__ == "__main__":
    mcp.run(transport="http")  # Health check at http://localhost:8000/health
```

## Key Features

- **Decorator-based**: Use `@mcp.tool`, `@mcp.resource`, `@mcp.prompt`
- **Type inference**: Automatically generates JSON schemas from type hints
- **Multiple transports**: STDIO, HTTP, Streamable HTTP, SSE
- **Error handling**: Built-in `ToolError` and `ResourceError` exceptions
- **Custom routes**: Add arbitrary HTTP endpoints
- **Production ready**: Built on Starlette/Uvicorn

## Next Steps

- [ADVANCED.md](ADVANCED.md) - Advanced features, middleware, authentication
- [TOOLS.md](TOOLS.md) - Comprehensive tool patterns
- [RESOURCES.md](RESOURCES.md) - Resource management
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment strategies
