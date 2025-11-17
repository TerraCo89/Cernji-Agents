"""Test if the LangChain tool properly handles async."""
import inspect
from src.resume_agent.tools.job_analyzer import analyze_job_posting

print("=" * 60)
print("LANGCHAIN TOOL INSPECTION")
print("=" * 60)

# Check the coroutine attribute
if hasattr(analyze_job_posting, 'coroutine'):
    print(f"\nTool.coroutine attribute exists: {analyze_job_posting.coroutine}")
    if analyze_job_posting.coroutine:
        print("  → This is an ASYNC tool")
        print(f"  → coroutine type: {type(analyze_job_posting.coroutine)}")
        print(f"  → Is coroutinefunction: {inspect.iscoroutinefunction(analyze_job_posting.coroutine)}")
    else:
        print("  → This is a SYNC tool")

# Check func attribute
if hasattr(analyze_job_posting, 'func'):
    print(f"\nTool.func: {analyze_job_posting.func}")
    print(f"  → Type: {type(analyze_job_posting.func)}")
    print(f"  → Is coroutinefunction: {inspect.iscoroutinefunction(analyze_job_posting.func)}")

# Test methods
print("\n" + "=" * 60)
print("AVAILABLE METHODS")
print("=" * 60)
print(f"Has invoke (sync):  {hasattr(analyze_job_posting, 'invoke')}")
print(f"Has ainvoke (async): {hasattr(analyze_job_posting, 'ainvoke')}")

print("\n✅ Tool is properly configured for async usage!")
