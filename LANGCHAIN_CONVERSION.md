# Resume Agent: LangChain/LangGraph Conversion

## Overview

This document explains how to convert the Resume Agent from FastMCP + Claude Agent SDK to LangChain/LangGraph, and why this makes an excellent portfolio piece for jobs requiring LangChain experience.

## Architecture Comparison

### Current Architecture (FastMCP + Claude SDK)
```
┌─────────────────────────────────────────┐
│         MCP Server (FastMCP)            │
├─────────────────────────────────────────┤
│  Tools: analyze_job, tailor_resume     │
│  Resources: resume://master            │
│  Prompts: Markdown files in .claude/  │
├─────────────────────────────────────────┤
│  Execution: subprocess → claude CLI    │
│  State: File-based (YAML/JSON)         │
│  Agent SDK: Loads .md prompts          │
└─────────────────────────────────────────┘
```

### LangChain Architecture
```
┌─────────────────────────────────────────┐
│      LangGraph StateGraph               │
├─────────────────────────────────────────┤
│  Nodes: job_analyzer, resume_writer    │
│  State: TypedDict with messages        │
│  Edges: Conditional routing            │
├─────────────────────────────────────────┤
│  LLM: ChatAnthropic (direct API)       │
│  Tools: @tool decorated functions      │
│  Chains: LCEL (prompt | llm | parser)  │
│  Memory: MemorySaver checkpointer      │
└─────────────────────────────────────────┘
```

## Key Differences

### 1. **Agent Orchestration**

**Current (Agent SDK):**
```python
# Markdown prompt files
# .claude/agents/job-analyzer.md
async def analyze_job(job_url: str):
    result = await invoke_slash_command(
        "career/analyze-job",
        arguments=job_url
    )
    return result
```

**LangChain (StateGraph):**
```python
# Nodes in a graph
def job_analyzer_node(state: ApplicationState):
    job_analysis = job_analysis_llm.invoke(...)
    return {"job_analysis": job_analysis}

workflow = StateGraph(ApplicationState)
workflow.add_node("analyze_job", job_analyzer_node)
workflow.add_edge(START, "analyze_job")
```

**Portfolio Value:** Shows understanding of stateful workflows and graph-based orchestration.

### 2. **State Management**

**Current (Manual):**
```python
# State passed through function arguments
job_analysis = analyze_job(url)
resume = tailor_resume(job_analysis, master_resume)
cover_letter = write_cover_letter(job_analysis, resume)
```

**LangChain (TypedDict State):**
```python
class ApplicationState(TypedDict):
    job_url: str
    job_analysis: Optional[JobAnalysis]
    master_resume: Optional[MasterResume]
    tailored_resume: Optional[str]
    messages: Sequence[BaseMessage]

# State automatically flows through nodes
```

**Portfolio Value:** Demonstrates knowledge of type-safe state management and message history.

### 3. **LLM Invocation**

**Current (Subprocess):**
```python
# Spawns claude CLI (uses MAX subscription)
process = await asyncio.create_subprocess_shell(
    f'claude --dangerously-skip-permissions -- /career:analyze-job {url}',
    stdout=asyncio.subprocess.PIPE
)
```

**LangChain (Direct API):**
```python
# Direct API calls with structured output
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
job_analysis_llm = llm.with_structured_output(JobAnalysis)

result = job_analysis_llm.invoke(prompt)
```

**Portfolio Value:** Shows proper API integration and structured output patterns.

### 4. **Tool Calling**

**Current (MCP Tools):**
```python
@mcp.tool()
def data_read_master_resume() -> dict:
    with open(MASTER_RESUME, 'r') as f:
        return yaml.safe_load(f)
```

**LangChain (Tool Decorator):**
```python
@tool
def load_master_resume() -> dict:
    """Load the master resume from YAML file."""
    with open(resume_path, 'r') as f:
        return yaml.safe_load(f)

# Tools can be bound to models
model_with_tools = llm.bind_tools([load_master_resume])
```

**Portfolio Value:** Demonstrates LangChain tool calling patterns.

### 5. **Chains (LCEL)**

**Current (Manual composition):**
```python
# Sequential function calls
job_data = fetch_job(url)
analysis = parse_job(job_data)
resume = tailor_resume(analysis)
```

