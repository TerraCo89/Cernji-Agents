"""
LangGraph Browser Automation with MCP (Model Context Protocol)
==============================================================

MODERN APPROACH using Microsoft's official Playwright MCP server.

This example demonstrates MCP integration with LangGraph for standardized
browser automation. Uses accessibility tree instead of screenshots for
faster, more deterministic navigation.

Features:
- Accessibility tree-based (no vision model required)
- Microsoft official Playwright MCP server
- Works with Claude Desktop, Cursor, VS Code
- Auto-discovers available tools
- Lower cost (no vision API calls)

Prerequisites:
    pip install langchain-mcp-adapters langgraph langchain-anthropic
    npm install -g @playwright/mcp  # Requires Node.js

Usage:
    python mcp_integration_example.py
"""

import asyncio
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, add_messages
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic


# ============================================================================
# EXAMPLE 1: Simple MCP Agent (Recommended)
# ============================================================================

async def example_1_simple_mcp_agent():
    """
    Simplest MCP approach: Auto-discover tools from MCP server.

    Best for: Claude Desktop integration, standardized interfaces
    """
    print("=== Example 1: Simple MCP Agent ===\n")

    # Configure MCP client with Microsoft Playwright server
    client = MultiServerMCPClient({
        "playwright": {
            "command": "npx",
            "args": ["@playwright/mcp@latest", "--headless"],
            "transport": "stdio"
        }
    })

    try:
        # Get tools from MCP server (auto-discovery!)
        tools = await client.get_tools()

        print(f"Discovered {len(tools)} MCP tools:")
        for tool in tools:
            print(f"  - {tool.name}")
        print()

        # Initialize LLM
        llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)

        # Create ReAct agent with MCP tools
        agent = create_react_agent(model=llm, tools=tools)

        # Execute browser automation
        result = await agent.ainvoke({
            "messages": [
                HumanMessage(content="""
                Navigate to https://www.example.com and take a screenshot.
                Then tell me what you see on the page.
                """)
            ]
        })

        print("\n=== Agent Response ===")
        for message in result["messages"]:
            if isinstance(message, AIMessage):
                print(f"Assistant: {message.content}\n")

    finally:
        # MCP client cleanup
        pass  # Client auto-cleans up


# ============================================================================
# EXAMPLE 2: Multi-Server MCP (Playwright + Other Services)
# ============================================================================

async def example_2_multi_server_mcp():
    """
    Connect to multiple MCP servers simultaneously.

    Best for: Complex workflows requiring multiple tools (browser + APIs + etc.)
    """
    print("\n=== Example 2: Multi-Server MCP ===\n")

    # Configure multiple MCP servers
    client = MultiServerMCPClient({
        # Local Playwright server (stdio transport)
        "playwright": {
            "command": "npx",
            "args": ["@playwright/mcp@latest", "--headless"],
            "transport": "stdio"
        },
        # You can add more MCP servers here:
        # "weather": {
        #     "url": "http://localhost:8000/mcp",
        #     "transport": "streamable_http",
        #     "headers": {"Authorization": "Bearer TOKEN"}
        # }
    })

    try:
        # Get all tools from all servers
        tools = await client.get_tools()

        print(f"Total tools from all servers: {len(tools)}")

        # Initialize LLM
        llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)

        # Create agent
        agent = create_react_agent(model=llm, tools=tools)

        # Execute multi-tool workflow
        result = await agent.ainvoke({
            "messages": [
                HumanMessage(content="""
                Navigate to https://github.com/microsoft/playwright-mcp
                and tell me what this MCP server does.
                """)
            ]
        })

        print("\n=== Result ===")
        print(result["messages"][-1].content)

    finally:
        pass


# ============================================================================
# EXAMPLE 3: Custom StateGraph with MCP Tools
# ============================================================================

class BrowserMCPState(TypedDict):
    """State for MCP-based browser automation"""
    messages: Annotated[list[BaseMessage], add_messages]
    current_url: str
    page_snapshot: str
    screenshot_data: str


