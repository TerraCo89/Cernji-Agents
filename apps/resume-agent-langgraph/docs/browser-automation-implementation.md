# Browser Automation Implementation Guide

## Overview

The `create_scraper_agent()` function in `src/resume_agent/tools/browser_automation.py` implements a LangGraph ReAct agent for browser-based job scraping using the LangChain PlayWrightBrowserToolkit.

## Implementation Details

### Function Signature

```python
async def create_scraper_agent(
    browser,
    use_checkpointing: bool = False
) -> CompiledGraph
```

### Parameters

- **browser** (AsyncPlaywrightBrowser): Playwright browser instance from `create_async_playwright_browser()`
- **use_checkpointing** (bool, optional): Enable conversation memory across invocations
  - Default: `False` (recommended for most use cases)
  - Warning: Playwright Page objects are not serializable. Only use if maintaining browser instance across multiple agent invocations within the same session.

### Returns

- **CompiledGraph**: LangGraph ReAct agent with 7 browser tools bound

### Implementation Steps

The implementation follows the pattern from `.claude/skills/langgraph-builder/examples/browser-automation/playwright_toolkit_example.py`:

#### 1. Initialize PlayWrightBrowserToolkit

```python
toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
tools = toolkit.get_tools()
```

The toolkit provides 7 pre-built browser tools:
- `navigate_browser` - Navigate to URLs with wait_until support
- `click_element` - Click on page elements
- `extract_text` - Extract text from specific elements
- `get_elements` - Find elements matching criteria
- `extract_hyperlinks` - Get all links from page
- `get_current_page` - Get current page state
- `navigate_back` - Go back to previous page

#### 2. Initialize LLM

```python
llm = ChatAnthropic(
    model="claude-sonnet-4-5",
    temperature=0  # Deterministic for reliable extraction
)
```

Uses Claude Sonnet 4.5 for:
- Superior reasoning on complex multi-step scraping workflows
- Intelligent tool selection
- Robust handling of dynamic content

Temperature set to 0 for deterministic, reliable data extraction.

#### 3. Create ReAct Agent

```python
from langchain.agents import create_react_agent as create_agent

# Without checkpointing (default, recommended)
agent = create_agent(model=llm, tools=tools)

# With checkpointing (optional, advanced use case)
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
agent = create_agent(model=llm, tools=tools, checkpointer=checkpointer)
```

The `create_agent()` function (formerly `create_react_agent` from `langgraph.prebuilt`) automatically:
- Binds tools to the LLM
- Sets up tool calling logic
- Handles routing between agent and tools
- Manages conversation state

#### 4. Return Compiled Agent

The agent is ready for invocation with:

```python
result = await agent.ainvoke({
    "messages": [HumanMessage(content="Navigate to example.com and extract title")]
})
```

## Usage Examples

### Basic Usage

```python
from resume_agent.tools.browser_automation import create_browser_context, create_scraper_agent
from langchain_core.messages import HumanMessage

async with create_browser_context(headless=True) as browser:
    agent = await create_scraper_agent(browser)

    result = await agent.ainvoke({
        "messages": [HumanMessage(content="""
        Navigate to https://japan-dev.com/jobs/12345
        Extract the job title, company name, and location.
        """)]
    })

    print(result["messages"][-1].content)
```

### With Checkpointing (Advanced)

```python
async with create_browser_context(headless=True) as browser:
    agent = await create_scraper_agent(browser, use_checkpointing=True)

    config = {"configurable": {"thread_id": "scraping-session-1"}}

    # Step 1: Navigate
    result1 = await agent.ainvoke(
        {"messages": [HumanMessage(content="Go to example.com")]},
        config=config
    )

    # Step 2: Extract (remembers previous context)
    result2 = await agent.ainvoke(
        {"messages": [HumanMessage(content="Extract the main heading")]},
        config=config
    )
```

### Integration with Site-Specific Scrapers

```python
async def scrape_japan_dev_job(url: str) -> JobPostingData:
    """Site-specific scraper using the agent."""
    async with create_browser_context(headless=True) as browser:
        agent = await create_scraper_agent(browser)

        extraction_prompt = f"""
        Navigate to {url} and extract:
        1. Job title
        2. Company name
        3. Location
        4. Job description
        5. Required skills

        Wait for the page to fully load before extraction.
        """

        result = await agent.ainvoke({
            "messages": [HumanMessage(content=extraction_prompt)]
        })

        # Parse LLM response into structured data
        return parse_job_data(result["messages"][-1].content)
```

