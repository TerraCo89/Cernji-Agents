# Agent Chat UI Setup for Resume Agent

This directory contains the Agent Chat UI configured to work with the Resume Agent LangGraph server.

## Architecture

```
┌─────────────────────────┐
│   Agent Chat UI         │
│   (Next.js Frontend)    │
│   Port: 3000            │
└───────────┬─────────────┘
            │ HTTP/REST
            ▼
┌─────────────────────────┐
│  LangGraph Server       │
│  (Resume Agent API)     │
│  Port: 2024             │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Resume Agent Graph     │
│  (Conversational AI)    │
└─────────────────────────┘
```

## Prerequisites

1. **Node.js & pnpm**: Required for Agent Chat UI
   ```bash
   # Install pnpm if you don't have it
   npm install -g pnpm
   ```

2. **Python & UV**: Required for LangGraph server
   ```bash
   # Install UV if you don't have it
   pip install uv
   ```

3. **LangGraph CLI**: Required to run the server
   ```bash
   pip install "langgraph-cli[inmem]"
   ```

4. **API Keys**: Configure in `apps/resume-agent-langgraph/.env`
   - `ANTHROPIC_API_KEY` (for Claude) OR
   - `OPENAI_API_KEY` (for GPT models)

## Quick Start

### Terminal 1: Start LangGraph Server

```bash
# Navigate to Resume Agent LangGraph directory
cd apps/resume-agent-langgraph

# Ensure dependencies are installed
uv sync

# Start the LangGraph development server
langgraph dev
```

The server will start on `http://localhost:2024` and provide:
- **REST API**: `http://localhost:2024` - For Agent Chat UI
- **Studio UI**: `http://localhost:2024/studio` - For debugging

### Terminal 2: Start Agent Chat UI

```bash
# Navigate to Agent Chat UI directory
cd apps/agent-chat-ui

# Install dependencies (first time only)
pnpm install

# Start the Next.js dev server
pnpm dev
```

The UI will be available at `http://localhost:3000`

## Configuration

### LangGraph Server Configuration

**File**: `apps/resume-agent-langgraph/langgraph.json`

```json
{
  "dependencies": ["."],
  "graphs": {
    "resume_agent": "./resume_agent_langgraph.py:build_conversation_graph"
  },
  "env": ".env",
  "python_version": "3.11"
}
```

### Agent Chat UI Configuration

**File**: `apps/agent-chat-ui/.env`

```bash
# Backend API URL (server-side, used by Next.js API proxy)
LANGGRAPH_API_URL=http://localhost:2024

# Frontend API URL (client-side, must be absolute URL for SDK)
NEXT_PUBLIC_API_URL=http://localhost:3000/api

# Agent/Assistant ID - use resume_agent as the primary agent
NEXT_PUBLIC_ASSISTANT_ID=resume_agent
```

- `LANGGRAPH_API_URL`: Backend URL of the LangGraph server (used by Next.js API proxy)
- `NEXT_PUBLIC_API_URL`: Frontend API URL (client-side, must point to `/api` endpoint)
- `NEXT_PUBLIC_ASSISTANT_ID`: Graph ID from `langgraph.json`

**Note**: The `NEXT_PUBLIC_API_URL` must point to `http://localhost:3000/api` (the Next.js API proxy), NOT directly to the LangGraph server. This is because the LangGraph SDK requires an absolute URL for client-side requests.

## Usage

1. Open `http://localhost:3000` in your browser
2. The app will automatically connect to the LangGraph server
3. Start chatting with the Resume Agent!

## Features

### Current Features (v0.3.0)
- Real-time conversational interface
- Message streaming from Claude/OpenAI
- Conversation history management
- Multi-provider support (Claude + OpenAI)

### Planned Features
- Job posting analysis
- Resume tailoring
- Cover letter generation
- Portfolio code search
- Company website RAG

## Troubleshooting

### LangGraph Server Won't Start

**Problem**: `langgraph: command not found`

**Solution**: Install LangGraph CLI
```bash
pip install "langgraph-cli[inmem]"
```

**Problem**: Python version error

**Solution**: LangGraph requires Python 3.11+
```bash
python --version  # Check your version
```

### Agent Chat UI Issues

**Problem**: Port 3000 already in use

**Solution**: Use a different port
```bash
pnpm dev -- -p 3001
```

**Problem**: "Cannot connect to server"

**Solution**: Ensure LangGraph server is running on port 2024
```bash
# Check if server is running
curl http://localhost:2024/health
```

### API Key Issues

**Problem**: "ANTHROPIC_API_KEY not found"

**Solution**: Add to `apps/resume-agent-langgraph/.env`
```bash
# Choose one provider:
ANTHROPIC_API_KEY=sk-ant-...
# OR
OPENAI_API_KEY=sk-...
```

## Development

### Modifying the Resume Agent Graph

1. Edit `apps/resume-agent-langgraph/resume_agent_langgraph.py`
2. The `langgraph dev` server will auto-reload
3. Refresh the Agent Chat UI to see changes

### Changing LLM Provider

Edit `apps/resume-agent-langgraph/.env`:
```bash
# Use OpenAI (cheaper for testing)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# OR use Claude
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-5
```

### Debugging with LangGraph Studio

The LangGraph dev server includes a Studio UI at `http://localhost:2024/studio`

Features:
- Visualize graph structure
- Inspect state transitions
- View message flow
- Debug node execution

## Project Structure

```
apps/
├── resume-agent-langgraph/
│   ├── resume_agent_langgraph.py  # Main graph definition
│   ├── langgraph.json             # LangGraph config
│   ├── .env                       # API keys
│   └── pyproject.toml             # Python dependencies
│
└── agent-chat-ui/
    ├── src/                       # Next.js source
    ├── .env                       # Chat UI config
    ├── package.json               # Node dependencies
    └── SETUP.md                   # This file
```

## Resources

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph
- **Agent Chat UI Repo**: https://github.com/langchain-ai/agent-chat-ui
- **Resume Agent Spec**: `/specs/006-langgraph-resume-agent/spec.md`
- **Resume Agent README**: `apps/resume-agent-langgraph/README.md`

## Next Steps

1. Test the conversational interface
2. Add job analysis workflow (see spec)
3. Integrate resume tailoring capabilities
4. Add cover letter generation
5. Implement portfolio search
