# Python Implementation Guide

## Prerequisites

```bash
pip install langgraph langchain-core langchain-openai  # or langchain-anthropic
```

## State Schema

### Basic State with UI

```python
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer

class AgentState(TypedDict):
    """State with messages and UI components."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
```

### Extended State Example

```python
from typing import Optional

class WeatherAgentState(TypedDict):
    """Weather agent with caching and UI."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
    location: Optional[str]
    cached_weather: Optional[dict]
```

## Emitting UI Messages

### Basic Push

```python
import uuid
from langchain_core.messages import AIMessage
from langgraph.graph.ui import push_ui_message

def weather_node(state: AgentState):
    """Node that emits weather UI component."""

    # Fetch weather data
    weather_data = get_weather(state["location"])

    # Create AI message
    message = AIMessage(
        id=str(uuid.uuid4()),
        content=f"Here's the weather for {weather_data['city']}"
    )

    # Push UI component
    push_ui_message(
        "weather_card",  # Component name (must match React export)
        {                # Props passed to React component
            "city": weather_data["city"],
            "temperature": weather_data["temp"],
            "conditions": weather_data["conditions"],
            "forecast": weather_data["forecast"]
        },
        message=message  # Link to AI message
    )

    return {"messages": [message]}
```

### Progressive Updates

```python
async def streaming_node(state: AgentState):
    """Stream updates to same component."""

    ui_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    message = AIMessage(id=message_id, content="Generating...")

    # Initial push
    push_ui_message(
        "writer",
        {"content": ""},
        id=ui_id,
        message=message
    )

    # Stream updates
    content = ""
    async for chunk in llm.astream("Write a poem"):
        content += chunk.content
        push_ui_message(
            "writer",
            {"content": content},
            id=ui_id,  # Same ID
            message=message,
            merge=True  # Merge props instead of replace
        )

    return {"messages": [message]}
```

### Multiple Components

```python
def analysis_node(state: AgentState):
    """Emit multiple UI components."""

    message = AIMessage(id=str(uuid.uuid4()), content="Analysis complete")

    # Chart component
    push_ui_message(
        "chart",
        {"data": chart_data, "type": "bar"},
        message=message
    )

    # Table component
    push_ui_message(
        "data_table",
        {"rows": table_rows, "columns": columns},
        message=message
    )

    # Summary card
    push_ui_message(
        "summary_card",
        {"title": "Summary", "stats": stats},
        message=message
    )

    return {"messages": [message]}
```

## Complete Graph Example

### Weather Agent with UI

```python
import uuid
from typing import Annotated, Sequence, TypedDict, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer, push_ui_message
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode


# State definition
class WeatherState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]


# Tool definition
@tool
def get_weather(city: str) -> dict:
    """Get weather data for a city."""
    # Mock data - replace with real API
    return {
        "city": city,
        "temperature": 72,
        "conditions": "Sunny",
        "humidity": 65,
        "wind_speed": 10
    }


# Agent node
def agent_node(state: WeatherState):
    """Process messages and call tools."""
    llm = ChatAnthropic(model="claude-sonnet-4-5")
    llm_with_tools = llm.bind_tools([get_weather])

    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# UI emission node
def ui_node(state: WeatherState):
    """Emit UI component after tool execution."""

    # Check if last message is tool result
    last_message = state["messages"][-1]
    if not hasattr(last_message, 'tool_calls'):
        return {}

    # Extract weather data from previous tool call
    tool_calls = last_message.tool_calls
    if not tool_calls or tool_calls[0]["name"] != "get_weather":
        return {}

    # Get tool result
    tool_result = state["messages"][-2]  # ToolMessage
    weather_data = eval(tool_result.content)  # Parse result

    # Create AI message
    message = AIMessage(
        id=str(uuid.uuid4()),
        content=f"Weather data for {weather_data['city']}"
    )

    # Push weather card component
    push_ui_message(
        "weather_card",
        {
            "city": weather_data["city"],
            "temperature": weather_data["temperature"],
            "conditions": weather_data["conditions"],
            "humidity": weather_data["humidity"],
            "wind_speed": weather_data["wind_speed"]
        },
        message=message
    )

    return {"messages": [message]}


# Routing logic
def should_continue(state: WeatherState) -> str:
    """Route to tools or UI node."""
    last_message = state["messages"][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return "ui"


# Build graph
tool_node = ToolNode(tools=[get_weather])

workflow = StateGraph(WeatherState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.add_node("ui", ui_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    "ui": "ui"
})
workflow.add_edge("tools", "agent")
workflow.add_edge("ui", END)

graph = workflow.compile()
```

### Usage

```python
from langchain_core.messages import HumanMessage

# Invoke graph
result = graph.invoke({
    "messages": [HumanMessage(content="What's the weather in San Francisco?")]
})

# Stream with multiple modes
for chunk in graph.stream(
    {"messages": [HumanMessage(content="Weather in NYC?")]},
    stream_mode=["updates", "custom"]
):
    print(chunk)
```

## Progress Tracking

### Custom Events for Progress

```python
from langgraph.config import get_stream_writer

def long_running_node(state: AgentState):
    """Track progress with custom events."""
    writer = get_stream_writer()

    # Initial status
    writer({"type": "status", "message": "Starting analysis..."})

    # Progress updates
    for i in range(100):
        # Do work
        process_chunk(i)

        # Emit progress
        writer({
            "type": "progress",
            "current": i + 1,
            "total": 100,
            "message": f"Processing {i + 1}/100"
        })

    # Final status
    writer({"type": "status", "message": "Complete!"})

    return {"messages": [AIMessage(content="Analysis complete")]}
```

