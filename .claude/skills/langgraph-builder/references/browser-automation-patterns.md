# Browser Automation Patterns for LangGraph

Comprehensive guide to integrating browser automation with LangGraph for navigating JavaScript-heavy websites.

## Quick Reference

| Approach | Best For | Complexity | Setup Time |
|----------|----------|------------|------------|
| **Playwright Toolkit** | Production, standard tasks | Low | 5 min |
| **MCP Integration** | Claude Desktop, standardization | Medium | 15 min |
| **Custom Tools** | Specialized workflows | Medium-High | 30 min |
| **Vision-Enabled** | Complex UIs, visual tasks | High | 1 hour |

## 1. Playwright Toolkit (Recommended)

### Overview
Official LangChain integration providing 7 pre-built browser automation tools.

### When to Use
- ✅ Production deployments
- ✅ Standard web automation tasks (scraping, forms, navigation)
- ✅ Teams wanting maintained, tested code
- ✅ Rapid prototyping

### Architecture Pattern
```
LangGraph Agent → PlayWrightBrowserToolkit → Playwright → Browser
```

### Key Code Pattern
```python
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_async_playwright_browser
from langgraph.prebuilt import create_react_agent

# Initialize browser and toolkit
async_browser = create_async_playwright_browser(headless=True)
toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
tools = toolkit.get_tools()

# Create agent - tools work directly!
agent = create_react_agent(model=llm, tools=tools)
```

### Available Tools
1. **navigate_browser** - Navigate to URLs
2. **previous_page** - Go back
3. **click_element** - Click via CSS selector
4. **extract_text** - Parse page content with BeautifulSoup
5. **extract_hyperlinks** - Get all links
6. **get_elements** - Select elements by CSS
7. **current_page** - Get current URL

### JavaScript Handling
```python
# Toolkit automatically waits for network idle
await page.goto(url, wait_until="networkidle")
```

### Pros & Cons
**Pros:**
- Zero setup, works out-of-box
- Maintained by LangChain team
- Handles 90% of use cases
- Multi-browser support

**Cons:**
- Less granular control than raw Playwright
- Basic toolset may need customization

### References
- **Example**: `examples/browser-automation/playwright_toolkit_example.py`
- **Docs**: https://python.langchain.com/docs/integrations/tools/playwright/

---

## 2. MCP Integration (Modern Approach)

### Overview
Uses Model Context Protocol (MCP) servers for standardized browser automation via Microsoft's official Playwright MCP server.

### When to Use
- ✅ Building for Claude Desktop, Cursor, VS Code
- ✅ Want standardized tool interfaces
- ✅ Need plug-and-play tools (500+ MCP servers available)
- ✅ Prefer accessibility tree over vision models (faster, cheaper)

### Architecture Pattern
```
LangGraph Agent → langchain-mcp-adapters → MCP Client → MCP Server → Playwright
```

### Key Code Pattern
```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# Configure MCP client
client = MultiServerMCPClient({
    "playwright": {
        "command": "npx",
        "args": ["@playwright/mcp@latest", "--headless"],
        "transport": "stdio"
    }
})

# Auto-discover tools
tools = await client.get_tools()
agent = create_react_agent(llm, tools)
```

### Available MCP Tools
- `browser_navigate` - Load URLs
- `browser_click` - Click elements with modifiers
- `browser_type` - Type text character-by-character
- `browser_fill` - Fill form fields
- `browser_snapshot` - Capture accessibility tree
- `browser_evaluate` - Execute JavaScript
- `browser_take_screenshot` - Screenshots
- `browser_console_messages` - Console logs
- Tab management, network monitoring, and more

### MCP vs Direct Integration

| Factor | MCP | Direct |
|--------|-----|--------|
| **Standardization** | ✅ Works with any MCP client | ❌ App-specific |
| **Performance** | ⚠️ Protocol overhead | ✅ Lower latency |
| **Ecosystem** | ✅ 500+ servers | ❌ Build yourself |
| **Control** | ⚠️ Limited | ✅ Full control |
| **Debugging** | ⚠️ Cross-process | ✅ In-process |

