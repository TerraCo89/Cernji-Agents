# Troubleshooting Guide

## Common Issues and Solutions

### 1. Components Not Rendering

**Symptom:** UI components don't appear in the chat interface

**Possible Causes:**

#### A. Missing `onCustomEvent` Handler

**Solution:**
```typescript
import { uiMessageReducer, isUIMessage, isRemoveUIMessage } from "@langchain/langgraph-sdk/react-ui";

const stream = useStream({
  apiUrl: "http://localhost:2024",
  assistantId: "agent",
  // Add this handler
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

#### B. Backend Not Emitting UI Messages

**Check Python Code:**
```python
# ✅ Correct
from langgraph.graph.ui import push_ui_message

push_ui_message("component_name", props, message=message)

# ❌ Missing
# Just returning message without pushing UI
return {"messages": [message]}
```

#### C. Component Name Mismatch

**Backend:**
```python
push_ui_message("weather_card", props, message=message)
```

**Frontend Must Match:**
```typescript
export default {
  weather_card: WeatherComponent,  // Must match "weather_card"
};
```

### 2. TypeScript Errors

**Symptom:** Type errors with `useStream` or `UIMessage`

**Solution:**

```typescript
import type { Message } from "@langchain/langgraph-sdk";
import type { UIMessage, RemoveUIMessage } from "@langchain/langgraph-sdk/react-ui";

// Define state type explicitly
type StateType = {
  messages: Message[];
  ui?: UIMessage[];
};

// Define update types
type UpdateTypes = {
  UpdateType: {
    messages?: Message[] | Message | string;
    ui?: (UIMessage | RemoveUIMessage)[] | UIMessage | RemoveUIMessage;
  };
  CustomEventType: UIMessage | RemoveUIMessage;
};

// Use in useStream
const stream = useStream<StateType, UpdateTypes>({
  apiUrl: "http://localhost:2024",
  assistantId: "agent",
  // ...
});
```

### 3. CORS Errors

**Symptom:** `Access to fetch at 'http://localhost:2024' from origin 'http://localhost:3000' has been blocked by CORS policy`

**Solution A: Configure LangGraph Server (Recommended)**

```python
# langgraph.json
{
  "graphs": {...},
  "env": ".env",
  "cors": {
    "allowed_origins": ["http://localhost:3000", "http://localhost:5173"]
  }
}
```

**Solution B: Development Proxy (Next.js)**

```javascript
// next.config.js
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:2024/:path*',
      },
    ];
  },
};
```

Then update frontend:
```typescript
const stream = useStream({
  apiUrl: "/api",  // Use proxy
  assistantId: "agent",
});
```

### 4. Images Not Displaying

**Symptom:** Broken image icons or images not loading

**Possible Causes:**

#### A. Invalid Base64 Encoding

**Check Python Code:**
```python
import base64

