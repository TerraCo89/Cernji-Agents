"""Quick test runner to bypass interactive prompts."""
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tests.test_job_analysis_e2e import test_job_analysis_workflow_e2e

if __name__ == "__main__":
    try:
        # Run async test
        asyncio.run(test_job_analysis_workflow_e2e())
        print("\nTest passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
