# LangGraph StateGraph Implementation Patterns (v0.2.0+)

## Solution Description

LangGraph StateGraph uses TypedDict-based state schemas with specialized reducers to manage message history and state updates. The `add_messages` reducer is the key pattern for handling messages in conversational agents, providing intelligent message merging that prevents duplicates while allowing updates by message ID.

### Key Concepts

1. **State Schema Options**:
   - **TypedDict with add_messages**: Full control over state structure, recommended for complex applications
   - **MessagesState**: Pre-built convenience class for simple chat applications (internally uses TypedDict + add_messages)
   - **Pydantic BaseModel**: Supported but slower performance than TypedDict

2. **Message Handling**:
   - Messages are represented as dictionaries with `role` and `content` keys
   - Nodes return partial state updates as dictionaries
   - The `add_messages` reducer appends new messages and updates existing ones by ID
   - Messages can be provided as Message objects or tuples: `("assistant", "text")`

3. **Node Return Pattern**:
   - Nodes must return a dictionary matching state keys to update
   - For messages: `return {"messages": [message_dict]}`
   - Multiple state keys can be updated: `return {"messages": [...], "other_key": value}`

4. **Common Pitfall - KeyError: 'role'**:
   - Occurs when message format doesn't match expected structure
   - Always use `{"role": "user/assistant", "content": "text"}` format
   - Or use LangChain Message objects: `AIMessage(content="text")`

## Working Code Example

### Example 1: Basic Chatbot with TypedDict

```python
"""
Basic LangGraph chatbot using TypedDict and add_messages.
Demonstrates proper message handling and state updates.
"""

from typing import Annotated
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


# State schema using TypedDict
class State(TypedDict):
    """
    State schema for chatbot.

    messages: Conversation history with add_messages reducer
              - Appends new messages to list
              - Updates existing messages by ID
    """
    messages: Annotated[list, add_messages]


# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.2)


def chatbot(state: State) -> dict:
    """
    Chatbot node - processes messages with LLM.

    Args:
        state: Current conversation state

    Returns:
        Partial state update with new message
    """
    # Invoke LLM with message history
    response = llm.invoke(state["messages"])

    # Return update - add_messages will append this
    return {"messages": [response]}


# Build graph
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("chatbot", chatbot)

# Define edges
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Compile
graph = graph_builder.compile()

# Usage
result = graph.invoke({
    "messages": [("user", "What is LangGraph?")]
})

print(result["messages"])
# Output: [HumanMessage(content='What is LangGraph?'), AIMessage(content='LangGraph is...')]
```

### Example 2: Advanced with Custom State and Tools

```python
"""
Advanced LangGraph agent with tools, custom state, and conditional routing.
Demonstrates MessagesState subclassing and tool integration.
"""

from typing import Annotated
from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver


# Custom state extending MessagesState
class AgentState(MessagesState):
    """
    Extended state with additional fields.

    Inherits:
        messages: Annotated[list, add_messages] from MessagesState

    Additional fields:
        documents: Retrieved documents for context
        query_count: Track number of tool calls
    """
    documents: list[str]
    query_count: int


# Setup tools
tool = TavilySearchResults(max_results=2)
tools = [tool]

# Setup LLM with tools
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: AgentState) -> dict:
    """
    Main chatbot node with tool calling capability.

    Args:
        state: Current agent state

    Returns:
        Partial state update with AI message and updated query count
    """
    # Invoke LLM
    response = llm_with_tools.invoke(state["messages"])

    # Update state
    return {
        "messages": [response],
        "query_count": state.get("query_count", 0) + 1
    }


def should_continue(state: AgentState) -> str:
    """
    Routing function for conditional edges.

    Args:
        state: Current agent state

    Returns:
        Next node name or END
    """
    # Check if we've hit max queries
    if state.get("query_count", 0) >= 5:
        return END

    # Use built-in tools_condition for tool routing
    return tools_condition(state)


# Build graph
graph_builder = StateGraph(AgentState)

# Add nodes
graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# Define edges
graph_builder.add_edge(START, "chatbot")

# Conditional edge: chatbot -> tools or END
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    {
        "tools": "tools",
        END: END
    }
)

# After tools, go back to chatbot
graph_builder.add_edge("tools", "chatbot")

# Compile with checkpointing
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# Usage with checkpointing
config = {"configurable": {"thread_id": "1"}}
result = graph.invoke(
    {
        "messages": [("user", "Search for LangGraph documentation")],
        "documents": [],
        "query_count": 0
    },
    config=config
)

print(f"Final message count: {len(result['messages'])}")
print(f"Query count: {result['query_count']}")
```

### Example 3: Human-in-the-Loop with Custom State Updates

```python
"""
Human-in-the-loop pattern with Command for complex state updates.
Demonstrates interrupt() and Command for multi-field updates.
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt
from langchain_core.messages import ToolMessage, AIMessage


class ReviewState(TypedDict):
    """State for review workflow."""
    messages: Annotated[list, add_messages]
    name: str
    birthday: str
    needs_review: bool
    approved: bool


def collect_info(state: ReviewState) -> dict:
    """Collect information from user."""
    # Get info (in real app, this would call LLM)
    response = AIMessage(
        content="What is your name and birthday?",
        tool_calls=[{
            "id": "verify_1",
            "name": "verify_info",
            "args": {"name": "John", "birthday": "1990-01-01"}
        }]
    )

    return {
        "messages": [response],
        "needs_review": True
    }


def verify_info(state: ReviewState) -> dict:
    """
    Verify information with human reviewer.
    Uses Command to update multiple state fields.
    """
    if state.get("needs_review"):
        # Pause for human review
        verified_data = interrupt({
            "question": "Please verify the information:",
            "name": state.get("name", ""),
            "birthday": state.get("birthday", "")
        })

        # Update multiple fields using Command
        tool_msg = ToolMessage(
            content=f"Verified: {verified_data['name']}",
            tool_call_id="verify_1"
        )

        return Command(
            update={
                "name": verified_data["name"],
                "birthday": verified_data["birthday"],
                "messages": [tool_msg],
                "needs_review": False,
                "approved": True
            }
        )

    return {"approved": state.get("approved", False)}


# Build graph
graph_builder = StateGraph(ReviewState)
graph_builder.add_node("collect", collect_info)
graph_builder.add_node("verify", verify_info)

graph_builder.add_edge(START, "collect")
graph_builder.add_edge("collect", "verify")
graph_builder.add_edge("verify", END)

# Compile with checkpointing for interrupts
from langgraph.checkpoint.memory import MemorySaver
graph = graph_builder.compile(checkpointer=MemorySaver())
```

