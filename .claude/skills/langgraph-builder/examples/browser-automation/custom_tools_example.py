"""
LangGraph Custom Browser Automation Tools
==========================================

MAXIMUM CONTROL approach for specialized workflows.

This example demonstrates how to build custom browser automation tools
from scratch using the @tool decorator and InjectedToolArg pattern.

Features:
- Full control over browser behavior
- Custom business logic in tools
- Composable, stateless tool functions
- Context managers for lifecycle management
- Error handling and retry logic

Installation:
    pip install playwright langgraph langchain-anthropic
    playwright install chromium

Usage:
    python custom_tools_example.py
"""

import asyncio
import platform
from typing import TypedDict, Annotated, Optional, List
from playwright.async_api import async_playwright, Page, Browser
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, add_messages
from langchain_core.tools import tool, InjectedToolArg
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic


# ============================================================================
# BROWSER CONTEXT MANAGER (Best Practice)
# ============================================================================

class BrowserContext:
    """
    Context manager for browser lifecycle management.
    Ensures proper cleanup even on errors.
    """

    def __init__(self, headless: bool = True, viewport_width: int = 1280, viewport_height: int = 720):
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.playwright = None
        self.browser = None
        self.page = None

    async def __aenter__(self):
        """Initialize browser on context entry"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page(
            viewport={"width": self.viewport_width, "height": self.viewport_height}
        )
        return self.page

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup browser on context exit"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        return False  # Don't suppress exceptions


# ============================================================================
# CUSTOM BROWSER TOOLS (Using @tool decorator + InjectedToolArg)
# ============================================================================

@tool
async def navigate_to_url(
    url: str,
    state: Annotated[dict, InjectedToolArg]
) -> str:
    """
    Navigate browser to specified URL and wait for page to load.

    Args:
        url: The URL to navigate to
    """
    try:
        page: Page = state["page"]

        # Navigate and wait for network idle (crucial for JS-heavy sites)
        await page.goto(url, wait_until="networkidle")

        # Additional wait for DOM content
        await page.wait_for_load_state("domcontentloaded")

        # Get page title as confirmation
        title = await page.title()

        return f"Successfully navigated to {url}. Page title: {title}"

    except Exception as e:
        return f"Error navigating to {url}: {str(e)}"


@tool
async def click_element(
    selector: str,
    state: Annotated[dict, InjectedToolArg]
) -> str:
    """
    Click on an element identified by CSS selector.

    Args:
        selector: CSS selector for the element (e.g., 'button.submit', '#login-btn')
    """
    try:
        page: Page = state["page"]

        # Wait for element to be visible and enabled
        await page.wait_for_selector(selector, state="visible", timeout=5000)

        # Scroll element into view
        element = await page.query_selector(selector)
        if element:
            await element.scroll_into_view_if_needed()

        # Small delay for smooth scroll
        await asyncio.sleep(0.3)

        # Try regular click first, fallback to JS click
        try:
            await page.click(selector)
        except:
            await page.evaluate(f"document.querySelector('{selector}').click()")

        return f"Successfully clicked element: {selector}"

    except Exception as e:
        return f"Error clicking element '{selector}': {str(e)}"


@tool
async def type_text(
    selector: str,
    text: str,
    submit: bool = False,
    state: Annotated[dict, InjectedToolArg] = None
) -> str:
    """
    Type text into an input field.

    Args:
        selector: CSS selector for the input field
        text: Text to type
        submit: Whether to press Enter after typing (default: False)
    """
    try:
        page: Page = state["page"]

        # Wait for input to be available
        await page.wait_for_selector(selector, state="visible")

        # Click to focus
        await page.click(selector)

        # Clear existing text
        select_all = "Meta+A" if platform.system() == "Darwin" else "Control+A"
        await page.keyboard.press(select_all)
        await page.keyboard.press("Backspace")

        # Type new text
        await page.keyboard.type(text)

        # Optionally submit
        if submit:
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)  # Wait for form submission

        return f"Successfully typed text into '{selector}'{' and submitted' if submit else ''}"

    except Exception as e:
        return f"Error typing into '{selector}': {str(e)}"


@tool
async def extract_text(
    selector: str,
    state: Annotated[dict, InjectedToolArg]
) -> str:
    """
    Extract text content from an element.

    Args:
        selector: CSS selector for the element
    """
    try:
        page: Page = state["page"]

        # Wait for element
        await page.wait_for_selector(selector, state="attached", timeout=5000)

        # Extract text
        element = await page.query_selector(selector)
        if element:
            text = await element.inner_text()
            return f"Text from '{selector}': {text.strip()}"
        else:
            return f"Element '{selector}' not found"

    except Exception as e:
        return f"Error extracting text from '{selector}': {str(e)}"


@tool
async def extract_all_text(
    selector: str,
    state: Annotated[dict, InjectedToolArg]
) -> str:
    """
    Extract text from all matching elements.

    Args:
        selector: CSS selector that may match multiple elements
    """
    try:
        page: Page = state["page"]

        # Wait for at least one element
        await page.wait_for_selector(selector, state="attached", timeout=5000)

        # Get all matching elements
        elements = await page.query_selector_all(selector)

        texts = []
        for i, element in enumerate(elements):
            text = await element.inner_text()
            if text.strip():
                texts.append(f"{i+1}. {text.strip()}")

        if texts:
            return f"Found {len(texts)} elements matching '{selector}':\n" + "\n".join(texts)
        else:
            return f"No elements with text found for '{selector}'"

    except Exception as e:
        return f"Error extracting texts from '{selector}': {str(e)}"


@tool
async def scroll_page(
    direction: str,
    amount: int = 500,
    state: Annotated[dict, InjectedToolArg] = None
) -> str:
    """
    Scroll the page up or down.

    Args:
        direction: 'up' or 'down'
        amount: Number of pixels to scroll (default: 500)
    """
    try:
        page: Page = state["page"]

        if direction.lower() == "up":
            delta_y = -amount
        elif direction.lower() == "down":
            delta_y = amount
        else:
            return f"Error: direction must be 'up' or 'down', got '{direction}'"

        await page.evaluate(f"window.scrollBy(0, {delta_y})")
        await asyncio.sleep(0.5)  # Wait for scroll to complete

        return f"Scrolled {direction} by {amount}px"

    except Exception as e:
        return f"Error scrolling: {str(e)}"


@tool
async def wait_for_element(
    selector: str,
    timeout: int = 10,
    state: Annotated[dict, InjectedToolArg] = None
) -> str:
    """
    Wait for an element to become visible (for dynamically loaded content).

    Args:
        selector: CSS selector for the element
        timeout: Maximum wait time in seconds (default: 10)
    """
    try:
        page: Page = state["page"]

        await page.wait_for_selector(
            selector,
            state="visible",
            timeout=timeout * 1000  # Convert to milliseconds
        )

        return f"Element '{selector}' is now visible"

    except Exception as e:
        return f"Timeout: Element '{selector}' did not become visible within {timeout} seconds"


@tool
async def wait_for_ajax(
    timeout: int = 10,
    state: Annotated[dict, InjectedToolArg] = None
) -> str:
    """
    Wait for all AJAX/fetch requests to complete.
    Essential for JavaScript-heavy single-page applications.

    Args:
        timeout: Maximum wait time in seconds (default: 10)
    """
    try:
        page: Page = state["page"]

        # Wait for network to be idle
        await page.wait_for_load_state("networkidle", timeout=timeout * 1000)

        # Wait for jQuery AJAX if present
        await page.evaluate("() => typeof jQuery === 'undefined' || jQuery.active === 0")

        return "All AJAX requests completed"

    except Exception as e:
        return f"AJAX wait timeout after {timeout} seconds: {str(e)}"


@tool
async def get_page_info(
    state: Annotated[dict, InjectedToolArg]
) -> str:
    """
    Get current page URL, title, and basic information.
    """
    try:
        page: Page = state["page"]

        url = page.url
        title = await page.title()
        ready_state = await page.evaluate("() => document.readyState")

        return f"URL: {url}\nTitle: {title}\nReady State: {ready_state}"

    except Exception as e:
        return f"Error getting page info: {str(e)}"


# ============================================================================
# STATE DEFINITION
# ============================================================================

class CustomBrowserState(TypedDict):
    """State for custom browser automation agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    page: Page  # Playwright page instance (non-serializable!)
    current_url: str
    extracted_data: List[str]


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_custom_browser_agent(page: Page) -> StateGraph:
    """
    Build a LangGraph agent with custom browser tools.

    Args:
        page: Playwright Page instance to be used by tools
    """
    # Collect all custom tools
    tools = [
        navigate_to_url,
        click_element,
        type_text,
        extract_text,
        extract_all_text,
        scroll_page,
        wait_for_element,
        wait_for_ajax,
        get_page_info
    ]

    # Initialize LLM
    llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    # Define nodes
    def agent_node(state: CustomBrowserState) -> dict:
        """Agent decides which tools to use"""
        system_prompt = SystemMessage(content="""
You are a browser automation assistant. You have access to custom browser tools.

Always wait for AJAX to complete after navigation before extracting data.
Use wait_for_element for dynamically loaded content.
Extract data methodically and confirm success before proceeding.
        """.strip())

        messages = [system_prompt] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: CustomBrowserState) -> str:
        """Route to tools or end"""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    # Build graph
    graph = StateGraph(CustomBrowserState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", END: END}
    )
    graph.add_edge("tools", "agent")

    # Compile with memory (Page objects can't be serialized to disk)
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


