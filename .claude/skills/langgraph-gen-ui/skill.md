---
name: langgraph-gen-ui
description: This skill should be used when implementing rich, interactive React components in LangGraph applications, including weather dashboards, image galleries, flashcards, charts, forms, and custom visualizations. Use when building new agents with custom UI, retrofitting existing agents with generative UI, or implementing specific component types like galleries or interactive forms.
---

# LangGraph Generative UI Builder

## Purpose

This skill provides comprehensive guidance for implementing LangGraph Generative UI, which enables AI agents to dynamically render custom React components during conversation flows. Instead of plain text responses, agents can emit rich visualizations (charts, galleries, dashboards), interactive components (forms, flashcards, controls), and custom UI elements.

The skill covers:
- Architecture understanding and data flow
- Python backend implementation with `push_ui_message()`
- React component creation and styling
- Integration with existing Next.js applications
- Complete working examples (weather, gallery, flashcards)
- Troubleshooting and optimization

## When to Use This Skill

This skill should be used when:
- Building a LangGraph agent that needs to display rich UI components
- Migrating from plain text responses to interactive visualizations
- Implementing image galleries, flashcards, or data visualizations in agents
- Adding progress indicators or interactive forms to agents
- Creating human-in-the-loop workflows with custom UI components
- Retrofitting generative UI into existing LangGraph applications
- Displaying screenshots, OCR results, or media content in chat interfaces

**Trigger phrases:**
- "Add custom UI to my LangGraph agent"
- "Display images/charts/flashcards in LangGraph"
- "Implement generative UI for [agent name]"
- "Create interactive components for LangGraph"
- "Show me how to add weather cards/galleries/forms"
- "How do I display screenshots in LangGraph?"

---

## Workflow

### Step 1: Determine Implementation Type

Present the user with implementation options to understand their needs:

**Question:** "What would you like to implement with LangGraph Generative UI?"

**Options:**
1. **Start from scratch** - New LangGraph agent with custom UI
2. **Add to existing agent** - Retrofit generative UI into existing LangGraph app
3. **Specific component** - Weather card, image gallery, flashcard, chart, form
4. **Learn architecture** - Understand how generative UI works

Proceed to the appropriate step based on the user's response.

---

### Step 2A: Start from Scratch (New Agent)

For new implementations requiring both backend and frontend creation:

#### Backend Setup (Python)

1. **Load architecture documentation:**
   ```
   Read: references/01-architecture.md
   Read: references/02-python-implementation.md
   ```

2. **Create state schema with `ui` field:**

   Define the agent state with UI message support:

   ```python
   from typing import Annotated, Sequence, TypedDict
   from langchain_core.messages import BaseMessage
   from langgraph.graph.message import add_messages
   from langgraph.graph.ui import AnyUIMessage, ui_message_reducer

   class AgentState(TypedDict):
       messages: Annotated[Sequence[BaseMessage], add_messages]
       ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
   ```

3. **Implement node that emits UI:**

   Create nodes that push UI messages:

   ```python
   import uuid
   from langchain_core.messages import AIMessage
   from langgraph.graph.ui import push_ui_message

   def ui_node(state: AgentState):
       # Process data
       data = process_user_request(state)

       # Create AI message
       message = AIMessage(
           id=str(uuid.uuid4()),
           content="Here's your result"
       )

       # Push UI component
       push_ui_message(
           "component_name",  # Must match React export
           {
               "prop1": data["value1"],
               "prop2": data["value2"]
           },
           message=message
       )

       return {"messages": [message]}
   ```

4. **Build graph and configure deployment:**

   Configure `langgraph.json` with UI components:

   ```json
   {
     "graphs": {"agent": "./src/agent.py:graph"},
     "ui": {"agent": "./ui/components.tsx"}
   }
   ```

#### Frontend Setup (React)

1. **Load component documentation:**
   ```
   Read: references/04-react-components.md
   ```

2. **Create React component with TypeScript:**

   ```tsx
   interface ComponentProps {
     prop1: string;
     prop2: string;
   }

   export default function Component({ prop1, prop2 }: ComponentProps) {
     return (
       <div className="component">
         <h3>{prop1}</h3>
         <p>{prop2}</p>
       </div>
     );
   }
   ```

