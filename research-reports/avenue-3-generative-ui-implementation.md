# Research Avenue 3: Generative UI Implementation

**Source**: https://github.com/bracesproul/gen-ui-python

## Executive Summary

The gen-ui-python repository demonstrates a **hybrid approach** to generative UI where:
- Python backend (LangGraph + LangChain) generates **structured data** and **metadata** about what UI to render
- TypeScript/React frontend uses this metadata to **select and render** pre-built React components
- Streaming is handled via **LangServe** (backend) and **Vercel AI SDK's RSC** (frontend)
- **NOT** true code generation - components are pre-built, agent just decides which to show and with what data

## Architecture Overview

### Stack
- **Backend**: Python 3.x, LangChain, LangGraph, LangServe, FastAPI
- **Frontend**: Next.js 15, React, TypeScript, Vercel AI SDK (ai/rsc), Shadcn UI
- **Communication**: HTTP with streaming via LangServe RemoteRunnable

### Pattern
```
User Input → LangGraph Agent → Tool Execution → Component Selection → Props Generation → Frontend Rendering
```

## 1. UI Component Schema/Types in Python

### Backend Python Schemas (Pydantic)

```python
from pydantic import BaseModel
from typing import List, Union, Literal, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Chart visualization types
ChartType = Literal["bar", "line", "pie"]

# Chart metadata
class DataDisplayTypeAndDescription(BaseModel):
    """Schema for chart display configuration"""
    title: str  # Title of the data display
    chartType: ChartType  # Type of chart (bar/line/pie)
    description: str  # Description of what this display shows
    key: str  # Unique identifier for this display format

# Order data structure
class Address(BaseModel):
    street: str
    city: str
    state: str
    zip: str

class Order(BaseModel):
    id: str
    productName: str
    amount: float
    discount: Optional[float]  # 0-100 percentage
    address: Address
    status: Literal["pending", "processing", "shipped", "delivered", "cancelled", "returned"]
    orderedAt: str  # YYYY-MM-DD format

# Filter criteria
class Filter(BaseModel):
    productNames: Optional[List[str]] = None
    beforeDate: Optional[str] = None  # YYYY-MM-DD
    afterDate: Optional[str] = None  # YYYY-MM-DD
    minAmount: Optional[float] = None
    maxAmount: Optional[float] = None
    state: Optional[str] = None
    city: Optional[str] = None
    discount: Optional[bool] = None
    minDiscountPercentage: Optional[float] = None  # 0-100
    status: Optional[str] = None

# Chat input
class ChatInputType(BaseModel):
    """Input schema for chat endpoint"""
    input: List[Union[HumanMessage, AIMessage, SystemMessage]]

# Dynamic schema generation for validation
def filter_schema(product_names: List[str]) -> Type[BaseModel]:
    """Generates FilterSchema with runtime validation constraints"""
    class FilterSchema(BaseModel):
        productNames: Optional[List[str]] = Field(
            None,
            description=f"MUST only be a list of the following products: {product_names}"
        )
        beforeDate: Optional[str] = Field(None, description="Date format: YYYY-MM-DD")
        afterDate: Optional[str] = Field(None, description="Date format: YYYY-MM-DD")
        minAmount: Optional[float] = None
        maxAmount: Optional[float] = None
        state: Optional[str] = None
        city: Optional[str] = None
        discount: Optional[bool] = None
        minDiscountPercentage: Optional[float] = Field(
            None,
            ge=0,
            le=100,
            description="Discount percentage between 0-100"
        )
        status: Optional[str] = None
    return FilterSchema
```

### Frontend TypeScript Types

```typescript
// Order structure (mirrors Python)
interface Address {
  street: string;
  city: string;
  state: string;
  zip: string;
}

interface Order {
  id: string;
  productName: string;
  amount: number;
  discount?: number;  // 0-100 percentage
  address: Address;
  status: "pending" | "processing" | "shipped" | "delivered" | "cancelled" | "returned";
  orderedAt: Date;
}

// Filter structure
interface Filter {
  productNames?: string[];
  beforeDate?: string;
  afterDate?: string;
  minAmount?: number;
  maxAmount?: number;
  state?: string;
  city?: string;
  discount?: boolean;
  minDiscountPercentage?: number;
  status?: string;
}

// Component props for tools
interface CurrentWeatherProps {
  temperature: number;
  city: string;
  state: string;
}

interface DemoGithubProps {
  owner: string;
  repo: string;
  description: string;
  stars: number;
  language: string;
}

interface InvoiceProps {
  orderId: string;
  lineItems: LineItem[];
  shippingAddress?: ShippingAddress;
  customerInfo?: CustomerInfo;
  paymentInfo?: PaymentInfo;
}

interface LineItem {
  id: string;
  name: string;
  quantity: number;
  price: number;
}
```

## 2. How UI Components Are Generated in Agent Nodes

### Backend: LangGraph Node Pattern

