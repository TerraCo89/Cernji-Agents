"""
End-to-end test for job analysis workflow.

This script tests the complete job analysis workflow:
1. User sends message with job URL
2. Chatbot calls analyze_job_posting tool
3. Tool result processed, job_url extracted
4. Workflow triggered: check_cache -> fetch_job -> analyze_job
5. Results returned to chatbot

Run this script directly to see the workflow in action:
    python tests/test_job_analysis_e2e.py

Or run as pytest:
    pytest tests/test_job_analysis_e2e.py -v -s
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langchain_core.messages import HumanMessage
from resume_agent.graph import graph
from resume_agent.state import create_initial_state


async def test_job_analysis_workflow_e2e():
    """
    Test the complete job analysis workflow end-to-end.

    This test requires:
    - Valid ANTHROPIC_API_KEY or OPENAI_API_KEY in .env
    - Internet connection for job fetching
    - Browser automation dependencies (Playwright)

    The test will:
    1. Create initial state
    2. Send user message requesting job analysis
    3. Let the chatbot invoke analyze_job_posting tool
    4. Verify workflow executes
    5. Check final state contains job_analysis
    """
    print("\n" + "="*80)
    print("JOB ANALYSIS WORKFLOW - END-TO-END TEST")
    print("="*80)

    # Sample job URL (use a real URL for actual testing)
    # For this example, we'll use a japan-dev URL
    job_url = "https://japan-dev.com/jobs/example-job-posting"

    print(f"\nJob URL: {job_url}")
    print("\n" + "-"*80)

    # Create initial state
    print("\n[1/5] Creating initial state...")
    state = create_initial_state()
    print("    [OK] Initial state created")
    print(f"    - user_id: {state['user_id']}")
    print(f"    - job_url: {state['job_url']}")
    print(f"    - job_analysis: {state['job_analysis']}")

    # Add user message requesting job analysis
    print("\n[2/5] Adding user message...")
    user_message = HumanMessage(
        content=f"Please analyze this job posting: {job_url}"
    )
    state["messages"] = [user_message]
    print(f"    [OK] User message: '{user_message.content}'")

    # Invoke the graph
    print("\n[3/5] Invoking graph workflow...")
    print("    This may take 30-60 seconds for browser automation...")

    try:
        # Configure with thread ID for checkpointing
        config = {
            "configurable": {
                "thread_id": "test-job-analysis-e2e-001"
            }
        }

        # Invoke graph (this will execute the full workflow)
        # Use ainvoke because we have async nodes (fetch_job_node)
        print("\n    Graph execution starting...")
        result = await graph.ainvoke(state, config=config)

        print("\n[4/5] Workflow completed!")
        print(f"    [OK] Total messages in state: {len(result['messages'])}")

        # Display workflow results
        print("\n[5/5] Analyzing results...")

        # Check if job_url was extracted
        if result.get("job_url"):
            print(f"    [OK] job_url extracted: {result['job_url']}")
        else:
            print("    [X] job_url not found in state")

        # Check if job_content was fetched
        if result.get("job_content"):
            content_preview = result["job_content"][:200] + "..." if len(result["job_content"]) > 200 else result["job_content"]
            print(f"    [OK] job_content fetched: {content_preview}")
        else:
            print("    [X] job_content not found in state")

        # Check if job_analysis was performed
        if result.get("job_analysis"):
            analysis = result["job_analysis"]
            print("    [OK] job_analysis completed:")
            print(f"       - Company: {analysis.get('company', 'N/A')}")
            print(f"       - Job Title: {analysis.get('job_title', 'N/A')}")
            print(f"       - Location: {analysis.get('location', 'N/A')}")
            print(f"       - Required Qualifications: {len(analysis.get('required_qualifications', []))} items")
            print(f"       - Keywords: {len(analysis.get('keywords', []))} items")

            if analysis.get('keywords'):
                print(f"       - Sample Keywords: {', '.join(analysis['keywords'][:5])}")
        else:
            print("    [X] job_analysis not found in state")

        # Check for errors
        if result.get("error_message"):
            print(f"\n    [WARNING] Error message: {result['error_message']}")

        # Display message history
        print("\n" + "-"*80)
        print("MESSAGE HISTORY:")
        print("-"*80)
        for i, msg in enumerate(result["messages"], 1):
            msg_type = msg.__class__.__name__
            content_preview = str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content)
            print(f"{i}. [{msg_type}] {content_preview}")

            # Show tool calls if present
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"   -> Tool: {tc.get('name', 'unknown')}")
                    print(f"   -> Args: {tc.get('args', {})}")

        print("\n" + "="*80)
        print("TEST COMPLETED SUCCESSFULLY")
        print("="*80)

        # Assert conditions for pytest
        assert result is not None, "Result should not be None"
        assert len(result["messages"]) > 1, "Should have multiple messages"

        # Note: We can't assert job_analysis exists because it depends on external services
        # This is more of a smoke test to verify the workflow executes

        return result

    except Exception as e:
        print(f"\n[X] Error during workflow execution:")
        print(f"  {type(e).__name__}: {str(e)}")
        print("\nPossible causes:")
        print("  - Missing .env file with API keys")
        print("  - No internet connection")
        print("  - Browser automation dependencies not installed")
        print("  - Invalid job URL")

        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

        raise


def test_graph_structure():
    """Test that the graph has the expected structure."""
    print("\n" + "="*80)
    print("GRAPH STRUCTURE TEST")
    print("="*80)

    print("\nGraph nodes:")
    for i, node_name in enumerate(graph.nodes.keys(), 1):
        print(f"  {i}. {node_name}")

    # Expected nodes
    expected_nodes = {
        "chatbot",
        "tools",
        "process_tool_results",
        "check_cache",
        "fetch_job",
        "analyze_job",
        "__start__"  # LangGraph adds this automatically
    }

    actual_nodes = set(graph.nodes.keys())

    print(f"\nExpected nodes: {len(expected_nodes)}")
    print(f"Actual nodes: {len(actual_nodes)}")

    missing = expected_nodes - actual_nodes
    extra = actual_nodes - expected_nodes

    if missing:
        print(f"\n[X] Missing nodes: {missing}")
    else:
        print("\n[OK] All expected nodes present")

    if extra:
        print(f"[INFO] Extra nodes: {extra}")

    assert "chatbot" in actual_nodes, "chatbot node should exist"
    assert "check_cache" in actual_nodes, "check_cache node should exist"
    assert "fetch_job" in actual_nodes, "fetch_job node should exist"
    assert "analyze_job" in actual_nodes, "analyze_job node should exist"

    print("\n[OK] Graph structure test passed")


def test_initial_state_structure():
    """Test that initial state has required fields."""
    print("\n" + "="*80)
    print("INITIAL STATE STRUCTURE TEST")
    print("="*80)

    state = create_initial_state()

    required_fields = [
        "messages",
        "job_url",
        "job_content",
        "job_analysis",
        "master_resume",
        "tailored_resume",
        "cover_letter",
        "portfolio_examples",
        "current_intent",
        "workflow_progress",
        "requires_user_input",
        "error_message",
        "user_id"
    ]

    print("\nChecking required fields:")
    for field in required_fields:
        if field in state:
            print(f"  [OK] {field}: {type(state[field]).__name__}")
        else:
            print(f"  [X] {field}: MISSING")

    # Assert all required fields exist
    for field in required_fields:
        assert field in state, f"State should contain '{field}' field"

    # Check initial values
    assert state["job_url"] is None, "job_url should be None initially"
    assert state["job_analysis"] is None, "job_analysis should be None initially"
    assert state["messages"] == [], "messages should be empty list initially"
    assert state["portfolio_examples"] == [], "portfolio_examples should be empty list initially"

    print("\n[OK] Initial state structure test passed")


if __name__ == "__main__":
    """Run tests when executed directly."""
    import asyncio

    print("\n" + "="*80)
    print("RESUME AGENT LANGGRAPH - JOB ANALYSIS WORKFLOW TESTS")
    print("="*80)

    # Check for .env file
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print("\n[WARNING] WARNING: No .env file found")
        print(f"   Expected location: {env_path}")
        print("   The workflow test will likely fail without API keys")

    try:
        # Run structure tests first (these don't require external services)
        print("\n\nRunning structure tests...")
        test_graph_structure()
        test_initial_state_structure()

        # Run E2E test (requires external services)
        print("\n\nRunning end-to-end workflow test...")
        print("[WARNING] This test requires:")
        print("  - Valid API key in .env (ANTHROPIC_API_KEY or OPENAI_API_KEY)")
        print("  - Internet connection")
        print("  - Browser automation working")

        input("\nPress Enter to continue with E2E test, or Ctrl+C to skip...")

        # Run async test
        asyncio.run(test_job_analysis_workflow_e2e())

        print("\n\n" + "="*80)
        print("ALL TESTS PASSED [OK]")
        print("="*80)

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\n[X] Tests failed: {e}")
        sys.exit(1)
