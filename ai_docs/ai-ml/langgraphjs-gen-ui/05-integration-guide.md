# Integration Guide

## Integrating with Existing Next.js App

### Prerequisites

```bash
npm install @langchain/langgraph-sdk
# or
pnpm add @langchain/langgraph-sdk
```

### Step 1: Check Existing Setup

Most Next.js apps with LangGraph already have `useStream` configured. Check your stream provider:

```typescript
// src/providers/Stream.tsx
import { useStream } from "@langchain/langgraph-sdk/react";

const stream = useStream({
  apiUrl: "http://localhost:2024",
  assistantId: "agent",
  // ... other config
});
```

### Step 2: Add UI Message Handling

Update your stream provider to handle UI messages:

```typescript
// src/providers/Stream.tsx
import { useStream } from "@langchain/langgraph-sdk/react";
import {
  uiMessageReducer,
  isUIMessage,
  isRemoveUIMessage,
  type UIMessage
} from "@langchain/langgraph-sdk/react-ui";

export function StreamProvider({ children }) {
  const stream = useStream<
    { messages: Message[]; ui?: UIMessage[] },
    {
      UpdateType: {
        messages?: Message[] | Message | string;
        ui?: (UIMessage | RemoveUIMessage)[] | UIMessage | RemoveUIMessage;
      };
      CustomEventType: UIMessage | RemoveUIMessage;
    }
  >({
    apiUrl: process.env.NEXT_PUBLIC_API_URL,
    assistantId: process.env.NEXT_PUBLIC_ASSISTANT_ID,
    messagesKey: "messages",

    // Add this handler for UI messages
    onCustomEvent: (event, options) => {
      if (isUIMessage(event) || isRemoveUIMessage(event)) {
        options.mutate((prev) => {
          const ui = uiMessageReducer(prev.ui ?? [], event);
          return { ...prev, ui };
        });
      }
    },
  });

  return (
    <StreamContext.Provider value={stream}>
      {children}
    </StreamContext.Provider>
  );
}
```

### Step 3: Add Component Rendering

Update your message components to render UI:

```typescript
// src/components/thread/messages/ai.tsx
import { LoadExternalComponent } from "@langchain/langgraph-sdk/react-ui";
import { useStreamContext } from "@/providers/Stream";
import type { Message } from "@langchain/langgraph-sdk";

export function AssistantMessage({
  message,
  isLoading,
  handleRegenerate
}: {
  message: Message;
  isLoading: boolean;
  handleRegenerate?: () => void;
}) {
  const stream = useStreamContext();

  return (
    <div className="assistant-message">
      {/* Existing message content */}
      <div className="message-content">
        {typeof message.content === 'string'
          ? message.content
          : JSON.stringify(message.content)}
      </div>

      {/* NEW: Render custom UI components */}
      {stream.values?.ui
        ?.filter((ui) => ui.metadata?.message_id === message.id)
        .map((ui) => (
          <div key={ui.id} className="custom-component">
            <LoadExternalComponent
              stream={stream.thread}
              message={ui}
              fallback={
                <div className="loading-skeleton">
                  <div className="shimmer" />
                  Loading component...
                </div>
              }
            />
          </div>
        ))}
    </div>
  );
}
```

### Step 4: Optional - Client-Side Components

For better performance, provide pre-loaded components:

```typescript
// src/components/thread/messages/ai.tsx
import { LoadExternalComponent } from "@langchain/langgraph-sdk/react-ui";
import WeatherCard from "@/components/custom-ui/WeatherCard";
import ImageViewer from "@/components/custom-ui/ImageViewer";

const clientComponents = {
  weather_card: WeatherCard,
  image_viewer: ImageViewer,
};

export function AssistantMessage({ message }) {
  const stream = useStreamContext();

  return (
    <div className="assistant-message">
      <div className="message-content">{message.content}</div>

      {stream.values?.ui
        ?.filter((ui) => ui.metadata?.message_id === message.id)
        .map((ui) => (
          <LoadExternalComponent
            key={ui.id}
            stream={stream.thread}
            message={ui}
            components={clientComponents}  // Pre-loaded
            fallback={<div>Loading...</div>}
          />
        ))}
    </div>
  );
}
```

### Step 5: Configure Backend

Update your LangGraph configuration:

```json
// langgraph.json
{
  "python_version": "3.11",
  "graphs": {
    "agent": "./src/agent.py:graph"
  },
  "ui": {
    "agent": "./ui/components.tsx"
  },
  "env": ".env"
}
```

Create UI components file:

```tsx
// ui/components.tsx
import WeatherCard from './WeatherCard';
import ImageViewer from './ImageViewer';

export default {
  weather_card: WeatherCard,
  image_viewer: ImageViewer,
};
```

## Integrating with React App (Non-Next.js)

### Step 1: Install Dependencies

```bash
npm install @langchain/langgraph-sdk
```

### Step 2: Create Stream Provider

```typescript
// src/providers/StreamProvider.tsx
import React, { createContext, useContext } from 'react';
import { useStream } from '@langchain/langgraph-sdk/react';
import {
  uiMessageReducer,
  isUIMessage,
  isRemoveUIMessage,
} from '@langchain/langgraph-sdk/react-ui';

const StreamContext = createContext(null);

export function StreamProvider({ children, apiUrl, assistantId }) {
  const stream = useStream({
    apiUrl,
    assistantId,
    messagesKey: 'messages',
    onCustomEvent: (event, options) => {
      if (isUIMessage(event) || isRemoveUIMessage(event)) {
        options.mutate((prev) => {
          const ui = uiMessageReducer(prev.ui ?? [], event);
          return { ...prev, ui };
        });
      }
    },
  });

  return (
    <StreamContext.Provider value={stream}>
      {children}
    </StreamContext.Provider>
  );
}

export const useStreamContext = () => {
  const context = useContext(StreamContext);
  if (!context) {
    throw new Error('useStreamContext must be used within StreamProvider');
  }
  return context;
};
```

### Step 3: Use in App

```typescript
// src/App.tsx
import { StreamProvider } from './providers/StreamProvider';
import ChatInterface from './components/ChatInterface';

function App() {
  return (
    <StreamProvider
      apiUrl="http://localhost:2024"
      assistantId="agent"
    >
      <ChatInterface />
    </StreamProvider>
  );
}
```

### Step 4: Render Messages

```typescript
// src/components/ChatInterface.tsx
import { LoadExternalComponent } from '@langchain/langgraph-sdk/react-ui';
import { useStreamContext } from '../providers/StreamProvider';

export default function ChatInterface() {
  const { thread, values, submit, isLoading } = useStreamContext();

  return (
    <div className="chat-interface">
      <div className="messages">
        {thread.messages.map((message) => (
          <div key={message.id} className="message">
            <div className="content">{message.content}</div>

            {/* Render UI components */}
            {values.ui
              ?.filter((ui) => ui.metadata?.message_id === message.id)
              .map((ui) => (
                <LoadExternalComponent
                  key={ui.id}
                  stream={thread}
                  message={ui}
                />
              ))}
          </div>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          const input = new FormData(e.currentTarget).get('message');
          submit({ messages: [{ type: 'human', content: input }] });
          e.currentTarget.reset();
        }}
      >
        <input name="message" disabled={isLoading} />
        <button type="submit" disabled={isLoading}>
          Send
        </button>
      </form>
    </div>
  );
}
```

## Migration from Plain Chat

### Before (Plain Text)

```typescript
function ChatMessage({ message }) {
  return (
    <div className="message">
      {message.content}
    </div>
  );
}
```

### After (With Generative UI)

```typescript
import { LoadExternalComponent } from '@langchain/langgraph-sdk/react-ui';
import { useStreamContext } from '@/providers/Stream';

function ChatMessage({ message }) {
  const stream = useStreamContext();

  return (
    <div className="message">
      {/* Text content */}
      <div className="text-content">{message.content}</div>

      {/* Custom UI components */}
      {stream.values?.ui
        ?.filter((ui) => ui.metadata?.message_id === message.id)
        .map((ui) => (
          <LoadExternalComponent
            key={ui.id}
            stream={stream.thread}
            message={ui}
          />
        ))}
    </div>
  );
}
```

## Environment Variables

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=agent
NEXT_PUBLIC_API_KEY=optional_key_here
```

### Backend (.env)

```bash
# Python
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Optional
LANGSMITH_API_KEY=your_key_here
LANGSMITH_TRACING=true
```

## Deployment

### Vercel (Next.js)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

**Environment Variables in Vercel:**
- Add `NEXT_PUBLIC_API_URL` with production LangGraph URL
- Add `NEXT_PUBLIC_ASSISTANT_ID`

### LangGraph Cloud

```bash
# Install LangGraph CLI
pip install langgraph-cli