Each node in the LangGraph workflow returns **state updates** that contain metadata about what UI to render:

```python
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

# Example node: Generate filters
def generate_filters(state: AgentExecutorState) -> dict:
    """
    Node that uses LLM to extract filter criteria from user input
    Returns: {"selected_filters": Filter}
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    llm_with_schema = llm.with_structured_output(FilterSchema)

    result = llm_with_schema.invoke([
        SystemMessage(content="Extract filter criteria from user input"),
        HumanMessage(content=state["input"])
    ])

    # Return state update
    return {"selected_filters": result}

# Example node: Generate chart type
def generate_chart_type(state: AgentExecutorState) -> dict:
    """
    Node that decides which chart type to use
    Returns: {"chart_type": "bar" | "line" | "pie"}
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    llm_with_schema = llm.with_structured_output(ChartTypeSchema)

    result = llm_with_schema.invoke([
        SystemMessage(content=f"Choose optimal chart for filters: {state['selected_filters']}"),
        HumanMessage(content=state["input"])
    ])

    return {"chart_type": result.chart_type}

# Example node: Filter data
def filter_data(state: AgentExecutorState) -> dict:
    """
    Node that filters orders based on generated criteria
    Returns: {"orders": List[Order]}
    """
    filters = state["selected_filters"]
    orders = state["orders"]

    filtered = [
        order for order in orders
        if matches_filters(order, filters)
    ]

    return {"orders": filtered}

# Build the graph
graph = StateGraph(AgentExecutorState)
graph.add_node("generate_filters", generate_filters)
graph.add_node("generate_chart_type", generate_chart_type)
graph.add_node("filter_data", filter_data)

graph.add_edge("generate_filters", "generate_chart_type")
graph.add_edge("generate_chart_type", "filter_data")
graph.set_entry_point("generate_filters")
```

### Tools Pattern

Tools return **plain data dictionaries** without UI metadata:

```python
from langchain_core.tools import tool

@tool
def weather_data(city: str, state: str, country: str = "usa") -> dict:
    """Get current weather for a location"""
    # 1. Geocode city/state to lat/long
    coords = geocode(city, state, country)

    # 2. Get weather forecast
    forecast = get_forecast(coords["lat"], coords["lon"])

    # 3. Return plain data
    return {
        "city": city,
        "state": state,
        "country": country,
        "temperature": forecast["temperature"]
    }

@tool
def github_repo(owner: str, repo: str) -> dict:
    """Get GitHub repository information"""
    response = requests.get(f"https://api.github.com/repos/{owner}/{repo}")
    data = response.json()

    return {
        "owner": owner,
        "repo": repo,
        "description": data["description"],
        "stars": data["stargazers_count"],
        "language": data["language"]
    }

@tool
def invoice_parser(invoice_data: str) -> Invoice:
    """Parse invoice and return structured data"""
    # Parse invoice text/data
    parsed = parse_invoice(invoice_data)

    return Invoice(
        orderId=parsed["order_id"],
        lineItems=parsed["items"],
        shippingAddress=parsed.get("shipping"),
        customerInfo=parsed.get("customer"),
        paymentInfo=parsed.get("payment")
    )
```

### Agent Chain Pattern

The main chain orchestrates tool calling and returns results:

```python
from langchain.agents import AgentExecutor
from langchain_openai import ChatOpenAI

def create_agent_chain():
    """Create the main agent chain"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0, streaming=True)

    tools = [weather_data, github_repo, invoice_parser]

    # Agent decides which tool to call
    agent = create_tool_calling_agent(llm, tools)
    executor = AgentExecutor(agent=agent, tools=tools)

    return executor

# Usage in chain
def process_chat(state: dict) -> dict:
    """Main processing function"""
    executor = create_agent_chain()

    # Invoke returns: {"output": str, "tool_calls": [...], "tool_results": [...]}
    result = executor.invoke({"input": state["input"]})

    # Check if tools were called
    if result.get("tool_calls"):
        tool_name = result["tool_calls"][0]["name"]
        tool_result = result["tool_results"][0]

        return {
            "tool_result": {
                "name": tool_name,
                "data": tool_result
            }
        }

    return {"output": result["output"]}
```

## 3. Message Format for Streaming UI to Frontend

### Backend: LangServe Streaming

```python
from fastapi import FastAPI
from langserve import add_routes

app = FastAPI()

# Add streaming endpoint
add_routes(
    app,
    graph.with_types(input_type=ChatInputType, output_type=dict),
    path="/chat",
    playground_type="chat"  # Enables chat interface
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### Frontend: Vercel AI SDK Streaming

The frontend uses **Vercel AI SDK's React Server Components (RSC)** for streaming:

```typescript
"use server";

import { createStreamableUI, createStreamableValue } from "ai/rsc";
import { RemoteRunnable } from "@langchain/core/runnables/remote";

