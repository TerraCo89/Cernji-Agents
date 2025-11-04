"""
LangGraph Browser Automation with Playwright Toolkit
=====================================================

RECOMMENDED APPROACH for most use cases.

This example demonstrates the official LangChain PlayWrightBrowserToolkit
integration with LangGraph. No custom code required - works out-of-box!

Features:
- 7 pre-built browser tools (navigate, click, extract, etc.)
- Handles JavaScript-heavy sites with wait_until='networkidle'
- Multi-browser support (Chromium, Firefox, WebKit)
- Maintained by LangChain team

Installation:
    pip install playwright langchain-community langgraph langchain-anthropic
    playwright install chromium

Usage:
    python playwright_toolkit_example.py
"""

import asyncio
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, add_messages
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_async_playwright_browser
from langchain.agents import create_react_agent as create_agent
from langchain_anthropic import ChatAnthropic


# ============================================================================
# EXAMPLE 1: Simple ReAct Agent (Recommended for beginners)
# ============================================================================

async def example_1_simple_agent():
    """
    Simplest approach: Use create_agent with toolkit tools.

    Best for: Quick prototyping, standard web automation tasks
    """
    print("=== Example 1: Simple ReAct Agent ===\n")

    # Initialize async browser
    async_browser = create_async_playwright_browser(
        headless=False  # Set to True for production
    )

    # Create toolkit with 7 browser tools
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
    tools = toolkit.get_tools()

    print(f"Loaded {len(tools)} browser tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    print()

    # Initialize LLM
    llm = ChatAnthropic(
        model="claude-sonnet-4-5",
        temperature=0
    )

    # Create ReAct agent - tools work directly with LangGraph!
    agent = create_agent(model=llm, tools=tools)

    try:
        # Execute browser automation task
        result = await agent.ainvoke({
            "messages": [
                HumanMessage(content="""
                Navigate to https://www.example.com and extract the main heading text.
                Then tell me what you found.
                """)
            ]
        })

        print("\n=== Agent Response ===")
        for message in result["messages"]:
            if isinstance(message, AIMessage):
                print(f"Assistant: {message.content}\n")

    finally:
        # Clean up browser
        await async_browser.close()


# ============================================================================
# EXAMPLE 2: Custom StateGraph with Toolkit Tools
# ============================================================================

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode


class BrowserAgentState(TypedDict):
    """State for browser automation agent"""
    messages: Annotated[list[BaseMessage], add_messages]
    current_url: str
    extracted_data: str


async def example_2_custom_graph():
    """
    Custom StateGraph with PlayWrightBrowserToolkit tools.

    Best for: Workflows requiring custom logic or conditional routing
    """
    print("\n=== Example 2: Custom StateGraph ===\n")

    # Initialize browser and toolkit
    async_browser = create_async_playwright_browser(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
    tools = toolkit.get_tools()

    # Initialize LLM with tools
    llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    # Define nodes
    def agent_node(state: BrowserAgentState) -> dict:
        """Agent decides which tools to use"""
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def should_continue(state: BrowserAgentState) -> str:
        """Route to tools or end"""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    # Build graph
    graph = StateGraph(BrowserAgentState)

    # Add nodes
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))  # Toolkit tools work directly!

    # Define flow
    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", END: END}
    )
    graph.add_edge("tools", "agent")  # Return to agent after tools

    # Compile
    app = graph.compile()

    try:
        # Execute workflow
        result = await app.ainvoke({
            "messages": [
                HumanMessage(content="""
                Go to https://news.ycombinator.com and tell me:
                1. What is the title of the first article?
                2. How many points does it have?
                """)
            ],
            "current_url": "",
            "extracted_data": ""
        })

        print("\n=== Final Result ===")
        print(f"Last message: {result['messages'][-1].content}")

    finally:
        await async_browser.close()


# ============================================================================
# EXAMPLE 3: Job Scraper (Real-world use case)
# ============================================================================