### Pros & Cons
**Pros:**
- Standardized interface
- Works with Claude Desktop, Cursor
- Accessibility tree (no vision model needed)
- Lower costs

**Cons:**
- Additional process overhead
- Requires Node.js
- Security concerns (43% of MCP servers have vulnerabilities - use official Microsoft server)

### References
- **Example**: `examples/browser-automation/mcp_integration_example.py`
- **Docs**: https://langchain-ai.github.io/langgraph/agents/mcp/
- **Microsoft MCP**: https://github.com/microsoft/playwright-mcp

---

## 3. Custom Tools (Maximum Control)

### Overview
Build your own browser automation tools from scratch using `@tool` decorator and `InjectedToolArg`.

### When to Use
- ✅ Need fine-grained control over browser behavior
- ✅ Custom business logic
- ✅ Specialized workflows not covered by toolkit
- ✅ Performance optimization for specific use cases

### Architecture Pattern
```
LangGraph Agent → Custom @tool Functions → Playwright API → Browser
```

### Key Code Pattern
```python
from langchain_core.tools import tool, InjectedToolArg
from typing import Annotated
from playwright.async_api import Page

@tool
async def click_element(
    selector: str,
    state: Annotated[dict, InjectedToolArg]
) -> str:
    """Click element by CSS selector"""
    page: Page = state["page"]

    try:
        await page.wait_for_selector(selector, state="visible", timeout=5000)
        await page.click(selector)
        return f"Clicked: {selector}"
    except Exception as e:
        return f"Error: {str(e)}"

# Use in LangGraph
tools = [click_element, type_text, extract_data, ...]
llm_with_tools = llm.bind_tools(tools)
```

### Common Custom Tools
1. **navigate_to_url** - Navigation with custom wait logic
2. **click_element** - Click with retry and fallback
3. **type_text** - Typing with human-like delays
4. **extract_text** - Custom extraction logic
5. **wait_for_ajax** - Wait for AJAX/fetch completion
6. **scroll_page** - Scrolling with amount control
7. **wait_for_element** - Dynamic content synchronization
8. **get_page_info** - URL, title, ready state

### State Management Pattern
```python
class BrowserState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    page: Page  # Non-serializable!
    current_url: str
    extracted_data: str
```

### Browser Lifecycle Pattern
```python
class BrowserContext:
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch()
        self.page = await self.browser.new_page()
        return self.page

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.page.close()
        await self.browser.close()
        await self.playwright.stop()

# Usage
async with BrowserContext() as page:
    result = await agent.ainvoke({"page": page, ...})
```

### Pros & Cons
**Pros:**
- Full control over browser behavior
- Custom business logic
- Performance optimization
- No dependency on external toolkits

**Cons:**
- More code to maintain
- Must handle edge cases yourself
- Takes longer to implement

### References
- **Example**: `examples/browser-automation/custom_tools_example.py`
- **Docs**: https://langchain-ai.github.io/langgraph/concepts/tools/

---

## 4. Vision-Enabled (Web Voyager Pattern)

### Overview
Uses annotated screenshots with bounding boxes. Vision models (GPT-4V, Claude 3.5) analyze numbered overlays to decide which elements to interact with.

### When to Use
- ✅ Complex, visually-driven UIs
- ✅ Need to verify visual appearance
- ✅ Layout changes frequently (no brittle selectors)
- ✅ Multi-site workflows with different designs

### Architecture Pattern
```
1. Annotate Page (inject JS, mark elements, number them)
2. Screenshot (capture with overlays)
3. Vision Model (analyze and decide action)
4. Execute Action (click bbox_id, type into bbox_id)
5. Repeat
```

### Key Code Pattern
```python
# JavaScript annotation
mark_script = """
() => {
    const elements = document.querySelectorAll('a, button, input');
    elements.forEach((el, index) => {
        const rect = el.getBoundingClientRect();
        // Create numbered overlay
        const overlay = document.createElement('div');
        overlay.textContent = index;
        overlay.style = 'position: fixed; ...';
        document.body.appendChild(overlay);
    });
}
"""
bboxes = await page.evaluate(mark_script)

# Capture screenshot
screenshot = base64.b64encode(await page.screenshot()).decode()

# Vision analysis
messages = [
    HumanMessage(content=[
        {"type": "text", "text": "What action should you take?"},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot}"}}
    ])
]
response = await llm.ainvoke(messages)
```

