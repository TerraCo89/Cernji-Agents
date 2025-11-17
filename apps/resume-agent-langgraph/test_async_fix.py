"""Quick test to verify analyze_job_posting is async."""
import inspect
from src.resume_agent.tools.job_analyzer import analyze_job_posting

print("Tool type:", type(analyze_job_posting))
print("Has 'func' attribute:", hasattr(analyze_job_posting, 'func'))

if hasattr(analyze_job_posting, 'func'):
    print("Wrapped function is coroutine:", inspect.iscoroutinefunction(analyze_job_posting.func))

if hasattr(analyze_job_posting, 'ainvoke'):
    print("Has ainvoke method: YES")
else:
    print("Has ainvoke method: NO")

if hasattr(analyze_job_posting, 'invoke'):
    print("Has invoke method: YES")
else:
    print("Has invoke method: NO")

print("\nTool attributes:", dir(analyze_job_posting))
