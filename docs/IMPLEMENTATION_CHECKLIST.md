# Progressive Disclosure Implementation Checklist

**Transform your LangGraph development in 5 steps**

Use this checklist to implement the progressive disclosure pattern for your LangGraph agents and Agent Chat UI integration.

## Prerequisites

- [ ] LangGraph project exists (`apps/resume-agent-langgraph/`)
- [ ] Agent Chat UI exists (`apps/agent-chat-ui/`)
- [ ] Both can run independently
- [ ] You've read `/prime-agentic-systems` (run the slash command)
- [ ] You've reviewed `docs/LANGGRAPH_PROGRESSIVE_DISCLOSURE.md`

## Phase 1: Audit Current State (15 minutes)

### Analyze Existing Code

- [ ] Check main graph file size:
  ```bash
  wc -l apps/resume-agent-langgraph/src/resume_agent/graph.py
  ```
  - If >300 lines → **Progressive disclosure will help significantly**
  - If <200 lines → **Consider whether split is needed**

- [ ] List existing workflows in your agent:
  - [ ] Workflow 1: _________________ (~___ lines)
  - [ ] Workflow 2: _________________ (~___ lines)
  - [ ] Workflow 3: _________________ (~___ lines)
  - [ ] Workflow 4: _________________ (~___ lines)
  - [ ] Workflow 5: _________________ (~___ lines)

- [ ] Check if separate graph files already exist:
  ```bash
  ls apps/resume-agent-langgraph/src/resume_agent/graphs/
  ```

- [ ] Review current `langgraph.json`:
  ```bash
  cat apps/resume-agent-langgraph/langgraph.json
  ```

### Decision Point

Choose your implementation path:

**Path A: Extract from Monolith**
- [ ] You have one large `graph.py` file (300+ lines)
- [ ] Multiple workflows are intermingled
- [ ] Follow "Extract First Agent" section below

**Path B: Expose Existing Graphs**
- [ ] You already have separate graph files in `graphs/` directory
- [ ] They just aren't exposed in `langgraph.json`
- [ ] Follow "Expose Existing Agents" section below

## Phase 2: Expose Existing Agents (30 minutes)

**Use this if you already have modular graph files**

### Step 1: Verify Graph Exports

Each graph file must export a compiled graph at module level:

- [ ] Check `graphs/job_analysis.py`:
  ```bash
  python -c "from src.resume_agent.graphs.job_analysis import graph; print('✅')"
  ```

- [ ] Check `graphs/resume_tailor.py`:
  ```bash
  python -c "from src.resume_agent.graphs.resume_tailor import graph; print('✅')"
  ```

- [ ] Check `graphs/cover_letter.py`:
  ```bash
  python -c "from src.resume_agent.graphs.cover_letter import graph; print('✅')"
  ```

- [ ] Fix any import errors before proceeding

### Step 2: Update langgraph.json

- [ ] Open `apps/resume-agent-langgraph/langgraph.json`

- [ ] Add each graph to the `"graphs"` section:
  ```json
  {
    "graphs": {
      "job_analyzer": "./src/resume_agent/graphs/job_analysis.py:graph",
      "resume_tailor": "./src/resume_agent/graphs/resume_tailor.py:graph",
      "cover_letter_writer": "./src/resume_agent/graphs/cover_letter.py:graph"
    }
  }
  ```

- [ ] Save file

### Step 3: Test LangGraph Server

- [ ] Start LangGraph dev server:
  ```bash
  cd apps/resume-agent-langgraph
  langgraph dev
  ```

- [ ] Verify all agents load in terminal output:
  ```
  ✅ Loaded graphs: job_analyzer, resume_tailor, cover_letter_writer
  ```

- [ ] Open LangGraph Studio: http://localhost:2024

- [ ] Create thread for each agent and test:
  - [ ] Test `job_analyzer`
  - [ ] Test `resume_tailor`
  - [ ] Test `cover_letter_writer`

## Phase 3: Extract First Agent from Monolith (2 hours)

**Use this if you need to extract workflows from monolithic graph.py**

### Choose First Workflow to Extract

Pick the **simplest, most independent** workflow to start:

- [ ] Selected workflow: _________________
- [ ] Estimated lines: _________________
- [ ] External dependencies: _________________

### Create New Graph File

- [ ] Create new file:
  ```bash
  touch apps/resume-agent-langgraph/src/resume_agent/graphs/my_first_agent.py
  ```

- [ ] Copy template from `EXAMPLE_SELF_CONTAINED_AGENT.py`:
  ```bash
  cp apps/resume-agent-langgraph/src/resume_agent/graphs/EXAMPLE_SELF_CONTAINED_AGENT.py \
     apps/resume-agent-langgraph/src/resume_agent/graphs/my_first_agent.py
  ```

### Extract Components

- [ ] **State Schema** - Copy relevant state fields from main graph:
  ```python
  class MyAgentState(TypedDict, total=False):
      messages: List[BaseMessage]
      # Only include fields THIS workflow needs
  ```