# ============================================================================
# EXAMPLES
# ============================================================================

async def example_1_basic_scraping():
    """Example 1: Basic web scraping with custom tools"""
    print("=== Example 1: Basic Scraping ===\n")

    async with BrowserContext(headless=False) as page:
        # Create agent
        agent = create_custom_browser_agent(page)

        # Execute
        config = {"configurable": {"thread_id": "custom-1"}}
        result = await agent.ainvoke(
            {
                "messages": [
                    HumanMessage(content="""
                    Navigate to https://www.example.com
                    Wait for the page to fully load
                    Then extract the main heading text
                    Tell me what you found
                    """)
                ],
                "page": page,
                "current_url": "",
                "extracted_data": []
            },
            config=config
        )

        print("\n=== Result ===")
        print(result["messages"][-1].content)


async def example_2_search_automation():
    """Example 2: Search form automation"""
    print("\n=== Example 2: Search Automation ===\n")

    async with BrowserContext(headless=False) as page:
        agent = create_custom_browser_agent(page)

        config = {"configurable": {"thread_id": "custom-2"}}
        result = await agent.ainvoke(
            {
                "messages": [
                    HumanMessage(content="""
                    Go to https://www.google.com
                    Type "LangGraph browser automation" into the search box
                    Submit the search
                    Wait for results to load
                    Extract the title of the first search result
                    """)
                ],
                "page": page,
                "current_url": "",
                "extracted_data": []
            },
            config=config
        )

        print("\n=== Search Result ===")
        print(result["messages"][-1].content)


async def example_3_dynamic_content():
    """Example 3: Handling dynamically loaded content"""
    print("\n=== Example 3: Dynamic Content ===\n")

    async with BrowserContext(headless=True) as page:
        agent = create_custom_browser_agent(page)

        config = {"configurable": {"thread_id": "custom-3"}}
        result = await agent.ainvoke(
            {
                "messages": [
                    HumanMessage(content="""
                    Navigate to https://news.ycombinator.com
                    Wait for AJAX to complete
                    Wait for the article list to be visible
                    Extract the titles of the first 5 articles
                    """)
                ],
                "page": page,
                "current_url": "",
                "extracted_data": []
            },
            config=config
        )

        print("\n=== Articles Found ===")
        print(result["messages"][-1].content)


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run custom tools examples"""

    # Example 1: Basic scraping
    await example_1_basic_scraping()

    # Example 2: Search automation
    # await example_2_search_automation()

    # Example 3: Dynamic content
    # await example_3_dynamic_content()


if __name__ == "__main__":
    asyncio.run(main())