export async function agent(input: string, chatHistory: [string, string][]) {
  const ui = createStreamableUI();  // Streamable UI component
  const textStream = createStreamableValue("");  // Streamable text value

  // Connect to backend
  const remoteRunnable = new RemoteRunnable({
    url: "http://localhost:8000/chat"
  });

  // Stream events from backend
  const streamEvents = remoteRunnable.streamEvents(
    { input: [...chatHistory, ["human", input]] },
    { version: "v1" }
  );

  let lastEvent = null;

  // Process each event
  for await (const event of streamEvents) {
    lastEvent = event;

    switch (event.event) {
      case "on_chat_model_stream":
        // Handle streaming text from LLM
        handleChatModelStreamEvent(event, textStream);
        break;

      case "invoke_model":
        // Handle tool invocation start
        handleInvokeModelEvent(event, ui);
        break;

      case "invoke_tools":
        // Handle tool results
        handleInvokeToolsEvent(event, ui);
        break;
    }
  }

  return { ui: ui.value, lastEvent, textStream: textStream.value };
}
```

### Event Types and Structure

#### 1. Chat Model Stream Event
```typescript
{
  event: "on_chat_model_stream",
  name: "ChatOpenAI",
  run_id: "uuid",
  data: {
    chunk: {
      content: "chunk of text"
    }
  }
}
```

Handler:
```typescript
function handleChatModelStreamEvent(event: StreamEvent, textStream: StreamableValue) {
  const chunk = event.data?.chunk?.content;
  if (chunk) {
    textStream.append(chunk);
  }
}
```

#### 2. Invoke Model Event (Tool Call Detected)
```typescript
{
  event: "invoke_model",
  name: "agent",
  data: {
    output: {
      tool_calls: [
        {
          name: "weather-data",
          args: { city: "San Francisco", state: "CA" }
        }
      ]
    }
  }
}
```

Handler:
```typescript
function handleInvokeModelEvent(event: StreamEvent, ui: StreamableUI) {
  const toolCalls = event.data?.output?.tool_calls;

  if (toolCalls && toolCalls.length > 0) {
    const toolName = toolCalls[0].name;

    // Show loading component based on tool type
    const LoadingComponent = TOOL_LOADING_MAP[toolName];
    ui.update(<LoadingComponent />);
  }
}
```

#### 3. Invoke Tools Event (Tool Results)
```typescript
{
  event: "invoke_tools",
  name: "tools",
  data: {
    output: [
      {
        name: "weather-data",
        result: {
          city: "San Francisco",
          state: "CA",
          country: "usa",
          temperature: 72
        }
      }
    ]
  }
}
```

Handler:
```typescript
function handleInvokeToolsEvent(event: StreamEvent, ui: StreamableUI) {
  const toolResults = event.data?.output;

  if (toolResults && toolResults.length > 0) {
    const { name, result } = toolResults[0];

    // Render final component with data
    const Component = TOOL_COMPONENT_MAP[name];
    ui.update(<Component {...result} />);
  }
}
```

#### 4. Chain End Event (LangGraph Node Completion)
```typescript
{
  event: "on_chain_end",
  name: "generate_filters",  // Node name
  data: {
    output: {
      selected_filters: {
        productNames: ["Widget A"],
        minAmount: 100
      }
    }
  }
}
```

Handler:
```typescript
function handleChainEndEvent(event: StreamEvent, ui: StreamableUI) {
  const nodeName = event.name;
  const output = event.data?.output;

  switch (nodeName) {
    case "generate_filters":
      // Render filter pills
      ui.append(
        <div>
          {Object.entries(output.selected_filters).map(([key, value]) => (
            <FilterButton key={key} filterKey={key} filterValue={value} />
          ))}
        </div>
      );
      break;

    case "generate_chart_type":
      // Show loading skeleton for chart type
      const chartType = output.chart_type;
      ui.append(<LoadingChart type={chartType} />);
      break;

    case "filter_data":
      // Replace loading with actual chart
      const chartData = output.orders;
      ui.update(<Chart data={chartData} type={chartType} />);
      break;
  }
}
```

### Complete Event Handler Example

```typescript
export async function filterGraph(input: {
  input: string;
  orders: Order[];
  display_formats: any[];
}) {
  const ui = createStreamableUI();

  const remoteRunnable = new RemoteRunnable({
    url: "http://localhost:8000/chart"
  });

  const streamEvents = remoteRunnable.streamEvents(input, { version: "v1" });

  let selectedFilters = null;
  let chartType = null;
  let displayFormat = null;
  let filteredOrders = null;

  for await (const event of streamEvents) {
    if (event.event === "on_chain_end") {
      switch (event.name) {
        case "generate_filters":
          selectedFilters = event.data.output.selected_filters;

          // Update UI with filter buttons
          ui.append(
            <div className="flex gap-2">
              {Object.entries(selectedFilters).map(([key, value]) => (
                <FilterButton key={key} filterKey={key} filterValue={value} />
              ))}
            </div>
          );
          break;

        case "generate_chart_type":
          chartType = event.data.output.chart_type;

          // Show loading skeleton
          ui.append(<LoadingChart type={chartType} />);
          break;

        case "generate_data_display_format":
          displayFormat = event.data.output.display_format;

          // Update with title and description
          ui.update(
            <>
              <h2>{displayFormat.title}</h2>
              <p>{displayFormat.description}</p>
              <LoadingChart type={chartType} />
            </>
          );
          break;

        case "filter_data":
          filteredOrders = event.data.output.orders;

          // Replace loading with actual chart
          const chartProps = constructChartProps(
            filteredOrders,
            chartType,
            displayFormat
          );

          ui.update(
            <>
              <h2>{displayFormat.title}</h2>
              <p>{displayFormat.description}</p>
              <Chart {...chartProps} />
            </>
          );
          break;
      }
    }
  }

  return {
    ui: ui.value,
    lastEvent: { selectedFilters, chartType, displayFormat, filteredOrders }
  };
}
```

## 4. Code Examples of Generating Different UI Types

### Example 1: Weather Card

**Backend Tool:**
```python
@tool
def weather_data(city: str, state: str, country: str = "usa") -> dict:
    """Get current weather data"""
    coords = geocode(city, state, country)
    forecast = get_forecast(coords["lat"], coords["lon"])

    return {
        "city": city,
        "state": state,
        "country": country,
        "temperature": forecast["temperature"]
    }