# Deploy
langgraph deploy
```

**Get Deployment URL:**
```bash
langgraph deployments list
```

Update frontend env:
```bash
NEXT_PUBLIC_API_URL=https://your-deployment.langgraph.app
```

## Troubleshooting

### Components Not Rendering

**Problem:** UI components don't appear

**Solution:**
1. Check `onCustomEvent` is configured:
   ```typescript
   onCustomEvent: (event, options) => {
     if (isUIMessage(event) || isRemoveUIMessage(event)) {
       options.mutate((prev) => {
         const ui = uiMessageReducer(prev.ui ?? [], event);
         return { ...prev, ui };
       });
     }
   }
   ```

2. Verify backend emits UI messages:
   ```python
   push_ui_message("component_name", props, message=message)
   ```

3. Check component name matches:
   ```typescript
   // Backend: "weather_card"
   // Frontend export: { weather_card: WeatherCard }
   ```

### CORS Issues

**Problem:** Cannot connect to LangGraph server

**Solution:**
```typescript
// Add credentials to useStream
const stream = useStream({
  apiUrl: "http://localhost:2024",
  assistantId: "agent",
  // Add this for CORS
  fetchOptions: {
    mode: 'cors',
    credentials: 'include',
  }
});
```

### Loading State Stuck

**Problem:** Components show "Loading..." forever

**Solution:**
1. Check network tab for failed requests
2. Verify component export matches name
3. Add error fallback:
   ```typescript
   <LoadExternalComponent
     stream={thread}
     message={ui}
     fallback={<div>Loading...</div>}
     onError={(error) => {
       console.error('Component load failed:', error);
       return <div>Failed to load component</div>;
     }}
   />
   ```

### Type Errors

**Problem:** TypeScript errors with `useStream`

**Solution:**
```typescript
import type { Message } from "@langchain/langgraph-sdk";
import type { UIMessage } from "@langchain/langgraph-sdk/react-ui";

const stream = useStream<
  { messages: Message[]; ui?: UIMessage[] },  // State type
  {
    UpdateType: {
      messages?: Message[] | Message | string;
      ui?: (UIMessage | RemoveUIMessage)[] | UIMessage | RemoveUIMessage;
    };
    CustomEventType: UIMessage | RemoveUIMessage;
  }
>({
  // ... config
});
```

## Testing

### Unit Tests

```typescript
import { render, screen } from '@testing-library/react';
import { StreamProvider } from './providers/StreamProvider';
import ChatInterface from './components/ChatInterface';

jest.mock('@langchain/langgraph-sdk/react', () => ({
  useStream: () => ({
    thread: { messages: [] },
    values: { ui: [] },
    submit: jest.fn(),
    isLoading: false,
  }),
}));

test('renders chat interface', () => {
  render(
    <StreamProvider apiUrl="http://localhost:2024" assistantId="agent">
      <ChatInterface />
    </StreamProvider>
  );

  expect(screen.getByRole('textbox')).toBeInTheDocument();
});
```

### Integration Tests

```typescript
import { test, expect } from '@playwright/test';

test('displays custom UI component', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Type message
  await page.fill('input[name="message"]', 'Show weather');
  await page.click('button[type="submit"]');

  // Wait for UI component
  await page.waitForSelector('.weather-card');

  // Verify component rendered
  expect(await page.textContent('.weather-card')).toContain('San Francisco');
});
```

## Performance Optimization

### 1. Code Splitting

```typescript
// Lazy load components
const WeatherCard = lazy(() => import('./components/WeatherCard'));

<Suspense fallback={<div>Loading...</div>}>
  <WeatherCard {...props} />
</Suspense>
```

### 2. Memoization

```typescript
import { memo } from 'react';

export default memo(function CustomComponent({ data }) {
  // Component will only re-render when data changes
});
```

### 3. Virtualization

```typescript
import { VirtualList } from 'react-virtual';

// For large lists of messages
<VirtualList
  items={messages}
  renderItem={(message) => <ChatMessage message={message} />}
/>
```

## Next Steps

- **[06-examples.md](06-examples.md)**: Complete working examples
- **[07-troubleshooting.md](07-troubleshooting.md)**: Common issues and solutions