### State Schema
```python
class VisionBrowserState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    page: Page
    task: str
    screenshot: str  # Base64 annotated screenshot
    bboxes: List[BBox]  # Element coordinates
    prediction: Prediction  # Parsed action
    scratchpad: List[BaseMessage]  # Action history
    step_count: int
```

### Graph Flow
```
START → annotate → agent → execute → update_scratchpad → [continue/end]
```

### Pros & Cons
**Pros:**
- Works on visually complex interfaces
- No brittle CSS selectors
- Resilient to layout changes
- Good for multi-site workflows

**Cons:**
- Higher cost (vision API calls)
- Slower than accessibility tree
- Token-intensive
- Requires vision-capable model

### References
- **Example**: `examples/browser-automation/vision_enabled_example.py`
- **Tutorial**: https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/
- **Production**: https://github.com/DonGuillotine/langraph_browser_agent

---

## Common Patterns Across All Approaches

### 1. Waiting for JavaScript

```python
# Network idle
await page.goto(url, wait_until="networkidle")

# DOM content loaded
await page.wait_for_load_state("domcontentloaded")

# Specific element
await page.wait_for_selector(".dynamic-content", state="visible")

# Custom condition
await page.wait_for_function("() => window.appReady === true")

# AJAX completion
await page.evaluate("() => typeof jQuery === 'undefined' || jQuery.active === 0")
```

### 2. Error Handling

```python
@tool
async def robust_click(selector: str, state: Annotated[dict, InjectedToolArg]) -> str:
    page: Page = state["page"]
    max_retries = 3

    for attempt in range(max_retries):
        try:
            await page.wait_for_selector(selector, state="visible", timeout=5000)
            await page.click(selector)
            return f"Clicked: {selector}"
        except Exception as e:
            if attempt == max_retries - 1:
                return f"Failed after {max_retries} attempts: {str(e)}"
            await asyncio.sleep(1)
```

### 3. State Management

```python
# Use MemorySaver for Page objects (can't serialize to disk)
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
agent = create_react_agent(llm, tools, checkpointer=checkpointer)
```

### 4. Conditional Routing

```python
def should_continue(state: BrowserState) -> str:
    last_message = state["messages"][-1]

    # Check for tool calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Check for max steps
    if state.get("step_count", 0) >= 20:
        return END

    return END
```

### 5. Browser Configuration

```python
# Production configuration
browser = await playwright.chromium.launch(
    headless=True,  # Headless for production
    args=[
        "--disable-gpu",
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled"  # Anti-detection
    ]
)

page = await browser.new_page(
    viewport={"width": 1920, "height": 1080},
    user_agent="Mozilla/5.0 ..."  # Custom user agent
)
```

---

## Performance Considerations

### Headless vs Headed Mode

| Mode | Speed | Use Case |
|------|-------|----------|
| Headless | 2-15x faster | Production, testing |
| Headed | Slower | Development, debugging |

### Browser Pooling
```python
# Reuse browser instances for better performance
class BrowserPool:
    def __init__(self, size=5):
        self.browsers = []
        self.size = size

    async def get_browser(self):
        if len(self.browsers) < self.size:
            browser = await playwright.chromium.launch()
            self.browsers.append(browser)
        return self.browsers[len(self.browsers) % self.size]
```

### Resource Blocking
```python
# Block images, fonts, analytics for faster loads
await page.route("**/*", lambda route:
    route.abort() if route.request.resource_type in ["image", "font", "media"]
    else route.continue_()
)
```

---

## Security & Anti-Detection

### Stealth Configuration
```python
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)

# Remove webdriver flag
await page.evaluate("Object.defineProperty(navigator, 'webdriver', { get: () => undefined })")
```