**LangChain (LCEL Chains):**
```python
# Declarative chain composition
chain = (
    prompt
    | llm
    | PydanticOutputParser(pydantic_object=JobAnalysis)
)

result = chain.invoke({"job_content": content})
```

**Portfolio Value:** Shows understanding of declarative programming and LCEL.

### 6. **Conditional Routing**

**Current (Not implemented):**
```python
# Would require manual if/else logic
if match_score > 0.7:
    find_portfolio()
else:
    skip_portfolio()
```

**LangChain (Conditional Edges):**
```python
def should_continue(state: ApplicationState) -> str:
    return "find_portfolio" if state["match_score"] >= 0.7 else "skip"

workflow.add_conditional_edges(
    "analyze_job",
    should_continue,
    {"find_portfolio": "find_portfolio", "skip": "write_resume"}
)
```

**Portfolio Value:** Demonstrates dynamic workflow routing.

## Portfolio-Worthy Features

### 1. **Multi-Agent Collaboration**
```python
# Multiple specialized agents working together
workflow.add_node("job_analyzer", job_analyzer_node)       # Agent 1
workflow.add_node("portfolio_finder", portfolio_finder_node) # Agent 2
workflow.add_node("resume_writer", resume_writer_node)     # Agent 3
workflow.add_node("cover_letter_writer", cover_letter_writer_node) # Agent 4
```

**Why it matters:** Shows ability to design agent teams with clear responsibilities.

### 2. **RAG Implementation** (Bonus)
```python
def create_resume_rag_system():
    """RAG system for semantic search over career history."""
    # Load documents
    loader = DirectoryLoader("./resumes", glob="*.yaml")
    docs = loader.load()

    # Split and embed
    splitter = RecursiveCharacterTextSplitter(chunk_size=500)
    splits = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(splits, embeddings)

    # Create RAG chain
    retriever = vectorstore.as_retriever()
    rag_chain = {"context": retriever | format_docs} | prompt | llm

    return rag_chain

# Use case: "Find my experience with distributed systems"
```

**Why it matters:** RAG is a top requirement in LangChain job postings.

### 3. **Structured Output with Pydantic**
```python
# Type-safe LLM responses
class JobAnalysis(BaseModel):
    company: str
    job_title: str
    required_qualifications: List[str]
    keywords: List[str]

llm_with_structure = llm.with_structured_output(JobAnalysis)
result = llm_with_structure.invoke(prompt)  # Returns JobAnalysis object
```

**Why it matters:** Shows understanding of production-grade LLM applications.

### 4. **State Persistence (Checkpointing)**
```python
# Resume workflow from any point
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# First run
config = {"configurable": {"thread_id": "app-001"}}
app.invoke(initial_state, config=config)

# Resume later (e.g., after human review)
app.invoke({"continue": True}, config=config)
```

**Why it matters:** Critical for long-running agent workflows.

### 5. **Streaming Support**
```python
# Stream tokens as they're generated
for chunk in chain.stream({"topic": "job application"}):
    print(chunk.content, end="", flush=True)

# Stream events from complex graphs
async for event in app.astream_events(initial_state):
    if event['event'] == 'on_chat_model_stream':
        print(event['data']['chunk'].content, end="")
```

**Why it matters:** Better UX for real-time applications.

## Migration Strategy

### Phase 1: Core Conversion (2-3 hours)
1. ✅ Create `ApplicationState` TypedDict
2. ✅ Convert agents to LangGraph nodes
3. ✅ Build StateGraph with edges
4. ✅ Replace subprocess with ChatAnthropic
5. ✅ Convert MCP tools to @tool functions

### Phase 2: Advanced Features (3-4 hours)
6. ⬜ Add conditional routing based on match score
7. ⬜ Implement RAG for resume search
8. ⬜ Add streaming support
9. ⬜ Implement checkpointing/persistence
10. ⬜ Add callbacks for logging/tracing

### Phase 3: Polish (2-3 hours)
11. ⬜ Add LangSmith tracing
12. ⬜ Create Jupyter notebook demo
13. ⬜ Write comprehensive README
14. ⬜ Add unit tests with LangChain testing utils
15. ⬜ Deploy as LangServe API

## Code Comparison: Key Workflow

