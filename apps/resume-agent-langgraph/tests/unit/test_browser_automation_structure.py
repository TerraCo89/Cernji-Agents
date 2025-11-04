"""
Test browser automation module structure and signature validation.

This test validates the implementation structure without requiring
langchain-community installation. It checks that:
1. The module is importable
2. Function signatures match requirements
3. Basic structure is correct

Full integration tests require: pip install langchain-community playwright
"""

import ast
import inspect
from pathlib import Path


def test_create_scraper_agent_exists():
    """Verify create_scraper_agent function exists in module."""
    module_path = Path(__file__).parent.parent / "src" / "resume_agent" / "tools" / "browser_automation.py"

    # Parse the file as AST to avoid import errors
    with open(module_path) as f:
        tree = ast.parse(f.read())

    # Find the create_scraper_agent function
    functions = [node for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)]
    function_names = [f.name for f in functions]

    assert "create_scraper_agent" in function_names, "create_scraper_agent function not found"


def test_create_scraper_agent_signature():
    """Verify create_scraper_agent has correct signature."""
    module_path = Path(__file__).parent.parent / "src" / "resume_agent" / "tools" / "browser_automation.py"

    with open(module_path) as f:
        tree = ast.parse(f.read())

    # Find the function
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "create_scraper_agent":
            # Check parameters
            args = node.args
            param_names = [arg.arg for arg in args.args]

            assert "browser" in param_names, "Missing required 'browser' parameter"
            assert "use_checkpointing" in param_names, "Missing optional 'use_checkpointing' parameter"

            # Check it's async
            assert isinstance(node, ast.AsyncFunctionDef), "Function should be async"

            # Check has docstring
            docstring = ast.get_docstring(node)
            assert docstring is not None, "Function missing docstring"
            assert "ReAct agent" in docstring, "Docstring should mention ReAct agent"
            assert "PlayWrightBrowserToolkit" in docstring, "Docstring should mention toolkit"

            return

    raise AssertionError("create_scraper_agent function not found in AST")


def test_implementation_structure():
    """Verify implementation follows LangGraph patterns."""
    module_path = Path(__file__).parent.parent / "src" / "resume_agent" / "tools" / "browser_automation.py"

    with open(module_path) as f:
        content = f.read()

    # Verify key imports are present
    assert "from langchain_community.agent_toolkits import PlayWrightBrowserToolkit" in content, \
        "Missing PlayWrightBrowserToolkit import"
    assert "from langchain_anthropic import ChatAnthropic" in content, \
        "Missing ChatAnthropic import"
    assert "from langchain.agents import create_react_agent" in content, \
        "Missing create_react_agent import (should be from langchain.agents, not langgraph.prebuilt)"

    # Verify toolkit initialization pattern
    assert "PlayWrightBrowserToolkit.from_browser" in content, \
        "Should use PlayWrightBrowserToolkit.from_browser()"
    assert "toolkit.get_tools()" in content, \
        "Should call toolkit.get_tools()"

    # Verify LLM initialization
    assert 'model="claude-sonnet-4-5"' in content, \
        "Should use claude-sonnet-4-5 model"
    assert "temperature=0" in content, \
        "Should use temperature=0 for deterministic extraction"

    # Verify agent creation
    assert "create_react_agent(" in content, \
        "Should use create_react_agent()"
    assert "model=llm" in content, \
        "Should pass llm to agent"
    assert "tools=tools" in content, \
        "Should pass tools to agent"

    # Verify checkpointing logic
    assert "if use_checkpointing:" in content, \
        "Should conditionally handle checkpointing"
    assert "MemorySaver" in content, \
        "Should use MemorySaver for checkpointing"


def test_context_manager_exists():
    """Verify create_browser_context async context manager exists."""
    module_path = Path(__file__).parent.parent / "src" / "resume_agent" / "tools" / "browser_automation.py"

    with open(module_path) as f:
        content = f.read()

    # Check for context manager decorator and function
    assert "@asynccontextmanager" in content, \
        "Should have @asynccontextmanager decorator"
    assert "async def create_browser_context" in content, \
        "Should define create_browser_context function"
    assert "create_async_playwright_browser" in content, \
        "Should use create_async_playwright_browser"


def test_scraper_functions_defined():
    """Verify site-specific scraper functions are defined."""
    module_path = Path(__file__).parent.parent / "src" / "resume_agent" / "tools" / "browser_automation.py"

    with open(module_path) as f:
        tree = ast.parse(f.read())

    async_functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)]

    # Check required scraper functions exist
    assert "scrape_japan_dev_job" in async_functions, \
        "Should define scrape_japan_dev_job function"
    assert "scrape_recruit_job" in async_functions, \
        "Should define scrape_recruit_job function"
    assert "scrape_generic_job_posting" in async_functions, \
        "Should define scrape_generic_job_posting function"
    assert "scrape_job_posting" in async_functions, \
        "Should define scrape_job_posting router function"


if __name__ == "__main__":
    # Run tests
    test_create_scraper_agent_exists()
    print("[PASS] create_scraper_agent function exists")

    test_create_scraper_agent_signature()
    print("[PASS] create_scraper_agent has correct signature")

    test_implementation_structure()
    print("[PASS] Implementation follows LangGraph patterns")

    test_context_manager_exists()
    print("[PASS] Browser context manager exists")

    test_scraper_functions_defined()
    print("[PASS] Scraper functions defined")

    print("\n[SUCCESS] All structure validation tests passed!")
