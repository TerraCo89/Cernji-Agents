import pytest

from agent import graph

pytestmark = pytest.mark.anyio


# @pytest.mark.langsmith  # Commented out to avoid auth issues during testing
async def test_agent_simple_passthrough() -> None:
    inputs = {"messages": [{"role": "user", "content": "Hello! How are you?"}]}
    res = await graph.ainvoke(inputs)
    assert res is not None
    assert "messages" in res
    assert len(res["messages"]) > 0
    print(f"Response: {res['messages'][-1].content}")
