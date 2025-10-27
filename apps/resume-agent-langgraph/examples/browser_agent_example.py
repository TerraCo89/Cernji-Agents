"""
Example: Using LangChain PlayWrightBrowserToolkit with LangGraph

This example demonstrates how to integrate LangChain's browser automation tools
with LangGraph for scraping JavaScript-heavy websites like job boards.

Features:
- Direct use of PlayWrightBrowserToolkit in LangGraph
- Two implementation patterns: create_react_agent and custom StateGraph
- Asynchronous browser automation for dynamic content
- Error handling and state management

Requirements:
    pip install playwright lxml
    playwright install chromium
"""

import asyncio
import nest_asyncio
from typing import Annotated, TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, add_messages
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_async_playwright_browser
from langgraph.prebuilt import create_react_agent, ToolNode
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model

# Allow nested event loops (required for Jupyter/async contexts)
nest_asyncio.apply()


# =============================================================================
# State Schema for Custom Graph Implementation
# =============================================================================

class BrowserAgentState(TypedDict):
    """State schema for browser automation agent.

    Uses TypedDict (not Pydantic) for msgpack serialization compatibility.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    target_url: str
    scraped_data: dict
    error_message: str | None


# =============================================================================
# Pattern 1: Using create_react_agent (Simplest)
# =============================================================================

async def example_react_agent():
    """
    Simplest approach: Use LangGraph's prebuilt ReAct agent with Playwright tools.

    This pattern:
    - Automatically handles tool routing
    - Manages conversation state
    - Provides error handling via ToolNode
    - Requires minimal code
    """
    print("\n" + "="*80)
    print("PATTERN 1: Using create_react_agent with PlayWrightBrowserToolkit")
    print("="*80 + "\n")

    # Initialize Playwright browser
    async_browser = create_async_playwright_browser()

    # Create toolkit and extract tools
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
    tools = toolkit.get_tools()

    print(f"✓ Initialized {len(tools)} browser tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")

    # Initialize LLM (use environment variables for API keys)
    llm = init_chat_model(model="anthropic:claude-3-5-sonnet-latest", temperature=0)

    # Create ReAct agent - tools are passed directly!
    agent = create_react_agent(model=llm, tools=tools)

    # Invoke agent with task
    print("\n📋 Task: Navigate to LangChain website and extract headers")

    result = await agent.ainvoke({
        "messages": [HumanMessage(content="Go to https://www.langchain.com and tell me what the main headers are")]
    })

    # Extract final response
    final_message = result["messages"][-1]
    print(f"\n✓ Agent Response:\n{final_message.content}\n")

    # Cleanup
    await async_browser.close()

    return result


# =============================================================================
# Pattern 2: Custom StateGraph with ToolNode
# =============================================================================

async def example_custom_graph():
    """
    Advanced approach: Build custom StateGraph with explicit tool execution node.

    This pattern:
    - Provides fine-grained control over workflow
    - Custom state schema
    - Explicit error handling
    - Conditional routing based on state
    """
    print("\n" + "="*80)
    print("PATTERN 2: Custom StateGraph with ToolNode")
    print("="*80 + "\n")

    # Initialize browser and tools
    async_browser = create_async_playwright_browser()
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
    tools = toolkit.get_tools()

    # Initialize LLM with tools bound
    llm = init_chat_model(model="anthropic:claude-3-5-sonnet-latest", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    # Define agent node
    def agent_node(state: BrowserAgentState):
        """Agent decides which tools to call based on conversation."""
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # Create ToolNode for automatic tool execution
    tool_node = ToolNode(tools)

    # Define conditional edge function
    def should_continue(state: BrowserAgentState):
        """Route to tools if LLM made tool calls, otherwise end."""
        messages = state["messages"]
        last_message = messages[-1]

        # Check if last message has tool calls
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        return END

    # Build StateGraph
    graph_builder = StateGraph(BrowserAgentState)

    # Add nodes
    graph_builder.add_node("agent", agent_node)
    graph_builder.add_node("tools", tool_node)

    # Add edges
    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges(
        "agent",
        should_continue,
        ["tools", END]
    )
    graph_builder.add_edge("tools", "agent")  # Return to agent after tool execution

    # Compile graph
    graph = graph_builder.compile()

    print("✓ Graph compiled with nodes: agent, tools")
    print("✓ Conditional routing: agent → tools (if tool_calls) → agent → END\n")

    # Invoke graph
    print("📋 Task: Navigate to Python.org and extract navigation links")

    initial_state = {
        "messages": [HumanMessage(content="Go to https://www.python.org and list the main navigation links")],
        "target_url": "",
        "scraped_data": {},
        "error_message": None
    }

    result = await graph.ainvoke(initial_state)

    # Extract final response
    final_message = result["messages"][-1]
    print(f"\n✓ Agent Response:\n{final_message.content}\n")

    # Cleanup
    await async_browser.close()

    return result


# =============================================================================
# Pattern 3: Manual Tool Invocation in Custom Nodes
# =============================================================================

async def example_manual_tool_usage():
    """
    Most control: Manually invoke specific tools within custom node functions.

    This pattern:
    - Maximum control over tool execution
    - Custom error handling per tool
    - Selective tool usage
    - Explicit state updates
    """
    print("\n" + "="*80)
    print("PATTERN 3: Manual Tool Invocation in Custom Nodes")
    print("="*80 + "\n")

    # Initialize browser
    async_browser = create_async_playwright_browser()

    # Import specific tools
    from langchain_community.tools.playwright import (
        NavigateTool,
        ExtractTextTool,
        GetElementsTool
    )

    # Initialize specific tools
    navigate_tool = NavigateTool(async_browser=async_browser)
    extract_text_tool = ExtractTextTool(async_browser=async_browser)
    get_elements_tool = GetElementsTool(async_browser=async_browser)

    print("✓ Initialized specific tools: navigate, extract_text, get_elements\n")

    # Define custom node with manual tool invocation
    async def scrape_job_posting_node(state: BrowserAgentState):
        """Custom node that manually orchestrates tool calls."""
        url = state["target_url"]

        try:
            # Step 1: Navigate to URL
            print(f"📍 Navigating to: {url}")
            await navigate_tool.ainvoke({"url": url})

            # Step 2: Extract job title
            print("🔍 Extracting job title...")
            title_elements = await get_elements_tool.ainvoke({
                "selector": "h1.job-title, .job-title, h1",
                "attributes": ["innerText"]
            })

            # Step 3: Extract job description
            print("📄 Extracting page text...")
            page_text = await extract_text_tool.ainvoke({})

            # Package data
            scraped_data = {
                "url": url,
                "title": title_elements if title_elements else "Title not found",
                "text_preview": page_text[:500] if page_text else "No text extracted"
            }

            return {
                "scraped_data": scraped_data,
                "messages": [AIMessage(content=f"Successfully scraped job posting from {url}")]
            }

        except Exception as e:
            return {
                "error_message": f"Scraping failed: {str(e)}",
                "messages": [AIMessage(content=f"Error scraping {url}: {str(e)}")]
            }

    # Build simple graph
    graph_builder = StateGraph(BrowserAgentState)
    graph_builder.add_node("scrape", scrape_job_posting_node)
    graph_builder.add_edge(START, "scrape")
    graph_builder.add_edge("scrape", END)
    graph = graph_builder.compile()

    # Invoke graph
    print("📋 Task: Scrape LangChain documentation page\n")

    initial_state = {
        "messages": [],
        "target_url": "https://python.langchain.com/docs/introduction/",
        "scraped_data": {},
        "error_message": None
    }

    result = await graph.ainvoke(initial_state)

    # Display results
    if result.get("scraped_data"):
        print("\n✓ Scraped Data:")
        print(f"  Title: {result['scraped_data'].get('title')}")
        print(f"  Text Preview: {result['scraped_data'].get('text_preview')}...\n")

    # Cleanup
    await async_browser.close()

    return result


# =============================================================================
# Job Scraping Use Case: Complete Example
# =============================================================================

async def scrape_job_posting(job_url: str) -> dict:
    """
    Complete example: Scrape job posting from JavaScript-heavy job board.

    Args:
        job_url: URL of job posting to scrape

    Returns:
        dict: Extracted job data (title, company, description, requirements)
    """
    print("\n" + "="*80)
    print("COMPLETE EXAMPLE: Job Posting Scraper")
    print("="*80 + "\n")

    # Initialize browser and tools
    async_browser = create_async_playwright_browser()
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
    tools = toolkit.get_tools()

    # Initialize LLM
    llm = init_chat_model(model="anthropic:claude-3-5-sonnet-latest", temperature=0)

    # Create agent
    agent = create_react_agent(model=llm, tools=tools)

    # Construct detailed scraping prompt
    prompt = f"""
    Navigate to this job posting: {job_url}

    Extract the following information:
    1. Job title
    2. Company name
    3. Location
    4. Key requirements (top 5)
    5. Job description summary (2-3 sentences)

    Provide the information in a structured format.
    """

    print(f"📍 Scraping job posting: {job_url}\n")

    # Invoke agent
    result = await agent.ainvoke({
        "messages": [HumanMessage(content=prompt)]
    })

    # Extract response
    final_response = result["messages"][-1].content

    print("✓ Extraction Complete:\n")
    print(final_response)
    print()

    # Cleanup
    await async_browser.close()

    return {
        "url": job_url,
        "extracted_data": final_response,
        "tool_calls": len([m for m in result["messages"] if hasattr(m, 'tool_calls') and m.tool_calls])
    }


# =============================================================================
# Main Runner
# =============================================================================

async def main():
    """Run all examples."""

    print("\n" + "="*80)
    print("LangChain PlayWrightBrowserToolkit + LangGraph Integration Examples")
    print("="*80)

    # Example 1: ReAct Agent (Simplest)
    try:
        await example_react_agent()
    except Exception as e:
        print(f"❌ Example 1 failed: {e}\n")

    # Example 2: Custom StateGraph
    try:
        await example_custom_graph()
    except Exception as e:
        print(f"❌ Example 2 failed: {e}\n")

    # Example 3: Manual Tool Usage
    try:
        await example_manual_tool_usage()
    except Exception as e:
        print(f"❌ Example 3 failed: {e}\n")

    # Complete Example: Job Scraping
    try:
        # Use a public example URL
        example_job_url = "https://www.langchain.com/careers"
        await scrape_job_posting(example_job_url)
    except Exception as e:
        print(f"❌ Job scraping example failed: {e}\n")

    print("="*80)
    print("All examples completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Run all examples
    asyncio.run(main())
