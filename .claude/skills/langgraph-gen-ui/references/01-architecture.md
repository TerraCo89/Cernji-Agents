# LangGraph Generative UI - Architecture Overview

## What is Generative UI?

LangGraph Generative UI enables AI agents to dynamically generate and render custom React components during conversation flows. Instead of returning plain text, agents can emit rich, interactive UI components like charts, forms, cards, galleries, and custom visualizations.

## Architecture Components

### 1. Backend (LangGraph Agent)

**Languages:** Python or TypeScript/JavaScript

**Key Elements:**
- **StateGraph**: Main graph orchestrating agent behavior
- **State Schema**: Must include `ui` field with `ui_message_reducer`
- **UI Emission**: `push_ui_message()` (Python) or `ui.push()` (TypeScript)
- **Streaming**: SSE-based protocol carrying UI specifications

```python
# Python State Schema
from typing import Annotated, Sequence, TypedDict
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
```

```typescript
// TypeScript State Schema
import { Annotation } from "@langchain/langgraph";
import { uiMessageReducer } from "@langchain/langgraph-sdk/react-ui/server";

const AgentState = Annotation.Root({
  messages: Annotation<Message[]>({
    reducer: (left, right) => left.concat(right),
    default: () => [],
  }),
  ui: Annotation({
    reducer: uiMessageReducer,
    default: () => []
  }),
});
```

### 2. Streaming Protocol

**Transport:** Server-Sent Events (SSE)

**Stream Modes:**
- `values`: Full state after each node
- `updates`: State deltas (only changes)
- `messages`: LLM tokens + metadata
- `custom`: User-defined events
- `debug`: Execution traces

**UIMessage Structure:**
```typescript
interface UIMessage {
  type: "ui";
  id: string;
  name: string;  // Component identifier
  props: Record<string, unknown>;
  metadata?: {
    message_id?: string;  // Link to AI message
    merge?: boolean;      // Progressive updates
    run_id?: string;
    tags?: string[];
  };
}
```

### 3. Frontend (React)

**Key Packages:**
- `@langchain/langgraph-sdk`: Core SDK with hooks
- `@langchain/langgraph-sdk/react-ui`: UI-specific utilities

**Core Hooks:**
- `useStream()`: Manages streaming connection, state, and lifecycle
- `useStreamContext()`: Access thread state within components

**Core Components:**
- `LoadExternalComponent`: Renders UI components (external or local)

### 4. Component Registration

**Two Patterns:**

**Pattern 1: Server-Side Bundle (LangGraph Platform)**
```json
// langgraph.json
{
  "graphs": {
    "agent": "./src/agent/graph.py:graph"
  },
  "ui": {
    "agent": "./ui/components.tsx"
  }
}
```

Components are bundled by LangGraph Platform and served as external assets.

**Pattern 2: Client-Side Components**
```typescript
import { LoadExternalComponent } from "@langchain/langgraph-sdk/react-ui";
import WeatherCard from "./components/WeatherCard";

const clientComponents = {
  weather: WeatherCard,
};

<LoadExternalComponent
  stream={thread}
  message={ui}
  components={clientComponents}  // Pre-loaded
/>
```

## Data Flow

### Complete Request-Response Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│  1. User Input                                                  │
│  ────────────────────────────────────────────────────────────── │
│  User submits message via submit({ messages: [...] })          │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Backend Processing                                          │
│  ────────────────────────────────────────────────────────────── │
│  • StateGraph executes nodes sequentially                       │
│  • Agent calls tools, processes data                            │
│  • Node emits UI message:                                       │
│    push_ui_message("component_name", props, message=msg)        │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Streaming to Frontend                                       │
│  ────────────────────────────────────────────────────────────── │
│  • UIMessage created with component name + props                │
│  • Streamed via SSE alongside text messages                     │
│  • Frontend receives via onCustomEvent callback                 │
│  • uiMessageReducer merges into state                           │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Component Rendering                                         │
│  ────────────────────────────────────────────────────────────── │
│  • LoadExternalComponent matches name to React component        │
│  • Component renders with props                                 │
│  • Optional: useStreamContext() for agent interaction           │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. User Interaction (Optional)                                 │
│  ────────────────────────────────────────────────────────────── │
│  • User clicks button, submits form, etc.                       │
│  • Component calls submit() from useStreamContext()             │
│  • New message sent to agent → Cycle repeats                    │
└─────────────────────────────────────────────────────────────────┘
```

## Progressive Rendering

### Incremental Updates

Update the same component as data arrives (e.g., LLM streaming):

```python
# Python
ui_id = str(uuid.uuid4())

# Initial push
push_ui_message("writer", {"content": ""}, id=ui_id, message=message)

# Stream updates with merge=True
async for chunk in llm.astream("Write a poem"):
    content += chunk.content
    push_ui_message(
        "writer",
        {"content": content},
        id=ui_id,  # Same ID
        message=message,
        merge=True  # Merge props
    )
```

```typescript
// TypeScript
const ui = typedUi<typeof ComponentMap>(config);
const id = uuidv4();

ui.push({ id, name: "writer", props: { content: "" } }, { message });

for await (const chunk of contentStream) {
  content = content?.concat(chunk) ?? chunk;
  ui.push(
    { id, name: "writer", props: { content: content?.text } },
    { message, merge: true }
  );
}
```

## Key Benefits

✅ **Rich Interactions**: Move beyond text to visual, interactive components
✅ **Streaming Updates**: Progressive rendering as agent processes data
✅ **Type Safety**: TypeScript support for component props and state
✅ **Modular**: Separate agent logic from UI presentation
✅ **Reusable**: Components work across multiple agent types
✅ **Bidirectional**: User interactions feed back to agent via submit()

## Use Cases

- **Data Visualization**: Charts, graphs, tables
- **Forms**: Multi-step forms, surveys, configuration
- **Galleries**: Image/video collections, product catalogs
- **Cards**: Flashcards, content previews, summaries
- **Interactive Tools**: Calculators, editors, drawing tools
- **Progress Tracking**: Loading states, operation progress
- **Approvals**: Human-in-the-loop workflows with approve/reject

## Architecture Decisions

### Why SSE?

- **Unidirectional streaming**: Server → Client (perfect for AI generation)
- **Automatic reconnection**: Built into EventSource API
- **HTTP/1.1 compatible**: No WebSocket upgrade needed
- **LangGraph Platform support**: Native integration

### Why Shadow DOM (LoadExternalComponent)?

- **Style isolation**: External component CSS doesn't leak
- **Security**: Sandbox external code
- **Performance**: Lazy loading of component bundles

### Why ui_message_reducer?

- **State management**: Accumulates UI messages in state
- **Merge support**: Update components progressively
- **Message ordering**: Maintains chronological order
- **Filtering**: Easy to filter by message_id

## Next Steps

- **[02-python-implementation.md](02-python-implementation.md)**: Python backend guide
- **[03-typescript-implementation.md](03-typescript-implementation.md)**: TypeScript backend guide
- **[04-react-components.md](04-react-components.md)**: React component patterns
- **[05-integration-guide.md](05-integration-guide.md)**: Retrofit existing apps
- **[06-examples.md](06-examples.md)**: Complete working examples
