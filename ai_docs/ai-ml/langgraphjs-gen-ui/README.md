# LangGraph Generative UI - Complete Guide

A comprehensive guide to implementing rich, interactive UI components in LangGraph applications. This documentation covers both Python and TypeScript implementations with complete working examples.

## What is Generative UI?

LangGraph Generative UI enables AI agents to dynamically render custom React components during conversation flows. Instead of plain text responses, agents can emit:

- **Rich Visualizations**: Charts, graphs, data tables
- **Interactive Components**: Forms, buttons, controls
- **Media Display**: Images, galleries, videos
- **Custom Cards**: Weather cards, flashcards, product cards
- **Progress Indicators**: Loading states, operation progress

## Quick Start

### 1. Check Prerequisites

```bash
# Python backend
pip install langgraph langchain-core langchain-openai

# React frontend
npm install @langchain/langgraph-sdk
```

### 2. Minimal Example

**Backend (Python):**

```python
from langgraph.graph.ui import push_ui_message, ui_message_reducer

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]

def weather_node(state):
    message = AIMessage(id=str(uuid.uuid4()), content="Weather data")
    push_ui_message("weather_card", {"city": "SF", "temp": 72}, message=message)
    return {"messages": [message]}
```

**Frontend (React):**

```typescript
import { useStream } from "@langchain/langgraph-sdk/react";
import { LoadExternalComponent } from "@langchain/langgraph-sdk/react-ui";

const { thread, values } = useStream({
  apiUrl: "http://localhost:2024",
  assistantId: "agent",
  onCustomEvent: (event, options) => {
    if (isUIMessage(event)) {
      options.mutate((prev) => ({
        ...prev,
        ui: uiMessageReducer(prev.ui ?? [], event)
      }));
    }
  }
});

// Render UI components
{values.ui?.map((ui) => (
  <LoadExternalComponent key={ui.id} stream={thread} message={ui} />
))}
```

## Documentation Structure

### Core Guides

1. **[01-architecture.md](01-architecture.md)**
   - Architecture overview and data flow
   - Key components and their roles
   - Progressive rendering patterns
   - Use cases and benefits

2. **[02-python-implementation.md](02-python-implementation.md)**
   - State schema setup
   - Emitting UI messages
   - Complete graph examples
   - Progress tracking and image handling

3. **[04-react-components.md](04-react-components.md)**
   - Component patterns and best practices
   - Common UI patterns (gallery, flashcards, forms, charts)
   - Styling with CSS Modules and Tailwind
   - Testing strategies

4. **[05-integration-guide.md](05-integration-guide.md)**
   - Integrating with existing Next.js apps
   - React app integration (non-Next.js)
   - Migration from plain chat
   - Deployment guides (Vercel, LangGraph Cloud)

### Examples and Reference

5. **[06-examples.md](06-examples.md)**
   - Complete working examples:
     - Weather Dashboard
     - Japanese OCR Gallery
     - Interactive Flashcard System
   - Full source code with CSS
   - Setup and deployment instructions

6. **[07-troubleshooting.md](07-troubleshooting.md)**
   - Common issues and solutions
   - Debugging checklist
   - Error message reference
   - Performance optimization

## Key Features

### ✅ Progressive Rendering

Stream updates to components as data arrives:

```python
# Python
ui_id = str(uuid.uuid4())
for i in range(100):
    push_ui_message("progress", {"value": i}, id=ui_id, merge=True)
```

### ✅ Interactive Components

Components can communicate back to agents:

```typescript
const { submit } = useStreamContext();

<button onClick={() => submit({ messages: [{ type: "human", content: "Refresh" }] })}>
  Refresh Data
</button>
```

### ✅ Type Safety

Full TypeScript support for component props:

```typescript
interface WeatherProps {
  city: string;
  temperature: number;
}

const WeatherCard = ({ city, temperature }: WeatherProps) => { /* ... */ };
```

### ✅ Image Support

Display base64-encoded images:

```python
# Python
image_b64, media_type = encode_image_to_base64("screenshot.png")
push_ui_message("image_viewer", {"image_data": image_b64, "media_type": media_type})
```

```tsx
// React
<img src={`data:${media_type};base64,${image_data}`} alt="Screenshot" />
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (React)                                               │
│  ────────────────────────────────────────────────────────────── │
│  • useStream() - Manages streaming connection                   │
│  • LoadExternalComponent - Renders UI components                │
│  • useStreamContext() - Access thread state                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ SSE Streaming
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  Backend (Python/TypeScript)                                    │
│  ────────────────────────────────────────────────────────────── │
│  • StateGraph - Orchestrates agent behavior                     │
│  • push_ui_message() - Emits UI specifications                  │
│  • ui_message_reducer - Accumulates UI state                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Component Specs
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  UI Components (React)                                          │
│  ────────────────────────────────────────────────────────────── │
│  • WeatherCard, Gallery, Flashcard, etc.                       │
│  • Registered in langgraph.json                                 │
│  • Bundled and served by LangGraph Platform                    │
└─────────────────────────────────────────────────────────────────┘
```

## Use Cases