async def example_3_job_scraper():
    """
    Real-world example: Scrape job postings from a careers page.

    Best for: Understanding how to build practical automation workflows
    """
    print("\n=== Example 3: Job Scraper ===\n")

    # Initialize browser
    async_browser = create_async_playwright_browser(headless=True)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
    tools = toolkit.get_tools()

    # Initialize LLM
    llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)

    # Create agent
    agent = create_agent(model=llm, tools=tools)

    try:
        # Multi-step job scraping workflow
        result = await agent.ainvoke({
            "messages": [
                HumanMessage(content="""
                Navigate to https://www.example-jobs.com/careers

                Then:
                1. Find all job listings on the page
                2. Extract the title and location of the first 3 jobs
                3. Summarize what you found in a structured format

                Take your time and wait for the page to fully load before extracting data.
                """)
            ]
        })

        print("\n=== Job Listings Found ===")
        print(result["messages"][-1].content)

    finally:
        await async_browser.close()


# ============================================================================
# EXAMPLE 4: Form Automation
# ============================================================================

async def example_4_form_automation():
    """
    Automate form filling and submission.

    Best for: Account creation, search automation, data entry
    """
    print("\n=== Example 4: Form Automation ===\n")

    # Initialize browser (headless=False to watch it work)
    async_browser = create_async_playwright_browser(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
    tools = toolkit.get_tools()

    # Initialize LLM
    llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)

    # Create agent
    agent = create_agent(model=llm, tools=tools)

    try:
        result = await agent.ainvoke({
            "messages": [
                HumanMessage(content="""
                Go to https://www.google.com

                Then:
                1. Find the search box
                2. Type "LangGraph browser automation"
                3. Click the search button or press Enter
                4. Wait for results to load
                5. Tell me the title of the first search result
                """)
            ]
        })

        print("\n=== Search Results ===")
        print(result["messages"][-1].content)

    finally:
        await async_browser.close()


# ============================================================================
# EXAMPLE 5: Multi-Page Navigation
# ============================================================================

async def example_5_multi_page_navigation():
    """
    Navigate across multiple pages and maintain context.

    Best for: Research tasks, data collection across sites
    """
    print("\n=== Example 5: Multi-Page Navigation ===\n")

    # Initialize browser
    async_browser = create_async_playwright_browser(headless=True)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
    tools = toolkit.get_tools()

    # Initialize LLM
    llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)

    # Create agent with checkpointing for conversation memory
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()

    agent = create_agent(
        model=llm,
        tools=tools,
        checkpointer=checkpointer
    )

    try:
        # Configuration for persistent conversation
        config = {"configurable": {"thread_id": "browser-session-1"}}

        # Step 1: Navigate to first site
        result1 = await agent.ainvoke(
            {"messages": [HumanMessage(content="Go to https://www.example.com")]},
            config=config
        )

        # Step 2: Navigate to second site (remembers previous context)
        result2 = await agent.ainvoke(
            {"messages": [HumanMessage(content="Now go to https://www.wikipedia.org")]},
            config=config
        )

        # Step 3: Reference previous navigation
        result3 = await agent.ainvoke(
            {"messages": [HumanMessage(content="What was the first website I asked you to visit?")]},
            config=config
        )

        print("\n=== Navigation History ===")
        print(result3["messages"][-1].content)

    finally:
        await async_browser.close()


# ============================================================================
# MAIN: Run Examples
# ============================================================================

async def main():
    """Run all examples (comment out ones you don't want to run)"""

    # Example 1: Simple ReAct agent (recommended starting point)
    await example_1_simple_agent()

    # Example 2: Custom StateGraph (for advanced workflows)
    # await example_2_custom_graph()

    # Example 3: Job scraper (real-world use case)
    # await example_3_job_scraper()

    # Example 4: Form automation (search, login, etc.)
    # await example_4_form_automation()

    # Example 5: Multi-page navigation (research tasks)
    # await example_5_multi_page_navigation()


if __name__ == "__main__":
    asyncio.run(main())
