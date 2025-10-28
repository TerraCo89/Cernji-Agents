#!/usr/bin/env python3
"""Test graph invocation programmatically"""

from examples.minimal_agent import build_graph
from langchain_core.messages import HumanMessage
import uuid

print("=" * 60)
print("Testing Graph Invocation")
print("=" * 60)

# Build graph
print("\n1. Building graph...")
app = build_graph()
print("   [OK] Graph built successfully")

# Create test state
print("\n2. Creating test state...")
state = {
    "messages": [HumanMessage(content="Hello from test script")]
}
print(f"   [OK] State created: {len(state['messages'])} messages")

# Invoke with thread_id
print("\n3. Invoking graph...")
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

try:
    result = app.invoke(state, config=config)
    print(f"   [OK] Invocation successful!")
    print(f"\n4. Result:")
    for msg in result["messages"]:
        print(f"   - {msg.type}: {msg.content}")
except Exception as e:
    print(f"   [ERROR] Invocation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