## Image Handling

### Base64 Encoding

```python
import base64
from pathlib import Path

def encode_image_to_base64(image_path: str) -> tuple[str, str]:
    """Encode image to base64 for UI component."""
    path = Path(image_path)

    # Determine media type
    extension = path.suffix.lower()
    media_type_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    media_type = media_type_map.get(extension, "image/png")

    # Encode
    with open(image_path, "rb") as f:
        image_data = f.read()
        base64_string = base64.b64encode(image_data).decode("utf-8")

    return base64_string, media_type


def image_display_node(state: AgentState):
    """Display image in UI component."""

    image_path = state.get("image_path")
    if not image_path:
        return {}

    # Encode image
    image_b64, media_type = encode_image_to_base64(image_path)

    message = AIMessage(
        id=str(uuid.uuid4()),
        content="Here's the image"
    )

    # Push image component
    push_ui_message(
        "image_viewer",
        {
            "image_data": image_b64,
            "media_type": media_type,
            "caption": "Generated image",
            "metadata": {"source": "dalle-3"}
        },
        message=message
    )

    return {"messages": [message]}
```

## Error Handling

```python
def safe_ui_node(state: AgentState):
    """Emit UI with error handling."""

    try:
        # Attempt to fetch data
        data = fetch_external_api()

        message = AIMessage(id=str(uuid.uuid4()), content="Data retrieved")

        push_ui_message(
            "data_display",
            {"data": data},
            message=message
        )

        return {"messages": [message]}

    except Exception as e:
        # Emit error UI component
        error_message = AIMessage(
            id=str(uuid.uuid4()),
            content=f"Error: {str(e)}"
        )

        push_ui_message(
            "error_card",
            {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "retry_action": "fetch_data"
            },
            message=error_message
        )

        return {"messages": [error_message]}
```

## Best Practices

### 1. Always Link to Message

```python
# ✅ Good - Links UI to message
message = AIMessage(id=str(uuid.uuid4()), content="Result")
push_ui_message("component", props, message=message)

# ❌ Bad - Orphaned UI component
push_ui_message("component", props)
```

### 2. Use Unique IDs for Progressive Updates

```python
# ✅ Good - Same ID for updates
ui_id = str(uuid.uuid4())
push_ui_message("component", {"value": 0}, id=ui_id, message=msg)
push_ui_message("component", {"value": 50}, id=ui_id, message=msg, merge=True)

# ❌ Bad - Creates new components
push_ui_message("component", {"value": 0}, message=msg)
push_ui_message("component", {"value": 50}, message=msg)
```

### 3. Validate Props

```python
from pydantic import BaseModel

class WeatherProps(BaseModel):
    city: str
    temperature: int
    conditions: str

def weather_node(state: AgentState):
    # Validate before pushing
    props = WeatherProps(
        city="San Francisco",
        temperature=72,
        conditions="Sunny"
    )

    push_ui_message(
        "weather_card",
        props.model_dump(),
        message=message
    )
```

### 4. Memory Management

```python
# ⚠️ Be careful with large data
def gallery_node(state: AgentState):
    images = get_all_images()  # Could be hundreds of images

    # Paginate instead
    page_size = 10
    page = 0
    current_images = images[page * page_size:(page + 1) * page_size]

    push_ui_message(
        "gallery",
        {
            "images": current_images,
            "page": page,
            "total_pages": len(images) // page_size
        },
        message=message
    )
```

## Testing

```python
import pytest
from langchain_core.messages import HumanMessage

def test_weather_ui_emission():
    """Test that weather node emits UI message."""

    result = graph.invoke({
        "messages": [HumanMessage(content="Weather in NYC?")]
    })

    # Check UI messages
    assert "ui" in result
    assert len(result["ui"]) > 0

    ui_msg = result["ui"][0]
    assert ui_msg["name"] == "weather_card"
    assert "city" in ui_msg["props"]
    assert ui_msg["props"]["city"] == "NYC"


def test_progressive_updates():
    """Test streaming updates."""

    updates = []
    for chunk in graph.stream(
        {"messages": [HumanMessage(content="Write a story")]},
        stream_mode=["custom"]
    ):
        updates.append(chunk)

    # Should have multiple updates for same component
    assert len(updates) > 1
```

## Deployment

### langgraph.json

```json
{
  "python_version": "3.11",
  "dependencies": [
    "langchain-anthropic",
    "langgraph"
  ],
  "graphs": {
    "weather_agent": "./src/agent.py:graph"
  },
  "ui": {
    "weather_agent": "./ui/components.tsx"
  },
  "env": ".env"
}
```

### Environment Variables

```bash
ANTHROPIC_API_KEY=your_key_here
LANGSMITH_API_KEY=your_key_here  # Optional
LANGSMITH_TRACING=true           # Optional
```

## Next Steps

- **[03-typescript-implementation.md](03-typescript-implementation.md)**: TypeScript alternative
- **[04-react-components.md](04-react-components.md)**: Build React components
- **[05-integration-guide.md](05-integration-guide.md)**: Integrate with existing apps
