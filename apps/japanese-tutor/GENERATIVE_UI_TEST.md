# LangGraph Generative UI - Test Implementation

## Overview

Successfully implemented a simple test component to verify the LangGraph Generative UI pipeline works end-to-end.

## What Was Implemented

### 1. Backend Changes

**File: `src/japanese_agent/state/schemas.py`**
- Added `ui` field to `JapaneseAgentState` with `ui_message_reducer`
- Added `ui: []` to initial state
- Imported necessary types: `Sequence`, `AnyUIMessage`, `ui_message_reducer`

**File: `src/japanese_agent/graph.py`**
- Added imports: `push_ui_message`, `uuid`
- Created `test_ui_node()` function that emits a "hello_card" component
- Added test_ui node to graph between preprocess_images and chatbot
- Graph flow: START → preprocess_images → test_ui → chatbot → tools/END

### 2. Frontend Changes

**File: `apps/agent-chat-ui/src/components/custom/HelloCard.tsx`** (NEW)
- Simple React component that displays:
  - Greeting message
  - Test data
  - Timestamp
- Styled with TailwindCSS classes

**File: `apps/agent-chat-ui/src/components/custom/index.ts`** (NEW)
- Component registry that maps component names to React components
- Exports `customComponents` object with `hello_card` mapping

**File: `apps/agent-chat-ui/src/components/thread/messages/ai.tsx`** (MODIFIED)
- Added import for local component registry
- Modified `CustomComponent` function to check local registry first
- Falls back to `LoadExternalComponent` for external components

### 3. Architecture Decision

**Important:** UI components should be in the **frontend app** (agent-chat-ui), not the backend!

- ❌ Backend serving components requires special build setup and langgraph-cli features still in development
- ✅ Frontend components are simpler, faster, and more maintainable
- Backend only emits UI message specifications via `push_ui_message()`
- Frontend renders components from local registry

## How It Works

1. **User sends a message** → LangGraph backend receives it
2. **preprocess_images** → Extracts any attached images
3. **test_ui** → Emits "hello_card" UI component via `push_ui_message()`
4. **chatbot** → Processes the message normally
5. **Frontend** → Receives UI message via SSE stream
6. **LoadExternalComponent** → Renders HelloCard.tsx
7. **Result** → Blue card appears in chat with greeting and timestamp

## Testing Instructions

### Step 1: Start Backend

```bash
cd apps/japanese-tutor
langgraph dev
```

Expected output:
```
Ready!
- API: http://localhost:2024
- LangGraph Studio: https://smith.langchain.com/studio/?baseUrl=http://localhost:2024
```

### Step 2: Start Frontend

```bash
cd apps/agent-chat-ui
npm run dev
```

Expected output:
```
ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

### Step 3: Configure Agent Chat UI

1. Open http://localhost:3000
2. Enter configuration:
   - **Deployment URL**: `http://localhost:2024`
   - **Assistant / Graph ID**: `japanese_agent`
   - **API Key**: (leave empty for local server)
3. Click "Continue"

### Step 4: Send Test Message

1. Type any message in the chat input (e.g., "Hello")
2. Press Enter or click "Send"

### Step 5: Verify UI Component

**Expected Result:**
You should see TWO things in the chat:
1. ✅ A **blue card** with:
   - "Hello from LangGraph Generative UI!"
   - Test data message
   - Timestamp
2. ✅ Regular AI response text below the card

**What to Check:**
- [ ] Blue card appears above the text response
- [ ] Timestamp shows current date/time
- [ ] Card has rounded corners and shadow
- [ ] Card is properly styled and readable

## Troubleshooting

### Component Not Rendering

**Check Backend Logs:**
```bash
# Terminal running langgraph dev
# Should see: "Pushing UI: hello_card"
```

**Check Browser Console:**
```javascript
// Open DevTools → Console
// Should see custom event logs if you added debug logging
```

**Verify langgraph.json:**
```bash
cd apps/japanese-tutor
cat langgraph.json
# Should have "ui": {"japanese_agent": "./ui/components.tsx"}
```

### CORS Errors

If you see CORS errors in browser console:

**Add to `langgraph.json`:**
```json
{
  "cors": {
    "allowed_origins": ["http://localhost:3000"]
  }
}
```

Then restart backend: `langgraph dev`

### Component Loading Forever

**Check Network Tab:**
1. Open DevTools → Network
2. Filter: "components"
3. Look for request to load component bundle
4. Check if it's returning 200 OK

**Verify File Paths:**
```bash
ls apps/japanese-tutor/ui/
# Should see: HelloCard.tsx, components.tsx
```

### TypeScript Errors

If frontend shows TypeScript errors:

```bash
cd apps/agent-chat-ui
npm install @langchain/langgraph-sdk@latest
npm run dev
```

## Next Steps

Once the simple component works, gradually add more features:

### Phase 1: Screenshot Display
- Modify test_ui_node to emit base64-encoded images
- Create ImageCard.tsx component
- Test screenshot display

### Phase 2: Vocabulary Cards
- Create VocabularyCard.tsx component
- Show word, reading, meaning
- Add study status indicator

### Phase 3: Interactive Flashcards
- Create Flashcard.tsx component
- Add flip animation (CSS transforms)
- Use `useStreamContext()` to submit ratings back to agent

### Phase 4: Gallery View
- Create Gallery.tsx component
- Display multiple screenshots in responsive grid
- Add click to expand functionality

## Architecture Notes

**Data Flow:**
```
Python Node
    ↓ push_ui_message("hello_card", {...})
SSE Stream
    ↓ CustomEvent: UIMessage
onCustomEvent Handler
    ↓ uiMessageReducer(prev.ui, event)
State Update
    ↓ stream.values.ui
CustomComponent
    ↓ LoadExternalComponent
HelloCard.tsx Renders
```

**Key Components:**
- **Backend**: `push_ui_message()` emits UI specifications
- **Stream**: SSE transports UI messages to frontend
- **Reducer**: `uiMessageReducer` accumulates UI state
- **Renderer**: `LoadExternalComponent` dynamically loads and renders React components
- **Props**: Component receives props from backend via `message.props`

## Files Modified

### Backend (japanese-tutor)
- ✅ `src/japanese_agent/state/schemas.py` (added ui field, imports)
- ✅ `src/japanese_agent/graph.py` (added test_ui_node, graph flow)

### Frontend (agent-chat-ui)
- ✅ `src/components/thread/messages/ai.tsx` (local component rendering)

## Files Created

### Backend (japanese-tutor)
- ✅ `GENERATIVE_UI_TEST.md` (this file)

### Frontend (agent-chat-ui)
- ✅ `src/components/custom/HelloCard.tsx` (test component)
- ✅ `src/components/custom/index.ts` (component registry)

## Documentation

For comprehensive guides on LangGraph Generative UI:
- **Architecture**: `ai_docs/ai-ml/langgraphjs-gen-ui/01-architecture.md`
- **Python Guide**: `ai_docs/ai-ml/langgraphjs-gen-ui/02-python-implementation.md`
- **React Guide**: `ai_docs/ai-ml/langgraphjs-gen-ui/04-react-components.md`
- **Examples**: `ai_docs/ai-ml/langgraphjs-gen-ui/06-examples.md`
- **Troubleshooting**: `ai_docs/ai-ml/langgraphjs-gen-ui/07-troubleshooting.md`

## Skill Usage

To get help implementing more complex UI components:

```
Use the langgraph-gen-ui skill
```

The skill provides interactive workflows for:
- Starting from scratch with new components
- Adding components to existing agents
- Implementing specific patterns (gallery, flashcards, forms, charts)
- Learning architecture and best practices