async def example_3_custom_graph_mcp():
    """
    Custom StateGraph using MCP tools for fine-grained control.

    Best for: Workflows with custom business logic and routing
    """
    print("\n=== Example 3: Custom StateGraph with MCP ===\n")

    # Initialize MCP client
    client = MultiServerMCPClient({
        "playwright": {
            "command": "npx",
            "args": ["@playwright/mcp@latest", "--headless"],
            "transport": "stdio"
        }
    })

    try:
        # Get MCP tools
        tools = await client.get_tools()
        llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)
        llm_with_tools = llm.bind_tools(tools)

        # Define nodes
        def agent_node(state: BrowserMCPState) -> dict:
            """LLM decides which MCP tools to use"""
            response = llm_with_tools.invoke(state["messages"])
            return {"messages": [response]}

        async def tool_node(state: BrowserMCPState) -> dict:
            """Execute MCP tool calls"""
            from langchain_core.messages import ToolMessage

            last_message = state["messages"][-1]
            tool_responses = []

            for tool_call in last_message.tool_calls:
                # Find and invoke the MCP tool
                tool = next(t for t in tools if t.name == tool_call["name"])
                result = await tool.ainvoke(tool_call["args"])

                tool_responses.append(
                    ToolMessage(
                        content=str(result),
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"]
                    )
                )

            return {"messages": tool_responses}

        def should_continue(state: BrowserMCPState) -> str:
            """Route to tools or end"""
            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            return END

        # Build graph
        graph = StateGraph(BrowserMCPState)
        graph.add_node("agent", agent_node)
        graph.add_node("tools", tool_node)

        graph.add_edge(START, "agent")
        graph.add_conditional_edges(
            "agent",
            should_continue,
            {"tools": "tools", END: END}
        )
        graph.add_edge("tools", "agent")

        # Compile
        app = graph.compile()

        # Execute
        result = await app.ainvoke({
            "messages": [
                HumanMessage(content="Navigate to https://www.wikipedia.org and take a page snapshot")
            ],
            "current_url": "",
            "page_snapshot": "",
            "screenshot_data": ""
        })

        print("\n=== Final State ===")
        print(f"Messages: {len(result['messages'])}")
        print(f"Last response: {result['messages'][-1].content}")

    finally:
        pass


# ============================================================================
# EXAMPLE 4: Accessibility Tree Navigation (MCP Advantage)
# ============================================================================

async def example_4_accessibility_tree():
    """
    Use MCP's accessibility tree for deterministic navigation.

    MCP Advantage: Uses structured accessibility data instead of vision,
    making it faster and more reliable than screenshot-based approaches.

    Best for: Production systems requiring consistent element discovery
    """
    print("\n=== Example 4: Accessibility Tree Navigation ===\n")

    client = MultiServerMCPClient({
        "playwright": {
            "command": "npx",
            "args": ["@playwright/mcp@latest", "--headless"],
            "transport": "stdio"
        }
    })

    try:
        tools = await client.get_tools()
        llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)
        agent = create_react_agent(model=llm, tools=tools)

        # MCP Playwright uses browser_snapshot for accessibility tree
        result = await agent.ainvoke({
            "messages": [
                HumanMessage(content="""
                Navigate to https://news.ycombinator.com

                Use browser_snapshot to get the accessibility tree.
                Then tell me about the interactive elements you can see.

                This is faster and cheaper than using screenshots + vision models!
                """)
            ]
        })

        print("\n=== Accessibility Analysis ===")
        print(result["messages"][-1].content)

    finally:
        pass


# ============================================================================
# EXAMPLE 5: Stateful Multi-Step Workflow with Checkpointing
# ============================================================================