3. **Export component map:**

   ```tsx
   import Component from './Component';

   export default {
     component_name: Component,
   };
   ```

4. **Integrate with application:**

   Add `LoadExternalComponent` to message rendering and configure `useStream` with `onCustomEvent` handler.

---

### Step 2B: Add to Existing Agent (Retrofit)

For integrating generative UI into existing LangGraph applications:

#### Step 1: Analyze Current Setup

- Read existing graph code to understand structure
- Identify nodes where UI should be emitted
- Check if frontend already uses `useStream` hook
- Determine which components are needed

#### Step 2: Update Backend

1. **Add `ui` field to existing state schema:**

   ```python
   from langgraph.graph.ui import AnyUIMessage, ui_message_reducer

   # Update existing state
   class ExistingState(TypedDict):
       messages: Annotated[Sequence[BaseMessage], add_messages]
       ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]  # Add this
       # ... existing fields
   ```

2. **Import UI emission functions:**

   ```python
   from langgraph.graph.ui import push_ui_message
   ```

3. **Add UI emission to relevant nodes:**

   Identify nodes that should emit UI and add `push_ui_message()` calls.

#### Step 3: Update Frontend

1. **Load integration guide:**
   ```
   Read: references/05-integration-guide.md
   ```

2. **Add `onCustomEvent` handler to `useStream`:**

   ```typescript
   import { uiMessageReducer, isUIMessage, isRemoveUIMessage } from "@langchain/langgraph-sdk/react-ui";

   const stream = useStream({
     apiUrl: "http://localhost:2024",
     assistantId: "agent",
     onCustomEvent: (event, options) => {
       if (isUIMessage(event) || isRemoveUIMessage(event)) {
         options.mutate((prev) => {
           const ui = uiMessageReducer(prev.ui ?? [], event);
           return { ...prev, ui };
         });
       }
     }
   });
   ```

3. **Add `LoadExternalComponent` to message rendering:**

   ```typescript
   import { LoadExternalComponent } from "@langchain/langgraph-sdk/react-ui";

   {stream.values?.ui
     ?.filter((ui) => ui.metadata?.message_id === message.id)
     .map((ui) => (
       <LoadExternalComponent
         key={ui.id}
         stream={stream.thread}
         message={ui}
         fallback={<div>Loading...</div>}
       />
     ))}
   ```

4. **Create component files:**

   Implement React components and export them in component map.

#### Step 4: Test End-to-End

- Start backend: `langgraph dev`
- Start frontend: `npm run dev`
- Verify UI messages are emitted and rendered
- Test interactive features

---

### Step 2C: Specific Component Implementation

For implementing specific component types, load targeted examples:

#### Weather Dashboard

```
Read: references/06-examples.md (section: Example 1)
```

Includes:
- Backend weather data emission with forecast
- Frontend display with current weather + 5-day forecast
- Refresh button for user interaction
- Gradient styling and weather icons

#### Image Gallery

```
Read: references/06-examples.md (section: Example 2)
```

Includes:
- Base64 image encoding on backend
- Responsive gallery grid with lazy loading
- Click to expand, captions, and metadata
- Perfect for Japanese OCR screenshots

#### Flashcard System

```
Read: references/06-examples.md (section: Example 3)
```

Includes:
- Flip animation with CSS transforms
- Progress tracking across cards
- Difficulty rating feedback to agent
- Navigation controls

#### Charts and Data Visualization

```
Read: references/04-react-components.md (section: Chart Component)
```

Includes:
- Recharts integration for data visualization
- Support for line, bar, pie charts
- Interactive tooltips and legends

#### Forms

```
Read: references/04-react-components.md (section: Form Component)
```

Includes:
- Dynamic form fields from props
- Validation and submission
- Send form data back to agent

---

### Step 2D: Learn Architecture

For users wanting to understand the underlying system:

1. **Load and explain architecture:**
   ```
   Read: references/01-architecture.md
   ```

2. **Show data flow:**

   Explain the complete request-response cycle:
   - User submits message
   - Backend processes and emits UI specification
   - Streams via SSE to frontend
   - LoadExternalComponent renders React component
   - User interactions feed back to agent

