#!/usr/bin/env python3
"""
Verify that the Japanese Learning Agent is set up correctly.

This script checks:
- Python version
- Required dependencies
- Graph compilation
- State schema validation
- Tool imports
"""

import sys
from pathlib import Path


def check_python_version():
    """Check Python version is 3.11+."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print(f"  [OK] Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  [FAIL] Python {version.major}.{version.minor}.{version.micro} (need 3.11+)")
        return False


def check_dependencies():
    """Check that required packages are installed."""
    print("\nChecking dependencies...")
    required = [
        "langgraph",
        "langchain",
        "langchain_core",
        "anthropic",
        "openai",
        "pydantic",
    ]

    all_good = True
    for package in required:
        try:
            __import__(package.replace("-", "_"))
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [FAIL] {package} (not installed)")
            all_good = False

    return all_good


def check_graph_compilation():
    """Check that the graph compiles."""
    print("\nChecking graph compilation...")
    try:
        from japanese_agent.graph import graph
        print("  [OK] Graph compiled successfully")
        return True
    except Exception as e:
        print(f"  [FAIL] Graph compilation failed: {e}")
        return False


def check_state_schema():
    """Check that state schema can be imported."""
    print("\nChecking state schema...")
    try:
        from japanese_agent.state.schemas import (
            JapaneseAgentState,
            create_initial_state,
        )
        state = create_initial_state()
        assert "messages" in state
        assert "vocabulary" in state
        print("  [OK] State schema valid")
        return True
    except Exception as e:
        print(f"  [FAIL] State schema error: {e}")
        return False


def check_tools():
    """Check that tools can be imported."""
    print("\nChecking tools...")
    try:
        from japanese_agent.tools import (
            search_vocabulary,
            get_vocabulary_statistics,
            get_due_flashcards,
        )
        print("  [OK] All tools imported successfully")
        return True
    except Exception as e:
        print(f"  [FAIL] Tool import error: {e}")
        return False


def check_environment():
    """Check environment configuration."""
    print("\nChecking environment configuration...")
    import os

    env_file = Path(".env")
    if env_file.exists():
        print("  [OK] .env file found")

        # Check for API keys
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))

        if has_openai or has_anthropic:
            print(f"  [OK] API key configured ({'OpenAI' if has_openai else 'Anthropic'})")
            return True
        else:
            print("  [WARN] No API key found in environment")
            print("    Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
            return True  # Not critical for basic setup
    else:
        print("  [WARN] .env file not found (optional)")
        print("    Copy .env.example to .env and add your API keys")
        return True


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Japanese Learning Agent - Setup Verification")
    print("=" * 60)

    checks = [
        check_python_version(),
        check_dependencies(),
        check_state_schema(),
        check_tools(),
        check_graph_compilation(),
        check_environment(),
    ]

    print("\n" + "=" * 60)
    if all(checks):
        print("[SUCCESS] All checks passed! Setup is complete.")
        print("\nNext steps:")
        print("  1. Configure .env with your API keys")
        print("  2. Run: langgraph dev")
        print("  3. Open LangGraph Studio and start chatting!")
    else:
        print("[ERROR] Some checks failed. Please fix the issues above.")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
