# LangChain Browser Tools in LangGraph

## Overview

This guide explains how to use LangChain's browser automation tools within LangGraph applications, specifically for handling JavaScript-heavy websites that require dynamic rendering.

## Quick Answer: Full Compatibility

**Yes, LangChain browser tools work directly with LangGraph with no adapters needed.**

- Same parent company (LangChain Inc.)
- Shared tool interface (`@tool` decorator)
- Native support in `create_react_agent` and `ToolNode`
- No conversion or wrapper required

## PlayWrightBrowserToolkit

LangChain's `PlayWrightBrowserToolkit` provides seven browser automation tools built on Microsoft's Playwright library:

| Tool | Name | Purpose |
|------|------|---------|
| `NavigateTool` | `navigate_browser` | Navigate to URLs |
| `NavigateBackTool` | `previous_page` | Browser back button |
| `ClickTool` | `click_element` | Click elements via CSS selector |
| `ExtractTextTool` | `extract_text` | Extract visible text (BeautifulSoup) |
| `ExtractHyperlinksTool` | `extract_hyperlinks` | Extract all links |
| `GetElementsTool` | `get_elements` | Query elements by selector |
| `CurrentWebPageTool` | `current_webpage` | Get current URL |

### When to Use

**Use Playwright browser tools when:**
- Target site renders content with JavaScript (React, Vue, Angular)
- Static HTTP requests return incomplete/empty content
- Need to interact with UI elements (click, fill forms, scroll)
- Site requires browser session state or cookies

**Use simple HTTP requests when:**
- Static HTML content is sufficient
- Site provides API endpoints
- No JavaScript rendering required

## Installation

```bash
# Install required packages
pip install playwright lxml langchain-community

# Install browser executable (one-time setup)
playwright install chromium
```

## Integration Patterns

### Pattern 1: create_react_agent (Recommended)

**Best for:** Quick prototyping, simple workflows, automatic tool routing

```python
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_async_playwright_browser
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model

# Initialize browser and toolkit
async_browser = create_async_playwright_browser()
toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
tools = toolkit.get_tools()

# Create agent - tools passed directly!
llm = init_chat_model(model="anthropic:claude-3-5-sonnet-latest")
agent = create_react_agent(model=llm, tools=tools)

# Invoke
result = await agent.ainvoke({
    "messages": [{"role": "user", "content": "Go to example.com and extract headers"}]
})
```

**Pros:**
- Minimal code required
- Automatic tool routing
- Built-in error handling
- Conversation state managed automatically

**Cons:**
- Less control over workflow
- Fixed ReAct pattern
- Limited customization

### Pattern 2: Custom StateGraph with ToolNode

**Best for:** Complex workflows, custom state management, conditional logic

```python
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, add_messages

# Define state schema
class BrowserState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    scraped_data: dict

# Initialize tools
toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
tools = toolkit.get_tools()
tool_node = ToolNode(tools)

# Build graph
def agent_node(state):
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state):
    last_message = state["messages"][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return END

graph = StateGraph(BrowserState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, ["tools", END])
graph.add_edge("tools", "agent")

compiled_graph = graph.compile()
```

**Pros:**
- Full control over workflow
- Custom state schema
- Conditional routing
- Multi-step processes

**Cons:**
- More boilerplate code
- Manual tool execution management
- Must handle errors explicitly

### Pattern 3: Manual Tool Invocation

**Best for:** Specific tool usage, custom error handling, predetermined workflows

```python
from langchain_community.tools.playwright import NavigateTool, ExtractTextTool

# Initialize specific tools
navigate = NavigateTool(async_browser=async_browser)
extract = ExtractTextTool(async_browser=async_browser)

# Custom node with manual tool calls
async def scrape_node(state):
    try:
        # Navigate
        await navigate.ainvoke({"url": state["target_url"]})

        # Extract
        text = await extract.ainvoke({})

        return {"scraped_data": {"text": text}}
    except Exception as e:
        return {"error_message": str(e)}
```