- [ ] **Tools** - Copy tools this workflow uses:
  ```python
  @tool
  def my_tool(...):
      """Tool description."""
      # Implementation
  ```

- [ ] **Nodes** - Copy node functions:
  ```python
  def my_node(state: MyAgentState) -> Dict:
      # Implementation
      return {...}
  ```

- [ ] **Routing** - Copy routing logic:
  ```python
  def route_after_node(state: MyAgentState) -> str:
      if state.get("errors"):
          return "error_handler"
      return "next_node"
  ```

### Build Graph

- [ ] Implement `build_graph()` function:
  ```python
  def build_my_agent_graph():
      graph = StateGraph(MyAgentState)

      # Add nodes
      graph.add_node("node1", node1_func)
      graph.add_node("node2", node2_func)

      # Define flow
      graph.add_edge(START, "node1")
      graph.add_edge("node1", "node2")
      graph.add_edge("node2", END)

      return graph.compile(checkpointer=MemorySaver())
  ```

- [ ] Export compiled graph:
  ```python
  graph = build_my_agent_graph()
  ```

### Test Standalone

- [ ] Add test block at bottom of file:
  ```python
  if __name__ == "__main__":
      test_graph = build_my_agent_graph()
      result = test_graph.invoke(
          {"messages": [HumanMessage(content="Test query")]},
          config={"configurable": {"thread_id": "test-1"}}
      )
      print(result)
  ```

- [ ] Run standalone test:
  ```bash
  python -m resume_agent.graphs.my_first_agent
  ```

- [ ] Verify output is correct

### Add to LangGraph Server

- [ ] Add to `langgraph.json`:
  ```json
  {
    "graphs": {
      "my_first_agent": "./src/resume_agent/graphs/my_first_agent.py:graph"
    }
  }
  ```

- [ ] Restart LangGraph server

- [ ] Test in LangGraph Studio

### Extract Remaining Workflows

- [ ] Repeat above steps for each workflow:
  - [ ] Workflow 2: _________________
  - [ ] Workflow 3: _________________
  - [ ] Workflow 4: _________________
  - [ ] Workflow 5: _________________

## Phase 4: Update Agent Chat UI (1 hour)

### Create Agent Selector Component

- [ ] Create `apps/agent-chat-ui/src/components/agent-selector.tsx`

- [ ] Copy implementation from `docs/QUICK_START_MULTI_AGENT.md`

- [ ] Define your agent list:
  ```typescript
  const AGENTS: Agent[] = [
    {
      id: "job_analyzer",
      name: "Job Analyzer",
      description: "Analyze job postings",
      icon: "🔍"
    },
    // ... add all your agents
  ];
  ```

- [ ] Test component in isolation

### Update Thread Page

- [ ] Open `apps/agent-chat-ui/src/app/thread/[thread]/page.tsx`

- [ ] Add agent selection state:
  ```typescript
  const [selectedAgent, setSelectedAgent] = useState<AgentType>("conversational");
  ```

- [ ] Add `<AgentSelector />` component to UI

- [ ] Pass `selectedAgent` to `<Thread />` component

### Update Thread Component

- [ ] Open `apps/agent-chat-ui/src/components/thread/index.tsx`

- [ ] Add `agentId` prop to component:
  ```typescript
  interface ThreadProps {
    threadId: string;
    agentId: string;
  }
  ```

- [ ] Update stream call to use `agentId`:
  ```typescript
  const stream = client.runs.stream(
    threadId,
    agentId, // Use selected agent
    { input: { messages: [...] } }
  );
  ```

### Test Multi-Agent UI

- [ ] Start both servers:
  ```bash
  # Terminal 1
  cd apps/resume-agent-langgraph && langgraph dev

  # Terminal 2
  cd apps/agent-chat-ui && npm run dev
  ```

- [ ] Open http://localhost:3000

- [ ] Test each agent:
  - [ ] Select agent from dropdown
  - [ ] Send test message
  - [ ] Verify correct agent responds
  - [ ] Switch to different agent
  - [ ] Verify switch works

## Phase 5: Refinement (2 hours)

### Optimize Graph Files

- [ ] Review each graph file for size:
  ```bash
  wc -l apps/resume-agent-langgraph/src/resume_agent/graphs/*.py
  ```

- [ ] If any file >250 lines, consider splitting further

- [ ] Ensure each graph is truly self-contained:
  - [ ] All tools embedded in file or imported explicitly
  - [ ] All nodes defined in file
  - [ ] State schema is minimal (only fields this graph needs)

### Add Documentation

- [ ] Add docstring to each graph file explaining:
  - [ ] What this agent does
  - [ ] When to use it
  - [ ] Example queries

- [ ] Update `README.md` with agent descriptions

- [ ] Add agent selection guide to UI (help tooltip)