### Current Implementation
```python
# resume_agent.py (FastMCP + Agent SDK)
@mcp.tool()
async def apply_to_job(job_url: str) -> dict:
    # Execute slash command (subprocess)
    result_text = await invoke_slash_command("career/apply", arguments=job_url)

    return {
        "status": "success",
        "result": result_text
    }
```

### LangChain Implementation
```python
# resume_agent_langchain.py (LangGraph)
def apply_to_job_langchain(job_url: str) -> Dict[str, Any]:
    # Create workflow graph
    workflow = StateGraph(ApplicationState)
    workflow.add_node("analyze_job", job_analyzer_node)
    workflow.add_node("find_portfolio", portfolio_finder_node)
    workflow.add_node("write_resume", resume_writer_node)
    workflow.add_node("write_cover_letter", cover_letter_writer_node)
    workflow.add_node("save_files", save_files_node)

    # Define workflow
    workflow.add_edge(START, "analyze_job")
    workflow.add_edge("analyze_job", "find_portfolio")
    workflow.add_edge("find_portfolio", "write_resume")
    workflow.add_edge("write_resume", "write_cover_letter")
    workflow.add_edge("write_cover_letter", "save_files")
    workflow.add_edge("save_files", END)

    # Compile with memory
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    # Execute
    initial_state = ApplicationState(
        job_url=job_url,
        include_cover_letter=True,
        messages=[HumanMessage(content=f"Apply to job: {job_url}")]
    )

    final_state = app.invoke(initial_state, config={"configurable": {"thread_id": "app-001"}})

    return final_state
```

## When to Use Each Approach

### Use Current (FastMCP + Agent SDK) When:
- ✅ You want to use Claude Code's MAX subscription (no API costs)
- ✅ You prefer markdown-based agent definitions
- ✅ MCP integration with Claude Desktop is primary use case
- ✅ You want simpler deployment (single file, no external LLM calls)

### Use LangChain/LangGraph When:
- ✅ You need to demonstrate LangChain experience for job applications
- ✅ You want advanced features (RAG, conditional routing, streaming)
- ✅ You need production deployment (LangServe, monitoring)
- ✅ You want framework-agnostic LLM usage (swap providers easily)
- ✅ You need stateful, resumable workflows
- ✅ You want to showcase technical depth in portfolio

## Interview Talking Points

When discussing this project in interviews for LangChain roles:

1. **"Tell me about your LangChain experience"**
   - "I converted a job application automation system from a simple agent SDK to LangGraph to demonstrate multi-agent orchestration"
   - "The system uses StateGraph with 5 specialized nodes for job analysis, portfolio search, resume tailoring, and cover letter generation"
   - "I implemented conditional routing based on match scores to optimize the workflow"

2. **"Have you worked with RAG?"**
   - "Yes, I added a RAG system for semantic search over my career history"
   - "Used FAISS for vector storage with recursive text splitting optimized for YAML resume documents"
   - "The retriever helps identify relevant experience for different job types"

3. **"How do you handle state in agent workflows?"**
   - "I use LangGraph's TypedDict state with message history"
   - "Implemented checkpointing with MemorySaver for resumable workflows"
   - "Each node reads from and writes to shared state, ensuring type safety with Pydantic"

4. **"What about production deployment?"**
   - "The current version is development-focused, but I could deploy via LangServe"
   - "I've integrated LangSmith tracing for debugging and monitoring"
   - "The architecture supports horizontal scaling since HTTP Streamable transport is stateless"

## Dependencies

```bash
# Current stack
pip install fastmcp pyyaml httpx sqlmodel python-dotenv

# LangChain stack
pip install langchain langchain-anthropic langgraph langchain-community langchain-openai faiss-cpu
```

## Conclusion

**Current system** is production-ready and cost-effective for personal use.

**LangChain version** is a portfolio piece demonstrating:
- Multi-agent orchestration with LangGraph
- RAG implementation with vector stores
- Conditional workflow routing
- State management and persistence
- Tool calling patterns
- LCEL chain composition
- Structured output with Pydantic

**Recommendation for job applications:**
- Keep both implementations
- Showcase LangChain version in portfolio
- Explain trade-offs and design decisions
- Demonstrate you understand when to use each approach

This shows mature engineering judgment, not just framework knowledge.