```

**Frontend Component:**
```typescript
// Loading state
function CurrentWeatherLoading() {
  return (
    <div className="weather-card">
      <div className="skeleton h-20 w-20" />
      <div className="skeleton h-4 w-32" />
    </div>
  );
}

// Final component
interface CurrentWeatherProps {
  temperature: number;
  city: string;
  state: string;
}

function CurrentWeather(props: CurrentWeatherProps) {
  const percentage = ((props.temperature + 20) / 150) * 100;
  const now = new Date();

  return (
    <div className="weather-card">
      <div className="temperature">
        {props.temperature}&deg;
      </div>
      <Progress value={percentage} />
      <div className="location">
        {props.city}, {props.state}
      </div>
      <div className="time">
        {format(now, "h:mm a")} · {format(now, "EEEE")}
      </div>
    </div>
  );
}
```

**Event Handler:**
```typescript
const TOOL_COMPONENT_MAP = {
  "weather-data": CurrentWeather
};

const TOOL_LOADING_MAP = {
  "weather-data": CurrentWeatherLoading
};

function handleInvokeModelEvent(event: StreamEvent, ui: StreamableUI) {
  const toolCalls = event.data?.output?.tool_calls;
  if (toolCalls?.[0]?.name === "weather-data") {
    ui.update(<CurrentWeatherLoading />);
  }
}

function handleInvokeToolsEvent(event: StreamEvent, ui: StreamableUI) {
  const toolResults = event.data?.output;
  const result = toolResults?.[0];

  if (result?.name === "weather-data") {
    ui.update(
      <CurrentWeather
        temperature={result.result.temperature}
        city={result.result.city}
        state={result.result.state}
      />
    );
  }
}
```

### Example 2: GitHub Repository Card

**Backend Tool:**
```python
@tool
def github_repo(owner: str, repo: str) -> dict:
    """Get GitHub repository information"""
    response = requests.get(f"https://api.github.com/repos/{owner}/{repo}")
    data = response.json()

    return {
        "owner": owner,
        "repo": repo,
        "description": data["description"],
        "stars": data["stargazers_count"],
        "language": data["language"]
    }
```

**Frontend Component:**
```typescript
interface DemoGithubProps {
  owner: string;
  repo: string;
  description: string;
  stars: number;
  language: string;
}

function Github(props: DemoGithubProps) {
  const handleStarClick = () => {
    window.location.href = `https://github.com/${props.owner}/${props.repo}`;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <span>{props.owner}/{props.repo}</span>
          <Button onClick={handleStarClick}>
            Star
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <p>{props.description}</p>
      </CardContent>
      <CardFooter>
        <div className="flex gap-4">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            {props.language}
          </div>
          <div className="flex items-center gap-1">
            <Star size={16} />
            {props.stars.toLocaleString()}
          </div>
          <div>
            Updated {format(new Date(), "MMMM yyyy")}
          </div>
        </div>
      </CardFooter>
    </Card>
  );
}
```

### Example 3: Invoice Display

**Backend Tool:**
```python
class LineItem(BaseModel):
    id: str
    name: str
    quantity: int
    price: float

class Invoice(BaseModel):
    orderId: str
    lineItems: List[LineItem]
    shippingAddress: Optional[Address] = None
    customerInfo: Optional[CustomerInfo] = None
    paymentInfo: Optional[PaymentInfo] = None

