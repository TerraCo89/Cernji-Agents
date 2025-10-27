# Browser Automation Examples

This folder contains complete, production-ready examples of integrating browser automation with LangGraph for navigating JavaScript-heavy websites.

## Examples

### 1. `playwright_toolkit_example.py` (Recommended)
**Best for:** Production use, standard web automation tasks

Uses LangChain's official `PlayWrightBrowserToolkit` which provides 7 pre-built tools:
- NavigateTool - Navigate to URLs
- ClickTool - Click elements via CSS selector
- ExtractTextTool - Parse page content
- GetElementsTool - Select elements by CSS
- ExtractHyperlinksTool - Extract all links
- NavigateBackTool - Go to previous page
- CurrentPageTool - Get current URL

**Why use this:**
- Zero setup, works out-of-box with LangGraph
- Maintained by LangChain team
- Handles JavaScript with `wait_until='networkidle'`
- Multi-browser support (Chromium, Firefox, WebKit)

### 2. `mcp_integration_example.py`
**Best for:** Standardized tool interfaces, Claude Desktop integration

Uses Microsoft's official Playwright MCP server via `langchain-mcp-adapters`:
- Accessibility tree-based navigation (faster than vision)
- No vision model required
- Works with Claude Desktop, Cursor, VS Code
- 500+ available MCP servers in ecosystem

**Why use this:**
- Future-proof with MCP standard
- Plug-and-play tools
- Lower costs (no vision API calls)

### 3. `custom_tools_example.py`
**Best for:** Maximum control, specialized workflows

Demonstrates how to build custom browser automation tools:
- `@tool` decorator with `InjectedToolArg` for state access
- Context managers for browser lifecycle
- Error handling and retry logic
- Composable, stateless tool functions

**Why use this:**
- Full control over browser behavior
- Custom business logic
- Optimized for specific use cases

### 4. `vision_enabled_example.py`
**Best for:** Complex UIs, visual verification

Implements the Web Voyager pattern with annotated screenshots:
- Bounding box annotation with numbered overlays
- Vision model analysis (GPT-4V, Claude 3.5)
- StateGraph with annotate → agent → execute flow
- Resilient to layout changes

**Why use this:**
- Works on visually complex interfaces
- Doesn't rely on brittle CSS selectors
- Good for multi-site workflows

## Installation

### For Playwright Toolkit
```bash
pip install playwright langchain-community langgraph langchain-anthropic
playwright install chromium
```

### For MCP Integration
```bash
pip install langchain-mcp-adapters langgraph langchain-anthropic
npm install -g @playwright/mcp  # Requires Node.js
```

### For Custom Tools
```bash
pip install playwright langgraph langchain-anthropic
playwright install chromium
```

## Quick Start

```python
# Run the recommended example
python playwright_toolkit_example.py

# Or use MCP approach
python mcp_integration_example.py

# Or build custom tools
python custom_tools_example.py

# Or use vision-enabled navigation
python vision_enabled_example.py
```

## Common Patterns

### 1. Waiting for JavaScript
```python
await page.goto(url, wait_until="networkidle")  # Wait for network idle
await page.wait_for_selector(".dynamic-content")  # Wait for specific element
await page.wait_for_load_state("domcontentloaded")  # Wait for DOM
```

### 2. State Management
```python
class BrowserState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    page: Page  # Playwright page (non-serializable!)
    url: str
    screenshot: str  # base64
```

### 3. Error Handling
```python
@tool
async def click_element(selector: str, state: Annotated[dict, InjectedToolArg]) -> str:
    try:
        page: Page = state["page"]
        await page.wait_for_selector(selector, state="visible", timeout=5000)
        await page.click(selector)
        return f"Clicked: {selector}"
    except Exception as e:
        return f"Error: {str(e)}"
```

## Production Considerations

1. **Browser Lifecycle**: Use context managers (`async with`) for cleanup
2. **Headless Mode**: Set `headless=True` for production
3. **Timeouts**: Configure appropriate timeout values (5-10s)
4. **Stealth**: Add `--disable-blink-features=AutomationControlled` to avoid detection
5. **Checkpointing**: Use `MemorySaver` (Page objects aren't serializable)
6. **Observability**: Integrate with LangSmith for monitoring

## References

- **LangGraph Web Voyager**: https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/
- **Playwright Toolkit**: https://python.langchain.com/docs/integrations/tools/playwright/
- **MCP Integration**: https://langchain-ai.github.io/langgraph/agents/mcp/
- **Microsoft Playwright MCP**: https://github.com/microsoft/playwright-mcp
- **Browser-Use (Production)**: https://github.com/browser-use/browser-use

## Troubleshooting

### Browser not closing
Use context managers or ensure `await browser.close()` in finally blocks.

### TimeoutError on dynamic content
Increase timeout or use explicit waits: `page.wait_for_selector(selector, timeout=10000)`

### "Page" object cannot be pickled
Use `MemorySaver()` checkpointer instead of disk-based checkpointers.

### Element not clickable
Wait for element to be visible and enabled: `page.wait_for_selector(selector, state="visible")`

### Bot detection
Add stealth options:
```python
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option('excludeSwitches', ['enable-automation'])
```