## Design Patterns

### Browser Lifecycle Management

Always use the `create_browser_context()` async context manager:

```python
async with create_browser_context(headless=True) as browser:
    agent = await create_scraper_agent(browser)
    # Use agent...
# Browser automatically closes
```

This ensures proper cleanup even if scraping fails.

### Error Handling

The ReAct agent handles tool errors gracefully. You should wrap invocations in try/except for network errors:

```python
try:
    result = await agent.ainvoke({"messages": [...]})
except Exception as e:
    logger.error(f"Scraping failed: {e}")
    # Handle error
```

### Retries

For production use, implement retry logic:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def scrape_with_retry(url: str) -> JobPostingData:
    async with create_browser_context() as browser:
        agent = await create_scraper_agent(browser)
        result = await agent.ainvoke({"messages": [...]})
        return parse_result(result)
```

## LangGraph Best Practices

### 1. Tool Compatibility

The PlayWrightBrowserToolkit tools work directly with LangGraph - no custom wrappers needed.

### 2. State Management

- No need for custom state schemas for simple scraping
- Use checkpointing only when conversation memory is required
- Remember: Page objects are not serializable

### 3. ReAct Pattern

The agent uses ReAct (Reason + Act) pattern:
1. **Reason**: LLM analyzes task and decides which tools to use
2. **Act**: Execute tools (navigate, click, extract)
3. **Observe**: Process tool results
4. **Repeat**: Continue until task complete

### 4. Prompt Engineering

Be explicit in your scraping prompts:
- Specify wait conditions ("Wait for page to load")
- List exact data to extract
- Provide fallback behavior ("If not found, return 'Not specified'")
- Request structured format for easier parsing

## Testing

### Structure Tests

Run structure validation without full dependencies:

```bash
python tests/test_browser_automation_structure.py
```

### Integration Tests

Requires full dependencies installed:

```bash
pip install langchain-community playwright
playwright install chromium

pytest tests/test_browser_automation_integration.py
```

### Manual Testing

Use the test function in the module:

```bash
cd apps/resume-agent-langgraph
python -c "import asyncio; from src.resume_agent.tools.browser_automation import test_scraper; asyncio.run(test_scraper())"
```

## Performance Considerations

### Headless vs Headful

- **Headless** (`headless=True`): Faster, use for production
- **Headful** (`headless=False`): Slower, use for debugging

### Wait Strategies

The toolkit's `navigate_browser` tool supports wait conditions:
- `networkidle`: Wait until no network activity (recommended for JS-heavy sites)
- `domcontentloaded`: Wait for DOM ready (faster but may miss dynamic content)
- `load`: Wait for full page load (default)

### Parallel Scraping

For scraping multiple URLs, use asyncio.gather:

```python
urls = ["url1", "url2", "url3"]
results = await asyncio.gather(*[scrape_job_posting(url) for url in urls])
```

Each scrape gets its own browser instance (via context manager).

## Troubleshooting

### "Module not found: langchain_community"

Install dependencies:
```bash
pip install -e .
# Or specifically:
pip install langchain-community playwright
```

### "Browser not installed"

Install Playwright browsers:
```bash
playwright install chromium
```

### "Page object not serializable"

Don't use checkpointing with short-lived browser sessions. The error occurs when trying to serialize Playwright Page objects. Use `use_checkpointing=False` (default) for most cases.

### Timeout Errors

Increase timeout in navigation:
```python
# In your prompt:
"Navigate to {url} and wait for networkidle before extracting"
```

Or adjust Playwright timeout:
```python
browser = create_async_playwright_browser(
    headless=True,
    slow_mo=1000  # Slow down by 1 second per operation
)
```

## References

- **Reference Implementation**: `.claude/skills/langgraph-builder/examples/browser-automation/playwright_toolkit_example.py`
- **LangGraph Docs**: https://python.langchain.com/docs/langgraph
- **PlayWrightBrowserToolkit**: https://python.langchain.com/docs/integrations/toolkits/playwright
- **Playwright Docs**: https://playwright.dev/python/docs/intro
- **ReAct Paper**: https://arxiv.org/abs/2210.03629

## Related Files

- `src/resume_agent/tools/browser_automation.py` - Main implementation
- `tests/test_browser_automation_structure.py` - Structure validation tests
- `.claude/skills/langgraph-builder/examples/browser-automation/` - Example implementations
- `.claude/skills/langgraph-builder/references/browser-automation-patterns.md` - Pattern guide
