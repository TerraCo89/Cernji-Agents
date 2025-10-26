# Basic LangGraph Agent

[![CI](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml)

This application demonstrates key LangGraph patterns using the official tutorial. It showcases tool integration, human-in-the-loop interactions, and multi-node graph orchestration using [LangGraph](https://github.com/langchain-ai/langgraph), designed for use with [LangGraph Server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/#langgraph-server) and [LangGraph Studio](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/), a visual debugging IDE.

<div align="center">
  <img src="./static/studio_ui.png" alt="Graph view in LangGraph studio UI" width="75%" />
</div>

## Features

The core logic defined in `src/agent/graph.py` demonstrates:

- **Tool Integration**: Uses TavilySearch for web search and a custom human_assistance tool
- **Human-in-the-Loop**: Implements interrupt() for dynamic human feedback with support for both Studio UI (string) and programmatic (dict) responses
- **State Management**: Extended state schema tracking messages, name, and birthday
- **Conditional Routing**: Automatic tool execution routing via tools_condition
- **Command Pattern**: Tools can directly update graph state using Command objects

This provides a foundation for building more complex agentic workflows that can be visualized and debugged in LangGraph Studio.

## Getting Started

1. Install dependencies, along with the [LangGraph CLI](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/), which will be used to run the server.

```bash
cd path/to/your/app
pip install -e . "langgraph-cli[inmem]"
```

2. Configure environment variables. Create a `.env` file with your API keys.

```bash
cp .env.example .env
```

Add the required API keys to the `.env` file:

```text
# .env
# Required: LLM provider (choose one)
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...

# Required: For TavilySearch tool
TAVILY_API_KEY=tvly-...

# Optional: For LangSmith tracing
LANGSMITH_API_KEY=lsv2...
```

3. Start the LangGraph Server.

```shell
langgraph dev
```

For more information on getting started with LangGraph Server, [see here](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/).

## How to customize

1. **Add or modify tools**: The `tools` list in `graph.py` currently includes TavilySearch and human_assistance. You can add more tools or create custom tools using the `@tool` decorator.

2. **Extend the state schema**: The `State` TypedDict can be extended with additional fields. Use the `add_messages` reducer for message fields, or define custom reducers for other field types.

3. **Modify graph flow**: The core logic is defined in [graph.py](./src/agent/graph.py). You can:
   - Add new nodes for different processing steps
   - Change conditional routing logic via `tools_condition` or custom conditions
   - Implement additional human-in-the-loop breakpoints using `interrupt()`

4. **Change LLM provider**: Update the `init_chat_model()` call to use different models (e.g., `"anthropic:claude-3-5-sonnet-latest"`, `"openai:gpt-4"`)

## Development

While iterating on your graph in LangGraph Studio, you can edit past state and rerun your app from previous states to debug specific nodes. Local changes will be automatically applied via hot reload.

Follow-up requests extend the same thread. You can create an entirely new thread, clearing previous history, using the `+` button in the top right.

For more advanced features and examples, refer to the [LangGraph documentation](https://langchain-ai.github.io/langgraph/). These resources can help you adapt this template for your specific use case and build more sophisticated conversational agents.

LangGraph Studio also integrates with [LangSmith](https://smith.langchain.com/) for more in-depth tracing and collaboration with teammates, allowing you to analyze and optimize your chatbot's performance.