3. **Provide minimal working example:**

   Show simplest possible implementation of backend + frontend.

4. **Link to detailed documentation:**

   Direct user to comprehensive guides in references/.

---

### Step 3: Implementation

Execute the implementation based on user's chosen path:

#### If Creating New Files

1. Create backend graph with UI emission
2. Create React component files
3. Create `langgraph.json` configuration
4. Set up component export map
5. Provide complete setup instructions

#### If Modifying Existing Files

1. Read existing files to understand structure
2. Present proposed changes using Edit tool
3. Update state schema to include `ui` field
4. Add UI emission calls to relevant nodes
5. Update frontend message rendering

#### Always Provide

- Complete, working code with proper imports
- Type definitions for TypeScript/Python
- Comments explaining key implementation details
- Next steps for testing and verification

---

### Step 4: Testing and Troubleshooting

Guide the user through testing and resolving issues:

#### Testing Steps

1. **Start backend:**
   ```bash
   langgraph dev
   ```

2. **Start frontend:**
   ```bash
   npm run dev  # or pnpm dev
   ```

3. **Test the flow:**
   - Send message that triggers UI emission
   - Verify component renders correctly
   - Test any interactive features
   - Check browser console for errors

#### If Issues Occur

1. **Load troubleshooting guide:**
   ```
   Read: references/07-troubleshooting.md
   ```

2. **Check common issues:**
   - Components not rendering → Verify `onCustomEvent` handler
   - Name mismatch → Check component export name matches backend
   - CORS errors → Configure LangGraph server CORS settings
   - Images not loading → Verify base64 encoding
   - Loading forever → Check `langgraph.json` ui path

3. **Enable debug logging:**

   Frontend:
   ```typescript
   onCustomEvent: (event) => console.log("[Event]", event)
   ```

   Backend:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

4. **Verify configuration:**
   - Check component names match between backend and frontend
   - Verify file paths in `langgraph.json`
   - Ensure all dependencies are installed

---

## Key Implementation Patterns

### Pattern 1: Basic UI Emission

Emit a simple UI component from agent node:

```python
# Backend
from langchain_core.messages import AIMessage
from langgraph.graph.ui import push_ui_message
import uuid

message = AIMessage(id=str(uuid.uuid4()), content="Result")
push_ui_message("component_name", {"prop": "value"}, message=message)
return {"messages": [message]}
```

```tsx
// Frontend
<LoadExternalComponent key={ui.id} stream={thread} message={ui} />
```

### Pattern 2: Progressive Updates

Stream incremental updates to same component:

```python
# Backend - Update component as data arrives
ui_id = str(uuid.uuid4())

# Initial push
push_ui_message("component", {"value": 0}, id=ui_id, message=msg)

# Update with same ID
push_ui_message("component", {"value": 50}, id=ui_id, message=msg, merge=True)
```

### Pattern 3: Interactive Components

Create components that communicate back to agent:

```tsx
// Frontend - User actions trigger agent messages
import { useStreamContext } from "@langchain/langgraph-sdk/react-ui";

function Component({ data }) {
  const { submit } = useStreamContext();

  const handleAction = () => {
    submit({
      messages: [{
        type: "human",
        content: "User action"
      }]
    });
  };

  return <button onClick={handleAction}>Action</button>;
}
```

### Pattern 4: Image Display

Display base64-encoded images:

```python
# Backend - Encode and emit image
import base64

with open(image_path, "rb") as f:
    image_data = f.read()
    image_b64 = base64.b64encode(image_data).decode("utf-8")

push_ui_message("image_viewer", {
    "image_data": image_b64,
    "media_type": "image/png",
    "caption": "Screenshot"
}, message=message)
```

```tsx
// Frontend - Display image with data URL
<img
  src={`data:${media_type};base64,${image_data}`}
  alt={caption}
  loading="lazy"
/>
```

---

## Best Practices

### 1. Always Link UI to Messages

```python
# ✅ Correct
message = AIMessage(id=str(uuid.uuid4()), content="Result")
push_ui_message("component", props, message=message)

# ❌ Incorrect - Orphaned UI component
push_ui_message("component", props)
```

### 2. Use Unique IDs for Progressive Updates