**Pros:**
- Maximum control
- Custom error handling per tool
- No LLM token usage for tool selection
- Predictable execution

**Cons:**
- No automatic tool selection
- More code to maintain
- Less flexible

## JavaScript-Heavy Sites

### Common Challenges

1. **Content Not Loaded**: Page returns empty/incomplete HTML
2. **Click Required**: Content hidden behind interactions
3. **Infinite Scroll**: Pagination via scroll events
4. **Form Submission**: Need to fill forms and submit

### Solutions with Playwright Tools

**Challenge 1: Content Not Loaded**

```python
# Solution: Wait for elements before extracting
await navigate.ainvoke({"url": target_url})
await asyncio.sleep(2)  # Wait for JS execution
elements = await get_elements.ainvoke({"selector": ".dynamic-content"})
```

**Challenge 2: Click Required**

```python
# Solution: Use ClickTool to trigger interactions
await click.ainvoke({"selector": ".show-more-button"})
await asyncio.sleep(1)  # Wait for content reveal
text = await extract_text.ainvoke({})
```

**Challenge 3: Infinite Scroll**

```python
# Solution: Use agent to iteratively scroll and extract
prompt = """
Navigate to the job board, then:
1. Scroll down to load more jobs
2. Extract all visible job titles
3. Repeat scroll 3 times
4. Return all collected titles
"""
result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
```

**Challenge 4: Form Submission**

Note: PlayWrightBrowserToolkit doesn't include a form fill tool by default. You can:

1. **Use ClickTool + Type**: Click input, type text
2. **Custom Tool**: Create custom form fill tool
3. **Direct Playwright**: Use browser context directly

```python
# Option 2: Custom form fill tool
from langchain_core.tools import tool

@tool
async def fill_form(field_selector: str, value: str) -> str:
    """Fill a form field with a value."""
    page = await async_browser.new_page()
    await page.fill(field_selector, value)
    return f"Filled {field_selector} with {value}"

tools = toolkit.get_tools() + [fill_form]
```

## Error Handling

### ToolNode Automatic Error Handling

LangGraph's `ToolNode` catches exceptions and returns them as `ToolMessage` objects:

```python
# ToolNode handles errors automatically
tool_node = ToolNode(tools)

# If a tool raises an exception:
# 1. Exception is caught
# 2. ToolMessage created with error status
# 3. Returned to agent for recovery
```

### Custom Error Handling

```python
async def resilient_scrape_node(state):
    """Node with custom error handling."""
    try:
        await navigate.ainvoke({"url": state["url"]})
        text = await extract_text.ainvoke({})
        return {"scraped_data": {"text": text}, "error": None}
    except Exception as e:
        # Accumulate error in state (don't raise)
        return {
            "error": f"Scraping failed: {str(e)}",
            "messages": [AIMessage(content=f"Error: {str(e)}")]
        }
```

## Performance Considerations

### Browser Lifecycle

```python
# Create browser once, reuse across invocations
async_browser = create_async_playwright_browser()
toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)

# Use in multiple graph invocations
result1 = await graph.ainvoke(state1)
result2 = await graph.ainvoke(state2)

# Close when done
await async_browser.close()
```

### Headless vs Headed

```python
# Headless (faster, production)
from langchain_community.tools.playwright.utils import (
    create_async_playwright_browser
)

browser = create_async_playwright_browser()  # Headless by default

# Headed (debugging, development)
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(headless=False)
    # ... use browser
```

### Parallel Tool Execution

```python
# Disable parallel tool calls for sequential operations
llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)

agent = create_react_agent(
    model=llm_with_tools,
    tools=tools
)
```

## Migration from LangChain Agents

### AgentExecutor → create_react_agent

**Before (LangChain):**

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent

agent = create_openai_tools_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
result = executor.invoke({"input": "scrape website"})
```

**After (LangGraph):**

```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(model=llm, tools=tools)
result = await agent.ainvoke({
    "messages": [{"role": "user", "content": "scrape website"}]
})
```

### Key Changes

| LangChain | LangGraph | Notes |
|-----------|-----------|-------|
| `prompt` with scratchpad | `prompt` parameter optional | System message format |
| `max_iterations` | `recursion_limit` in config | Multiply by 2, add 1 |
| `memory` | `checkpointer` | Simplified persistence |
| `return_intermediate_steps` | Full message state | Always available |

## Best Practices

### 1. Always Use Async

```python
# ✅ Correct
async_browser = create_async_playwright_browser()
result = await agent.ainvoke(state)

# ❌ Wrong
sync_browser = create_sync_playwright_browser()  # Slower, blocks
```

### 2. Cleanup Resources

```python
try:
    browser = create_async_playwright_browser()
    # ... use browser
finally:
    await browser.close()  # Always cleanup
```

### 3. Provide Clear Tool Instructions

```python
# ✅ Specific prompt
"Navigate to example.com, click the 'Jobs' link, then extract all job titles from h2.job-title elements"

# ❌ Vague prompt
"Get job listings"
```

### 4. Handle Timeouts

```python
# Set timeout in config
result = await agent.ainvoke(
    state,
    config={"configurable": {"step_timeout": 30}}  # 30 second timeout
)
```

### 5. Use Type Safety

```python
from typing import TypedDict, Annotated

class BrowserState(TypedDict, total=False):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    url: str
    data: dict
```

## Troubleshooting

### Issue: "Browser executable not found"

**Solution:**
```bash
playwright install chromium
```

### Issue: "KeyError in tool invocation"

**Cause:** Pydantic V2 compatibility issue

**Solution:**
```bash
pip install --upgrade langchain langchain-community langchain-core
```

### Issue: "Tool returns empty results"

**Causes:**
1. JavaScript not finished loading
2. Wrong CSS selector
3. Content in iframe

**Solutions:**
```python
# Wait for content
await asyncio.sleep(2)

# Verify selector with get_elements
elements = await get_elements.ainvoke({
    "selector": "h1",
    "attributes": ["innerText", "className"]
})
print(elements)  # Debug output

# Check for iframes (requires custom tool)
```

### Issue: "Agent loops without ending"

**Cause:** LLM keeps making tool calls

**Solution:**
```python
# Set recursion limit
result = await agent.ainvoke(
    state,
    config={"recursion_limit": 10}
)
```

## Example: Job Scraping Agent

Complete example in `examples/browser_agent_example.py`:

```python
async def scrape_job_posting(job_url: str) -> dict:
    """Scrape job posting from JavaScript-heavy job board."""

    # Initialize
    browser = create_async_playwright_browser()
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    agent = create_react_agent(model=llm, tools=toolkit.get_tools())

    # Scrape
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": f"Extract job title, company, requirements from {job_url}"
        }]
    })

    # Cleanup
    await browser.close()

    return result
```

## Resources

- **Example Code**: `examples/browser_agent_example.py`
- **LangChain Playwright Docs**: https://python.langchain.com/docs/integrations/tools/playwright/
- **LangGraph Tool Calling**: https://langchain-ai.github.io/langgraph/how-tos/tool-calling/
- **Playwright API**: https://playwright.dev/python/
- **Migration Guide**: https://python.langchain.com/docs/how_to/migrate_agent/

## Summary

| Question | Answer |
|----------|--------|
| **Can LangChain tools be used in LangGraph?** | Yes, directly with no conversion |
| **Are adapters required?** | No |
| **Which pattern to use?** | `create_react_agent` for most cases |
| **Best for JavaScript sites?** | Yes, Playwright handles dynamic content |
| **Performance impact?** | Slightly slower than HTTP, but necessary for JS sites |
| **Production ready?** | Yes, used in production LangGraph apps |