async def example_5_stateful_workflow():
    """
    Multi-step browser automation with persistent state.

    Best for: Long-running tasks, research workflows, data collection
    """
    print("\n=== Example 5: Stateful Workflow ===\n")

    client = MultiServerMCPClient({
        "playwright": {
            "command": "npx",
            "args": ["@playwright/mcp@latest", "--headless"],
            "transport": "stdio"
        }
    })

    try:
        tools = await client.get_tools()
        llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)

        # Create agent with memory
        checkpointer = MemorySaver()
        agent = create_react_agent(
            model=llm,
            tools=tools,
            checkpointer=checkpointer
        )

        # Configuration for persistent session
        config = {"configurable": {"thread_id": "mcp-browser-session-1"}}

        # Step 1: Navigate to first page
        print("Step 1: Navigating to GitHub...")
        result1 = await agent.ainvoke(
            {"messages": [HumanMessage(content="Go to https://github.com")]},
            config=config
        )

        # Step 2: Perform action (state persists)
        print("Step 2: Taking snapshot...")
        result2 = await agent.ainvoke(
            {"messages": [HumanMessage(content="Take a page snapshot")]},
            config=config
        )

        # Step 3: Reference previous actions
        print("Step 3: Recalling previous actions...")
        result3 = await agent.ainvoke(
            {"messages": [HumanMessage(content="What website did I ask you to visit?")]},
            config=config
        )

        print("\n=== Conversation History ===")
        print(result3["messages"][-1].content)

    finally:
        pass


# ============================================================================
# EXAMPLE 6: MCP Server Configuration Options
# ============================================================================

async def example_6_advanced_configuration():
    """
    Advanced MCP server configuration with custom options.

    Best for: Production deployments with specific requirements
    """
    print("\n=== Example 6: Advanced Configuration ===\n")

    # Advanced configuration with multiple options
    client = MultiServerMCPClient({
        "playwright": {
            "command": "npx",
            "args": [
                "@playwright/mcp@latest",
                "--browser", "chromium",  # or "firefox", "webkit"
                "--headless",
                "--viewport-size", "1920x1080",
                # Security: Restrict to specific domains
                # "--allowed-origins", "https://example.com;https://trusted.com",
                # Persistence: Use browser profile
                # "--user-data-dir", "/path/to/profile"
            ],
            "transport": "stdio"
        }
    })

    try:
        tools = await client.get_tools()
        llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)
        agent = create_react_agent(model=llm, tools=tools)

        result = await agent.ainvoke({
            "messages": [
                HumanMessage(content="Navigate to https://www.example.com and get the page snapshot")
            ]
        })

        print("\n=== Result ===")
        print(result["messages"][-1].content)

    finally:
        pass


# ============================================================================
# COMPARING MCP vs Direct Playwright
# ============================================================================

def print_comparison():
    """
    When to use MCP vs direct Playwright integration?
    """
    print("\n" + "="*70)
    print("MCP vs Direct Playwright Comparison")
    print("="*70)

    comparison = """
    Use MCP When:
    ✅ Building for Claude Desktop, Cursor, or VS Code
    ✅ Need standardized tool interfaces across projects
    ✅ Want to leverage 500+ pre-built MCP servers
    ✅ Prefer accessibility tree over vision models (faster, cheaper)
    ✅ Rapid prototyping with plug-and-play tools

    Use Direct Playwright When:
    ✅ High-performance, low-latency requirements
    ✅ Complex stateful browser workflows
    ✅ Need fine-grained control over browser lifecycle
    ✅ Single-application deployments
    ✅ Want to avoid protocol overhead

    MCP Advantages:
    - Standardization (works with any MCP client)
    - Ecosystem (500+ servers available)
    - Fast iteration
    - Lower costs (no vision API calls)

    Direct Integration Advantages:
    - Better performance (no protocol overhead)
    - Full control over browser state
    - Simpler debugging (in-process)
    - More flexible customization
    """

    print(comparison)


# ============================================================================
# MAIN: Run Examples
# ============================================================================

async def main():
    """Run MCP examples"""

    # Print comparison first
    print_comparison()

    # Example 1: Simple MCP agent (recommended starting point)
    await example_1_simple_mcp_agent()

    # Example 2: Multi-server MCP
    # await example_2_multi_server_mcp()

    # Example 3: Custom StateGraph with MCP tools
    # await example_3_custom_graph_mcp()

    # Example 4: Accessibility tree navigation (MCP advantage)
    # await example_4_accessibility_tree()

    # Example 5: Stateful multi-step workflow
    # await example_5_stateful_workflow()

    # Example 6: Advanced configuration
    # await example_6_advanced_configuration()


if __name__ == "__main__":
    asyncio.run(main())