```python
# ✅ Correct - Same ID for updates
ui_id = str(uuid.uuid4())
push_ui_message("component", {"value": 0}, id=ui_id, message=msg)
push_ui_message("component", {"value": 50}, id=ui_id, message=msg, merge=True)

# ❌ Incorrect - Creates multiple components
push_ui_message("component", {"value": 0}, message=msg)
push_ui_message("component", {"value": 50}, message=msg)
```

### 3. Validate Props with Pydantic

```python
from pydantic import BaseModel

class ComponentProps(BaseModel):
    field: str
    count: int

# Validate before pushing
props = ComponentProps(field="value", count=42)
push_ui_message("component", props.model_dump(), message=message)
```

### 4. Handle Errors in Components

```tsx
<LoadExternalComponent
  stream={thread}
  message={ui}
  fallback={<div className="loading">Loading...</div>}
  onError={(error) => (
    <div className="error">
      Failed to load: {error.message}
    </div>
  )}
/>
```

### 5. Optimize Performance

- Lazy load images: `<img loading="lazy" />`
- Memoize expensive components: `React.memo()`
- Virtualize long lists: `react-window`
- Limit UI messages in state (keep last 50)

---

## Success Criteria

Implementation is complete when all criteria are met:

- ✅ Backend emits UI messages using `push_ui_message()`
- ✅ State schema includes `ui` field with `ui_message_reducer`
- ✅ Frontend handles `onCustomEvent` for UI messages
- ✅ `LoadExternalComponent` renders UI components correctly
- ✅ Components display with proper styling and layout
- ✅ Interactive features work (if applicable)
- ✅ `langgraph.json` configured with UI component paths
- ✅ End-to-end test passes successfully
- ✅ No console errors in browser or backend logs

---

## Bundled Resources

### References

Comprehensive documentation for LangGraph Generative UI implementation:

- **[📐 01-architecture.md](./references/01-architecture.md)**: Architecture overview, data flow, progressive rendering patterns, and use cases. Load when understanding the system design.

- **[🐍 02-python-implementation.md](./references/02-python-implementation.md)**: Complete Python backend guide including state schemas, UI emission, graph examples, progress tracking, and image handling. Load when implementing the backend.

- **[⚛️ 04-react-components.md](./references/04-react-components.md)**: React component patterns covering 8 common types (gallery, flashcard, form, chart, etc.), styling approaches, and testing strategies. Load when creating frontend components.

- **[🔌 05-integration-guide.md](./references/05-integration-guide.md)**: Integration with existing Next.js and React apps, migration from plain chat, deployment guides, and troubleshooting. Load when retrofitting into existing applications.

- **[💡 06-examples.md](./references/06-examples.md)**: Three complete working examples with full source code: Weather Dashboard, Japanese OCR Gallery, and Interactive Flashcard System. Load when implementing specific component types.

- **[🔧 07-troubleshooting.md](./references/07-troubleshooting.md)**: Solutions for 10+ common issues, debugging checklist, error reference table, and performance optimization. Load when encountering problems.

- **[📚 README.md](./references/README.md)**: Quick start guide, feature overview, documentation structure, and best practices summary. Load for high-level understanding.

---

## Quick Reference

### Common Commands

```bash
# Start LangGraph server
langgraph dev

# Start frontend
npm run dev  # or pnpm dev

# Deploy backend
langgraph deploy

# Deploy frontend
vercel
```

### Import Statements

```python
# Python backend
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer, push_ui_message
```

```typescript
// React frontend
import { useStream } from "@langchain/langgraph-sdk/react";
import { LoadExternalComponent } from "@langchain/langgraph-sdk/react-ui";
import { useStreamContext } from "@langchain/langgraph-sdk/react-ui";
import { uiMessageReducer, isUIMessage, isRemoveUIMessage } from "@langchain/langgraph-sdk/react-ui";
```

### Troubleshooting Quick Checks

| Issue | Solution |
|-------|----------|
| Components not rendering | Check `onCustomEvent` handler |
| Name mismatch | Verify export name matches backend |
| CORS errors | Configure `langgraph.json` cors |
| Images not loading | Check base64 encoding |
| Loading forever | Verify `langgraph.json` ui path |
| Type errors | Add explicit type annotations |