### Example 4: Proper Message Format Handling

```python
"""
Demonstrates different message formats accepted by add_messages.
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage


class ChatState(TypedDict):
    messages: Annotated[list, add_messages]


def example_node_tuple_format(state: ChatState) -> dict:
    """
    Return messages as tuples.
    Format: (role, content)
    """
    return {
        "messages": [
            ("user", "Hello"),
            ("assistant", "Hi there!")
        ]
    }


def example_node_dict_format(state: ChatState) -> dict:
    """
    Return messages as dictionaries.
    Format: {"role": str, "content": str}
    """
    return {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
    }


def example_node_message_objects(state: ChatState) -> dict:
    """
    Return LangChain Message objects.
    This is the most type-safe approach.
    """
    return {
        "messages": [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!")
        ]
    }


# All three formats produce the same result:
# [HumanMessage(content='Hello', id='...'), AIMessage(content='Hi there!', id='...')]
```

## TypedDict vs MessagesState Decision Matrix

| Use Case | Recommended Approach | Reason |
|----------|---------------------|--------|
| Simple chatbot | `MessagesState` | Less boilerplate, pre-configured |
| Need custom state fields | Subclass `MessagesState` | Inherits message handling + custom fields |
| Complex multi-workflow | `TypedDict` with `add_messages` | Full control over schema and reducers |
| Need Pydantic validation | `TypedDict` (not BaseModel) | Better performance than Pydantic |

## Troubleshooting KeyError: 'role'

**Problem**: `KeyError: 'role'` when processing messages

**Causes**:
1. Wrong message format in node return value
2. Mixing message formats (SDK vs API format)
3. Missing message conversion when using custom LLM wrappers

**Solutions**:

```python
# ❌ WRONG - Missing required fields
def bad_node(state):
    return {"messages": [{"content": "text"}]}  # Missing 'role'

# ✅ CORRECT - Dictionary format
def good_node_dict(state):
    return {"messages": [{"role": "assistant", "content": "text"}]}

# ✅ CORRECT - Tuple format
def good_node_tuple(state):
    return {"messages": [("assistant", "text")]}

# ✅ CORRECT - Message object
def good_node_object(state):
    from langchain_core.messages import AIMessage
    return {"messages": [AIMessage(content="text")]}
```

## Message ID Behavior

The `add_messages` reducer has intelligent ID-based updating:

```python
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage

# Initial messages
msgs1 = [HumanMessage(content="Hello", id="1")]

# New message with same ID - updates existing
msgs2 = [HumanMessage(content="Hello there!", id="1")]

result = add_messages(msgs1, msgs2)
# Result: [HumanMessage(content='Hello there!', id='1')]
# Message was UPDATED, not appended

# New message with different ID - appends
msgs3 = [AIMessage(content="Hi!", id="2")]
result = add_messages(result, msgs3)
# Result: [HumanMessage(content='Hello there!', id='1'), AIMessage(content='Hi!', id='2')]
```

This is crucial for human-in-the-loop workflows where you need to update messages after user review.

## Performance Notes

From LangGraph documentation:

1. **TypedDict**: Fastest performance, recommended for production
2. **Dataclasses**: Good performance, useful when default values needed
3. **Pydantic BaseModel**: Slower performance, use only if validation is critical

## Sources

- **[Official LangGraph Docs - State Customization](https://langchain-ai.github.io/langgraph/tutorials/get-started/5-customize-state/)**: Complete tutorial on custom state with TypedDict and add_messages
- **[LangGraph Reference - Graphs](https://langchain-ai.github.io/langgraph/reference/graphs/)**: API reference for StateGraph and state schemas
- **[LangGraph Concepts - Low Level](https://langchain-ai.github.io/langgraph/concepts/low_level/)**: Deep dive into StateGraph, reducers, and message handling
- **[GitHub - message.py](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/graph/message.py)**: Source code for add_messages implementation
- **[LangGraph Tutorial with Example](https://www.gettingstarted.ai/langgraph-tutorial-with-example/)**: Practical examples (partial, requires subscription for full code)
- **[StateGraph and MessagesState Tutorial](https://deepwiki.com/langchain-ai/langchain-academy/3.1-stategraph-and-messagesstate)**: Comparison of state schema approaches
- **[State, AgentState, TypeDict in LangGraph](https://notechit.com/state-agentstate-typedict-and-message-state-in-langgraph)**: Comprehensive guide to state types

## Additional Resources

- **LangGraph GitHub Repository**: https://github.com/langchain-ai/langgraph
- **LangGraph Examples**: https://github.com/langchain-ai/langgraph/tree/main/docs/docs/tutorials
- **LangChain Academy**: Free course on LangGraph basics
- **Context7 LangGraph Docs**: Available via `mcp__context7__get-library-docs` with library ID `/langchain-ai/langgraph`