### 1. Data Visualization
Display charts, graphs, and tables from agent analysis

### 2. Image Galleries
Show collections of images with captions and metadata

### 3. Flashcards
Interactive learning tools with flip animations and ratings

### 4. Forms
Multi-step forms with validation and agent processing

### 5. Progress Tracking
Real-time progress updates for long-running operations

### 6. Approvals
Human-in-the-loop workflows with approve/reject UI

## Real-World Examples

### Weather Dashboard

```python
push_ui_message("weather_dashboard", {
    "city": "San Francisco",
    "temperature": 72,
    "conditions": "Sunny",
    "forecast": [...]
}, message=message)
```

### Japanese OCR Gallery

```python
push_ui_message("japanese_gallery", {
    "items": [
        {
            "image_data": base64_image,
            "extracted_text": "こんにちは",
            "translation": "Hello"
        },
        ...
    ]
}, message=message)
```

### Interactive Flashcards

```python
push_ui_message("flashcard_deck", {
    "cards": [
        {"word": "こんにちは", "reading": "konnichiwa", "meaning": "Hello"},
        ...
    ]
}, message=message)
```

## Best Practices

### 1. Always Link to Messages

```python
# ✅ Good
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
```

### 3. Validate Props

```python
from pydantic import BaseModel

class WeatherProps(BaseModel):
    city: str
    temperature: int

# Validate before pushing
props = WeatherProps(city="SF", temperature=72)
push_ui_message("weather_card", props.model_dump(), message=message)
```

### 4. Handle Errors Gracefully

```typescript
<LoadExternalComponent
  stream={thread}
  message={ui}
  fallback={<div>Loading...</div>}
  onError={(error) => <ErrorComponent error={error} />}
/>
```

## Performance Tips

### 1. Lazy Load Images

```tsx
<img src={imageUrl} loading="lazy" />
```

### 2. Memoize Components

```typescript
export default memo(function ExpensiveComponent({ data }) {
  const processed = useMemo(() => processData(data), [data]);
  return <div>{processed}</div>;
});
```

### 3. Virtualize Long Lists

```typescript
import { FixedSizeList } from 'react-window';

<FixedSizeList height={600} itemCount={messages.length} itemSize={100}>
  {({ index, style }) => <Message message={messages[index]} style={style} />}
</FixedSizeList>
```

### 4. Limit UI Messages in State

```python
def cleanup_ui(state):
    """Keep only last 50 UI messages."""
    ui = state.get("ui", [])
    return {"ui": ui[-50:]} if len(ui) > 50 else {}
```

## Testing

### Unit Tests

```typescript
import { render, screen } from '@testing-library/react';

test('renders weather card', () => {
  render(<WeatherCard city="SF" temperature={72} conditions="Sunny" />);
  expect(screen.getByText('SF')).toBeInTheDocument();
  expect(screen.getByText('72°F')).toBeInTheDocument();
});
```

### Integration Tests

```python
def test_weather_ui_emission():
    result = graph.invoke({
        "messages": [HumanMessage(content="Weather in NYC?")]
    })

    assert "ui" in result
    assert len(result["ui"]) > 0
    assert result["ui"][0]["name"] == "weather_card"
```

## Deployment

### Vercel (Frontend)

```bash
vercel

# Set environment variables in Vercel dashboard:
# NEXT_PUBLIC_API_URL=https://your-langgraph-deployment.app
# NEXT_PUBLIC_ASSISTANT_ID=agent
```

### LangGraph Cloud (Backend)

```bash
langgraph deploy

# Get deployment URL
langgraph deployments list
```

## Resources

### Official Documentation
- **LangGraph Generative UI**: https://docs.langchain.com/langgraph-platform/generative-ui-react
- **LangGraph SDK**: https://www.npmjs.com/package/@langchain/langgraph-sdk
- **API Reference**: https://langchain-ai.github.io/langgraphjs/

### Examples
- **Official Examples**: https://github.com/langchain-ai/langgraphjs-gen-ui-examples
- **Agent Chat UI**: https://github.com/langchain-ai/agent-chat-ui

### Community
- **Discord**: https://discord.gg/langchain
- **GitHub Issues**: https://github.com/langchain-ai/langgraph/issues
- **Stack Overflow**: Tag `langgraph`

## Getting Help

### 1. Check Documentation
- Start with [01-architecture.md](01-architecture.md) for concepts
- See [07-troubleshooting.md](07-troubleshooting.md) for common issues

### 2. Enable Debug Logging

```typescript
// Frontend
onCustomEvent: (event) => console.log("[Event]", event)
```

```python
# Backend
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 3. Ask for Help
- **Discord**: Share code snippets and error messages
- **GitHub**: Create issue with minimal reproduction
- **Stack Overflow**: Tag with `langgraph` and `react`

## Contributing

Found an issue or want to improve this documentation?

1. Open an issue describing the problem
2. Submit a PR with improvements
3. Share your examples and use cases

## License

This documentation is licensed under MIT. See individual repositories for code licenses.

---

**Last Updated**: 2025-01-05

**Trust Score**: 9.2

**Code Snippets**: 50+
