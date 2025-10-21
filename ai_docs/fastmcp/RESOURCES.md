# FastMCP - Resources Guide

Source: `/jlowin/fastmcp` (Context7)

## Basic Resource Definition

### Static Resource

```python
import json
from fastmcp import FastMCP

mcp = FastMCP(name="DataServer")

# Basic dynamic resource returning a string
@mcp.resource("resource://greeting")
def get_greeting() -> str:
    """Provides a simple greeting message."""
    return "Hello from FastMCP Resources!"

# Resource returning JSON data (dict is auto-serialized)
@mcp.resource("data://config")
def get_config() -> dict:
    """Provides application configuration as JSON."""
    return {
        "theme": "dark",
        "version": "1.2.0",
        "features": ["tools", "resources"]
    }
```

### Async Resource

```python
@mcp.resource("resource://my-resource")
async def get_data() -> str:
    data = await fetch_data()
    return f"Hello, world! {data}"
```

## Templated Resources (Dynamic URIs)

### Basic Template

```python
@mcp.resource("resource://{city}/weather")
def get_weather(city: str) -> str:
    return f"Weather for {city}"
```

### Template with Context

```python
from fastmcp import FastMCP, Context

@mcp.resource("resource://{city}/weather")
async def get_weather_with_context(city: str, ctx: Context) -> str:
    await ctx.info(f"Fetching weather for {city}")
    return f"Weather for {city}"
```

### Template with Data Fetching

```python
@mcp.resource("data://{id}")
def get_data_by_id(id: str) -> dict:
    """Template resources support error handling."""
    if id == "secure":
        raise ValueError("Cannot access secure data")
    elif id == "missing":
        raise ResourceError("Data ID 'missing' not found in database")
    return {"id": id, "value": "data"}
```

## Resource Metadata

### Full Configuration

```python
@mcp.resource(
    uri="data://app-status",      # Explicit URI (required)
    name="ApplicationStatus",      # Custom name
    description="Provides the current status of the application.",
    mime_type="application/json",  # Explicit MIME type
    tags={"monitoring", "status"}, # Categorization tags
    meta={"version": "2.1", "team": "infrastructure"}  # Custom metadata
)
def get_application_status() -> dict:
    """Internal function description (ignored if description is provided above)."""
    return {"status": "ok", "uptime": 12345, "version": mcp.settings.version}
```

## Error Handling

### Using ResourceError

```python
from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError

mcp = FastMCP(name="DataServer")

@mcp.resource("resource://safe-error")
def fail_with_details() -> str:
    """This resource provides detailed error information."""
    # ResourceError contents are always sent back to clients,
    # regardless of mask_error_details setting
    raise ResourceError("Unable to retrieve data: file not found")

@mcp.resource("resource://masked-error")
def fail_with_masked_details() -> str:
    """This resource masks internal error details when mask_error_details=True."""
    # This message would be masked if mask_error_details=True
    raise ValueError("Sensitive internal file path: /etc/secrets.conf")
```

## Duplicate Resource Handling

```python
from fastmcp import FastMCP

mcp = FastMCP(
    name="ResourceServer",
    on_duplicate_resources="error"  # Raise error on duplicates
)

@mcp.resource("data://config")
def get_config_v1():
    return {"version": 1}

# This registration attempt will raise a ValueError because
# "data://config" is already registered and the behavior is "error".
# @mcp.resource("data://config")
# def get_config_v2():
#     return {"version": 2}
```

## Disabling Resources

### At Creation Time

```python
@mcp.resource("data://secret", enabled=False)
def get_secret_data():
    """This resource is currently disabled."""
    return "Secret data"
```

## URI Prefix Management

### Check for Prefix

```python
from fastmcp.server import has_resource_prefix

# New style
has_resource_prefix("resource://prefix/path/to/resource", "prefix")
# True

# Legacy style
has_resource_prefix("prefix+resource://path/to/resource", "prefix")
# True

# No prefix
has_resource_prefix("resource://other/path/to/resource", "prefix")
# False
```

### Add Prefix

```python
from fastmcp.server import add_resource_prefix

# New style
add_resource_prefix("resource://path/to/resource", "prefix")
# "resource://prefix/path/to/resource"

# Absolute path
add_resource_prefix("resource:///absolute/path", "prefix")
# "resource://prefix//absolute/path"
```

### Remove Prefix

```python
from fastmcp.server import remove_resource_prefix

# New style
remove_resource_prefix("resource://prefix/path/to/resource", "prefix")
# "resource://path/to/resource"

# Absolute path
remove_resource_prefix("resource://prefix//absolute/path", "prefix")
# "resource:///absolute/path"
```

## Client-Side Resource Access

### Reading Resources

```python
async with client:
    # Access resources from different servers
    weather_icons = await client.read_resource("weather://weather/icons/sunny")
    templates = await client.read_resource("resource://assistant/templates/list")

    print(f"Weather icon: {weather_icons[0].blob}")
    print(f"Templates: {weather_icons[0].text}")
```

### With Context in Tools

```python
from fastmcp import Context

@mcp.tool
async def process_config(ctx: Context) -> str:
    """Read data from resources."""
    content_list = await ctx.read_resource("resource://config")
    content = content_list[0].content
    return f"Config: {content}"
```

## Resource with MCPMixin

### Basic Definition

```python
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_resource

class MyComponent(MCPMixin):
    @mcp_resource(uri="component://data")
    def resource_method(self):
        return {"data": "some data"}
```

### Disabled Resource

```python
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_resource

class MyComponent(MCPMixin):
    @mcp_resource(uri="component://data", enabled=False)
    def resource_method(self):
        return {"data": "some data"}
```

### With Metadata

```python
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_resource

class MyComponent(MCPMixin):
    @mcp_resource(
        uri="component://config",
        title="Data resource Title",
        meta={"internal": True, "cache_ttl": 3600, "priority": "high"}
    )
    def config_resource_method(self):
        return {"config": "data"}
```

## Best Practices

1. **Use clear URI schemes** - `resource://`, `data://`, `file://`
2. **Provide meaningful descriptions** - Help clients understand resource purpose
3. **Use ResourceError for clear error messages** - Always visible to clients
4. **Consider caching** - Resources may be read frequently
5. **Validate template parameters** - Check inputs in templated resources
6. **Use appropriate MIME types** - Helps clients process content correctly
7. **Document metadata** - Explain custom metadata fields
8. **Test error cases** - Ensure errors are handled gracefully
