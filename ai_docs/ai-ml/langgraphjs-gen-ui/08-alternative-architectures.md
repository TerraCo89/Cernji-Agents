# Alternative Generative UI Architectures

## Overview

This document presents alternative approaches to implementing generative UI in LangGraph applications, based on the [gen-ui-python](https://github.com/bracesproul/gen-ui-python) reference implementation. This architecture differs from the official LangGraph Generative UI pattern and offers valuable insights for different use cases.

## Architecture Comparison

### Official LangGraph Pattern (Documented in 01-architecture.md)

**Backend:** Python LangGraph with `push_ui_message()` and `ui_message_reducer`
**Frontend:** Next.js with `LoadExternalComponent` (Shadow DOM)
**Communication:** SSE streaming with UI specifications
**Component Loading:** External bundles via LangGraph Platform

### Alternative Pattern (gen-ui-python)

**Backend:** Python LangGraph with LangServe + FastAPI
**Frontend:** Next.js with Vercel AI SDK
**Communication:** HTTP streaming via RemoteRunnable
**Component Loading:** Client-side pre-registered components

## Key Architectural Differences

### 1. Component Specification vs. Data Return

**Official Pattern:**
```python
# Backend emits UI component specifications
from langgraph.graph.ui import push_ui_message

push_ui_message("weather_card", {
    "city": "SF",
    "temp": 72
}, message=message)
```

**Alternative Pattern:**
```python
# Backend returns structured data directly
from langchain_core.tools import tool

@tool("weather-data", return_direct=True)
def weather_data(city: str) -> dict:
    """Get weather data."""
    return {
        "city": city,
        "temperature": 72,
        "conditions": "Sunny"
    }
```

**Key Difference:** The alternative pattern uses `return_direct=True` on tools, bypassing intermediate processing and returning tool output directly to the client.

### 2. Server Actions vs. useStream Hook

**Official Pattern:**
```typescript
// Client-side hook manages connection
const { thread, values } = useStream({
  apiUrl: "http://localhost:2024",
  assistantId: "agent",
});
```

**Alternative Pattern:**
```typescript
// Server action wraps backend connection
"use server";

async function agent(inputs: AgentInputs) {
  const remoteRunnable = new RemoteRunnable({
    url: "http://localhost:8000/chat"
  });

  return streamRunnableUI(remoteRunnable, inputs);
}
```

**Key Difference:** Alternative pattern uses Next.js Server Actions for secure API communication, keeping credentials server-side.

### 3. Component Rendering Strategies

**Official Pattern:**
```typescript
// LoadExternalComponent fetches from LangGraph Platform
<LoadExternalComponent
  stream={thread}
  message={ui}
/>
```

**Alternative Pattern:**
```typescript
// Tool-to-component mapping with pre-loaded components
const TOOL_COMPONENT_MAP = {
  "weather-data": {
    loading: WeatherLoading,
    final: WeatherCard,
  }
};

// Progressive rendering: loading → final
const toolUI = createStreamableUI(<toolMap[name].loading />);
// Later...
toolUI.done(<toolMap[name].final {...data} />);
```

**Key Difference:** Alternative pattern provides both loading and final states for smooth progressive rendering without external fetches.

## Reference Implementation: gen-ui-python

### Project Structure

```
gen-ui-python/
├── backend/                     # Python FastAPI + LangServe
│   ├── gen_ui_backend/
│   │   ├── chain.py            # Main LangGraph workflow
│   │   ├── server.py           # FastAPI server setup
│   │   ├── tools/              # LangChain tools
│   │   │   ├── github.py
│   │   │   ├── weather.py
│   │   │   └── invoice.py
│   │   └── charts/             # Complex workflow example
│   │       ├── chain.py
│   │       └── schema.py
│   ├── pyproject.toml          # Poetry dependencies
│   └── langgraph.json          # LangGraph config
│
└── frontend/                    # Next.js 15 + React 19
    ├── app/
    │   ├── agent.tsx           # Server action (backend proxy)
    │   └── page.tsx            # Main chat page
    ├── components/
    │   ├── prebuilt/           # Custom UI components
    │   │   ├── github.tsx
    │   │   ├── weather.tsx
    │   │   ├── invoice.tsx
    │   │   └── chat.tsx
    │   └── ui/                 # Shadcn UI components (21 total)
    └── package.json
```

### Tech Stack

**Backend:**
- Python 3.9-3.11 (not 3.12 due to dependency constraints)
- LangChain Core 0.2.4
- LangGraph 0.0.62
- FastAPI + Uvicorn
- LangServe 0.2.1 (automatic streaming endpoints)
- Pydantic v1 (<2.0)

**Frontend:**
- Next.js 15 (App Router with React Server Components)
- TypeScript 80.8% of codebase
- Vercel AI SDK 3.1.16 (`createStreamableUI`, `createStreamableValue`)
- LangChain SDK (@langchain/core, @langchain/langgraph-sdk)
- Shadcn UI + Radix UI
- Tailwind CSS

### Backend Implementation Patterns

#### 1. State Definition

```python
from typing import List, Optional, TypedDict
from langchain_core.messages import HumanMessage

class GenerativeUIState(TypedDict):
    input: HumanMessage
    result: Optional[str]
    """Plain text response if no tool was used."""
    tool_calls: Optional[List[dict]]
    """A list of parsed tool calls."""
    tool_result: Optional[dict]
    """The result of a tool call."""
```

**Key Pattern:** Use `TypedDict` with optional fields (`total=False`) for flexible state updates.

#### 2. LangGraph Workflow

```python
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.output_parsers.openai_tools import JsonOutputToolsParser

def invoke_model(state: GenerativeUIState, config: RunnableConfig):
    """Process messages and detect tool calls."""
    model = ChatOpenAI(model="gpt-4o", temperature=0, streaming=True)
    tools = [github_repo, invoice_parser, weather_data]
    model_with_tools = model.bind_tools(tools)

    result = chain.invoke({"input": state["input"]}, config)

    if result.tool_calls:
        return {"tool_calls": tools_parser.invoke(result)}
    else:
        return {"result": str(result.content)}

def invoke_tools(state: GenerativeUIState):
    """Execute selected tool."""
    tools_map = {
        "github-repo": github_repo,
        "weather-data": weather_data,
    }

    tool = state["tool_calls"][0]
    selected_tool = tools_map[tool["type"]]
    return {"tool_result": selected_tool.invoke(tool["args"])}

def invoke_tools_or_return(state: GenerativeUIState) -> str:
    """Route to tools or end."""
    if "result" in state:
        return END
    elif "tool_calls" in state:
        return "invoke_tools"
    else:
        raise ValueError("Invalid state")

# Build graph
workflow = StateGraph(GenerativeUIState)
workflow.add_node("invoke_model", invoke_model)
workflow.add_node("invoke_tools", invoke_tools)
workflow.add_conditional_edges("invoke_model", invoke_tools_or_return)
workflow.set_entry_point("invoke_model")
workflow.set_finish_point("invoke_tools")

graph = workflow.compile()
```

**Key Pattern:** Three-function workflow: `invoke_model` → conditional routing → `invoke_tools` or END.

#### 3. Tool Definition with Structured Output

```python
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool

class GithubRepoInput(BaseModel):
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")

@tool("github-repo", args_schema=GithubRepoInput, return_direct=True)
def github_repo(owner: str, repo: str) -> dict:
    """Get GitHub repository information."""
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
    )

    if not response.ok:
        return f"Error: {response.status_code}"

    data = response.json()
    return {
        "owner": owner,
        "repo": repo,
        "description": data.get("description", ""),
        "stars": data.get("stargazers_count", 0),
        "language": data.get("language", ""),
    }
```

**Key Pattern:**
- `return_direct=True` bypasses additional processing
- Pydantic schema for type validation
- Return structured dict for UI consumption

#### 4. Complex Nested Schemas

```python
from typing import List, Optional
from uuid import uuid4

class LineItem(BaseModel):
    id: str = Field(default_factory=uuid4)
    name: str = Field(..., description="Name or description")
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)

class Invoice(BaseModel):
    """Parse an invoice. ALWAYS call if image is provided."""
    orderId: str
    lineItems: List[LineItem]
    shippingAddress: Optional[ShippingAddress] = None
    customerInfo: Optional[CustomerInfo] = None
    paymentInfo: Optional[PaymentInfo] = None

@tool("invoice-parser", args_schema=Invoice, return_direct=True)
def invoice_parser(
    orderId: str,
    lineItems: List[LineItem],
    shippingAddress: Optional[ShippingAddress],
    customerInfo: Optional[CustomerInfo],
    paymentInfo: Optional[PaymentInfo],
) -> Invoice:
    """Parse an invoice and return without modification."""
    return Invoice(
        orderId=orderId,
        lineItems=lineItems,
        shippingAddress=shippingAddress,
        customerInfo=customerInfo,
        paymentInfo=paymentInfo,
    )
```

**Key Pattern:**
- Nested Pydantic models for complex structured extraction
- LLM populates all fields from image/text
- Validation happens at schema level

#### 5. FastAPI + LangServe Server

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
import uvicorn

app = FastAPI(
    title="Gen UI Backend",
    version="1.0",
    description="API using Langchain's Runnable interfaces"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create graph and add type contracts
graph = create_graph()
runnable = graph.with_types(
    input_type=ChatInputType,
    output_type=dict
)

# Expose as /chat endpoint with automatic streaming
add_routes(
    app,
    runnable,
    path="/chat",
    playground_type="chat"  # Built-in testing UI
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Key Pattern:** LangServe's `add_routes()` automatically creates:
- `POST /chat/invoke` - Single invocation
- `POST /chat/stream` - SSE streaming
- `GET /chat/playground` - Interactive testing UI

### Frontend Implementation Patterns

#### 1. Server Action (Secure API Proxy)

```typescript
"use server";

import { RemoteRunnable } from "@langchain/core/runnables/remote";
import { createStreamableUI, createStreamableValue } from "ai/rsc";

async function agent(inputs: {
  input: string;
  chat_history: [role: string, content: string][];
  file?: { base64: string; extension: string; };
}) {
  const remoteRunnable = new RemoteRunnable({
    url: "http://localhost:8000/chat"
  });

  // Format messages for LangChain
  const messages = inputs.chat_history.map(([role, content]) => ({
    type: role,
    content,
  }));
  messages.push({ type: "human", content: inputs.input });

  // Stream with custom event handlers
  return streamRunnableUI(remoteRunnable, { input: messages }, {
    onInvokeModelEvent: handleToolDetection,
    onInvokeToolsEvent: handleToolResults,
    onChatModelStreamEvent: handleTextStream,
  });
}
```

**Key Pattern:**
- `"use server"` directive runs code securely on server
- API keys never exposed to client
- `RemoteRunnable` connects to Python backend

#### 2. Tool-to-Component Mapping

```typescript
import { GithubLoading, Github } from "@/components/prebuilt/github";
import { WeatherLoading, Weather } from "@/components/prebuilt/weather";

const TOOL_COMPONENT_MAP: ToolComponentMap = {
  "github-repo": {
    loading: GithubLoading,
    final: Github,
  },
  "weather-data": {
    loading: WeatherLoading,
    final: Weather,
  },
  "invoice-parser": {
    loading: InvoiceLoading,
    final: Invoice,
  },
};
```

**Key Pattern:** Centralized registry mapping tool names to loading + final components.

#### 3. Event Handlers for Progressive Rendering

```typescript
function handleInvokeModelEvent(event: StreamEvent) {
  const toolCalls = event.data?.output?.tool_calls || [];

  if (toolCalls.length > 0) {
    const toolName = toolCalls[0].name; // "weather-data"
    const component = TOOL_COMPONENT_MAP[toolName];

    // Create streamable UI with loading skeleton
    const ui = createStreamableUI(<component.loading />);

    return { ui, toolName };
  }
}

function handleInvokeToolsEvent(event: StreamEvent, selectedToolUI) {
  const toolResult = event.data?.output;
  const component = TOOL_COMPONENT_MAP[selectedToolUI.toolName];

  // Update from loading to final state
  selectedToolUI.ui.done(<component.final {...toolResult} />);
}

function handleTextStream(event: StreamEvent, textStreams) {
  const runId = event.run_id;

  if (!textStreams[runId]) {
    textStreams[runId] = createStreamableValue("");
    // Append to UI
  }

  const chunk = event.data?.chunk?.content || "";
  textStreams[runId].append(chunk);

  if (event.event === "on_chat_model_end") {
    textStreams[runId].done();
  }
}
```

**Key Pattern:** Three-phase event handling:
1. Tool detection → Show loading UI
2. Tool completion → Show final UI with data
3. Text streaming → Progressive text updates

#### 4. Chat Component with State Management

```typescript
"use client";

import { useState } from "react";
import { useActions } from "ai/rsc";

export function Chat() {
  const [elements, setElements] = useState<JSX.Element[]>([]);
  const [history, setHistory] = useState<[string, string][]>([]);
  const [input, setInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const { agent } = useActions<typeof EndpointsContext>();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Convert file to base64 if present
    let fileData;
    if (selectedFile) {
      const base64 = await convertFileToBase64(selectedFile);
      fileData = { base64, extension: selectedFile.name.split('.').pop()! };
    }

    // Display user message
    setElements(prev => [
      ...prev,
      <HumanMessage content={input} key={Date.now()} />
    ]);

    // Call server action
    const result = await agent({
      input,
      chat_history: history,
      file: fileData,
    });

    // Wait for stream completion
    const lastEvent = await result.lastEvent;

    // Update history based on event type
    if (lastEvent.event === "invoke_model") {
      setHistory(prev => [
        ...prev,
        ["human", input],
        ["ai", lastEvent.invoke_model.result]
      ]);
    } else if (lastEvent.event === "invoke_tools") {
      setHistory(prev => [
        ...prev,
        ["human", input],
        ["tool", JSON.stringify(lastEvent.invoke_tools.tool_result)]
      ]);
    }

    // Render AI response
    setElements(prev => [...prev, result.ui]);

    // Clear form
    setInput("");
    setSelectedFile(null);
  };

  return (
    <div>
      <div className="messages">{elements}</div>

      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
        />
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
```

**Key Pattern:**
- `elements` state for rendered UI
- `history` state for conversation context
- File upload with base64 encoding
- Wait for `result.lastEvent` before updating history

#### 5. Dual Component Pattern (Loading + Final)

```typescript
// Loading skeleton
export function GithubLoading() {
  return (
    <Card className="w-full max-w-[700px]">
      <CardHeader>
        <Skeleton className="h-4 w-[250px]" />
        <Skeleton className="h-4 w-[200px]" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-10 w-[100px]" />
      </CardContent>
    </Card>
  );
}

// Final component
export interface GithubProps {
  owner: string;
  repo: string;
  description: string;
  stars: number;
  language: string;
}

export function Github({ owner, repo, description, stars, language }: GithubProps) {
  return (
    <Card className="w-full max-w-[700px]">
      <CardHeader>
        <CardTitle>{owner}/{repo}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <Button asChild>
          <a href={`https://github.com/${owner}/${repo}`}>
            <StarIcon className="mr-2" />
            Star
          </a>
        </Button>
        <div className="flex gap-4 mt-4">
          <div className="flex items-center gap-2">
            <CircleIcon className="fill-sky-400" />
            <span>{language}</span>
          </div>
          <div>{stars.toLocaleString()} stars</div>
        </div>
      </CardContent>
    </Card>
  );
}
```

**Key Pattern:**
- Loading and final components have identical layout dimensions
- Skeleton elements match final content structure
- Smooth transition without layout shift

#### 6. Complex Component with Dynamic Calculations

```typescript
export interface InvoiceProps {
  orderId: string;
  lineItems: LineItem[];
  shippingAddress?: ShippingAddress;
  customerInfo?: CustomerInfo;
  paymentInfo?: PaymentInfo;
}

export function Invoice({ orderId, lineItems, shippingAddress, customerInfo, paymentInfo }: InvoiceProps) {
  const [subtotal, setSubtotal] = useState(0);
  const [shipping] = useState(5.0);
  const [tax, setTax] = useState(0);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const sub = lineItems.reduce((acc, item) => acc + item.price * item.quantity, 0);
    setSubtotal(sub);

    const taxAmount = parseFloat((sub * 0.075).toFixed(2));
    setTax(taxAmount);

    setTotal(sub + shipping + taxAmount);
  }, [lineItems]);

  return (
    <Card className="w-full max-w-[700px]">
      <CardHeader>
        <CardTitle>Invoice #{orderId}</CardTitle>
        <Button onClick={() => navigator.clipboard.writeText(orderId)}>
          Copy Order ID
        </Button>
      </CardHeader>
      <CardContent>
        {/* Line Items */}
        <ul className="space-y-2">
          {lineItems.map((item) => (
            <li key={item.id} className="flex justify-between">
              <span>{item.name} x {item.quantity}</span>
              <span>${(item.price * item.quantity).toFixed(2)}</span>
            </li>
          ))}
        </ul>

        {/* Price Breakdown */}
        <Separator className="my-4" />
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>Subtotal</span>
            <span>${subtotal.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span>Shipping</span>
            <span>${shipping.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span>Tax (7.5%)</span>
            <span>${tax.toFixed(2)}</span>
          </div>
          <Separator />
          <div className="flex justify-between font-bold text-lg">
            <span>Total</span>
            <span>${total.toFixed(2)}</span>
          </div>
        </div>

        {/* Conditional Sections */}
        {shippingAddress && (
          <div className="mt-4 border-t pt-2">
            <h3 className="font-semibold">Shipping Address</h3>
            <p>{shippingAddress.name}</p>
            <p>{shippingAddress.street}</p>
            <p>{shippingAddress.city}, {shippingAddress.state} {shippingAddress.zip}</p>
          </div>
        )}

        {customerInfo && (
          <div className="mt-4 border-t pt-2">
            <h3 className="font-semibold">Customer Info</h3>
            <p>{customerInfo.name}</p>
            {customerInfo.email && <p>{customerInfo.email}</p>}
            {customerInfo.phone && <p>{customerInfo.phone}</p>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

**Key Pattern:**
- `useEffect` for dynamic calculations
- Conditional rendering for optional fields
- Interactive elements (copy to clipboard)

### Advanced Pattern: Multi-Node LangGraph Workflow

The gen-ui-python repository also demonstrates a sophisticated chart filtering workflow:

```python
# backend/gen_ui_backend/charts/chain.py

class AgentExecutorState(TypedDict, total=False):
    input: str
    display_formats: List[DataDisplayTypeAndDescription]
    orders: List[Order]
    selected_filters: Optional[Filter]
    chart_type: Optional[ChartType]
    display_format: Optional[str]
    props: Optional[dict]

def generate_filters(state: AgentExecutorState) -> dict:
    """Convert natural language to structured filters using LLM."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Convert user input to structured query filters."),
        ("human", "{input}"),
    ])

    # Dynamic schema based on available product names
    unique_products = list(set(order["productName"].lower() for order in state["orders"]))
    FilterSchema = filter_schema(unique_products)

    model = ChatOpenAI(model="gpt-4-turbo").with_structured_output(FilterSchema)
    result = (prompt | model).invoke(input=state["input"]["content"])

    return {"selected_filters": result}

def generate_chart_type(state: AgentExecutorState) -> dict:
    """LLM selects optimal chart type (bar, line, pie) based on filters."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert data analyst. Select the best chart type.
Available types: 'bar', 'line', 'pie'.
Data display types: {data_display_types}"""),
        ("human", "User input: {input}\nFilters: {filters}"),
    ])

    class ChartTypeSchema(BaseModel):
        chart_type: Literal["bar", "line", "pie"]

    model = ChatOpenAI(model="gpt-4-turbo").with_structured_output(ChartTypeSchema)
    result = (prompt | model).invoke(input={
        "input": state["input"],
        "filters": state["selected_filters"],
        "data_display_types": format_display_types(state["display_formats"]),
    })

    return {"chart_type": result.chart_type}

def generate_data_display_format(state: AgentExecutorState) -> dict:
    """Select specific display format key for the chart."""
    # LLM selects which data key to visualize
    # (e.g., "productName", "orderAmount", "orderStatus")
    pass

def filter_data(state: AgentExecutorState) -> dict:
    """Apply all filters to order dataset."""
    filters = state["selected_filters"]
    orders = state["orders"]

    filtered = []
    for order in orders:
        if filters.product_names and order.get("productName", "").lower() not in filters.product_names:
            continue
        if filters.before_date and order.get("orderedAt", "") > filters.before_date:
            continue
        if filters.after_date and order.get("orderedAt", "") < filters.after_date:
            continue
        # ... more conditions
        filtered.append(order)

    return {"orders": filtered}

# Build workflow
workflow = StateGraph(AgentExecutorState)
workflow.add_node("generate_filters", generate_filters)
workflow.add_node("generate_chart_type", generate_chart_type)
workflow.add_node("generate_data_display_format", generate_data_display_format)
workflow.add_node("filter_data", filter_data)

workflow.add_edge("generate_filters", "generate_chart_type")
workflow.add_edge("generate_chart_type", "generate_data_display_format")
workflow.add_edge("generate_data_display_format", "filter_data")

workflow.set_entry_point("generate_filters")
workflow.set_finish_point("filter_data")

graph = workflow.compile()
```

**Key Pattern:** Multi-node sequential processing where each node uses LLM for decision-making:
1. **NLP → Structured Filters** (GPT-4)
2. **Filter Analysis → Chart Type** (GPT-4)
3. **Chart Type → Display Format** (GPT-4)
4. **Apply Filters → Final Data** (deterministic)

## When to Use Which Pattern

### Use Official LangGraph Pattern When:

✅ Building on LangGraph Platform
✅ Need external component bundles
✅ Want Shadow DOM style isolation
✅ Deploying to LangGraph Cloud
✅ Using TypeScript backend

### Use Alternative Pattern When:

✅ Need Next.js Server Actions security
✅ Want client-side component pre-loading
✅ Prefer Vercel AI SDK patterns
✅ Building Vercel-hosted frontends
✅ Need flexible FastAPI backend
✅ Want `return_direct` tool pattern

## Best Practices from gen-ui-python

### 1. Dual Component Pattern

Always create both loading and final components:

```typescript
// Loading matches final layout
export function ComponentLoading() {
  return (
    <Card className="w-[450px]">
      <Skeleton className="h-4 w-[250px]" />
      <Skeleton className="h-4 w-[200px]" />
    </Card>
  );
}

export function Component(props: Props) {
  return (
    <Card className="w-[450px]">
      <CardTitle>{props.title}</CardTitle>
      <CardDescription>{props.description}</CardDescription>
    </Card>
  );
}
```

### 2. Type Safety Across Stack

Mirror types between Python and TypeScript:

```python
# Python
class WeatherProps(BaseModel):
    city: str
    temperature: int
    conditions: str
```

```typescript
// TypeScript
interface WeatherProps {
  city: string;
  temperature: number;
  conditions: string;
}
```

### 3. Tool Return Pattern

Use `return_direct=True` for final results:

```python
@tool("tool-name", args_schema=InputSchema, return_direct=True)
def tool_function(...) -> Union[Dict, str]:
    """Returns structured data for UI or error string."""
    try:
        return {"data": result}
    except Exception as e:
        return f"Error: {str(e)}"
```

### 4. Error Handling

Backend returns user-friendly error messages:

```python
try:
    response = requests.get(url)
    response.raise_for_status()
    return process_data(response.json())
except requests.exceptions.RequestException as err:
    print(err)  # Log technical details
    return "There was an error fetching data."  # User-friendly message
```

Frontend handles errors gracefully:

```typescript
export function Component({ data }: Props) {
  if (!data) {
    return <div>Data unavailable</div>;
  }

  return <Card>{/* Normal rendering */}</Card>;
}
```

### 5. Progressive Rendering

Show immediate feedback with loading states:

```typescript
// Phase 1: Show loading immediately
const toolUI = createStreamableUI(<ToolLoading />);
append(toolUI.value);

// Phase 2: Execute tool in background
const result = await executeTool(args);

// Phase 3: Update to final component
toolUI.done(<Tool {...result} />);
```

### 6. File Upload Pattern

Base64 encoding for image/file transmission:

```typescript
async function convertFileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = (reader.result as string).split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

// Usage
const fileData = {
  base64: await convertFileToBase64(selectedFile),
  extension: selectedFile.name.split('.').pop()!
};
```

## Performance Considerations

### LangServe Auto-Streaming

LangServe provides automatic streaming endpoints with no configuration:

```python
# Just call add_routes - streaming is automatic
add_routes(app, runnable, path="/chat", playground_type="chat")

# Creates:
# POST /chat/invoke   - Single invocation
# POST /chat/stream   - SSE streaming (automatic)
# POST /chat/batch    - Batch processing
# GET  /chat/playground - Testing UI
```

### Client-Side Component Pre-Loading

Pre-register components for instant rendering:

```typescript
const clientComponents = {
  weather: WeatherCard,
  github: GithubCard,
  invoice: InvoiceCard,
};

<LoadExternalComponent
  stream={thread}
  message={ui}
  components={clientComponents}  // No fetch needed
/>
```

### Memoization

Prevent unnecessary re-renders:

```typescript
export default memo(function ExpensiveComponent({ data }: Props) {
  const processed = useMemo(() => processData(data), [data]);
  return <div>{processed}</div>;
});
```

## Migration Path

### From Official Pattern to Alternative Pattern

1. **Backend:**
   - Keep LangGraph StateGraph
   - Replace `push_ui_message()` with `return_direct=True` tools
   - Add FastAPI + LangServe server
   - Use `add_routes()` for automatic streaming

2. **Frontend:**
   - Add Next.js Server Action for API proxy
   - Replace `useStream` with `useActions`
   - Create tool-to-component mapping
   - Implement dual component pattern (loading + final)
   - Use `createStreamableUI` for progressive rendering

3. **Components:**
   - Convert external components to client-side
   - Add loading states
   - Mirror TypeScript interfaces with Python Pydantic models

## Resources

### Reference Implementation
- **Repository**: https://github.com/bracesproul/gen-ui-python
- **Backend**: /backend/gen_ui_backend/
- **Frontend**: /frontend/

### Dependencies

**Backend (`pyproject.toml`):**
```toml
[tool.poetry.dependencies]
python = ">=3.9,<3.12"
langchain-core = "^0.2.4"
langchain = "^0.2.2"
langchain-openai = "^0.1.8"
langgraph = "^0.0.62"
langserve = "^0.2.1"
fastapi = ">=0.110.2,<1"
uvicorn = ">=0.23.2,<0.24.0"
pydantic = ">=1.10.13,<2"
```

**Frontend (`package.json`):**
```json
{
  "dependencies": {
    "next": "14.2.3",
    "react": "^18",
    "typescript": "^5",
    "ai": "3.1.16",
    "@langchain/core": "0.2.6",
    "@langchain/langgraph-sdk": "0.0.1-rc.14",
    "@radix-ui/react-*": "various",
    "tailwindcss": "^3.4.1"
  }
}
```

## Conclusion

The gen-ui-python reference implementation demonstrates a viable alternative to the official LangGraph Generative UI pattern, with key differences:

**Strengths:**
- Next.js Server Actions for secure API access
- Client-side component pre-loading for performance
- Vercel AI SDK patterns familiar to Next.js developers
- Dual component pattern for smooth UX
- `return_direct` tool pattern for simplicity

**Trade-offs:**
- Not using official `push_ui_message()` API
- Requires manual tool-to-component mapping
- Server Actions tied to Next.js
- No Shadow DOM style isolation

Both patterns are valid and production-ready. Choose based on your deployment environment, tech stack familiarity, and specific requirements.

---

**Last Updated**: 2025-01-05
**Trust Score**: 8.8
**Reference**: bracesproul/gen-ui-python (main branch)
