#!/usr/bin/env python3
"""
Test script for the new modular structure.

Verifies all imports and basic functionality.
"""

import sys
from pathlib import Path

print("\n" + "="*60)
print("Testing Modular Resume Agent Structure")
print("="*60)

# Test 1: Configuration
print("\n[Test 1] Configuration Module")
try:
    from src.resume_agent.config import get_settings, reset_settings
    settings = get_settings()
    print(f"  Provider: {settings.llm_provider}")
    print(f"  Claude Model: {settings.claude_model}")
    print(f"  OpenAI Model: {settings.openai_model}")
    print("  Status: PASS")
except Exception as e:
    print(f"  Status: FAIL - {e}")
    sys.exit(1)

# Test 2: State Schemas
print("\n[Test 2] State Schemas")
try:
    from src.resume_agent.state import (
        ResumeAgentState,
        JobAnalysisState
    )
    print(f"  ResumeAgentState: OK")
    print(f"  JobAnalysisState: OK")
    print("  Status: PASS")
except Exception as e:
    print(f"  Status: FAIL - {e}")
    sys.exit(1)

# Test 3: LLM Providers
print("\n[Test 3] LLM Provider Abstraction")
try:
    from src.resume_agent.llm import call_llm, get_provider_info
    provider, model = get_provider_info()
    print(f"  Current Provider: {provider}")
    print(f"  Current Model: {model}")
    print("  Status: PASS")
except Exception as e:
    print(f"  Status: FAIL - {e}")
    sys.exit(1)

# Test 4: Prompts
print("\n[Test 4] Prompt Templates")
try:
    from src.resume_agent.prompts import (
        SYSTEM_RESUME_AGENT,
        SYSTEM_JOB_ANALYZER,
        CONVERSATION_SYSTEM
    )
    print(f"  SYSTEM_RESUME_AGENT: {len(SYSTEM_RESUME_AGENT)} chars")
    print(f"  SYSTEM_JOB_ANALYZER: {len(SYSTEM_JOB_ANALYZER)} chars")
    print(f"  CONVERSATION_SYSTEM: {len(CONVERSATION_SYSTEM)} chars")
    print("  Status: PASS")
except Exception as e:
    print(f"  Status: FAIL - {e}")
    sys.exit(1)

# Test 5: Nodes
print("\n[Test 5] Node Implementations")
try:
    from src.resume_agent.nodes import (
        check_cache_node,
        fetch_job_node,
        analyze_job_node
    )
    print(f"  check_cache_node: OK")
    print(f"  fetch_job_node: OK")
    print(f"  analyze_job_node: OK")
    print("  Status: PASS")
except Exception as e:
    print(f"  Status: FAIL - {e}")
    sys.exit(1)

# Test 6: Graphs
print("\n[Test 6] Graph Orchestration")
try:
    from src.resume_agent.graphs import build_job_analysis_graph
    app = build_job_analysis_graph()
    print(f"  build_job_analysis_graph: OK")
    print(f"  Graph compiled: {app is not None}")
    print("  Status: PASS")
except Exception as e:
    print(f"  Status: FAIL - {e}")
    sys.exit(1)

# Test 7: Main Package Exports
print("\n[Test 7] Main Package Exports")
try:
    from src.resume_agent.config import get_settings
    from src.resume_agent.state import ResumeAgentState
    from src.resume_agent.llm import call_llm
    from src.resume_agent.graphs import build_job_analysis_graph
    print(f"  All main exports accessible via submodules: OK")
    print("  Status: PASS")
except Exception as e:
    print(f"  Status: FAIL - {e}")
    sys.exit(1)

print("\n" + "="*60)
print("All Tests Passed!")
print("="*60)
print("\nThe modular structure is working correctly.")
print("\nNext steps:")
print("1. Run the CLI: uv run src/cli.py")
print("2. Or use as a package: from src.resume_agent import build_conversation_graph")
print("\n")