### Domain Restrictions (MCP)
```json
{
  "playwright": {
    "args": [
      "@playwright/mcp@latest",
      "--allowed-origins", "https://example.com;https://trusted.com"
    ]
  }
}
```

---

## Production Deployment Checklist

- [ ] **Headless mode** enabled
- [ ] **Timeouts** configured (5-10s)
- [ ] **Error handling** with retry logic
- [ ] **Cleanup** via context managers or finally blocks
- [ ] **Checkpointing** with MemorySaver (Page objects not serializable)
- [ ] **Observability** (LangSmith integration)
- [ ] **Rate limiting** for scraping
- [ ] **User agent** randomization
- [ ] **Anti-detection** measures
- [ ] **Resource blocking** for performance
- [ ] **Browser pooling** for concurrency
- [ ] **Graceful shutdown** handling

---

## Troubleshooting Common Issues

### Issue: ChatAnthropic authentication error
**Symptom:**
```
TypeError: "Could not resolve authentication method. Expected either api_key or auth_token to be set..."
```

**Root Cause:** `.env` file exists but environment variables not loaded into Python process.

**Solution:** Load dotenv BEFORE creating browser agent
```python
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

# CRITICAL: Load at module level (top of file)
load_dotenv()

# Now ChatAnthropic can find ANTHROPIC_API_KEY
async def create_scraper_agent(browser):
    llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)
    # ... rest of agent setup
```

**See:** `llm-provider-integration.md` → "Environment Variable Loading (CRITICAL)" for complete guide

### Issue: Browser not closing
**Solution**: Use context managers or ensure cleanup in finally blocks
```python
async with BrowserContext() as page:
    # Work with page
# Browser auto-closes
```

### Issue: TimeoutError on dynamic content
**Solution**: Increase timeout or use explicit waits
```python
await page.wait_for_selector(selector, timeout=10000)
```

### Issue: "Page" object cannot be pickled
**Solution**: Use MemorySaver instead of disk-based checkpointers
```python
checkpointer = MemorySaver()  # Not SqliteSaver
```

### Issue: Element not clickable
**Solution**: Wait for visibility + scroll into view
```python
await page.wait_for_selector(selector, state="visible")
await element.scroll_into_view_if_needed()
await page.click(selector)
```

### Issue: Bot detection
**Solution**: Add stealth options
```python
options.add_argument("--disable-blink-features=AutomationControlled")
```

---

## Decision Matrix

Choose your approach based on requirements:

```
Need standard web automation? → Playwright Toolkit
Need Claude Desktop integration? → MCP
Need fine-grained control? → Custom Tools
Need visual verification? → Vision-Enabled

High performance required? → Custom Tools or Playwright Toolkit
Low latency critical? → Custom Tools (avoid MCP overhead)
Multi-site with layout changes? → Vision-Enabled
Complex forms and workflows? → Custom Tools
Simple scraping? → Playwright Toolkit
Rapid prototyping? → Playwright Toolkit or MCP
```

---

## Additional Resources

### Official Documentation
- **LangGraph Web Voyager**: https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/
- **Playwright Toolkit**: https://python.langchain.com/docs/integrations/tools/playwright/
- **MCP Integration**: https://langchain-ai.github.io/langgraph/agents/mcp/
- **Playwright Python**: https://playwright.dev/python/docs/intro

### Production Examples
- **browser-use**: https://github.com/browser-use/browser-use (71k stars)
- **Skyvern**: https://github.com/Skyvern-AI/skyvern (15k stars)
- **DonGuillotine**: https://github.com/DonGuillotine/langraph_browser_agent (educational)

### Learning Resources
- **LearnOpenCV Tutorial**: https://learnopencv.com/langgraph-building-a-visual-web-browser-agent/
- **LangGraph Concepts**: https://langchain-ai.github.io/langgraph/concepts/

### Community
- **LangGraph GitHub**: https://github.com/langchain-ai/langgraph
- **LangGraph Discussions**: https://github.com/langchain-ai/langgraph/discussions
- **Awesome-LangGraph**: https://github.com/von-development/awesome-LangGraph
