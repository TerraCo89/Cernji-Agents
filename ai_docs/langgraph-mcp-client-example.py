"""
Example: Using MCP Client Inside LangGraph Nodes

This demonstrates Pattern #1 - calling MCP server via MCP client protocol.
Use this pattern when you need runtime decoupling or cross-language integration.
"""

import asyncio
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ============================================================================
# State Schema
# ============================================================================

class JobAnalysisState(TypedDict):
    """State for job analysis workflow"""
    job_url: str
    company: str
    job_title: str
    job_analysis: dict | None
    cached: bool
    errors: list[str]


# ============================================================================
# MCP Client Helper
# ============================================================================

class MCPClientHelper:
    """Helper for calling MCP server tools"""

    def __init__(self, server_command: str, server_args: list[str]):
        self.server_params = StdioServerParameters(
            command=server_command,
            args=server_args
        )

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call an MCP tool and return result"""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Call the tool
                result = await session.call_tool(tool_name, arguments=arguments)

                # Parse result (MCP returns ToolResult object)
                if hasattr(result, 'content'):
                    # Extract content from MCP response
                    if isinstance(result.content, list):
                        # Multiple content blocks
                        return {"data": [c.text for c in result.content]}
                    else:
                        # Single content block
                        return {"data": result.content}

                return {"data": result}


# ============================================================================
# LangGraph Nodes Using MCP Client
# ============================================================================

# Initialize MCP client (reuse across nodes)
mcp_client = MCPClientHelper(
    server_command="uv",
    server_args=["run", "apps/resume-agent/resume_agent.py"]
)


async def check_cache_node(state: JobAnalysisState) -> dict:
    """Check if job analysis is cached (via MCP)"""
    try:
        # Call MCP server's data_read_job_analysis tool
        result = await mcp_client.call_tool(
            "data_read_job_analysis",
            arguments={
                "company": state["company"],
                "job_title": state["job_title"]
            }
        )

        # Parse MCP response
        data = result.get("data", {})
        if data and data.get("status") != "not_found":
            return {
                "job_analysis": data.get("data"),
                "cached": True
            }

        return {"cached": False}

    except Exception as e:
        return {
            "cached": False,
            "errors": state["errors"] + [f"Cache check failed: {str(e)}"]
        }


async def analyze_job_node(state: JobAnalysisState) -> dict:
    """Analyze job posting using LLM (hypothetical MCP tool)"""
    try:
        # Call hypothetical MCP tool for job analysis
        result = await mcp_client.call_tool(
            "analyze_job_posting",
            arguments={"job_url": state["job_url"]}
        )

        return {
            "job_analysis": result.get("data"),
            "cached": False
        }

    except Exception as e:
        return {
            "errors": state["errors"] + [f"Analysis failed: {str(e)}"]
        }


async def save_analysis_node(state: JobAnalysisState) -> dict:
    """Save job analysis to database (via MCP)"""
    try:
        # Call MCP server's data_write_job_analysis tool
        result = await mcp_client.call_tool(
            "data_write_job_analysis",
            arguments={
                "company": state["company"],
                "job_title": state["job_title"],
                "job_data": state["job_analysis"]
            }
        )

        return {"errors": []}  # Success

    except Exception as e:
        return {
            "errors": state["errors"] + [f"Save failed: {str(e)}"]
        }


# ============================================================================
# Build Graph with Async Nodes
# ============================================================================

def build_job_analysis_graph():
    """Build LangGraph workflow using MCP client"""

    workflow = StateGraph(JobAnalysisState)

    # Add nodes (all async)
    workflow.add_node("check_cache", check_cache_node)
    workflow.add_node("analyze_job", analyze_job_node)
    workflow.add_node("save_analysis", save_analysis_node)

    # Define routing
    def should_skip_analysis(state: JobAnalysisState) -> str:
        """Skip analysis if cached"""
        return END if state.get("cached") else "analyze_job"

    def should_save(state: JobAnalysisState) -> str:
        """Save if no errors"""
        return "save_analysis" if not state.get("errors") else END

    # Set entry point
    workflow.set_entry_point("check_cache")

    # Add conditional edges
    workflow.add_conditional_edges(
        "check_cache",
        should_skip_analysis,
        {"analyze_job": "analyze_job", END: END}
    )

    workflow.add_conditional_edges(
        "analyze_job",
        should_save,
        {"save_analysis": "save_analysis", END: END}
    )

    workflow.add_edge("save_analysis", END)

    return workflow.compile()


# ============================================================================
# Usage Example
# ============================================================================

async def main():
    """Example usage of MCP-powered LangGraph workflow"""

    graph = build_job_analysis_graph()

    # Initial state
    state = {
        "job_url": "https://example.com/job",
        "company": "Example Corp",
        "job_title": "Software Engineer",
        "job_analysis": None,
        "cached": False,
        "errors": []
    }

    # Execute workflow (MCP calls happen inside nodes)
    result = await graph.ainvoke(state)

    print(f"Analysis complete: {result['job_analysis']}")
    print(f"From cache: {result['cached']}")
    print(f"Errors: {result['errors']}")


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================================
# Comparison: Pattern #1 (MCP Client) vs Pattern #2 (Direct Import)
# ============================================================================

"""
Pattern #1 (This File - MCP Client):
------------------------------------
✅ Runtime decoupling - MCP server can be upgraded independently
✅ Cross-language support - TypeScript → Python, Python → Rust, etc.
✅ Distributed systems - MCP server on different host/container
❌ Performance overhead - Process spawning + IPC for each call
❌ Complexity - Async/await, connection management, error handling
❌ Debugging difficulty - Two separate processes

Pattern #2 (Your Codebase - Direct Import):
-------------------------------------------
✅ Maximum performance - Direct function calls, no IPC
✅ Simple debugging - Single process, standard Python exceptions
✅ Type safety - Python type hints work across boundaries
✅ Code reuse - 70% of tools reused without duplication
❌ Same language only - Both must be Python
❌ Deployed together - Can't upgrade independently
❌ Import-time coupling - Changes to MCP server affect imports

Your Choice (Pattern #2) is Correct Because:
-------------------------------------------
- Both implementations are Python ✅
- Deployed together in monorepo ✅
- Share same SQLite database ✅
- Performance matters (career agent is interactive) ✅
- Development efficiency (70% code reuse) ✅
"""