### Improve Agent Selection UX

- [ ] Add agent descriptions to UI tooltip

- [ ] Show agent capabilities in selection dropdown

- [ ] Add example prompts for each agent:
  ```typescript
  const EXAMPLE_PROMPTS = {
    job_analyzer: [
      "Analyze this job posting: [URL]",
      "What are the key requirements for this role?"
    ],
    resume_tailor: [
      "Customize my resume for this job",
      "Highlight my Python experience"
    ]
  };
  ```

- [ ] Consider smart routing (auto-select agent based on query)

### Performance Testing

- [ ] Measure agent load time:
  ```bash
  time curl http://localhost:2024/threads
  ```

- [ ] Test concurrent agent access:
  - [ ] Open 3 browser tabs
  - [ ] Use different agent in each
  - [ ] Verify no conflicts

- [ ] Check context window usage:
  - [ ] Enable LLM tracing
  - [ ] Compare token usage: monolith vs individual agents

## Phase 6: Team Onboarding (30 minutes)

### Documentation

- [ ] Create team guide explaining:
  - [ ] How to add new agents
  - [ ] How to test agents standalone
  - [ ] How to update agent selection UI

- [ ] Add architecture diagram showing:
  - [ ] Agent Chat UI → LangGraph Server flow
  - [ ] Multiple agents in server
  - [ ] How agent selection works

### Developer Experience

- [ ] Create quick-add script:
  ```bash
  #!/bin/bash
  # scripts/add-agent.sh
  AGENT_NAME=$1
  cp src/resume_agent/graphs/EXAMPLE_SELF_CONTAINED_AGENT.py \
     src/resume_agent/graphs/${AGENT_NAME}.py
  echo "✅ Created graphs/${AGENT_NAME}.py"
  echo "📝 Add to langgraph.json: \"${AGENT_NAME}\": \"./src/resume_agent/graphs/${AGENT_NAME}.py:graph\""
  ```

- [ ] Add to project commands:
  ```bash
  # Makefile or package.json scripts
  add-agent:
    ./scripts/add-agent.sh $(NAME)
  ```

### Team Training

- [ ] Show team how to:
  - [ ] Copy template
  - [ ] Build self-contained graph
  - [ ] Test standalone
  - [ ] Add to langgraph.json
  - [ ] Update UI agent list

## Success Metrics

Track these metrics to measure improvement:

### Before Implementation

- [ ] Time to add new workflow: _______ hours
- [ ] Time to fix bug: _______ minutes
- [ ] Test cycle time: _______ minutes
- [ ] Merge conflicts per week: _______
- [ ] Context window usage: _______ tokens

### After Implementation

- [ ] Time to add new agent: _______ minutes
- [ ] Time to fix bug: _______ minutes
- [ ] Test cycle time: _______ seconds
- [ ] Merge conflicts per week: _______
- [ ] Context window usage: _______ tokens

### Target Improvements

- [ ] Development speed: 3-4x faster
- [ ] Bug fix time: 75% reduction
- [ ] Context usage: 80% reduction
- [ ] Merge conflicts: 90% reduction

## Troubleshooting

### Graph won't import

**Error:** `ImportError: cannot import name 'graph'`

**Fix:**
- [ ] Ensure file exports `graph` at module level:
  ```python
  graph = build_my_graph()
  ```
- [ ] Check for syntax errors:
  ```bash
  python -m py_compile src/resume_agent/graphs/my_agent.py
  ```

### Agent not appearing in LangGraph Studio

**Fix:**
- [ ] Verify entry in `langgraph.json`
- [ ] Restart LangGraph server
- [ ] Check server logs for errors

### Agent Chat UI can't switch agents

**Fix:**
- [ ] Verify `agentId` prop is passed to `Thread` component
- [ ] Check browser console for errors
- [ ] Verify LangGraph server has agent loaded

### State fields missing

**Error:** Agent behavior is broken after extraction

**Fix:**
- [ ] Review original monolithic state schema
- [ ] Ensure all required fields are in new agent's state
- [ ] Test with same input as before

## Next Steps After Completion

- [ ] Deploy to staging environment
- [ ] A/B test with users (single agent vs multi-agent UI)
- [ ] Gather feedback on agent selection UX
- [ ] Consider additional agents for specialized workflows
- [ ] Explore agent-to-agent handoffs (advanced)

## Resources

- [ ] Read `docs/LANGGRAPH_PROGRESSIVE_DISCLOSURE.md`
- [ ] Review `docs/QUICK_START_MULTI_AGENT.md`
- [ ] Study `docs/LANGGRAPH_BEFORE_AFTER.md`
- [ ] Copy template from `EXAMPLE_SELF_CONTAINED_AGENT.py`
- [ ] Consult `/prime-agentic-systems` for philosophy

---

**Remember:** The goal is simple, focused agents that are fast to build and maintain, not sophisticated multi-agent orchestration. Start simple and iterate.