# ✅ Correct
with open(image_path, "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

# ❌ Incorrect - forgot decode
image_data = base64.b64encode(image_data)  # Returns bytes, not string
```

#### B. Missing Data URL Prefix

**React Component:**
```tsx
// ✅ Correct
<img src={`data:${media_type};base64,${image_data}`} />

// ❌ Incorrect - missing data URL prefix
<img src={image_data} />
```

#### C. Large Images Causing Memory Issues

**Solution - Resize Before Encoding:**
```python
from PIL import Image
import io
import base64

def encode_resized_image(path: str, max_width: int = 800) -> tuple[str, str]:
    """Resize and encode image."""
    img = Image.open(path)

    # Resize if too large
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    # Encode
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return b64, "image/png"
```

### 5. Streaming Not Working

**Symptom:** Components only appear after entire response completes

**Solution - Enable Streaming:**

**Python:**
```python
async def streaming_node(state: AgentState):
    """Stream updates progressively."""
    ui_id = str(uuid.uuid4())
    message = AIMessage(id=str(uuid.uuid4()), content="Generating...")

    # Initial push
    push_ui_message("writer", {"content": ""}, id=ui_id, message=message)

    content = ""
    async for chunk in llm.astream("Write a story"):
        content += chunk.content
        # Progressive update with merge=True
        push_ui_message(
            "writer",
            {"content": content},
            id=ui_id,
            message=message,
            merge=True  # Critical for streaming
        )

    return {"messages": [message]}
```

**Frontend:**
```typescript
// Component renders partial content
function Writer({ content }: { content: string }) {
  const isStreaming = content && !content.endsWith('.');

  return (
    <div>
      <div>{content}</div>
      {isStreaming && <span className="cursor">▊</span>}
    </div>
  );
}
```

### 6. State Not Persisting

**Symptom:** Conversation resets on page refresh

**Solution - Enable Checkpointing:**

**Python:**
```python
from langgraph.checkpoint.memory import MemorySaver

# Add checkpointer
checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
```

**Frontend:**
```typescript
const [threadId, setThreadId] = useQueryState("threadId");

const stream = useStream({
  apiUrl: "http://localhost:2024",
  assistantId: "agent",
  threadId: threadId ?? null,  // Preserve thread ID
  onThreadId: setThreadId,     // Save to URL
});
```

### 7. Components Loading Forever

**Symptom:** "Loading component..." never resolves

**Debugging Steps:**

#### 1. Check Network Tab

Open DevTools → Network → Filter "fetch"
- Is the component bundle request succeeding?
- Is the response valid JavaScript?

#### 2. Verify langgraph.json

```json
{
  "ui": {
    "agent": "./ui/components.tsx"  // Correct path?
  }
}
```

#### 3. Check Component Export

```typescript
// ui/components.tsx
// ✅ Correct - default export with component map
export default {
  weather: WeatherComponent,
};

// ❌ Incorrect - named export
export { WeatherComponent };
```

#### 4. Add Error Handler

```typescript
<LoadExternalComponent
  stream={thread}
  message={ui}
  fallback={<div>Loading...</div>}
  onError={(error) => {
    console.error("Component load failed:", error);
    return <div>Failed to load: {error.message}</div>;
  }}
/>
```

### 8. Memory Leaks / Performance Issues

**Symptom:** App becomes slow over time, high memory usage

**Solution A: Limit UI Messages**

```python
# Backend - Only keep recent UI messages
def cleanup_ui(state: AgentState):
    """Keep only last 50 UI messages."""
    ui_messages = state.get("ui", [])
    if len(ui_messages) > 50:
        return {"ui": ui_messages[-50:]}
    return {}
```

**Solution B: Virtualize Long Lists**

```tsx
import { FixedSizeList } from 'react-window';

function MessageList({ messages }) {
  return (
    <FixedSizeList
      height={600}
      itemCount={messages.length}
      itemSize={100}
      width="100%"
    >
      {({ index, style }) => (
        <div style={style}>
          <ChatMessage message={messages[index]} />
        </div>
      )}
    </FixedSizeList>
  );
}
```

**Solution C: Lazy Load Images**

```tsx
<img
  src={`data:${media_type};base64,${image_data}`}
  loading="lazy"  // Browser-level lazy loading
  onLoad={() => setLoaded(true)}
/>
```

### 9. Deployment Issues

#### Vercel Deploy Fails

**Error:** `Module not found: Can't resolve '@langchain/langgraph-sdk'`

**Solution:**
```bash
# Verify package.json includes dependency
npm install @langchain/langgraph-sdk --save

# Check .npmrc (if using private registry)
# registry=https://registry.npmjs.org/

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### LangGraph Cloud Deploy Fails

**Error:** `Failed to load UI components`

**Solution:**
```bash
# Check langgraph.json paths
langgraph config validate

# Verify component file exists
ls ui/components.tsx

# Test locally first
langgraph dev

# Deploy with verbose logging
langgraph deploy --verbose
```

### 10. Interactive Features Not Working

**Symptom:** Buttons don't respond, form submissions fail

**Solution - Verify useStreamContext:**

```tsx
import { useStreamContext } from "@langchain/langgraph-sdk/react-ui";

function InteractiveComponent({ data }) {
  const { submit, thread } = useStreamContext();

  // ✅ Correct
  const handleClick = () => {
    submit({
      messages: [{
        type: "human",
        content: "Button clicked"
      }]
    });
  };

  // ❌ Incorrect - submit not defined
  const handleClick = () => {
    console.log("Click");  // Nothing happens
  };

  return <button onClick={handleClick}>Click Me</button>;
}
```

## Debugging Checklist

When components aren't working, check in order:

1. **Backend Emitting?**
   ```python
   print(f"Pushing UI: {component_name}")
   push_ui_message(component_name, props, message=message)
   ```

2. **Frontend Receiving?**
   ```typescript
   onCustomEvent: (event, options) => {
     console.log("Custom event:", event);  // Should see UIMessage
     // ...
   }
   ```

3. **Component Registered?**
   ```typescript
   export default {
     component_name: ComponentFunction,  // Name matches backend?
   };
   ```

4. **Rendering?**
   ```typescript
   {stream.values?.ui?.map((ui) => {
     console.log("Rendering UI:", ui.name);  // Should log
     return <LoadExternalComponent key={ui.id} ... />;
   })}
   ```

5. **No Errors?**
   - Check browser console for errors
   - Check LangGraph server logs
   - Check network tab for failed requests

## Getting Help

### Enable Debug Logging

**Frontend:**
```typescript
const stream = useStream({
  apiUrl: "http://localhost:2024",
  assistantId: "agent",
  onCustomEvent: (event, options) => {
    console.log("[CustomEvent]", event);
    // ... handler
  },
  onError: (error) => {
    console.error("[Stream Error]", error);
  },
  onFinish: (state, run) => {
    console.log("[Stream Finished]", state, run);
  },
});
```

**Backend:**
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def my_node(state):
    logger.debug(f"Node executing: {state}")
    push_ui_message(...)
    logger.debug("UI message pushed")
```

### Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `Cannot read property 'ui' of undefined` | State doesn't have `ui` field | Add `ui` field to state schema |
| `Component not found: weather_card` | Name mismatch | Check component export name |
| `TypeError: submit is not a function` | Not inside StreamContext | Wrap in StreamProvider |
| `NetworkError when attempting to fetch resource` | CORS or server down | Check CORS config, verify server running |
| `Failed to load external component` | Component bundle 404 | Check langgraph.json `ui` path |

## Resources

- **LangGraph Discord**: https://discord.gg/langchain
- **GitHub Issues**: https://github.com/langchain-ai/langgraph/issues
- **Documentation**: https://docs.langchain.com/langgraph-platform/generative-ui-react
- **Examples Repository**: https://github.com/langchain-ai/langgraphjs-gen-ui-examples
