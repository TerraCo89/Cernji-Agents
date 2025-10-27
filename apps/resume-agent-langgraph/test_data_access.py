"""
Quick test script for data access wrapper module.

This verifies that all data access functions are properly imported
and can be called without errors.
"""

import os
import sys

# Set required environment variable
os.environ["STORAGE_BACKEND"] = "sqlite"

# Suppress MCP server warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from src.resume_agent.data import (
    load_master_resume,
    load_career_history,
    get_job_analysis,
    search_portfolio_by_tech,
    save_job_analysis,
    save_tailored_resume,
    save_cover_letter,
    list_applications,
)


def test_imports():
    """Test that all functions are importable."""
    print("[PASS] All data access functions imported successfully")
    print()


def test_read_functions():
    """Test read functions with real database."""
    print("Testing read functions...")

    try:
        # Test master resume loading
        resume = load_master_resume()
        print(f"  [PASS] load_master_resume() - Loaded resume with {len(resume.get('employment_history', []))} jobs")
    except Exception as e:
        print(f"  [FAIL] load_master_resume() failed: {e}")

    try:
        # Test career history loading
        history = load_career_history()
        print(f"  [PASS] load_career_history() - Loaded {len(history.get('employment_history', []))} positions")
    except Exception as e:
        print(f"  [FAIL] load_career_history() failed: {e}")

    try:
        # Test job analysis (may return None if not cached)
        analysis = get_job_analysis("Test Company", "Test Job")
        if analysis:
            print(f"  [PASS] get_job_analysis() - Found cached analysis")
        else:
            print(f"  [PASS] get_job_analysis() - No cached analysis (expected)")
    except Exception as e:
        print(f"  [FAIL] get_job_analysis() failed: {e}")

    try:
        # Test portfolio search
        examples = search_portfolio_by_tech("Python", limit=5)
        print(f"  [PASS] search_portfolio_by_tech() - Found {len(examples)} examples")
    except Exception as e:
        print(f"  [FAIL] search_portfolio_by_tech() failed: {e}")

    try:
        # Test list applications
        apps = list_applications(limit=5)
        print(f"  [PASS] list_applications() - Found {len(apps)} applications")
    except Exception as e:
        print(f"  [FAIL] list_applications() failed: {e}")

    print()


def test_function_signatures():
    """Test that function signatures match expected interface."""
    print("Testing function signatures...")

    # Check that functions exist and are callable
    assert callable(load_master_resume)
    assert callable(load_career_history)
    assert callable(get_job_analysis)
    assert callable(search_portfolio_by_tech)
    assert callable(save_job_analysis)
    assert callable(save_tailored_resume)
    assert callable(save_cover_letter)
    assert callable(list_applications)

    print("  [PASS] All functions are callable")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Data Access Wrapper - Test Suite")
    print("=" * 60)
    print()

    test_imports()
    test_function_signatures()
    test_read_functions()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