@tool
def invoice_parser(invoice_data: str) -> Invoice:
    """Parse invoice and return structured data"""
    parsed = parse_invoice_text(invoice_data)

    return Invoice(
        orderId=parsed["order_id"],
        lineItems=[
            LineItem(**item) for item in parsed["items"]
        ],
        shippingAddress=Address(**parsed.get("shipping")) if parsed.get("shipping") else None,
        customerInfo=CustomerInfo(**parsed.get("customer")) if parsed.get("customer") else None,
        paymentInfo=PaymentInfo(**parsed.get("payment")) if parsed.get("payment") else None
    )
```

**Frontend Component:**
```typescript
interface InvoiceProps {
  orderId: string;
  lineItems: LineItem[];
  shippingAddress?: ShippingAddress;
  customerInfo?: CustomerInfo;
  paymentInfo?: PaymentInfo;
}

function Invoice(props: InvoiceProps) {
  const [priceDetails, setPriceDetails] = useState({
    subtotal: 0,
    tax: 0,
    shipping: 5,
    total: 0
  });

  useEffect(() => {
    const subtotal = props.lineItems.reduce(
      (sum, item) => sum + (item.price * item.quantity),
      0
    );
    const tax = subtotal * 0.075;
    const total = subtotal + tax + 5;

    setPriceDetails({ subtotal, tax, shipping: 5, total });
  }, [props.lineItems]);

  return (
    <Card>
      <CardHeader>
        <h2>Invoice #{props.orderId}</h2>
      </CardHeader>
      <CardContent>
        {/* Line Items */}
        <div className="line-items">
          {props.lineItems.map(item => (
            <div key={item.id} className="flex justify-between">
              <span>{item.name} x {item.quantity}</span>
              <span>${(item.price * item.quantity).toFixed(2)}</span>
            </div>
          ))}
        </div>

        <Separator />

        {/* Price Breakdown */}
        <div className="price-details">
          <div className="flex justify-between">
            <span>Subtotal</span>
            <span>${priceDetails.subtotal.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span>Tax (7.5%)</span>
            <span>${priceDetails.tax.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span>Shipping</span>
            <span>${priceDetails.shipping.toFixed(2)}</span>
          </div>
          <div className="flex justify-between font-bold">
            <span>Total</span>
            <span>${priceDetails.total.toFixed(2)}</span>
          </div>
        </div>

        {/* Conditional sections */}
        {props.shippingAddress && (
          <div className="shipping">
            <h3>Shipping Address</h3>
            <p>{props.shippingAddress.street}</p>
            <p>{props.shippingAddress.city}, {props.shippingAddress.state} {props.shippingAddress.zip}</p>
          </div>
        )}

        {props.customerInfo && (
          <div className="customer">
            <h3>Customer</h3>
            <p>{props.customerInfo.name}</p>
            <p>{props.customerInfo.email}</p>
          </div>
        )}

        {props.paymentInfo && (
          <div className="payment">
            <h3>Payment</h3>
            <p>{props.paymentInfo.cardType} ending in {props.paymentInfo.lastFour}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

### Example 4: Dynamic Charts

**Backend LangGraph Chain:**
```python
from langgraph.graph import StateGraph
from typing import TypedDict

class AgentExecutorState(TypedDict):
    input: str
    orders: List[Order]
    display_formats: List[DataDisplayTypeAndDescription]
    selected_filters: Optional[Filter]
    chart_type: Optional[str]
    display_format: Optional[str]

def generate_filters(state: AgentExecutorState) -> dict:
    """Extract filters from natural language"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    llm_with_schema = llm.with_structured_output(
        filter_schema([order.productName for order in state["orders"]])
    )

    result = llm_with_schema.invoke([
        SystemMessage(content="Extract filter criteria from user request"),
        HumanMessage(content=state["input"])
    ])

    return {"selected_filters": result}

def generate_chart_type(state: AgentExecutorState) -> dict:
    """Decide optimal chart type"""
    class ChartTypeSchema(BaseModel):
        chart_type: ChartType

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_schema = llm.with_structured_output(ChartTypeSchema)

    prompt = f"""
    User request: {state["input"]}
    Filters: {state["selected_filters"]}

    Choose the best chart type:
    - bar: Compare categories or products
    - line: Show trends over time
    - pie: Show proportions or distribution
    """

    result = llm_with_schema.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=state["input"])
    ])

    return {"chart_type": result.chart_type}

def generate_data_display_format(state: AgentExecutorState) -> dict:
    """Select specific display format"""
    # Filter formats by chart type
    compatible_formats = [
        fmt for fmt in state["display_formats"]
        if fmt.chartType == state["chart_type"]
    ]

    class DisplayFormatSchema(BaseModel):
        display_key: str = Field(
            description=f"Must be one of: {[fmt.key for fmt in compatible_formats]}"
        )

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_schema = llm.with_structured_output(DisplayFormatSchema)

    result = llm_with_schema.invoke([
        SystemMessage(content=f"Choose display format from: {compatible_formats}"),
        HumanMessage(content=state["input"])
    ])

    selected_format = next(
        fmt for fmt in compatible_formats
        if fmt.key == result.display_key
    )

    return {"display_format": selected_format}

def filter_data(state: AgentExecutorState) -> dict:
    """Apply filters to orders"""
    filters = state["selected_filters"]
    orders = state["orders"]

    filtered = []
    for order in orders:
        # Apply all filter conditions
        if filters.productNames and order.productName not in filters.productNames:
            continue
        if filters.minAmount and order.amount < filters.minAmount:
            continue
        if filters.maxAmount and order.amount > filters.maxAmount:
            continue
        if filters.state and order.address.state.lower() != filters.state.lower():
            continue
        if filters.status and order.status.lower() != filters.status.lower():
            continue
        if filters.beforeDate and order.orderedAt > filters.beforeDate:
            continue
        if filters.afterDate and order.orderedAt < filters.afterDate:
            continue
        if filters.discount is not None:
            has_discount = order.discount is not None and order.discount > 0
            if filters.discount != has_discount:
                continue
        if filters.minDiscountPercentage:
            if not order.discount or order.discount < filters.minDiscountPercentage:
                continue

        filtered.append(order)

    return {"orders": filtered}

# Build graph
graph = StateGraph(AgentExecutorState)
graph.add_node("generate_filters", generate_filters)
graph.add_node("generate_chart_type", generate_chart_type)
graph.add_node("generate_data_display_format", generate_data_display_format)
graph.add_node("filter_data", filter_data)

graph.add_edge("generate_filters", "generate_chart_type")
graph.add_edge("generate_chart_type", "generate_data_display_format")
graph.add_edge("generate_data_display_format", "filter_data")
graph.set_entry_point("generate_filters")

compiled_graph = graph.compile()
```

**Frontend Event Handler:**
```typescript
"use server";

import { createStreamableUI } from "ai/rsc";
import { RemoteRunnable } from "@langchain/core/runnables/remote";

export async function filterGraph(input: {
  input: string;
  orders: Order[];
  display_formats: DataDisplayFormat[];
}) {
  const ui = createStreamableUI();

  const remoteRunnable = new RemoteRunnable({
    url: "http://localhost:8000/chart"
  });

  const streamEvents = remoteRunnable.streamEvents(input, { version: "v1" });

  let state = {
    selectedFilters: null,
    chartType: null,
    displayFormat: null,
    filteredOrders: null
  };

  for await (const event of streamEvents) {
    if (event.event === "on_chain_end") {
      const nodeName = event.name;
      const output = event.data.output;

      switch (nodeName) {
        case "generate_filters":
          state.selectedFilters = output.selected_filters;

          // Render filter pills
          ui.append(
            <div className="flex gap-2 mb-4">
              {Object.entries(state.selectedFilters).map(([key, value]) => (
                <FilterButton
                  key={key}
                  filterKey={key}
                  filterValue={value as string | number}
                />
              ))}
            </div>
          );
          break;

        case "generate_chart_type":
          state.chartType = output.chart_type;

          // Show loading skeleton
          ui.append(<LoadingCharts type={state.chartType} />);
          break;

        case "generate_data_display_format":
          state.displayFormat = output.display_format;

          // Update with metadata
          ui.update(
            <>
              {/* Keep filters */}
              <div className="flex gap-2 mb-4">
                {Object.entries(state.selectedFilters).map(([key, value]) => (
                  <FilterButton
                    key={key}
                    filterKey={key}
                    filterValue={value as string | number}
                  />
                ))}
              </div>

              {/* Add title and description */}
              <div className="mb-4">
                <h2 className="text-2xl font-bold">{state.displayFormat.title}</h2>
                <p className="text-muted-foreground">{state.displayFormat.description}</p>
              </div>

              {/* Keep loading */}
              <LoadingCharts type={state.chartType} />
            </>
          );
          break;

        case "filter_data":
          state.filteredOrders = output.orders;

          // Construct chart props based on type
          let chartComponent;

          switch (state.chartType) {
            case "bar":
              const barProps = constructProductSalesBarChartProps(state.filteredOrders);
              chartComponent = <BarChart {...barProps} />;
              break;

            case "line":
              const lineProps = constructOrderAmountOverTimeLineChartProps(state.filteredOrders);
              chartComponent = <LineChart {...lineProps} />;
              break;

            case "pie":
              const pieProps = constructOrderStatusDistributionPieChartProps(state.filteredOrders);
              chartComponent = <PieChart {...pieProps} />;
              break;
          }

          // Final UI with chart
          ui.update(
            <>
              <div className="flex gap-2 mb-4">
                {Object.entries(state.selectedFilters).map(([key, value]) => (
                  <FilterButton
                    key={key}
                    filterKey={key}
                    filterValue={value as string | number}
                  />
                ))}
              </div>

              <div className="mb-4">
                <h2 className="text-2xl font-bold">{state.displayFormat.title}</h2>
                <p className="text-muted-foreground">{state.displayFormat.description}</p>
              </div>

              {chartComponent}
            </>
          );
          break;
      }
    }
  }

  return {
    ui: ui.value,
    lastEvent: state
  };
}

// Helper functions
function constructProductSalesBarChartProps(orders: Order[]) {
  const salesByProduct = orders.reduce((acc, order) => {
    acc[order.productName] = (acc[order.productName] || 0) + order.amount;
    return acc;
  }, {} as Record<string, number>);

  return {
    data: Object.entries(salesByProduct).map(([product, amount]) => ({
      name: product,
      value: amount
    })),
    xKey: "name",
    yKey: "value",
    xLabel: "Product",
    yLabel: "Sales ($)"
  };
}

function constructOrderAmountOverTimeLineChartProps(orders: Order[]) {
  const ordersByDate = orders.reduce((acc, order) => {
    acc[order.orderedAt] = (acc[order.orderedAt] || 0) + order.amount;
    return acc;
  }, {} as Record<string, number>);

  return {
    data: Object.entries(ordersByDate)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, amount]) => ({
        date,
        amount
      })),
    xKey: "date",
    yKey: "amount",
    xLabel: "Date",
    yLabel: "Order Amount ($)"
  };
}

function constructOrderStatusDistributionPieChartProps(orders: Order[]) {
  const statusCounts = orders.reduce((acc, order) => {
    acc[order.status] = (acc[order.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return {
    data: Object.entries(statusCounts).map(([status, count]) => ({
      name: status,
      value: count
    })),
    nameKey: "name",
    valueKey: "value"
  };
}
```

**Frontend Chart Components:**
```typescript
// Bar Chart
function BarChart({ data, xKey, yKey, xLabel, yLabel }: BarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <RechartsBarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={xKey} label={{ value: xLabel, position: "insideBottom", offset: -5 }} />
        <YAxis label={{ value: yLabel, angle: -90, position: "insideLeft" }} />
        <Tooltip />
        <Bar dataKey={yKey} fill="#8884d8" />
      </RechartsBarChart>
    </ResponsiveContainer>
  );
}

// Line Chart
function LineChart({ data, xKey, yKey, xLabel, yLabel }: LineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <RechartsLineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={xKey} label={{ value: xLabel, position: "insideBottom", offset: -5 }} />
        <YAxis label={{ value: yLabel, angle: -90, position: "insideLeft" }} />
        <Tooltip />
        <Line type="monotone" dataKey={yKey} stroke="#8884d8" />
      </RechartsLineChart>
    </ResponsiveContainer>
  );
}

// Pie Chart
function PieChart({ data, nameKey, valueKey }: PieChartProps) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <RechartsPieChart>
        <Pie
          data={data}
          dataKey={valueKey}
          nameKey={nameKey}
          cx="50%"
          cy="50%"
          outerRadius={100}
          fill="#8884d8"
          label
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </RechartsPieChart>
    </ResponsiveContainer>
  );
}
```

## 5. Integration Points Between Backend and Frontend

### 1. HTTP Streaming Endpoint

**Backend (LangServe):**
```python
from fastapi import FastAPI
from langserve import add_routes

app = FastAPI()

# Main chat endpoint
add_routes(
    app,
    agent_executor.with_types(input_type=ChatInputType, output_type=dict),
    path="/chat",
    playground_type="chat"
)

# Chart generation endpoint
add_routes(
    app,
    compiled_graph.with_types(input_type=ChartInputType, output_type=dict),
    path="/chart",
    playground_type="chat"
)

# CORS configuration
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Frontend (RemoteRunnable):**
```typescript
import { RemoteRunnable } from "@langchain/core/runnables/remote";

const chatRunnable = new RemoteRunnable({
  url: "http://localhost:8000/chat"
});

const chartRunnable = new RemoteRunnable({
  url: "http://localhost:8000/chart"
});
```

### 2. Event Streaming

**Backend emits:**
- `on_chat_model_stream` - LLM text chunks
- `on_chain_start` - Node execution starts
- `on_chain_end` - Node execution completes
- `invoke_model` - Tool call detected
- `invoke_tools` - Tool results available

**Frontend consumes:**
```typescript
const streamEvents = remoteRunnable.streamEvents(input, { version: "v1" });

for await (const event of streamEvents) {
  // Process each event type
  switch (event.event) {
    case "on_chat_model_stream":
      // Handle text streaming
      break;
    case "on_chain_end":
      // Handle node completion
      break;
    case "invoke_model":
      // Show loading state
      break;
    case "invoke_tools":
      // Show final component
      break;
  }
}
```

### 3. Component Registration

**Frontend maintains mappings:**
```typescript
// Tool name -> Component mapping
const TOOL_COMPONENT_MAP: Record<string, React.ComponentType<any>> = {
  "weather-data": CurrentWeather,
  "github-repo": Github,
  "invoice-parser": Invoice
};

// Tool name -> Loading component mapping
const TOOL_LOADING_MAP: Record<string, React.ComponentType> = {
  "weather-data": CurrentWeatherLoading,
  "github-repo": GithubLoading,
  "invoice-parser": InvoiceLoading
};

// LangGraph node name -> Handler mapping
const NODE_HANDLERS: Record<string, (event: StreamEvent, ui: StreamableUI) => void> = {
  "generate_filters": handleSelectedFilters,
  "generate_chart_type": handleChartType,
  "generate_data_display_format": handleDisplayFormat,
  "filter_data": handleConstructingCharts
};
```

### 4. Data Flow Sequence

```
1. User Input → Frontend
2. Frontend → RemoteRunnable.streamEvents(input) → Backend
3. Backend → LangGraph executes nodes → Emits events
4. Frontend ← Stream events ← Backend
5. Frontend → Process events → Update StreamableUI
6. Frontend → Render components with data
```

## 6. Streaming Architecture Deep Dive

### Backend: How Streaming Works

**LangServe automatically streams events from LangGraph:**

```python
from langgraph.graph import StateGraph

# Define graph
graph = StateGraph(AgentExecutorState)
graph.add_node("node1", func1)
graph.add_node("node2", func2)
graph.add_edge("node1", "node2")

compiled_graph = graph.compile()

# LangServe wraps it
add_routes(app, compiled_graph, path="/chat")

# When invoked, automatically emits:
# - on_chain_start for each node start
# - on_chain_end for each node completion
# - on_chat_model_stream for LLM chunks (if streaming=True)
```

**Event emission is automatic** - you don't need to manually emit events. LangGraph + LangServe handle this.

### Frontend: StreamableUI Pattern

**Key concept**: `StreamableUI` allows progressive UI updates

```typescript
const ui = createStreamableUI();

// Initial state
ui.update(<LoadingSpinner />);

// Update as data comes in
ui.append(<FilterPill filter="price > 100" />);

// Replace with final state
ui.update(<CompleteChart data={chartData} />);

// Return to caller
return { ui: ui.value };
```

**StreamableValue for text:**
```typescript
const textStream = createStreamableValue("");

// Append chunks
textStream.append("Hello");
textStream.append(" world");

// Done
textStream.done();

// In component
<div>{textStream.value}</div>  // Renders "Hello world"
```

## 7. Key Patterns and Best Practices

### 1. Component Pre-building
- **All UI components are pre-built** in React
- Backend doesn't generate JSX/HTML
- Backend only returns **data** and **metadata about which component to use**

### 2. Two-Phase Rendering
```typescript
// Phase 1: Show loading
ui.update(<WeatherLoading />);

// Phase 2: Show actual data
ui.update(<Weather temperature={72} city="SF" />);
```

### 3. Progressive Enhancement
```typescript
// Start simple
ui.update(<LoadingChart />);

// Add metadata
ui.append(<ChartTitle title="Sales by Product" />);

// Replace with final
ui.update(
  <>
    <ChartTitle title="Sales by Product" />
    <BarChart data={chartData} />
  </>
);
```

### 4. State Accumulation in LangGraph
```python
# Each node returns partial state updates
def node1(state):
    return {"field1": value1}

def node2(state):
    # Has access to field1 from node1
    return {"field2": value2}

# Final state has both field1 and field2
```

### 5. Type Safety
```typescript
// Backend defines Pydantic models
class WeatherResult(BaseModel):
    temperature: float
    city: str
    state: str

// Frontend mirrors with TypeScript
interface WeatherResult {
  temperature: number;
  city: string;
  state: string;
}
```

### 6. Error Handling
```python
@tool
def weather_data(city: str, state: str) -> dict:
    try:
        # Fetch weather
        return {"temperature": temp, "city": city, "state": state}
    except Exception as e:
        # Return error in same format
        return {"error": str(e), "city": city, "state": state}
```

```typescript
function handleInvokeToolsEvent(event: StreamEvent, ui: StreamableUI) {
  const result = event.data?.output?.[0]?.result;

  if (result.error) {
    ui.update(<ErrorMessage error={result.error} />);
  } else {
    ui.update(<Weather {...result} />);
  }
}
```

## Summary

The gen-ui-python implementation demonstrates a **metadata-driven generative UI pattern**:

1. **Backend generates structured data** (not UI code)
2. **Backend emits events** indicating what happened (tool called, node completed)
3. **Frontend listens to events** and decides which pre-built component to render
4. **Frontend passes data as props** to components
5. **Streaming enables progressive updates** (loading → data → final)

This is **NOT** true code generation - it's **intelligent component selection** based on:
- Tool types (weather → WeatherCard)
- Data types (chart_type="bar" → BarChart)
- Node completions (filters generated → show FilterPills)

The key innovation is using **LangGraph events** to trigger **UI state transitions** in the frontend, creating a responsive, streaming experience while maintaining type safety and component reusability.
