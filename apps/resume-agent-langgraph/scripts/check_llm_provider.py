#!/usr/bin/env python3
"""Quick test script for LLM provider abstraction."""

import sys
from pathlib import Path

# Add src to path (now two levels up from tests/integration/ to get to project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from resume_agent.config import get_settings
    from resume_agent.llm import call_llm, get_provider_info

    print("✓ Imports successful!")

    # Test get_provider_info
    provider, model = get_provider_info()
    print(f"✓ Provider: {provider}, Model: {model}")

    # Test config access
    settings = get_settings()
    print(f"✓ LLM Provider configured: {settings.llm_provider}")
    print(f"✓ Temperature: {settings.temperature}")
    print(f"✓ Max tokens: {settings.max_tokens}")

    print("\n✓ All tests passed!")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
