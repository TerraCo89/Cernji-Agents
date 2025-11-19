# Quick Start: Multi-Agent LangGraph + Agent Chat UI

**Get multiple specialized agents running in 15 minutes**

## Current State

You already have modular graph files:
- ✅ `src/resume_agent/graphs/job_analysis.py`
- ✅ `src/resume_agent/graphs/resume_tailor.py`
- ✅ `src/resume_agent/graphs/cover_letter.py`
- ✅ `src/resume_agent/graphs/conversation.py`

They're just not exposed as separate agents yet!

## Step 1: Update langgraph.json (2 minutes)

**File:** `apps/resume-agent-langgraph/langgraph.json`

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "dependencies": [".", "./src"],
  "graphs": {
    "job_analyzer": "./src/resume_agent/graphs/job_analysis.py:graph",
    "resume_tailor": "./src/resume_agent/graphs/resume_tailor.py:graph",
    "cover_letter_writer": "./src/resume_agent/graphs/cover_letter.py:graph",
    "conversational": "./src/resume_agent/graphs/conversation.py:graph",
    "legacy_advanced": "./src/resume_agent/graph.py:graph"
  },
  "env": ".env",
  "image_distro": "wolfi"
}
```

**Note:** Each graph file must export a compiled graph named `graph`.

## Step 2: Ensure Graphs Export Properly (5 minutes)

Each graph file should export a compiled graph at the module level:

**Example:** `src/resume_agent/graphs/job_analysis.py`

```python
# ... (existing imports and code)

def build_job_analysis_graph():
    """Build job analysis workflow."""
    graph = StateGraph(JobAnalysisState)
    # ... (existing graph construction)
    return graph.compile(checkpointer=MemorySaver())

# Export compiled graph for LangGraph server
graph = build_job_analysis_graph()
```

**Check each file:**
```bash
cd apps/resume-agent-langgraph

# Verify exports
python -c "from src.resume_agent.graphs.job_analysis import graph; print('✅ job_analysis')"
python -c "from src.resume_agent.graphs.resume_tailor import graph; print('✅ resume_tailor')"
python -c "from src.resume_agent.graphs.cover_letter import graph; print('✅ cover_letter')"
```

Fix any import errors before proceeding.

## Step 3: Start LangGraph Server (1 minute)

```bash
cd apps/resume-agent-langgraph
langgraph dev
```

**Verify agents are loaded:**
Open http://localhost:2024 (LangGraph Studio)

You should see all agents listed:
- job_analyzer
- resume_tailor
- cover_letter_writer
- conversational
- legacy_advanced

## Step 4: Update Agent Chat UI - Add Agent Selection (7 minutes)

### 4.1: Create Agent Selector Component

**File:** `apps/agent-chat-ui/src/components/agent-selector.tsx`

```typescript
"use client";

import { useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export type AgentType =
  | "job_analyzer"
  | "resume_tailor"
  | "cover_letter_writer"
  | "conversational";

export interface Agent {
  id: AgentType;
  name: string;
  description: string;
  icon: string;
}

const AGENTS: Agent[] = [
  {
    id: "job_analyzer",
    name: "Job Analyzer",
    description: "Analyze job postings and extract requirements",
    icon: "🔍",
  },
  {
    id: "resume_tailor",
    name: "Resume Tailor",
    description: "Customize your resume for specific jobs",
    icon: "📝",
  },
  {
    id: "cover_letter_writer",
    name: "Cover Letter Writer",
    description: "Generate personalized cover letters",
    icon: "✉️",
  },
  {
    id: "conversational",
    name: "Career Assistant",
    description: "General career guidance and questions",
    icon: "💬",
  },
];

interface AgentSelectorProps {
  selectedAgent: AgentType;
  onAgentChange: (agent: AgentType) => void;
}

export function AgentSelector({
  selectedAgent,
  onAgentChange,
}: AgentSelectorProps) {
  const selected = AGENTS.find((a) => a.id === selectedAgent)!;

  return (
    <div className="w-full max-w-sm">
      <Select value={selectedAgent} onValueChange={(v) => onAgentChange(v as AgentType)}>
        <SelectTrigger className="w-full">
          <SelectValue>
            <div className="flex items-center gap-2">
              <span>{selected.icon}</span>
              <span className="font-medium">{selected.name}</span>
            </div>
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {AGENTS.map((agent) => (
            <SelectItem key={agent.id} value={agent.id}>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span>{agent.icon}</span>
                  <span className="font-medium">{agent.name}</span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {agent.description}
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
```

### 4.2: Update Thread Page to Support Agent Selection

**File:** `apps/agent-chat-ui/src/app/thread/[thread]/page.tsx`

```typescript
"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Thread } from "@/components/thread";
import { AgentSelector, AgentType } from "@/components/agent-selector";

export default function ThreadPage() {
  const params = useParams();
  const threadId = params.thread as string;
  const [selectedAgent, setSelectedAgent] = useState<AgentType>("conversational");

  return (
    <div className="flex flex-col h-screen">
      {/* Header with Agent Selector */}
      <div className="border-b p-4 bg-background">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold mb-4">Career Assistant</h1>
          <AgentSelector
            selectedAgent={selectedAgent}
            onAgentChange={setSelectedAgent}
          />
        </div>
      </div>

      {/* Thread Component */}
      <div className="flex-1 overflow-hidden">
        <Thread
          threadId={threadId}
          agentId={selectedAgent}
        />
      </div>
    </div>
  );
}
```

### 4.3: Update Thread Component to Accept Agent ID

**File:** `apps/agent-chat-ui/src/components/thread/index.tsx`

Add `agentId` prop:

```typescript
interface ThreadProps {
  threadId: string;
  agentId: string; // Add this
}

export function Thread({ threadId, agentId }: ThreadProps) {
  // ... existing code

  // Update the stream call to use agentId
  const handleSubmit = async (message: string) => {
    const stream = client.runs.stream(
      threadId,
      agentId, // Use the selected agent
      {
        input: {
          messages: [{ role: "human", content: message }]
        }
      }
    );

    for await (const chunk of stream) {
      // ... existing streaming logic
    }
  };

  // ... rest of component
}
```

## Step 5: Test the Multi-Agent Setup

### 5.1: Start Both Servers

**Terminal 1 - LangGraph Server:**
```bash
cd apps/resume-agent-langgraph
langgraph dev
# Runs on http://localhost:2024
```

**Terminal 2 - Agent Chat UI:**
```bash
cd apps/agent-chat-ui
npm run dev
# Runs on http://localhost:3000
```

### 5.2: Test Each Agent

1. **Open** http://localhost:3000
2. **Select "Job Analyzer"** from dropdown
3. **Send message:** "Analyze this job: https://example.com/job"
4. **Verify:** Agent analyzes the job posting
5. **Switch to "Resume Tailor"**
6. **Send message:** "Tailor my resume for this job"
7. **Verify:** Agent customizes resume

## Step 6: Deploy to Production (Optional)

### 6.1: LangGraph Cloud

```bash
cd apps/resume-agent-langgraph

# Deploy all agents
langgraph deploy

# Output:
# ✅ Deployed 5 agents:
#    - job_analyzer
#    - resume_tailor
#    - cover_letter_writer
#    - conversational
#    - legacy_advanced
```

### 6.2: Update Agent Chat UI Environment

```bash
# apps/agent-chat-ui/.env.production
LANGGRAPH_API_URL=https://your-deployment.langraph.app
LANGSMITH_API_KEY=your-api-key
```

## Troubleshooting

### Issue: Graph file doesn't export `graph`

**Error:** `ImportError: cannot import name 'graph'`

**Fix:** Ensure each graph file exports the compiled graph:

```python
# Bottom of graph file
def build_my_graph():
    # ... graph construction
    return graph.compile(checkpointer=MemorySaver())

# This line is REQUIRED
graph = build_my_graph()
```

### Issue: Agent not appearing in LangGraph Studio

**Check:**
1. Is the graph listed in `langgraph.json`?
2. Does the file path in `langgraph.json` point to the correct file?
3. Can you import the graph in Python?
   ```bash
   python -c "from src.resume_agent.graphs.job_analysis import graph"
   ```

### Issue: Agent Chat UI shows error when switching agents

**Check:**
1. Is the `agentId` prop being passed correctly to the `Thread` component?
2. Does the LangGraph server have the agent loaded?
3. Open browser DevTools → Network tab → Check API requests

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  Agent Chat UI (Next.js)                │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ Agent Selector                                  │    │
│  │  🔍 Job Analyzer                               │    │
│  │  📝 Resume Tailor      ← User selects agent   │    │
│  │  ✉️ Cover Letter Writer                       │    │
│  │  💬 Career Assistant                           │    │
│  └────────────────────────────────────────────────┘    │
│                         ↓                               │
│                  Creates thread with                    │
│                  selected agent ID                      │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTP/SSE
┌─────────────────────────────────────────────────────────┐
│           LangGraph Server (port 2024)                  │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  job_analyzer    │  │  resume_tailor   │            │
│  │  Graph           │  │  Graph           │            │
│  └──────────────────┘  └──────────────────┘            │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  cover_letter    │  │  conversational  │            │
│  │  Graph           │  │  Graph           │            │
│  └──────────────────┘  └──────────────────┘            │
│                                                          │
│          Each graph is independently loaded              │
│          based on thread agent selection                 │
└─────────────────────────────────────────────────────────┘
```

## Benefits Recap

✅ **Fast Iteration:** Edit one graph file, reload only that agent
✅ **Low Context:** Only load the graph you're using
✅ **Production Ready:** LangGraph server handles everything
✅ **User Choice:** Let users pick the right agent for their task
✅ **Git Friendly:** No merge conflicts when team works on different agents
✅ **Testable:** Test each agent independently

## Next Steps

1. **Expose more agents** - Portfolio Finder, ATS Scorer, etc.
2. **Add agent metadata** - Description, capabilities, example prompts
3. **Smart routing** - Auto-select agent based on user message
4. **Agent handoffs** - Let agents delegate to specialized agents
5. **Streaming improvements** - Show which agent is responding

## Resources

- **LangGraph Multi-Agent Docs:** https://langchain-ai.github.io/langgraph/
- **Agent Chat UI Template:** https://github.com/langchain-ai/agent-chat-ui
- **Progressive Disclosure Guide:** `docs/LANGGRAPH_PROGRESSIVE_DISCLOSURE.md`
